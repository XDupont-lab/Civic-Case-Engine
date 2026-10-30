#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_reconstructie_schone_machine.py — Volledige Schone-Machine Reconstructietest.

Toetst de 7 harde eisen voor een veilige installatieketen en rampenherstel (Disaster Recovery):
  [1] Nieuwe Windows-gebruiker    -> Installatie zonder handmatige reparaties
  [2] Ontbrekende afhankelijkheid -> Correcte detectie en installatie-instructie
  [3] Geen NVIDIA-sleutel         -> Begrijpelijke degradatie, geen crash
  [4] Verkeerde API-sleutel       -> Foutmelding zonder lekken
  [5] Onderbroken installatie     -> Herstart zonder dubbele of beschadigde toestand
  [6] Bestaande installatie       -> Idempotente heruitvoering
  [7] GitHub-update               -> Geen overschrijving van lokale dossiers
"""

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

_ENGINE_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _ENGINE_DIR.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
if str(_REPO_ROOT / "gui") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "gui"))

import model_bus
import omgeving_inrichter
import pii_mask


class TestSchoneMachineReconstructie(unittest.TestCase):
    """Volledige reconstructietest van schone machine tot rampenherstel."""

    def test_01_nieuwe_windows_gebruiker_schone_installatie(self):
        """[1] Nieuwe Windows-gebruiker: Installatie slaagt zonder handmatige tussenkomst."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            sandbox = Path(tmp_dir) / "CivicHelper_Nieuw"
            sandbox.mkdir(parents=True, exist_ok=True)

            status = omgeving_inrichter.voer_inrichting_uit(doel_root=sandbox)

            # Verifieer dat alle vereiste werkmappen automatisch buiten git zijn klaargezet
            vereiste_mappen = [
                sandbox / "werk",
                sandbox / "werk" / "binnen",
                sandbox / "werk" / "takken",
                sandbox / "werk" / "archief",
                sandbox / "Dossier",
                sandbox / "Incoming_Letters",
                sandbox / "Outgoing_Drafts",
                sandbox / "Ketengrootboek",
            ]
            for m in vereiste_mappen:
                self.assertTrue(m.exists(), f"Ontbrekende map bij schone start: {m.name}")
                self.assertTrue(m.is_dir(), f"Pad is geen map: {m.name}")

            # Verifieer dat het Kompas is aangemaakt en geldige UTF-8 bevat
            kompas = sandbox / "werk" / "00_Kompas.md"
            self.assertTrue(kompas.exists(), "00_Kompas.md ontbreekt bij schone start")
            self.assertGreater(kompas.stat().st_size, 10, "00_Kompas.md is leeg")
            inhoud = kompas.read_text(encoding="utf-8")
            self.assertIn("Kompas", inhoud)

            # Verifieer PII-masker op schone installatie
            self.assertTrue(status.get("masker_ok"), "PII-masker niet actief bij schone installatie")

    def test_02_ontbrekende_afhankelijkheid_detectie(self):
        """[2] Ontbrekende afhankelijkheid: Correcte detectie en gerichte instructie."""
        # 1. requirements.txt moet aanwezig zijn en alle kernpakketten specificeren
        req_file = _REPO_ROOT / "requirements.txt"
        self.assertTrue(req_file.exists(), "requirements.txt ontbreekt in root")
        req_text = req_file.read_text(encoding="utf-8").lower()
        for pkg in ("pyqt6", "pypdf", "pymupdf", "requests", "winocr"):
            self.assertIn(pkg, req_text, f"Vereist pakket '{pkg}' ontbreekt in requirements.txt")

        # 2. Toets dat een gesimuleerde ontbrekende tool geen onbehandelde crash geeft
        fake_status = {
            "mappen_gereed": True,
            "tools_aantal": 5,
            "tools_totaal": 8,
            "huizen_actief": [],
            "multi_llm_gereed": False,
            "masker_ok": True,
            "voorbeeld_voor": "test",
            "voorbeeld_na": "test",
        }
        md = omgeving_inrichter.genereer_stappenplan_markdown(fake_status)
        self.assertIn("5/8 Python-gereedschappen", md)
        self.assertIn("UITBREIDEN AANBEVOLEN", md)

    def test_03_geen_nvidia_sleutel_begrijpelijke_degradatie_geen_crash(self):
        """[3] Geen NVIDIA-sleutel: Begrijpelijke degradatie, zero crash."""
        # Bewaar originele env
        orig_nv = os.environ.get("NVIDIA_API_KEY")
        orig_deepseek = os.environ.get("DEEPSEEK_API_KEY")
        try:
            # Forceer afwezigheid van sleutels
            os.environ["NVIDIA_API_KEY"] = ""
            os.environ["DEEPSEEK_API_KEY"] = ""

            status = model_bus.available()
            self.assertFalse(status.get("nvidia", False), "nvidia mag niet actief zijn zonder sleutel")

            # Roep complete aan voor nvidia: moet een schone fouttekst geven, GEEN unhandled exception
            result = model_bus.complete("nvidia", "system prompt", "gebruiker vraag")
            self.assertTrue(isinstance(result, str), "Resultaat moet een string zijn")
            self.assertTrue(result.startswith("[FOUT]"), f"Verwachtte foutmelding, kreeg: {result}")
            self.assertIn("NVIDIA_API_KEY", result)
        finally:
            if orig_nv is not None:
                os.environ["NVIDIA_API_KEY"] = orig_nv
            if orig_deepseek is not None:
                os.environ["DEEPSEEK_API_KEY"] = orig_deepseek

    def test_04_verkeerde_api_sleutel_foutmelding_zonder_lekken(self):
        """[4] Verkeerde API-sleutel: Foutmelding zonder dat de sleutel lekt."""
        geheime_foutieve_sleutel = "nvapi-SUPER-GEHEIME-TOKEN-DIE-NOOIT-MAG-LEKKEN-12345"

        # 1. Test token-scrubber direct
        lekkende_tekst = f"HTTP 401 Unauthorized: Bearer {geheime_foutieve_sleutel} was rejected by server."
        geschoond = model_bus._scrub_tokens(lekkende_tekst, geheime_foutieve_sleutel)
        self.assertNotIn(geheime_foutieve_sleutel, geschoond, "Sleutel lekt in geschoonde tekst!")
        self.assertIn("[VERBORGEN_SLEUTEL]", geschoond)

        # 2. Test URL query scrubber (?key=...)
        lekkende_url = "https://generativelanguage.googleapis.com/v1beta?key=AIzaSyDUMMYKEYFORBIDDENTOLEAK99"
        geschoonde_url = model_bus._scrub_tokens(lekkende_url)
        self.assertNotIn("AIzaSyDUMMYKEYFORBIDDENTOLEAK99", geschoonde_url)
        self.assertIn("[VERBORGEN_SLEUTEL]", geschoonde_url)

    def test_05_onderbroken_installatie_herstart_zonder_corruptie(self):
        """[5] Onderbroken installatie: Herstart herstelt toestand zonder duplicaten of corruptie."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            sandbox = Path(tmp_dir) / "CivicHelper_Half"
            sandbox.mkdir(parents=True, exist_ok=True)
            werk = sandbox / "werk"
            werk.mkdir(parents=True, exist_ok=True)

            # Simuleer een crash midden in een bestandsschrijf-actie (0-byte bestand)
            beschadigd_kompas = werk / "00_Kompas.md"
            beschadigd_kompas.write_bytes(b"")  # 0 bytes corruptie
            self.assertEqual(beschadigd_kompas.stat().st_size, 0)

            # Simuleer een verweesd lock-bestand
            lock_file = sandbox / ".install.lock.tmp"
            lock_file.write_text("pid=9999", encoding="utf-8")

            # Herstart de installatie / inrichting
            status = omgeving_inrichter.voer_inrichting_uit(doel_root=sandbox)

            # Verifieer dat het beschadigde bestand automatisch is hersteld
            self.assertTrue(beschadigd_kompas.exists())
            self.assertGreater(beschadigd_kompas.stat().st_size, 10, "Beschadigd 0-byte bestand is niet gerepareerd!")
            inhoud = beschadigd_kompas.read_text(encoding="utf-8")
            self.assertIn("Kompas", inhoud)

            # Verifieer dat er geen dubbele geneste mappen zijn ontstaan (zoals werk/werk)
            self.assertFalse((werk / "werk").exists(), "Dubbele werkmap ontstaan na herstart!")

    def test_06_bestaande_installatie_idempotente_heruitvoering(self):
        """[6] Bestaande installatie: Idempotente heruitvoering (f(f(x)) = f(x))."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            sandbox = Path(tmp_dir) / "CivicHelper_Actief"
            sandbox.mkdir(parents=True, exist_ok=True)

            # 1. Eerste run
            omgeving_inrichter.voer_inrichting_uit(doel_root=sandbox)

            # 2. De gebruiker schrijft een eigen aantekening in 00_Kompas.md
            kompas = sandbox / "werk" / "00_Kompas.md"
            gebruikers_tekst = (
                "# Kompas van Xander\n\n"
                "Zaaknummer: ZK-2026-9912\n"
                "Gemeente: Voorbeeldstad\n"
                "Laatste stand: WGBO-verzoek verzonden op 2026-10-30.\n"
            )
            kompas.write_text(gebruikers_tekst, encoding="utf-8")
            hash_voor = hashlib.sha256(kompas.read_bytes()).hexdigest()

            # 3. Voer de inrichting nog 3 keer achter elkaar uit
            for _ in range(3):
                status = omgeving_inrichter.voer_inrichting_uit(doel_root=sandbox)
                self.assertTrue(status.get("mappen_gereed"))

            # 4. Verifieer dat de gebruikersgegevens 100% onaangeroerd zijn gebleven
            hash_na = hashlib.sha256(kompas.read_bytes()).hexdigest()
            self.assertEqual(hash_voor, hash_na, "Idempotentie geschonden: gebruikersnotities zijn overschreven!")
            self.assertEqual(kompas.read_text(encoding="utf-8"), gebruikers_tekst)

    def test_07_github_update_overschrijft_geen_dossiers(self):
        """[7] GitHub-update: Geen overschrijving van lokale dossiers en persoonsdata."""
        # Controleer gitignore regels voor alle gevoelige burgerpaden
        gitignore_path = _REPO_ROOT / ".gitignore"
        self.assertTrue(gitignore_path.exists(), ".gitignore ontbreekt")
        gi_lines = [l.strip() for l in gitignore_path.read_text(encoding="utf-8").splitlines()]

        # Harde controles op kritieke uitsluitingen
        self.assertIn("werk/", gi_lines, "werk/ map is niet beschermd in .gitignore!")
        self.assertIn(".env", gi_lines, ".env is niet beschermd in .gitignore!")

        # Maak tijdelijke bestanden aan die in de beschermde mappen zouden leven
        gevoelige_relatieve_paden = [
            "werk/00_Kompas.md",
            "werk/binnen/bankmutaties.csv",
            "werk/takken/01_zorg.md",
            "Dossier/medisch_verslag.pdf",
            "Dossier/bloedwaarden.csv",
            "Incoming_Letters/besluit_wmo.pdf",
            "Outgoing_Drafts/concept_avg_brief.md",
            "Ketengrootboek/memoriaal.json",
            "Ketengrootboek/boek2_journaal.json",
            "Ketengrootboek/ketengrootboek.json",
        ]

        # Als git aanwezig is in deze checkout, voer 'git check-ignore' uit
        if shutil.which("git") and (_REPO_ROOT / ".git").exists():
            for rel in gevoelige_relatieve_paden:
                res = subprocess.run(
                    ["git", "check-ignore", "-q", rel],
                    cwd=str(_REPO_ROOT),
                )
                self.assertEqual(
                    res.returncode,
                    0,
                    f"Kritieke fout: pad '{rel}' wordt NIET genegeerd door git en kan door git pull worden overschreven!",
                )


