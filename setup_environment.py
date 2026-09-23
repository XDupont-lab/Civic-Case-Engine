#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
setup_environment.py — Volledig Autonoom Inrichtingsscript voor Civic Case Engine & AI Tools.

Dit script automatiseert de volledige replicatie van de soevereine werkomgeving:
1. Systeem- & Runtimecontrole (Python, Git, Winget).
2. Virtuele Python-omgeving (.venv_bu) aanmaken.
3. Installatie van de AI Browser Agent dependencies (browser-use, langchain-google-genai, playwright).
4. Installatie van headless Chromium browser via Playwright.
5. Aanmaken van alle benodigde mappen (Dossier, Incoming_Letters, Outgoing_Drafts, etc.).
6. Genereren van 1-klik Desktop starters voor de gebruiker.
7. Starten van de interactieve juridische onboarding wizard (bootstrap.py).
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

# Force UTF-8 encoding on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT_DIR = Path(__file__).resolve().parent
VENV_DIR = ROOT_DIR / ".venv_bu"
IS_WINDOWS = sys.platform == "win32"

def print_step(num: int, title: str):
    print(f"\n{'='*70}")
    print(f"  [STAP {num}] {title}")
    print(f"{'='*70}")

def run_cmd(cmd, check=True, cwd=ROOT_DIR):
    print(f"[*] Uitvoeren: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    res = subprocess.run(cmd, cwd=cwd, shell=isinstance(cmd, str))
    if check and res.returncode != 0:
        print(f"[!] Fout bij uitvoeren van commando (code {res.returncode})")
    return res.returncode == 0

def get_venv_python() -> Path:
    if IS_WINDOWS:
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"

def get_venv_pip() -> Path:
    if IS_WINDOWS:
        return VENV_DIR / "Scripts" / "pip.exe"
    return VENV_DIR / "bin" / "pip"

def main():
    print("""
================================================================================
🏛️  CIVIC CASE ENGINE — SOVEREIGN ENVIRONMENT PROVISIONER v1.0
    Autonome Systeem- & Gereedschapsinrichter voor Antigravity / Agy
================================================================================
""")

    # STAP 1: Mappenstructuur
    print_step(1, "Lokale mappenstructuur verifiëren en aanmaken")
    directories = [
        ROOT_DIR / "Dossier",
        ROOT_DIR / "Incoming_Letters",
        ROOT_DIR / "Outgoing_Drafts",
        ROOT_DIR / "Landschap",
        ROOT_DIR / "Ketengrootboek",
        ROOT_DIR / "Probes"
    ]
    for d in directories:
        d.mkdir(parents=True, exist_ok=True)
        print(f"  [+] Map gereed: {d.name}/")

    # STAP 2: Virtual Environment (.venv_bu)
    print_step(2, "Python Virtuele Omgeving inrichten (.venv_bu)")
    venv_python = get_venv_python()
    if not venv_python.exists():
        print("[*] .venv_bu aanmaken met standaard Python...")
        if not run_cmd([sys.executable, "-m", "venv", str(VENV_DIR)]):
            print("[!] Kon virtuele omgeving niet direct aanmaken. Probeer pip install virtualenv...")
            run_cmd([sys.executable, "-m", "pip", "install", "virtualenv"])
            run_cmd([sys.executable, "-m", "virtualenv", str(VENV_DIR)])
    else:
        print("[+] Virtuele omgeving bestaat reeds.")

    # STAP 3: Packages voor de AI Browser Agent
    print_step(3, "AI Browser Agent dependencies installeren")
    venv_pip = get_venv_pip()
    if venv_pip.exists():
        print("[*] Upgraden van pip...")
        run_cmd([str(venv_pip), "install", "--upgrade", "pip", "--quiet"])
        
        print("[*] Installeren van browser-use, playwright en langchain integraties...")
        packages = ["browser-use", "playwright", "langchain-google-genai", "langchain-openai"]
        run_cmd([str(venv_pip), "install"] + packages)
        
        print("[*] Installeren van Playwright Chromium browser...")
        run_cmd([str(venv_python), "-m", "playwright", "install", "chromium"])
        print("[+] AI Browser Agent runtime is 100% operationeel.")
    else:
        print("[!] Waarschuwing: venv pip niet gevonden, overgeslagen.")

    # STAP 4: Desktop Starters / Launchers genereren
    if IS_WINDOWS:
        print_step(4, "Bureaublad & Lokale Launchers inrichten")
        desktop = Path(os.environ.get("USERPROFILE", "")) / "Desktop"
        if desktop.exists():
            start_engine_cmd = desktop / "Start-Civic-Engine.cmd"
            start_engine_cmd.write_text(f'@echo off\ncd /d "{ROOT_DIR}"\ncall START.cmd\n', encoding="utf-8")
            print(f"  [+] Snelkoppeling gemaakt op Bureaublad: {start_engine_cmd.name}")

    # STAP 5: Starten van de juridische wizard
    print_step(5, "Juridische Onboarding Wizard starten (bootstrap.py)")
    bootstrap_script = ROOT_DIR / "bootstrap.py"
    if bootstrap_script.exists():
        print("[*] Starten van bootstrap.py...")
        run_cmd([sys.executable, str(bootstrap_script)], check=False)

    print(f"""
{'='*70}
🎉 SOVEREINE WERKOMGEVING IS VOLLEDIG INGERICHT!
{'='*70}
Je kunt de Civic Case Engine direct bedienen via:
  • START.cmd (Centraal Keuzemenu)
  • RUN_BROWSER_AGENT.cmd (AI Browser Agent voor overheids- en zorgportalen)
  • Of praat direct met je Antigravity / Agy agent in deze map!
""")

if __name__ == "__main__":
    main()
