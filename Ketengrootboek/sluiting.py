#!/usr/bin/env python3
"""
CIVIC HELPER — SLUITING, PROEFBALANS & DRIE-BOEKENSTELSEL (Ketengrootboek v2.0)
Pure Python Standard Library (Zero External Dependencies).

Implementeert het Drie-Boekenstelsel van Simon Stevin gekoppeld aan De Tafel:
  - Boek 1 (Het Memoriaal)      : memoriaal.json      (spiegel: journaal.json)
      Multimodale Laag-1 waarnemingen (PDF, WAV/MP3, e-mail, bank-CSV, zorgdossier) + SHA-256
      én Laag-3 loket-interpretaties (betwist/onbetwist).
  - Boek 2 (Het Journaal)       : boek2_journaal.json (spiegel: grootboek.json)
      Gekoppelde ketenoverdrachten (POST-...) van Debet (Zender) naar Credit (Ontvanger),
      inclusief Tafel-besluitreferentie (`tafel_besluit`) en wettelijke termijn (`termijn`).
  - Boek 3 (Het Ketengrootboek) : ketengrootboek.json (spiegel: saldo.json)
      100% automatisch afgeleide rekeningbalans per ketenpartij + De Klok (`openstaande_termijnen`).

Aanroep:
  python sluiting.py <post_id>     -> Toetst één specifieke journaalpost
  python sluiting.py ALL           -> Draait de volledige PROEFBALANS en ververst ketengrootboek.json & saldo.json
  python sluiting.py --klok        -> Toont de automatisch afgeleide Klok (openstaande termijnen & vervaldata)
  python sluiting.py --integriteit -> Print het volledige 3-Boeken Ketenintegriteitsrapport (Markdown)
  python sluiting.py --rekening X  -> Herleidt één rekening vanuit het Grootboek terug naar Journaal & Memoriaal
"""

from __future__ import annotations

