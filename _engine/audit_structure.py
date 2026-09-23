#!/usr/bin/env python3
"""
CIVIC CASE ENGINE — MULTI-LLM STRUCTURE AUDIT
Voert een dialectische multi-LLM audit uit op de nieuwe doctrine en architectuur:
- DeepSeek: Wetstechnische, bestuursrechtelijke en formele toetsing (Awb, Wmo, AVG, CRvB).
- Grok: Strategische, cybernetische en institutionele machtsdynamiek (The Velvet Glove, decorum, backlash-preventie).
"""

import os
import sys
import json
import tempfile
import subprocess
import urllib.request
import urllib.error
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

engine_dir = Path(__file__).resolve().parent
root_dir = engine_dir.parent
sys.path.append(str(engine_dir))

from audit_engine import load_env_keys, call_api, ENDPOINTS, MODELS, GROK_CLI_PATH

def run_grok_cli(prompt_text, timeout=180):
    if not GROK_CLI_PATH.exists():
        return None
    temp_in = None
    try:
        with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8", suffix=".txt") as f:
            f.write(prompt_text)
            temp_in = f.name
        
        cmd = [
            str(GROK_CLI_PATH),
            "--no-plan",
            "--no-subagents",
            "--prompt-file", temp_in
        ]
        res = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout
        )
        if res.returncode == 0 and res.stdout.strip():
            return res.stdout.strip()
        else:
            print(f"[!] Grok stderr: {res.stderr[:300]}")
            return None
    except Exception as e:
        print(f"[!] Grok CLI Exception: {e}")
        return None
    finally:
        if temp_in and os.path.exists(temp_in):
            try:
                os.remove(temp_in)
            except Exception:
                pass

