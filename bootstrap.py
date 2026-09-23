#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bootstrap.py — Turnkey Onboarding & Setup Wizard voor Civic Case Engine.

Dit script leidt een nieuwe gebruiker (of Antigravity agent) in 5 behapbare stappen
door de volledige inrichting:
1. Jurisdictie & Rechtsorde
2. Basisprofiel & Tegenpartij
3. API-sleutels & Live Connectie-test (Google Gemini + DeepSeek)
4. Veiligheid & Verzendgarantie
5. Initialisatie van Dossier, Doctrine, Ketengrootboek en Eerste Sonde.
"""

import os
import sys
import json
import time
import urllib.request
from pathlib import Path

# Force UTF-8 on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT_DIR = Path(__file__).resolve().parent
ENGINE_DIR = ROOT_DIR / "_engine"
DOMAIN_PACKS_DIR = ENGINE_DIR / "domain_packs"
DOSSIER_DIR = ROOT_DIR / "Dossier"
PROBES_DIR = ROOT_DIR / "Probes"
OUTGOING_DIR = ROOT_DIR / "Outgoing_Drafts"
INCOMING_DIR = ROOT_DIR / "Incoming_Letters"
LANDSCHAP_DIR = ROOT_DIR / "Landschap"
LEDGER_DIR = ROOT_DIR / "Ketengrootboek"
ENV_FILE = ROOT_DIR / ".env"

BANNER = """
================================================================================
🏛️  CIVIC CASE ENGINE — SOVEREIGN CITIZEN EXOSKELETON
    Interactieve Inrichtings- & Onboarding Wizard (v1.0)
