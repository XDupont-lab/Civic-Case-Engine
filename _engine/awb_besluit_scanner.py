#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
awb_besluit_scanner.py — Lichtgewicht Bestuursrechtelijke Besluit-Detector (Awb)
100% Python Standard Library (Zero External Dependencies).

Onderdeel van de Civic Case Engine (Batch 4 open-source adoptie).
Toetst inkomende stukken van overheidsinstanties op de formele criteria van:
- Art. 1:3 Awb: Is dit een formeel 'besluit' (schriftelijke beslissing van een bestuursorgaan, inhoudende een publiekrechtelijke rechtshandeling)?
- Art. 3:45 / 6:7 Awb: Bevat het document een rechtsmiddelenclausule (6-wekentermijn voor bezwaar/beroep)?
- Art. 6:3 Awb: Betreft het een niet-appellabele voorbereidingsbeslissing?
- Art. 4:17 Awb: Is er sprake van een termijnoverschrijding / grond voor ingebrekestelling?

VEILIGHEIDSINVARIANT (Tafel-afspraak DeepSeek & Grok):
Deze detector fungeert UITSLUITEND als signalerend waarschuwingsfilter (suggestie).
Er worden NOOIT autonoom rechten prijsgegeven of termijnen definitief geboekt zonder
expliciete menselijke bevestiging aan De Tafel (Human-in-the-Loop).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

_ENGINE_DIR = Path(__file__).resolve().parent
if str(_ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(_ENGINE_DIR))

try:
    from institutional_conditions import InstitutionalConditionsAnalyzer
    _HAS_CONDITIONS = True
except ImportError:
    _HAS_CONDITIONS = False

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Bestuursorganen (formeel bevoegd gezag)
BESTUURSORGANEN_PATRONEN = [
    (r"\bcollege van b(?:urgemeester)? en w(?:ethouders)?\b", "College van B&W"),
    (r"\bburgemeester van \w+\b", "Burgemeester"),
    (r"\bgemeente\s+[A-Z][a-z]+(?:-[A-Z][a-z]+)?\b", "Gemeente"),
    (r"\bbelastingdienst(?:\s*/\s*toeslagen)?\b", "Belastingdienst / Dienst Toeslagen"),
    (r"\bminister(?:ie)? van [A-Za-z\s]+\b", "Ministerie"),
    (r"\bhet cak\b|\bcentraal administratie kantoor\b", "Het CAK"),
    (r"\bciz\b|\bcentrum indicatiestelling zorg\b", "CIZ"),
    (r"\bnederlandse zorgautoriteit\b|\bnza\b", "NZa"),
    (r"\bautoriteit persoonsgegevens\b|\bap\b", "Autoriteit Persoonsgegevens"),
    (r"\buwv\b|\buitvoeringsinstituut werknemersverzekeringen\b", "UWV"),
    (r"\bsvb\b|\bsociale verzekeringsbank\b", "SVB"),
    (r"\bcjib\b|\bcentraal justitieel incassobureau\b", "CJIB"),
    (r"\bind\b|\bimmigratie- en naturalisatiedienst\b", "IND"),
    (r"\bduo\b|\bdienst uitvoering onderwijs\b", "DUO"),
    (r"\braad van state\b", "Raad van State"),
    (r"\bcentrale raad van beroep\b|\bcrvb\b", "Centrale Raad van Beroep"),
    (r"\brechtbank\s+[A-Za-z\s-]+\b", "Rechtbank"),
]

