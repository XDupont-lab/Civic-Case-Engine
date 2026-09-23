#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CIVIC CASE ENGINE — TWEE-POORTEN-DISPATCHER (v1.0)
Pure Python Standard Library (Zero External Dependencies).

DE TWEE POORTEN
===============
De Civic Engine heeft twee onafhankelijke poorten:

  1. VETO-GATE (inhoud)      — toetst WAT er gecommuniceerd wordt.
                                Klinische lekken, kanaalzuiverheid, drift, ad hominem.
  2. GUARD-GATE (draagkracht) — toetst of het kanaal en de ACTOR de transmissie
                                überhaupt kunnen dragen.

DE DISPATCH-LOGICA
==================
Beide poorten moeten passeren. En de volgorde is beslissend:

  1. GUARD-GATE eerst   — als de actor niet kan dragen, is de inhoud irrelevant.
  2. VETO-GATE daarna   — als de inhoud niet zuiver is, gaat het stuk niet uit.

WAAROM DEZE VOLGORDE
====================
Als de actor in METRIC_TRIP zit (fysieke crash), dan is het niet zinvol om de
briefinhoud te toetsen. Eerst herstellen. De inhoud komt later.

En als de actor in ATTRACTOR_LOCK zit (dysexecutieve verstarring), dan is de
kans groot dat de brief zelf een zelfbevestigende lus is. Dus escaleren naar
Kamer 2, niet doorstampen.
"""

import sys
from pathlib import Path
from typing import Any, Dict, Optional

_ENGINE = Path(__file__).resolve().parent
if str(_ENGINE) not in sys.path:
    sys.path.insert(0, str(_ENGINE))

from veto_gate import VetoGate
from guard_gate import GuardGate


class TwoGateDispatcher:
    """De dispatcher met twee poorten: draagkracht en inhoud."""

    def __init__(self, root_dir=None):
        self.root_dir = Path(root_dir) if root_dir else Path(__file__).resolve().parent.parent
        self.veto = VetoGate(root_dir=self.root_dir)
        self.guard = GuardGate(root_dir=self.root_dir)

    def dispatch(self,
                 text: str,
                 actor_state: Optional[Dict[str, Any]] = None,
                 slot_metadata: Optional[Dict[str, Any]] = None,
                 has_local_discours: bool = False) -> Dict[str, Any]:
        """Toets een uitgaande handeling aan beide poorten.

        text: de concepttekst
        actor_state: {"G":..., "D":..., "I":..., "lambda_min": optioneel}
        slot_metadata: metadata van het doel-slot
        has_local_discours: of er een actief L2-discours is

        Returns een dict met:
          - allowed: bool (mag het stuk de deur uit?)
          - guard: het GuardResult
          - veto: de lijst VetoResults
          - reason: waarom wel/niet
        """
        actor_state = actor_state or {"G": 0.0, "D": 0.45, "I": 0.0, "lambda_min": 0.99}

        # POORT 1: draagkracht
        guard_result = self.guard.check_actor_state(actor_state)

        if not guard_result.passed:
            return {
                "allowed": False,
                "gate": "GUARD",
                "guard": guard_result.to_dict(),
                "veto": [],
                "reason": (f"Draagkracht-poort: {guard_result.label}. "
                           f"Actie: {guard_result.action}. {guard_result.suggestion}"),
            }

        # POORT 2: inhoud
        # veto_gate.check_draft geeft een dict: {all_passed, has_rejections, results}
        veto_report = self.veto.check_draft(
            text,
            slot_metadata=slot_metadata,
            has_local_discours=has_local_discours,
        )
        veto_dicts = veto_report.get("results", [])
        rejects = [v for v in veto_dicts if v.get("severity") == "REJECT"]
        warns = [v for v in veto_dicts if v.get("severity") == "WARN"]

        if rejects:
            return {
                "allowed": False,
                "gate": "VETO",
                "guard": guard_result.to_dict(),
                "veto": veto_dicts,
                "reason": (f"Inhoud-poort: {len(rejects)} REJECT(s). "
                           f"Eerste: {rejects[0].get('rule')} — "
                           f"{rejects[0].get('suggestion')}"),
            }

        return {
            "allowed": True,
            "gate": None,
            "guard": guard_result.to_dict(),
            "veto": veto_dicts,
            "reason": (f"Beide poorten gepasseerd. "
                       f"{len(warns)} waarschuwing(en)." if warns
                       else "Beide poorten gepasseerd."),
        }


def main() -> int:
    import argparse
    import json

    parser = argparse.ArgumentParser(
        description="Civic Case Engine — twee-poorten-dispatcher")
    parser.add_argument("--text", type=str, default="",
                        help="De concepttekst")
    parser.add_argument("--actor", type=str, default=None,
                        help='JSON met G, D, I (en optioneel lambda_min)')
    parser.add_argument("--selftest", action="store_true",
                        help="Draai de ingebouwde test")
    args = parser.parse_args()

    d = TwoGateDispatcher()

    if args.selftest:
        print("=" * 78)
        print("TWEE-POORTEN-DISPATCHER — ZELFTEST")
        print("=" * 78)
        print()

        # Een schone brief (met schriftelijkheidsclausule)
        clean_text = ("Geachte heer, mevrouw,\n\n"
                      "Ik verzoek u de stukken uitsluitend schriftelijk per e-mail "
                      "aan te leveren.\n\nMet vriendelijke groet.")

        # Een brief met een klinisch lek
        leaky_text = ("Geachte heer, mevrouw,\n\n"
                      "Mijn stoma en darmproblematiek maken dit moeilijk.\n\n"
                      "Met vriendelijke groet.")

        cases = [
            ("grounded + schone brief",
             {"G": 0.0, "D": 0.45, "I": 0.0, "lambda_min": 0.99}, clean_text, True),
            ("grounded + klinisch lek",
             {"G": 0.0, "D": 0.45, "I": 0.0, "lambda_min": 0.99}, leaky_text, False),
            ("ATTRACTOR_LOCK + schone brief",
             {"G": 1.0, "D": 1.10, "I": 0.0, "lambda_min": -1.38}, clean_text, False),
            ("METRIC_TRIP + schone brief",
             {"G": 0.6, "D": 50.0, "I": 0.0, "lambda_min": -45.0}, clean_text, False),
        ]

        for name, actor, text, verwacht_allowed in cases:
            r = d.dispatch(text, actor_state=actor)
            good = r["allowed"] == verwacht_allowed
            mark = "OK " if good else "FOUT"
            gate = r["gate"] or "-"
            print(f"  [{mark}] {name:<34} allowed={r['allowed']!s:<5} gate={gate}")
            print(f"         {r['reason'][:100]}")

        print()
        return 0

    actor = json.loads(args.actor) if args.actor else None
    r = d.dispatch(args.text, actor_state=actor)
    print(json.dumps(r, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
