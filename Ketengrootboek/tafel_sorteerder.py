#!/usr/bin/env python3
"""
CIVIC HELPER — BOEKHOUD-SORTEERDER & TAFEL-OOGSTER (v1.1)
Pure Python Standard Library (Zero External Dependencies).

Sorteert de aanwezige historische én actuele bronnen (TAFEL.md, archief/tafel/*.md,
00_Termijnen_en_Klok.md, Incoming_Letters, Outgoing_Letters, mail_outbox, Audio_Recordings)
gericht naar het Drie-Boekenstelsel van Simon Stevin:

  1. Boek 1 (Het Memoriaal - memoriaal.json):
     Alleen waarnemingen met een fysiek bestaand bronbestand op schijf + SHA-256 hash.
     Geen losse AI-chattekst zonder bewijsstuk (De Zeef).
  2. Boek 2 (Het Journaal - boek2_journaal.json):
     Ketenoverdrachten (Debet/Zender -> Credit/Ontvanger) inclusief wettelijke termijn (Klok)
     en terugverwijzing naar het Tafel-besluit (`tafel_besluit`).
  3. Tafel-Besluit & Auditregister (tafel_besluiten.json):
     De oogst uit de gesprekken tussen Xander en de LLM's (Grok, agy, DeepSeek, Argon,
     ChatGPT, Claude, Mistral, Qwen) gekoppeld aan de boeken.

Gebruik:
  python tafel_sorteerder.py --voorstel       (Dry-run: toont wat er klaarstaat om geboekt te worden)
  python tafel_sorteerder.py --boek-alles     (Boekt alle met SHA-256 geverifieerde ketensporen in Boek 1, 2, 3 + tafel_besluiten.json)
  python tafel_sorteerder.py --analyse-tafel  (Toont per beurt op de huidige TAFEL.md of het Bestuur of Kassabon is)
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys
from typing import Any, Dict, List, Optional, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

KETEN_DIR = Path(__file__).resolve().parent
if str(KETEN_DIR) not in sys.path:
    sys.path.insert(0, str(KETEN_DIR))

from sluiting import SluitingsToetser, sha256_bestand


MAANDEN_NL = {
    "jan": "01", "januari": "01",
    "feb": "02", "februari": "02",
    "mrt": "03", "maart": "03",
    "apr": "04", "april": "04",
    "mei": "05",
    "jun": "06", "juni": "06",
    "jul": "07", "juli": "07",
    "aug": "08", "augustus": "08",
    "sep": "09", "sept": "09", "september": "09",
    "okt": "10", "oktober": "10",
    "nov": "11", "november": "11",
    "dec": "12", "december": "12",
}

GENERIEKE_OVERZICHT_STUKKEN = {
    "45_integrale_huisartsen_en_zorgverleners_chronologie_2016_2026",
    "49_overdrachtsketen",
}


def parse_nl_datum(tekst: str) -> Optional[str]:
    """Zet Nederlandse datumtekst (bijv. '17 okt 2026' of '2026-10-17') om naar ISO YYYY-MM-DD."""
    if not tekst:
        return None
    m_iso = re.search(r"\b(20\d{2}-\d{2}-\d{2})\b", tekst)
    if m_iso:
        return m_iso.group(1)
    m_nl = re.search(r"\b(\d{1,2})\s+([a-zA-Z]+)\.?\s+(20\d{2})\b", tekst)
    if m_nl:
        dag = int(m_nl.group(1))
        maand_naam = m_nl.group(2).lower()
        jaar = m_nl.group(3)
        maand = MAANDEN_NL.get(maand_naam)
        if maand:
            return f"{jaar}-{maand}-{dag:02d}"
    return None


def bepaal_modaliteit(pad_str: str) -> str:
    ext = Path(pad_str).suffix.lower()
    if ext in (".wav", ".mp3", ".m4a", ".ogg"):
        return "audio_opname"
    if ext == ".pdf":
        return "pdf_document"
    if ext in (".jpg", ".jpeg", ".png"):
        return "beeld_scan"
    if ext in (".csv", ".xml"):
        return "bank_data"
    if ext == ".eml":
        return "raw_email_eml"
    if "Sent_" in pad_str or "Outgoing_Letters" in pad_str:
        return "uitgaande_email"
    if "Incoming_Letters" in pad_str:
        return "inkomend_stuk"
    if "Zorgdossier" in pad_str:
        return "zorgdossier_stuk"
    return "schriftelijk_bewijs"


class BoekhoudSorteerder:
    def __init__(self, toetser: Optional[SluitingsToetser] = None):
        self.toetser = toetser or SluitingsToetser()
        self.keten_dir = self.toetser.keten_dir
        self.civic_root = self.toetser.workspace_root
        self.hub_root = self.toetser.hub_root
        self.zorg_dir = self.hub_root / "Zorgdossier"
        self.tafel_pad = self.hub_root / "agy_werk" / "TAFEL.md"
        self.tafel_archief_dir = self.hub_root / "agy_werk" / "archief" / "tafel"

    def vind_echt_bestand(self, verwijzing: str) -> Optional[Tuple[str, Path, str]]:
        """Lost een wikilink [[...]] of relatief pad op naar (rel_pad, abs_pad, sha256) indien het op schijf staat."""
        schoon = verwijzing.strip().strip("`'\"").replace("file:///E:/LLM_Workspace/", "").replace("file:///e:/LLM_Workspace/", "")
        if not schoon:
            return None

        direct = self.toetser._los_bestand_op(schoon)
        if direct and direct.is_file():
            h = sha256_bestand(direct)
            rel = self._maak_relatief(direct)
            return (rel, direct, h or "")

        zoek_mappen = [
            self.zorg_dir,
            self.civic_root / "Incoming_Letters",
            self.civic_root / "Outgoing_Letters",
            self.hub_root / "Shared_Tools" / "mail_outbox",
            self.hub_root / "Audio_Recordings",
            self.hub_root / "agy_werk" / "outbox",
        ]
        for zmap in zoek_mappen:
            if not zmap.is_dir():
                continue
            for kandidaat in zmap.iterdir():
                if not kandidaat.is_file():
                    continue
                if kandidaat.name == schoon or kandidaat.stem == schoon or kandidaat.stem.startswith(schoon + "_"):
                    h = sha256_bestand(kandidaat)
                    rel = self._maak_relatief(kandidaat)
                    return (rel, kandidaat, h or "")
        return None

    def _maak_relatief(self, abs_pad: Path) -> str:
        try:
            return abs_pad.relative_to(self.civic_root).as_posix()
        except ValueError:
            try:
                return abs_pad.relative_to(self.hub_root).as_posix()
            except ValueError:
                return abs_pad.as_posix()

    def oogst_uit_klok_tabel(self) -> List[Dict[str, Any]]:
        """Scant Tabel 1 en Tabel 2 van Zorgdossier/00_Termijnen_en_Klok.md op geverifieerde ketensporen."""
        klok_pad = self.zorg_dir / "00_Termijnen_en_Klok.md"
        if not klok_pad.is_file():
            return []

        feiten_index, posten_lijst = self.toetser.laad_boeken()
        bestaande_paden = {
            f.get("bewijsstuk", "").replace("\\", "/").lower()
            for f in feiten_index.values()
        }
        for f in feiten_index.values():
            for ep in f.get("extra_bewijsstukken", []):
                bestaande_paden.add(ep.replace("\\", "/").lower())

        regels = klok_pad.read_text(encoding="utf-8").splitlines()
        gevonden_sporen: List[Dict[str, Any]] = []

        in_tabel_1 = False
        rij_nr = 0
        for line in regels:
            if line.startswith("## 1. Lopende Wettelijke"):
                in_tabel_1 = True
                continue
            if line.startswith("## 2. Zorg- en Ketenopvolging"):
                break
            if not in_tabel_1 or not line.strip().startswith("|"):
                continue
            cellen = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cellen) < 8 or cellen[0] in ("Dossierstuk", "---"):
                continue

            rij_nr += 1
            stuk_cel, instantie, onderwerp, start_str, verval_str, grondslag, status_str, vervolgstap = cellen[:8]

            refs = re.findall(r"`([^`]+\.(?:md|pdf|txt|wav|jpg|eml))`", line) + re.findall(r"\[\[([^\]]+)\]\]", line)
            opgeloste_bestanden: List[Tuple[str, Path, str]] = []
            for ref in refs:
                res = self.vind_echt_bestand(ref)
                if res and res[0] not in [x[0] for x in opgeloste_bestanden]:
                    opgeloste_bestanden.append(res)

            if not opgeloste_bestanden:
                continue

            # Kies bij voorkeur het meest specifieke stuk i.p.v. generieke overzichtsstukken 45/49
            specifieke = [
                x for x in opgeloste_bestanden
                if x[1].stem.lower() not in GENERIEKE_OVERZICHT_STUKKEN
            ]
            geordend = specifieke + [x for x in opgeloste_bestanden if x not in specifieke]

            primair_rel, _, primair_hash = geordend[0]
            extra_rels = [x[0] for x in geordend[1:]]

            # Controleer of dit spoor al in Boek 1/2 gedekt is (op bestand of op vervolgpost)
            al_geboekt = primair_rel.lower() in bestaande_paden
            inst_low = instantie.lower()
            ond_low = onderwerp.lower()
            if not al_geboekt:
                for p in posten_lijst:
                    p_str = json.dumps(p, ensure_ascii=False).lower()
                    if inst_low and inst_low.split()[0] in p_str and any(k in p_str for k in ond_low.split() if len(k) > 5):
                        al_geboekt = True
                        break

            start_iso = parse_nl_datum(start_str) or "2026-10-01"
            verval_iso = parse_nl_datum(verval_str) or start_iso

            is_voldaan = any(w in status_str.upper() for w in ("VOLDAAN", "VOLLEDIG VOLDAAN", "BLANCO"))
            slug = re.sub(r"[^A-Z0-9]+", "-", instantie.upper()).strip("-")[:22]
            datum_compact = start_iso.replace("-", "")

            feit_id = f"EVT-KLOK-{slug}-{datum_compact}-{rij_nr:02d}"
            post_id = f"POST-KLOK-{slug}-{rij_nr:03d}"

            gevonden_sporen.append({
                "rij_nr": rij_nr,
                "al_in_boeken": al_geboekt,
                "feit_id": feit_id,
                "post_id": post_id,
                "instantie": instantie,
                "onderwerp": onderwerp,
                "start_datum": start_iso,
                "verval_datum": verval_iso,
                "grondslag": grondslag,
                "status_tekst": status_str,
                "is_materieel_voldaan": is_voldaan,
                "vervolgstap": vervolgstap,
                "primair_bewijsstuk": primair_rel,
                "primair_sha256": primair_hash,
                "extra_bewijsstukken": extra_rels,
                "modaliteit": bepaal_modaliteit(primair_rel),
            })

        return gevonden_sporen

    def analyseer_huidige_tafel(self) -> List[Dict[str, Any]]:
        """Analyseert alle beurten in agy_werk/TAFEL.md en classificeert ze:
        - 'KASSABON_ADMINISTRATIE' : Verslag van verzending/archivering met bestandspaden (hoort in Boek 1 & 2)
        - 'SYSTEEM_FOUT_LOG'       : Technische foutmelding (bijv. HTTP 402) (hoort niet op de Tafel)
        - 'SEIN_OF_RICHTING_BURGER': Inbreng/besluit van Xander
        - 'BESTUUR_EN_AFWEGING'    : Inhoudelijk gesprek, hypothese, model-weging
        """
        if not self.tafel_pad.is_file():
            return []

        tekst = self.tafel_pad.read_text(encoding="utf-8")
        blokken = re.split(r"(?m)^##\s+", tekst)
        beurten: List[Dict[str, Any]] = []

        for blok in blokken[1:]:
            regels = blok.strip().splitlines()
            kop = regels[0].strip() if regels else "Onbekend"
            body = "\n".join(regels[1:]).strip()

            pad_matches = re.findall(r"file:///E:/LLM_Workspace/([^\)\s]+)", body)
            pad_matches += re.findall(r"`([A-Za-z0-9_/\.\-]+?\.(?:md|pdf|txt|wav|mp3|json))`", body)
            unieke_paden = list(dict.fromkeys(pad_matches))

            if "[FOUT " in body or "HTTP 402" in body or "prepayment credits" in body:
                categorie = "SYSTEEM_FOUT_LOG"
                bestemming = "Verwijderen van Tafel (technische log)"
            elif any(k in kop for k in ("Verzonden:", "Inkomend Gearchiveerd:", "Ontvangstbevestiging", "Telefoongesprek Woningstichting")):
                categorie = "KASSABON_ADMINISTRATIE"
                bestemming = "Boek 1 (memoriaal.json) + Boek 2 (boek2_journaal.json); op Tafel hooguit 1-regelige beslis-/uitvoeringslink"
            elif kop.startswith("Xander"):
                categorie = "SEIN_OF_RICHTING_BURGER"
                bestemming = "Behouden op Tafel + koppelen als `tafel_besluit` in Boek 2"
            else:
                categorie = "BESTUUR_EN_AFWEGING"
                bestemming = "Behouden op Tafel (inhoudelijke weging / model-analyse)"

            beurten.append({
                "kop": kop,
                "categorie": categorie,
                "bestemming": bestemming,
                "aantal_regels": len(regels),
                "gekoppelde_bestanden": unieke_paden[:6],
            })

        return beurten

    def scan_tafel_archief_statistiek(self) -> Dict[str, Any]:
        """Telt hoeveel gearchiveerde Tafel-bestanden en beurten er in agy_werk/archief/tafel/ liggen."""
        if not self.tafel_archief_dir.is_dir():
            return {"bestanden": 0, "beurten": 0, "bewijs_verwijzingen": 0}
        bestanden = sorted(self.tafel_archief_dir.glob("*.md"))
        totaal_beurten = 0
        totaal_refs = 0
        for b in bestanden:
            inhoud = b.read_text(encoding="utf-8", errors="replace")
            totaal_beurten += len(re.findall(r"(?m)^##\s+", inhoud))
            totaal_refs += len(re.findall(r"\.(?:md|pdf|txt|wav|mp3|csv|xml)\b", inhoud))
        return {
            "bestanden": len(bestanden),
            "beurten": totaal_beurten,
            "bewijs_verwijzingen": totaal_refs,
        }

    def bouw_tafel_besluitregister(self) -> List[Dict[str, Any]]:
        """Genereert tafel_besluiten.json: koppelt de Tafel-besluiten en Multi-LLM audits
        aan de bijbehorende posten in Boek 2 en bewijsstukken in Boek 1.
        """
        _, posten_lijst = self.toetser.laad_boeken()
        register: List[Dict[str, Any]] = []
        for p in posten_lijst:
            register.append({
                "tafel_besluit_id": p.get("tafel_besluit", f"TAFEL-{p['post_id']}"),
                "gekoppeld_post_id": p["post_id"],
                "gekoppeld_anker_feit": p.get("anker_feit"),
                "gekoppeld_tegen_feit": p.get("tegen_feit"),
                "rekening_credit": p.get("credit_rekening"),
                "kwalificatie_kern": p.get("naam"),
                "invariante_eis": (p.get("vaste_posten") or [{}])[0].get("omschrijving", ""),
                "termijn": p.get("termijn"),
            })
        uit_pad = self.keten_dir / "tafel_besluiten.json"
        uit_pad.write_text(json.dumps(register, indent=2, ensure_ascii=False), encoding="utf-8")
        return register

    def boek_nieuwe_klok_sporen(self) -> Tuple[int, int]:
        """Boekt alle nog ontbrekende, met SHA-256 geverifieerde ketensporen uit 00_Termijnen_en_Klok.md
        in Boek 1 (memoriaal.json) en Boek 2 (boek2_journaal.json) en ververst Boek 3 (ketengrootboek.json).
        """
        sporen = self.oogst_uit_klok_tabel()
        nieuwe_sporen = [s for s in sporen if not s["al_in_boeken"]]
        if not nieuwe_sporen:
            self.bouw_tafel_besluitregister()
            return (0, 0)

        b1_prim, b1_leg = self.toetser._boek1_paden()
        b2_prim, b2_leg = self.toetser._boek2_paden()

        memoriaal_lijst = json.loads(b1_prim.read_text(encoding="utf-8"))
        journaal_lijst = json.loads(b2_prim.read_text(encoding="utf-8"))

        bestaande_feit_ids = {f["id"] for f in memoriaal_lijst}
        bestaande_post_ids = {p["post_id"] for p in journaal_lijst}

        geboekte_feiten = 0
        geboekte_posten = 0

        for s in nieuwe_sporen:
            fid = s["feit_id"]
            pid = s["post_id"]
            is_voldaan = s["is_materieel_voldaan"]

            feit_type = "levering_voltooid" if is_voldaan else "schriftelijk_verzoek_of_inzage"

            if fid not in bestaande_feit_ids:
                nieuw_feit: Dict[str, Any] = {
                    "id": fid,
                    "datum": s["start_datum"],
                    "type": feit_type,
                    "modaliteit": s["modaliteit"],
                    "actor": s["instantie"],
                    "omschrijving": f"{s['onderwerp']} — Status: {s['status_tekst']}",
                    "bewijsstuk": s["primair_bewijsstuk"],
                    "laag": "LAAG_1_WAARNEMING",
                    "interpretatie_historie": [],
                }
                if s["extra_bewijsstukken"]:
                    nieuw_feit["extra_bewijsstukken"] = s["extra_bewijsstukken"]
                memoriaal_lijst.append(nieuw_feit)
                bestaande_feit_ids.add(fid)
                geboekte_feiten += 1

            if pid not in bestaande_post_ids:
                nieuwe_post: Dict[str, Any] = {
                    "post_id": pid,
                    "naam": f"{s['instantie']} — {s['onderwerp'][:80]}",
                    "debet_rekening": "Burger / Belanghebbende (chart_burger)",
                    "credit_rekening": f"{s['instantie']}",
                    "anker_feit": fid,
                    "tegen_feit": fid,
                    "tafel_besluit": f"TAFEL-KLOK-REGISTER-RIJ-{s['rij_nr']:02d}",
                    "termijn": {
                        "grondslag": s["grondslag"],
                        "start_datum": s["start_datum"],
                        "verval_datum": s["verval_datum"],
                        "uiterste_datum": s["verval_datum"],
                        "vervolgstap_bij_overschrijding": s["vervolgstap"][:160],
                    },
                    "sluitings_conditie": {
                        "vereist_feit_type": "levering_voltooid",
                        "tussen_anker_en_tegenfeit": True,
                    },
                    "vaste_posten": [
                        {
                            "id": f"C_klok_{s['rij_nr']:02d}",
                            "omschrijving": f"Ketenverplichting: {s['onderwerp'][:90]}",
                            "in_credit_geboekt": is_voldaan,
                        }
                    ],
                    "micro_observables": [
                        {
                            "id": f"O_bewijs_{s['rij_nr']:02d}",
                            "omschrijving": f"Geverifieerd dossierstuk: {s['primair_bewijsstuk']}",
                        }
                    ],
                    "vereiste_velden": ["volledig_dossier_of_besluit"],
                    "geboekte_velden": ["volledig_dossier_of_besluit"] if is_voldaan else [],
                    "poorten": {
                        "bronpoort": {
                            "naam": s["grondslag"],
                            "voldaan": True,
                        },
                        "doelpoort": {
                            "naam": f"Materiële afhandeling door {s['instantie']}",
                            "voldaan": is_voldaan,
                        },
                    },
                }
                journaal_lijst.append(nieuwe_post)
                bestaande_post_ids.add(pid)
                geboekte_posten += 1

        b1_tekst = json.dumps(memoriaal_lijst, indent=2, ensure_ascii=False)
        b1_prim.write_text(b1_tekst, encoding="utf-8")
        b1_leg.write_text(b1_tekst, encoding="utf-8")

        b2_tekst = json.dumps(journaal_lijst, indent=2, ensure_ascii=False)
        b2_prim.write_text(b2_tekst, encoding="utf-8")
        b2_leg.write_text(b2_tekst, encoding="utf-8")

        self.toetser.draai_proefbalans()
        self.bouw_tafel_besluitregister()
        return (geboekte_feiten, geboekte_posten)

    def formatteer_voorstel_rapport(self) -> str:
        klok_sporen = self.oogst_uit_klok_tabel()
        al_aanwezig = [s for s in klok_sporen if s["al_in_boeken"]]
        nieuw_kandidaat = [s for s in klok_sporen if not s["al_in_boeken"]]
        tafel_beurten = self.analyseer_huidige_tafel()
        archief_stats = self.scan_tafel_archief_statistiek()

        lines = []
        lines.append("=" * 120)
        lines.append("CIVIC HELPER — BOEKHOUD-SORTEERDER & ARCHIEF-OOGSTER (VOORSTEL / DRY-RUN)")
        lines.append("=" * 120)
        lines.append(f"1. Tafel-Archief (`agy_werk/archief/tafel/`): {archief_stats['bestanden']} bestanden | {archief_stats['beurten']} beurten | {archief_stats['bewijs_verwijzingen']} bestandsverwijzingen")
        lines.append(f"2. Huidige `TAFEL.md`: {len(tafel_beurten)} beurten geanalyseerd")
        lines.append(f"3. Keten- & Klokregister (`00_Termijnen_en_Klok.md`): {len(klok_sporen)} sporen met fysiek bewijs op schijf ({len(al_aanwezig)} al in Boek 1/2, {len(nieuw_kandidaat)} klaar om te boeken)")
        lines.append("-" * 120)
        lines.append("A. KANDIDAAT-BOEKINGEN VOOR BOEK 1 (MEMORIAAL) & BOEK 2 (JOURNAAL) MET SHA-256 OP SCHIJF:")
        lines.append("-" * 120)
        for s in nieuw_kandidaat:
            status_kort = "SLUIT (VOLDAAN)" if s["is_materieel_voldaan"] else f"OPEN (vervalt {s['verval_datum']})"
            lines.append(
                f"  * {s['post_id']:<34} | {s['instantie'][:28]:<28} | {status_kort:<24} | {s['primair_bewijsstuk']} (sha256={s['primair_sha256'][:10]}...)"
            )

        lines.append("")
        lines.append("-" * 120)
        lines.append("B. SORTEER-ANALYSE VAN DE HUIDIGE BEURTEN OP `TAFEL.md` (BESTUUR VS. KASSABON):")
        lines.append("-" * 120)
        for idx, b in enumerate(tafel_beurten, 1):
            lines.append(f"  [{idx:02d}] {b['categorie']:<24} | {b['kop'][:60]:<60} ({b['aantal_regels']} regels)")
        lines.append("=" * 120)
        return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Civic Helper Boekhoud-Sorteerder & Tafel-Oogster")
    parser.add_argument("--voorstel", action="store_true", help="Dry-run: toon boekingsvoorstel en Tafel-analyse")
    parser.add_argument("--boek-alles", action="store_true", help="Boek alle met SHA-256 geverifieerde ketensporen in Boek 1, 2 en 3")
    parser.add_argument("--analyse-tafel", action="store_true", help="Toon gedetailleerde classificatie van de huidige TAFEL.md")
    args = parser.parse_args()

    sorteerder = BoekhoudSorteerder()

    if args.boek_alles:
        f_cnt, p_cnt = sorteerder.boek_nieuwe_klok_sporen()
        print(f"[*] {f_cnt} nieuwe feiten geboekt in Boek 1 (memoriaal.json) en {p_cnt} nieuwe overdrachten in Boek 2 (boek2_journaal.json).")
        print(sorteerder.toetser.draai_proefbalans())
        return

    if args.analyse_tafel:
        print(json.dumps(sorteerder.analyseer_huidige_tafel(), indent=2, ensure_ascii=False))
        return

    print(sorteerder.formatteer_voorstel_rapport())


if __name__ == "__main__":
    main()