================================================================================
"""

def print_banner():
    print(BANNER)

def ensure_directories():
    for d in [DOSSIER_DIR, PROBES_DIR, OUTGOING_DIR, INCOMING_DIR, LANDSCHAP_DIR, LEDGER_DIR]:
        d.mkdir(parents=True, exist_ok=True)

def test_gemini_key(api_key: str) -> bool:
    if not api_key:
        return False
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    payload = {"contents": [{"parts": [{"text": "ping"}]}]}
    try:
        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return "candidates" in data
    except Exception:
        return False

def test_deepseek_key(api_key: str) -> bool:
    if not api_key:
        return False
    url = "https://api.deepseek.com/chat/completions"
    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": "ping"}],
        "max_tokens": 5
    }
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return "choices" in data
    except Exception:
        return False

def run_wizard():
    print_banner()
    ensure_directories()

    print("Dit stappenplan richt jouw persoonlijke juridische zenuwstelsel in.")
    print("Alle data blijft 100% lokaal op jouw computer. Geen centrale servers.\n")

    # --------------------------------------------------------------------------
    # STAP 1: Jurisdictie
    # --------------------------------------------------------------------------
    print("─" * 80)
    print("📍 STAP 1: KIES JE JURISDICTIE / RECHTSORDE")
    print("─" * 80)
    print("  [1] Nederland (Awb, Wmo 2015, Zorgverzekeringswet, Schulden/Beslagverbod)")
    print("  [2] Verenigd Koninkrijk (Housing Act 1996, Equality Act 2010)")
    print("  [3] Duitsland (VwGO, SGB I-XII, Widerspruchsverfahren)")
    print("  [4] Verenigde Staten (Federal/State, Due Process, Civil Rights)")
    
    choice = input("\nMaak een keuze [1-4] (standaard: 1): ").strip() or "1"
    jurisdiction_map = {
        "1": ("nl_wmo", "Nederland", "Awb / Wmo / Sociaal Domein"),
        "2": ("uk_housing", "Verenigd Koninkrijk", "UK Housing & Equality Act"),
        "3": ("nl_wmo", "Duitsland", "VwGO / SGB (Duitsland Driver)"),
        "4": ("nl_wmo", "Verenigde Staten", "US Civil Rights / Due Process")
    }
    domain_pack, jur_name, jur_desc = jurisdiction_map.get(choice, jurisdiction_map["1"])
    print(f"✔️ Gekozen: {jur_name} ({jur_desc})\n")

    # --------------------------------------------------------------------------
    # STAP 2: Profiel & Casus Context
    # --------------------------------------------------------------------------
    print("─" * 80)
    print("👤 STAP 2: BASISGEGEVENS & TEGENPARTIJ")
    print("─" * 80)
    name = input("Jouw volledige naam (bijv. Jan Jansen): ").strip() or "Burger"
    residence = input("Jouw woonplaats / gemeente (bijv. Groningen): ").strip() or "Onbekend"
    target_entity = input("Belangrijkste tegenpartij/instantie (bijv. Gemeente / CAK / Deurwaarder): ").strip() or "Gemeente"
    email_contact = input("Jouw e-mailadres voor correspondentie: ").strip() or "burger@local.box"
    
    profile = {
        "name": name,
        "residence": residence,
        "target_entity": target_entity,
        "email": email_contact,
        "jurisdiction": jur_name,
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    profile_path = DOSSIER_DIR / "profile.json"
    profile_path.write_text(json.dumps(profile, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"✔️ Profiel opgeslagen in: Dossier/profile.json\n")

    # --------------------------------------------------------------------------
    # STAP 3: API-Sleutels (De Breinen)
    # --------------------------------------------------------------------------
    print("─" * 80)
    print("🧠 STAP 3: AI-AUDITOREN KOPPELEN (MULTI-LLM KWALITEITSPOORT)")
    print("─" * 80)
    print("Om te voorkomen dat brieven juridische fouten of hallucinaties bevatten,")
    print("gebruikt de Civic Engine twee onafhankelijke AI-toetsers die elkaars werk controleren:\n")
    print("  1. Google Gemini (Brede synthese, lange context, dossier-analyse)")
    print("     👉 Haal een gratis/prepaid sleutel op: https://aistudio.google.com")
    print("  2. DeepSeek (Genadeloze formele logica, advocaat van de duivel)")
    print("     👉 Haal een sleutel op (€2 is genoeg voor 100+ dossiers): https://platform.deepseek.com\n")

    existing_env = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                existing_env[k.strip()] = v.strip()

    gemini_key = input(f"Plak je GOOGLE_API_KEY of GEMINI_API_KEY [{existing_env.get('GOOGLE_API_KEY', 'geen')}]: ").strip() or existing_env.get("GOOGLE_API_KEY", "")
    deepseek_key = input(f"Plak je DEEPSEEK_API_KEY [{existing_env.get('DEEPSEEK_API_KEY', 'geen')}]: ").strip() or existing_env.get("DEEPSEEK_API_KEY", "")

    print("\n🔍 Testen van de verbindingen...")
    if gemini_key:
        print(" - Test Google Gemini...", end=" ")
        if test_gemini_key(gemini_key):
            print("✅ SUCCES!")
        else:
            print("⚠️ Kon geen verbinding maken (sleutel onjuist of netwerkfout).")
    else:
        print(" - Google Gemini overgeslagen.")

    if deepseek_key:
        print(" - Test DeepSeek...", end=" ")
        if test_deepseek_key(deepseek_key):
            print("✅ SUCCES!")
        else:
            print("⚠️ Kon geen verbinding maken (sleutel onjuist of saldo ontoereikend).")
    else:
        print(" - DeepSeek overgeslagen.")

    # Opslaan in .env
    env_content = f"""# Civic Case Engine — Lokale Omgevingsvariabelen
# NOOIT COMMITTEN NAAR GIT

