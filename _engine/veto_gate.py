#!/usr/bin/env python3
"""
CIVIC HELPER — VETO GATE (CYBERNETIC HARNESS v1.1 + PROTOCOL FH-01)
Pure Python Standard Library (Zero External Dependencies).

Implementeert de deterministische Veto-Keten (Stappen B, C, D) van de Cybernetische Architectuur
én Protocol FH-01 (Epistemische Laagscheiding & Fluwelen Handschoen):
1. Veto 1 (Payload/Slot Ingest): klinisch in payload maar niet in slot.ingest -> REJECT
2. Veto 2 (Politiek Discours): politiek_cc == true maar geen lokaal discours -> REJECT
3. Veto 3 (Driftbewaking): telefonische afhandeling openlaten -> REJECT / WARN
4. Veto 4 (Oordeel & Loopbaan): loopbaan, CV of bureau in uitgaande brieftekst -> REJECT
5. Veto 5 (Dubbele Klok): tweede t=0 of nieuw narratief terwijl klok loopt (termijnen.json of Ketengrootboek) -> REJECT
6. Veto 6 (Protocol FH-01): demoniseren/sussen, professioneel dictaat of manipulatieve agency inversion -> REJECT
"""

import os
import sys
import re
import json
from pathlib import Path

_ENGINE_DIR = Path(__file__).resolve().parent
if str(_ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(_ENGINE_DIR))

from sbar_protocol import SBARProtocol

# Lijst van bekende klinische termen die NIET in een administratieve/productcode-sonde horen
CLINICAL_KEYWORDS = [
    r"\bstoma\b", r"\bdarmproblematiek\b", r"\bziekenhuisopname\b",
    r"\bneuroloog\b", r"\bpsychiatrisch\b", r"\bmedicatieoverzicht\b",
    r"\bpijnklachten\b", r"\bincontinentie\b", r"\bdiagnose\b"
]

# Signalen die wijzen op ambtelijke drift (toestaan van telefonische afhandeling)
DRIFT_KEYWORDS = [
    r"u kunt mij (?:hierover )?bellen",
    r"telefonisch (?:toelichten|bespreken|overleg)",
    r"neem gerust telefonisch contact op",
    r"graag even bellen"
]

# Vereiste Velvet Glove schriftelijkheidsclausule
VELVET_GLOVE_WRITTEN_CLAUSE = [
    "uitsluitend schriftelijk",
    "uitsluitend digitaal",
    "per e-mail"
]

# Verboden loopbaan / bureau verwijzingen (ad hominem in uitgaande stukken)
CAREER_AD_HOMINEM_KEYWORDS = [
    r"\bmaandag\b(?!\s+(?:1[0-9]|2[0-9]|3[01]|[0-9]))",  # 'maandag' als uitzendbureau, niet als datum
    r"\bedah\b", r"\bdetacheerder\b", r"\bcv van\b",
    r"\bonbekwaam\b", r"\bkan haar werk niet\b", r"\bopleidingsniveau\b"
]

# Politieke CC ontvangers
POLITICAL_CC_KEYWORDS = [
    r"\bgriffie\b", r"\braadsleden\b", r"\bfractie\b",
    r"\bwethouder\b", r"\bgemeenteraad\b"
]


class VetoResult:
    def __init__(self, passed=True, rule="", message="", severity="REJECT", suggestion=""):
        self.passed = passed
        self.rule = rule
        self.message = message
        self.severity = severity  # REJECT of WARN
        self.suggestion = suggestion

    def to_dict(self):
        return {
            "passed": self.passed,
            "rule": self.rule,
            "message": self.message,
            "severity": self.severity,
            "suggestion": self.suggestion
        }


