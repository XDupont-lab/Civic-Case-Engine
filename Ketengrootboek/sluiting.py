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

# Feittypes die slechts administratieve ontvangst, doorverwijzing of stilzitten vaststellen en NOOIT een zorgpost sluiten
NIET_SLUITENDE_TYPES = {
    "ontvangstbevestiging",
    "doorverwijzing_zonder_uitvoering",
    "ontkenning_ontvangst_wmo",
    "stilzitten_schuldhulpverlening",
    "signaal_ontvangen_zonder_actie",
    "automatisch_bericht_ontvangen",
}

# Feittypes die een inter-loket tegenstrijdige registratie markeren (twee administraties sluiten elk intern maar spreken elkaar tegen)
TEGENSTRIJDIGE_FEIT_TYPES = {
    "vektis_status_n_uitsluiting",
    "betwisting_onverzekerdheid_polisoverzicht",
    "dacas_mainframe_journaalboeking",
    "bancaire_kasstroom_nulstand",
    "tegenstrijdige_registratie",
}

ONVERANDERLIJKE_LAAG1_VELDEN = ("id", "datum", "type", "actor", "omschrijving", "bewijsstuk", "sha256")


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

        # 6. Ketenintegriteitslaag: Drie afzonderlijke sluitingskenmerken (Rekenkundig, Procedureel, Materieel)
        anker_type = (anker or {}).get("type", "")
        tegen_type = (tegen or {}).get("type", "")
        is_tegenstrijdig = (
            anker_type in TEGENSTRIJDIGE_FEIT_TYPES
            or tegen_type in TEGENSTRIJDIGE_FEIT_TYPES
            or sluit_cond.get("tussen_anker_en_tegenfeit") is False
            or bool(post.get("tegenstrijdige_registratie", False))
        )

        rekenkundig_sluitend = not is_tegenstrijdig
        procedureel_gesloten = bool(
            bronpoort.get("voldaan", False)
            or (tegen is not None and tegen.get("bestand_gevonden", False))
        )
        materieel_vereffend = bool(sluit_ok and fase == FASE_3_FEITELIJKE_REALISATIE)

        if materieel_vereffend:
            keten_diagnose = "MATERIEEL_VEREFFEND"
            werklexicon_code = "KATHARSIS_VEREFFEND"
            werklexicon_toelichting = "Verplichting aantoonbaar vervuld met geldig sluitingsbewijs."
        elif not rekenkundig_sluitend:
            keten_diagnose = "TEGENSTRIJDIGE_REGISTRATIE"
            werklexicon_code = "STASIS_TEGENSTRIJDIGE_WERKELIJKHEID"
            werklexicon_toelichting = (
                f"Twee administraties boeken onderling onverenigbare feiten ({anker_id} vs. {tegen_id}), "
                "ook al sluit elke deeladministratie afzonderlijk."
            )
        elif procedureel_gesloten and not materieel_vereffend:
            keten_diagnose = "SCHIJNSLUITING"
            werklexicon_code = "ATE_LOKALE_AFSLUITING_ZONDER_KETENVERVOLG"
            werklexicon_toelichting = (
                "Het loket heeft zijn procedure of melding afgerond, maar de onderliggende verplichting "
                "is materieel niet vervuld."
            )
        else:
            keten_diagnose = "UITSTAANDE_OVERDRACHT"
            werklexicon_code = "MENIS_ONVEREFFEND_RESTANT"
            werklexicon_toelichting = "Overdracht staat zowel procedureel als materieel nog open."

        vaste_omschr = "; ".join(c.get("omschrijving", c.get("id", "")) for c in vaste_posten) or post.get("naam", "")
        overdracht_velden = {
            "bron_en_bewijs": f"{anker_id} ({(anker or {}).get('bewijsstuk', 'onbekend')})",
            "zender_naar_ontvanger": f"{post.get('debet_rekening', '')} -> {post.get('credit_rekening', '')}",
            "verplichting": vaste_omschr,
            "aanvaarding": "Ja (Fase 2/3)" if fase in (FASE_2_AANVAARDING, FASE_3_FEITELIJKE_REALISATIE) else f"Nee ({fase})",
            "uitvoering": "Voltooid" if materieel_vereffend else ("Betwist / Tegenstrijdig" if not rekenkundig_sluitend else "Niet gerealiseerd"),
            "rekenkundige_status": "Ja" if rekenkundig_sluitend else "Nee (Tegenstrijdige registraties)",
            "procedurele_status": "Ja" if procedureel_gesloten else "Nee",
            "materiele_status": "Ja" if materieel_vereffend else "Nee",
            "sluitingsbewijs": (tegen or {}).get("bewijsstuk") if materieel_vereffend else None,
        }

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
            "rekenkundig_sluitend": rekenkundig_sluitend,
            "procedureel_gesloten": procedureel_gesloten,
            "materieel_vereffend": materieel_vereffend,
            "keten_diagnose": keten_diagnose,
            "werklexicon_code": werklexicon_code,
            "werklexicon_toelichting": werklexicon_toelichting,
            "overdracht_velden": overdracht_velden,
            "anker": anker,
            "tegen": tegen,
        }

    @staticmethod
    def voeg_interpretatie_toe(
        waarneming: Dict[str, Any],
        classificatie: str,
        actor: str,
        datum: str,
        betwist: bool = True,
        werklexicon_code: str = "",
        grondslag_betwisting: str = "",
    ) -> Dict[str, Any]:
        """Laag 3 (interpretatie) toevoegen zonder Laag 1 (oorspronkelijke waarneming) te wijzigen."""
        nieuw = dict(waarneming)
        historie = list(nieuw.get("interpretatie_historie", []))
        entry: Dict[str, Any] = {
            "classificatie": classificatie,
            "actor": actor,
            "datum": datum,
            "betwist": betwist,
        }
        if werklexicon_code:
            entry["werklexicon_code"] = werklexicon_code
        if grondslag_betwisting:
            entry["grondslag_betwisting"] = grondslag_betwisting
        historie.append(entry)
        nieuw["interpretatie_historie"] = historie
        nieuw["huidige_interpretatie"] = classificatie
        nieuw["betwist"] = betwist
        return nieuw

    @staticmethod
    def verifieer_niet_overschrijving(origineel: Dict[str, Any], huidig: Dict[str, Any]) -> bool:
        """Harde systeeminvariant: een latere interpretatie mag Laag 1 nooit wijzigen of wissen."""
        for veld in ONVERANDERLIJKE_LAAG1_VELDEN:
            if veld in origineel and origineel.get(veld) != huidig.get(veld):
                raise ValueError(
                    f"NIET_OVERSCHRIJVINGS_SCHENDING: Laag-1 waarnemingsveld '{veld}' "
                    f"is gewijzigd van '{origineel.get(veld)}' naar '{huidig.get(veld)}'."
                )
        return True

    def registreer_waarneming(
        self,
        feit_id: str,
        datum: str,
        feit_type: str,
        actor: str,
        omschrijving: str,
        bewijsstuk: str,
        opslaan: bool = True,
    ) -> Dict[str, Any]:
        """Boek 1 (Memoriaal — Laag 1): Registreert een nieuwe feitelijke waarneming met SHA-256.
        Weigert een bestaand Laag-1 feit te overschrijven als de inhoud afwijkt.
        """
        journaal_pad = self.keten_dir / "journaal.json"
        feiten_lijst: List[Dict[str, Any]] = []
        if journaal_pad.is_file():
            with open(journaal_pad, "r", encoding="utf-8") as f:
                feiten_lijst = json.load(f)

        bestaand = next((item for item in feiten_lijst if item.get("id") == feit_id), None)
        nieuw_feit: Dict[str, Any] = {
            "id": feit_id,
            "datum": datum,
            "type": feit_type,
            "actor": actor,
            "omschrijving": omschrijving,
            "bewijsstuk": bewijsstuk,
            "laag": "LAAG_1_WAARNEMING",
            "interpretatie_historie": list(bestaand.get("interpretatie_historie", [])) if bestaand else [],
        }

        if bestaand is not None:
            self.verifieer_niet_overschrijving(bestaand, nieuw_feit)
            return bestaand

        b_pad = self._los_bestand_op(bewijsstuk)
        nieuw_feit["sha256"] = sha256_bestand(b_pad) if b_pad else None
        nieuw_feit["bestand_gevonden"] = bool(b_pad)

        if opslaan:
            opslag_kopie = {k: v for k, v in nieuw_feit.items() if k not in ("sha256", "bestand_gevonden")}
            feiten_lijst.append(opslag_kopie)
            with open(journaal_pad, "w", encoding="utf-8") as f:
                json.dump(feiten_lijst, f, indent=2, ensure_ascii=False)
        return nieuw_feit

    def registreer_interpretatie_op_feit(
        self,
        feit_id: str,
        classificatie: str,
        actor: str,
        datum: str,
        betwist: bool = True,
        werklexicon_code: str = "",
        grondslag_betwisting: str = "",
        opslaan: bool = True,
    ) -> Dict[str, Any]:
        """Boek 1 (Laag 3 bovenop Laag 1): Hangt een latere loket-interpretatie onder een waarneming
        zonder de oorspronkelijke waarneming in Laag 1 aan te tasten.
        """
        journaal_pad = self.keten_dir / "journaal.json"
        with open(journaal_pad, "r", encoding="utf-8") as f:
            feiten_lijst = json.load(f)

        gevonden_idx = next((i for i, item in enumerate(feiten_lijst) if item.get("id") == feit_id), None)
        if gevonden_idx is None:
            raise KeyError(f"Waarneming '{feit_id}' niet gevonden in het Memoriaal.")

        origineel = dict(feiten_lijst[gevonden_idx])
        bijgewerkt = self.voeg_interpretatie_toe(
            origineel,
            classificatie=classificatie,
            actor=actor,
            datum=datum,
            betwist=betwist,
            werklexicon_code=werklexicon_code,
            grondslag_betwisting=grondslag_betwisting,
        )
        self.verifieer_niet_overschrijving(origineel, bijgewerkt)
        feiten_lijst[gevonden_idx] = bijgewerkt

        if opslaan:
            with open(journaal_pad, "w", encoding="utf-8") as f:
                json.dump(feiten_lijst, f, indent=2, ensure_ascii=False)
        return bijgewerkt

    def bouw_rekeningen_grootboek(self) -> Dict[str, Dict[str, Any]]:
        """Boek 3 (Het Grootboek / Schuldboek van Simon Stevin):
        Reconstrueert de actuele positie per betrokken rekening/loket en koppelt elke positie
        terugwaarts aan de mutaties in het Journaal (Boek 2) en de bewijsstukken in het Memoriaal (Boek 1).
        """
        feiten_index, posten_lijst = self.laad_boeken()
        resultaten = [self.toets_post(p, feiten_index) for p in posten_lijst]
        rekeningen: Dict[str, Dict[str, Any]] = {}

        def _init_rek(naam: str) -> Dict[str, Any]:
            if naam not in rekeningen:
                rekeningen[naam] = {
                    "rekening": naam,
                    "overgedragen_posten": [],
                    "te_vervullen_posten": [],
                    "rekenkundig_sluitend": True,
                    "procedureel_gesloten": True,
                    "materieel_vereffend": True,
                    "open_verplichtingen_aantal": 0,
                    "herleidbare_bewijsstukken": [],
                }
            return rekeningen[naam]

        for r in resultaten:
            zender = r["debet"]
            ontvanger = r["credit"]
            rek_z = _init_rek(zender)
            rek_o = _init_rek(ontvanger)

            mutatie_samenvatting = {
                "post_id": r["post_id"],
                "naam": r["naam"],
                "rol": "zender (debet)",
                "tegenpartij": ontvanger,
                "rekenkundig_sluitend": r["rekenkundig_sluitend"],
                "procedureel_gesloten": r["procedureel_gesloten"],
                "materieel_vereffend": r["materieel_vereffend"],
                "keten_diagnose": r["keten_diagnose"],
                "werklexicon_code": r["werklexicon_code"],
                "anker_feit": (r.get("anker") or {}).get("id"),
                "tegen_feit": (r.get("tegen") or {}).get("id"),
            }
            rek_z["overgedragen_posten"].append(mutatie_samenvatting)

            mutatie_ontvanger = dict(mutatie_samenvatting)
            mutatie_ontvanger["rol"] = "ontvanger (credit / verplichting)"
            mutatie_ontvanger["tegenpartij"] = zender
            rek_o["te_vervullen_posten"].append(mutatie_ontvanger)

            for rek in (rek_z, rek_o):
                if not r["rekenkundig_sluitend"]:
                    rek["rekenkundig_sluitend"] = False
                if not r["procedureel_gesloten"]:
                    rek["procedureel_gesloten"] = False
                if not r["materieel_vereffend"]:
                    rek["materieel_vereffend"] = False
                    rek["open_verplichtingen_aantal"] += 1
                for feit_obj in (r.get("anker"), r.get("tegen")):
                    if feit_obj and feit_obj.get("id"):
                        spoor = f"{feit_obj['id']} ({feit_obj.get('datum', '')}) -> {feit_obj.get('bewijsstuk', '')}"
                        if spoor not in rek["herleidbare_bewijsstukken"]:
                            rek["herleidbare_bewijsstukken"].append(spoor)

        return rekeningen

    def herleid_rekening(self, zoekterm: str) -> List[Dict[str, Any]]:
        """Terugwaartse herleiding vanuit het Grootboek (Boek 3) naar Journaal (Boek 2) en Memoriaal (Boek 1)."""
        grootboek = self.bouw_rekeningen_grootboek()
        term = (zoekterm or "").strip().lower()
        return [
            data for naam, data in grootboek.items()
            if not term or term in naam.lower()
        ]

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

        # Werk saldo.json bij (inclusief Boek 3: Rekeningen-Grootboek en 3 Sluitingskenmerken)
        rekeningen_gb = self.bouw_rekeningen_grootboek()
        overzicht = self.ketenstatus_overzicht()
        saldo_data = {
            "bijgewerkt_op": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
            "schaal": "meso-bestuur / Wmo",
            "patch": "chart_wmo",
            "regime": regime,
            "ketenstatus": {
                "rekenkundig_sluitend": overzicht["rekenkundig_sluitend"],
                "procedureel_gesloten": overzicht["procedureel_gesloten"],
                "materieel_vereffend": overzicht["materieel_vereffend"],
                "schijnsluitingen": overzicht["schijnsluitingen"],
                "tegenstrijdigheden": overzicht["tegenstrijdigheden"],
            },
            "open_posten": open_posten,
            "rekeningen_grootboek": rekeningen_gb,
            "klokken": {
                "omega_star": "stil (geen getypte intake)",
                "omega_c": "actief (onpauzeerbaar lichaam / stoma / NAH)"
            },
            "eerstvolgende_handeling": "Schriftelijk wijzen op niet-sluitende post POST-WONEN-WMO-001 (noodsignaal 15 juli / ontkenning 17 juli); geen klinische herhaling aan het loket."
        }
        with open(self.keten_dir / "saldo.json", "w", encoding="utf-8") as sf:
            json.dump(saldo_data, sf, indent=2, ensure_ascii=False)

        return "\n".join(lines)

    def ketenstatus_overzicht(self) -> Dict[str, Any]:
        """Geeft de geaggregeerde ketenintegriteit (3 afzonderlijke sluitingskenmerken + diagnoses) terug."""
        feiten_index, posten_lijst = self.laad_boeken()
        resultaten = [self.toets_post(p, feiten_index) for p in posten_lijst]
        rekenkundig_ok = all(r.get("rekenkundig_sluitend", True) for r in resultaten)
        procedureel_gesloten_aantal = sum(1 for r in resultaten if r.get("procedureel_gesloten", False))
        materieel_vereffend_aantal = sum(1 for r in resultaten if r.get("materieel_vereffend", False))
        schijnsluitingen = [r["post_id"] for r in resultaten if r.get("keten_diagnose") == "SCHIJNSLUITING"]
        tegenstrijdigheden = [r["post_id"] for r in resultaten if r.get("keten_diagnose") == "TEGENSTRIJDIGE_REGISTRATIE"]
        return {
            "totaal_posten": len(resultaten),
            "rekenkundig_sluitend": rekenkundig_ok,
            "procedureel_gesloten": procedureel_gesloten_aantal == len(resultaten) and len(resultaten) > 0,
            "procedureel_gesloten_aantal": procedureel_gesloten_aantal,
            "materieel_vereffend": materieel_vereffend_aantal == len(resultaten) and len(resultaten) > 0,
            "materieel_vereffend_aantal": materieel_vereffend_aantal,
            "schijnsluitingen": schijnsluitingen,
            "tegenstrijdigheden": tegenstrijdigheden,
            "resultaten": resultaten,
        }

    def formatteer_ketenintegriteit_markdown(self) -> str:
        """Genereert het leesbare 3-Boeken Ketenintegriteitsrapport (Simon Stevin + 3 Sluitingskenmerken + Werklexicon)."""
        feiten_index, _ = self.laad_boeken()
        overzicht = self.ketenstatus_overzicht()
        rekeningen_gb = self.bouw_rekeningen_grootboek()

        rek_str = "Ja" if overzicht["rekenkundig_sluitend"] else f"Nee ({len(overzicht['tegenstrijdigheden'])} tegenstrijdige loket-registraties)"
        proc_str = f"Ja ({overzicht['procedureel_gesloten_aantal']}/{overzicht['totaal_posten']} procedureel afgerond)" if overzicht["procedureel_gesloten_aantal"] else "Nee"
        mat_str = "Ja" if overzicht["materieel_vereffend"] else f"Nee ({overzicht['materieel_vereffend_aantal']}/{overzicht['totaal_posten']} materieel vereffend)"

        md = [
            "# Ketenintegriteit & Drie-Boekenstelsel (Simon Stevin & Werklexicon)",
            "",
            "## Overzicht — Ketenstatus (3 Afzonderlijke Sluitingskenmerken)",
            "",
            f"- **Rekenkundig sluitend:** **{rek_str}**",
            f"- **Procedureel gesloten:** **{proc_str}**",
            f"- **Materieel vereffend:** **{mat_str}**",
            "",
        ]
        if overzicht["schijnsluitingen"] or overzicht["tegenstrijdigheden"]:
            md.append("> **⚠️ Schijnsluiting & Tegenstrijdige Registratie gedetecteerd:**")
            md.append("> De betrokken loketten hebben hun eigen processtap beëindigd, maar de onderliggende verplichtingen zijn materieel niet vervuld of spreken elkaar tussen loketten tegen.")
            md.append("> **Actie:** Openstaande overdracht behouden en bewijs van feitelijke uitvoering of rectificatie verlangen.")
            md.append("")

        # BOEK 3: HET GROOTBOEK / SCHULDBOEK PER REKENING (Met Terugwaartse Herleidbaarheid)
        md.extend([
            "---",
            "## Boek 3 — Het Grootboek / Schuldboek (Toestand per Loket & Terugwaartse Herleidbaarheid)",
            "",
            "| Rekening / Loket | Overgedragen (Debet) | Te vervullen (Credit) | Rekenkundig | Procedureel | Materieel | Terugwaarts Bewijsspoor (Memoriaal) |",
            "| :--- | :---: | :---: | :---: | :---: | :---: | :--- |",
        ])
        for naam, rek in rekeningen_gb.items():
            r_ok = "Ja" if rek["rekenkundig_sluitend"] else "**Nee**"
            p_ok = "Ja" if rek["procedureel_gesloten"] else "Nee"
            m_ok = "Ja" if rek["materieel_vereffend"] else f"**Nee ({rek['open_verplichtingen_aantal']} open)**"
            sporen = "<br>".join(f"`{s.split(' -> ')[0]}`" for s in rek["herleidbare_bewijsstukken"][:3])
            md.append(
                f"| **{naam}** | {len(rek['overgedragen_posten'])} | {len(rek['te_vervullen_posten'])} | {r_ok} | {p_ok} | {m_ok} | {sporen} |"
            )
        md.append("")

        # BOEK 2: HET JOURNAAL VAN OVERDRACHTEN (9 Controlevelden per Post)
        md.extend([
            "---",
            "## Boek 2 — Het Journaal (Relaties & 9 Controlevelden per Overdracht)",
            "",
        ])
        for r in overzicht["resultaten"]:
            v = r["overdracht_velden"]
            md.extend([
                f"### {r['post_id']} — {r['naam']}",
                f"- **Diagnose:** `{r['keten_diagnose']}` · **Analysecode:** `{r['werklexicon_code']}`",
                f"- **Toelichting:** {r['werklexicon_toelichting']}",
                "",
                "| Veld | Waarde |",
                "| :--- | :--- |",
                f"| **Bron en bewijs (Laag 1 Memoriaal)** | `{v['bron_en_bewijs']}` |",
                f"| **Zender → ontvanger (Laag 2 Journaal)** | {v['zender_naar_ontvanger']} |",
                f"| **Verplichting** | {v['verplichting']} |",
                f"| **Aanvaarding** | {v['aanvaarding']} |",
                f"| **Uitvoering** | {v['uitvoering']} |",
                f"| **Rekenkundige status** | **{v['rekenkundige_status']}** |",
                f"| **Procedurele status** | **{v['procedurele_status']}** |",
                f"| **Materiële status** | **{v['materiele_status']}** |",
                f"| **Sluitingsbewijs** | `{v['sluitingsbewijs'] or 'Ontbreekt — post blijft open'}` |",
                "",
            ])

        # BOEK 1: HET MEMORIAAL (Laag 1 Waarnemingen vs. Laag 3 Betwiste Interpretaties)
        md.extend([
            "---",
            "## Boek 1 — Het Memoriaal (Onveranderlijke Laag-1 Waarnemingen vs. Laag-3 Interpretaties)",
            "",
            "> **Systeeminvariant (Niet-Overschrijvingsregel):** *Een latere interpretatie of classificatie (Laag 3) mag een oorspronkelijke waarneming in het Memoriaal (Laag 1) nooit wijzigen, verwijderen of stilzwijgend vervangen.*",
            "",
        ])
        for fid, f_obj in feiten_index.items():
            h_short = (f_obj.get("sha256") or "GEEN_HASH")[:16]
            md.extend([
                f"### `{fid}` ({f_obj.get('datum', '')}) — {f_obj.get('actor', '')}",
                f"- **Laag 1 Waarneming (Immutable):** {f_obj.get('omschrijving', '')}",
                f"- **Bewijsstuk & Integriteit:** `{f_obj.get('bewijsstuk', '')}` · SHA-256: `{h_short}...`",
            ])
            interps = f_obj.get("interpretatie_historie", [])
            if interps:
                for idx, ip in enumerate(interps, 1):
                    status_lbl = "🔴 BETWISTE LOKET-INTERPRETATIE" if ip.get("betwist") else "🟢 ERKENDE INTERPRETATIE"
                    code_lbl = f" · `{ip['werklexicon_code']}`" if ip.get("werklexicon_code") else ""
                    md.append(
                        f"- **Laag 3 Interpretatie #{idx} ({status_lbl}{code_lbl}):** "
                        f"*{ip.get('actor', '')} ({ip.get('datum', '')}):* \"{ip.get('classificatie', '')}\""
                    )
                    if ip.get("grondslag_betwisting"):
                        md.append(f"  - *Weerlegging vanuit Laag 1:* {ip['grondslag_betwisting']}")
            else:
                md.append("- **Laag 3 Interpretaties:** Geen afwijkende loket-herclassificatie geregistreerd.")
            md.append("")

        return "\n".join(md)


def main():
    parser = argparse.ArgumentParser(description="Ketengrootboek — Sluiting, Proefbalans & Drie-Boekenstelsel")
    parser.add_argument("target", nargs="?", default="ALL", help="Post ID (bijv. POST-WONEN-WMO-001) of ALL voor Proefbalans")
    parser.add_argument("--json", action="store_true", help="Uitvoer als ruw JSON")
    parser.add_argument("--integriteit", action="store_true", help="Print het volledige 3-Boeken Ketenintegriteitsrapport (Markdown)")
    parser.add_argument("--rekening", type=str, default="", help="Reconstrueer een specifieke rekening vanuit het Grootboek terug naar Memoriaal")
    args = parser.parse_args()

    toetser = SluitingsToetser()

    if args.integriteit:
        print(toetser.formatteer_ketenintegriteit_markdown())
        return

    if args.rekening:
        matches = toetser.herleid_rekening(args.rekening)
        print(json.dumps(matches, indent=2, ensure_ascii=False))
        return

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