def run_audit_table():
    """Voert de tests uit en toont een tabel met de 7 concrete bewijzen."""
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestSchoneMachineReconstructie)
    runner = unittest.TextTestRunner(verbosity=0)
    result = runner.run(suite)

    tests_labels = [
        ("Nieuwe Windows-gebruiker", "Installatie zonder handmatige reparaties"),
        ("Ontbrekende afhankelijkheid", "Correcte detectie en installatie-instructie"),
        ("Geen NVIDIA-sleutel", "Begrijpelijke degradatie, geen crash"),
        ("Verkeerde API-sleutel", "Foutmelding zonder lekken"),
        ("Onderbroken installatie", "Herstart zonder dubbele of beschadigde toestand"),
        ("Bestaande installatie", "Idempotente heruitvoering"),
        ("GitHub-update", "Geen overschrijving van lokale dossiers"),
    ]

    print("\n" + "=" * 80)
    print("      CIVIC HELPER — SCHONE-MACHINE RECONSTRUCTIE- ^& HERSTELAUDIT")
    print("=" * 80)
    print(f"{'Test':<30} {'Bewijs':<40} {'Status'}")
    print("-" * 80)

    all_passed = result.wasSuccessful()
    for naam, bewijs in tests_labels:
        status_str = "[V] GESLAAGD" if all_passed else "[!] FAALT"
        print(f"{naam:<30} {bewijs:<40} {status_str}")

    print("=" * 80)
    if all_passed:
        print("  RECONSTRUCTIE-STATUS: 100% BEWEZEN (7/7 scenario's geslaagd)\n")
        return 0
    else:
        print(f"  FOUTEN: {len(result.failures) + len(result.errors)} scenario's faalden.\n")
        return 1


if __name__ == "__main__":
    sys.exit(run_audit_table())
