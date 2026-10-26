#!/usr/bin/env python3
"""
CIVIC HELPER — REGRESSIETESTS KETENGROOTBOEK (v1.1)
Pure Python Standard Library (unittest).

Toetst de formele borging van sluiting en proefbalans conform de architectuurreview van Sol 6.1:
  1. Regressietest Sol 6.1: Een los intakefeit van een andere partij (bijv. Syncope)
     mag nooit een openstaande post van een andere overdracht (bijv. Woningcorporatie -> Wmo) sluiten.
  2. Ketenfasering: Een administratieve ontvangstbevestiging of ontkenning (Fase 1)
     mag een zorgpost NOOIT op groen / sluitend zetten.
  3. Bewijsplicht tegenboeking: Een tegenfeit zonder bestaand bewijsbestand op schijf
     met SHA-256 hash mag nooit tot sluiting leiden.
  4. Legitieme sluiting: Pas wanneer een specifiek aan déze post gekoppeld tegenfeit
     met bewezen bestand én vereist type aanwezig is, en alle velden/poorten kloppen,
     sluit de post (Fase 3: Feitelijke Realisatie).
"""

import copy
import json
from pathlib import Path
import tempfile
import unittest

from sluiting import SluitingsToetser, FASE_1_ONTVANGST_ONTKENNING, FASE_3_FEITELIJKE_REALISATIE


