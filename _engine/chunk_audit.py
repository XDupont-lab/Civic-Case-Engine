#!/usr/bin/env python3
"""
CIVIC CASE ENGINE — CHUNK-AUDIT ENGINE (v0.3 PROTOCOL IMPLEMENTATIE)
Cognitieve Werkgeheugentoets & Dichtheidsbewaker tegen Hyper-Densification.
Pure Python Standard Library (Zero External Dependencies).

Protocolreferentie:
Notion: Chunk-Audit — telprotocol voor leesbaarheid (v0.3, instrument-kandidaat)
Status: Geïntegreerde Cognitieve Impedantie-Poort voor Civic Case Engine.

Waarom dit nodig is:
Na zware multi-LLM audits (DeepSeek, Grok, Gemini) neemt de dichtheid van teksten
vaak extreem toe. Juridische precisie en defensieve clausules stapelen zich op tot
de tekst cognitief dichtslaat voor de menselijke lezer (rechter, ambtenaar, arts).

De Lat (per actie-eenheid / regel):
  ≤ 4  | ✅ GROEN   | Past in het werkgeheugen. Geen ingreep.
  5–6  | 🟡 GEEL    | Krap. Verwijs in plaats van herhalen; voorbeelden naar bijlage.
  ≥ 7  | 🔴 ROOD    | Te vol. Verplicht ingrijpen: splitsen of details uitplaatsen.

Macro-lat:
  ≤ 7 nieuwe kernbegrippen per pagina / macro-sectie.
"""

import sys
import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional

# Force UTF-8 on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