# Rechtsgevolg markers (publiekrechtelijke rechtshandeling die rechten/plichten wijzigt)
RECHTSGEVOLG_PATRONEN = [
    (r"\bwij hebben besloten\b|\bheeft besloten\b|\bbesluit\s*:", "Formele besluitformule"),
    (r"\bwij kennen u (?:een|de)?\s*(?:[^\.\n]+?)\s+toe\b|\bwordt toegekend\b", "Toekenning aanspraak"),
    (r"\bwij wijzen uw (?:[^\.\n]+?)\s+af\b|\bwijzen (?:wij|het) (?:[^\.\n]+?)\s+af\b|\bwordt afgewezen\b", "Afwijzing aanvraag/bezwaar"),
    (r"\bwij be[eë]indigen uw (?:[^\.\n]+?)\b|\bwordt be[eë]indigd\b", "Beëindiging recht"),
    (r"\bterugvorder(?:ing|en)? van\b|\bvorderen wij van u terug\b", "Terugvordering"),
    (r"\bherziening van uw recht\b|\bherzien wij uw\b", "Herzieningsbesluit"),
    (r"\blast onder dwangsom\b|\bbestuurlijke boete\b", "Sanctiebeschikking"),
    (r"\bvaststelling van uw (?:eigen bijdrage|verzoek|recht)\b", "Formele vaststelling"),
    (r"\bniet-ontvankelijk verklaard\b|\bverklaart het bezwaar gegrond\b|\bongegrond\b", "Beslissing op bezwaar"),
]

# Rechtsmiddelenverwijzing (art. 3:45 jo. art. 6:7 Awb)
BEZWAARCLAUSULE_PATRONEN = [
    (r"\bbinnen zes weken\b|\btermijn van 6 weken\b|\bzes weken na\b", "6-weken termijn"),
    (r"\bbezwaarschrift indienen\b|\bkunt u bezwaar maken\b|\bbezwaar aantekenen\b", "Bezwaarclausule"),
    (r"\bberoepschrift indienen\b|\bin beroep gaan bij de rechtbank\b", "Beroepsclausule"),
    (r"\bvoorlopige voorziening\b", "Voorlopige voorziening optie"),
    (r"\bgriffier van de rechtbank\b|\bsector bestuursrecht\b", "Rechtbank griffie"),
]

# Feitelijke handelingen / Informatieve mededelingen (geen rechtsgevolg)
FEITELIJK_INFORMATIEF_PATRONEN = [
    (r"\bter informatie\b|\bter kennisname\b|\bter kennisgeving\b|\bter attentie van\b", "Informatief"),
    (r"\buitnodiging voor een (?:keukentafel)?gesprek\b|\bgesprek gepland\b", "Gespreksuitnodiging"),
    (r"\bontvangstbevestiging\b", "Ontvangstbevestiging"),
    (r"\bvragen wij u om nadere informatie\b|\bvullen van de ontbrekende\b", "Informatie-uitvraag"),
    (r"\bherinnering aan uw afspraak\b", "Afspraakherinnering"),
    (r"\bbrochure\b|\bnieuwsbrief\b|\bzie bijgevoegde folder\b", "Voorlichting"),
    (r"\bgeen verdere behandeling\b", "Afdoening ter kennisname"),
]

# Voorbereidingsbeslissingen (art. 6:3 Awb)
VOORBEREIDING_PATRONEN = [
    (r"\bverslag van het (?:keukentafel)?gesprek\b|\bonderzoeksverslag\b", "Onderzoeksverslag"),
    (r"\bconcept(?:-|\s+)rapport\b|\bconcept(?:-|\s+)advies\b", "Conceptadvies"),
    (r"\btermijnverlenging\b|\bverdaging van de beslissing\b|\bart(?:ikel|\.)?\s*4:14\b", "Verdagingsbericht"),
    (r"\bbeslissen binnen \d+ weken op uw bezwaarschrift\b|\bbeslistermijn\b", "Beslistermijn art. 7:10 Awb"),
]


