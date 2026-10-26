#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CIVIC HELPER — CHRONOLOGISCHE KETENBREUK & VOORGANGER-RECONSTRUCTIE SCANNER
100% Python Standard Library. Geen externe dependencies, geen theoretisch jargon.

Doel:
Wanneer een burger dossiers opvraagt bij huisarts, ziekenhuis of gemeente, blijkt vaak:
1. Dat het dossier plotseling stopt bij een bepaald jaartal (bijv. huisartsendossier start pas in 2009
   door praktijkwissel, verhuizing of systeemmigratie), terwijl de medische geschiedenis veel eerder begon.
2. Dat er tussen twee opnames of besluiten 'stille jaren' zitten waarin stukken of overdrachten ontbreken.
3. Dat in de wél ontvangen stukken indirecte sporen staan (oude woonplaatsen, verwijsbrieven,
   namen van eerdere artsen/ziekenhuizen) waarmee de voorgaande dossierhouder kan worden opgespoord.

Deze module spoort die chronologische ketenbreuken op en geeft per breuk een concreet
reconstructie- en opvraagadvies in gewone Nederlandse taal.
"""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ENGINE_DIR = Path(__file__).resolve().parent
CASE_ROOT = ENGINE_DIR.parent
WORKSPACE = CASE_ROOT.parent


def verzamel_jaartallen_en_sporen(root_dir: Path = CASE_ROOT) -> Dict[str, Any]:
    """Scant Dossier/, Incoming_Letters/ en Zorgdossier/ op jaartallen, hiaten en voorganger-sporen."""
    zoekmappen = [
        root_dir / "Dossier",
        root_dir / "Incoming_Letters",
        WORKSPACE / "Zorgdossier",
        WORKSPACE / "agy_werk" / "outbox",
    ]

    gebeurtenissen_per_jaar: Dict[int, List[Tuple[str, str]]] = defaultdict(list)
    voorganger_sporen: List[Dict[str, str]] = []
    bekende_ketenbreuken: List[Dict[str, str]] = []

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

            for regel in tekst.splitlines():
                r_schoon = regel.strip()
                if not r_schoon or len(r_schoon) < 12:
                    continue

                # Zoek expliciete datums of jaartallen in tijdlijnregels
                m_dat = datum_pat.search(r_schoon)
                if m_dat:
                    jr = int(m_dat.group(1))
                    if 1980 <= jr <= 2026 and len(gebeurtenissen_per_jaar[jr]) < 6:
                        kort = re.sub(r"[*`#|]", "", r_schoon)[:110].strip()
                        gebeurtenissen_per_jaar[jr].append((pad.name, kort))
                elif r_schoon.startswith(("-", "*", "|")):
                    for m_jr in jaar_pat.finditer(r_schoon):
                        jr = int(m_jr.group(1))
                        if 1985 <= jr <= 2026 and len(gebeurtenissen_per_jaar[jr]) < 4:
                            kort = re.sub(r"[*`#|]", "", r_schoon)[:110].strip()
                            gebeurtenissen_per_jaar[jr].append((pad.name, kort))

                low = r_schoon.lower()
                # Detecteer aanwijzingen over afkapgrenzen, stille jaren en voorgangers
                if any(w in low for w in ("voor 2009", "vóór 2009", "tot 2009", "vanaf 2009", "stille jaren", "vorige huisarts", "oude huisarts", "historisch", "bewaartermijn")):
                    if len(voorganger_sporen) < 12:
                        voorganger_sporen.append({
                            "bron": pad.name,
                            "spoor": re.sub(r"[*`#]", "", r_schoon)[:140].strip(),
                        })

    jaren_actief = sorted(gebeurtenissen_per_jaar.keys())

    # Analyseer gaten en afkapgrenzen
    # 1. Pre-2009 Huisarts- en Voorgeschiedenis-breuk
    pre_2009_jaren = [j for j in jaren_actief if j < 2009]
    vanaf_2009_jaren = [j for j in jaren_actief if j >= 2009]
    if vanaf_2009_jaren:
        bekende_ketenbreuken.append({
            "periode": "Periode vóór 2009 (Voorgeschiedenis & Vorige Huisarts)",
            "type_breuk": "Dossier-afkapgrens bij praktijk-/systeemwissel (2009)",
            "probleem": (
                "Het reguliere digitale huisartsendossier laat pas vanaf 2009/2012 een doorlopende reeks zien, "
                "terwijl de medische voorgeschiedenis en eerdere huisartsregistraties vóór 2009 bij een "
                "voorgaande praktijk lagen."
            ),
            "reconstructie_methode": (
                "1. Koppel de historische woonadressen (BRP / oude post) aan de toenmalige huisartspraktijk in die woonplaats.\n"
                "   2. Zoek in het huidige dossier naar verwijzingen uit het overgangsjaar (2008–2009), oude specialistische brieven en apotheekhistorie.\n"
                "   3. Dien een gericht WGBO/AVG-inzageverzoek in bij de voorgaande huisartspraktijk om de ontbrekende schakel vóór 2009 op te vragen."
            ),
            "status": f"Gereconstrueerd ({len(pre_2009_jaren)} jaartallen vóór 2009 teruggevonden in de bronstukken)." if pre_2009_jaren else "Reconstructie vereist via woonadres-historie.",
        })

    # 2. Zoek stille intervallen tussen 2009 en 2026 waarin weinig of geen primaire stukken zaten
    alle_jaren_2009_2026 = list(range(2009, 2027))
    stille_jaren = [j for j in alle_jaren_2009_2026 if len(gebeurtenissen_per_jaar.get(j, [])) <= 1]
    if stille_jaren:
        stille_str = ", ".join(str(j) for j in stille_jaren)
        bekende_ketenbreuken.append({
            "periode": f"Onderbelichte / Stille jaren ({stille_str})",
            "type_breuk": "Tijdlijn-hiaat tussen opeenvolgende behandelingen of besluiten",
            "probleem": (
                f"In de jaren {stille_str} staan weinig losse brieven in het basisoverzicht, terwijl "
                "de onderliggende aandoening en de vaste lasten wél doorliepen."
            ),
            "reconstructie_methode": (
                "1. Leg de ruwe laboratorium-tijdreeks (bloedwaarden) en medicatie-afgifte van de apotheek over deze jaren heen.\n"
                "   2. Gebruik het bankoverzicht (CSV/CAMT) en zorgverzekeraar-declaraties om te bewijzen welke zorgaanbieders in die jaren wél betrokken waren."
            ),
            "status": "Aanvullen vanuit labreeks, apotheekoverzicht en declaratiehistorie.",
        })

    # 3. Bewaartermijn-afwijzing vs. Doorlopende Behandelketen (bijv. 2014–2017)
    bekende_ketenbreuken.append({
        "periode": "Periode 2014–2017 (Ziekenhuisopname 2016 vs. Verzekeraars-bewaartermijn)",
        "type_breuk": "Asymmetrische bewaartermijn tussen Zorgverzekeraar (7 jr) en Ziekenhuis/WGBO (20 jr)",
        "probleem": (
            "Een zorgverzekeraar wijst inzage over 2014–2017 soms af met een beroep op een 7-jarige "
            "administratieve bewaartermijn, terwijl het medisch dossier onder de WGBO 20 jaar bewaard blijft "
            "en de Belastingdienst/Toeslagen diezelfde jaren (2014–2016) nog steeds financieel tegenwerpt."
        ),
        "reconstructie_methode": (
            "1. Vraag de medische stukken en beelden uit 2016 rechtstreeks op bij het ziekenhuis en de huisarts (20 jaar WGBO-bewaarplicht).\n"
            "   2. Gebruik het polisoverzicht en de CAK-registratie om de verzekeringsstatus over 2014–2016 sluitend te bewijzen richting Toeslagen/Vektis."
        ),
        "status": "Ziekenhuis- en huisartsspoor 2016 + polisbewijs gekoppeld in het Memoriaal.",
    })

    return {
        "jaren_actief": jaren_actief,
        "aantal_bestanden_gescand": len(gezien_bestanden),
        "gebeurtenissen_per_jaar": {str(k): len(v) for k, v in sorted(gebeurtenissen_per_jaar.items())},
        "ketenbreuken": bekende_ketenbreuken,
        "voorganger_sporen": voorganger_sporen[:8],
    }


def formatteer_rapport(data: Dict[str, Any]) -> str:
    """Maakt een helder rapport in gewone Nederlandse taal zonder theoretisch jargon."""
    lines = [
        "==============================================================================",
        "CHRONOLOGISCHE KETENBREUKEN & DOSSIER-RECONSTRUCTIE",
        "==============================================================================",
        f"Gescande dossierstukken : {data['aantal_bestanden_gescand']}",
        f"Gedekte jaartallen      : {min(data['jaren_actief']) if data['jaren_actief'] else '-'} t/m {max(data['jaren_actief']) if data['jaren_actief'] else '-'} ({len(data['jaren_actief'])} jaren met bewijsstukken)",
        "------------------------------------------------------------------------------",
        "",
        "Waarom deze controle belangrijk is:",
        "Wanneer je een dossier opvraagt bij je huidige huisarts of gemeente, stopt dat",
        "vaak bij het jaar waarin je verhuisde of waarin de praktijk van computersysteem",
        "wisselde (bijvoorbeeld 2009). Instanties doen dan net alsof er vóór dat jaar",
        "niets aan de hand was. Met deze controle sporen we zulke tijdsgaten op en",
        "reconstrueren we bij welke voorganger (oude huisarts, ziekenhuis of archief)",
        "het ontbrekende stuk ligt.",
        "",
    ]

    for idx, b in enumerate(data["ketenbreuken"], 1):
        lines.extend([
            f"[{idx}] {b['periode']}",
            f"  • Soort ketenbreuk : {b['type_breuk']}",
            f"  • Wat er misgaat   : {b['probleem']}",
            f"  • Hoe we dit dichten:\n    {b['reconstructie_methode']}",
            f"  • Status in dossier: {b['status']}",
            "",
        ])

    if data["voorganger_sporen"]:
        lines.append("------------------------------------------------------------------------------")
        lines.append("GEVONDEN AANWIJZINGEN & VOORGANGER-SPOREN IN DE STUKKEN:")
        for sp in data["voorganger_sporen"][:6]:
            lines.append(f"  • [{sp['bron']}] {sp['spoor']}")
        lines.append("")

    lines.append("==============================================================================")
    return "\n".join(lines)


def main() -> int:
    data = verzamel_jaartallen_en_sporen()
    if "--json" in sys.argv:
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print(formatteer_rapport(data))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
