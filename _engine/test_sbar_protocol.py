#!/usr/bin/env python3
"""
Unit tests voor _engine/sbar_protocol.py
Toetst SBARIII herkenning/validatie én Protocol FH-01 (Invoer-Filter, 3 IJkcontroles, 2 Negatieve Invarianten).
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
            "Met vriendelijke groet,\nBurger"
        )
        report = SBARProtocol.validate_text(incomplete)
        self.assertIn("assessment", report.missing_components)
        self.assertIn("read_back", report.missing_components)
        self.assertTrue(len(report.warnings) >= 2)

    def test_defense_reply(self):
        reply = SBARProtocol.get_defense_reply("format")
        self.assertIn("AHRQ TeamSTEPPS", reply)
        self.assertIn("PMC9778833", reply)

        reply_assessment = SBARProtocol.get_defense_reply("assessment")
        self.assertIn("sense-making", reply_assessment)

    def test_fh01_clean_transform_passes_all_checks(self):
        tekst = (
            "Geachte dokter,\n\n"
            "Naar aanleiding van het consult van gisteren schets ik kort mijn hulpvraag rond "
            "objectieve functiediagnostiek NAH en het herstel van het overdrachtsprotocol. "
            "Ik verzoek u te bezien welk vervolgonderzoek hiervoor passend is. "
            "Graag ontvang ik uw reactie uitsluitend schriftelijk binnen 14 dagen.\n"
        )
        res = SBARProtocol.validate_fh01_transform(
            tekst,
            required_goals=["functiediagnostiek NAH", "overdrachtsprotocol"],
        )
        self.assertTrue(res.passed)
        self.assertTrue(res.inhoud_behouden)
        self.assertTrue(res.taalhandeling_zuiver)
        self.assertTrue(res.ruimte_intact)
        self.assertTrue(res.geen_agency_inversion)
        self.assertTrue(res.geen_sussen_of_demoniseren)

    def test_fh01_detects_dropped_goals_and_demonization_and_dictation(self):
        foute_tekst = (
            "Door uw klerkenreflex en EPD-rampen weigert u mee te werken. "
            "U moet als arts vaststellen dat er sprake is van letsel. "
            "Zoals u zelf ongetwijfeld al had besloten, volgt nu herstel."
        )
        res = SBARProtocol.validate_fh01_transform(
            foute_tekst,
            required_goals=["functiediagnostiek NAH"],
        )
        self.assertFalse(res.passed)
        self.assertFalse(res.inhoud_behouden)
        self.assertFalse(res.taalhandeling_zuiver)
        self.assertFalse(res.ruimte_intact)
        self.assertFalse(res.geen_agency_inversion)
        self.assertFalse(res.geen_sussen_of_demoniseren)
        self.assertIn("functiediagnostiek NAH", res.ontbrekende_doelen)
        self.assertTrue(len(res.dictaat_zinnen) >= 1)
        self.assertTrue(len(res.demonisering_termen) >= 1)

    def test_fh01_two_step_intake_prompts_isolate_step1(self):
        prompts = SBARProtocol.build_fh01_intake_prompts(
            raw_incoming_text="Patiënt gezien op spreekuur; geen acute afwijkingen.",
            keten_goals="Volledige inzage ex art. 15 AVG en NAH-diagnostiek.",
            tafel_context="Kort en feitelijk houden.",
        )
        # Stap 1 mag GEEN ketendoelen bevatten (strikt Invoer-Filter)
        self.assertIn("Patiënt gezien op spreekuur", prompts["step_1_memoriaal_prompt"])
        self.assertNotIn("art. 15 AVG", prompts["step_1_memoriaal_prompt"])
        # Stap 2 bevat wél de ketendoelen
        self.assertIn("art. 15 AVG", prompts["step_2_koppeling_prompt"])


if __name__ == "__main__":
    unittest.main()
