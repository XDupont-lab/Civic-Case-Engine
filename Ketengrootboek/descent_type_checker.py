#!/usr/bin/env python3
"""
CIVIC HELPER — DESCENT TYPE-CHECKER v2.0 (Ketengrootboek & Stack-Runtime Engine)
Pure Python Standard Library (Zero External Dependencies).

Theoretisch Fundament (Constraint Topologie & Stack-Theorie):
  - Schaal is lokale sluiting (Hoekpunt V_sigma).
  - Een lokaal vinkje (1/1) zonder functoriële descent over de interface (D)
    naar het onderliggende burgersaldo is een schijnsluiting.
  - Monodromie: Wanneer een vordering een gesloten ketenlus doorloopt
    (bijv. Zorgverzekeraar -> CAK -> Gemeente -> Burger) en de som over de lus
    ongelijk is aan nul (oint Delta != 0), bewijst dit een fictieve schuldcreatie.

Toetsen (data-gedreven; geen zaakgegevens in de code):
  1. Invariant Preservation (Casimir)              - post.vaste_posten niet in credit geboekt
  2. Source Lineage & Contractual Grounding       - feit type 'bron_contract_beeindigd'
  3. Representation Typing (Art. 15 lid 3 AVG)    - feit type 'inzage_alleen_samenvatting'
  4. Service & Notification Integrity             - feit type 'retour_afzender'
  5. Execution Phase Alignment                    - feit type in EXECUTIE_TYPES terwijl doelpoort open is
  6. Monodromy / Ketenlus-deficit (in euro's)     - post.ketenlus {naam, pad, geclaimd, bron_geverifieerd, bewijs}
  Een feit hoort bij een post via het veld 'betreft_post'.

Bronnen: Boek 1 memoriaal.json en Boek 2 boek2_journaal.json (privé, buiten git). Een verse clone
zonder eigen data valt terug op de publieke Voorbeeldstad-sample (grootboek.json + fictieve feiten).

Aanroep:
  python descent_type_checker.py               -> Volledig terminal rapport
  python descent_type_checker.py --json        -> Gestructureerde JSON output
  python descent_type_checker.py --audit       -> Genereert DESCENT_TYPECHECK_AUDIT.md (buiten git)
  python descent_type_checker.py --post <id>   -> Toetst één specifieke post
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, asdict
from datetime import datetime
import json
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent
CIVIC_DIR = BASE_DIR.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

MEMORIAAL_PATH = BASE_DIR / "memoriaal.json"
JOURNAAL_PATH = BASE_DIR / "boek2_journaal.json"
SAMPLE_JOURNAAL_PATH = BASE_DIR / "grootboek.json"
AUDIT_OUT_PATH = CIVIC_DIR / "DESCENT_TYPECHECK_AUDIT.md"

EXECUTIE_TYPES = {"dwanginvordering", "beslag", "incasso_aanmaning", "bronheffing_wanbetalers"}

# Fictieve Voorbeeldstad-feiten (2031) die de sample-posten uit grootboek.json aanvullen.
_VOORBEELD_DESCENT_FEITEN: List[Dict[str, Any]] = [
    {
        "id": "EVT-VERZEKERAAR-Z-UITSCHRIJVING-20311103",
        "datum": "2031-11-03",
        "type": "bron_contract_beeindigd",
        "actor": "Zorgverzekeraar Z (Polisadministratie)",
        "omschrijving": "Polis met terugwerkende kracht beëindigd; premies verrekend",
        "bewijsstuk": "Dossier_Templates/03_Financien_en_Bestaanszekerheid.template.md",
        "betreft_post": "POST-CAK-BIJSTAND-002",
        "bedrag": 1234.56,
    },
    {
        "id": "EVT-CAK-INZAGE-20311110",
        "datum": "2031-11-10",
        "type": "inzage_alleen_samenvatting",
        "actor": "CAK (Functionaris Gegevensbescherming)",
        "omschrijving": "Inzageverzoek beantwoord met een datum-overzicht in plaats van afschriften",
        "bewijsstuk": "Dossier_Templates/03_Financien_en_Bestaanszekerheid.template.md",
        "betreft_post": "POST-CAK-BIJSTAND-002",
    },
    {
        "id": "EVT-CAK-RETOUR-20310330",
        "datum": "2031-03-30",
        "type": "retour_afzender",
        "actor": "CAK",
        "omschrijving": "Eigen correspondentielijst vermeldt dat de aanmelding retour afzender kwam",
        "bewijsstuk": "Dossier_Templates/03_Financien_en_Bestaanszekerheid.template.md",
        "betreft_post": "POST-CAK-BIJSTAND-002",
    },
]

# Fictieve ketenlus voor de sample-modus (Zorgverzekeraar Z -> CAK -> Sociale Dienst Voorbeeldstad -> Burger).
_VOORBEELD_KETENLUSSEN: Dict[str, Dict[str, Any]] = {
    "POST-CAK-BIJSTAND-002": {
        "naam": "Ketenlus Zvw-bronheffing (Zorgverzekeraar Z -> CAK -> Sociale Dienst Voorbeeldstad -> Burger)",
        "pad": ["Zorgverzekeraar Z (Polis)", "CAK", "Sociale Dienst Voorbeeldstad", "Burger"],
        "geclaimd": 1234.56,
        "bron_geverifieerd": 0.00,
        "bewijs": ["EVT-VERZEKERAAR-Z-UITSCHRIJVING-20311103", "EVT-CAK-INZAGE-20311110"],
    },
}


@dataclass
class DescentTypeError:
    post_id: str
    carrier: str
    rule_name: str
    error_type: str
    expected: str
    received: str
    witness: str
    diagnostic: str
    severity: str = "ERROR"
    financial_delta: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MonodromyDeficit:
    chain_name: str
    loop_path: List[str]
    claimed_top_debt: float
    verified_source_debt: float
    monodromy_delta: float
    witness_proof: str
    legal_ground_status: str


class DescentTypeChecker:
    def __init__(self, keten_dir: Optional[Path] = None):
        keten_dir = Path(keten_dir) if keten_dir else BASE_DIR
        mem_pad = keten_dir / MEMORIAAL_PATH.name
        jour_pad = keten_dir / JOURNAAL_PATH.name
        self.sample_modus = not (mem_pad.is_file() and jour_pad.is_file())
        if self.sample_modus:
            from sluiting import _VOORBEELDSTAD_MEMORIAAL
            self.memoriaal: List[Dict[str, Any]] = [dict(f) for f in _VOORBEELDSTAD_MEMORIAAL] + [dict(f) for f in _VOORBEELD_DESCENT_FEITEN]
            self.journaal: List[Dict[str, Any]] = self._load_json(keten_dir / SAMPLE_JOURNAAL_PATH.name, default=[])
            for post in self.journaal:
                if post.get("post_id") in _VOORBEELD_KETENLUSSEN and "ketenlus" not in post:
                    post["ketenlus"] = dict(_VOORBEELD_KETENLUSSEN[post["post_id"]])
        else:
            self.memoriaal = self._load_json(mem_pad, default=[])
            self.journaal = self._load_json(jour_pad, default=[])
        self.errors: List[DescentTypeError] = []
        self.monodromies: List[MonodromyDeficit] = []
        self.passed_checks: int = 0

    def _load_json(self, path: Path, default: Any) -> Any:
        if not path.exists():
            return default
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return default

    def _feiten_voor(self, post_id: str, feit_types: set) -> List[Dict[str, Any]]:
        return [
            f for f in self.memoriaal
            if f.get("betreft_post") == post_id and f.get("type") in feit_types
        ]

    def check_all(self, target_post: Optional[str] = None) -> List[DescentTypeError]:
        self.errors.clear()
        self.monodromies.clear()
        self.passed_checks = 0

        posts_to_check = self.journaal
        if target_post:
            posts_to_check = [p for p in self.journaal if p.get("post_id") == target_post]

        for post in posts_to_check:
            self._check_post_invariants(post)
            self._check_post_lineage_and_sources(post)
            self._check_post_representation(post)
            self._check_post_delivery_and_service(post)
            self._check_post_execution_phase(post)
            self._compute_monodromy(post)
        return self.errors

    def _check_post_invariants(self, post: Dict[str, Any]):
        post_id = post.get("post_id", "UNKNOWN")
        doelpoort_voldaan = post.get("poorten", {}).get("doelpoort", {}).get("voldaan", False)
        for vp in post.get("vaste_posten", []):
            if not vp.get("in_credit_geboekt", False) and not doelpoort_voldaan:
                self.errors.append(DescentTypeError(
                    post_id=post_id,
                    carrier=post.get("credit_rekening", "Ontvanger"),
                    rule_name="Rule-Invariant-Preservation",
                    error_type="CasimirDroppedObstruction",
                    expected=f"PreservedInvariant[{vp.get('id')}] (Geboekt in credit-administratie)",
                    received="Null / Dropped on interface",
                    witness=post.get("anker_feit", "N/A"),
                    diagnostic=f"De vaste invariant '{vp.get('omschrijving')}' is aan de bron vastgesteld maar door de ontvanger niet in de credit-administratie erkend.",
                ))
            else:
                self.passed_checks += 1

    def _check_post_lineage_and_sources(self, post: Dict[str, Any]):
        post_id = post.get("post_id", "UNKNOWN")
        for feit in self._feiten_voor(post_id, {"bron_contract_beeindigd"}):
            self.errors.append(DescentTypeError(
                post_id=post_id,
                carrier=post.get("debet_rekening", "Zender"),
                rule_name="Rule-Source-Lineage-Validity",
                error_type="LineageRuptureObstruction",
                expected="ActivePolicyContract (Rechtsgeldige grondslag bij de bron)",
                received="RetroactiveTermination (Broncontract met terugwerkende kracht beëindigd)",
                witness=feit.get("bewijsstuk") or feit.get("id", "N/A"),
                diagnostic=f"{feit.get('actor', 'De bron')} ({feit.get('datum', '?')}): {feit.get('omschrijving', '')}. De grondslag voor de vordering ontbreekt bij de bron.",
                financial_delta=float(feit.get("bedrag", 0.0) or 0.0),
            ))

    def _check_post_representation(self, post: Dict[str, Any]):
        post_id = post.get("post_id", "UNKNOWN")
        for feit in self._feiten_voor(post_id, {"inzage_alleen_samenvatting"}):
            self.errors.append(DescentTypeError(
                post_id=post_id,
                carrier=feit.get("actor", post.get("debet_rekening", "Verwerker")),
                rule_name="Rule-Art15-3-Representation",
                error_type="LossyRepresentationObstruction",
                expected="DocumentCopy[PDF] (Getrouwe elektronische afschriften conform art. 15 lid 3 AVG / HvJ EU C-487/21)",
                received="MetadataSummaryTable (Overzicht in plaats van afschriften van de brondocumenten)",
                witness=feit.get("bewijsstuk") or feit.get("id", "N/A"),
                diagnostic="De verwerker levert een samenvatting in plaats van integrale kopieën. Schending van het recht op een elektronisch afschrift.",
            ))

    def _check_post_delivery_and_service(self, post: Dict[str, Any]):
        post_id = post.get("post_id", "UNKNOWN")
        for feit in self._feiten_voor(post_id, {"retour_afzender"}):
            self.errors.append(DescentTypeError(
                post_id=post_id,
                carrier=feit.get("actor", post.get("debet_rekening", "Zender")),
                rule_name="Rule-Service-Integrity",
                error_type="DocumentedReturnToSenderObstruction",
                expected="LegallyNotifiedService (Rechtsgeldig bekendgemaakt op geverifieerd adres)",
                received=f"ReturnedToSender[{feit.get('datum', '?')}]",
                witness=feit.get("bewijsstuk") or feit.get("id", "N/A"),
                diagnostic="De zender registreert zelf dat het stuk retour afzender kwam. Er is geen rechtsgeldige kennisgeving voltooid (art. 3:41 Awb).",
            ))

    def _check_post_execution_phase(self, post: Dict[str, Any]):
        post_id = post.get("post_id", "UNKNOWN")
        doel_voldaan = post.get("poorten", {}).get("doelpoort", {}).get("voldaan", False)
        executie = self._feiten_voor(post_id, EXECUTIE_TYPES)
        anker = next((f for f in self.memoriaal if f.get("id") == post.get("anker_feit")), None)
        if anker and anker.get("type") in EXECUTIE_TYPES:
            executie.append(anker)
        if executie and not doel_voldaan:
            self.errors.append(DescentTypeError(
                post_id=post_id,
                carrier=post.get("debet_rekening", "Zender"),
                rule_name="Rule-Execution-Without-Closure",
                error_type="IllegalPhaseMutation",
                expected="Phase3Closure (Post gesloten alvorens invordering wordt uitgevoerd)",
                received="Phase1Failure[POST_SLUIT_NIET] (Doelpoort staat open)",
                witness=executie[0].get("id", "N/A"),
                diagnostic="Er wordt administratieve of financiële druk uitgeoefend op een ketenoverdracht waarvan de doelpoort formeel niet is gesloten.",
            ))
        else:
            self.passed_checks += 1

    def _compute_monodromy(self, post: Dict[str, Any]):
        lus = post.get("ketenlus")
        if not lus:
            return
        geclaimd = float(lus.get("geclaimd", 0.0) or 0.0)
        bron = float(lus.get("bron_geverifieerd", 0.0) or 0.0)
        delta = round(geclaimd - bron, 2)
        if delta == 0:
            self.passed_checks += 1
            return
        self.monodromies.append(MonodromyDeficit(
            chain_name=lus.get("naam", post.get("post_id", "Ketenlus")),
            loop_path=list(lus.get("pad", [])),
            claimed_top_debt=geclaimd,
            verified_source_debt=bron,
            monodromy_delta=delta,
            witness_proof=" & ".join(lus.get("bewijs", [])) or "N/A",
            legal_ground_status="GRONDSLAG BETWIST — ketenlus sluit niet op de bron",
        ))

    def generate_audit_markdown(self) -> str:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        lines = [
            "# Formeel Ketenintegriteits- & Descent-Auditrapport",
            "",
            f"- **Datum van toetsing:** {now_str}",
            "- **Toetsingskader:** Constraint Topologie v2.0 (§3.3) / Stack-Runtime v1.0",
            f"- **Bron:** {'publieke Voorbeeldstad-sample (fictief)' if self.sample_modus else 'eigen boeken (memoriaal.json + boek2_journaal.json)'}",
            f"- **Aantal geëvalueerde journaalposten:** {len(self.journaal)}",
            f"- **Totaal aantal gedetecteerde Descent TypeErrors:** {len(self.errors)}",
            f"- **Gevalideerde keteninvarianten:** {self.passed_checks}",
            "",
            "---",
            "",
            "## 1. Samenvatting Monodromie & Ketenlus-Deficit (Fictieve Schulden)",
            "",
            "In de Constraint Topologie is de ketenlus-integraal $\\oint_{\\text{Keten}} \\Delta \\text{Saldo}$ de formele toets voor schijnsluiting. "
            "Wanneer een keten claimt dat een schuld 'gesloten' is, maar de integraal over de lus niet nul is, is er sprake van een administratieve hallucinatie.",
            "",
            "| Ketenlus | Geclaimde Schuld aan Top | Feitelijke Schuld aan Bron | Monodromie Deficit (Fictief) | Juridische Status |",
            "| :--- | :--- | :--- | :--- | :--- |",
        ]
        for m in self.monodromies:
            lines.append(
                f"| **{m.chain_name}** | € {m.claimed_top_debt:,.2f} | € {m.verified_source_debt:,.2f} | **+€ {m.monodromy_delta:,.2f}** | `{m.legal_ground_status}` |"
            )
        lines.extend(["", "---", "", "## 2. Gedetailleerd Register van Descent TypeErrors", ""])
        for idx, err in enumerate(self.errors, 1):
            lines.extend([
                f"### [{idx}] `{err.post_id}` — {err.rule_name}",
                f"- **Verantwoordelijke Carrier:** {err.carrier}",
                f"- **Foutclassificatie:** `{err.error_type}`",
                f"- **Geëist Wetstype (Expected):** `{err.expected}`",
                f"- **Aangetroffen Type (Received):** `{err.received}`",
                f"- **Financiële Impact / Delta:** € {err.financial_delta:,.2f}",
                f"- **Bewijsstuk in Dossier:** `{err.witness}`",
                f"- **Forensische Diagnose:** {err.diagnostic}",
                "",
            ])
        lines.extend([
            "---",
            "",
            "## 3. Conclusie en Rechtsgevolg",
            "",
            "1. **Geen materiële executietitel:** Zolang een post lijdt aan `CasimirDroppedObstruction`, `LineageRuptureObstruction` of `LossyRepresentationObstruction`, kan de administratieve claim niet rechtmatig afdalen (*descend*) naar het vermogen van de burger.",
            "2. **Schending van de Niet-Overschrijvingsregel:** Loketten die een lokaal procedureel vinkje hanteren terwijl de onderliggende gegevensdragers retour afzender zijn gekomen of door de bronhouder zijn geannuleerd, handelen in strijd met het evenredigheidsbeginsel (art. 3:4 lid 2 Awb) en art. 15 lid 3 AVG.",
            "",
        ])
        return "\n".join(lines)

    def print_report(self):
        print("=" * 100)
        print(" CIVIC HELPER — DESCENT TYPE-CHECKER v2.0 (STACK-RUNTIME ENGINE)")
        print(" Axiom: Schaal is lokale sluiting. Lokale geldigheid zonder functoriële descent is ongeldig.")
        print("=" * 100)
        print(f" Tijdstip toetsing : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f" Bron              : {'Voorbeeldstad-sample (fictief)' if self.sample_modus else 'eigen boeken'}")
        print(f" Totaal posten     : {len(self.journaal)}")
        print(f" Invarianten OK    : {self.passed_checks}")
        print(f" Gevonden TypeErrors: {len(self.errors)}")
        print("-" * 100)

        if self.monodromies:
            print("\n[!] GEDETECTEERDE KETENLUS-MONODROMIE (FICTIEF SALDO):")
            for m in self.monodromies:
                print(f"    * {m.chain_name}")
                print(f"      Top-claim : € {m.claimed_top_debt:,.2f}")
                print(f"      Bron-echt : € {m.verified_source_debt:,.2f}")
                print(f"      MONODROMIE: +€ {m.monodromy_delta:,.2f} ({m.legal_ground_status})")
            print("-" * 100)

        for idx, err in enumerate(self.errors, 1):
            lines = [
                f"\n[{err.severity} #{idx}] {err.post_id} — {err.rule_name}",
                f"  Carrier      : {err.carrier}",
                f"  Fouttype     : {err.error_type}",
                f"  Expected     : {err.expected}",
                f"  Received     : {err.received}",
                f"  Witness      : {err.witness}",
                f"  Diagnose     : {err.diagnostic}",
            ]
            if err.financial_delta > 0:
                lines.append(f"  Financieel   : +€ {err.financial_delta:,.2f}")
            print("\n".join(lines))

        print("\n" + "=" * 100)
        print(f" RESULTAAT: {len(self.errors)} DESCENT TYPE-ERROR(S) GECORRELEERD.")
        print(" Geen van de gemarkeerde posten kan rechtmatig afdalen naar het burgersaldo.")
        print("=" * 100)


def main():
    parser = argparse.ArgumentParser(description="Descent Type-Checker voor Ketengrootboek & Stack-Runtime")
    parser.add_argument("--post", help="Toets een specifieke post_id")
    parser.add_argument("--json", action="store_true", help="Print output als JSON")
    parser.add_argument("--audit", action="store_true", help="Genereer DESCENT_TYPECHECK_AUDIT.md (buiten git)")
    args = parser.parse_args()

    checker = DescentTypeChecker()
    errors = checker.check_all(target_post=args.post)

    if args.json:
        out = {
            "timestamp": datetime.now().isoformat(),
            "sample_modus": checker.sample_modus,
            "total_posts": len(checker.journaal),
            "passed_checks": checker.passed_checks,
            "error_count": len(errors),
            "monodromies": [asdict(m) for m in checker.monodromies],
            "errors": [e.to_dict() for e in errors],
        }
        print(json.dumps(out, indent=2, ensure_ascii=False))
    elif args.audit:
        AUDIT_OUT_PATH.write_text(checker.generate_audit_markdown(), encoding="utf-8")
        print(f"[✓] Formeel auditrapport opgeslagen in: {AUDIT_OUT_PATH}")
    else:
        checker.print_report()


if __name__ == "__main__":
    main()