class TestKetengrootboekSluiting(unittest.TestCase):
    def setUp(self):
        self.toetser = SluitingsToetser()
        self.feiten_index, self.posten_lijst = self.toetser.laad_boeken()

    def test_regressie_sol61_vreemd_intakefeit_sluit_post_niet(self):
        """Regressietest Sol 6.1:
        In POST-WONEN-WMO-001 zetten we alle velden, poorten en Casimirs kunstmatig op groen.
        In het journaal zit EVT-SYNCOPE-20260925 (type: intake_en_actie).
        Het tegenfeit van déze post is echter EVT-WMO-20260717 (type: ontkenning_ontvangst_wmo).
        In de oude bug sloot de post omdat er 'ergens' een intake_en_actie feit bestond.
        Nu MOET de post blijven openstaan (POST SLUIT NIET).
        """
        post = copy.deepcopy(next(p for p in self.posten_lijst if p["post_id"] == "POST-WONEN-WMO-001"))
        
        # Zet alles behalve het tegenfeit kunstmatig op groen
        post["geboekte_velden"] = list(post["vereiste_velden"])
        for c in post["vaste_posten"]:
            c["in_credit_geboekt"] = True
        post["poorten"]["bronpoort"]["voldaan"] = True
        post["poorten"]["doelpoort"]["voldaan"] = True

        res = self.toetser.toets_post(post, self.feiten_index)

        self.assertEqual(res["vonnis"], "POST SLUIT NIET", "Post mag niet sluiten op een vreemd intake-feit!")
        self.assertFalse(res["tegen_feit_ok"], "tegen_feit_ok moet False zijn voor ontkenning")
        self.assertTrue(any("tegen_type_ongeldig" in item for item in res["ontbrekend"]))
        self.assertTrue(res["fase"].startswith("FASE 1"), "Ketenfase moet FASE 1 zijn")

    def test_ontvangstbevestiging_sluit_post_nooit(self):
        """Ketenfasering: Een administratieve ontvangstbevestiging (Fase 1)
        mag een zorgpost nooit sluiten, zelfs als het type overeen zou komen.
        """
        post = copy.deepcopy(next(p for p in self.posten_lijst if p["post_id"] == "POST-WONEN-WMO-001"))
        post["geboekte_velden"] = list(post["vereiste_velden"])
        for c in post["vaste_posten"]:
            c["in_credit_geboekt"] = True
        post["poorten"]["bronpoort"]["voldaan"] = True
        post["poorten"]["doelpoort"]["voldaan"] = True

        # Stel een specifieke ontvangstbevestiging in
        feiten_mock = copy.deepcopy(self.feiten_index)
        feiten_mock["EVT-BEVESTIGING-01"] = {
            "id": "EVT-BEVESTIGING-01",
            "type": "ontvangstbevestiging",
            "bestand_gevonden": True,
            "sha256": "abcdef1234567890",
            "omschrijving": "Automatische ontvangstbevestiging van de gemeente"
        }
        post["tegen_feit"] = "EVT-BEVESTIGING-01"
        post["sluitings_conditie"]["vereist_feit_type"] = "ontvangstbevestiging"

        res = self.toetser.toets_post(post, feiten_mock)
        self.assertEqual(res["vonnis"], "POST SLUIT NIET")
        self.assertFalse(res["tegen_feit_ok"])
        self.assertTrue(any("slechts_ontvangst_of_stilzitten" in item for item in res["ontbrekend"]))

    def test_tegenbewijs_zonder_bestand_blokkeert_sluiting(self):
        """Bewijsplicht: Als het tegenfeit wel het juiste type heeft,
        maar het bewijsstuk ontbreekt op schijf, mag de post niet sluiten.
        """
        post = copy.deepcopy(next(p for p in self.posten_lijst if p["post_id"] == "POST-WONEN-WMO-001"))
        post["geboekte_velden"] = list(post["vereiste_velden"])
        for c in post["vaste_posten"]:
            c["in_credit_geboekt"] = True
        post["poorten"]["bronpoort"]["voldaan"] = True
        post["poorten"]["doelpoort"]["voldaan"] = True

        feiten_mock = copy.deepcopy(self.feiten_index)
        feiten_mock["EVT-INTAKE-SPOOK"] = {
            "id": "EVT-INTAKE-SPOOK",
            "type": "intake_en_actie",
            "bestand_gevonden": False,  # Bestand ontbreekt!
            "sha256": None,
            "omschrijving": "Niet-bewezen intake"
        }
        post["tegen_feit"] = "EVT-INTAKE-SPOOK"

        res = self.toetser.toets_post(post, feiten_mock)
        self.assertEqual(res["vonnis"], "POST SLUIT NIET")
        self.assertFalse(res["tegen_feit_ok"])
        self.assertTrue(any("ontbreekt_op_schijf" in item for item in res["ontbrekend"]))

    def test_legitieme_sluiting_met_geldig_tegenfeit(self):
        """Legitieme sluiting:
        Wanneer een specifiek gekoppeld tegenfeit van het juiste type aanwezig is,
        bewezen op schijf staat, en alle velden, poorten en Casimirs kloppen,
        sluit de post met FASE 3: FEITELIJKE REALISATIE.
        """
        post = copy.deepcopy(next(p for p in self.posten_lijst if p["post_id"] == "POST-WONEN-WMO-001"))
        post["geboekte_velden"] = list(post["vereiste_velden"])
        for c in post["vaste_posten"]:
            c["in_credit_geboekt"] = True
        post["poorten"]["bronpoort"]["voldaan"] = True
        post["poorten"]["doelpoort"]["voldaan"] = True

        # Koppel een bewezen intake-feit van de Wmo
        feiten_mock = copy.deepcopy(self.feiten_index)
        feiten_mock["EVT-WMO-ECHTE-INTAKE"] = {
            "id": "EVT-WMO-ECHTE-INTAKE",
            "type": "intake_en_actie",
            "bestand_gevonden": True,
            "sha256": "d29c13b0d35f8a0a112233445566778899aabbccddeeff001122334455667788",
            "omschrijving": "Formele intake en feitelijke start ondersteuning Wmo"
        }
        post["tegen_feit"] = "EVT-WMO-ECHTE-INTAKE"

        res = self.toetser.toets_post(post, feiten_mock)
        self.assertEqual(res["vonnis"], "POST SLUIT", "Post moet sluiten bij bewezen en passende tegenboeking")
        self.assertTrue(res["tegen_feit_ok"])
        self.assertEqual(len(res["ontbrekend"]), 0)
        self.assertTrue(res["fase"].startswith("FASE 3"))
        self.assertTrue(res["rekenkundig_sluitend"])
        self.assertTrue(res["procedureel_gesloten"])
        self.assertTrue(res["materieel_vereffend"])
        self.assertEqual(res["keten_diagnose"], "MATERIEEL_VEREFFEND")

    def test_doorverwijzing_zonder_uitvoering_geeft_schijnsluiting(self):
        """Test 2: Doorverwijzing zonder aantoonbare uitvoering is procedureel gesloten,
        maar materieel NIET vereffend (SCHIJNSLUITING).
        """
        post = copy.deepcopy(next(p for p in self.posten_lijst if p["post_id"] == "POST-WONEN-WMO-001"))
        feiten_mock = copy.deepcopy(self.feiten_index)
        feiten_mock["EVT-DOORVERWIJZING-01"] = {
            "id": "EVT-DOORVERWIJZING-01",
            "type": "doorverwijzing_zonder_uitvoering",
            "bestand_gevonden": True,
            "sha256": "11223344556677889900",
            "omschrijving": "Loket verwijst door naar ander team en sluit eigen melding af.",
        }
        post["tegen_feit"] = "EVT-DOORVERWIJZING-01"
        res = self.toetser.toets_post(post, feiten_mock)
        self.assertTrue(res["rekenkundig_sluitend"])
        self.assertTrue(res["procedureel_gesloten"])
        self.assertFalse(res["materieel_vereffend"])
        self.assertEqual(res["keten_diagnose"], "SCHIJNSLUITING")
        self.assertEqual(res["werklexicon_code"], "ATE_LOKALE_AFSLUITING_ZONDER_KETENVERVOLG")

    def test_niet_overschrijvings_invariant_laag1_vs_laag3(self):
        """Test 4: Een latere interpretatie (Laag 3) mag de oorspronkelijke waarneming (Laag 1)
        nooit wijzigen, verwijderen of stilzwijgend vervangen.
        """
        origineel = copy.deepcopy(self.feiten_index["EVT-CORP-20260715"])
        met_interpretatie = self.toetser.voeg_interpretatie_toe(
            origineel,
            classificatie="Geen acute Wmo-hulpvraag volgens loket",
            actor="Sociaal Team",
            datum="2026-07-17",
            betwist=True,
        )
        # Laag 1 moet 100% intact zijn
        self.assertTrue(self.toetser.verifieer_niet_overschrijving(origineel, met_interpretatie))
        self.assertEqual(met_interpretatie["omschrijving"], origineel["omschrijving"])
        self.assertEqual(met_interpretatie["sha256"], origineel["sha256"])
        self.assertTrue(met_interpretatie["betwist"])
        self.assertEqual(
            len(met_interpretatie["interpretatie_historie"]),
            len(origineel.get("interpretatie_historie", [])) + 1,
        )

        # Poging om Laag 1 waarneming te overschrijven moet falen
        vervalst = copy.deepcopy(met_interpretatie)
        vervalst["omschrijving"] = "Cliënt had geen zorgvraag"
        with self.assertRaises(ValueError):
            self.toetser.verifieer_niet_overschrijving(origineel, vervalst)

    def test_tegenstrijdige_registraties_tussen_twee_loketten(self):
        """Test 5: Tegenstrijdige registraties bij twee loketten (bijv. Vektis Status N vs. Menzis premie-incasso)
        moeten als rekenkundig_sluitend=False en TEGENSTRIJDIGE_REGISTRATIE zichtbaar blijven,
        ook wanneer beide administraties procedureel gesloten zijn.
        """
        post_vektis = next(p for p in self.posten_lijst if p["post_id"] == "POST-VEKTIS-MENZIS-004")
        res = self.toetser.toets_post(post_vektis, self.feiten_index)
        self.assertFalse(res["rekenkundig_sluitend"])
        self.assertTrue(res["procedureel_gesloten"])
        self.assertFalse(res["materieel_vereffend"])
        self.assertEqual(res["keten_diagnose"], "TEGENSTRIJDIGE_REGISTRATIE")
        self.assertEqual(res["werklexicon_code"], "STASIS_TEGENSTRIJDIGE_WERKELIJKHEID")

    def test_drie_boeken_rekeningen_grootboek_en_terugwaartse_herleidbaarheid(self):
        """Test 6: Boek 3 (Grootboek per Rekening) reconstrueert de positie per loket
        en herleidt elke rekening terug naar het Journaal (Boek 2) en het Memoriaal (Boek 1).
        """
        grootboek = self.toetser.bouw_rekeningen_grootboek()
        self.assertGreaterEqual(len(grootboek), 5)
        wmo_rekeningen = self.toetser.herleid_rekening("wmo")
        self.assertTrue(len(wmo_rekeningen) >= 1)
        wmo = wmo_rekeningen[0]
        self.assertFalse(wmo["materieel_vereffend"])
        self.assertGreaterEqual(wmo["open_verplichtingen_aantal"], 1)
        self.assertTrue(any("EVT-" in spoor for spoor in wmo["herleidbare_bewijsstukken"]))


if __name__ == "__main__":
    unittest.main()
