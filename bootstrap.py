#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bootstrap.py — Gestroomlijnde Inrichting via ontkiem.py.

Conform de specificatie:
- Geen API-sleutels op het scherm en geen sleutels wegschrijven naar bestanden.
- Persoonlijk dossier en kompas worden buiten git in `werk/` ingericht.
- Ketengrootboek (`grootboek.json`) blijft een zuivere lijst van posten.
"""

import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import ontkiem


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    print("=" * 72)
    print("  CIVIC HELPER — ONTKIEMING & STARTVOORWAARDEN")
    print("=" * 72)

    rapport = ontkiem.controleer_startvoorwaarden()
    print(json.dumps(rapport, indent=2, ensure_ascii=False))

    if "--check" in sys.argv or "--test" in sys.argv:
        raise SystemExit(0 if rapport.get("alle_voorwaarden_ok") else 1)

    if not ontkiem.PROFIEL.exists():
        print("\nOpenen van het profielvenster (Naam, Woonplaats, één gratis Gmail-adres)...")
        ingevuld = ontkiem.scherm()
        if ingevuld:
            ontkiem.schrijf_profiel(
                ingevuld.get("naam", ""),
                ingevuld.get("plaats", ""),
                ingevuld.get("email", ""),
            )
            print("Profiel opgeslagen in werk/profiel.txt en werk/00_Kompas.md.")

    print("\nKlaar. Start het venster met CivicHelper.cmd of hulp/venster.py.")


if __name__ == "__main__":
    main()
