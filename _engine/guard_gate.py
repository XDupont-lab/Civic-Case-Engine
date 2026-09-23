#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CIVIC CASE ENGINE — GUARD GATE (DRAAGKRACHT-POORT v1.0)
Pure Python Standard Library (Zero External Dependencies).

DE TWEEDE POORT
===============
De Civic Engine heeft twee poorten:

  1. VETO-GATE (inhoud)      — toetst WAT er gecommuniceerd wordt.
                                Klinische lekken, kanaalzuiverheid, drift, ad hominem.
  2. GUARD-GATE (draagkracht) — toetst of het kanaal en de ACTOR de transmissie
                                überhaupt kunnen dragen.

De Veto-Gate kijkt naar de brief. De Guard-Gate kijkt naar de mens.

WAAROM DIT CRUCIAAL IS
======================
In het Wmo-zaakdossier is de burger onderhevig aan de
biologische klok omega_c. Bij executieve uitputting of overprikkeling bevindt
de menselijke pool zich in:

  [1] ATTRACTOR_LOCK  — dysexecutieve verstarring / gevel-masking
                        (intern vloeiend, maar ontkoppeld van de werkelijkheid)
  [2] METRIC_TRIP     — fysieke crash (acute breuk)

De Guard-Gate zorgt ervoor dat het systeem GEEN uitgaande proceshandelingen
forceert wanneer de draagkracht ontbreekt.

DE VIJF REGIMES (uit Shared_Tools/trf_guard.py)
===============================================
  [0] GROUNDED            geaard, kleine G, voldoende D
  [1] ATTRACTOR_LOCK      ongeaard maar stil (D laag, G hoog)
  [2] METRIC_TRIP         acute breuk (lambda_min <= 0)
  [3] INSUFFICIENT        geen D-meting of NaN/Inf
  [4] ATTENTION_OVERFLOW  I > I_MAX (diffuse focus)

DE DISPATCH-REGELS
==================
  [0] GROUNDED            -> doorgaan
  [1] ATTRACTOR_LOCK      -> escaleren naar Kamer 2 (formele procesvertegenwoordiging)
  [2] METRIC_TRIP         -> STOPPEN; eerst herstellen
  [3] INSUFFICIENT        -> meten (niet beslissen)
  [4] ATTENTION_OVERFLOW  -> focussen (I-as herstellen)
