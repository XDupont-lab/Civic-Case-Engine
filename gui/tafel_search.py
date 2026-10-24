#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TAFEL SEARCH — Razendsnel Zoeken door alle Beraadslagingen
Pure Python Standard Library (Zero External Dependencies).

Zoekt direct in TAFEL_INDEX.json zonder duizenden tokens te laden.
Ondersteunt:
  python tafel_search.py "WWB"
  python tafel_search.py --author Grok "toeslagen"
  python tafel_search.py --parked          # toont alle geparkeerde / onuitgewerkte verkenningen
  python tafel_search.py --recent 10       # toont de laatste 10 beurten
"""

from __future__ import annotations

import sys
import os
import json
import argparse
from pathlib import Path

# Force UTF-8 console output on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

GUI_DIR = Path(__file__).resolve().parent
REPO_ROOT = GUI_DIR.parent
WORKSPACE = Path(os.environ.get("CIVIC_WORKSPACE", r"E:\LLM_Workspace" if Path(r"E:\LLM_Workspace").exists() else REPO_ROOT))
AGY_WERK = WORKSPACE / "agy_werk" if (WORKSPACE / "agy_werk").exists() else (REPO_ROOT / "werk")
INDEX_PATH = AGY_WERK / "TAFEL_INDEX.json" if AGY_WERK.exists() else (REPO_ROOT / "TAFEL_INDEX.json")

# ANSI kleuren
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
MAGENTA = "\033[35m"
BLUE = "\033[34m"


def format_author_color(author: str) -> str:
    low = author.lower()
    if "grok" in low:
        return f"{YELLOW}{BOLD}{author}{RESET}"
    if "deepseek" in low:
        return f"{BLUE}{BOLD}{author}{RESET}"
    if "agy" in low:
        return f"{GREEN}{BOLD}{author}{RESET}"
    if "xander" in low:
        return f"{MAGENTA}{BOLD}{author}{RESET}"
    return f"{CYAN}{BOLD}{author}{RESET}"


def search_tafel(query: str = "", author_filter: str = "", parked_only: bool = False, limit: int = 15) -> None:
    if not INDEX_PATH.exists():
        print(f"[!] Geen indexbestand gevonden op {INDEX_PATH}. Draai eerst tafel_indexer.py.")
        return

    data = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    turns = data.get("turns", [])

    results = []
    q_low = query.lower().strip()
    a_low = author_filter.lower().strip()

    for t in turns:
        if a_low and a_low not in t["author"].lower():
            continue
        if parked_only and not t.get("is_parked", False):
            continue

        if not q_low:
            results.append(t)
        else:
            title_match = q_low in t["title"].lower()
            summary_match = q_low in t["summary"].lower()
            kw_match = any(q_low in kw.lower() for kw in t.get("keywords", []))
            author_match = q_low in t["author"].lower()

            if title_match or summary_match or kw_match or author_match:
                results.append(t)

    print(f"\n{BOLD}{CYAN}=== TAFEL ZOEKRESULTATEN ==={RESET}")
    print(f"{DIM}Totaal in index: {len(turns)} beurten | Gevonden: {len(results)} match(es){RESET}\n")

    if not results:
        print(f"{YELLOW}Geen beurten gevonden voor '{query}'.{RESET}\n")
        return

    results_to_show = results[-limit:] if len(results) > limit else results

    for r in results_to_show:
        author_colored = format_author_color(r['author'])
        file_link = f"file:///{r['filepath'].replace('\\', '/')}#L{r['start_line']}"
        active_badge = f"{GREEN}[ACTIEF]{RESET} " if r['file'] == 'TAFEL.md' else f"{DIM}[ARCHIEF]{RESET} "
        parked_badge = f"{YELLOW}[GEPARKEERD/VERKENNING]{RESET} " if r.get('is_parked') else ""

        print(f"{active_badge}{parked_badge}{author_colored} ({CYAN}{r['date_raw']}{RESET}) — {BOLD}{r['title']}{RESET}")
        print(f"  {DIM}Locatie: {r['file']} (regels {r['start_line']}-{r['end_line']}){RESET}")
        print(f"  {DIM}Link:    {file_link}{RESET}")
        if r.get('baton_to') and r['baton_to'] != "Onbekend":
            print(f"  {DIM}Stok naar: {r['baton_to']}{RESET}")
        if r.get('keywords'):
            print(f"  {DIM}Tags:    {', '.join(r['keywords'])}{RESET}")
        if r.get('summary'):
            clean_summary = r['summary'].replace('\n', ' ')
            if len(clean_summary) > 160:
                clean_summary = clean_summary[:160] + "..."
            print(f"  › {clean_summary}")
        print()


def main():
    parser = argparse.ArgumentParser(description="Doorzoek de beraadslagingen van Tafel (live en archief).")
    parser.add_argument("query", nargs="?", default="", help="Zoekterm (titel, inhoud, wetsartikel)")
    parser.add_argument("-a", "--author", default="", help="Filter op auteur (Grok, agy, DeepSeek, Xander)")
    parser.add_argument("-p", "--parked", action="store_true", help="Toon alleen geparkeerde verkenningen en open eindjes")
    parser.add_argument("-n", "--limit", type=int, default=15, help="Maximaal aantal getoonde resultaten (standaard 15)")
    args = parser.parse_args()

    search_tafel(query=args.query, author_filter=args.author, parked_only=args.parked, limit=args.limit)


if __name__ == "__main__":
    main()
