#!/usr/bin/env python3
"""
CIVIC CASE ENGINE — CIVIC LEGAL KERNEL (PROCESDOSSIER BUNDLER & EXPORTER v1.0)
Civic Exoskeleton Forensic Case Assembler.
Pure Python Standard Library (Zero External Dependencies).

Rol in de architectuur:
De synthese- en exportmodule van de Civic Legal Kernel. Bundelt chronologie,
actieve rechtsdoctrine en genummerde producties tot een onweerlegbaar procesdossier.

Doel:
Genereert een integraal, professioneel genummerd en forensisch geverifieerd procesdossier
(bundel met inhoudsopgave, master-chronologie, doctrine-inbedding en genummerde producties
inclusief SHA-256 integriteitshashes).

Direct gereed voor indiening bij de Bezwaarcommissie, de Rechtbank (sector Bestuursrecht/Kanton),
of de Nationale Ombudsman.

Pure Python 3 Standard Library — Geen externe packages vereist.
"""

import os
import sys
import json
import hashlib
import datetime
import re
import argparse
from pathlib import Path

# Forceer UTF-8 console output op Windows
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

BASE_DIR = Path(__file__).resolve().parent.parent
DOSSIER_DIR = BASE_DIR / "Dossier"
INCOMING_DIR = BASE_DIR / "Incoming_Letters"
OUTGOING_DIR = BASE_DIR / "Outgoing_Drafts"
PROBES_DIR = BASE_DIR / "Probes"
DOCTRINE_FILE = BASE_DIR / "DOCTRINE.md"

def sha256_file(filepath: Path) -> str:
    """Berekent de SHA-256 hash van een bestand."""
    h = hashlib.sha256()
    try:
        with open(filepath, 'rb') as f:
            while chunk := f.read(65536):
                h.update(chunk)
        return h.hexdigest()
    except Exception as e:
        return f"ERROR_HASHING: {e}"

def read_text_safe(filepath: Path) -> str:
    """Leest tekstbestand veilig uit met UTF-8 fallback."""
    if not filepath.exists():
        return ""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        try:
            with open(filepath, 'r', encoding='latin-1') as f:
                return f.read()
        except Exception:
            return ""
    except Exception:
        return ""

def get_thematic_dossiers() -> list:
    """Verzamelt alle thematische dossierbestanden (01_ t/m 12_)."""
    thematics = []
    if not DOSSIER_DIR.exists():
        return thematics
    boilerplate_prefixes = (
        "#", "**Beschrijving:**", "---",
        "- Wat is", "- Wie zijn", "- Welke",
        "- Waar wringt", "- Incoming_Letters",
        "- Medische verklaringen"
    )
    for f in sorted(DOSSIER_DIR.glob("*.md")):
        name = f.name
        if re.match(r"^\d{2}_", name) and not name.startswith("00_"):
            content = read_text_safe(f).strip()
            custom_lines = [
                l for l in content.splitlines()
                if l.strip() and not any(l.strip().startswith(p) for p in boilerplate_prefixes)
            ]
            thematics.append({
                "path": f,
                "name": name,
                "title": name.replace(".md", "").replace("_", " "),
                "content": content,
                "has_custom_content": len(custom_lines) > 0
            })
    return thematics

def collect_productions() -> list:
    """Verzamelt alle bewijsstukken en processtukken uit Outgoing_Drafts en Incoming_Letters."""
    productions = []
    prod_id = 1

    # 1. Outgoing letters & drafts (verstuurde sondes en concepten)
    if OUTGOING_DIR.exists():
        for f in sorted(OUTGOING_DIR.glob("*.md")):
            if f.name.startswith("AUDIT_REPORT_"):
                continue  # Sla interne auditrapporten over in de externe bundel
            content = read_text_safe(f)
            if not content.strip():
                continue
            h = sha256_file(f)
            stat = f.stat()
            mod_date = datetime.date.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d")
            
            title = f.name.replace(".md", "").replace("_", " ")
            # Probeer titel uit eerste H1 te halen
            for line in content.splitlines():
                if line.startswith("# "):
                    title = line.replace("# ", "").strip()
                    break

            productions.append({
                "id": prod_id,
                "filename": f.name,
                "path": f,
                "relative": f.relative_to(BASE_DIR).as_posix(),
                "title": title,
                "category": "Uitgaand Processtuk / Formele Sonde",
                "date": mod_date,
                "sha256": h,
                "content": content
            })
            prod_id += 1

    # 2. Incoming letters (inkomende brieven en beschikkingen)
    if INCOMING_DIR.exists():
        for f in sorted(INCOMING_DIR.iterdir()):
            if f.is_file() and not f.name.startswith("."):
                content = read_text_safe(f) if f.suffix.lower() in [".md", ".txt"] else f"[Binair bewijsstuk / PDF: {f.name}]"
                h = sha256_file(f)
                stat = f.stat()
                mod_date = datetime.date.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d")
                
                productions.append({
                    "id": prod_id,
                    "filename": f.name,
                    "path": f,
                    "relative": f.relative_to(BASE_DIR).as_posix(),
                    "title": f"Inkomend stuk: {f.name}",
                    "category": "Inkomend Bewijsstuk / Beschikking",
                    "date": mod_date,
                    "sha256": h,
                    "content": content
                })
                prod_id += 1

    return productions

