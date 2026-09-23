#!/usr/bin/env python3
"""
CIVIC CASE ENGINE — AGENTIC CASE FRAMEWORK (DIALECTIC HARNESS v2.0)
Civic Exoskeleton Multi-Model Review Engine.
Pure Python Standard Library (Zero External Dependencies).

Rol in de architectuur:
Het probabilistische 'Agentic Harness' dat meerdere externe LLM's (DeepSeek + Grok)
aanstuurt en bindt aan strikte juridische doctrines via dialectische kruisverificatie.

Architectuur:
- Automatische Multi-Model detectie (DeepSeek + Grok via OpenRouter / xAI).
- Parallelle toetsing:
  * DeepSeek: Formele logica, Awb/Wmo wetteksten, termijnen en feitelijke consistentie met dossier.
  * Grok: Strategische hefbomen, institutionele dynamiek en 'The Velvet Glove' verfijning.
- Optionele Kruislingse Verificatie (--critical): Grok toetst DeepSeek, DeepSeek toetst Grok.
- Genereert een tweeledige output in Outgoing_Drafts/:
  1. AUDIT_REPORT_<naam>.md (volledig dialectisch rapport)
  2. REFINED_<naam>.md (direct verzendklare brief waarin de verbeteringen zijn geïntegreerd)
"""

import os
import sys
import json
import re
import urllib.request
import urllib.error
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

ENDPOINTS = {
    "deepseek": "https://api.deepseek.com/chat/completions",
    "openrouter": "https://openrouter.ai/api/v1/chat/completions",
    "mistral": "https://api.mistral.ai/v1/chat/completions"
}

MODELS = {
    "deepseek": "deepseek-chat",
    "grok": "x-ai/grok-4.5",
    "mistral": "mistral-large-latest"
}

