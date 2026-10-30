#!/usr/bin/env python3
"""
Unit tests voor institutional_conditions.py
Toetst de detectie van de 5 institutionele condities en de Fluwelen Handschoen / Polder-vertaling.
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
)


class TestInstitutionalConditions(unittest.TestCase):
    def setUp(self):
        self.analyzer = InstitutionalConditionsAnalyzer()

    def test_transfer_of_burden_detection(self):
        tekst = """
        Geachte heer Dupont,
        Wij hebben uw gegevens nog niet aangetroffen in ons zaaksysteem.
        Kunt u ons alsnog een kopie toezenden van de salarisspecificaties over 2017?
        Met vriendelijke groet,
        Afdeling Personeel & Financiën
        """
        matches = self.analyzer.scan_tekst(tekst, context={"datum": "14 september 2026", "kenmerk": "ZK-1724925"})
        codes = [m.code for m in matches]
        self.assertIn("TRANSFER_OF_BURDEN", codes)
        
        m_burden = next(m for m in matches if m.code == "TRANSFER_OF_BURDEN")
        self.assertGreaterEqual(m_burden.confidence, 0.70)
        self.assertIn("Om u zoekwerk in het archief te besparen", m_burden.polder_handreiking)
        self.assertIn("ZK-1724925", m_burden.polder_handreiking)

    def test_procedural_deflection_detection(self):
        tekst = """
        Geachte burger,
        Wij zijn niet bevoegd om dit verzoek te behandelen.
        Dit verzoek kunt u uitsluitend via het portaal met DigiD indienen.
        Daarom verwijzen wij u door naar het algemene loket.
        """
        matches = self.analyzer.scan_tekst(tekst, context={"onderwerp": "Wmo indicatie", "doel_loket": "Sociaal Team"})
        codes = [m.code for m in matches]
        self.assertIn("PROCEDURAL_DEFLECTION", codes)

        m_deflect = next(m for m in matches if m.code == "PROCEDURAL_DEFLECTION")
        self.assertIn("Dank voor uw toelichting over de interne bevoegdheidsverdeling", m_deflect.polder_handreiking)
        self.assertIn("Sociaal Team", m_deflect.polder_handreiking)

    def test_institutional_delay_and_repeated_contact(self):
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
        codes = [m.code for m in matches]
        self.assertIn("INSTITUTIONAL_DELAY", codes)
        self.assertIn("REPEATED_CONTACT_WITHOUT_RESOLUTION", codes)

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

    def test_report_generation(self):
        tekst = "Kunt u ons alsnog een kopie toezenden van het formulier?"
        matches = self.analyzer.scan_tekst(tekst)
        rapport = self.analyzer.genereer_diagnose_rapport(matches, document_naam="brief.md")
        self.assertIn("Interne Conditie-Diagnose: `brief.md`", rapport)
        self.assertIn("TRANSFER_OF_BURDEN", rapport)
        self.assertIn("Fluwelen Handschoen", rapport)


if __name__ == "__main__":
    unittest.main()