import argparse
from datetime import date, datetime, timezone
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
    "ontvangstbevestiging_bezwaarschrift",
    "doorverwijzing_zonder_uitvoering",
    "ontkenning_ontvangst_wmo",
    "stilzitten_schuldhulpverlening",
    "signaal_ontvangen_zonder_actie",
    "automatisch_bericht_ontvangen",
    "termijnverlenging_art_12_3_avg",
    "schriftelijke_bevestiging_ketenbreuk_archief",
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
        self.hub_root = self.workspace_root.parent

    def _los_bestand_op(self, rel_pad: str) -> Optional[Path]:
        """Zoekt bestand lokaal in CivicHelper, Ketengrootboek of de hub-root (E:\\LLM_Workspace)."""
        if not rel_pad:
            return None
        for basis in (self.workspace_root, self.keten_dir.parent, self.keten_dir, self.hub_root):
            kandidaat = basis / rel_pad
            if kandidaat.is_file():
                return kandidaat
        return None

    def _boek1_paden(self) -> Tuple[Path, Path]:
        """Geeft (primair memoriaal.json, legacy spiegel journaal.json) terug."""
        return self.keten_dir / "memoriaal.json", self.keten_dir / "journaal.json"

    def _boek2_paden(self) -> Tuple[Path, Path]:
        """Geeft (primair boek2_journaal.json, legacy spiegel grootboek.json) terug."""
        return self.keten_dir / "boek2_journaal.json", self.keten_dir / "grootboek.json"

    def _boek3_paden(self) -> Tuple[Path, Path]:
        """Geeft (primair ketengrootboek.json, legacy spiegel saldo.json) terug."""
        return self.keten_dir / "ketengrootboek.json", self.keten_dir / "saldo.json"

    def synchroniseer_spiegelbestanden(self) -> None:
        """Houdt Boek 1 (memoriaal.json -> journaal.json) synchroon (zonder publiek grootboek.json te overschrijven)."""
        b1_prim, b1_leg = self._boek1_paden()
        if b1_prim.is_file():
            inhoud = b1_prim.read_text(encoding="utf-8")
            if not b1_leg.is_file() or b1_leg.read_text(encoding="utf-8") != inhoud:
                b1_leg.write_text(inhoud, encoding="utf-8")

    def laad_boeken(self) -> Tuple[Dict[str, Dict[str, Any]], List[Dict[str, Any]]]:
        """Laadt Boek 1 (Memoriaal) en Boek 2 (Journaal) in met multimodale SHA-256 verificatie."""
        b1_prim, b1_leg = self._boek1_paden()
        b2_prim, b2_leg = self._boek2_paden()

        memoriaal_pad = b1_prim if b1_prim.is_file() else b1_leg
        journaal_pad = b2_prim if b2_prim.is_file() else b2_leg

        feiten_lijst = []
        if memoriaal_pad.is_file():
            with open(memoriaal_pad, "r", encoding="utf-8") as f:
                feiten_lijst = json.load(f)

        if not journaal_pad.is_file():
            raise FileNotFoundError("Boek 2 (boek2_journaal.json of grootboek.json) niet gevonden")

        with open(journaal_pad, "r", encoding="utf-8") as f:
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

            # Multimodale bundel-verificatie (extra_bewijsstukken: WAV, PDF, MD, CSV)
            extra_paden = feit.get("extra_bewijsstukken", [])
            extra_hashes: Dict[str, Optional[str]] = {}
            for ep in extra_paden:
                ep_resolved = self._los_bestand_op(ep)
                extra_hashes[ep] = sha256_bestand(ep_resolved) if ep_resolved else None
            if extra_paden:
                f_copy["extra_sha256"] = extra_hashes
                f_copy["multimodale_bundel_compleet"] = all(v is not None for v in extra_hashes.values())
            else:
                f_copy["multimodale_bundel_compleet"] = f_copy["bestand_gevonden"]

            feiten_index[feit["id"]] = f_copy

        return feiten_index, posten_lijst

    @staticmethod
    def bereken_termijn_status(
        termijn: Optional[Dict[str, Any]],
        materieel_vereffend: bool,
        peildatum: Optional[date] = None,
    ) -> Optional[Dict[str, Any]]:
        """Berekent de actuele klok-status voor een overdrachtspost in Boek 2."""
        if not termijn:
            return None
        if peildatum is None:
            peildatum = datetime.now(timezone.utc).astimezone().date()

        verval_str = termijn.get("verval_datum", "")
        uiterste_str = termijn.get("uiterste_datum", verval_str)
        start_str = termijn.get("start_datum", "")

        try:
            verval_d = date.fromisoformat(verval_str)
            dagen_tot_verval = (verval_d - peildatum).days
        except ValueError:
            dagen_tot_verval = None

        try:
            uiterste_d = date.fromisoformat(uiterste_str) if uiterste_str else None
            dagen_tot_uiterste = (uiterste_d - peildatum).days if uiterste_d else None
        except ValueError:
            dagen_tot_uiterste = None

        if materieel_vereffend:
            klok_status = "AFGELETTERD"
        elif dagen_tot_verval is not None and dagen_tot_verval < 0:
            klok_status = "BUITEN_TERMIJN"
        elif dagen_tot_verval is not None and dagen_tot_verval <= 14:
            klok_status = "KRITIEK_BINNEN_14_DAGEN"
        else:
            klok_status = "LOOPT"

        return {
            "grondslag": termijn.get("grondslag", ""),
            "start_datum": start_str,
            "verval_datum": verval_str,
            "uiterste_datum": uiterste_str,
            "dagen_resterend": dagen_tot_verval,
            "dagen_tot_uiterste": dagen_tot_uiterste,
            "klok_status": klok_status,
            "vervolgstap_bij_overschrijding": termijn.get("vervolgstap_bij_overschrijding", ""),
        }

    def toets_post(
        self,
        post: Dict[str, Any],
        feiten_index: Dict[str, Dict[str, Any]],
        peildatum: Optional[date] = None,
    ) -> Dict[str, Any]:
        """Toetst één journaalpost (Boek 2) tegen de feiten in het Memoriaal (Boek 1).

        Borging tegen schijnsluiting (Sol 6.1 verwerkt):
        - Post sluit uitsluitend als het specifiek aan déze post gekoppelde tegenfeit bestaat.
        - Het tegenfeit moet een verifieerbaar bewijsstuk op schijf hebben met een geldige SHA-256 hash.
        - Het type van het tegenfeit moet exact voldoen aan de sluitingsconditie.
        - Administratieve ontvangst/ontkenning (Fase 1) sluit NOOIT een zorg- of overdrachtspost.
        """
        post_id = post.get("post_id", "ONBEKEND")
        anker_id = post.get("anker_feit")
        tegen_id = post.get("tegen_feit")
        tafel_besluit = post.get("tafel_besluit", "ONBEKEND")

        anker = feiten_index.get(anker_id)
        tegen = feiten_index.get(tegen_id)

        # 1. Toets op aanwezigheid en integriteit van het ankerbewijs (Debet-opening)
        if not anker or not anker.get("bestand_gevonden"):
            return {
                "post_id": post_id,
                "naam": post.get("naam", ""),
                "debet": post.get("debet_rekening", ""),
                "credit": post.get("credit_rekening", ""),
                "tafel_besluit": tafel_besluit,
                "fase": FASE_0_UITSTAAND,
                "vonnis": "NOG NIET GESTELD",
                "reden": f"Ankerbewijs ontbreekt of bestand niet op schijf ({anker_id})",
                "locus": ("C_onbekend", post_id, "Poort_onbekend"),
                "ontbrekend": ["anker_bewijsstuk"],
                "termijn_info": self.bereken_termijn_status(post.get("termijn"), False, peildatum),
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

        termijn_info = self.bereken_termijn_status(post.get("termijn"), materieel_vereffend, peildatum)

        vaste_omschr = "; ".join(c.get("omschrijving", c.get("id", "")) for c in vaste_posten) or post.get("naam", "")
        overdracht_velden = {
            "bron_en_bewijs": f"{anker_id} ({(anker or {}).get('bewijsstuk', 'onbekend')})",
            "zender_naar_ontvanger": f"{post.get('debet_rekening', '')} -> {post.get('credit_rekening', '')}",
            "tafel_besluit": tafel_besluit,
            "verplichting": vaste_omschr,
            "aanvaarding": "Ja (Fase 2/3)" if fase in (FASE_2_AANVAARDING, FASE_3_FEITELIJKE_REALISATIE) else f"Nee ({fase})",
            "uitvoering": "Voltooid" if materieel_vereffend else ("Betwist / Tegenstrijdig" if not rekenkundig_sluitend else "Niet gerealiseerd"),
            "rekenkundige_status": "Ja" if rekenkundig_sluitend else "Nee (Tegenstrijdige registraties)",
            "procedurele_status": "Ja" if procedureel_gesloten else "Nee",
            "materiele_status": "Ja" if materieel_vereffend else "Nee",
            "termijn_status": (
                f"{termijn_info['klok_status']} (vervalt {termijn_info['verval_datum']}, {termijn_info['dagen_resterend']} dgn)"
                if termijn_info
                else "Geen actieve klok"
            ),
            "sluitingsbewijs": (tegen or {}).get("bewijsstuk") if materieel_vereffend else None,
        }

        return {
            "post_id": post_id,
            "naam": post.get("naam", ""),
            "debet": post.get("debet_rekening", ""),
            "credit": post.get("credit_rekening", ""),
            "tafel_besluit": tafel_besluit,
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
            "termijn_info": termijn_info,
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
        modaliteit: str = "schriftelijk_bewijs",
        extra_bewijsstukken: Optional[List[str]] = None,
        opslaan: bool = True,
    ) -> Dict[str, Any]:
        """Boek 1 (Memoriaal — Laag 1): Registreert een nieuwe feitelijke multimodale waarneming met SHA-256.
        Weigert een bestaand Laag-1 feit te overschrijven als de inhoud afwijkt.
        """
        b1_prim, b1_leg = self._boek1_paden()
        lees_pad = b1_prim if b1_prim.is_file() else b1_leg
        feiten_lijst: List[Dict[str, Any]] = []
        if lees_pad.is_file():
            with open(lees_pad, "r", encoding="utf-8") as f:
                feiten_lijst = json.load(f)

        bestaand = next((item for item in feiten_lijst if item.get("id") == feit_id), None)
        nieuw_feit: Dict[str, Any] = {
            "id": feit_id,
            "datum": datum,
            "type": feit_type,
            "modaliteit": modaliteit,
            "actor": actor,
            "omschrijving": omschrijving,
            "bewijsstuk": bewijsstuk,
            "laag": "LAAG_1_WAARNEMING",
            "interpretatie_historie": list(bestaand.get("interpretatie_historie", [])) if bestaand else [],
        }
        if extra_bewijsstukken:
            nieuw_feit["extra_bewijsstukken"] = list(extra_bewijsstukken)

        if bestaand is not None:
            self.verifieer_niet_overschrijving(bestaand, nieuw_feit)
            return bestaand

        b_pad = self._los_bestand_op(bewijsstuk)
        nieuw_feit["sha256"] = sha256_bestand(b_pad) if b_pad else None
        nieuw_feit["bestand_gevonden"] = bool(b_pad)

        if opslaan:
            opslag_kopie = {k: v for k, v in nieuw_feit.items() if k not in ("sha256", "bestand_gevonden")}
            feiten_lijst.append(opslag_kopie)
            tekst = json.dumps(feiten_lijst, indent=2, ensure_ascii=False)
            b1_prim.write_text(tekst, encoding="utf-8")
            b1_leg.write_text(tekst, encoding="utf-8")
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
        b1_prim, b1_leg = self._boek1_paden()
        lees_pad = b1_prim if b1_prim.is_file() else b1_leg
        with open(lees_pad, "r", encoding="utf-8") as f:
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
            tekst = json.dumps(feiten_lijst, indent=2, ensure_ascii=False)
            b1_prim.write_text(tekst, encoding="utf-8")
            b1_leg.write_text(tekst, encoding="utf-8")
        return bijgewerkt

    def bouw_openstaande_klok(self, peildatum: Optional[date] = None) -> List[Dict[str, Any]]:
        """Afgeleide Klok-view op basis van Boek 2 (Journaal):
        Geeft alle posten met een actieve termijn gesorteerd op vervaldatum terug.
        """
        feiten_index, posten_lijst = self.laad_boeken()
        klok_items: List[Dict[str, Any]] = []
        for p in posten_lijst:
            r = self.toets_post(p, feiten_index, peildatum=peildatum)
            t_info = r.get("termijn_info")
            if t_info and not r.get("materieel_vereffend", False):
                klok_items.append({
                    "post_id": r["post_id"],
                    "naam": r["naam"],
                    "debiteur_ketenpartij": r["credit"],
                    "eiser_zender": r["debet"],
                    "tafel_besluit": r["tafel_besluit"],
                    "keten_diagnose": r["keten_diagnose"],
                    "grondslag": t_info["grondslag"],
                    "start_datum": t_info["start_datum"],
                    "verval_datum": t_info["verval_datum"],
                    "uiterste_datum": t_info["uiterste_datum"],
                    "dagen_resterend": t_info["dagen_resterend"],
                    "dagen_tot_uiterste": t_info["dagen_tot_uiterste"],
                    "klok_status": t_info["klok_status"],
                    "vervolgstap_bij_overschrijding": t_info["vervolgstap_bij_overschrijding"],
                })
        klok_items.sort(key=lambda x: (x.get("verval_datum") or "9999-12-31", x["post_id"]))
        return klok_items

    def bouw_rekeningen_grootboek(self, peildatum: Optional[date] = None) -> Dict[str, Dict[str, Any]]:
        """Boek 3 (Het Grootboek / Schuldboek van Simon Stevin):
        Reconstrueert de actuele positie per betrokken rekening/loket en koppelt elke positie
        terugwaarts aan de mutaties in het Journaal (Boek 2) en de bewijsstukken in het Memoriaal (Boek 1).
        """
        feiten_index, posten_lijst = self.laad_boeken()
        resultaten = [self.toets_post(p, feiten_index, peildatum=peildatum) for p in posten_lijst]
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
                    "lopende_termijnen": [],
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
                "tafel_besluit": r["tafel_besluit"],
                "rekenkundig_sluitend": r["rekenkundig_sluitend"],
                "procedureel_gesloten": r["procedureel_gesloten"],
                "materieel_vereffend": r["materieel_vereffend"],
                "keten_diagnose": r["keten_diagnose"],
                "werklexicon_code": r["werklexicon_code"],
                "anker_feit": (r.get("anker") or {}).get("id"),
                "tegen_feit": (r.get("tegen") or {}).get("id"),
                "termijn_info": r.get("termijn_info"),
            }
            rek_z["overgedragen_posten"].append(mutatie_samenvatting)

            mutatie_ontvanger = dict(mutatie_samenvatting)
            mutatie_ontvanger["rol"] = "ontvanger (credit / verplichting)"
            mutatie_ontvanger["tegenpartij"] = zender
            rek_o["te_vervullen_posten"].append(mutatie_ontvanger)

            if r.get("termijn_info") and not r["materieel_vereffend"]:
                rek_o["lopende_termijnen"].append({
                    "post_id": r["post_id"],
                    "verval_datum": r["termijn_info"]["verval_datum"],
                    "dagen_resterend": r["termijn_info"]["dagen_resterend"],
                    "klok_status": r["termijn_info"]["klok_status"],
                })

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

    def formatteer_klok_overzicht(self) -> str:
        """Formatteert de automatisch afgeleide Klok uit Boek 2 & Boek 3."""
        klok = self.bouw_openstaande_klok()
        lines = []
        lines.append("=" * 120)
        lines.append(f"KETENGROOTBOEK — AFGELEIDE KLOK & OPENSTAANDE TERMIJNEN ({datetime.now(timezone.utc).astimezone().strftime('%Y-%m-%d')})")
        lines.append("=" * 120)
        lines.append(f"{'Post ID':<30} | {'Ketenpartij (Credit)':<34} | {'Vervaldatum':<12} | {'Dagen':<8} | {'Status':<24}")
        lines.append("-" * 120)
        for item in klok:
            dgn = item["dagen_resterend"]
            dgn_str = f"{dgn:+d}d" if dgn is not None else "n.v.t."
            lines.append(
                f"{item['post_id']:<30} | {item['debiteur_ketenpartij'][:34]:<34} | "
                f"{item['verval_datum']:<12} | {dgn_str:<8} | {item['klok_status']:<24}"
            )
        lines.append("=" * 120)
        return "\n".join(lines)

    def formatteer_post_detail(self, resultaat: Dict[str, Any]) -> str:
        """Maakt een gedetailleerd overzicht van één post."""
        lines = []
        lines.append("=" * 80)
        lines.append(f"KETENGROOTBOEK — SLUITING VAN POST: {resultaat['post_id']}")
        lines.append("=" * 80)
        lines.append(f"Omschrijving:    {resultaat['naam']}")
        lines.append(f"Debet (Zender):  {resultaat['debet']}")
        lines.append(f"Credit (Doel):   {resultaat['credit']}")
        lines.append(f"Tafel-besluit:   {resultaat.get('tafel_besluit', 'ONBEKEND')}")
        if resultaat.get("termijn_info"):
            ti = resultaat["termijn_info"]
            lines.append(f"Termijn / Klok:  {ti['klok_status']} (vervalt {ti['verval_datum']}, uiterlijk {ti['uiterste_datum']}, {ti['dagen_resterend']} dgn)")
        lines.append("")

        ank = resultaat.get("anker")
        if ank:
            h_short = (ank.get("sha256") or "GEEN_HASH")[:16] + "..."
            lines.append(f"Ankerfeit:       {ank.get('id')} ({ank.get('datum')}) [{ank.get('modaliteit', 'tekst')}] hash={h_short}")
            lines.append(f"                 \"{ank.get('omschrijving')}\"")
        teg = resultaat.get("tegen")
        if teg:
            h_short = (teg.get("sha256") or "GEEN_HASH")[:16] + "..."
            lines.append(f"Tegenfeit:       {teg.get('id')} ({teg.get('datum')}) [{teg.get('modaliteit', 'tekst')}] hash={h_short}")
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
        """Draait de volledige proefbalans over alle journaalposten en schrijft ketengrootboek.json én saldo.json."""
        self.synchroniseer_spiegelbestanden()
        feiten_index, posten_lijst = self.laad_boeken()
        resultaten = [self.toets_post(p, feiten_index) for p in posten_lijst]

        lines = []
        lines.append("=" * 120)
        lines.append(f"PROEFBALANS VAN HET KETENGROOTBOEK (3 BOEKEN SIMON STEVIN) — {datetime.now(timezone.utc).astimezone().strftime('%Y-%m-%d %H:%M')}")
        lines.append("=" * 120)
        lines.append(f"{'Post ID':<30} | {'Debet (Zender)':<24} | {'Credit (Ontvanger)':<26} | {'Fase':<8} | {'Stand':<16}")
        lines.append("-" * 120)

        sluit_niet_aantal = 0
        sluit_wel_aantal = 0
        open_posten = []

        for r in resultaten:
            fase_kort = r.get("fase", "").split(":")[0].strip()[:8]
            lines.append(f"{r['post_id']:<30} | {r['debet'][:24]:<24} | {r['credit'][:26]:<26} | {fase_kort:<8} | {r['vonnis']:<16}")
            if r["vonnis"] == "POST SLUIT NIET":
                sluit_niet_aantal += 1
                open_posten.append(r["post_id"])
            elif r["vonnis"] == "POST SLUIT":
                sluit_wel_aantal += 1

        lines.append("-" * 120)
        regime = "HF (Frustratie)" if sluit_niet_aantal > 0 else "HK (Harmonie)"
        lines.append(f"KETENSALDO: {sluit_niet_aantal} post(en) sluiten niet | {sluit_wel_aantal} post(en) sluiten | Regime: {regime}")
        lines.append("=" * 120)

        # Werk Boek 3 bij: ketengrootboek.json én legacy spiegel saldo.json
        rekeningen_gb = self.bouw_rekeningen_grootboek()
        overzicht = self.ketenstatus_overzicht()
        openstaande_klok = self.bouw_openstaande_klok()

        eerstvolgende_klok = openstaande_klok[0] if openstaande_klok else None
        saldo_data = {
            "bijgewerkt_op": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
            "stelsel": "Simon Stevin Drie-Boekenstelsel (Boek 1: memoriaal.json -> Boek 2: boek2_journaal.json -> Boek 3: ketengrootboek.json)",
            "schaal": "meso-bestuur / Zorg / Financiën / AVG",
            "patch": "chart_integraal",
            "regime": regime,
            "ketenstatus": {
                "rekenkundig_sluitend": overzicht["rekenkundig_sluitend"],
                "procedureel_gesloten": overzicht["procedureel_gesloten"],
                "materieel_vereffend": overzicht["materieel_vereffend"],
                "schijnsluitingen": overzicht["schijnsluitingen"],
                "tegenstrijdigheden": overzicht["tegenstrijdigheden"],
            },
            "open_posten": open_posten,
            "openstaande_termijnen": openstaande_klok,
            "rekeningen_grootboek": rekeningen_gb,
            "klokken": {
                "omega_star": f"{len(openstaande_klok)} actieve ketentermijnen in Boek 3",
                "omega_c": "actief (onpauzeerbaar lichaam / stoma / NAH)"
            },
            "eerstvolgende_handeling": (
                f"{eerstvolgende_klok['post_id']} ({eerstvolgende_klok['debiteur_ketenpartij']}): "
                f"vervaldatum {eerstvolgende_klok['verval_datum']} ({eerstvolgende_klok['klok_status']})"
                if eerstvolgende_klok
                else "Geen openstaande posten."
            ),
        }

        b3_prim, b3_leg = self._boek3_paden()
        tekst = json.dumps(saldo_data, indent=2, ensure_ascii=False)
        b3_prim.write_text(tekst, encoding="utf-8")
        b3_leg.write_text(tekst, encoding="utf-8")

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
        """Genereert het leesbare 3-Boeken Ketenintegriteitsrapport (Simon Stevin + 3 Sluitingskenmerken + Klok)."""
        feiten_index, _ = self.laad_boeken()
        overzicht = self.ketenstatus_overzicht()
        rekeningen_gb = self.bouw_rekeningen_grootboek()
        klok = self.bouw_openstaande_klok()

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

        # AFGELEIDE KLOK-VIEW UIT BOEK 3
        md.extend([
            "---",
            "## De Klok — Afgeleide Termijnen-View uit Boek 2 & Boek 3",
            "",
            "| Post ID | Debiteur / Ketenpartij | Vervaldatum | Uiterste datum | Dagen | Klok-status | Tafel-besluit |",
            "| :--- | :--- | :---: | :---: | :---: | :--- | :--- |",
        ])
        for k in klok:
            dgn = k["dagen_resterend"]
            dgn_str = f"`{dgn:+d}d`" if dgn is not None else "n.v.t."
            md.append(
                f"| `{k['post_id']}` | {k['debiteur_ketenpartij']} | {k['verval_datum']} | {k['uiterste_datum']} | {dgn_str} | **{k['klok_status']}** | `{k['tafel_besluit']}` |"
            )
        md.append("")

        # BOEK 3: HET GROOTBOEK / SCHULDBOEK PER REKENING (Met Terugwaartse Herleidbaarheid)
        md.extend([
            "---",
            "## Boek 3 — Het Ketengrootboek / Schuldboek (`ketengrootboek.json`)",
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

        # BOEK 2: HET JOURNAAL VAN OVERDRACHTEN
        md.extend([
            "---",
            "## Boek 2 — Het Journaal (`boek2_journaal.json`)",
            "",
        ])
        for r in overzicht["resultaten"]:
            v = r["overdracht_velden"]
            md.extend([
                f"### {r['post_id']} — {r['naam']}",
                f"- **Diagnose:** `{r['keten_diagnose']}` · **Analysecode:** `{r['werklexicon_code']}` · **Tafel-besluit:** `{r['tafel_besluit']}`",
                f"- **Toelichting:** {r['werklexicon_toelichting']}",
                "",
                "| Veld | Waarde |",
                "| :--- | :--- |",
                f"| **Bron en bewijs (Laag 1 Memoriaal)** | `{v['bron_en_bewijs']}` |",
                f"| **Zender → ontvanger (Laag 2 Journaal)** | {v['zender_naar_ontvanger']} |",
                f"| **Tafel-kwalificatie / Autorisatie** | `{v['tafel_besluit']}` |",
                f"| **Verplichting** | {v['verplichting']} |",
                f"| **Aanvaarding** | {v['aanvaarding']} |",
                f"| **Uitvoering** | {v['uitvoering']} |",
                f"| **Rekenkundige status** | **{v['rekenkundige_status']}** |",
                f"| **Procedurele status** | **{v['procedurele_status']}** |",
                f"| **Materiële status** | **{v['materiele_status']}** |",
                f"| **Termijn / Klok** | {v['termijn_status']} |",
                f"| **Sluitingsbewijs** | `{v['sluitingsbewijs'] or 'Ontbreekt — post blijft open'}` |",
                "",
            ])

        # BOEK 1: HET MEMORIAAL (Laag 1 Waarnemingen vs. Laag 3 Betwiste Interpretaties)
        md.extend([
            "---",
            "## Boek 1 — Het Memoriaal (`memoriaal.json`: Multimodale Laag-1 Waarnemingen vs. Laag-3 Interpretaties)",
            "",
            "> **Systeeminvariant (Niet-Overschrijvingsregel):** *Een latere interpretatie of classificatie (Laag 3) mag een oorspronkelijke waarneming in het Memoriaal (Laag 1) nooit wijzigen, verwijderen of stilzwijgend vervangen.*",
            "",
        ])
        for fid, f_obj in feiten_index.items():
            h_short = (f_obj.get("sha256") or "GEEN_HASH")[:16]
            mod = f_obj.get("modaliteit", "tekst")
            extra_cnt = len(f_obj.get("extra_bewijsstukken", []))
            bundel_lbl = f" (+{extra_cnt} gekoppelde bronbestanden, bundel_ok={f_obj.get('multimodale_bundel_compleet')})" if extra_cnt else ""
            md.extend([
                f"### `{fid}` ({f_obj.get('datum', '')}) — {f_obj.get('actor', '')} [`{mod}`]",
                f"- **Laag 1 Waarneming (Immutable):** {f_obj.get('omschrijving', '')}",
                f"- **Bewijsstuk & Integriteit:** `{f_obj.get('bewijsstuk', '')}` · SHA-256: `{h_short}...`{bundel_lbl}",
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

    def bouw_chain_of_custody(self, jsonl_pad: Optional[Path] = None) -> List[Dict[str, Any]]:
        """Bouwt een cryptografische append-only hash chain over alle Laag-1 bewijsstukken in het Memoriaal.
        Conform FRE 803(6) / Art. 8:29 Awb vrije bewijslevering.
        """
        feiten_index, _ = self.laad_boeken()
        pad_uitvoer = jsonl_pad or (self.keten_dir / "chain_of_custody.jsonl")

        receipts: List[Dict[str, Any]] = []
        prev_hash = "0" * 64

        # Sorteer op datum en id voor deterministische volgorde
        gesorteerde_feiten = sorted(feiten_index.values(), key=lambda f: (f.get("datum", ""), f.get("id", "")))

        for f in gesorteerde_feiten:
            fid = f.get("id", "")
            datum = f.get("datum", "")
            actor = f.get("actor", "")
            bewijs_rel = f.get("bewijsstuk", "")
            b_pad = self._los_bestand_op(bewijs_rel) if bewijs_rel else None
            b_hash = sha256_bestand(b_pad) if (b_pad and b_pad.is_file()) else f.get("sha256", "GEEN_BESTAND")
            
            # Bepaal of de waarneming betwiste interpretaties bevat
            heeft_betwisting = any(ip.get("betwist", False) for ip in f.get("interpretatie_historie", []))
            status_vordering = "betwist" if heeft_betwisting else "vastgesteld"

            # Cryptografische hash-koppeling (SHA-256 over vorige hash + actuele payload)
            payload_str = f"{prev_hash}|{fid}|{datum}|{actor}|{bewijs_rel}|{b_hash}|{status_vordering}"
            entry_hash = hashlib.sha256(payload_str.encode("utf-8")).hexdigest()

            receipt = {
                "receipt_id": f"REC-{datum.replace('-', '')}-{fid}",
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "feit_id": fid,
                "datum": datum,
                "actor": actor,
                "bewijsstuk": bewijs_rel,
                "sha256": b_hash,
                "status_vordering": status_vordering,
                "vorige_hash": prev_hash,
                "receipt_hash": entry_hash
            }
            receipts.append(receipt)
            prev_hash = entry_hash

        # Schrijf append-only jsonl
        with open(pad_uitvoer, "w", encoding="utf-8") as out_f:
            for r in receipts:
                out_f.write(json.dumps(r, ensure_ascii=False) + "\n")

        return receipts

    def formatteer_chain_of_custody_markdown(self) -> str:
        """Genereert een menselijk leesbaar audit-rapport van de cryptografische bewijsketen."""
        receipts = self.bouw_chain_of_custody()
        md = [
            "# Ketengrootboek — Cryptografische Chain-of-Custody (Boek 1 Memoriaal)",
            "",
            f"- **Geverifieerde bewijsketen:** {len(receipts)} transacties in onafhankelijke hash chain",
            f"- **Laatste keten-hash (Tip):** `{receipts[-1]['receipt_hash'] if receipts else 'N/A'}`",
            f"- **Wettelijke grondslag bewijsbehoud:** Art. 8:29 jo. 8:39 Awb / FRE 803(6) (Self-Authenticating Record)",
            "",
            "| Receipt ID | Feit ID | Datum | Actor | Bewijsstuk (SHA-256) | Status | Receipt Hash (Chain) |",
            "|---|---|---|---|---|---|---|",
        ]
        for r in receipts:
            h_bewijs = (r["sha256"] or "")[:10] + "..." if r["sha256"] else "N/A"
            h_rec = r["receipt_hash"][:12] + "..."
            icoon = "🔴 Betwist" if r["status_vordering"] == "betwist" else "🟢 Vastgesteld"
            md.append(f"| `{r['receipt_id']}` | `{r['feit_id']}` | {r['datum']} | {r['actor']} | `{r['bewijsstuk']}` (`{h_bewijs}`) | {icoon} | `{h_rec}` |")
        return "\n".join(md)



def main():
    parser = argparse.ArgumentParser(description="Ketengrootboek — Sluiting, Proefbalans & Drie-Boekenstelsel")
    parser.add_argument("target", nargs="?", default="ALL", help="Post ID (bijv. POST-WONEN-WMO-001) of ALL voor Proefbalans")
    parser.add_argument("--json", action="store_true", help="Uitvoer als ruw JSON")
    parser.add_argument("--integriteit", action="store_true", help="Print het volledige 3-Boeken Ketenintegriteitsrapport (Markdown)")
    parser.add_argument("--custody", "--chain", action="store_true", help="Genereer en print de cryptografische Chain-of-Custody (append-only hash chain)")
    parser.add_argument("--klok", action="store_true", help="Print de automatisch afgeleide Klok (openstaande termijnen)")
    parser.add_argument("--rekening", type=str, default="", help="Reconstrueer een specifieke rekening vanuit het Grootboek terug naar Memoriaal")
    args = parser.parse_args()

    toetser = SluitingsToetser()

    if args.klok:
        if args.json:
            print(json.dumps(toetser.bouw_openstaande_klok(), indent=2, ensure_ascii=False))
        else:
            print(toetser.formatteer_klok_overzicht())
        return

    if args.integriteit:
        print(toetser.formatteer_ketenintegriteit_markdown())
        return

    if args.custody:
        if args.json:
            print(json.dumps(toetser.bouw_chain_of_custody(), indent=2, ensure_ascii=False))
        else:
            print(toetser.formatteer_chain_of_custody_markdown())
        return

    if args.rekening:
        matches = toetser.herleid_rekening(args.rekening)
        print(json.dumps(matches, indent=2, ensure_ascii=False))
        return

    if args.target.upper() == "ALL":
        print(toetser.draai_proefbalans())
    else:
        feiten_index, posten_lijst = toetser.laad_boeken()
        match = next((p for p in posten_lijst if p["post_id"] == args.target or args.target in p["post_id"]), None)
        if not match:
            print(f"FOUT: Post '{args.target}' niet gevonden in boek2_journaal.json", file=sys.stderr)
            sys.exit(1)
        res = toetser.toets_post(match, feiten_index)
        if args.json:
            print(json.dumps(res, indent=2, ensure_ascii=False))
        else:
            print(toetser.formatteer_post_detail(res))


if __name__ == "__main__":
    main()
