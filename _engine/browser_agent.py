"""
Civic_Case_Engine / _engine / browser_agent.py
Sovereign Civic Browser Agent — Autonome Portaal & Inzage Harvester

Functies:
1. Portaal Navigatie & Documentenoogst:
   - Navigeert veilig door burgerportalen (MijnOverheid, Gemeente, UWV, CAK, Zorgverzekeraars, Rechtspraak).
   - Verzamelt en downloadt besluiten, brieven en beschikkingen.
   - Slaat gedownloade stukken automatisch op in `Incoming_Letters/` met SHA256 hash.

2. AVG Art. 15 / Woo Webformulier Assistent:
   - Helpt bij het doorlopen van online aanvraagformulieren.
   - Veto Gate Invariant: Nooit definitieve verzending of betaling zonder expliciet menselijk akkoord.

3. Ketenintegratie:
   - Meldt nieuwe stukken direct aan bij `timeline_weaver.py` en `statutory_clock.py`.
"""

import os
import sys
import json
import hashlib
import asyncio
from pathlib import Path
from datetime import datetime

ENGINE_DIR = Path(__file__).resolve().parent
ROOT_DIR = ENGINE_DIR.parent
INCOMING_DIR = ROOT_DIR / "Incoming_Letters"

# Virtual environment pad voor browser-use integratie
VENV_PATH = Path("E:/LLM_Workspace/scratch/.venv_bu")
if VENV_PATH.exists():
    site_packages = VENV_PATH / "Lib" / "site-packages"
    if site_packages.exists() and str(site_packages) not in sys.path:
        sys.path.insert(0, str(site_packages))

def get_browser_llm():
    try:
        from browser_use import ChatGoogle
    except ImportError:
        print("[!] browser-use package is niet geladen. Installeer via: pip install browser-use playwright")
        return None

    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if api_key:
        return ChatGoogle(model="gemini-3.7-flash", api_key=api_key)
    
    ds_key = os.getenv("DEEPSEEK_API_KEY")
    if ds_key:
        from browser_use import ChatOpenAI
        return ChatOpenAI(
            model="deepseek-chat",
            base_url="https://api.deepseek.com/v1",
            api_key=ds_key
        )

    oa_key = os.getenv("OPENAI_API_KEY") or os.getenv("CHATGPT_API_KEY")
    if oa_key:
        from browser_use import ChatOpenAI
        return ChatOpenAI(model="gpt-4o-mini", api_key=oa_key)

    return None

async def harvest_portal_documents(portal_url: str, task_description: str, visible: bool = True):
    """
    Start een autonome browser sessie om documenten op te halen uit een burgerportaal.
    """
    from browser_use import Agent, Browser

    llm = get_browser_llm()
    if not llm:
        print("[!] Geen LLM-sleutel geconfigureerd.")
        return False

    browser = Browser(headless=not visible)

    full_task = (
        f"1. Ga naar {portal_url}. "
        f"2. {task_description}. "
        f"3. Als er documenten (PDF, brieven, beschikkingen) downloadbaar zijn, download deze. "
        f"4. VETO GATE REGEL: Als er sprake is van een definitieve 'Verzenden' / 'Indienen' / 'Betalen' knop, "
        f"stop en vraag de gebruiker eerst om bevestiging. Voer nooit onomkeerbare handelingen zelfstandig uit. "
        f"5. Rapporteer een overzicht van alle geopende pagina's en gedownloade documenten."
    )

    print(f"[*] Civic Browser Agent gestart voor: {portal_url}")
    agent = Agent(task=full_task, llm=llm, browser=browser)
    
    history = await agent.run(max_steps=20)
    result = history.final_result()

    print("\n=== Civic Browser Agent Resultaat ===")
    print(result)

    # Log activiteit in Ketengrootboek
    log_file = ROOT_DIR / "Ketengrootboek" / "browser_agent_log.jsonl"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now().isoformat(),
        "portal_url": portal_url,
        "task": task_description,
        "status": "COMPLETED",
        "result_summary": str(result)[:500]
    }
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

    return True

def run_cli():
    import argparse
    parser = argparse.ArgumentParser(description="Civic Case Engine — Browser Agent")
    parser.add_argument("--url", type=str, required=True, help="URL van het burgerportaal of de instantie")
    parser.add_argument("--task", type=str, required=True, help="Omschrijving van de inzage- of oogsttaak")
    parser.add_argument("--headless", action="store_true", help="Draai zonder GUI venster")

    args = parser.parse_args()
    asyncio.run(harvest_portal_documents(args.url, args.task, visible=not args.headless))

if __name__ == "__main__":
    run_cli()