def load_env_keys(root_dir):
    candidates = [
        root_dir / ".env",
        root_dir / "_engine" / ".env",
        root_dir.parent / "Shared_Tools" / ".env",
        Path(r"E:\LLM_Workspace\Shared_Tools\.env")
    ]
    env_keys = {}
    for p in candidates:
        if p.exists():
            try:
                with open(p, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            k, v = k.strip(), v.strip().strip("'").strip('"')
                            if k in ["DEEPSEEK_API_KEY", "OPENROUTER_API_KEY", "MISTRAL_API_KEY"] and v and v != "vul_hier_in":
                                env_keys[k] = v
            except Exception:
                pass
            if len(env_keys) >= 2:
                break
    return env_keys

def load_doctrine(root_dir):
    candidates = [
        root_dir / "DOCTRINE.md",
        root_dir / "_engine" / "DOCTRINE.md",
        root_dir / "AGENTS.md"
    ]
    for c in candidates:
        if c.exists():
            try:
                with open(c, "r", encoding="utf-8") as f:
                    return f.read()[:6000]
            except Exception:
                pass
    return "Universal Constitutional & Administrative Law: Duty of care, legal certainty, proportionality, and statutory compliance."

def load_landscape(root_dir):
    candidates = [
        root_dir / "Landschap",
        # Optioneel lokaal dossier buiten de engine
        root_dir.parent / "Zaakdossier" / "Landschap",
        Path(r"E:\LLM_Workspace\Zaakdossier")
    ]
    landscape_text = []
    for ldir in candidates:
        if ldir.exists() and ldir.is_dir():
            for p in list(ldir.glob("*.md"))[:4]:
                if any(w in p.name.lower() for w in ["organisatie", "keten", "landschap"]):
                    try:
                        with open(p, "r", encoding="utf-8") as f:
                            landscape_text.append(f"### Landschap Context ({p.name}):\n" + f.read()[:2000])
                    except Exception:
                        pass
            if landscape_text:
                break
    return "\n\n".join(landscape_text) if landscape_text else "Geen specifieke machtskaart geladen."

def load_dossier_context(root_dir):
    candidates = [
        root_dir / "Dossier",
        root_dir.parent / "Zaakdossier"
    ]
    context_snippets = []
    for ddir in candidates:
        if ddir.exists() and ddir.is_dir():
            # Prioriteit voor 00_Master_Chronologie.md
            chrono = ddir / "00_Master_Chronologie.md"
            if chrono.exists():
                try:
                    with open(chrono, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                        # Neem de eerste 120 regels van de chronologie (inclusief integriteitsregister en anomalies)
                        context_snippets.append("### FORENSISCHE MASTER CHRONOLOGIE (KERNFEITEN):\n" + "".join(lines[:120]))
                except Exception:
                    pass
            for p in list(ddir.glob("*.md"))[:5]:
                if p.name.startswith("00_Master"): continue
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        context_snippets.append(f"--- Dossier Feit: {p.name} ---\n" + f.read()[:1500])
                except Exception:
                    pass
            if context_snippets:
                break
    return "\n\n".join(context_snippets) if context_snippets else "Geen dossier-feiten beschikbaar."

def get_latest_draft(drafts_dir):
    files = list(drafts_dir.glob("*.md"))
    valid = [f for f in files if not f.name.startswith(("AUDIT_REPORT_", "REFINED_"))]
    if not valid:
        return None
    valid.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    return valid[0]

GROK_CLI_PATH = Path(os.getenv("GROK_CLI_PATH", r"C:\Program Files\Grok\bin\grok.exe"))

def execute_native_grok(full_prompt_text):
    """Voert native Grok CLI (grok.exe) uit via grok.com account met live websearch."""
    if not GROK_CLI_PATH.exists():
        return None
    import subprocess
    import tempfile
    temp_in = None
    temp_out = None
    temp_err = None
    try:
        with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8", suffix=".txt") as f:
            f.write(full_prompt_text)
            temp_in = f.name
        temp_out = tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8", suffix=".txt").name
        temp_err = tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8", suffix=".txt").name
        
        cmd = [
            str(GROK_CLI_PATH),
            "--no-plan",
            "--no-subagents",
            "--tools", "",
            "--output-format", "plain",
            "--prompt-file", temp_in
        ]
        with open(temp_out, "w", encoding="utf-8") as out_f, open(temp_err, "w", encoding="utf-8") as err_f:
            res = subprocess.run(
                cmd,
                stdin=subprocess.DEVNULL,
                stdout=out_f,
                stderr=err_f,
                timeout=240
            )
        
        result_text = ""
        if os.path.exists(temp_out):
            with open(temp_out, "r", encoding="utf-8", errors="replace") as out_f:
                result_text = out_f.read().strip()
                
        if res.returncode == 0 and result_text:
            return result_text
        if os.path.exists(temp_err):
            with open(temp_err, "r", encoding="utf-8", errors="replace") as err_f:
                err_text = err_f.read().strip()
                if err_text:
                    print(f"[Native Grok Stderr: {err_text[:200]}]")
        return None
    except Exception as e:
        print(f"[Native Grok Exception: {e}]")
        return None
    finally:
        for tf in [temp_in, temp_out, temp_err]:
            if tf and os.path.exists(tf):
                try:
                    os.remove(tf)
                except Exception:
                    pass

def call_grok_engine(system_prompt, user_prompt, openrouter_key, max_tokens=2048, temp=0.3):
    full_prompt = f"Systeem: {system_prompt}\n\nOpdracht & Inhoud:\n{user_prompt}"
    native_res = execute_native_grok(full_prompt)
    if native_res:
        return native_res
    if openrouter_key and openrouter_key != "vul_hier_in" and not openrouter_key.startswith("leeg_"):
        try:
            return call_api(ENDPOINTS["openrouter"], openrouter_key, MODELS["grok"], system_prompt, user_prompt, max_tokens, temp)
        except Exception as e:
            return f"[Grok Fout: {e}]"
    return "[Grok Fout: Native Grok CLI heeft geen output geleverd en geen secundaire API geconfigureerd]"

def call_api(endpoint, api_key, model, system_prompt, user_prompt, max_tokens=2048, temp=0.2):
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": temp,
        "max_tokens": max_tokens
    }
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "http://localhost",
        "X-Title": "Civic_Case_Engine_Audit"
    }
    req = urllib.request.Request(endpoint, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=60) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        return res["choices"][0]["message"]["content"].strip()

