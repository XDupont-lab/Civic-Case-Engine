#!/usr/bin/env python3
"""
CIVIC CASE ENGINE — REGRESSIESUITE CYBERNETISCHE INVARIANTEN (T1 t/m T6)
Pure Python Standard Library (Zero External Dependencies).

Toetst de 6 kernlessen van de reële casus (Grok Synthese):
- T1: Payload/slot-mismatch (klinische uitleg -> productcode-poort => REJECT)
- T2: Vacature in het slot (detachering/afwezigheid zonder beschikking => mandate commit)
- T3: Handshake (na toewijzing backliner => geen tweede crisisbrief)
- T4: Drift (telefoon toegestaan => REJECT/WARN)
- T5: Discours (politieke cc zonder L2 discours => REJECT)
- T6: Oordeel (CV/loopbaan ambtenaar in brieftekst => REJECT)
"""

import unittest
import sys
import json
from pathlib import Path

# Voeg engine directory toe aan path
ENGINE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ENGINE_DIR))

from veto_gate import VetoGate

class TestCyberneticInvariants(unittest.TestCase):

    def setUp(self):
        self.gate = VetoGate(root_dir=ENGINE_DIR.parent)

    def test_t1_payload_slot_mismatch(self):
        """T1: Klinische uitleg gestuurd naar een productcode-poort moet door Veto 1 worden afgekeurd."""
        concept_brief = """
        Geachte heer/mevrouw,
        Hierbij vraag ik huishoudelijke hulp aan.
        Ik heb ernstige darmproblematiek en een stoma, waardoor ik dagelijks veel pijnklachten ervaar.
        Gelet op mijn medische belastbaarheid verzoek ik alle stukken uitsluitend schriftelijk per e-mail te sturen.
        """
        slot = {
            "name": "Wmo Consulent Flex (Loket)",
            "authority": "Gemeente Voorbeeldstad",
            "ingest_capacity": ["productcodes"]  # Geen 'klinisch'
        }
        report = self.gate.check_draft(concept_brief, slot_metadata=slot)
        self.assertFalse(report["all_passed"], "Brief had geblokkeerd moeten worden wegens klinische payload")
        rules_hit = [r["rule"] for r in report["results"]]
        self.assertIn("VETO_1_PAYLOAD_SLOT_INGEST", rules_hit)

    def test_t2_vacature_in_slot_mandate_escalation(self):
        """T2: Bij afwezigheid/detachering moet payload naar mandaatlaag (teamleider), niet verdere uitleg."""
        # Als we naar een teamleider sturen met ingest ['termijnen', 'keten', 'klinisch'], mag klinische context wel
        concept_crisis = """
        Aan de Teamleider Wmo,
        Wegens het wegvallen van de toegewezen consulent zonder overdracht is een acute zorgval ontstaan.
        Ik verzoek om onverwijlde continuering van de maatwerkvoorziening en toewijzing van een vaste casemanager.
        Gelet op mijn medische belastbaarheid verzoek ik alle stukken uitsluitend schriftelijk per e-mail te sturen.
        """
        slot_teamleider = {
            "name": "Teamleider Wmo (Mandaat)",
            "authority": "Gemeente Voorbeeldstad",
            "ingest_capacity": ["productcodes", "termijnen", "keten", "klinisch", "privacy"]
        }
        report = self.gate.check_draft(concept_crisis, slot_metadata=slot_teamleider)
        self.assertTrue(report["all_passed"], "Crisiscommit naar teamleider moet passeren")

    def test_t3_handshake_blocks_second_crisis(self):
        """T3: Na formele handshake mag geen tweede crisisbrief naar hetzelfde slot worden gestuurd."""
        concept_tweede_crisis = """
        Aan de Teamleider Wmo,
        Ik herhaal nogmaals mijn noodkreet over de zorgtoewijzing en eis direct actie.
        Gelet op mijn medische belastbaarheid verzoek ik alle stukken uitsluitend schriftelijk per e-mail te sturen.
        """
        slot_teamleider = {
            "name": "Teamleider Wmo",
            "authority": "Gemeente Voorbeeldstad (Wmo & FG)",
            "is_crisis_commit": True  # Markeer als poging tot tweede crisiscommit
        }
        report = self.gate.check_draft(concept_tweede_crisis, slot_metadata=slot_teamleider)
        # In termijnen.json loopt wmo_avg_gemeente reeds voor Gemeente Voorbeeldstad
        rules_hit = [r["rule"] for r in report["results"]]
        self.assertIn("VETO_5_TWEEDE_NU_DUBBELE_KLOK", rules_hit)

    def test_t4_drift_detection(self):
        """T4: Concept dat telefonische afhandeling openlaat moet worden afgekeurd."""
        concept_met_telefoon = """
        Geachte heer/mevrouw,
        Hierbij doe ik een AVG-verzoek. U kunt mij hierover bellen om het mondeling toe te lichten.
        """
        report = self.gate.check_draft(concept_met_telefoon)
        self.assertFalse(report["all_passed"])
        rules_hit = [r["rule"] for r in report["results"]]
        self.assertIn("VETO_3_DRIFT_TELEFOON", rules_hit)

    def test_t5_channel_purity_cross_contamination_cc(self):
        """T5: Politieke CC op een administratieve/uitvoerende sonde moet worden afgekeurd wegens kanaalbesmetting."""
        concept_met_griffie = """
        Aan: privacy@menzis.nl
        CC: griffie@voorbeeldgemeente.nl, fractievoorzitter@voorbeeldgemeente.nl
        Onderwerp: AVG-inzage
        Gelet op mijn medische belastbaarheid verzoek ik alle stukken uitsluitend schriftelijk per e-mail te sturen.
        """
        report = self.gate.check_draft(concept_met_griffie)
        self.assertFalse(report["all_passed"])
        rules_hit = [r["rule"] for r in report["results"]]
        self.assertIn("VETO_2_KANAALBESMETTING_CC", rules_hit)

        # Maar een ZELFSTANDIGE Signaalbrief gericht AAN de politiek moet WEL passeren:
        concept_signaalbrief = """
        Aan: De fractie van Fractie A en Fractie B
        Kopie aan: De Raadsgriffie van de gemeente Voorbeeldstad
        Onderwerp: Politiek Signaal: Noodzaak Sociaal Raadslieden
        Hierbij leg ik u een praktijkcasus voor ter staving van het raadsdebat.
        Gelet op mijn medische belastbaarheid verzoek ik alle stukken uitsluitend schriftelijk per e-mail te sturen.
        """
        slot_politiek = {
            "name": "Raadsfracties & Griffie",
            "is_political_brief": True,
            "ingest_capacity": ["keten", "privacy"]
        }
        report_politiek = self.gate.check_draft(concept_signaalbrief, slot_metadata=slot_politiek)
        self.assertTrue(report_politiek["all_passed"], "Zelfstandige politieke signaalbrief moet passeren!")

    def test_t6_oordeel_loopbaan_rejection(self):
        """T6: Brieftekst met loopbaangegevens of subjectieve diskwalificatie van ambtenaar moet worden afgekeurd."""
        concept_met_oordeel = """
        Geachte heer/mevrouw,
        Consulent mw. X werkte voorheen bij de Edah en is via Maandag gedetacheerd. Zij is volstrekt onbekwaam.
        Gelet op mijn medische belastbaarheid verzoek ik alle stukken uitsluitend schriftelijk per e-mail te sturen.
        """
        report = self.gate.check_draft(concept_met_oordeel)
        self.assertFalse(report["all_passed"])
        rules_hit = [r["rule"] for r in report["results"]]
        self.assertIn("VETO_4_LOOPBAAN_OF_OORDEEL", rules_hit)

    def test_t7_glue_check_def4_evaluator(self):
        """T7: Formal Def. 4 / Addendum II evaluation via GlueChecker."""
        from glue_check import GlueChecker
        checker = GlueChecker(root_dir=ENGINE_DIR.parent)
        interfaces_file = ENGINE_DIR.parent / "interfaces.json"
        self.assertTrue(interfaces_file.exists(), "interfaces.json must exist")

        with open(interfaces_file, "r", encoding="utf-8") as f:
            ifaces = json.load(f)

        iface_wonen = next((i for i in ifaces if i["id"] == "IF-WONEN-WMO-001"), None)
        self.assertIsNotNone(iface_wonen)

        verdict = checker.evaluate_interface(iface_wonen)
        self.assertEqual(verdict.verdict, "GLUING_FAILURE")
        self.assertFalse(verdict.tests["Def4.R"].passed)
        self.assertFalse(verdict.tests["Def4.O"].passed)
        self.assertFalse(verdict.tests["Def4.G"].passed)
        self.assertTrue(verdict.tests["Def4.A"].passed)
        self.assertEqual(verdict.locus[0], "C_medische_urgentie_01")
        self.assertEqual(verdict.locus[1], "IF-WONEN-WMO-001")
        self.assertIn("Art. 2.1.1 en 2.3.2 Wmo 2015", verdict.locus[2])

if __name__ == "__main__":
    unittest.main(verbosity=2)

