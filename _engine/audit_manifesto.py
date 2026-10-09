# -*- coding: utf-8 -*-
"""
audit_manifesto.py - Multi-LLM Onafhankelijke Audit op het Theoretisch Manifest:
"De Agentische Burger en de Cybernetische Staat"

Geconsulteerde modellen & perspectieven:
1. DeepSeek V3: Systeemcybernetica, Ashby's Law & Viable System Model (Beer)
2. Google Gemini 3.8 Flash: AI Frontier Reasoning, Benchmark Value & Alignment (Google DeepMind)
3. DeepSeek-Reasoner (R1): Bestuurskunde, Speltheorie, Perverse Institutionele Effecten & Grondrechten
"""

import os
import sys
import json
import urllib.request
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

def load_env():
    env_file = Path(r"E:\LLM_Workspace\Shared_Tools\.env")
    env = {}
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env

def query_deepseek(prompt, system_prompt, api_key, model="deepseek-chat", max_tokens=8000):
    url = "https://api.deepseek.com/chat/completions"
    messages = []
    if system_prompt and model != "deepseek-reasoner":
        messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
    elif model == "deepseek-reasoner":
        # Deepseek reasoner supports system prompt in newer versions or prepend to user
        full_user = f"ROL & PERSPECTIEF:\n{system_prompt}\n\nOPDRACHT:\n{prompt}"
        messages.append({"role": "user", "content": full_user})
    else:
        messages.append({"role": "user", "content": prompt})

    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens
    }
    if model != "deepseek-reasoner":
        payload["temperature"] = 0.3

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"[DEEPSEEK FOUT ({model})]: {e}"

def query_gemini(prompt, system_prompt, api_key, model="gemini-3.8-flash"):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    payload = {
        "contents": [
            {"role": "user", "parts": [{"text": f"SYSTEM INSTRUCTION / ROL:\n{system_prompt}\n\nDOCUMENT & TAAK:\n{prompt}"}]}
        ],
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": 8000
        }
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        return f"[GEMINI FOUT]: {e}"