class VetoGate:
    def __init__(self, root_dir=None):
        self.root_dir = Path(root_dir) if root_dir else Path(__file__).resolve().parent.parent

    def _find_active_clocks(self, target_authority: str) -> list[str]:
        """Zoekt lopende termijnen voor target_authority in zowel Dossier/termijnen.json als het Ketengrootboek."""
        if not target_authority:
            return []
        auth_low = target_authority.lower()
        auth_tokens = [t for t in re.split(r"[\s(),/&_-]+", auth_low) if len(t) >= 3]
        active_ids: list[str] = []

        # Bron 1: Dossier/termijnen.json
        termijnen_file = self.root_dir / "Dossier" / "termijnen.json"
        if termijnen_file.exists():
            try:
                clocks = json.loads(termijnen_file.read_text(encoding="utf-8"))
                for c in clocks:
                    c_auth = str(c.get("authority", "")).lower()
                    if c.get("status") == "LOPEND" and (auth_low in c_auth or c_auth in auth_low):
                        active_ids.append(str(c.get("id", "termijnen.json")))
            except Exception:
                pass

        # Bron 2: Ketengrootboek (Boek 3 ketengrootboek.json / Boek 2 grootboek.json)
        keten_dir = self.root_dir / "Ketengrootboek"
        keten_boek3 = keten_dir / "ketengrootboek.json"
        if keten_boek3.exists():
            try:
                kdata = json.loads(keten_boek3.read_text(encoding="utf-8"))
                for t in kdata.get("openstaande_termijnen", []):
                    loket_str = f"{t.get('loket_id', '')} {t.get('loket_naam', '')}".lower()
                    if auth_low in loket_str or any(tok in loket_str for tok in auth_tokens):
                        pid = str(t.get("post_id", "KETEN_KLOK"))
                        if pid not in active_ids:
                            active_ids.append(pid)
            except Exception:
                pass

        keten_boek2 = keten_dir / "grootboek.json"
        if keten_boek2.exists():
            try:
                posten = json.loads(keten_boek2.read_text(encoding="utf-8"))
                for p in posten:
                    if not p.get("termijn"):
                        continue
                    rec_str = f"{p.get('debet_rekening', '')} {p.get('credit_rekening', '')} {p.get('naam', '')}".lower()
                    if auth_low in rec_str or any(tok in rec_str for tok in auth_tokens):
                        pid = str(p.get("post_id", "GROOTBOEK_KLOK"))
                        if pid not in active_ids:
                            active_ids.append(pid)
            except Exception:
                pass

        return active_ids

    def check_draft(self, text, slot_metadata=None, has_local_discours=False):
        """
        Toetst een concepttekst aan alle 6 cybernetische en FH-01 veto-regels.
        slot_metadata: dict met o.a. 'name', 'type', 'ingest_capacity' (list van strings), 'required_goals'
        has_local_discours: bool, of er een actief L2-discours document aanwezig is
        """
        results = []
        slot_metadata = slot_metadata or {}
        ingest = slot_metadata.get("ingest_capacity", ["productcodes", "termijnen", "privacy"])

        # VETO 1: Payload / Slot Ingest
        if "klinisch" not in ingest:
            found_clinical = []
            for pat in CLINICAL_KEYWORDS:
                if re.search(pat, text, re.IGNORECASE):
                    found_clinical.append(pat.replace(r"\b", ""))
            if found_clinical:
                results.append(VetoResult(
                    passed=False,
                    rule="VETO_1_PAYLOAD_SLOT_INGEST",
                    message=f"Klinische details aangetroffen ({', '.join(found_clinical)}) terwijl slot '{slot_metadata.get('name', 'onbekend')}' geen klinische ingest bezit.",
                    severity="REJECT",
                    suggestion="Strip klinische details en vervang door de neutrale Velvet Glove formule: 'Gelet op mijn medische belastbaarheid verzoek ik alle stukken uitsluitend digitaal aan te leveren.'"
                ))

        # VETO 2: Kanaalbesmetting (Politieke of Media CC op administratieve/uitvoerende sonde)
        is_cross_contaminated_cc = False
        is_executive_sonde = not slot_metadata.get("is_political_brief", False) and not slot_metadata.get("is_media_brief", False)

        if is_executive_sonde:
            for pat in POLITICAL_CC_KEYWORDS:
                if re.search(r"(?:cc|kopie aan):.*?" + pat, text, re.IGNORECASE):
                    is_cross_contaminated_cc = True
                    break

        if is_cross_contaminated_cc:
            results.append(VetoResult(
                passed=False,
                rule="VETO_2_KANAALBESMETTING_CC",
                message="Politieke functionarissen (griffie/raad/wethouder) in CC aangetroffen bij een administratieve sonde naar een uitvoeringsorgaan.",
                severity="REJECT",
                suggestion="Houd de administratieve sonde zuiver ambtelijk. Open de politieke flank (Macht 2) altijd via een zelfstandige Signaalbrief via de Raadsgriffie."
            ))

        # VETO 3: Driftbewaking (Telefoon)
        found_drift = []
        for pat in DRIFT_KEYWORDS:
            if re.search(pat, text, re.IGNORECASE):
                found_drift.append(pat)

        has_written_clause = any(clause in text.lower() for clause in VELVET_GLOVE_WRITTEN_CLAUSE)

        if found_drift:
            results.append(VetoResult(
                passed=False,
                rule="VETO_3_DRIFT_TELEFOON",
                message="Brief laat ruimte voor telefonisch contact (ambtelijke drift).",
                severity="REJECT",
                suggestion="Schrap telefonische uitnodiging en dwing strikte schriftelijkheid af."
            ))
        elif not has_written_clause:
            results.append(VetoResult(
                passed=False,
                rule="VETO_3_DRIFT_SCHRIFTELIJKHEID_ONTBREEKT",
                message="Strikte schriftelijkheidsclausule ontbreekt in het stuk.",
                severity="WARN",
                suggestion="Voeg de Velvet Glove schriftelijkheidsclausule toe ('uitsluitend schriftelijk en digitaal per e-mail')."
            ))

        # VETO 4: Oordeel & Loopbaan (Ad Hominem)
        found_career = []
        for pat in CAREER_AD_HOMINEM_KEYWORDS:
            if re.search(pat, text, re.IGNORECASE):
                found_career.append(pat.replace(r"\b", ""))
        if found_career:
            results.append(VetoResult(
                passed=False,
                rule="VETO_4_LOOPBAAN_OF_OORDEEL",
                message=f"Loopbaangegevens, detacheringsbureau of subjectief oordeel in uitgaande tekst ({', '.join(found_career)}).",
                severity="REJECT",
                suggestion="Verwijder alle verwijzingen naar CV, bureau of bekwaamheid van de functionaris. Dit hoort strikt in het interne landschap (L1)."
            ))

        # VETO 5: Dubbele Klok / Tweede 'Nu' (termijnen.json én Ketengrootboek)
        target_authority = slot_metadata.get("authority", "")
        if target_authority and slot_metadata.get("is_crisis_commit", False):
            active_for_auth = self._find_active_clocks(target_authority)
            if active_for_auth:
                results.append(VetoResult(
                    passed=False,
                    rule="VETO_5_TWEEDE_NU_DUBBELE_KLOK",
                    message=f"Er loopt reeds een actieve wettelijke klok voor '{target_authority}' ({active_for_auth[0]}). Een nieuw narratief verstoort de lopende termijn.",
                    severity="REJECT",
                    suggestion="Respecteer de lopende klok (ω*). Verstuur geen nieuw crisisnarratief naar hetzelfde slot zolang de termijn tikt."
                ))

        # VETO 6: Protocol FH-01 (3 IJkcontroles + 2 Negatieve Invarianten)
        fh01 = SBARProtocol.validate_fh01_transform(
            text,
            required_goals=slot_metadata.get("required_goals"),
        )
        if not fh01.passed:
            results.append(VetoResult(
                passed=False,
                rule="VETO_6_FH01_TRANSFORMATIE_EN_TOON",
                message=" | ".join(fh01.warnings),
                severity="REJECT",
                suggestion="Pas Protocol FH-01 toe: behoud alle ketendoelen (geen sussen), vermijd vijandtaal (geen demoniseren), en laat de professionele beoordelingsruimte van de ontvanger intact."
            ))

        all_passed = all(r.passed or r.severity == "WARN" for r in results)
        return {
            "all_passed": all_passed,
            "has_rejections": any(r.severity == "REJECT" for r in results),
            "results": [r.to_dict() for r in results],
            "fh01": fh01.to_dict(),
        }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Gebruik: python veto_gate.py <concept_bestand.md>")
        sys.exit(1)

    p = Path(sys.argv[1])
    if not p.exists():
        print(f"Fout: Bestand niet gevonden: {p}")
        sys.exit(1)

    with open(p, "r", encoding="utf-8") as f:
        content = f.read()

    gate = VetoGate()
    report = gate.check_draft(content)
    print(f"\n=== VETO GATE AUDIT RESULTAAT VOOR: {p.name} ===")
    print(f"Status: {'[VRIJGEGEVEN]' if report['all_passed'] else '[GEBLOKKEERD DOOR VETO]'}")
    for r in report["results"]:
        status_icon = "[WARN]" if r["severity"] == "WARN" else "[REJECT]"
        print(f"\n{status_icon} Regel: {r['rule']}")
        print(f"  Melding: {r['message']}")
        print(f"  Suggestie: {r['suggestion']}")
    if not report["results"]:
        print("\nGeen veto-inbreuken geconstateerd. Stuk voldoet aan de cybernetische en FH-01 standaarden.")