def extract_chronology_highlights() -> tuple:
    """Leest de 00_Master_Chronologie uit en extraheert kernfeiten en zorgbreuken."""
    chrono_md = DOSSIER_DIR / "00_Master_Chronologie.md"
    chrono_json = DOSSIER_DIR / "00_Master_Chronologie.json"
    
    total_facts = 0
    disruptions = []
    events_table = []
    text_content = ""

    if chrono_json.exists():
        try:
            with open(chrono_json, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    total_facts = len(data)
                elif isinstance(data, dict):
                    total_facts = data.get("total_facts", len(data.get("facts", [])))
                    disruptions = data.get("care_disruptions_and_silences", [])
        except Exception:
            pass

    if chrono_md.exists():
        text_content = read_text_safe(chrono_md)
        m = re.search(r"Totaal aantal unieke geverifieerde feiten:\*\*\s*(\d+)", text_content)
        if m:
            total_facts = int(m.group(1))
        elif total_facts == 0:
            total_facts = len([l for l in text_content.splitlines() if l.startswith("| **20") or l.startswith("| 20")])

        # Extraheer gedetecteerde zorgbreuken uit markdown indien aanwezig
        if not disruptions and "Gedetecteerde Zorgbreuken" in text_content:
            try:
                parts = text_content.split("Gedetecteerde Zorgbreuken")
                sec_disrupt = parts[1].split("---")[0]
                for r in sec_disrupt.strip().splitlines():
                    if r.startswith("| **") or r.startswith("| Ketenbreuk") or r.startswith("| Zorgstilte"):
                        cols = [c.strip() for c in r.split("|")[1:-1]]
                        if len(cols) >= 5:
                            disruptions.append({
                                "severity": cols[0].replace("*", ""),
                                "start_date": cols[1],
                                "end_date": cols[1],
                                "days_silence": cols[2],
                                "statutory_violation": cols[3],
                                "description": cols[4]
                            })
            except Exception:
                pass

        # Extraheer tabelregels specifiek uit Ketenmatrix (Sectie 3)
        if "Integrale Forensische Ketenmatrix" in text_content:
            matrix_part = text_content.split("Integrale Forensische Ketenmatrix")[1]
            events_table = [l for l in matrix_part.splitlines() if l.startswith("|")]

    return text_content, total_facts, disruptions, events_table

def build_case_bundle(case_title: str, author_name: str, respondent_name: str, output_file: Path) -> Path:
    """Bouwt het complete procesdossier op in Markdown en optioneel HTML."""
    now_str = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    date_str = datetime.datetime.now().strftime("%d-%m-%Y")
    
    # 1. Lees data
    doctrine_content = read_text_safe(DOCTRINE_FILE)
    chrono_text, total_facts, disruptions, events_table = extract_chronology_highlights()
    thematics = get_thematic_dossiers()
    productions = collect_productions()

    # 2. Bereken bundel-hashes voor verificatiematrix
    bundle_manifest = []
    for p in productions:
        bundle_manifest.append(f"{p['id']:02d} | {p['date']} | {p['category']} | {p['filename']} | `{p['sha256'][:16]}...`")

    # 3. Assembleer Markdown Bundel
    b = []
    
    # --- VOORBLAD / FRONTISPICE ---
    b.append("# ⚖️ INTEGRAAL PROCESDOSSIER & BEWIJSBUNDEL")
    b.append("")
    b.append(f"**Zaak:** {case_title}  ")
    b.append(f"**Indiener / Betrokkene:** {author_name}  ")
    b.append(f"**Wederpartij / Bestuursorgaan:** {respondent_name}  ")
    b.append(f"**Datum van samenstelling:** {date_str} (Gegenereerd om {now_str})  ")
    b.append(f"**Forensische Integriteitsstatus:** Verifieerbaar via SHA-256 Checksums  ")
    b.append("")
    b.append("> [!IMPORTANT]")
    b.append("> Dit procesdossier is samengesteld via het *Civic Case Engine Exoskeleton*. Alle opgenomen producties, feiten en correspondentie zijn voorzien van een cryptografische SHA-256 vingerafdruk ter verificatie van de materiële en temporele authenticiteit.")
    b.append("")
    b.append("---")
    b.append("")

    # --- INHOUDSOPGAVE ---
    b.append("## 📋 Inhoudsopgave van de Bundel")
    b.append("")
    b.append("1. [Deel I: Zaaksbeschrijving & Toepasselijk Juridisch Kader](#deel-i-zaaksbeschrijving--toepasselijk-juridisch-kader)")
    b.append("2. [Deel II: Forensische Master Chronologie & Geconstateerde Zorgbreuken](#deel-ii-forensische-master-chronologie--geconstateerde-zorgbreuken)")
    b.append("3. [Deel III: Thematische Feitenconstatering](#deel-iii-thematische-feitenconstatering)")
    b.append("4. [Deel IV: SHA-256 Integriteitsregister van Producties](#deel-iv-sha-256-integriteitsregister-van-producties)")
    b.append("5. [Deel V: Genummerde Producties & Bewijsstukken](#deel-v-genummerde-producties--bewijsstukken)")
    b.append("6. [Deel VI: Formeel Petitum & Conclusie](#deel-vi-formeel-petitum--conclusie)")
    b.append("")
    b.append("---")
    b.append("")

    # --- DEEL I: JURIDISCH KADER & DOCTRINE ---
    b.append("## Deel I: Zaaksbeschrijving & Toepasselijk Juridisch Kader")
    b.append("")
    b.append(f"Dit procesdossier documenteert het feitelijke en procedurele verloop tussen **{author_name}** en **{respondent_name}**.")
    b.append("De grondslag van het verweer c.q. de vordering rust op de heersende wettelijke kaders en jurisprudentie van de hoogste bestuursrechters:")
    b.append("")
    if doctrine_content:
        # Filter markdown koppen iets omlaag zodat ze in de bundelstructuur passen
        doc_lines = []
        for line in doctrine_content.splitlines():
            if line.startswith("# "):
                doc_lines.append(f"### {line[2:]}")
            elif line.startswith("## "):
                doc_lines.append(f"#### {line[3:]}")
            else:
                doc_lines.append(line)
        b.append("\n".join(doc_lines))
    else:
        b.append("*Geen specifiek doctrinebestand geladen.*")
    b.append("")
    b.append("---")
    b.append("")

    # --- DEEL II: MASTER CHRONOLOGIE ---
    b.append("## Deel II: Forensische Master Chronologie & Geconstateerde Zorgbreuken")
    b.append("")
    b.append(f"De feitenmatrix omvat **{total_facts} chronologische gebeurtenissen**, samengesteld uit primaire brondocumenten (waaronder bankmutaties, officiële beschikkingen, zaaksysteemnotities en formele communicatie).")
    b.append("")
    if disruptions:
        b.append("### ⚠️ Geconstateerde Zorgbreuken en Institutionele Communicatiestiltes")
        b.append("")
        b.append("| Periode / Datum | Aard van de Stilte / Breuk | Dagen / Duur | Ernst | Juridische Toets & Context |")
        b.append("|---|---|---|---|---|")
        for d in disruptions:
            b.append(f"| {d.get('start_date', '')} | {d.get('description', '')} | {d.get('days_silence', '')} | **{d.get('severity', '')}** | {d.get('statutory_violation', '')} |")
        b.append("")

    # Pak een overzichtelijke uitsnede van de chronologie (de laatste 60 regels van de tabel of de gehele tabel als die beknopt is)
    if events_table:
        b.append("### Integrale Feitenmatrix (Uittreksel Recente Gebeurtenissen)")
        b.append("")
        if len(events_table) > 70:
            b.append("> [!NOTE]")
            b.append(f"> De volledige chronologie bevat {total_facts} feiten. Hieronder worden de kopregels en de meest recente gebeurtenissen getoond. Het complete feitenregister is vastgelegd in `00_Master_Chronologie.md` en `00_Master_Chronologie.json`.")
            b.append("")
            b.append("\n".join(events_table[:2]))   # Header en divisor
            b.append("\n".join(events_table[-50:]))  # Laatste 50 feiten
        else:
            b.append("\n".join(events_table))
    elif chrono_text:
        b.append(chrono_text)
    b.append("")
    b.append("---")
    b.append("")

    # --- DEEL III: THEMATISCHE DOSSIERS ---
    b.append("## Deel III: Thematische Feitenconstatering")
    b.append("")
    custom_thematics = [t for t in thematics if t["has_custom_content"]]
    if custom_thematics:
        for t in custom_thematics:
            b.append(f"### {t['title']}")
            b.append(t["content"])
            b.append("")
    else:
        b.append("*(De thematische dossierstukken 01 t/m 12 zijn gearchiveerd en ter inzage in het basissysteem; kernfeiten zijn integraal opgenomen in de Master Chronologie en de producties).*")
    b.append("")
    b.append("---")
    b.append("")

    # --- DEEL IV: INTEGRITEITSREGISTER ---
    b.append("## Deel IV: SHA-256 Integriteitsregister van Producties")
    b.append("")
    b.append("Onderstaande tabel bevat het bindende authenticiteitsregister. Ieder stuk kan onweerlegbaar worden geverifieerd tegen het bronbestand:")
    b.append("")
    b.append("| Nr. | Datum | Categorie | Stuk / Bestandsnaam | SHA-256 Checksum (Prefix) |")
    b.append("|---|---|---|---|---|")
    for row in bundle_manifest:
        b.append(f"| {row} |")
    b.append("")
    b.append("---")
    b.append("")

    # --- DEEL V: PRODUCTIES ---
    b.append("## Deel V: Genummerde Producties & Bewijsstukken")
    b.append("")
    if productions:
        for p in productions:
            b.append(f"### Productie {p['id']}: {p['title']}")
            b.append(f"- **Document:** `{p['filename']}`")
            b.append(f"- **Categorie:** {p['category']}")
            b.append(f"- **Datum:** {p['date']}")
            b.append(f"- **Volledige SHA-256 Hash:** `{p['sha256']}`")
            b.append("")
            b.append("```markdown")
            b.append(p['content'].strip())
            b.append("```")
            b.append("")
            b.append('<div style="page-break-after: always;"></div>')
            b.append("")
    else:
        b.append("*Geen afzonderlijke producties ingeladen in `Outgoing_Drafts` of `Incoming_Letters`.*")
        b.append("")
    b.append("---")
    b.append("")

    # --- DEEL VI: PETITUM ---
    b.append("## Deel VI: Formeel Petitum & Conclusie")
    b.append("")
    b.append(f"Op grond van het vorenstaande, de geconstateerde feiten en de toepasselijke wettelijke bepalingen, verzoekt **{author_name}**:")
    b.append("")
    b.append("1. **Rechtsherstel & Nakoming:** Het bestuursorgaan c.q. de wederpartij te bevelen haar wettelijke zorg- en beslisplichten onverkort na te komen;")
    b.append("2. **Schriftelijkheid:** Alle toekomstige communicatie, besluitvorming en voorstellen uitsluitend schriftelijk te laten plaatsvinden;")
    b.append("3. **Kostenvergoeding:** Overeenkomstig artikel 7:15 lid 2 Awb c.q. artikel 8:75 Awb de gemaakte proces- en administratiekosten integraal te vergoeden.")
    b.append("")
    b.append(f"**Aldus opgemaakt te Nederland, d.d. {date_str},**")
    b.append("")
    b.append(f"*{author_name}*")
    b.append("")

    # Schrijf Markdown bundel
    bundle_text = "\n".join(b)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(bundle_text)

    # Genereer optioneel standalone HTML printversie
    html_file = output_file.with_suffix(".html")
    generate_standalone_html(case_title, bundle_text, html_file)

    return output_file

def generate_standalone_html(title: str, markdown_content: str, html_output: Path):
    """Zet de Markdown bundel om in een elegante, printklare HTML-pagina met CSS page breaks."""
    # Eenvoudige, robuuste Markdown naar HTML converter zonder externe libs
    html_body = markdown_content
    # Escape basics
    html_body = html_body.replace("&", "&amp;").replace("<div style=\"page-break-after: always;\"></div>", "<div class=\"page-break\"></div>")
    # Headers
    html_body = re.sub(r"^### (.*?)$", r"<h3>\1</h3>", html_body, flags=re.MULTILINE)
    html_body = re.sub(r"^## (.*?)$", r"<h2>\1</h2>", html_body, flags=re.MULTILINE)
    html_body = re.sub(r"^# (.*?)$", r"<h1>\1</h1>", html_body, flags=re.MULTILINE)
    # Bold & Italic
    html_body = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", html_body)
    html_body = re.sub(r"\*(.*?)\*", r"<em>\1</em>", html_body)
    # Inline code
    html_body = re.sub(r"`(.*?)`", r"<code>\1</code>", html_body)
    # Line breaks
    html_body = html_body.replace("\n\n", "<br><br>\n")

    html_template = f"""<!DOCTYPE html>
<html lang="nl">
<head>
<meta charset="UTF-8">
<title>{title}</title>
<style>
    body {{
        font-family: 'Segoe UI', Georgia, serif;
        line-height: 1.6;
        color: #1a1a1a;
        max-width: 900px;
        margin: 40px auto;
        padding: 20px;
        background-color: #fafafa;
    }}
    .container {{
        background: #ffffff;
        padding: 50px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        border-radius: 6px;
    }}
    h1 {{ color: #1e3a8a; border-bottom: 2px solid #1e3a8a; padding-bottom: 8px; margin-top: 0; }}
    h2 {{ color: #1e40af; border-bottom: 1px solid #cbd5e1; padding-bottom: 5px; margin-top: 35px; }}
    h3 {{ color: #334155; margin-top: 25px; }}
    code {{ background: #f1f5f9; padding: 2px 6px; border-radius: 4px; font-family: Consolas, monospace; font-size: 0.9em; }}
    pre {{ background: #f8fafc; border: 1px solid #e2e8f0; padding: 15px; border-radius: 6px; overflow-x: auto; }}
    blockquote {{ border-left: 4px solid #3b82f6; margin: 20px 0; padding: 10px 20px; background: #eff6ff; }}
    table {{ width: 100%; border-collapse: collapse; margin: 20px 0; font-size: 0.9em; }}
    th, td {{ border: 1px solid #cbd5e1; padding: 8px 12px; text-align: left; }}
    th {{ background: #f1f5f9; font-weight: bold; }}
    .page-break {{ page-break-after: always; height: 1px; margin: 30px 0; border-top: 1px dashed #cbd5e1; }}
    @media print {{
        body {{ background: none; margin: 0; padding: 0; }}
        .container {{ box-shadow: none; padding: 0; }}
        .page-break {{ page-break-after: always; border: none; }}
        a {{ text-decoration: none; color: inherit; }}
    }}
</style>
</head>
<body>
<div class="container">
{html_body}
</div>
</body>
</html>"""
    try:
        with open(html_output, 'w', encoding='utf-8') as f:
            f.write(html_template)
    except Exception:
        pass

def main():
    parser = argparse.ArgumentParser(description="Civic Case Engine — Forensic Case Bundler")
    parser.add_argument("--title", default="Zaakdossier & Maatwerkvoorziening Wmo", help="Zaakstitel")
    parser.add_argument("--author", default="Betrokkene", help="Naam indiener")
    parser.add_argument("--respondent", default="College van Burgemeester en Wethouders", help="Wederpartij")
    parser.add_argument("--out", default=None, help="Uitvoerbestand (pad naar .md)")

    args = parser.parse_args()

    date_tag = datetime.datetime.now().strftime("%Y%m%d")
    clean_title = re.sub(r"[^\w\-_]", "_", args.title.strip())
    
    if args.out:
        out_path = Path(args.out)
    else:
        out_path = DOSSIER_DIR / f"PROCESBUNDEL_{clean_title}_{date_tag}.md"

    print("=" * 70)
    print("⚖️  CIVIC CASE ENGINE — FORENSIC PROCESDOSSIER BUNDLER")
    print("=" * 70)
    print(f"[*] Zaakstitel:       {args.title}")
    print(f"[*] Indiener:         {args.author}")
    print(f"[*] Wederpartij:      {args.respondent}")
    print(f"[*] Doelbestand:      {out_path}")
    print()
    print("[+] Scannen van chronologie en bewijsstukken...")
    
    res = build_case_bundle(args.title, args.author, args.respondent, out_path)
    
    print(f"[✓] Procesbundel succesvol gegenereerd:")
    print(f"    - Markdown: {res.resolve()}")
    html_f = res.with_suffix(".html")
    if html_f.exists():
        print(f"    - Printbare HTML: {html_f.resolve()}")
    print("=" * 70)

if __name__ == "__main__":
    main()