def scan_tekst(tekst: str, bestandsnaam: str = "Inkomend document") -> Dict[str, Any]:
    """Scant een tekstbestand of ruwe string op bestuursrechtelijke besluitkenmerken (Awb)."""
    tekst_schoon = tekst.replace("\r\n", "\n")

    bestuursorganen_gevonden = []
    for pat, label in BESTUURSORGANEN_PATRONEN:
        if re.search(pat, tekst_schoon, re.IGNORECASE):
            bestuursorganen_gevonden.append(label)

    rechtsgevolg_gevonden = []
    for pat, label in RECHTSGEVOLG_PATRONEN:
        m = re.search(pat, tekst_schoon, re.IGNORECASE)
        if m:
            rechtsgevolg_gevonden.append({"type": label, "fragment": m.group(0)})

    bezwaar_gevonden = []
    for pat, label in BEZWAARCLAUSULE_PATRONEN:
        m = re.search(pat, tekst_schoon, re.IGNORECASE)
        if m:
            bezwaar_gevonden.append({"type": label, "fragment": m.group(0)})

    feit_gevonden = []
    for pat, label in FEITELIJK_INFORMATIEF_PATRONEN:
        m = re.search(pat, tekst_schoon, re.IGNORECASE)
        if m:
            feit_gevonden.append({"type": label, "fragment": m.group(0)})

    voorbereiding_gevonden = []
    for pat, label in VOORBEREIDING_PATRONEN:
        m = re.search(pat, tekst_schoon, re.IGNORECASE)
        if m:
            voorbereiding_gevonden.append({"type": label, "fragment": m.group(0)})

    # Determinatie van classificatie
    heeft_bestuursorgaan = len(bestuursorganen_gevonden) > 0
    heeft_rechtsgevolg = len(rechtsgevolg_gevonden) > 0
    heeft_bezwaarclausule = len(bezwaar_gevonden) > 0
    is_voorbereiding = len(voorbereiding_gevonden) > 0 and not heeft_bezwaarclausule

    if heeft_rechtsgevolg and heeft_bezwaarclausule:
        classificatie = "BESLUIT_EX_ART_1_3_AWB"
        zekerheid = 0.95
        advies = "Formeel besluit vastgesteld. Bezwaartermijn van 6 weken loopt vanaf dagtekening/bekendmaking (art. 6:7 Awb)."
    elif heeft_rechtsgevolg and not heeft_bezwaarclausule:
        classificatie = "MOGELIJK_BESLUIT_ZONDER_CLAUSULE"
        zekerheid = 0.80
        advies = "Bevat rechtsgevolg maar ontbeert rechtsmiddelenverwijzing (schending art. 3:45 Awb). Termijnoverschrijding kan verschoonbaar zijn (art. 6:11 Awb)."
    elif is_voorbereiding:
        classificatie = "VOORBEREIDINGSHANDELING_ART_6_3"
        zekerheid = 0.85
        advies = "Voorbereidende handeling. Geen zelfstandig bezwaar mogelijk (art. 6:3 Awb), tenzij rechtstreeks in belang getroffen."
    elif len(feit_gevonden) > 0 and not heeft_rechtsgevolg:
        classificatie = "FEITELIJKE_MEDEDELING"
        zekerheid = 0.90
        advies = "Feitelijke of informatieve handeling. Geen rechtsgevolg; geen Awb-bezwaar mogelijk. Bij geschil eventueel klacht (hfd 9 Awb)."
    else:
        classificatie = "ONBEKEND_OF_AMBIGU"
        zekerheid = 0.50
        advies = "Geen duidelijke bestuursrechtelijke formules herkend. Beoordeel handmatig aan De Tafel."

    # Ingebrekestelling-relevantie (ontvangstbevestiging zonder besluit)
    ingebrekestelling_relevant = (
        classificatie == "FEITELIJKE_MEDEDELING" and
        any("ontvangstbevestiging" in f["type"].lower() for f in feit_gevonden)
    )

    condities = []
    if _HAS_CONDITIONS:
        try:
            condities_matches = InstitutionalConditionsAnalyzer().scan_tekst(tekst_schoon)
            condities = [m.to_dict() for m in condities_matches]
        except Exception:
            condities = []

    return {
        "document": bestandsnaam,
        "classificatie": classificatie,
        "confidence": zekerheid,
        "bestuursorgaan": bestuursorganen_gevonden[0] if bestuursorganen_gevonden else "Niet specifiek gedetecteerd",
        "rechtsgevolg_aanwezig": heeft_rechtsgevolg,
        "bezwaarclausule_aanwezig": heeft_bezwaarclausule,
        "termijn_weken": 6 if heeft_bezwaarclausule else None,
        "ingebrekestelling_relevant": ingebrekestelling_relevant,
        "institutionele_condities": condities,
        "details": {
            "bestuursorganen": list(set(bestuursorganen_gevonden)),
            "rechtsgevolg_markers": rechtsgevolg_gevonden,
            "bezwaar_markers": bezwaar_gevonden,
            "feitelijke_markers": feit_gevonden,
            "voorbereidings_markers": voorbereiding_gevonden,
        },
        "advies_tafel": advies,
        "veiligheidswaarschuwing": "⚠️ STRIKT TER BEOORDELING: Bevestig altijd handmatig aan De Tafel vóórdat bezwaartermijnen definitief worden ingeboekt."
    }