def run_constructive_audit(draft_path, is_critical=False):
    root_dir = Path(__file__).resolve().parent.parent
    draft_path = Path(draft_path)
    
    if not draft_path.exists():
        print(f"[!] Fout: Conceptbestand niet gevonden: {draft_path}")
        return

    with open(draft_path, "r", encoding="utf-8") as f:
        draft_content = f.read()

    print(f"[*] Dossier Hub               : {root_dir.name}")
    print(f"[*] Te auditen conceptbrief    : {draft_path.name}")
    
    doctrine_context = load_doctrine(root_dir)
    landscape_context = load_landscape(root_dir)
    dossier_context = load_dossier_context(root_dir)
    env_keys = load_env_keys(root_dir)

    deepseek_key = env_keys.get("DEEPSEEK_API_KEY")
    openrouter_key = env_keys.get("OPENROUTER_API_KEY")
    mistral_key = env_keys.get("MISTRAL_API_KEY")

    has_grok = GROK_CLI_PATH.exists() or (openrouter_key and openrouter_key != "vul_hier_in")
    has_multi = deepseek_key and has_grok
    grok_label = "Native Grok-4.6 (grok.com + live websearch)" if GROK_CLI_PATH.exists() else "Grok via OpenRouter"
    print(f"[*] Modus                     : {'DIALECTISCH MULTI-MODEL (DeepSeek + ' + grok_label + ')' if has_multi else 'SINGLE-MODEL'}")
    if is_critical and has_multi:
        print("[*] Verificatieniveau         : NIVEAU 3 — KRUISLINGSE FALSIFICATIE ACTIEF")

    # 1. DeepSeek Prompt (Wetstechnisch & Logisch)
    sys_deepseek = (
        "Je bent DeepSeek in de Civic Case Engine. Jouw rol: Wettechnische en logische auditor van een burger-conceptbrief. "
        "Methodologie: 'Bekijk kritisch, verrijk, verfijn en vul aan'. "
        "Toets strikt op: 1. Wetsartikelen (Awb, Wmo, AVG, Woo, Rv), termijnen en eventuele premature stappen. "
        "2. Feitelijke consistentie met het onderliggende dossier en de chronologie. "
        "3. Mazen waardoor een bestuursorgaan of jurist de brief kan ontwijken. "
        "Geen beleefdheidsfrutsels of filler words; wees scherp, direct en constructief."
    )
    user_deepseek = (
        f"GELADEN DOCTRINE:\n{doctrine_context}\n\n"
        f"DOSSIERFEITEN & CHRONOLOGIE:\n{dossier_context}\n\n"
        f"CONCEPTBRIEF TER BEOORDELING ({draft_path.name}):\n\"\"\"\n{draft_content}\n\"\"\"\n\n"
        "Geef een gestructureerde wetstechnische en logische audit. Benoem concrete versterkingen en ontbrekende wetsartikelen."
    )

    sys_grok = (
        "Je bent Grok in de Civic Case Engine. Jouw rol: Strategische en communicatieve reviewer van een burger-conceptbrief. "
        "Methodologie: 'Bekijk kritisch, verrijk, verfijn en vul aan'. "
        "Toets scherp op: "
        "1. De machtsdynamiek met bureaucratieën (voorkom dat ambtenaren in de weerstand schieten of traineren). "
        "2. 'The Velvet Glove' toonzetting: ontwapenend, hoffelijk, waardig, maar juridisch onwrikbaar. "
        "3. Psychologische hefbomen en strategische formuleringen om actie af te dwingen. "
        "Geen robot-steno, gewone Nederlandse zinnen, scherpe kern."
    )
    user_grok = (
        f"CONCEPTBRIEF TER BEOORDELING ({draft_path.name}):\n\"\"\"\n{draft_content}\n\"\"\"\n\n"
        "Toets deze conceptbrief scherp op machtsdynamiek en The Velvet Glove (hoffelijk, waardig, ontwapenend, onwrikbaar). "
        "Geef direct 3 concrete verbeterpunten en formuleringen in gewone zinnen."
    )

    print("\n[Ronde 1] Parallelle audits uitvoeren...")
    deepseek_audit = "[Niet uitgevoerd]"
    grok_audit = "[Niet uitgevoerd]"

    with ThreadPoolExecutor(max_workers=2) as executor:
        f_ds = executor.submit(call_api, ENDPOINTS["deepseek"], deepseek_key, MODELS["deepseek"], sys_deepseek, user_deepseek, 2048, 0.2) if deepseek_key else None
        f_grok = executor.submit(call_grok_engine, sys_grok, user_grok, openrouter_key, 2048, 0.3) if has_grok else None
        
        if f_ds: deepseek_audit = f_ds.result()
        if f_grok: grok_audit = f_grok.result()

    grok_on_deepseek = None
    deepseek_on_grok = None

    # Kruislingse ronde bij --critical
    if is_critical and has_multi:
        print("[Ronde 2] Kruislingse toetsing (Grok toetst DeepSeek & DeepSeek toetst Grok)...")
        sys_cross_grok = "Je bent Grok. Toets DeepSeeks audit op feitelijke overclaims, wettekst-hallucinaties en praktische houdbaarheid. Gebruik live websearch ter verificatie."
        user_cross_grok = f"ORIGINEEL:\n{draft_content[:2000]}\n\nDEEPSEEK AUDIT:\n{deepseek_audit}\n\nBeoordeel DeepSeeks conclusies scherp en feitelijk."
        
        sys_cross_ds = "Je bent DeepSeek. Toets Groks audit op logische gaten, aannames en procedurele consistentie."
        user_cross_ds = f"ORIGINEEL:\n{draft_content[:2000]}\n\nGROK AUDIT:\n{grok_audit}\n\nBeoordeel Groks aanbevelingen analytisch."

        with ThreadPoolExecutor(max_workers=2) as executor:
            f_cg = executor.submit(call_grok_engine, sys_cross_grok, user_cross_grok, openrouter_key, 1500, 0.3)
            f_cds = executor.submit(call_api, ENDPOINTS["deepseek"], deepseek_key, MODELS["deepseek"], sys_cross_ds, user_cross_ds, 1500, 0.2)
            grok_on_deepseek = f_cg.result()
            deepseek_on_grok = f_cds.result()

    # Ronde 3: Generatie van de definitieve Refined Version
    print("[Ronde 3] Integreren van inzichten tot verzendklare REFINED brief...")
    sys_refine = (
        "Je bent de Meester-Schrijver van de Civic Case Engine. "
        "Jouw taak is het produceren van de DEFINITIEVE, VERZENDKLARE VERSIE van de conceptbrief. "
        "Integreer alle terechte juridische versterkingen (wetsartikelen, termijnen) en pas 'The Velvet Glove' onberispelijk toe: "
        "hoffelijk, waardig, rustig, maar met een ijzeren greep op de wettelijke verplichtingen van het bestuursorgaan. "
        "Lever uitsluitend de complete, verzendklare brieftekst in Markdown zonder metatekst of inleiding."
    )
    user_refine = (
        f"ORIGINELE CONCEPTBRIEF:\n{draft_content}\n\n"
        f"WETSTECHNISCHE AUDIT (DeepSeek):\n{deepseek_audit}\n\n"
        f"STRATEGISCHE & VELVET GLOVE AUDIT (Grok):\n{grok_audit}\n\n"
        "Schrijf nu de definitieve, geperfectioneerde brief klaar voor verzending."
    )

    refined_letter = "[Geen model beschikbaar voor synthese]"
    if deepseek_key:
        refined_letter = call_api(ENDPOINTS["deepseek"], deepseek_key, MODELS["deepseek"], sys_refine, user_refine, 2500, 0.2)
    elif openrouter_key:
        refined_letter = call_api(ENDPOINTS["openrouter"], openrouter_key, MODELS["grok"], sys_refine, user_refine, 2500, 0.2)

    # Rapporten opslaan
    out_dir = root_dir / "Outgoing_Drafts"
    out_dir.mkdir(parents=True, exist_ok=True)
    report_file = out_dir / f"AUDIT_REPORT_{draft_path.stem}.md"
    refined_file = out_dir / f"REFINED_{draft_path.stem}.md"

    report_md = []
    report_md.append(f"# 🛡️ Dialectisch Multi-Model Audit Rapport: {draft_path.name}\n")
    report_md.append(f"**Doelbestand:** `{draft_path.name}`  \n**Modus:** {'Multi-Model Dialectiek' if has_multi else 'Single-Model'}  ")
    report_md.append(f"**Verificatieniveau:** {'Niveau 3 (Kruislings getoetst)' if is_critical else 'Niveau 2 (Parallel getoetst)'}\n")
    report_md.append("---\n")
    report_md.append("## 1. Wetstechnische & Logische Audit (DeepSeek)\n")
    report_md.append(deepseek_audit + "\n")
    report_md.append("---\n")
    report_md.append("## 2. Strategische & Velvet Glove Audit (Grok)\n")
    report_md.append(grok_audit + "\n")
    
    if grok_on_deepseek and deepseek_on_grok:
        report_md.append("---\n")
        report_md.append("## 3. Kruislingse Toets: Grok over DeepSeek (Falsificatie & Feitencontrole)\n")
        report_md.append(grok_on_deepseek + "\n")
        report_md.append("---\n")
        report_md.append("## 4. Kruislingse Toets: DeepSeek over Grok (Logica & Consistentie)\n")
        report_md.append(deepseek_on_grok + "\n")

    with open(report_file, "w", encoding="utf-8") as f:
        f.write("\n".join(report_md))

    with open(refined_file, "w", encoding="utf-8") as f:
        f.write(refined_letter)

    print("\n" + "=" * 72)
    print(" AUDIT SUCCESVOL VOLTOOID")
    print("=" * 72)
    print(f"[+] Audit Rapport opgeslagen  : {report_file.name}")
    print(f"[+] Verzendklare brief gereed : {refined_file.name}")
    print("=" * 72)

def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

    root_dir = Path(__file__).resolve().parent.parent
    drafts_dir = root_dir / "Outgoing_Drafts"
    drafts_dir.mkdir(parents=True, exist_ok=True)

    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = [a for a in sys.argv[1:] if a.startswith("--")]
    is_critical = "--critical" in flags

    if args:
        target = Path(args[0])
        if not target.is_absolute():
            target = Path.cwd() / target
    else:
        target = get_latest_draft(drafts_dir)

    if not target or not target.exists():
        print(f"[!] Geen conceptbrief gevonden in {drafts_dir} om te auditen.")
        print("    Plaats eerst een Markdown concept in Outgoing_Drafts/.")
        sys.exit(1)

    run_constructive_audit(target, is_critical=is_critical)

if __name__ == "__main__":
    main()
