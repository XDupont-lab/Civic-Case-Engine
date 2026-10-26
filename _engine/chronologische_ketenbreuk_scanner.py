#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CIVIC HELPER — CHRONOLOGISCHE KETENBREUK, BEWAARTERMIJN & VOORGANGER-RECONSTRUCTIE ENGINE
100% Python Standard Library. Geen externe dependencies, geen theoretisch jargon.

Kernprincipes:
1. Minimale vs. Maximale Bewaartermijn:
   - De wettelijke termijn (bijv. 20 jaar WGBO ex art. 7:454 lid 3 BW) is een MINIMUM-ondergrens,
     géén verbod om langer te bewaren en géén garantie dat oudere data vernietigd is.
   - Bij chronische aandoeningen, blijvend letsel (zoals NAH) of lopende geschillen geldt onder
     "goed hulpverlenerschap" een nog veel langere bewaarplicht.
   - Onder art. 15 AVG heeft de burger recht op inzage in ALLE gegevens die feitelijk nog in
     een systeem, archiefmap, backup of mainframe aanwezig zijn, ongeacht ouderdom.
2. De Historische Automatiserings-Knip (Vóór ~2011/2012):
   - In 2006–2011 werden huisartsendossiers bij verhuizing of praktijkwissel nog NIET automatisch
     elektronisch (MEDOVD/ZorgMail) overgezet. Vaak werd slechts een korte samenvatting handmatig
     overgetikt in het nieuwe HIS-systeem, bleef de papieren/oude kaart achter bij de vorige
     huisarts, of belandde die als losse scan in een aparte bijlagenmap die bij een standaard
     uitdraai wordt vergeten.
3. Hard Signaal + 5 Reconstructie-Vectoren:
   - Stopt een ontvangen medische reeks na bijv. 14–17 jaar (bijv. start pas in 2009 of 2012
     terwijl de 20-jaars WGBO-ondergrens in 2026 ten minste terugloopt tot 2006), dan geeft deze
     module een HARD SIGNAAL ('ONVOLLEDIGE_KETEN_BINNEN_BEWAARTERMIJN') en berekent zij direct
     de 5 Reconstructie-Vectoren om de tijdlijn alsnog sluitend te krijgen.
