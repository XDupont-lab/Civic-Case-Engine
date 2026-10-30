#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unit tests voor awb_besluit_scanner.py."""

import unittest
from pathlib import Path
import sys

ENGINE_DIR = Path(__file__).resolve().parent
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))

from awb_besluit_scanner import scan_tekst


class TestAwbBesluitScanner(unittest.TestCase):
    def test_formeel_besluit_met_clausule(self):
        tekst = """
        College van Burgemeester en Wethouders van Gemeente Midden-Groningen
        Besluit:
        Wij wijzen uw aanvraag voor een maatwerkvoorziening Wmo af.
        Bent u het niet eens met dit besluit? Dan kunt u binnen zes weken na de verzenddatum van deze brief een bezwaarschrift indienen.
        """
        res = scan_tekst(tekst, "Wmo_Afwijzing.txt")
        self.assertEqual(res["classificatie"], "BESLUIT_EX_ART_1_3_AWB")
        self.assertTrue(res["rechtsgevolg_aanwezig"])
        self.assertTrue(res["bezwaarclausule_aanwezig"])
        self.assertEqual(res["termijn_weken"], 6)
        self.assertIn("College van B&W", res["bestuursorgaan"])
        self.assertIn("Gemeente", res["details"]["bestuursorganen"])

    def test_besluit_zonder_bezwaarclausule(self):
        tekst = """
        Belastingdienst / Dienst Toeslagen
        Wij hebben besloten uw huurtoeslag over 2024 terug te vorderen.
        Het te betalen bedrag bedraagt EUR 1.250,00.
        """
        res = scan_tekst(tekst, "Toeslagen_Terugvordering.txt")
        self.assertEqual(res["classificatie"], "MOGELIJK_BESLUIT_ZONDER_CLAUSULE")
        self.assertTrue(res["rechtsgevolg_aanwezig"])
        self.assertFalse(res["bezwaarclausule_aanwezig"])

    def test_feitelijke_mededeling_en_ingebrekestelling_flag(self):
        tekst = """
        Gemeente Groningen
        Geachte heer Dupont,
        Hierbij sturen wij u ter informatie de ontvangstbevestiging van uw brief d.d. 5 oktober.
        Wij hebben uw verzoek in goede orde ontvangen.
        """
        res = scan_tekst(tekst, "Ontvangstbevestiging.txt")
        self.assertEqual(res["classificatie"], "FEITELIJKE_MEDEDELING")
        self.assertFalse(res["rechtsgevolg_aanwezig"])
        self.assertTrue(res["ingebrekestelling_relevant"])

    def test_voorbereidingshandeling(self):
        tekst = """
        Sociaal Team
        Hierbij ontvangt u het verslag van het keukentafelgesprek van 12 september.
        Dit betreft een concept-rapport ter controle van de feiten.
        """
        res = scan_tekst(tekst, "Verslag_Keukentafel.txt")
        self.assertEqual(res["classificatie"], "VOORBEREIDINGSHANDELING_ART_6_3")
        self.assertFalse(res["rechtsgevolg_aanwezig"])


if __name__ == "__main__":
    unittest.main()
