#!/usr/bin/env python3
"""
CIVIC HELPER — AGENTIC CASE FRAMEWORK (DIALECTIC HARNESS v2.1 + PROTOCOL FH-01)
CIVIC HELPER Multi-Model Review Engine.
Pure Python Standard Library (Zero External Dependencies).

Rol in de architectuur:
Het probabilistische 'Agentic Harness' dat meerdere externe LLM's (DeepSeek, Grok, NVIDIA NIM, Gemini)
aanstuurt via `gui/model_bus.py` (met lokale PII-maskering via `gui/pii_mask.py`) en bindt aan:
- Strikte juridische doctrines en dialectische kruisverificatie.
- De Twee Poorten (`TwoGateDispatcher`: GuardGate draagkracht + VetoGate 6 cybernetische & FH-01 veto's).
- Protocol FH-01 (`NOTITIE_COMMUNICATIEPROTOCOL_SBARIII.md` §7):
  * Uitgaand: Drie IJkcontroles (Inhoud, Taalhandeling, Ruimte) + Twee Negatieve Invarianten.
  * Inkomend (`--incoming`): Strikt 2-Staps Invoer-Filter (Stap 1 zuiver Memoriaal zonder doelen/strategie;
    Stap 2 koppeling met Ketengrootboek-doelen en Tafel-weging).
"""

import os
import sys
import json
import re
import shutil
import urllib.request
import urllib.error
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

ENGINE_DIR = Path(__file__).resolve().parent
ROOT_DIR = ENGINE_DIR.parent
GUI_DIR = ROOT_DIR / "gui"
SHARED_DIR = ROOT_DIR.parent / "Shared_Tools"

for _p in (ENGINE_DIR, GUI_DIR, SHARED_DIR):
    if _p.exists() and str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import model_bus
from pii_mask import mask, restore
from sbar_protocol import SBARProtocol

ENDPOINTS = {
    "deepseek": "https://api.deepseek.com/chat/completions",
    "openrouter": "https://openrouter.ai/api/v1/chat/completions",
    "mistral": "https://api.mistral.ai/v1/chat/completions",
}

MODELS = {
    "deepseek": "deepseek-chat",
    "grok": "x-ai/grok-4.5",
    "mistral": "mistral-large-latest",
}


