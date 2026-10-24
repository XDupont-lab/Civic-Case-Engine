#!/usr/bin/env python3
"""
CIVIC HELPER — SLUITING & PROEFBALANS (Ketengrootboek v1.0)
Pure Python Standard Library (Zero External Dependencies).

Toetst of grootboekposten tussen instanties sluiten op basis van het journaal:
  - Post sluit      (ADMISSIBLE)      : Tegenboeking aanwezig, vaste posten behouden, velden compleet.
  - Post sluit niet (GLUING_FAILURE) : Tegenboeking ontbreekt, Casimir-verlies, poort geblokkeerd.
  - Nog niet gesteld (UNDECIDED)     : Ankerfeit of bewijsstuk ontbreekt op schijf.

Aanroep:
  python sluiting.py <post_id>   -> Toetst één specifieke grootboekpost
  python sluiting.py ALL         -> Draait de volledige PROEFBALANS en ververst saldo.json
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


def sha256_bestand(pad: Path) -> Optional[str]:
    """Berekent SHA-256 hash van een bestand indien aanwezig."""
    if not pad.is_file():
        return None
    h = hashlib.sha256()
    with open(pad, "rb") as f:
        while brokje := f.read(65536):
            h.update(brokje)
    return h.hexdigest()


# Ketenfasering van overdrachten (administratieve continuïteit vs feitelijke levering)
FASE_0_UITSTAAND = "FASE 0: UITSTAAND (Geen credit-tegenboeking geregistreerd)"
FASE_1_ONTVANGST_ONTKENNING = "FASE 1: ONTVANGST / ONTKENNING (Signaal ontvangen of afgewezen; geen zorgstart)"
FASE_2_AANVAARDING = "FASE 2: VERANTWOORDELIJKHEID AANVAARD (In onderzoek / zaaktoewijzing)"
FASE_3_FEITELIJKE_REALISATIE = "FASE 3: FEITELIJKE REALISATIE (Afgeletterd / zorg feitelijk gestart)"

# Feittypes die slechts administratieve ontvangst of stilzitten vaststellen en NOOIT een zorgpost sluiten
NIET_SLUITENDE_TYPES = {
    "ontvangstbevestiging",
    "ontkenning_ontvangst_wmo",
    "stilzitten_schuldhulpverlening",
    "signaal_ontvangen_zonder_actie",
    "automatisch_bericht_ontvangen",
}


class SluitingsToetser:
    def __init__(self, root_dir: Optional[Path] = None):
        if root_dir is None:
            self.keten_dir = Path(__file__).resolve().parent
        else:
            self.keten_dir = Path(root_dir)
        self.workspace_root = self.keten_dir.parent

    def _los_bestand_op(self, rel_pad: str) -> Optional[Path]:
        """Zoekt bestand lokaal in workspace of keten_dir."""
        if not rel_pad:
            return None
        p1 = self.workspace_root / rel_pad
        if p1.is_file():
            return p1
        p2 = self.keten_dir.parent / rel_pad
        if p2.is_file():
            return p2
        p3 = self.keten_dir / rel_pad
        if p3.is_file():
            return p3
        return None

    def laad_boeken(self) -> Tuple[Dict[str, Dict[str, Any]], List[Dict[str, Any]]]:
        """Laadt journaal en grootboek in."""
        journaal_pad = self.keten_dir / "journaal.json"
        grootboek_pad = self.keten_dir / "grootboek.json"

        if not journaal_pad.is_file() or not grootboek_pad.is_file():
            raise FileNotFoundError("journaal.json of grootboek.json niet gevonden in Ketengrootboek/")

        with open(journaal_pad, "r", encoding="utf-8") as f:
            feiten_lijst = json.load(f)
        with open(grootboek_pad, "r", encoding="utf-8") as f:
            posten_lijst = json.load(f)

        feiten_index = {}
        for feit in feiten_lijst:
            f_copy = dict(feit)
            b_pad = self._los_bestand_op(feit.get("bewijsstuk", ""))
            if b_pad:
                f_copy["sha256"] = sha256_bestand(b_pad)
                f_copy["bestand_gevonden"] = True
            else:
                f_copy["sha256"] = None
                f_copy["bestand_gevonden"] = False
            feiten_index[feit["id"]] = f_copy

        return feiten_index, posten_lijst

    def toets_post(self, post: Dict[str, Any], feiten_index: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Toetst één grootboekpost tegen de feiten in het journaal.
        
        Borging tegen schijnsluiting (Sol 6.1 verwerkt):
        - Post sluit uitsluitend als het specifiek aan déze post gekoppelde tegenfeit bestaat.
        - Het tegenfeit moet een verifieerbaar bewijsstuk op schijf hebben met een geldige SHA-256 hash.
        - Het type van het tegenfeit moet exact voldoen aan de sluitingsconditie.
        - Administratieve ontvangst/ontkenning (Fase 1) sluit NOOIT een zorg- of overdrachtspost.
        """
        post_id = post.get("post_id", "ONBEKEND")
        anker_id = post.get("anker_feit")
        tegen_id = post.get("tegen_feit")

        anker = feiten_index.get(anker_id)
        tegen = feiten_index.get(tegen_id)

        # 1. Toets op aanwezigheid en integriteit van het ankerbewijs (Debet-opening)
        if not anker or not anker.get("bestand_gevonden"):
            return {
                "post_id": post_id,
                "naam": post.get("naam", ""),
                "debet": post.get("debet_rekening", ""),
                "credit": post.get("credit_rekening", ""),
                "fase": FASE_0_UITSTAAND,
                "vonnis": "NOG NIET GESTELD",
                "reden": f"Ankerbewijs ontbreekt of bestand niet op schijf ({anker_id})",
                "locus": ("C_onbekend", post_id, "Poort_onbekend"),
                "ontbrekend": ["anker_bewijsstuk"],
                "anker": anker,
                "tegen": tegen,
            }

        # Bepaal de ketenfase op basis van het specifieke tegenfeit
        if not tegen:
            fase = FASE_0_UITSTAAND
        elif tegen.get("type") in NIET_SLUITENDE_TYPES:
            fase = FASE_1_ONTVANGST_ONTKENNING
        elif tegen.get("type") in {"onderzoek_geopend", "zaak_aanvaard", "minimapolis_toetsing", "formeel_intrekkingsbesluit_2_3_10"}:
            fase = FASE_2_AANVAARDING
        elif tegen.get("type") in {"intake_en_actie", "feitelijke_zorgstart", "levering_voltooid"}:
            fase = FASE_3_FEITELIJKE_REALISATIE
        else:
            fase = f"FASE 1: ANDERS ({tegen.get('type')})"

        # 2. Toets veldentransport (Rep-compatibiliteit)
        vereiste_velden = post.get("vereiste_velden", [])
        geboekte_velden = post.get("geboekte_velden", [])
        ontbrekende_velden = [v for v in vereiste_velden if v not in geboekte_velden]
        rep_ok = len(ontbrekende_velden) == 0

        # 3. Toets vaste posten (Casimir-behoud)
        vaste_posten = post.get("vaste_posten", [])
        verloren_casimirs = [c for c in vaste_posten if not c.get("in_credit_geboekt", False)]
        casimir_ok = len(verloren_casimirs) == 0

        # 4. Toets poorten
        poorten = post.get("poorten", {})
        bronpoort = poorten.get("bronpoort", {})
        doelpoort = poorten.get("doelpoort", {})
        poorten_ok = bronpoort.get("voldaan", False) and doelpoort.get("voldaan", False)

        # 5. Sluitingsconditie: Strikte binding aan het specifieke tegenfeit van déze post
        sluit_cond = post.get("sluitings_conditie", {})
        vereist_type = sluit_cond.get("vereist_feit_type")
        
        tegen_feit_ok = False
        tegen_gebreken = []

        if not tegen_id:
            tegen_gebreken.append("tegen_feit_niet_aangewezen_in_post")
        elif not tegen:
            tegen_gebreken.append(f"tegen_feit_{tegen_id}_niet_gevonden_in_journaal")
        elif not tegen.get("bestand_gevonden") or not tegen.get("sha256"):
            tegen_gebreken.append(f"bewijsstuk_voor_tegenfeit_{tegen_id}_ontbreekt_op_schijf")
        elif vereist_type and tegen.get("type") != vereist_type:
            tegen_gebreken.append(f"tegen_type_ongeldig({tegen.get('type')}_!=_{vereist_type})")
        elif tegen.get("type") in NIET_SLUITENDE_TYPES:
            tegen_gebreken.append(f"tegen_feit_slechts_ontvangst_of_stilzitten({tegen.get('type')})")
        else:
            tegen_feit_ok = True

        sluit_ok = rep_ok and casimir_ok and poorten_ok and tegen_feit_ok

        vonnis = "POST SLUIT" if sluit_ok else "POST SLUIT NIET"

        ontbrekend = list(ontbrekende_velden)
        for c in verloren_casimirs:
            ontbrekend.append(f"creditboeking_{c['id']}")
        if not doelpoort.get("voldaan"):
            ontbrekend.append(f"poort_{doelpoort.get('naam', 'doel')}")
        for g in tegen_gebreken:
            ontbrekend.append(g)

        locus = None
        if not sluit_ok:
            c_tag = verloren_casimirs[0]["id"] if verloren_casimirs else "C_geen"
            p_tag = doelpoort.get("naam", "Poort_doel") if not doelpoort.get("voldaan") else "Poort_ok"
            locus = (c_tag, post_id, p_tag)

        return {
            "post_id": post_id,
            "naam": post.get("naam", ""),
            "debet": post.get("debet_rekening", ""),
            "credit": post.get("credit_rekening", ""),
            "fase": fase,
            "vonnis": vonnis,
            "locus": locus,
            "ontbrekend": ontbrekend,
            "rep_ok": rep_ok,
            "casimir_ok": casimir_ok,
            "poorten_ok": poorten_ok,
            "tegen_feit_ok": tegen_feit_ok,
            "anker": anker,
            "tegen": tegen,
        }

    def formatteer_post_detail(self, resultaat: Dict[str, Any]) -> str:
        """Maakt een gedetailleerd overzicht van één post."""
        lines = []
        lines.append("=" * 80)
        lines.append(f"KETENGROOTBOEK — SLUITING VAN POST: {resultaat['post_id']}")
        lines.append("=" * 80)
        lines.append(f"Omschrijving:    {resultaat['naam']}")
        lines.append(f"Debet (Zender):  {resultaat['debet']}")
        lines.append(f"Credit (Doel):   {resultaat['credit']}")
        lines.append("")

        ank = resultaat.get("anker")
        if ank:
            h_short = (ank.get("sha256") or "GEEN_HASH")[:16] + "..."
            lines.append(f"Ankerfeit:       {ank.get('id')} ({ank.get('datum')}) hash={h_short}")
            lines.append(f"                 \"{ank.get('omschrijving')}\"")
        teg = resultaat.get("tegen")
        if teg:
            h_short = (teg.get("sha256") or "GEEN_HASH")[:16] + "..."
            lines.append(f"Tegenfeit:       {teg.get('id')} ({teg.get('datum')}) hash={h_short}")
            lines.append(f"                 \"{teg.get('omschrijving')}\"")

        lines.append("")
        lines.append("-" * 80)
        lines.append(f"VONNIS:          {resultaat['vonnis']}")
        lines.append(f"Ketenfase:       {resultaat.get('fase', 'ONBEKEND')}")
        if resultaat.get("locus"):
            l = resultaat["locus"]
            lines.append(f"Locus breuk:     ({l[0]}, {l[1]}, {l[2]})")
        lines.append(f"Ontbrekend:      [{', '.join(resultaat.get('ontbrekend', []))}]")
        lines.append("=" * 80)
        return "\n".join(lines)

    def draai_proefbalans(self) -> str:
        """Draait de volledige proefbalans over alle grootboekposten en schrijft saldo.json."""
        feiten_index, posten_lijst = self.laad_boeken()
        resultaten = [self.toets_post(p, feiten_index) for p in posten_lijst]

        lines = []
        lines.append("=" * 115)
        lines.append(f"PROEFBALANS VAN HET KETENGROOTBOEK — {datetime.now(timezone.utc).astimezone().strftime('%Y-%m-%d %H:%M')}")
        lines.append("=" * 115)
        lines.append(f"{'Post ID':<23} | {'Debet (Zender)':<24} | {'Credit (Ontvanger)':<24} | {'Fase':<8} | {'Stand':<16}")
        lines.append("-" * 115)

        sluit_niet_aantal = 0
        sluit_wel_aantal = 0
        open_posten = []

        for r in resultaten:
            fase_kort = r.get("fase", "").split(":")[0].strip()[:8]  # bijv. "FASE 1"
            lines.append(f"{r['post_id']:<23} | {r['debet'][:24]:<24} | {r['credit'][:24]:<24} | {fase_kort:<8} | {r['vonnis']:<16}")
            if r["vonnis"] == "POST SLUIT NIET":
                sluit_niet_aantal += 1
                open_posten.append(r["post_id"])
            elif r["vonnis"] == "POST SLUIT":
                sluit_wel_aantal += 1

        lines.append("-" * 115)
        regime = "HF (Frustratie)" if sluit_niet_aantal > 0 else "HK (Harmonie)"
        lines.append(f"KETENSALDO: {sluit_niet_aantal} post(en) sluiten niet | {sluit_wel_aantal} post(en) sluiten | Regime: {regime}")
        lines.append("=" * 115)

        # Werk saldo.json bij
        saldo_data = {
            "bijgewerkt_op": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
            "schaal": "meso-bestuur / Wmo",
            "patch": "chart_wmo",
            "regime": regime,
            "open_posten": open_posten,
            "klokken": {
                "omega_star": "stil (geen getypte intake)",
                "omega_c": "actief (onpauzeerbaar lichaam / stoma / NAH)"
            },
            "eerstvolgende_handeling": "Schriftelijk wijzen op niet-sluitende post POST-WONEN-WMO-001 (noodsignaal 15 juli / ontkenning 17 juli); geen klinische herhaling aan het loket."
        }
        with open(self.keten_dir / "saldo.json", "w", encoding="utf-8") as sf:
            json.dump(saldo_data, sf, indent=2, ensure_ascii=False)

        return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Ketengrootboek — Sluiting & Proefbalans")
    parser.add_argument("target", nargs="?", default="ALL", help="Post ID (bijv. POST-WONEN-WMO-001) of ALL voor Proefbalans")
    parser.add_argument("--json", action="store_true", help="Uitvoer als ruw JSON")
    args = parser.parse_args()

    toetser = SluitingsToetser()

    if args.target.upper() == "ALL":
        print(toetser.draai_proefbalans())
    else:
        feiten_index, posten_lijst = toetser.laad_boeken()
        # Zoek match op post_id of iface id
        match = next((p for p in posten_lijst if p["post_id"] == args.target or args.target in p["post_id"]), None)
        if not match:
            print(f"FOUT: Post '{args.target}' niet gevonden in grootboek.json", file=sys.stderr)
            sys.exit(1)
        res = toetser.toets_post(match, feiten_index)
        if args.json:
            print(json.dumps(res, indent=2, ensure_ascii=False))
        else:
            print(toetser.formatteer_post_detail(res))


if __name__ == "__main__":
    main()
