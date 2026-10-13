#!/usr/bin/env python3
"""Het anker 2023/144 blijft smal. Een ongeijkt patroon gaat niet af."""

import sys
import unittest
from pathlib import Path

ENGINE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ENGINE_DIR))

from loket_patroon import (  # noqa: E402
    NIET_GEIJKT,
    Getuige,
    NietGeijkt,
    ZonderGetuige,
    anker_2023_041,
    anker_2023_144,
    anker_commons_2018,
    anker_phso_drempel,
    anker_phso_ontslag,
    lezen,
)


class TestLoketPatroon(unittest.TestCase):

    def test_anker_toont_vier_patronen_en_geen_getal(self):
        lezing = lezen(anker_2023_144())
        namen = tuple(dict.fromkeys(item.patroon for item in lezing.getoond))
        self.assertEqual(
            namen,
            ("vinkje", "twee_bakken", "stilte", "prijs_voor_de_burger"),
        )
        self.assertEqual(len(lezing.zetten), 4)
        self.assertIsNone(lezing.getal)
        self.assertNotIn("0", " ".join(lezing.zetten))
        self.assertNotIn("0,75", " ".join(lezing.zetten))

    def test_wmo_anker_bevestigt_drie_en_voegt_het_verslag_toe(self):
        lezing = lezen(anker_2023_041())
        namen = tuple(dict.fromkeys(item.patroon for item in lezing.getoond))
        self.assertEqual(
            namen,
            ("verslag_wijkt_af", "twee_bakken", "prijs_voor_de_burger"),
        )
        self.assertEqual(len(lezing.zetten), 3)
        self.assertTrue(lezing.zetten[0].startswith("Noem de twee bakken"))
        self.assertTrue(lezing.zetten[1].startswith("Zet de klacht"))
        self.assertTrue(lezing.zetten[2].startswith("Vraag het verslag"))
        self.assertIsNone(lezing.getal)
        self.assertNotIn("0", " ".join(lezing.zetten))

    def test_zijn_brief_is_geen_anker(self):
        zin = "Lichamelijk onderzoek: Niet verricht, nu geen indicatie voor."
        with self.assertRaises(NietGeijkt):
            lezen([Getuige("premature_closure", zin, "brief 12 oktober 2026")])
        alle = (
            anker_2023_144()
            + anker_2023_041()
            + anker_phso_ontslag()
            + anker_phso_drempel()
            + anker_commons_2018()
        )
        self.assertTrue(all(zin not in item.zin for item in alle))
        self.assertTrue(all("12 oktober 2026" not in item.bron for item in alle))
        self.assertTrue(all("stuk 80" not in item.bron for item in alle))

    def test_engelse_ankers_ijken_drie_en_geven_geen_getal(self):
        ontslag = lezen(anker_phso_ontslag())
        self.assertEqual(
            tuple(dict.fromkeys(item.patroon for item in ontslag.getoond)),
            ("sensor_uit",),
        )
        drempel = lezen(anker_phso_drempel())
        self.assertEqual(
            tuple(dict.fromkeys(item.patroon for item in drempel.getoond)),
            ("prijs_voor_de_burger",),
        )
        lagerhuis = lezen(anker_commons_2018())
        self.assertEqual(
            tuple(dict.fromkeys(item.patroon for item in lagerhuis.getoond)),
            ("verslag_wijkt_af", "sensor_uit", "vinkje", "prijs_voor_de_burger"),
        )
        for lezing in (ontslag, drempel, lagerhuis):
            self.assertIsNone(lezing.getal)
            self.assertNotIn("0", " ".join(lezing.zetten))

    def test_lege_lezing_is_geen_groen_loket(self):
        lezing = lezen(())
        self.assertEqual(lezing.getoond, ())
        self.assertEqual(lezing.zetten, ())
        self.assertIsNone(lezing.getal)

    def test_ongeijkt_patroon_gaat_niet_af(self):
        for naam in NIET_GEIJKT:
            with self.assertRaises(NietGeijkt):
                lezen([Getuige(naam, "een zin uit een brief", "ergens")])

    def test_onbekende_naam_gaat_niet_af(self):
        with self.assertRaises(NietGeijkt):
            lezen([Getuige("ossification_stage", "hoog", "gevoel")])

    def test_zin_zonder_bron_is_geen_getuige(self):
        with self.assertRaises(ZonderGetuige):
            lezen([Getuige("vinkje", "zij hebben een vinkje gezet", "  ")])

    def test_zet_volgt_de_anker_volgorde(self):
        lezing = lezen(
            [
                Getuige("stilte", "vijf jaar niets", "rapport"),
                Getuige("vinkje", "alleen een vinkje", "rapport"),
            ]
        )
        self.assertTrue(lezing.zetten[0].startswith("Vraag de daad terug"))
        self.assertTrue(lezing.zetten[1].startswith("Vraag een vaste contactpersoon"))


if __name__ == "__main__":
    unittest.main()