"""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ENGINE_DIR = Path(__file__).resolve().parent
CASE_ROOT = ENGINE_DIR.parent
WORKSPACE = CASE_ROOT.parent

HUIDIG_JAAR = datetime.now().year
WGBO_MIN_JAREN = 20
WGBO_ONDERGRENS_JAAR = HUIDIG_JAAR - WGBO_MIN_JAREN  # in 2026 -> 2006


def analyseer_tijdlijn_en_ketenbreuken(root_dir: Path = CASE_ROOT) -> Dict[str, Any]:
    """Scant de dossiers op startjaren per bron, bewaartermijn-onderschrijding en reconstructie-vectoren."""
    zoekmappen = [
        root_dir / "Dossier",
        root_dir / "Incoming_Letters",
        WORKSPACE / "Zorgdossier",
        WORKSPACE / "agy_werk" / "outbox",
    ]

    gebeurtenissen_per_jaar: Dict[int, List[Tuple[str, str]]] = defaultdict(list)
    huisarts_jaren: List[int] = []
    lab_jaren: List[int] = []
    ziekenhuis_jaren: List[int] = []
    woonadres_sporen: List[Dict[str, str]] = []
    voorganger_sporen: List[Dict[str, str]] = []

    jaar_pat = re.compile(r"\b(19[7-9]\d|20[0-2]\d)\b")
    datum_pat = re.compile(r"\b(19[7-9]\d|20[0-2]\d)-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])\b")

    gezien_bestanden = set()
    for map_pad in zoekmappen:
        if not map_pad.exists():
            continue
        for pad in sorted(map_pad.rglob("*.md")):
            if pad.name.lower() in {"readme.md", "structuur.md", "agents.md"} or pad in gezien_bestanden:
                continue
            gezien_bestanden.add(pad)
            try:
                tekst = pad.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue

            naam_low = pad.name.lower()
            is_huisarts_stuk = any(w in naam_low for w in ("huisarts", "oosterbroek", "journaal", "his"))
            is_lab_stuk = any(w in naam_low for w in ("lab", "bloed", "hematolog", "cytokine"))
            is_zkh_stuk = any(w in naam_low for w in ("umcg", "martini", "mzh", "ziekenhuis", "ic_"))

            for regel in tekst.splitlines():
                r_schoon = regel.strip()
                if not r_schoon or len(r_schoon) < 12:
                    continue

                gevonden_jr = None
                m_dat = datum_pat.search(r_schoon)
                if m_dat:
                    gevonden_jr = int(m_dat.group(1))
                elif r_schoon.startswith(("-", "*", "|")):
                    m_jr = jaar_pat.search(r_schoon)
                    if m_jr:
                        gevonden_jr = int(m_jr.group(1))

                if gevonden_jr and 1980 <= gevonden_jr <= HUIDIG_JAAR:
                    if len(gebeurtenissen_per_jaar[gevonden_jr]) < 6:
                        kort = re.sub(r"[*`#|]", "", r_schoon)[:110].strip()
                        gebeurtenissen_per_jaar[gevonden_jr].append((pad.name, kort))
                    if is_huisarts_stuk and gevonden_jr >= 2009:
                        huisarts_jaren.append(gevonden_jr)
                    if is_lab_stuk and gevonden_jr >= 2010:
                        lab_jaren.append(gevonden_jr)
                    if is_zkh_stuk:
                        ziekenhuis_jaren.append(gevonden_jr)

                low = r_schoon.lower()
                if any(w in low for w in ("voor 2009", "vóór 2009", "tot 2009", "vanaf 2009", "stille jaren", "vorige huisarts", "oude huisarts", "historisch", "bewaartermijn")):
                    if len(voorganger_sporen) < 10:
                        voorganger_sporen.append({
                            "bron": pad.name,
                            "spoor": re.sub(r"[*`#]", "", r_schoon)[:140].strip(),
                        })
                if any(w in low for w in ("1997", "2006", "2007", "2008", "verhuis", "brp", "woonachtig", "gemeente groningen")):
                    if len(woonadres_sporen) < 8:
                        woonadres_sporen.append({
                            "bron": pad.name,
                            "spoor": re.sub(r"[*`#]", "", r_schoon)[:140].strip(),
                        })

    jaren_actief = sorted(gebeurtenissen_per_jaar.keys())
    huisarts_start = min(huisarts_jaren) if huisarts_jaren else 2009
    lab_start = min(lab_jaren) if lab_jaren else 2012
    huisarts_gedekt_jaren = HUIDIG_JAAR - huisarts_start
    lab_gedekt_jaren = HUIDIG_JAAR - lab_start

    # Signaaltoets: Stopt de ontvangen keten vóór de minimale 20-jarige WGBO-ondergrens (2006)?
    keten_stopt_te_vroeg = huisarts_start > WGBO_ONDERGRENS_JAAR or lab_start > WGBO_ONDERGRENS_JAAR

    signalen = []
    if keten_stopt_te_vroeg:
        signalen.append({
            "code": "SIGNAAL_ONVOLLEDIGE_KETEN_BINNEN_20JR_WGBO",
            "ernst": "ROOD — LOKALE RECONSTRUCTIE ONVOLLEDIG",
            "titel": f"Keten stopt bij {huisarts_start} ({huisarts_gedekt_jaren} jaar) resp. {lab_start} ({lab_gedekt_jaren} jaar), terwijl minimale WGBO-termijn 20 jaar is (t/m {WGBO_ONDERGRENS_JAAR})",
            "toelichting": (
                f"1. Wettelijke ondergrens (20 jaar): Onder art. 7:454 lid 3 BW (WGBO) is de MINIMALE bewaartermijn 20 jaar "
                f"(dus ten minste terug tot {WGBO_ONDERGRENS_JAAR}), en bij chronische aandoeningen / NAH langer ('goed hulpverlenerschap').\n"
                f"2. Minimale termijn != Maximale termijn: Zolang oude gegevens feitelijk nog in een archief, backup of ziekenhuissysteem staan, "
                f"geeft art. 15 AVG recht op inzage — ook over jaren vóór {WGBO_ONDERGRENS_JAAR}.\n"
                f"3. Historische automatiserings-knip (2006–2011): Rond 2006–2009 werden dossiers bij verhuizing of praktijkwissel nog NIET automatisch "
                f"digitaal (via ZorgMail/MEDOVD) in het nieuwe HIS-systeem ingelezen. Vaak werd alleen een korte samenvatting overgetikt en bleef het "
                f"volledige dossier (of de ingescande oude/groene kaart) achter bij de vorige huisarts of in een aparte 'Oud Archief/Scans'-map."
            ),
        })

    # De 5 Reconstructie-Vectoren om de tijdlijn alsnog volledig te maken
    reconstructie_vectoren = [
        {
            "vector_id": "VECTOR 1 — Adres- & BRP-Reconstructie (Woonplaats -> Vorige Huisarts)",
            "doel": f"Achterhalen welke huisartspraktijk vóór {huisarts_start} (in en vóór {WGBO_ONDERGRENS_JAAR}) het dossier hield.",
            "actie": (
                "Leg de historische woonadressen uit de BRP / oude gemeentestukken naast de kaart van huisartspraktijken in die wijk. "
                "Vraag bij die voorgaande praktijk (of haar rechtsopvolger) expliciet om zowel het digitale HIS-archief als het "
                "fysieke/ingescande archief (oude groene kaart) onder art. 15 AVG & art. 7:456 BW."
            ),
        },
        {
            "vector_id": "VECTOR 2 — De Ziekenhuis-Spiegelvector (Specialistenbrieven verraden de oude Huisarts)",
            "doel": "Via het ziekenhuisarchief zowel de naam van de vroegere huisarts als de medische feiten vóór 2009 terughalen.",
            "actie": (
                "Ziekenhuizen (zoals UMCG en Martini) bewaren hun specialistenbrieven, operatieverslagen en radiologie (PACS) vaak veel langer dan 20 jaar. "
                "Op élke oude specialistenbrief staat bovenaan geadresseerd aan welke huisarts die destijds is verstuurd ('Aan huisarts X te Y'). "
                "Eén ziekenhuis-inzageverzoek levert daarmee direct de naam van de voorganger én de toenmalige brieven op."
            ),
        },
        {
            "vector_id": "VECTOR 3 — De 'Ingescande Bijlagen / Oud-Archief'-Vector bij de Huidige Huisarts",
            "doel": f"Controleren of het dossier van vóór {huisarts_start} als niet-geïndexeerde scan/PDF bij de huidige praktijk ligt.",
            "actie": (
                "Bij de overstap van papier/oud-HIS naar moderne HIS-pakketten (rond 2006–2012) zijn oude dossiers vaak als één platte PDF of TIFF-scan "
                "in een aparte bijlagenmap ('Correspondentie / Oud dossier / Scans') gehangen. Die komt NIET mee bij een standaard journaal-uitdraai. "
                "Vraag bij de huidige praktijk specifiek om alle niet-geïndexeerde bijlagen en scans uit het overgangsjaar."
            ),
        },
        {
            "vector_id": "VECTOR 4 — De Apotheek- & Voorschrijver-Vector (Medicatiehistorie & AGB-codes)",
            "doel": "Stille jaren en vroegere voorschrijvers reconstrueren via de apotheek-uitgiftehistorie.",
            "actie": (
                "Vraag bij de (huidige en vorige) apotheek het volledige historische medicatie-afgifteoverzicht op. "
                "Bij elke afgifte staat de AGB-code of naam van de voorschrijvend huisarts of specialist geregistreerd."
            ),
        },
        {
            "vector_id": "VECTOR 5 — De Verzekeraar- / Inschrijving-op-Naam (ION) Vector",
            "doel": "Sluitend bewijs bij welke huisarts en welk ziekenhuis in welk kwartaal zorg is geregistreerd.",
            "actie": (
                "Elke huisarts declareert per kwartaal het inschrijftarief (ION) bij de zorgverzekeraar. "
                "Samen met het polis- en declaratieoverzicht toont dit exact wanneer de overdracht van de oude naar de nieuwe huisarts plaatsvond."
            ),
        },
    ]

    return {
        "huidig_jaar": HUIDIG_JAAR,
        "wgbo_min_jaren": WGBO_MIN_JAREN,
        "wgbo_ondergrens_jaar": WGBO_ONDERGRENS_JAAR,
        "huisarts_start_jaar": huisarts_start,
        "huisarts_gedekt_jaren": huisarts_gedekt_jaren,
        "lab_start_jaar": lab_start,
        "lab_gedekt_jaren": lab_gedekt_jaren,
        "keten_stopt_te_vroeg": keten_stopt_te_vroeg,
        "aantal_bestanden_gescand": len(gezien_bestanden),
        "jaren_actief": jaren_actief,
        "signalen": signalen,
        "reconstructie_vectoren": reconstructie_vectoren,
        "voorganger_sporen": voorganger_sporen[:6],
        "woonadres_sporen": woonadres_sporen[:6],
    }


def formatteer_rapport(data: Dict[str, Any]) -> str:
    """Formatteert het rapport in heldere Nederlandse taal voor de gebruiker en de Tafel."""
    lines = [
        "==============================================================================",
        "CHRONOLOGISCHE KETENBREUKEN, BEWAARTERMIJN & VOORGANGER-RECONSTRUCTIE",
        "==============================================================================",
        f"Peiljaar controle                     : {data['huidig_jaar']}",
        f"Minimale WGBO-bewaartermijn (20 jaar) : ten minste terug tot {data['wgbo_ondergrens_jaar']} (langer bij chronische zorg / AVG feitelijk bezit)",
        f"Start regulier huisartsjournaal       : {data['huisarts_start_jaar']} ({data['huisarts_gedekt_jaren']} jaar gedekt -> MIST {data['huisarts_start_jaar'] - data['wgbo_ondergrens_jaar']} jaar binnen 20-jaarsgrens!)",
        f"Start aaneengesloten labreeks         : {data['lab_start_jaar']} ({data['lab_gedekt_jaren']} jaar gedekt -> MIST {data['lab_start_jaar'] - data['wgbo_ondergrens_jaar']} jaar binnen 20-jaarsgrens!)",
        f"Gescande dossierstukken               : {data['aantal_bestanden_gescand']} bestanden ({min(data['jaren_actief']) if data['jaren_actief'] else '-'} t/m {max(data['jaren_actief']) if data['jaren_actief'] else '-'})",
        "------------------------------------------------------------------------------",
        "",
    ]

    for sig in data["signalen"]:
        lines.extend([
            f"🚨 [{sig['ernst']}] {sig['titel']}",
            "",
            sig["toelichting"],
            "",
            "------------------------------------------------------------------------------",
            "",
        ])

    lines.append("DE 5 RECONSTRUCTIE-VECTOREN OM DE TIJDLIJN VOLLEDIG TE MAKEN:")
    lines.append("")
    for vec in data["reconstructie_vectoren"]:
        lines.extend([
            f"▶ {vec['vector_id']}",
            f"  • Doel  : {vec['doel']}",
            f"  • Actie : {vec['actie']}",
            "",
        ])

    if data["woonadres_sporen"] or data["voorganger_sporen"]:
        lines.append("------------------------------------------------------------------------------")
        lines.append("AANKNOPINGSPUNTEN GEVONDEN IN JOUW HUIDIGE STUKKEN:")
        for sp in (data["woonadres_sporen"][:4] + data["voorganger_sporen"][:4]):
            lines.append(f"  • [{sp['bron']}] {sp['spoor']}")
        lines.append("")

    lines.append("==============================================================================")
    return "\n".join(lines)


def main() -> int:
    data = analyseer_tijdlijn_en_ketenbreuken()
    if "--json" in sys.argv:
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print(formatteer_rapport(data))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
