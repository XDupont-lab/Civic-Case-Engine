#!/usr/bin/env python3
"""
CIVIC CASE ENGINE — UNIT TESTS G-TID INSTITUTIONAL FIELD ENGINE
Zero External Dependencies (unittest).
"""

import unittest
import sys
from pathlib import Path

ENGINE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ENGINE_DIR))

from gtid_engine import InstitutionalField, inspect_incoming_letter_for_gtid

class TestGTIDEngine(unittest.TestCase):

    def test_mechanical_order_detection(self):
        """Bij lage ambtelijke agency, hoge impedantie en hoge bias moet het regime MECHANISCHE_ORDE zijn."""
        field = InstitutionalField(
            entity_name="Bureaucratie X",
            w_citizen=0.4,
            w_official=0.1,
            delta_lambda=4,
            t_h=0.1,
            theta=0.6
        )
        diag = field.diagnose_summary()
        self.assertIn(diag["regime"], ["MECHANISCHE_ORDE", "BIFURCATIE_RISICO"])
        self.assertLessEqual(diag["psi_res"], 0.1)

    def test_harmonic_order_detection(self):
        """Bij hoge ambtelijke agency, lage impedantie en maatwerkruimte moet het regime HARMONISCHE_ORDE zijn."""
        field = InstitutionalField(
            entity_name="Meedenkende Consulent Y",
            w_citizen=0.5,
            w_official=0.6,
            delta_lambda=1,
            t_h=0.7,
            theta=0.1
        )
        diag = field.diagnose_summary()
        self.assertEqual(diag["regime"], "HARMONISCHE_ORDE")
        self.assertEqual(diag["operator"], "VELVET_GLOVE")
        self.assertGreater(diag["psi_res"], 0.35)

    def test_material_legitimacy_formula(self):
        """Materiële legitimiteit L = max(0, Psi_res) * w_citizen."""
        field = InstitutionalField(
            entity_name="Test",
            w_citizen=0.5,
            w_official=0.5,
            delta_lambda=1,
            t_h=0.5,
            theta=0.0
        )
        # base_pot = 0.5*0.6 + 0.5*0.4 = 0.5
        # friction = 0
        # psi_res = 0.5
        # L = 0.5 * 0.5 = 0.25
        self.assertAlmostEqual(field.psi_res, 0.5, places=2)
        self.assertAlmostEqual(field.material_legitimacy, 0.25, places=2)

    def test_ambtelijke_besluitrechtvaardiging_generation(self):
        """Genereert complete interne besluitrechtvaardiging voor de ambtenaar."""
        field = InstitutionalField(entity_name="Gemeente Westerwolde")
        hack_text = field.generate_ambtelijke_besluitrechtvaardiging(subject="Wmo Begeleiding")
        self.assertIn("G-TID AMBTELIJKE BESLUITRECHTVAARDIGING", hack_text)
        self.assertIn("Gemeente Westerwolde", hack_text)
        self.assertIn("Art. 2.3.5", hack_text)
        self.assertIn("Gws4all / Socrates", hack_text)

    def test_letter_inspection(self):
        """Inspecteert inkomende brieftekst en herkent zero-tolerance mechanische kenmerken."""
        sample = """
        Betreft: Afwijzing aanvraag.
        Naar aanleiding van uw schrijven delen wij mede dat het systeem een toekenning
        niet toestaat. Wij hanteren een strikte voorwaarde en kunnen geen uitzondering maken.
        Hoogachtend, Klantenservice Gemeente Oldambt.
        """
        field = inspect_incoming_letter_for_gtid(sample)
        self.assertEqual(field.entity_name, "Gemeente Oldambt")
        self.assertLessEqual(field.t_h, 0.2)
        self.assertGreaterEqual(field.delta_lambda, 3)

if __name__ == "__main__":
    unittest.main()
