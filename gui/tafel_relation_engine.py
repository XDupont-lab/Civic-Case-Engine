#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TAFEL NON-RAG RELATIE- EN CONSTRAINT-ZOEKER
Gebaseerd op: CivicHelper/ZOEKMETHODEN_NOTITIE_NON_RAG_RELATIES.md
Axioma: Same Entity != Same Constraint.
Geen semantische woordzoekers of TF-IDF woordwolken.

Volgt de gerichte relatie:
- Zender (P_bron) -> Ontvanger (P_doel).
- De overdracht (Besluit, Berekening, Dossierfeit).
- Het residu (delta = 0: Sluiting / Tegenboeking aanwezig; delta > 0: Ketenbreuk / Openstaande vraag).
"""

from __future__ import annotations

import sys
import os
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any

# Force UTF-8 console output on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

GUI_DIR = Path(__file__).resolve().parent
REPO_ROOT = GUI_DIR.parent
_CANDIDATE_WS = REPO_ROOT.parent if (REPO_ROOT.parent / "agy_werk").exists() else REPO_ROOT
WORKSPACE = Path(os.environ.get("CIVIC_WORKSPACE", str(_CANDIDATE_WS)))
AGY_WERK = WORKSPACE / "agy_werk" if (WORKSPACE / "agy_werk").exists() else (REPO_ROOT / "werk")
INDEX_PATH = AGY_WERK / "TAFEL_INDEX.json" if AGY_WERK.exists() else (REPO_ROOT / "TAFEL_INDEX.json")

# ANSI styling
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
MAGENTA = "\033[35m"
BLUE = "\033[34m"
RED = "\033[31m"


def load_index() -> List[Dict[str, Any]]:
    if not INDEX_PATH.exists():
        print(f"[!] TAFEL_INDEX.json niet gevonden op {INDEX_PATH}. Draai eerst tafel_indexer.py.")
        sys.exit(1)
    data = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    return data.get("turns", [])


def print_turn_card(t: Dict[str, Any], prefix: str = "") -> None:
    author = t["author"]
    color = YELLOW if "grok" in author.lower() else (BLUE if "deepseek" in author.lower() else (GREEN if "agy" in author.lower() else MAGENTA))
    file_link = f"file:///{t['filepath'].replace('\\', '/')}#L{t['start_line']}"
    
    print(f"{prefix}{BOLD}{color}{author}{RESET} ({CYAN}{t['date_raw']}{RESET}) — {BOLD}{t['title']}{RESET}")
    print(f"{prefix}  {DIM}Locatie: {t['file']} (L{t['start_line']}-L{t['end_line']}) | Link: {file_link}{RESET}")
    if t.get("addressed"):
        print(f"{prefix}  {DIM}Spreekt aan: {', '.join(t['addressed'])}{RESET}")
    if t.get("baton_to") and t["baton_to"] != "Onbekend":
        print(f"{prefix}  {DIM}Stok naar: {t['baton_to']}{RESET}")
    if t.get("keywords"):
        print(f"{prefix}  {DIM}Overdrachtsdomeinen: {', '.join(t['keywords'])}{RESET}")
    if t.get("summary"):
        print(f"{prefix}  › {t['summary'][:180]}...")
    print()


def cmd_matrix(turns: List[Dict[str, Any]]) -> None:
    """Toont de gerichte overdrachtsmatrix tussen alle actoren aan tafel."""
    actors = ["Xander", "Grok", "agy", "DeepSeek"]
    matrix = {a: {b: 0 for b in actors} for a in actors}
    
    for t in turns:
        sender = t["author"]
        baton = t.get("baton_to", "Onbekend")
        for a in actors:
            if a.lower() in sender.lower():
                for b in actors:
                    if b.lower() in baton.lower():
                        matrix[a][b] += 1
                        
    print(f"\n{BOLD}{CYAN}=== GERICHTE OVERDRACHTSMATRIX AAN TAFEL (P_bron -> P_doel) ==={RESET}\n")
    print(f"{'Zender \\ Ontvanger':<22} | " + " | ".join(f"{a:<10}" for a in actors))
    print("-" * 75)
    for a in actors:
        row = [f"{matrix[a][b]:<10}" for b in actors]
        print(f"{a:<22} | " + " | ".join(row))
    print()


def cmd_gap(turns: List[Dict[str, Any]]) -> None:
    """Vindt de 'Ketenbreuken' aan tafel: beurten met openstaand residu (delta > 0)."""
    print(f"\n{BOLD}{RED}=== NON-RAG GAP ANALYSE: OPENSTAANDE RESIDUEN & PARKEERSPEREN (delta > 0) ==={RESET}\n")
    
    gaps = []
    for i in range(len(turns)):
        t = turns[i]
        is_parked = t.get("is_parked", False)
        
        baton = t.get("baton_to", "Onbekend")
        unanswered_baton = False
        if i + 1 < len(turns) and baton not in ["Onbekend", "Jullie"]:
            next_turn = turns[i + 1]
            if baton.lower() not in next_turn["author"].lower() and next_turn["author"].lower() not in baton.lower():
                unanswered_baton = True
                
        if is_parked or unanswered_baton:
            gaps.append((t, is_parked, unanswered_baton, baton))
            
    print(f"{DIM}Totaal beurten met openstaand residu of overdrachtsverschuiving: {len(gaps)}{RESET}\n")
    for t, parked, unanswered, expected in gaps[-12:]:
        badge = f"{YELLOW}[GEPARKEERD/VERKENNING]{RESET} " if parked else ""
        if unanswered:
            badge += f"{RED}[STOK-VERSCHUIVING: mikte op {expected}]{RESET} "
        print_turn_card(t, prefix=badge)


def cmd_trace(turns: List[Dict[str, Any]], domain: str) -> None:
    """Volgt de causale keten van één specifiek overdrachtsdomein."""
    d_low = domain.lower()
    print(f"\n{BOLD}{CYAN}=== NON-RAG CAUSALE TRACE: DOMEIN '{domain}' ==={RESET}\n")
    
    chain = []
    for t in turns:
        if any(d_low in kw.lower() for kw in t.get("keywords", [])) or d_low in t["title"].lower():
            chain.append(t)
            
    if not chain:
        print(f"{YELLOW}Geen overdrachten gevonden voor domein '{domain}'.{RESET}\n")
        return
        
    print(f"{DIM}Causale keten bevat {len(chain)} opeenvolgende overdrachten:{RESET}\n")
    for i, t in enumerate(chain, 1):
        arrow = " └─► " if i > 1 else " ┌── "
        print_turn_card(t, prefix=arrow)


def cmd_relation(turns: List[Dict[str, Any]], sender: str, receiver: str) -> None:
    """Filtert op gerichte interacties tussen twee specifieke actoren (P_i -> P_j)."""
    s_low = sender.lower()
    r_low = receiver.lower() if receiver else ""
    
    print(f"\n{BOLD}{CYAN}=== GERICHTE RELATIES: {sender} -> {receiver or 'Iedereen'} ==={RESET}\n")
    
    matches = []
    for t in turns:
        if s_low in t["author"].lower():
            if not r_low:
                matches.append(t)
            else:
                baton_match = r_low in t.get("baton_to", "").lower()
                addr_match = any(r_low in a.lower() for a in t.get("addressed", []))
                if baton_match or addr_match:
                    matches.append(t)
                    
    print(f"{DIM}Gevonden overdrachten: {len(matches)}{RESET}\n")
    for t in matches[-10:]:
        print_turn_card(t)


def main():
    parser = argparse.ArgumentParser(description="Non-RAG Constraint & Relatie-Zoeker voor Tafel (Civic Helper).")
    sub = parser.add_subparsers(dest="subcommand", help="Kies analyse")
    
    sub.add_parser("matrix", help="Toon de overdrachtsmatrix tussen actoren")
    sub.add_parser("gap", help="Toon openstaande residuen (delta > 0) en geparkeerde verkenningen")
    
    p_trace = sub.add_parser("trace", help="Volg de causale keten van een domein (bijv. WWB, C6, Toeslagen)")
    p_trace.add_argument("domain", help="Het overdrachtsdomein")
    
    p_rel = sub.add_parser("rel", help="Toon gerichte overdrachten tussen actoren (P_i -> P_j)")
    p_rel.add_argument("--from-actor", "-f", required=True, help="Zendende actor (bijv. DeepSeek, Grok, agy, Xander)")
    p_rel.add_argument("--to-actor", "-t", default="", help="Ontvangende actor")
    
    args = parser.parse_args()
    turns = load_index()
    
    if args.subcommand == "matrix":
        cmd_matrix(turns)
    elif args.subcommand == "gap":
        cmd_gap(turns)
    elif args.subcommand == "trace":
        cmd_trace(turns, args.domain)
    elif args.subcommand == "rel":
        cmd_relation(turns, args.from_actor, args.to_actor)
    else:
        cmd_matrix(turns)
        cmd_gap(turns)


if __name__ == "__main__":
    main()
