#!/usr/bin/env python3
"""
CIVIC CASE ENGINE — GLUE CHECK (CT v1.0 & Addendum II Kernel Verifier)
Pure Python Standard Library (Zero External Dependencies).

Implements the formal Definition 4 & Addendum II Admissibility and Gluing Tests:
  Axiom P1: An admissibility verdict is only as strong as the provided interface test;
            no verdict without witness.
  Axiom P2: Global invariants = admissible groupoid Casimirs.

Tests evaluated for interface f: P_i -> P_j:
  1. Def4.A: Admissibility preservation (f(A_i) ⊆ A_j)
  2. Def4.R: Representation transport (Rep_j ∘ f = T_ij ∘ Rep_i)
  3. Def4.O: Observable & Casimir transport (f_*(Casimir(P_i)) ⊆ Casimir(P_j) ∪ Obs_P_j)
  4. Def4.G: Gate compatibility & alignment on anchor events

Outputs a proof-carrying kernel evaluation trace and discrete verdict:
  ADMISSIBLE or GLUING_FAILURE + locus (C, f, Gate).
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")



def sha256_file(filepath: Path) -> Optional[str]:
    """Computes SHA-256 hash of a file if it exists."""
    if not filepath.is_file():
        return None
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


class Def4Result:
    def __init__(
        self,
        test_id: str,
        name: str,
        passed: bool,
        details: Dict[str, Any],
        witness: Optional[str] = None,
    ):
        self.test_id = test_id
        self.name = name
        self.passed = passed
        self.details = details
        self.witness = witness

    def to_dict(self) -> Dict[str, Any]:
        return {
            "test_id": self.test_id,
            "name": self.name,
            "passed": self.passed,
            "details": self.details,
            "witness": self.witness,
        }


class InterfaceVerdict:
    def __init__(
        self,
        interface_id: str,
        evaluated_at: str,
        verdict: str,
        locus: Optional[Tuple[str, str, str]],
        tests: Dict[str, Def4Result],
        anchor_event: Dict[str, Any],
        response_event: Optional[Dict[str, Any]],
        formal_intake: str,
        obs_missing: List[str],
        omega_star: Dict[str, Any],
    ):
        self.interface_id = interface_id
        self.evaluated_at = evaluated_at
        self.verdict = verdict  # "ADMISSIBLE" or "GLUING_FAILURE"
        self.locus = locus      # (C_loss, interface_id, failed_gate)
        self.tests = tests
        self.anchor_event = anchor_event
        self.response_event = response_event
        self.formal_intake = formal_intake
        self.obs_missing = obs_missing
        self.omega_star = omega_star

    def format_trace(self) -> str:
        """Formats the raw evaluation trace matching CT kernel requirements."""
        lines = []
        lines.append("=" * 80)
        lines.append(f"CT-KERNEL / GLUE-CHECK v1.0 (Def. 4 & Addendum II Compliance)")
        lines.append("=" * 80)
        lines.append(f"interface:       {self.interface_id}")
        lines.append(f"evaluated_at:    {self.evaluated_at}")

        # Anchor Event
        anc = self.anchor_event
        anc_hash = anc.get("sha256") or "NO_FILE"
        anc_hash_short = anc_hash[:16] + "..." if len(anc_hash) > 16 else anc_hash
        lines.append(f"anchor_event:    {anc.get('event_id', 'UNKNOWN')} hash={anc_hash_short} date={anc.get('date', 'UNKNOWN')}")
        if anc.get("description"):
            lines.append(f"                 desc=\"{anc.get('description')}\"")

        # Response Event
        resp = self.response_event
        if resp:
            resp_hash = resp.get("sha256") or "NO_FILE"
            resp_hash_short = resp_hash[:16] + "..." if len(resp_hash) > 16 else resp_hash
            lines.append(f"response_event:  {resp.get('event_id', 'UNKNOWN')} hash={resp_hash_short} date={resp.get('date', 'UNKNOWN')}")
            if resp.get("description"):
                lines.append(f"                 desc=\"{resp.get('description')}\"")
        else:
            lines.append(f"response_event:  ABSENT")

        lines.append(f"formal_intake:   {self.formal_intake}")
        lines.append("")

        # Def4.A
        t_a = self.tests["Def4.A"]
        a_status = "PASS" if t_a.passed else "FAIL"
        lines.append(f"Def4.A  admissibility_preservation: {a_status}")
        if t_a.witness:
            lines.append(f"        witness: {t_a.witness}")
        if t_a.details.get("mapping"):
            lines.append(f"        mapping: {t_a.details['mapping']}")

        # Def4.R
        t_r = self.tests["Def4.R"]
        r_status = "PASS" if t_r.passed else "FAIL"
        lines.append(f"Def4.R  rep_transport:              {r_status}")
        if t_r.details.get("missing_fields"):
            lines.append(f"        missing_fields: [{', '.join(t_r.details['missing_fields'])}]")
        if t_r.details.get("source_rep"):
            lines.append(f"        source_rep:     \"{t_r.details['source_rep']}\"")
        if t_r.details.get("target_rep"):
            lines.append(f"        target_rep:     \"{t_r.details['target_rep']}\"")

        # Def4.O
        t_o = self.tests["Def4.O"]
        o_status = "PASS" if t_o.passed else "FAIL"
        lines.append(f"Def4.O  observable_transport:       {o_status}")
        for c_info in t_o.details.get("casimirs", []):
            lines.append(f"        {c_info['id']}: in_source={c_info['in_source']}  in_target_obs={c_info['in_target_obs']}  in_target_casimir={c_info['in_target_casimir']}")
            if c_info.get("loss"):
                lines.append(f"        → CASIMIR_LOSS ({c_info['loss_detail']})")
        for o_info in t_o.details.get("observables", []):
            lines.append(f"        {o_info['id']}: in_source={o_info['in_source']}  in_target_obs={o_info['in_target_obs']} ({o_info.get('note', '')})")

        # Def4.G
        t_g = self.tests["Def4.G"]
        g_status = "PASS" if t_g.passed else "FAIL"
        lines.append(f"Def4.G  gate_align:                 {g_status}")
        sg = t_g.details.get("source_gate", {})
        tg = t_g.details.get("target_gate", {})
        lines.append(f"        source_gate \"{sg.get('name', 'UNKNOWN')}\": {'PASS' if sg.get('satisfied') else 'FAIL'} ({sg.get('note', '')})")
        lines.append(f"        target_gate \"{tg.get('name', 'UNKNOWN')}\": {'PASS' if tg.get('satisfied') else 'FAIL'} ({tg.get('note', '')})")

        lines.append("")
        lines.append("-" * 80)
        lines.append(f"verdict:     {self.verdict}")
        if self.locus:
            lines.append(f"locus:       ({self.locus[0]}, {self.locus[1]}, {self.locus[2]})")
        else:
            lines.append(f"locus:       NONE (All Def. 4 conditions satisfied)")
        lines.append(f"obs_missing: [{', '.join(self.obs_missing)}]")
        lines.append(f"omega_star:  started={str(self.omega_star.get('started', False)).lower()}  reason={self.omega_star.get('reason', 'unspecified')}")
        lines.append("=" * 80)
        return "\n".join(lines)


class GlueChecker:
    def __init__(self, root_dir: Optional[Path] = None):
        # Default root is Civic_Case_Engine parent or Civic_Case_Engine
        if root_dir is None:
            self.engine_dir = Path(__file__).resolve().parent.parent
        else:
            self.engine_dir = Path(root_dir)
        self.workspace_root = self.engine_dir.parent if self.engine_dir.name == "Civic_Case_Engine" else self.engine_dir

    def _resolve_file(self, rel_path: str) -> Optional[Path]:
        """Resolves file path in engine_dir or workspace_root or local E:\\LLM_Workspace."""
        if not rel_path:
            return None
        p1 = self.engine_dir / rel_path
        if p1.is_file():
            return p1
        p2 = self.workspace_root / rel_path
        if p2.is_file():
            return p2
        p3 = Path(r"E:\LLM_Workspace") / rel_path
        if p3.is_file():
            return p3
        return None


    def evaluate_interface(self, iface: Dict[str, Any]) -> InterfaceVerdict:
        """Evaluates an interface object against Def. 4 and Addendum II."""
        iface_id = iface.get("id", "UNKNOWN_IFACE")
        evaluated_at = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")

        # 1. Anchor & Response Event Resolution & Witness Hashing
        anchor_data = dict(iface.get("anchor", {}))
        anchor_file_path = self._resolve_file(anchor_data.get("witness_file", ""))
        if anchor_file_path:
            anchor_data["sha256"] = sha256_file(anchor_file_path)
            anchor_data["resolved_path"] = str(anchor_file_path)

        resp_data = None
        if "response" in iface:
            resp_data = dict(iface["response"])
            resp_file_path = self._resolve_file(resp_data.get("witness_file", ""))
            if resp_file_path:
                resp_data["sha256"] = sha256_file(resp_file_path)
                resp_data["resolved_path"] = str(resp_file_path)

        formal_intake = "PRESENT" if resp_data and resp_data.get("target_formal_intake") else "ABSENT"

        # -------------------------------------------------------------
        # Def4.A: Admissibility Preservation (f(A_i) ⊆ A_j)
        # -------------------------------------------------------------
        from_chart = iface.get("from_chart", {})
        to_chart = iface.get("to_chart", {})
        # Domain boundary check: does receiving authority have statutory capacity for domain?
        domain_admissible = bool(to_chart.get("domain") in ("Zorg en Gezondheid", "Financiën en Bestaanszekerheid", "Huisvesting en Leefomgeving"))
        witness_exists = bool(anchor_file_path and anchor_file_path.exists())
        def4_a_passed = domain_admissible and witness_exists
        def4_a = Def4Result(
            test_id="Def4.A",
            name="admissibility_preservation",
            passed=def4_a_passed,
            details={
                "mapping": f"f(A_{from_chart.get('id', 'src')}) ⊆ A_{to_chart.get('id', 'tgt')} ({to_chart.get('carrier')} jurisdiction)",
                "witness_verified": witness_exists,
            },
            witness=str(anchor_file_path.relative_to(self.workspace_root)) if (anchor_file_path and self.workspace_root in anchor_file_path.parents) else (str(anchor_file_path) if anchor_file_path else None)
        )

        # -------------------------------------------------------------
        # Def4.R: Representation Transport (Rep_j ∘ f = T_ij ∘ Rep_i)
        # -------------------------------------------------------------
        translation = iface.get("translation", {})
        req_fields = translation.get("required_target_fields", [])
        mapped_fields = translation.get("mapped_fields", [])
        missing_fields = [f for f in req_fields if f not in mapped_fields]
        def4_r_passed = (len(missing_fields) == 0 and len(req_fields) > 0)
        def4_r = Def4Result(
            test_id="Def4.R",
            name="rep_transport",
            passed=def4_r_passed,
            details={
                "source_rep": translation.get("source_representation", ""),
                "target_rep": translation.get("target_representation", ""),
                "required_fields": req_fields,
                "mapped_fields": mapped_fields,
                "missing_fields": missing_fields,
            }
        )

        # -------------------------------------------------------------
        # Def4.O: Observable & Casimir Transport (Addendum II)
        # Invariants must satisfy: f_*(Casimir(P_i)) ⊆ Casimir(P_j) ∪ Obs_P_j
        # -------------------------------------------------------------
        invariants = iface.get("invariants", {})
        declared_casimirs = invariants.get("declared_casimirs", [])
        micro_observables = invariants.get("micro_observables", [])

        casimir_results = []
        any_casimir_loss = False
        locus_casimir = None

        for c in declared_casimirs:
            in_src = c.get("in_source", True)
            in_tgt_obs = c.get("in_target_obs", False)
            in_tgt_cas = c.get("in_target_casimir", False)
            loss = in_src and not (in_tgt_obs or in_tgt_cas)
            if loss:
                any_casimir_loss = True
                if locus_casimir is None:
                    locus_casimir = c.get("id", "C_unnamed")
            casimir_results.append({
                "id": c.get("id", "C_unnamed"),
                "in_source": in_src,
                "in_target_obs": in_tgt_obs,
                "in_target_casimir": in_tgt_cas,
                "loss": loss,
                "loss_detail": "Addendum II violation: source clinical invariant unobserved in target",
            })

        obs_results = []
        for o in micro_observables:
            obs_results.append({
                "id": o.get("id", "O_unnamed"),
                "in_source": o.get("in_source", True),
                "in_target_obs": o.get("in_target_obs", False),
                "note": o.get("description", ""),
            })

        def4_o_passed = (not any_casimir_loss) and (len(declared_casimirs) > 0)
        def4_o = Def4Result(
            test_id="Def4.O",
            name="observable_transport",
            passed=def4_o_passed,
            details={
                "casimirs": casimir_results,
                "observables": obs_results,
            }
        )

        # -------------------------------------------------------------
        # Def4.G: Gate Alignment on Anchor Events
        # -------------------------------------------------------------
        gate_info = iface.get("gate", {})
        sg = gate_info.get("source_gate", {})
        tg = gate_info.get("target_gate", {})
        sg_satisfied = sg.get("satisfied", False)
        tg_satisfied = tg.get("satisfied", False)

        def4_g_passed = sg_satisfied and tg_satisfied
        def4_g = Def4Result(
            test_id="Def4.G",
            name="gate_align",
            passed=def4_g_passed,
            details={
                "source_gate": {
                    "name": sg.get("name", "source_gate"),
                    "satisfied": sg_satisfied,
                    "note": "witnessed alert transmitted" if sg_satisfied else "source gate unmet",
                },
                "target_gate": {
                    "name": tg.get("name", "target_gate"),
                    "satisfied": tg_satisfied,
                    "note": "statutory response duty discharged" if tg_satisfied else f"no typed intake before response/denial ({resp_data.get('date', 'unspecified') if resp_data else 'absent'})",
                },
            }
        )

        tests = {
            "Def4.A": def4_a,
            "Def4.R": def4_r,
            "Def4.O": def4_o,
            "Def4.G": def4_g,
        }

        # -------------------------------------------------------------
        # Synthesize Verdict & Locus
        # -------------------------------------------------------------
        all_passed = def4_a.passed and def4_r.passed and def4_o.passed and def4_g.passed
        verdict = "ADMISSIBLE" if all_passed else "GLUING_FAILURE"

        # Locus calculation: (C_loss, interface_id, failed_gate)
        locus = None
        if not all_passed:
            c_tag = locus_casimir or "C_none"
            gate_tag = tg.get("name", "Gate_target") if not tg_satisfied else "Gate_none"
            locus = (c_tag, iface_id, gate_tag)

        # Missing observables
        obs_missing = []
        if not def4_r.passed:
            for fld in missing_fields:
                obs_missing.append(fld)
        if any_casimir_loss:
            for c_res in casimir_results:
                if c_res["loss"]:
                    obs_missing.append(f"gemeentelijke_registratie_{c_res['id']}")

        # Statutory clock (omega_star) evaluation
        started = formal_intake == "PRESENT"
        omega_star = {
            "started": started,
            "reason": "formal_intake_confirmed" if started else "no_formal_intake_event",
            "statutory_clock": to_chart.get("clock", "omega_w"),
        }

        return InterfaceVerdict(
            interface_id=iface_id,
            evaluated_at=evaluated_at,
            verdict=verdict,
            locus=locus,
            tests=tests,
            anchor_event=anchor_data,
            response_event=resp_data,
            formal_intake=formal_intake,
            obs_missing=obs_missing,
            omega_star=omega_star,
        )


def main():
    parser = argparse.ArgumentParser(description="CT v1.0 Glue Check & Def. 4 Kernel Evaluator")
    parser.add_argument("target", nargs="?", default="IF-WONEN-WMO-001", help="Interface ID or path to JSON file")
    parser.add_argument("--json", action="store_true", help="Output raw JSON instead of human-readable trace")
    args = parser.parse_args()

    engine_dir = Path(__file__).resolve().parent.parent
    interfaces_path = engine_dir / "interfaces.json"

    if not interfaces_path.is_file():
        print(f"ERROR: interfaces.json not found at {interfaces_path}", file=sys.stderr)
        sys.exit(1)

    with open(interfaces_path, "r", encoding="utf-8") as f:
        interfaces_data = json.load(f)

    checker = GlueChecker(root_dir=engine_dir)

    target_interfaces = []
    if args.target.endswith(".json"):
        with open(args.target, "r", encoding="utf-8") as f:
            target_interfaces = json.load(f)
    else:
        # Search by ID or evaluate all if "ALL"
        if args.target.upper() == "ALL":
            target_interfaces = interfaces_data
        else:
            target_interfaces = [i for i in interfaces_data if i.get("id") == args.target]
            if not target_interfaces:
                print(f"ERROR: Interface ID '{args.target}' not found in interfaces.json", file=sys.stderr)
                sys.exit(1)

    for iface in target_interfaces:
        verdict = checker.evaluate_interface(iface)
        if args.json:
            out = {
                "interface": verdict.interface_id,
                "evaluated_at": verdict.evaluated_at,
                "verdict": verdict.verdict,
                "locus": verdict.locus,
                "anchor_event": verdict.anchor_event,
                "response_event": verdict.response_event,
                "formal_intake": verdict.formal_intake,
                "tests": {k: v.to_dict() for k, v in verdict.tests.items()},
                "obs_missing": verdict.obs_missing,
                "omega_star": verdict.omega_star,
            }
            print(json.dumps(out, indent=2, ensure_ascii=False))
        else:
            print(verdict.format_trace())


if __name__ == "__main__":
    main()