def formatteer_scanner_markdown(scan_res: Dict[str, Any]) -> str:
    """Genereert een compacte besliskaart voor De Tafel."""
    c = scan_res["classificatie"]
    icoon = {
        "BESLUIT_EX_ART_1_3_AWB": "🚨 **FORMEEL BESLUIT (Art. 1:3 Awb)**",
        "MOGELIJK_BESLUIT_ZONDER_CLAUSULE": "⚠️ **BESLUIT ZONDER BEZWAARCLAUSULE (Art. 3:45 Awb gebrek)**",
        "VOORBEREIDINGSHANDELING_ART_6_3": "ℹ️ **VOORBEREIDINGSHANDELING (Art. 6:3 Awb)**",
        "FEITELIJKE_MEDEDELING": "📄 **FEITELIJKE MEDEDELING (Geen besluit)**",
        "ONBEKEND_OF_AMBIGU": "❓ **ONBEKEND / HANDMATIG TOETSEN**",
    }.get(c, c)

    md = [
        f"### Awb Besluit-Scan: `{scan_res['document']}`",
        "",
        f"- **Classificatie:** {icoon} (Zekerheid: `{scan_res['confidence'] * 100:.0f}%`)",
        f"- **Bestuursorgaan:** {scan_res['bestuursorgaan']}",
        f"- **Rechtsgevolg:** {'Ja (publiekrechtelijk)' if scan_res['rechtsgevolg_aanwezig'] else 'Nee (informatief/operationeel)'}",
        f"- **Bezwaarclausule:** {'Ja (6-wekentermijn)' if scan_res['bezwaarclausule_aanwezig'] else 'Nee'}",
        f"- **Advies voor De Tafel:** {scan_res['advies_tafel']}",
        "",
        f"> {scan_res['veiligheidswaarschuwing']}",
        ""
    ]

    details = scan_res.get("details", {})
    if details.get("rechtsgevolg_markers"):
        md.append("**Gevonden Rechtsgevolg-formules:**")
        for m in details["rechtsgevolg_markers"]:
            md.append(f"- *{m['type']}:* `\"{m['fragment']}\"`")
        md.append("")

    if details.get("bezwaar_markers"):
        md.append("**Gevonden Bezwaar/Beroep-clausules:**")
        for m in details["bezwaar_markers"]:
            md.append(f"- *{m['type']}:* `\"{m['fragment']}\"`")
        md.append("")

    condities = scan_res.get("institutionele_condities", [])
    if condities:
        md.append("**Interne Conditie-Diagnose (Civic Engine / Protocol FH-01):**")
        for c in condities:
            md.append(f"- **{c['code']}** ({c['name_nl']}): {c['polder_principe']}")
            md.append(f"  *Polder-handreiking:* \"{c['polder_handreiking'][:160]}...\"")
        md.append("")

    return "\n".join(md)


def main():
    parser = argparse.ArgumentParser(description="Lichtgewicht Awb Besluit-Detector (Civic Case Engine)")
    parser.add_argument("input", help="Pad naar het te scannen document (.txt/.md/.eml) of directe tekst")
    parser.add_argument("--json", action="store_true", help="Uitvoer als ruw JSON")
    args = parser.parse_args()

    in_path = Path(args.input)
    if in_path.is_file():
        tekst = in_path.read_text(encoding="utf-8", errors="replace")
        titel = in_path.name
    else:
        tekst = args.input
        titel = "Directe tekst"

    res = scan_tekst(tekst, titel)

    if args.json:
        print(json.dumps(res, indent=2, ensure_ascii=False))
    else:
        print(formatteer_scanner_markdown(res))


if __name__ == "__main__":
    main()