class ChunkAuditor:
    """Implementeert de telregels en dichtheidstoets van Chunk-Audit v0.3."""

    STOPWORDS_NL = {
        "de", "het", "een", "der", "den", "van", "naar", "op", "in", "bij", "voor",
        "met", "aan", "om", "te", "en", "of", "als", "dan", "ook", "is", "zijn",
        "was", "waren", "wordt", "worden", "werd", "werden", "kan", "kunnen", "moet",
        "moeten", "zal", "zullen", "geen", "niet", "wel", "dit", "deze", "dat",
        "die", "wat", "wie", "hoe", "waar", "er", "hier", "daar", "zich", "door",
        "uit", "over", "tot", "reeds", "nog", "maar", "want", "doch", "dus"
    }

    def __init__(self, green_max: int = 4, yellow_max: int = 6, macro_max: int = 7):
        self.green_max = green_max
        self.yellow_max = yellow_max
        self.macro_max = macro_max

    def extract_units(self, text: str) -> List[Dict]:
        """
        Splitst tekst in 'kleinste eenheden die iemand moet kunnen uitvoeren':
        - Genummerde lijst-items
        - Bullet-points
        - Tabelrijen
        - Korte alineablokken
        """
        lines = text.splitlines()
        units = []
        current_section = "Inleiding"
        current_para = []
        line_num_start = 1

        def flush_para(line_start, sec):
            if current_para:
                full_text = " ".join(current_para).strip()
                if full_text and len(full_text) > 10:
                    units.append({
                        "type": "paragraph",
                        "section": sec,
                        "line": line_start,
                        "raw": full_text
                    })
                current_para.clear()

        for idx, line in enumerate(lines, start=1):
            s = line.strip()
            if not s:
                flush_para(line_num_start, current_section)
                line_num_start = idx + 1
                continue

            # Sectiekoppen
            if s.startswith("#"):
                flush_para(line_num_start, current_section)
                current_section = s.lstrip("#").strip()
                line_num_start = idx + 1
                continue

            # Genummerde lijst: 1. of 1)
            num_match = re.match(r"^(\d+[\.\)])\s+(.*)", s)
            if num_match:
                flush_para(line_num_start, current_section)
                units.append({
                    "type": "numbered_item",
                    "prefix": num_match.group(1),
                    "section": current_section,
                    "line": idx,
                    "raw": num_match.group(2).strip()
                })
                line_num_start = idx + 1
                continue

            # Bullet points: * of -
            bullet_match = re.match(r"^[\*\-]\s+(.*)", s)
            if bullet_match:
                flush_para(line_num_start, current_section)
                units.append({
                    "type": "bullet_item",
                    "prefix": "•",
                    "section": current_section,
                    "line": idx,
                    "raw": bullet_match.group(1).strip()
                })
                line_num_start = idx + 1
                continue

            # Tabelrijen (overslaan scheidingslijnen |---|)
            if s.startswith("|") and s.endswith("|"):
                flush_para(line_num_start, current_section)
                if not re.match(r"^\|[\s\-:]+\|\s*$", s):
                    cells = [c.strip() for c in s.strip("|").split("|")]
                    units.append({
                        "type": "table_row",
                        "prefix": "table",
                        "section": current_section,
                        "line": idx,
                        "raw": " — ".join(cells)
                    })
                line_num_start = idx + 1
                continue

            # Gewone alinea-regel
            if not current_para:
                line_num_start = idx
            current_para.append(s)

        flush_para(line_num_start, current_section)
        return units

    def count_chunks_in_unit(self, unit_text: str, defined_corpus_terms: set) -> Tuple[int, List[str], List[str]]:
        """
        Telt het aantal actieve concepten / cognitieve chunks in één eenheid conform v0.3:
        1. Nieuw + nodig + samenhangend = 1
        2. Al gedefinieerd in corpus = 0
        3. Bekend begrip met nieuwe conditie = 1
        4. Verwijzing ('zie bijlage') = 1
        5. Conditionele vertakkingen ('indien', 'mits', 'tenzij', 'als') verhogen de belasting.
        """
        chunks = []
        flags = []

        # Verwijzingen tellen als 1 chunk
        refs = re.findall(r"(?:zie\s+(?:bijlage|artikel|wet|lijn|stuk|tabel)\s+[A-Za-z0-9_\-\.]+)", unit_text, re.IGNORECASE)
        for r in refs:
            chunks.append(f"Verwijzing: {r}")

        # Conditionele vertakkingen (complexiteits-triggers)
        branches = re.findall(r"\b(tenzij|mits|indien|op voorwaarde dat|uitgezonderd|in afwijking van)\b", unit_text, re.IGNORECASE)
        for b in branches:
            chunks.append(f"Voorwaarde/Uitzondering: '{b}'")
            flags.append("Conditionele vertakking verhoogt werkgeheugenbelasting")

        # Zoek samengestelde concepten, vaktermen, wetten of afkortingen
        # bijv. "art. 15 AVG", "Fournier-gangreen", "COPD GOLD 2", "A/G-ratio"
        legal_med_terms = re.findall(
            r"\b(?:art\.\s*\d+(?::\d+)?[a-z]?\s+[A-Z]+|[A-Z]{2,}(?:[-_][A-Z0-9]+)*|\b[A-Z][a-z]+(?:[A-Z][a-z]+)+\b)\b",
            unit_text
        )
        for t in legal_med_terms:
            t_clean = t.strip()
            if t_clean.lower() not in self.STOPWORDS_NL:
                if t_clean.lower() not in defined_corpus_terms:
                    chunks.append(f"Nieuwe term/norm: {t_clean}")
                    defined_corpus_terms.add(t_clean.lower())

        # Significante inhoudelijke zinsdelen / proposities (gescheiden door komma's/puntkomma's)
        clauses = [c.strip() for c in re.split(r"[,;]\s*", unit_text) if len(c.strip().split()) >= 3]
        for c in clauses:
            # Controleer of deze clause een actieve handeling of claim bevat
            words = [w.lower() for w in re.findall(r"\b[a-zA-Z0-9_\-]+\b", c) if w.lower() not in self.STOPWORDS_NL]
            if len(words) >= 3:
                phrase_repr = " ".join(words[:4])
                if phrase_repr not in [ch.lower() for ch in chunks]:
                    chunks.append(f"Handelingsclaim: '{c[:45]}...'")

        # Ontdubbelen en score bepalen
        score = len(chunks)
        # Zorg dat een enkele simpele zin nooit 0 scoort als er tekst is
        if score == 0 and len(unit_text.strip()) > 5:
            score = 1
            chunks.append("Enkele propositie")

        return score, chunks, flags

    def audit_text(self, text: str) -> Dict:
        """Voert de volledige Chunk-Audit v0.3 uit op een document."""
        units = self.extract_units(text)
        defined_terms = set()
        audited_units = []
        green_count = 0
        yellow_count = 0
        red_count = 0

        for u in units:
            score, chunk_list, flags = self.count_chunks_in_unit(u["raw"], defined_terms)
            if score <= self.green_max:
                verdict = "GROEN"
                icon = "✅"
                green_count += 1
            elif score <= self.yellow_max:
                verdict = "GEEL"
                icon = "🟡"
                yellow_count += 1
            else:
                verdict = "ROOD"
                icon = "🔴"
                red_count += 1

            audited_units.append({
                "type": u.get("type"),
                "prefix": u.get("prefix", ""),
                "section": u.get("section", ""),
                "line": u.get("line"),
                "raw": u.get("raw"),
                "score": score,
                "verdict": verdict,
                "icon": icon,
                "chunks": chunk_list,
                "flags": flags
            })

        total_units = len(audited_units)
        is_pass = (red_count == 0)

        # Macro analyse: aantal unieke gedefinieerde begrippen
        macro_score = len(defined_terms)
        macro_verdict = "✅ PAST" if macro_score <= (len(audited_units) * 2) else "🟡 VOL"

        return {
            "total_units": total_units,
            "green_count": green_count,
            "yellow_count": yellow_count,
            "red_count": red_count,
            "macro_score": macro_score,
            "macro_verdict": macro_verdict,
            "is_pass": is_pass,
            "units": audited_units
        }

    def format_report(self, audit_result: Dict, file_name: str = "Document") -> str:
        """Genereert een overzichtelijk audit-rapport in GitHub Markdown."""
        res = audit_result
        lines = []
        lines.append(f"# 🧮 Chunk-Audit Rapport v0.3 — {file_name}")
        lines.append("")
        lines.append(f"**Totaal geëvalueerde eenheden:** {res['total_units']}  ")
        lines.append(f"**Uitslag:** {'✅ GESLAAGD (100% Uitvoerbaar)' if res['is_pass'] else '🔴 INTERVENTIE VEREIST (Dichtheid te hoog)'}  ")
        lines.append(f"**Verdeling:** ✅ Groen (≤4): {res['green_count']} | 🟡 Geel (5–6): {res['yellow_count']} | 🔴 Rood (≥7): {res['red_count']}  ")
        lines.append(f"**Macro-dichtheid:** {res['macro_score']} actieve begrippen ({res['macro_verdict']})")
        lines.append("")
        lines.append("---")
        lines.append("")

        if not res["is_pass"]:
            lines.append("## 🔴 Verplichte Reparaties (Volgorde conform Protocol v0.3):")
            lines.append("1. **Haal versie-uitleg en ontstaansgeschiedenis uit de regel:** Verplaats achtergrond naar bijlage.")
            lines.append("2. **Haal voorbeelden uit de regel:** Plaats casusvoorbeelden in een toelichting.")
            lines.append("3. **Splits de regel:** Maak er drie van: de regel zelf, de ijkvoorwaarde, wat verboden is.")
            lines.append("")

        lines.append("## Detailtelling per Actie-eenheid:")
        lines.append("")
        lines.append("| Lijn | Sectie | Score | Oordeel | Tekstfragment / Chunks |")
        lines.append("|---|---|---|---|---|")

        for u in res["units"]:
            snippet = u["raw"][:70].replace("|", "\\|") + ("..." if len(u["raw"]) > 70 else "")
            chunks_desc = "<br>• ".join(u["chunks"][:3])
            if len(u["chunks"]) > 3:
                chunks_desc += f"<br>*(+ nog {len(u['chunks']) - 3} chunks)*"
            lines.append(f"| L{u['line']} | {u['section'][:20]} | **{u['score']}** | {u['icon']} {u['verdict']} | *{snippet}*<br>• {chunks_desc} |")

        return "\n".join(lines)


def audit_file(file_path: Path, verbose: bool = False) -> Dict:
    auditor = ChunkAuditor()
    text = file_path.read_text(encoding="utf-8", errors="replace")
    result = auditor.audit_text(text)
    report = auditor.format_report(result, file_name=file_path.name)
    if verbose:
        print(report)
    return result


def main():
    if len(sys.argv) < 2:
        print("Gebruik: python chunk_audit.py <pad-naar-document.md> [--verbose]")
        sys.exit(1)

    target_file = Path(sys.argv[1])
    if not target_file.exists():
        print(f"[!] Bestand niet gevonden: {target_file}")
        sys.exit(1)

    auditor = ChunkAuditor()
    text = target_file.read_text(encoding="utf-8", errors="replace")
    res = auditor.audit_text(text)
    report = auditor.format_report(res, file_name=target_file.name)
    print(report)

    if not res["is_pass"]:
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