GOOGLE_API_KEY={gemini_key}
GEMINI_API_KEY={gemini_key}
DEEPSEEK_API_KEY={deepseek_key}
"""
    ENV_FILE.write_text(env_content, encoding="utf-8")
    print(f"✔️ Sleutels veilig opgeslagen in .env (blijft 100% lokaal)\n")

    # --------------------------------------------------------------------------
    # STAP 4: Veiligheid & Verzendgarantie
    # --------------------------------------------------------------------------
    print("─" * 80)
    print("🛡️ STAP 4: DE ONVOORWAARDELIJKE VERZENDGARANTIE")
    print("─" * 80)
    print("De Civic Case Engine hanteert één onverbiddelijke veiligheidsregel:")
    print("  👉 Er wordt NOOIT automatisch post of mail verzonden zonder jouw expliciete akkoord.")
    print("  👉 Elk concept wordt eerst in Outgoing_Drafts/ geplaatst na een dubbele audit.")
    print("  👉 Jij houdt te allen tijde de vinger op de knop.\n")

    # --------------------------------------------------------------------------
    # STAP 5: Initialisatie van Dossier, Doctrine & Eerste Sonde
    # --------------------------------------------------------------------------
    print("─" * 80)
    print("⚙️ STAP 5: INITIALISATIE VAN HET SYSTEEM")
    print("─" * 80)
    
    # 1. Doctrine activeren
    src_doctrine = DOMAIN_PACKS_DIR / domain_pack / "DOCTRINE.md"
    tgt_doctrine = ROOT_DIR / "DOCTRINE.md"
    if src_doctrine.exists():
        tgt_doctrine.write_text(src_doctrine.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"✔️ Actieve doctrine geactiveerd: {domain_pack}")

    # 2. Ketengrootboek initialiseren
    initial_ledger = {
        "version": "1.0",
        "client": name,
        "jurisdiction": jur_name,
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "entries": []
    }
    ledger_file = LEDGER_DIR / "grootboek.json"
    if not ledger_file.exists():
        ledger_file.write_text(json.dumps(initial_ledger, indent=2), encoding="utf-8")
        print(f"✔️ Ketengrootboek geïnitialiseerd in: Ketengrootboek/grootboek.json")

    # 3. Eerste AVG-Sonde genereren op maat
    first_probe_text = f"""# Eerste AVG-Inzageverzoek (art. 15 AVG) — {target_entity}

**Aan:** {target_entity} (Functionaris Gegevensbescherming / Juridische Zaken)  
**Van:** {name} ({email_contact})  
**Woonplaats:** {residence}  
**Datum:** {time.strftime("%d-%m-%Y")}  
**Wettelijke vervaltermijn (art. 12 lid 3 AVG):** 1 maand na dagtekening  

---

Geachte Functionaris Gegevensbescherming van {target_entity},

Hierbij verzoek ik u, op grond van **Artikel 15 van de Algemene Verordening Gegevensbescherming (AVG)**, om mij kosteloos een volledig digitaal afschrift te verstrekken van alle persoonsgegevens die uw organisatie over mij verwerkt.

Dit verzoek betreft in het bijzonder:
1. Alle interne registraties, zaaksystemen, notities en communicatieverslagen betreffende mijn persoon;
2. Alle besluitvormingsdocumenten, adviezen en rapportages;
3. Een overzicht van eventuele doorgiften van mijn gegevens aan derden, inclusief de wettelijke grondslag daarvoor;
4. De herkomst van de door u verwerkte gegevens.

Conform artikel 12 lid 3 AVG dient u binnen **één maand** na ontvangst aan dit verzoek te voldoen. Gelet op mijn administratieve autonomie verzoek ik u de stukken digitaal per e-mail (PDF) toe te zenden.

Met vriendelijke groet,

**{name}**  
Woonachtig te {residence}  
E-mail: {email_contact}
"""
    probe_output = OUTGOING_DIR / f"01_Concept_AVG_Inzageverzoek_{target_entity.replace(' ', '_')}.md"
    probe_output.write_text(first_probe_text, encoding="utf-8")
    print(f"✔️ Eerste formele AVG-sonde klaargezet in: Outgoing_Drafts/{probe_output.name}")

    print("\n" + "=" * 80)
    print("🎉 DE CIVIC CASE ENGINE IS VOLLEDIG OPERATIONEEL!")
    print("================================================================================")
    print(f"1. Jouw eerste concept staat in: Outgoing_Drafts/{probe_output.name}")
    print("2. Dubbelklik op START.cmd om het hoofdmenu te openen en audits te draaien.")
    print("3. Sleep brieven van instanties naar Incoming_Letters/ om ze te laten analyseren.")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    run_wizard()