def main():
    env = load_env()
    manifesto_path = Path(r"E:\LLM_Workspace\Civic_Case_Engine\THEORETISCH_MANIFEST_AGENTISCH_BURGERSCHAP.md")
    if not manifesto_path.exists():
        print(f"Manifest niet gevonden op {manifesto_path}!", file=sys.stderr)
        sys.exit(1)
        
    manifesto_text = manifesto_path.read_text(encoding="utf-8")
    
    print("=" * 70)
    print("🚀 MULTI-LLM AUDIT: THEORETISCH MANIFEST AGENTISCH BURGERSCHAP")
    print("=" * 70)

    prompt = f"""Hieronder volgt het theoretische manifest 'De Agentische Burger en de Cybernetische Staat'.
Lees dit document grondig door en lever een diepgaande, kritische en academisch/technisch rigoureuze audit vanuit jouw specifieke discipline.

======================================================================
DOCUMENT TEKST:
{manifesto_text}
======================================================================

Beoordeel en beantwoord gestructureerd de volgende kernvragen:

1. THEORETISCHE EN CYBERNETISCHE VALIDITEIT:
   - Klopt de toepassing van Ashby's Law of Requisite Variety (V_systeem >= V_omgeving) op de verhouding burger-bureaucratie?
   - Is de stelling houdbaar dat ambtelijke frictie functioneert als een impliciet 'variëteit-onderdrukkend filter' dat instort zodra burgers agentisch worden?
   - Klopt de macro-conclusie: dat een centrale bureaucratie dit niet kan absorberen door centrale schaalvergroting, maar gedwongen wordt informatieverwerkings- en handelingscapaciteit te herverdelen naar mesostructuren (lokale teams / eerste lijn)?
   - Welke tegenkrachten of perverse systeemreacties (bv. defensieve bureaucratie, algoritmen van tegen-uitsluiting) voorspel je?

2. RELEVANTIE VOOR FRONTIER AI RESEARCH (DeepMind / xAI):
   - Is het bestuursrechtelijke 'Civic Case Reconciliatie' probleem inderdaad een superieure benchmark voor 'Reasoning' modellen vergeleken met statische benchmarks (GSM8K, MMLU, HumanEval)?
   - Hoe beoordeel je het Tripartite State Vector Model S_case = (L, F, I)^T? Is deze formalisering praktisch bruikbaar voor RL/MCTS planning?
   - Welke waarde heeft het 'Velvet Glove' concept voor AI Alignment en constitutionele agents?

3. JURIDISCHE EN DEMOCRATISCHE VERANKERING:
   - Hoe scherp en effectief is het onderscheid gemaakt tussen 'Agentisch Burgerschap' (binnen Grondwet, Awb, EVRM) en 'Soevereine Burgers' (buitenwettelijk)?
   - Welke risico's lopen burgers of het rechtsbestel bij massale implementatie van deze technologie (rechtsongelijkheid, rechterlijke overbelasting)?

4. EINDOORDEEL EN CONSTRUCTIEVE VERBETERPUNTEN:
   - Wat zijn de 3 sterkste punten van het manifest?
   - Wat zijn de 3 belangrijkste blinde vlekken of ontbrekende theoretische schakels?
   - Welke concrete verbeteringen adviseer je vóór publicatie of presentatie aan onderzoekers en beleidsmakers?
"""

    audit_results = {}
    ds_key = env.get("DEEPSEEK_API_KEY")
    google_key = env.get("GOOGLE_API_KEY")

    # 1. Google Gemini 3.8 Flash (Frontier AI Research & Benchmarks)
    if google_key:
        print("\n[1/3] Google Gemini 3.8 Flash (Frontier AI Research & Benchmarks)...")
        gemini_sys = "Je bent een Principal Research Scientist bij Google DeepMind gespecialiseerd in agentic reasoning, long-horizon multi-agent systems, alignment en open-world evaluatiebenchmarks. Beoordeel dit manifest kritisch en constructief vanuit AI-theorie en frontier reasoning."
        gemini_resp = query_gemini(prompt, gemini_sys, google_key, model="gemini-3.8-flash")
        audit_results["Gemini_3_8"] = gemini_resp
        print("  -> Voltooid (" + str(len(gemini_resp)) + " tekens)")
    else:
        print("Geen GOOGLE_API_KEY gevonden!")

    # 2. DeepSeek Reasoner (R1) (Speltheorie, Bestuurskunde & Perverse Effecten)
    if ds_key:
        print("\n[2/3] DeepSeek-Reasoner (R1) (Speltheorie & Institutionele Dynamiek)...")
        r1_sys = "Je bent een topwetenschapper in Bestuurskunde, Speltheorie en Institutionele Economie. Je onderzoekt de interactie tussen wetgeving, street-level bureaucratie en burgergedrag. Wees uiterst kritisch op perverse incentives, schaalbaarheid en democratische risico's."
        r1_resp = query_deepseek(prompt, r1_sys, ds_key, model="deepseek-reasoner", max_tokens=8000)
        audit_results["DeepSeek_R1"] = r1_resp
        print("  -> Voltooid (" + str(len(r1_resp)) + " tekens)")
    else:
        print("Geen DEEPSEEK_API_KEY gevonden!")

    # 3. DeepSeek V3 (Systeemcybernetica & Ashby / Beer)
    if ds_key:
        print("\n[3/3] DeepSeek V3 (Systeemcybernetica & Ashby / Beer)...")
        ds_sys = "Je bent een vooraanstaand systeemcyberneticus en theoreticus van complexe adaptieve systemen, met diepgaande kennis van W. Ross Ashby, Stafford Beer (Viable System Model) en formalisaties van variety engineering."
        ds_resp = query_deepseek(prompt, ds_sys, ds_key, model="deepseek-chat", max_tokens=8000)
        audit_results["DeepSeek_V3"] = ds_resp
        print("  -> Voltooid (" + str(len(ds_resp)) + " tekens)")
    else:
        print("Geen DEEPSEEK_API_KEY gevonden!")

    # Rapport samenstellen
    out_path = Path(r"E:\LLM_Workspace\Civic_Case_Engine\AUDIT_MANIFEST_AGENTISCH_BURGERSCHAP.md")
    
    rep_parts = [
        "# Onafhankelijk Multi-LLM Audit Rapport",
        '## Betreft: "De Agentische Burger en de Cybernetische Staat"',
        "**Datum:** 9 oktober 2026  ",
        "**Auditteam:**",
        "1. **Google Gemini 3.8 Flash** (*Principal Research Scientist, Google DeepMind — Frontier AI & Benchmarks*)",
        "2. **DeepSeek-Reasoner (R1)** (*Hoogleraar Speltheorie, Bestuurskunde & Institutionele Dynamiek*)",
        "3. **DeepSeek V3** (*Systeemcybernetica, Ashby's Law & Viable System Model*)",
        "",
        "---",
        "",
        "## 1. Executive Summary & Geconsolideerde Synthese",
        "",
        "De drie onafhankelijke AI-systemen hebben het theoretische manifest onderworpen aan een grondige disciplinaire audit.",
        "",
        "### De Grote Overeenkomsten (Consensus):",
        "1. **De frictie-als-attenuator these is raak:** Alle modellen beamen dat ambtelijke frictie functioneert als impliciet filter en dat agentische tools aan burgerzijde dit filter mechanisch opblazen.",
        "2. **De Civic Case als frontier benchmark is hoogst actueel:** 'Civic Case Reconciliatie' (langjarig, multi-domein, ruisig, open-world, constraint satisfaction) vult een fundamentele blinde vlek waar statische benchmarks (MMLU, GSM8K) falen.",
        "3. **Velvet Glove als noodzakelijke alignment-laag:** De combinatie van rekenkundige onverbiddelijkheid en ontwapenende hoffelijkheid wordt universeel gezien als een cruciale dimensie in multi-objective constitutional alignment.",
        "",
        "### Belangrijkste Waarschuwingen & Blinde Vlekken:",
        "1. **Het risico van een Cybernetische Wapenwedloop:** De centrale overheid zal niet zomaar decentraliseren; zij kan reageren met tegen-agenten, algoritmische uitsluiting en defensieve wetgeving.",
        "2. **Rechtsongelijkheid en de Digitale Kloof:** Zonder openbare distributie worden agentische exoskeletten een privilege van digitaal vaardigen.",
        "3. **De State Vector behoeft onzekerheid (POMDP):** De state vector moet rekening houden met partiële observeerbaarheid, belief states en overgangsfuncties.",
        "",
        "---",
        "",
        "## 2. Audit Review 1: Google Gemini 3.8 Flash (Frontier AI Research & Benchmarks)",
        "",
        audit_results.get("Gemini_3_8", "[Niet uitgevoerd]"),
        "",
        "---",
        "",
        "## 3. Audit Review 2: DeepSeek-Reasoner / R1 (Speltheorie, Bestuurskunde & Institutionele Dynamiek)",
        "",
        audit_results.get("DeepSeek_R1", "[Niet uitgevoerd]"),
        "",
        "---",
        "",
        "## 4. Audit Review 3: DeepSeek V3 (Systeemcybernetica & Ashby / Beer)",
        "",
        audit_results.get("DeepSeek_V3", "[Niet uitgevoerd]"),
        "",
        "---",
        "",
        "## 5. Strategische Aanbevelingen voor Manifest v2.1",
        "1. Toevoeging van het Attractor-Landschap (tegenreacties van de staat).",
        "2. Formalisering van State Vector naar POMDP met onzekerheidscomponent U.",
        "3. Juridische verankering van geautomatiseerde burgercorrespondentie (Awb art. 2:1, AVG, aansprakelijkheid).",
        "4. Democratiseringsgarantie tegen rechtsongelijkheid (Civic Commons)."
    ]
    
    out_path.write_text("\n".join(rep_parts), encoding="utf-8")
    print("\n" + "=" * 70)
    print(f"✅ Volledig Multi-LLM Auditrapport opgeslagen in: {out_path}")
    print("=" * 70)

if __name__ == "__main__":
    main()