"""

import sys
from pathlib import Path
from typing import Any, Dict, Optional

# Importeer de guard uit Shared_Tools
_SHARED = Path(__file__).resolve().parent.parent.parent / "Shared_Tools"
if str(_SHARED) not in sys.path:
    sys.path.insert(0, str(_SHARED))

try:
    from trf_guard import classify, evaluate, REGIMES
except ImportError:
    # Fallback: minimale inline-implementatie
    REGIMES = {0: "GROUNDED", 1: "ATTRACTOR_LOCK", 2: "METRIC_TRIP",
               3: "INSUFFICIENT", 4: "ATTENTION_OVERFLOW"}

    def classify(G, D, I, lam_min):
        import math
        def bad(v):
            try:
                f = float(v)
                return math.isnan(f) or math.isinf(f)
            except (TypeError, ValueError):
                return True
        if bad(G) or bad(D) or bad(I) or bad(lam_min) or D == 0.0:
            return 3, REGIMES[3]
        if I > 0.80:
            return 4, REGIMES[4]
        if D < 4.95 and G > 0.35:
            return 1, REGIMES[1]
        if lam_min <= 0.0:
            return 2, REGIMES[2]
        return 0, REGIMES[0]

    def evaluate(G, D, I, lam_min=None):
        if lam_min is None:
            lam_min = 1.0 - (G / 1.4648) ** 2 - (D / 23.4589) ** 2 - (I / 0.5591) ** 2
        regime, label = classify(G, D, I, lam_min)
        return {"G": G, "D": D, "I": I, "lambda_min": lam_min,
                "regime": regime, "label": label}


# ---------------------------------------------------------------------------
# Dispatch-regels per regime
# ---------------------------------------------------------------------------
DISPATCH_RULES = {
    0: {
        "action": "PROCEED",
        "severity": "OK",
        "message": "Draagkracht aanwezig. Uitgaande proceshandeling toegestaan.",
        "suggestion": "",
    },
    1: {
        "action": "ESCALATE_KAMER_2",
        "severity": "WARN",
        "message": ("ATTRACTOR_LOCK: de actor is intern vloeiend maar ontkoppeld "
                    "(dysexecutieve verstarring / gevel-masking)."),
        "suggestion": ("Escaleer naar Kamer 2: formele procesvertegenwoordiging "
                       "(bijv. Prakken d'Oliveira) of rust. Forceer geen uitgaande "
                       "handeling."),
    },
    2: {
        "action": "STOP_AND_RECOVER",
        "severity": "REJECT",
        "message": "METRIC_TRIP: acute breuk. De draagkracht is weg.",
        "suggestion": ("Stop alle uitgaande proceshandelingen. Eerst herstellen. "
                       "Geen brieven, geen termijnen, geen besluiten."),
    },
    3: {
        "action": "MEASURE",
        "severity": "WARN",
        "message": "INSUFFICIENT: geen meting (eerste token of numerieke instabiliteit).",
        "suggestion": "Verzamel meer data. Beslis niet op een ontbrekende meting.",
    },
    4: {
        "action": "FOCUS",
        "severity": "WARN",
        "message": "ATTENTION_OVERFLOW: diffuse focus (te veel sporen tegelijk).",
        "suggestion": ("Herstel de I-as: reduceer het aantal actieve sporen. "
                       "Eén conflictlijn per keer."),
    },
}


class GuardResult:
    """Resultaat van de draagkracht-toets."""

    def __init__(self, regime: int, label: str, metrics: Dict[str, Any],
                 action: str, severity: str, message: str, suggestion: str):
        self.regime = regime
        self.label = label
        self.metrics = metrics
        self.action = action
        self.severity = severity
        self.message = message
        self.suggestion = suggestion

    @property
    def passed(self) -> bool:
        """Alleen GROUNDED laat een uitgaande handeling door."""
        return self.regime == 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "regime": self.regime,
            "label": self.label,
            "action": self.action,
            "severity": self.severity,
            "message": self.message,
            "suggestion": self.suggestion,
            "metrics": self.metrics,
        }


class GuardGate:
    """De draagkracht-poort van de Civic Case Engine."""

    def __init__(self, root_dir=None):
        self.root_dir = Path(root_dir) if root_dir else Path(__file__).resolve().parent.parent

    def check_capacity(self, G: float, D: float, I: float,
                       lam_min: Optional[float] = None,
                       D_available: bool = True,
                       i_witness: str = "attention_head_weight_variance") -> GuardResult:
        """Toets de draagkracht van de actor.

        G, D, I: de GDI-assen van de actor-toestand.
        lam_min: optioneel; wordt berekend uit G, D, I indien niet gegeven.
        D_available: False betekent geen vorige toestand (geen D-meting).
        i_witness: welke I-witness is gebruikt (witness-aware overflow-check).
        """
        metrics = evaluate(G, D, I, lam_min, D_available=D_available, i_witness=i_witness)
        regime = metrics["regime"]
        rule = DISPATCH_RULES[regime]
        return GuardResult(
            regime=regime,
            label=metrics["label"],
            metrics=metrics,
            action=rule["action"],
            severity=rule["severity"],
            message=rule["message"],
            suggestion=rule["suggestion"],
        )

    def check_actor_state(self, state: Dict[str, Any]) -> GuardResult:
        """Toets een actor-state dict.

        Verwacht: {"G": float, "D": float, "I": float, "lambda_min": optioneel}
        """
        return self.check_capacity(
            state.get("G", 0.0),
            state.get("D", 0.0),
            state.get("I", 0.0),
            state.get("lambda_min"),
        )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main() -> int:
    import argparse
    import json

    parser = argparse.ArgumentParser(
        description="Civic Case Engine — Guard Gate (draagkracht-poort)")
    parser.add_argument("--json", type=str,
                        help='JSON met G, D, I (en optioneel lambda_min)')
    parser.add_argument("--selftest", action="store_true",
                        help="Draai de ingebouwde test")
    args = parser.parse_args()

    gate = GuardGate()

    if args.selftest:
        print("=" * 74)
        print("GUARD GATE — ZELFTEST")
        print("=" * 74)
        print()
        cases = [
            ("grounded",            0.00, 0.45, 0.00, +0.99, 0, "PROCEED"),
            ("attractor-lock",      1.00, 1.10, 0.00, -1.38, 1, "ESCALATE_KAMER_2"),
            ("metric-trip",         0.60, 50.0, 0.00, -45.0, 2, "STOP_AND_RECOVER"),
            ("eerste token",        0.00, 0.00, 0.00, +1.00, 3, "MEASURE"),
            ("attention-overflow",  0.10, 0.50, 0.95, +0.50, 4, "FOCUS"),
        ]
        ok = 0
        for name, G, D, I, lam, verw_regime, verw_action in cases:
            r = gate.check_capacity(G, D, I, lam)
            good = r.regime == verw_regime and r.action == verw_action
            ok += int(good)
            mark = "OK " if good else "FOUT"
            print(f"  [{mark}] {name:<22} -> [{r.regime}] {r.label:<20} {r.action}")
        print()
        print(f"  Correct: {ok}/{len(cases)}")
        return 0 if ok == len(cases) else 1

    if args.json:
        try:
            data = json.loads(args.json)
        except json.JSONDecodeError as e:
            print(f"FOUT: ongeldige JSON: {e}", file=sys.stderr)
            return 1
        r = gate.check_actor_state(data)
        print(json.dumps(r.to_dict(), indent=2))
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
