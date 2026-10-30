#!/usr/bin/env python3
"""
Unit tests voor institutional_conditions.py
Toetst de detectie van de 5 Nederlandse institutionele condities en de Fluwelen Handschoen / Polder-vertaling.
"""

from pathlib import Path
import sys
import unittest

ENGINE_DIR = Path(__file__).resolve().parent
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))

from institutional_conditions import (
    InstitutionalConditionsAnalyzer,
    CONDITIES_TAXONOMIE,
    ConditionMatch,
    NEDERLANDSE_TERMEN,
)


class TestInstitutionalConditions(unittest.TestCase):
    def setUp(self):
        self.analyzer = InstitutionalConditionsAnalyzer()

    def test_lastenverplaatsing_detection(self):
        tekst = """
        Geachte burger,
        Wij hebben uw gegevens nog niet aangetroffen in ons zaaksysteem.
        Kunt u ons alsnog een kopie toezenden van de salarisspecificaties over 2017?
        Met vriendelijke groet,
        Afdeling Personeel & Financiën
        """
        matches = self.analyzer.scan_tekst(tekst, context={"datum": "14 september 2026", "kenmerk": "ZK-VOORBEELD-001"})
        codes_nl = [m.code for m in matches]
        codes_en = [m.code_en for m in matches]
        self.assertIn("LASTENVERPLAATSING", codes_nl)
        self.assertIn("TRANSFER_OF_BURDEN", codes_en)
        
        m_burden = next(m for m in matches if m.code == "LASTENVERPLAATSING")
        self.assertGreaterEqual(m_burden.confidence, 0.70)
        self.assertIn("Om u zoekwerk in het archief te besparen", m_burden.polder_handreiking)
        self.assertIn("ZK-VOORBEELD-001", m_burden.polder_handreiking)

    def test_loketomleiding_detection(self):
        tekst = """
        Geachte burger,
        Wij zijn niet bevoegd om dit verzoek te behandelen.
        Dit verzoek kunt u uitsluitend via het portaal met DigiD indienen.
        Daarom verwijzen wij u door naar het algemene loket.
        """
        matches = self.analyzer.scan_tekst(tekst, context={"onderwerp": "Wmo indicatie", "doel_loket": "Sociaal Team"})
        codes_nl = [m.code for m in matches]
        codes_en = [m.code_en for m in matches]
        self.assertIn("LOKETOMLEIDING", codes_nl)
        self.assertIn("PROCEDURAL_DEFLECTION", codes_en)

        m_deflect = next(m for m in matches if m.code == "LOKETOMLEIDING")
        self.assertIn("Dank voor uw toelichting over de interne bevoegdheidsverdeling", m_deflect.polder_handreiking)
        self.assertIn("Sociaal Team", m_deflect.polder_handreiking)

    def test_termijnoverschrijding_and_dossier_amnesie(self):
        tekst = """
        Geachte betrokkene,
        Wegens grote achterstanden en drukke werkzaamheden hebben wij nog geen beslissing kunnen nemen.
        Onze excuses voor de vertraging.
        """
        ctx = {
            "eerdere_contacten_count": 4,
            "dagen_openstaand": 65,
            "wettelijke_termijn_dagen": 42,
            "datum_verval": "15 oktober 2026",
            "datum_voorstel": "10 november 2026"
        }
        matches = self.analyzer.scan_tekst(tekst, context=ctx)
        codes_nl = [m.code for m in matches]
        codes_en = [m.code_en for m in matches]
        self.assertIn("TERMIJNOVERSCHRIJDING", codes_nl)
        self.assertIn("INSTITUTIONAL_DELAY", codes_en)
        self.assertIn("DOSSIER_AMNESIE", codes_nl)
        self.assertIn("REPEATED_CONTACT_WITHOUT_RESOLUTION", codes_en)

    def test_urgentiekloof_detection(self):
        tekst = """
        Geachte betrokkene,
        Uw melding volgt de normale procedure en staat op de wachtlijst.
        Er is geen voorrang mogelijk.
        """
        ctx = {
            "medische_urgentie_verhoogd": True,
            "spoed_afgewezen": True,
            "behandelaar": "Dr. De Vries",
            "datum_diagnose": "28 oktober 2026"
        }
        matches = self.analyzer.scan_tekst(tekst, context=ctx)
        codes_nl = [m.code for m in matches]
        codes_en = [m.code_en for m in matches]
        self.assertIn("URGENTIEKLOOF", codes_nl)
        self.assertIn("ESCALATION_WITHOUT_RESPONSE", codes_en)

    def test_polder_phrasing_strictly_avoids_adversarial_words(self):
        """Controleert dat de Polder-vertaling 100% vrij is van strijdbare/demoniserende taal."""
        dummy_text = "kunt u ons een kopie toezenden. wij zijn niet bevoegd. wegens grote achterstanden."
        matches = self.analyzer.scan_tekst(dummy_text)
        
        for m in matches:
            handreiking = m.polder_handreiking.lower()
            for verboden in m.verboden_toon:
                self.assertNotIn(verboden.lower(), handreiking, f"Verboden toon '{verboden}' aangetroffen in handreiking!")
            # Geen vijandige labels in uitgaande tekst
            self.assertNotIn("nalatig", handreiking)
            self.assertNotIn("aanklacht", handreiking)
            self.assertNotIn("schuld", handreiking)
            self.assertNotIn("tegenstander", handreiking)

    def test_nederlandse_glossarium_termen(self):
        """Controleert dat alle analytische signaalbegrippen netjes in het Nederlands vertaald zijn."""
        self.assertEqual(NEDERLANDSE_TERMEN["Evidence Strength"], "Bewijskracht")
        self.assertEqual(NEDERLANDSE_TERMEN["Deadline Pressure"], "Termijndruk")
        self.assertEqual(NEDERLANDSE_TERMEN["Escalation Readiness"], "Escalatierijpheid")
        self.assertEqual(NEDERLANDSE_TERMEN["Case Momentum"], "Dossierdynamiek")
        self.assertEqual(NEDERLANDSE_TERMEN["TRANSFER_OF_BURDEN"], "Lastenverplaatsing")

    def test_report_generation(self):
        tekst = "Kunt u ons alsnog een kopie toezenden van het formulier?"
        matches = self.analyzer.scan_tekst(tekst)
        rapport = self.analyzer.genereer_diagnose_rapport(matches, document_naam="brief.md")
        self.assertIn("Interne Conditie-Diagnose: `brief.md`", rapport)
        self.assertIn("LASTENVERPLAATSING", rapport)
        self.assertIn("Fluwelen Handschoen", rapport)


if __name__ == "__main__":
    unittest.main()