def run_structure_audit():
    print("=" * 70)
    print("CIVIC CASE ENGINE — MULTI-LLM STRUCTUUR-AUDIT")
    print("=" * 70)

    doctrine_path = root_dir / "DOCTRINE.md"
    topology_path = root_dir / "NON_LINEAIRE_ANALYSE_EN_CONSTRAINT_TOPOLOGIE.md"

    doctrine_text = doctrine_path.read_text(encoding="utf-8") if doctrine_path.exists() else ""
    topology_text = topology_path.read_text(encoding="utf-8") if topology_path.exists() else ""

    print(f"[*] Geladen doctrine: {doctrine_path.name} ({len(doctrine_text)} bytes)")
    print(f"[*] Geladen topologie: {topology_path.name} ({len(topology_text)} bytes)")

    env_keys = load_env_keys(root_dir)
    deepseek_key = env_keys.get("DEEPSEEK_API_KEY")

    if not deepseek_key:
        print("[!] Fout: DEEPSEEK_API_KEY ontbreekt.")
        return

    # DeepSeek Audit Prompt (Bestuursrechtelijk, Juridisch, Logisch)
    sys_deepseek = (
        "Je bent DeepSeek, fungerend als Senior Bestuursrechtelijk en Wetstechnisch Auditor binnen de Civic Case Engine. "
        "Jouw rol is zuiver deductieve logica, wetsystematiek en bestuursrechtelijke houdbaarheid (Awb, Wmo 2015, AVG, CRvB-jurisprudentie). "
        "Let op: Je bent een statisch model en hebt geen live websearch. Baseer je daarom uitsluitend op de geldende bestuursrechtelijke principes en de verstrekte doctrinestukken. "
        "Toetsingseisen:\n"
        "1. Toetsing van de 17 sensoren op juridische houdbaarheid voor de bestuursrechter.\n"
        "2. Toetsing van Sensor 11 & 17: Trapsgewijze subsidiariteit & ambtelijk decorum (voorkomen van premature escalaties, respect voor het eerstelijns-slot).\n"
        "3. Toetsing van Sensor 14: Het ontmaskeren van het OCO-alibi (waarom een burger met multimorbiditeit/NAH niet afhankelijk mag zijn van een tandeloze en ondergefinancierde externe voorziening).\n"
        "4. Toetsing van Sensor 16: De orthogonale koppeling van materiële rechtsbescherming (art. 3:4 lid 2 Awb) en procedurele handhaving (termijnen, AVG, art. 3:2 Awb).\n"
        "Geef een scherpe, gestructureerde juridische audit in het Nederlands."
    )

    user_deepseek = (
        f"Hier is de actuele doctrinestructuur van de Civic Case Engine:\n\n"
        f"### KERN VAN DE DOCTRINE (17 SENSOREN):\n{doctrine_text}\n\n"
        f"### FORMALISERING & ESCALATIE (Topologie & Drie Kamers):\n{topology_text[:4000]}\n\n"
        "Voer nu een diepgaande wetstechnische en bestuursrechtelijke audit uit op deze structuur."
    )

    # Grok Audit Prompt (Strategisch, Institutioneel, Live Dynamiek)
    sys_grok = (
        "Je bent Grok, fungerend als Strategisch en Cybernetisch Auditor binnen de Civic Case Engine. "
        "Jouw rol: Beoordeel de nieuwe architectuur op institutionele werking, machtsdynamiek en strategische robuustheid tegen bureaucratische afweermechanismen. "
        "Toetsingseisen:\n"
        "1. De werking van 'The Velvet Glove' en trapsgewijze subsidiariteit (Sensoren 11 en 17): voorkomt dit effectief dat de bureaucratie in de defensieve bunker schiet?\n"
        "2. Het realisme van Sensor 14 (het OCO-alibi, urenquota, gebrek aan doorzettingsmacht bij instanties als MEE Noord) afgezet tegen de werkelijke gemeentelijke dynamiek.\n"
        "3. De Drie-Kamer-Architectuur: hoe effectief schermt dit de kwetsbare burger (NAH) af tegen cognitieve en emotionele overbelasting?\n"
        "Geef een scherpe, no-nonsense analyse in gewone Nederlandse zinnen."
    )

    user_grok = (
        f"Hier is de actuele doctrinestructuur van de Civic Case Engine:\n\n"
        f"### KERN VAN DE DOCTRINE (17 SENSOREN):\n{doctrine_text}\n\n"
        f"### FORMALISERING & ESCALATIE:\n{topology_text[:4000]}\n\n"
        "Toets deze structuur strategisch en cybernetisch op institutionele dynamiek, ambtelijk decorum en bescherming van de burger."
    )

    print("\n[Fase 1] Parallelle audits starten met DeepSeek en Native Grok...")

    deepseek_review = None
    grok_review = None

    with ThreadPoolExecutor(max_workers=2) as executor:
        f_ds = executor.submit(call_api, ENDPOINTS["deepseek"], deepseek_key, MODELS["deepseek"], sys_deepseek, user_deepseek, 3000, 0.2)
        f_grok = executor.submit(run_grok_cli, f"Systeem: {sys_grok}\n\nInhoud:\n{user_grok}", 180)

        try:
            deepseek_review = f_ds.result()
            print("[+] DeepSeek audit voltooid.")
        except Exception as e:
            print(f"[!] DeepSeek audit mislukt: {e}")

        try:
            grok_review = f_grok.result()
            if grok_review:
                print("[+] Grok audit voltooid.")
            else:
                print("[!] Grok audit leverde geen resultaat.")
        except Exception as e:
            print(f"[!] Grok audit mislukt: {e}")

    # Fase 2: Synthese en Eindoordeel
    print("\n[Fase 2] Dialectische synthese genereren...")
    sys_synth = (
        "Je bent de Dialectische Integrator van de Civic Case Engine. "
        "Synthetiseer de wetstechnische audit van DeepSeek en de strategische audit van Grok tot een helder, gezamenlijk eindoordeel over de nieuwe structuur. "
        "Formatteer het rapport strak in Markdown met concrete conclusies, goedgekeurde pijlers en eventuele operationele aandachtspunten."
    )
    user_synth = (
        f"DEEPSEEK AUDIT (Wetstechnisch):\n{deepseek_review}\n\n"
        f"GROK AUDIT (Strategisch & Institutioneel):\n{grok_review}\n\n"
        "Produceer de integrale synthese en het eindoordeel."
    )

    synthesis = call_api(ENDPOINTS["deepseek"], deepseek_key, MODELS["deepseek"], sys_synth, user_synth, 3000, 0.2)
    print("[+] Synthese voltooid.")

    # Opslaan van het rapport
    report_file = root_dir / "AUDIT_RAPPORT_NIEUWE_STRUCTUUR.md"
    report_content = f"""# Multi-LLM Auditrapport: Nieuwe Structuur Civic Case Engine

**Datum:** 13 september 2026  
**Auditors:** DeepSeek (Formeel & Bestuursrechtelijk) & Grok (Strategisch & Institutioneel)  
**Geauditeerde componenten:**
- Drie-Kamer-Architectuur (Fundering, Machinekamer, Uitkamer)
- De 17 Methodologische & Diagnostische Sensoren ([DOCTRINE.md](DOCTRINE.md))
- Non-lineaire analyse & Constraint Topologie ([NON_LINEAIRE_ANALYSE_EN_CONSTRAINT_TOPOLOGIE.md](NON_LINEAIRE_ANALYSE_EN_CONSTRAINT_TOPOLOGIE.md))
- Specifieke correcties: Trapsgewijze Subsidiariteit (Sensoren 11 & 17) en Ontmaskering OCO-Alibi (Sensor 14).

---

## I. Dialectische Synthese & Eindoordeel

{synthesis}

---

## II. Integrale Audit: DeepSeek (Wetstechnisch & Bestuursrechtelijk)

{deepseek_review}

---

## III. Integrale Audit: Grok (Strategisch & Institutioneel)

{grok_review}
"""

    report_file.write_text(report_content, encoding="utf-8")
    print(f"\n[+] Volledig auditrapport opgeslagen in: {report_file}")
    return report_file

if __name__ == "__main__":
    run_structure_audit()