def load_env_keys(root_dir):
    model_bus._load_env()
    candidates = [
        root_dir / ".env",
        root_dir / "_engine" / ".env",
        root_dir.parent / "Shared_Tools" / ".env",
        Path(os.getenv("SHARED_TOOLS_ENV", "")) if os.getenv("SHARED_TOOLS_ENV") else (root_dir.parent / "Shared_Tools" / ".env"),
    ]
    env_keys = {}
    tracked_vars = (
        "DEEPSEEK_API_KEY",
        "OPENROUTER_API_KEY",
        "MISTRAL_API_KEY",
        "NVIDIA_API_KEY",
        "GROQ_API_KEY",
        "GOOGLE_API_KEY",
    )
    for k in tracked_vars:
        val = os.environ.get(k, "").strip()
        if val and val != "vul_hier_in":
            env_keys[k] = val

    for p in candidates:
        if p and p.exists():
            try:
                with open(p, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            k, v = k.strip(), v.strip().strip("'").strip('"')
                            if k in tracked_vars and v and v != "vul_hier_in" and k not in env_keys:
                                env_keys[k] = v
            except Exception:
                pass
    return env_keys


def load_doctrine(root_dir):
    candidates = [
        root_dir / "DOCTRINE.md",
        root_dir / "_engine" / "DOCTRINE.md",
        root_dir / "AGENTS.md",
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
        root_dir / "werk" / "landschap",
        root_dir.parent / "Zaakdossier" / "Landschap",
        root_dir.parent / "Zaakdossier",
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
        root_dir / "werk",
        root_dir / "Dossier",
        root_dir.parent / "Zaakdossier",
    ]
    context_snippets = []
    for ddir in candidates:
        if ddir.exists() and ddir.is_dir():
            chrono = ddir / "00_Master_Chronologie.md"
            if chrono.exists():
                try:
                    with open(chrono, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                        context_snippets.append("### FORENSISCHE MASTER CHRONOLOGIE (KERNFEITEN):\n" + "".join(lines[:120]))
                except Exception:
                    pass
            for p in list(ddir.glob("*.md"))[:5]:
                if p.name.startswith("00_Master"):
                    continue
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
    valid = [f for f in files if not f.name.startswith(("AUDIT_REPORT_", "REFINED_", "FH01_INTAKE_"))]
    if not valid:
        return None
    valid.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    return valid[0]


_default_grok = (
    shutil.which("grok")
    or str(Path.home() / ".grok" / "bin" / "grok.exe")
    if (Path.home() / ".grok" / "bin" / "grok.exe").exists()
    else (r"C:\Program Files\Grok\bin\grok.exe" if sys.platform == "win32" else "grok")
)
GROK_CLI_PATH = Path(os.getenv("GROK_CLI_PATH", _default_grok))


def execute_native_grok(full_prompt_text):
    """Voert native Grok CLI (grok.exe) uit via grok.com account met live websearch."""
    if not GROK_CLI_PATH.exists():
        return None
    import subprocess
    import tempfile

    temp_in = temp_out = temp_err = None
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
            "--prompt-file", temp_in,
        ]
        with open(temp_out, "w", encoding="utf-8") as out_f, open(temp_err, "w", encoding="utf-8") as err_f:
            res = subprocess.run(
                cmd,
                stdin=subprocess.DEVNULL,
                stdout=out_f,
                stderr=err_f,
                timeout=240,
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


def call_grok_engine(system_prompt, user_prompt, openrouter_key=None, max_tokens=2048, temp=0.3):
    sys_m, kluis = mask(system_prompt or "")
    usr_m, kluis = mask(user_prompt or "", kluis)
    full_prompt = f"Systeem: {sys_m}\n\nOpdracht & Inhoud:\n{usr_m}"
    native_res = execute_native_grok(full_prompt)
    if native_res:
        return restore(native_res, kluis)
    return model_bus.complete("grok", system_prompt, user_prompt, temperature=temp, max_tokens=max_tokens)


def call_deepseek_engine(system_prompt, user_prompt, max_tokens=2048, temp=0.2):
    return model_bus.complete("deepseek", system_prompt, user_prompt, temperature=temp, max_tokens=max_tokens)


def run_fh01_incoming_intake(incoming_path: Path):
    """Voert het 2-Staps Invoer-Filter uit Protocol FH-01 (§7.2) uit op een binnengekomen bericht."""
    incoming_path = Path(incoming_path)
    if not incoming_path.exists():
        print(f"[!] Binnengekomen bestand niet gevonden: {incoming_path}")
        return None

    raw_text = incoming_path.read_text(encoding="utf-8", errors="replace")
    keten_goals = ""
    keten_file = ROOT_DIR / "Ketengrootboek" / "ketengrootboek.json"
    if keten_file.exists():
        try:
            kdata = json.loads(keten_file.read_text(encoding="utf-8"))
            open_posten = [
                f"- {r}: {info.get('keten_diagnose')}"
                for r, info in kdata.get("rekeningen_grootboek", {}).items()
                if not info.get("materieel_vereffend", False)
            ]
            keten_goals = "\n".join(open_posten)
        except Exception:
            pass

    prompts = SBARProtocol.build_fh01_intake_prompts(
        raw_incoming_text=raw_text,
        keten_goals=keten_goals or "Volledige materiële tegenboeking en behoud van de geformuleerde hulpvraag.",
    )

    print("[FH-01 Stap 1] Zuiver Memoriaal & Taalkundige Lezingen (zonder doelen/strategie)...")
    sys_step1 = "Je bent een neutrale feitenregistrator conform Protocol FH-01 Stap 1. Geen doelen, geen strategie, sussen noch demoniseren."
    step1_out = call_deepseek_engine(sys_step1, prompts["step_1_memoriaal_prompt"], max_tokens=1500, temp=0.1)

    print("[FH-01 Stap 2] Koppeling met Ketengrootboek-doelen & Fluwelen Handschoen...")
    sys_step2 = "Je bent de Ketengrootboek- en Tafel-integrator conform Protocol FH-01 Stap 2."
    step2_user = f"UITKOMST STAP 1 (ZUIVER MEMORIAAL):\n{step1_out}\n\n{prompts['step_2_koppeling_prompt']}"
    step2_out = call_deepseek_engine(sys_step2, step2_user, max_tokens=1800, temp=0.2)

    out_dir = ROOT_DIR / "Outgoing_Drafts"
    out_dir.mkdir(parents=True, exist_ok=True)
    intake_report = out_dir / f"FH01_INTAKE_{incoming_path.stem}.md"
    content = (
        f"# Protocol FH-01 Invoer-Filter Rapport: `{incoming_path.name}`\n\n"
        f"## Stap 1 — Zuiver Memoriaal (Laag A) & Taalkundige Werkhypothesen (Laag B)\n\n{step1_out}\n\n"
        f"---\n\n"
        f"## Stap 2 — Koppeling met Ketengrootboek (Laag C) & Transformatie (Laag D)\n\n{step2_out}\n"
    )
    intake_report.write_text(content, encoding="utf-8")
    print(f"[+] Protocol FH-01 Intake Rapport opgeslagen: {intake_report.name}")
    return intake_report


def run_constructive_audit(draft_path, is_critical=False):
    root_dir = ROOT_DIR
    draft_path = Path(draft_path)

    if not draft_path.exists():
        print(f"[!] Fout: Conceptbestand niet gevonden: {draft_path}")
        return

    with open(draft_path, "r", encoding="utf-8") as f:
        draft_content = f.read()

    from veto_gate import CLINICAL_KEYWORDS, VetoGate

    poort_voor = VetoGate(root_dir=root_dir).check_draft(
        draft_content,
        slot_metadata={"name": "lokaal loket", "ingest_capacity": ["productcodes", "termijnen", "privacy"]},
    )
    klinisch_eruit = any(
        (not item.get("passed", True)) and item.get("rule") == "VETO_1_PAYLOAD_SLOT_INGEST"
        for item in poort_voor.get("results", [])
    )
    draft_voor_model = draft_content
    if klinisch_eruit:
        stukken = re.split(r"(?<=[.!?])\s+", draft_content)
        gehouden = [s for s in stukken if not any(re.search(pat, s, re.IGNORECASE) for pat in CLINICAL_KEYWORDS)]
        gehouden.append("Gelet op mijn medische belastbaarheid verzoek ik alle stukken uitsluitend digitaal aan te leveren.")
        draft_voor_model = " ".join(gehouden)
        print("[*] Veto vóór de audit: klinische zinnen blijven lokaal en gaan niet naar het model.")

    print(f"[*] Dossier Hub               : {root_dir.name}")
    print(f"[*] Te auditen conceptbrief    : {draft_path.name}")

    doctrine_context = load_doctrine(root_dir)
    dossier_context = load_dossier_context(root_dir)
    huizen = model_bus.available()
    has_ds = huizen.get("deepseek", False)
    has_grok = GROK_CLI_PATH.exists() or huizen.get("grok", False)
    has_multi = has_ds and has_grok
    grok_label = "Native Grok-4.6 (grok.com + live websearch)" if GROK_CLI_PATH.exists() else "Grok via ModelBus"
    print(f"[*] Modus                     : {'DIALECTISCH MULTI-MODEL (DeepSeek + ' + grok_label + ')' if has_multi else 'MODELBUS SINGLE/FALLBACK'}")
    if is_critical and has_multi:
        print("[*] Verificatieniveau         : NIVEAU 3 — KRUISLINGSE FALSIFICATIE ACTIEF")

    sys_deepseek = (
        "Je bent DeepSeek in de Civic Helper. Jouw rol: Wetstechnische en logische auditor van een burger-conceptbrief. "
        "Methodologie: 'Bekijk kritisch, verrijk, verfijn en vul aan'. "
        "Toets strikt op: 1. Wetsartikelen (Awb, Wmo, AVG, Woo, Rv), termijnen en eventuele premature stappen. "
        "2. Feitelijke consistentie met het onderliggende dossier en de chronologie. "
        "3. Protocol FH-01: 100% behoud van ketendoelen (geen sussen), geen vijandtaal (geen demoniseren), "
        "en professionele ruimte van de ontvanger intact laten. "
        "Geen beleefdheidsfrutsels of filler words; wees scherp, direct en constructief."
    )
    user_deepseek = (
        f"GELADEN DOCTRINE:\n{doctrine_context}\n\n"
        f"DOSSIERFEITEN & CHRONOLOGIE:\n{dossier_context}\n\n"
        f"CONCEPTBRIEF TER BEOORDELING ({draft_path.name}):\n\"\"\"\n{draft_voor_model}\n\"\"\"\n\n"
        "Geef een gestructureerde wetstechnische en logische audit voor het dossier. "
        "Benoem ontbrekende wetsartikelen in dit rapport. Zet ze niet in de brief zelf als het loket lokaal Nederlands is."
    )

    sys_grok = (
        "Je bent Grok in de Civic Helper. Jouw rol: Strategische en communicatieve reviewer van een burger-conceptbrief. "
        "Methodologie: 'Bekijk kritisch, verrijk, verfijn en vul aan' + Protocol FH-01 (Fluwelen Handschoen). "
        "Toets scherp op: "
        "1. De machtsdynamiek met bureaucratieën (voorkom dat ambtenaren of artsen in de weerstand schieten). "
        "2. 'The Velvet Glove' & FH-01: ontwapenend, hoffelijk, waardig, inhoudelijk 100% behouden, maar zonder "
        "de professionele bevoegdheid van de ontvanger te dicteren en zonder manipulatieve Agency Inversion. "
        "Geen robot-steno, gewone Nederlandse zinnen, scherpe kern."
    )
    user_grok = (
        f"CONCEPTBRIEF TER BEOORDELING ({draft_path.name}):\n\"\"\"\n{draft_voor_model}\n\"\"\"\n\n"
        "Toets deze conceptbrief scherp op machtsdynamiek, Protocol FH-01 en The Velvet Glove. "
        "Geef direct 3 concrete verbeterpunten en formuleringen in gewone zinnen."
    )

    print("\n[Ronde 1] Parallelle audits uitvoeren (lokaal PII-gemaskeerd via pii_mask.py)...")
    deepseek_audit = "[Niet uitgevoerd]"
    grok_audit = "[Niet uitgevoerd]"

    with ThreadPoolExecutor(max_workers=2) as executor:
        f_ds = executor.submit(call_deepseek_engine, sys_deepseek, user_deepseek, 2048, 0.2) if has_ds else None
        f_grok = executor.submit(call_grok_engine, sys_grok, user_grok, None, 2048, 0.3) if has_grok else None

        if f_ds:
            deepseek_audit = f_ds.result()
        if f_grok:
            grok_audit = f_grok.result()

    grok_on_deepseek = None
    deepseek_on_grok = None

    if is_critical and has_multi:
        print("[Ronde 2] Kruislingse toetsing (Grok toetst DeepSeek & DeepSeek toetst Grok)...")
        sys_cross_grok = "Je bent Grok. Toets DeepSeeks audit op feitelijke overclaims, wettekst-hallucinaties en praktische houdbaarheid."
        user_cross_grok = f"ORIGINEEL:\n{draft_voor_model[:2000]}\n\nDEEPSEEK AUDIT:\n{deepseek_audit}\n\nBeoordeel DeepSeeks conclusies scherp en feitelijk."

        sys_cross_ds = "Je bent DeepSeek. Toets Groks audit op logische gaten, aannames en procedurele consistentie."
        user_cross_ds = f"ORIGINEEL:\n{draft_voor_model[:2000]}\n\nGROK AUDIT:\n{grok_audit}\n\nBeoordeel Groks aanbevelingen analytisch."

        with ThreadPoolExecutor(max_workers=2) as executor:
            f_cg = executor.submit(call_grok_engine, sys_cross_grok, user_cross_grok, None, 1500, 0.3)
            f_cds = executor.submit(call_deepseek_engine, sys_cross_ds, user_cross_ds, 1500, 0.2)
            grok_on_deepseek = f_cg.result()
            deepseek_on_grok = f_cds.result()

    print("[Ronde 3] Integreren van inzichten tot verzendklare REFINED brief (conform Protocol FH-01)...")
    sys_refine = (
        "Je schrijft de korte brief die een lokaal Nederlands loket of behandelaar kan lezen. "
        "Pas Protocol FH-01 toe: "
        "1. Inhoudscontrole: behoud 100% van de feiten en de concrete hulpvraag. "
        "2. Taalhandeling- & Ruimtecontrole: formuleer als helder verzoek en feitelijke overdracht, "
        "zonder de professionele beslissing van de ontvanger als voldongen feit te dicteren. "
        "3. De wetsartikelen en escalatiedreigingen blijven in het auditrapport; zet ze niet in deze brief. "
        "Lever uitsluitend de brieftekst, zonder inleiding."
    )
    user_refine = (
        f"ORIGINELE CONCEPTBRIEF:\n{draft_voor_model}\n\n"
        f"WAT IN HET RAPPORT BLIJFT (niet overnemen in de brief):\n{deepseek_audit}\n\n"
        f"TOON & FH-01 RICHTLIJN:\n{grok_audit}\n\n"
        "Schrijf de korte brief. De artikelen blijven achterwege."
    )

    refined_letter = draft_voor_model
    for house_candidate in ("deepseek", "nvidia", "gemini", "grok", "qwen", "mistral"):
        if huizen.get(house_candidate, False):
            candidate_out = model_bus.complete(house_candidate, sys_refine, user_refine, temperature=0.2, max_tokens=2500)
            if candidate_out and not candidate_out.startswith("[FOUT"):
                refined_letter = candidate_out
                break

    from two_gate_dispatcher import TwoGateDispatcher

    poort_na = TwoGateDispatcher(root_dir=root_dir).dispatch(
        refined_letter,
        slot_metadata={"name": "lokaal loket", "ingest_capacity": ["productcodes", "termijnen", "privacy"]},
    )
    fh01_rep = SBARProtocol.validate_fh01_transform(refined_letter)
    print(f"[*] Veto na de audit: {poort_na.get('reason')}")
    print(f"[*] Protocol FH-01  : {'✅ GESLAAGD' if fh01_rep.passed else '⚠️ WAARSCHUWING (' + '; '.join(fh01_rep.warnings) + ')'}")

    refined_letter = (
        refined_letter
        + "\n\n---\nDeze brief is nog niet verstuurd. Het sein van de persoon ontbreekt.\n"
        + poort_na.get("reason", "")
        + "\n"
    )

    out_dir = root_dir / "Outgoing_Drafts"
    out_dir.mkdir(parents=True, exist_ok=True)
    report_file = out_dir / f"AUDIT_REPORT_{draft_path.stem}.md"
    refined_file = out_dir / f"REFINED_{draft_path.stem}.md"

    report_md = [
        f"# 🛡️ Dialectisch Multi-Model Audit Rapport: {draft_path.name}\n",
        f"**Doelbestand:** `{draft_path.name}`  \n**Modus:** {'Multi-Model Dialectiek' if has_multi else 'Single-Model / ModelBus'}  ",
        f"**Verificatieniveau:** {'Niveau 3 (Kruislings getoetst)' if is_critical else 'Niveau 2 (Parallel getoetst)'}\n",
        "---\n",
        "## 1. Wetstechnische & Logische Audit (DeepSeek)\n",
        deepseek_audit + "\n",
        "---\n",
        "## 2. Strategische & Velvet Glove Audit (Grok)\n",
        grok_audit + "\n",
    ]

    if grok_on_deepseek and deepseek_on_grok:
        report_md.extend([
            "---\n",
            "## 3. Kruislingse Toets: Grok over DeepSeek (Falsificatie & Feitencontrole)\n",
            grok_on_deepseek + "\n",
            "---\n",
            "## 4. Kruislingse Toets: DeepSeek over Grok (Logica & Consistentie)\n",
            deepseek_on_grok + "\n",
        ])

    # Protocol FH-01 samenvatting
    report_md.extend([
        "\n---\n",
        "## 5. Protocol FH-01 IJkcontroles & Invarianten\n",
        f"- **1. Inhoudscontrole:** {'✅ Behouden' if fh01_rep.inhoud_behouden else '🔴 Ontbrekende doelen: ' + ', '.join(fh01_rep.ontbrekende_doelen)}",
        f"- **2. Taalhandelingcontrole:** {'✅ Zuiver' if fh01_rep.taalhandeling_zuiver else '🔴 Dictaat gedetecteerd'} `{fh01_rep.speech_act_breakdown}`",
        f"- **3. Ruimtecontrole:** {'✅ Professionele ruimte ontvanger intact' if fh01_rep.ruimte_intact else '🔴 Geschonden'}",
        f"- **Negatieve Invariant 1 (Geen Agency Inversion):** {'✅ OK' if fh01_rep.geen_agency_inversion else '🔴 Geschonden'}",
        f"- **Negatieve Invariant 2 (Sussen noch Demoniseren):** {'✅ OK' if fh01_rep.geen_sussen_of_demoniseren else '🔴 Geschonden'}\n",
    ])

    try:
        from chunk_audit import ChunkAuditor

        auditor = ChunkAuditor()
        chunk_res = auditor.audit_text(refined_letter)
        chunk_summary = [
            "\n---\n",
            "## 6. Cognitieve Werkgeheugentoets (Chunk-Audit v0.3)\n",
            "**Toetsingslat:** ≤ 4 chunks per eenheid (Miller/Cowan werkgeheugengrens).  ",
            f"**Uitslag:** {'✅ GESLAAGD (Uitvoerbaar & Scanbaar)' if chunk_res['is_pass'] else '🔴 HYPER-DENSIFICATION GEDETECTEERD'}  ",
            f"**Verdeling:** ✅ Groen (≤4): {chunk_res['green_count']} | 🟡 Geel (5–6): {chunk_res['yellow_count']} | 🔴 Rood (≥7): {chunk_res['red_count']}\n",
        ]
        if not chunk_res["is_pass"]:
            chunk_summary.append(
                "> **Let op:** De multi-LLM audit heeft de tekst juridisch aangescherpt, maar de dichtheid overschrijdt de menselijke verwerkingscapaciteit. Pas de volgorde van Chunk-Audit v0.3 toe (voorbeelden/geschiedenis naar bijlage, regels splitsen).\n"
            )
        report_md.extend(chunk_summary)
    except Exception:
        chunk_res = None

    try:
        from gtid_engine import inspect_incoming_letter_for_gtid

        field = inspect_incoming_letter_for_gtid(refined_letter)
        report_md.extend(["\n---\n", field.markdown()])
    except Exception:
        pass

    with open(report_file, "w", encoding="utf-8") as f:
        f.write("\n".join(report_md))

    with open(refined_file, "w", encoding="utf-8") as f:
        f.write(refined_letter)

    print("\n" + "=" * 72)
    print(" AUDIT SUCCESVOL VOLTOOID")
    print("=" * 72)
    print(f"[+] Audit Rapport opgeslagen  : {report_file.name}")
    print(f"[+] Verzendklare brief gereed : {refined_file.name}")
    if chunk_res:
        if chunk_res["is_pass"]:
            print(f"[+] Chunk-Audit v0.3         : ✅ GESLAAGD ({chunk_res['green_count']}/{chunk_res['total_units']} eenheden groen)")
        else:
            print(f"[!] Chunk-Audit v0.3         : 🔴 WAARSCHUWING ({chunk_res['red_count']} eenheden rood - hyper-densification!)")
    print("=" * 72)


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    root_dir = ROOT_DIR
    drafts_dir = root_dir / "Outgoing_Drafts"
    drafts_dir.mkdir(parents=True, exist_ok=True)

    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = [a for a in sys.argv[1:] if a.startswith("--")]
    is_critical = "--critical" in flags
    is_incoming = "--incoming" in flags

    if args:
        target = Path(args[0])
        if not target.is_absolute():
            target = Path.cwd() / target
    else:
        if is_incoming:
            inc_dir = root_dir / "Incoming_Letters"
            target = get_latest_draft(inc_dir) if inc_dir.exists() else None
        else:
            target = get_latest_draft(drafts_dir)

    if not target or not target.exists():
        print(f"[!] Geen bestand gevonden om te auditen.")
        sys.exit(1)

    if is_incoming:
        run_fh01_incoming_intake(target)
    else:
        run_constructive_audit(target, is_critical=is_critical)


if __name__ == "__main__":
    main()
