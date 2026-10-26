#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
setup_environment.py — Lichte omgevingsinrichter voor Civic Helper.

Richt de lokale mappen buiten git (`werk/`) in en controleert de vier startvoorwaarden
via `ontkiem.py`, zonder zware externe browser-afhankelijkheden of API-sleutels op schijf.
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

    for map_naam in ("Dossier", "Incoming_Letters", "Outgoing_Drafts", "Landschap", "Ketengrootboek", "Probes"):
        (ROOT_DIR / map_naam).mkdir(parents=True, exist_ok=True)

    rapport = ontkiem.controleer_startvoorwaarden()
    print(json.dumps(rapport, indent=2, ensure_ascii=False))
    return 0 if rapport.get("alle_voorwaarden_ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
