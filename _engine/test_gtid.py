#!/usr/bin/env python3
"""Eerste pass van de G-TID veldkaart. Sluit de consistentie, niet een rekensom."""

import sys
import unittest
from pathlib import Path

ENGINE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ENGINE_DIR))

from gtid_engine import (  # noqa: E402
    GIFT,
    VOLGENDE_SLUITING,
    VRAAG,
    WACHT,
    InstitutionalField,
    inspect_incoming_letter_for_gtid,
)

STATUTE_LEAKS = (
    "Art. 2.3.5",
    "4:17",
    "7:15",
    "art. 41",
    "dwangsom",
    "Gws4all",
    "Stuk 74",
    "BESLUITRECHTVAARDIGING",
)


class TestGTIDFirstPass(unittest.TestCase):

    def test_letter_does_not_measure_the_field(self):
        sample = """
        Betreft: Afwijzing aanvraag.
        Het systeem laat een toekenning niet toe. Wij hanteren een strikte voorwaarde
        en kunnen geen uitzondering maken.
        Hoogachtend, Klantenservice Gemeente Oldambt. Postbus 1.
        """
        field = inspect_incoming_letter_for_gtid(sample)
        card = field.card()
        self.assertEqual(card["entity"], "Gemeente Oldambt")
        self.assertTrue(card["front_open"])
        self.assertEqual(card["closure"], "open")
        self.assertEqual(card["coupling"], "niet afgelezen")
        self.assertIsNone(card["legitimacy"])
        self.assertIsNone(field.diagnose_summary()["psi_res"])
        self.assertEqual(card["operator"], VRAAG)
        self.assertNotEqual(card["operator"], VOLGENDE_SLUITING)
        self.assertTrue(card["hints"])

    def test_open_front_blocks_the_next_desk(self):
        field = InstitutionalField(
            entity_name="Sociaal team",
            front_open=True,
            closure="volgende",
            fact="De behoefte past niet in de productcode.",
        )
        self.assertEqual(field.operator, GIFT)
        self.assertNotEqual(field.operator, VOLGENDE_SLUITING)

    def test_live_conversation_waits(self):
        field = InstitutionalField(
            entity_name="Lennart",
            conversation_live=True,
            closure="volgende",
            front_open=False,
            fact="Een feit.",
        )
        self.assertEqual(field.operator, WACHT)

    def test_next_closure_only_when_the_front_is_shut(self):
        field = InstitutionalField(
            entity_name="Een balie",
            front_open=False,
            closure="volgende",
        )
        self.assertEqual(field.operator, VOLGENDE_SLUITING)
        note = field.gift_note()
        self.assertIn("ander boek", note)
        for leak in STATUTE_LEAKS:
            self.assertNotIn(leak, note)

    def test_gift_keeps_responsibility_and_names_the_cost(self):
        field = InstitutionalField(
            entity_name="Een gemeente",
            fact="Hij kan de post niet zelf op de rit houden.",
            deviation_cost="een berisping als zij van de productcode afwijkt",
        )
        note = field.generate_ambtelijke_besluitrechtvaardiging(
            subject="begeleiding",
            grounds=["dit mag de tekst niet halen"],
            risks_averted=["ook dit niet"],
        )
        self.assertIn("zelf tekent", note)
        self.assertIn("verantwoordelijkheid", note)
        self.assertIn("afletteren", note)
        self.assertIn("berisping", note)
        self.assertIn("post niet zelf", note)
        self.assertNotIn("dit mag de tekst niet halen", note)
        for leak in STATUTE_LEAKS:
            self.assertNotIn(leak, note)

    def test_back_pocket_stays_out_of_the_card(self):
        field = InstitutionalField(entity_name="Een orgaan")
        rendered = field.markdown()
        self.assertIn("proefbalans", rendered.lower())
        self.assertNotIn("Achterzak", rendered)
        self.assertIn("Achterzak", field.back_pocket())

    def test_coding_key_names_the_seam(self):
        key = InstitutionalField(entity_name="x").coding_key()
        self.assertIn("behandelaar", key["R"])
        self.assertIn("chart", key["sigma"])
        self.assertEqual(set(key["tau"]), {"G", "D", "I"})

    def test_passed_numbers_do_not_become_legitimacy(self):
        field = InstitutionalField(
            entity_name="Test",
            w_citizen=0.5,
            w_official=0.5,
            witnessed=False,
        )
        card = field.card()
        self.assertIsNone(card["legitimacy"])
        self.assertEqual(card["w_status"], "opgegeven")
        self.assertIsNone(card["regime_nickname"])


if __name__ == "__main__":
    unittest.main()
