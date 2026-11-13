#!/usr/bin/env python3
"""Tests voor de Descent Type-Checker op de publieke Voorbeeldstad-sample en op eigen boeken."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

KETEN_DIR = Path(__file__).resolve().parent
if str(KETEN_DIR) not in sys.path:
    sys.path.insert(0, str(KETEN_DIR))

from descent_type_checker import DescentTypeChecker


class TestDescentTypeChecker(unittest.TestCase):
    def _sample_checker(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        d = Path(tmp.name)
        (d / "grootboek.json").write_text((KETEN_DIR / "grootboek.json").read_text(encoding="utf-8"), encoding="utf-8")
        return DescentTypeChecker(keten_dir=d)

    def test_sample_modus_zonder_eigen_boeken(self):
        dtc = self._sample_checker()
        self.assertTrue(dtc.sample_modus)
        dtc.check_all()
        regels = {e.rule_name for e in dtc.errors}
        for regel in ("Rule-Invariant-Preservation", "Rule-Source-Lineage-Validity",
                      "Rule-Art15-3-Representation", "Rule-Service-Integrity", "Rule-Execution-Without-Closure"):
            self.assertIn(regel, regels)
        self.assertEqual(len(dtc.monodromies), 1)
        self.assertAlmostEqual(dtc.monodromies[0].monodromy_delta, 1234.56)

    def test_eigen_boeken_zonder_ketenfeiten_geven_geen_lineagefout(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        d = Path(tmp.name)
        post = {"post_id": "POST-X-001", "poorten": {"doelpoort": {"voldaan": True}}, "vaste_posten": []}
        (d / "memoriaal.json").write_text("[]", encoding="utf-8")
        (d / "boek2_journaal.json").write_text(json.dumps([post]), encoding="utf-8")
        dtc = DescentTypeChecker(keten_dir=d)
        self.assertFalse(dtc.sample_modus)
        self.assertEqual(dtc.check_all(), [])
        self.assertEqual(dtc.monodromies, [])


if __name__ == "__main__":
    unittest.main()
