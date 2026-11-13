#!/usr/bin/env python3
"""Tests voor de anti-zelfinperkingstoets (AGENTS.md afspraak 5, Veto 7)."""

import sys
import unittest
from pathlib import Path

ENGINE_DIR = Path(__file__).resolve().parent
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))

from sbar_protocol import SBARProtocol
from veto_gate import VetoGate

SCHOON = (
    "Op grond van art. 15 AVG verzoek ik u om een afschrift van alle persoonsgegevens die u over mij verwerkt, "
    "vanaf aanvang registratie tot heden, inclusief maar niet beperkt tot dossiernotities, e-mails en logbestanden. "
    "Ik ontvang de stukken uitsluitend digitaal per e-mail, niet per post, binnen de wettelijke termijn van een maand."
)


class TestAvgReikwijdte(unittest.TestCase):
    def test_schoon_verzoek_slaagt(self):
        rep = SBARProtocol.validate_avg_reikwijdte(SCHOON)
        self.assertTrue(rep.is_avg_verzoek)
        self.assertTrue(rep.passed, rep.warnings)

    def test_geen_avg_tekst_wordt_niet_getoetst(self):
        rep = SBARProtocol.validate_avg_reikwijdte("Sinds 2031 woon ik in Voorbeeldstad. Ik verzoek u om een gesprek per e-mail.")
        self.assertFalse(rep.is_avg_verzoek)
        self.assertTrue(rep.passed)

    def test_a_ongevraagd_beginjaar(self):
        rep = SBARProtocol.validate_avg_reikwijdte(
            "Op grond van de AVG verzoek ik om inzage in mijn gegevens vanaf 2031, inclusief maar niet beperkt tot notities.")
        self.assertFalse(rep.passed)
        self.assertTrue(rep.treffers["a_jaargrens"])

    def test_a_over_de_periode(self):
        rep = SBARProtocol.validate_avg_reikwijdte(
            "Ik verzoek op grond van de WGBO om een kopie van mijn dossier over de periode van mijn behandeling.")
        self.assertTrue(rep.treffers["a_jaargrens"])

    def test_b_gesloten_opsomming(self):
        rep = SBARProtocol.validate_avg_reikwijdte(
            "Op grond van art. 15 AVG verzoek ik om:\n- het dossier\n- de e-mails\n- de logbestanden\n")
        self.assertFalse(rep.passed)
        self.assertTrue(rep.treffers["b_gesloten_lijst"])

    def test_b_open_opsomming_slaagt(self):
        rep = SBARProtocol.validate_avg_reikwijdte(
            "Op grond van art. 15 AVG verzoek ik om alle gegevens, inclusief maar niet beperkt tot:\n- het dossier\n- de e-mails\n")
        self.assertFalse(rep.treffers["b_gesloten_lijst"])

    def test_c_art15_lid4_concessie(self):
        rep = SBARProtocol.validate_avg_reikwijdte(
            SCHOON + " Ik begrijp dat u op grond van art. 15 lid 4 AVG gegevens van derden mag weglakken.")
        self.assertFalse(rep.passed)
        self.assertTrue(rep.treffers["c_concessie_of_uitweg"])

    def test_c_papieren_uitweg(self):
        rep = SBARProtocol.validate_avg_reikwijdte(
            SCHOON + " Lukt digitaal niet, dan ontvang ik het ook graag op papier.")
        self.assertTrue(rep.treffers["c_concessie_of_uitweg"])

    def test_c_ontkende_uitweg_slaagt(self):
        rep = SBARProtocol.validate_avg_reikwijdte(SCHOON + " Ik wens de stukken niet via een portaal te ontvangen.")
        self.assertFalse(rep.treffers["c_concessie_of_uitweg"])

    def test_d_termijn_ingeslikt(self):
        rep = SBARProtocol.validate_avg_reikwijdte(SCHOON + " Er is overigens geen haast bij.")
        self.assertTrue(rep.treffers["d_termijn_ingeslikt"])

    def test_veto_7_in_veto_gate_is_waarschuwing(self):
        tekst = "Op grond van de AVG verzoek ik uitsluitend schriftelijk om inzage in mijn gegevens vanaf 2031."
        rapport = VetoGate().check_draft(tekst)
        v7 = [r for r in rapport["results"] if r["rule"] == "VETO_7_ANTI_ZELFINPERKING"]
        self.assertEqual(len(v7), 1)
        self.assertEqual(v7[0]["severity"], "WARN")

    # Vals-alarmgevallen uit Agy's review
    def test_fp_a_achtergrondjaar_sinds(self):
        rep = SBARProtocol.validate_avg_reikwijdte(
            "Op grond van art. 15 AVG verzoek ik om alle gegevens die betrekking hebben op mijn situatie sinds 2031, "
            "vanaf aanvang registratie tot heden, inclusief maar niet beperkt tot notities.")
        self.assertFalse(rep.treffers["a_jaargrens"])

    def test_fp_a_achtergrondjaar_zonder_volledige_reikwijdte(self):
        rep = SBARProtocol.validate_avg_reikwijdte(
            "Op grond van art. 15 AVG verzoek ik om afschriften van alle stukken die betrekking hebben op mijn situatie sinds 2031.")
        self.assertFalse(rep.treffers["a_jaargrens"])

    def test_fp_b_toelichtende_periode(self):
        rep = SBARProtocol.validate_avg_reikwijdte(
            "Op grond van art. 15 AVG verzoek ik om al mijn gegevens vanaf aanvang registratie tot heden "
            "(de kern van de zaak ligt in 2029-2031), inclusief maar niet beperkt tot notities.")
        self.assertFalse(rep.treffers["a_jaargrens"])
        self.assertTrue(rep.passed, rep.warnings)

    def test_fp_c_onder_meer_is_open(self):
        for open_woord in ("onder meer", "onder andere", "waaronder"):
            rep = SBARProtocol.validate_avg_reikwijdte(
                f"Op grond van art. 15 AVG verzoek ik om alle gegevens, {open_woord}:\n- het dossier\n- de e-mails\n")
            self.assertFalse(rep.treffers["b_gesloten_lijst"], open_woord)

    def test_fp_d_lange_ontkenning_voor_portaal(self):
        rep = SBARProtocol.validate_avg_reikwijdte(
            SCHOON + " Ik maak geen gebruik van uw digitale berichtenbox of online portaal.")
        self.assertFalse(rep.treffers["c_concessie_of_uitweg"])
        self.assertTrue(rep.passed, rep.warnings)

    def test_a_in_de_jaren_en_tot_jaar_blijven_positief(self):
        for zin in ("Ik verzoek op grond van de AVG om mijn gegevens in de jaren 2029 en 2030.",
                    "Ik verzoek op grond van de AVG om mijn gegevens tot 2031."):
            self.assertTrue(SBARProtocol.validate_avg_reikwijdte(zin).treffers["a_jaargrens"], zin)

    def test_veto_7_niet_bij_schoon_verzoek(self):
        rapport = VetoGate().check_draft(SCHOON)
        regels = [r["rule"] for r in rapport["results"]]
        self.assertNotIn("VETO_7_ANTI_ZELFINPERKING", regels)


if __name__ == "__main__":
    unittest.main()
