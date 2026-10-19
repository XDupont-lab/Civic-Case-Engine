#!/usr/bin/env python3
"""
Unit tests voor _engine/sbar_protocol.py
Toetst herkenning, validatie en de SBARIII componenten.
"""

import unittest
from sbar_protocol import SBARProtocol, SBARMessage


class TestSBARProtocol(unittest.TestCase):

    def test_complete_template_is_valid(self):
        msg = SBARProtocol.create_template(
            afzender="Burger X",
            ontvanger="Gemeente Y",
            situatie="Acute stopzetting van voorziening zonder overdracht.",
            achtergrond="Besluit van 2023 en lopend revalidatietraject.",
            beoordeling="Hiermee ontstaat een overdrachtsfout en acuut zorgvacuüm.",
            verzoek="Herstel van de toekenning conform art. 2.3.5 Wmo.",
            interventies="Bezwaarschrift ingediend en contact gezocht met wijkteam.",
            termijn_dagen=14
        )
        report = SBARProtocol.validate_text(msg.to_text())
        self.assertTrue(report.is_valid)
        self.assertEqual(report.score, 1.0)
        self.assertEqual(len(report.missing_components), 0)

    def test_incomplete_text_flags_missing_readback_and_assessment(self):
        incomplete = (
            "Geachte heer/mevrouw,\n"
            "Mijn situatie is dat ik een vraag heb over mijn dossier.\n"
            "De achtergrond is dat ik in 2022 geopereerd ben.\n"
            "Ik verzoek u mij de stukken te sturen.\n"
            "Met vriendelijke groet,\nXander"
        )
        report = SBARProtocol.validate_text(incomplete)
        # Assessment and Read-back are missing
        self.assertIn("assessment", report.missing_components)
        self.assertIn("read_back", report.missing_components)
        self.assertTrue(len(report.warnings) >= 2)

    def test_defense_reply(self):
        reply = SBARProtocol.get_defense_reply("format")
        self.assertIn("AHRQ TeamSTEPPS", reply)
        self.assertIn("PMC9778833", reply)

        reply_assessment = SBARProtocol.get_defense_reply("assessment")
        self.assertIn("sense-making", reply_assessment)


if __name__ == "__main__":
    unittest.main()
