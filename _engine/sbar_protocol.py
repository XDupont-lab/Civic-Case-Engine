#!/usr/bin/env python3
"""
CIVIC HELPER — SBARIII COMMUNICATION PROTOCOL & PROTOCOL FH-01 VALIDATOR
Pure Python Standard Library (Zero External Dependencies).

Onderbouwd door:
- AHRQ TeamSTEPPS 3.0 Curriculum (Repeat-Back Recommendations and Requests)
- Martínez-Fernández et al. (2022), PMC9778833 (Veerkracht + 97% failure ongestructureerde handoffs)
- Civic Helper: NOTITIE_COMMUNICATIEPROTOCOL_SBARIII.md (§1-6 SBARIII, §7 Protocol FH-01)

Componenten van SBARIII:
1. I — Identification (Identificatie van afzender, ontvanger en dossier)
2. S — Situation (De acute focus/vraag van vandaag)
3. B — Background (Geobjectiveerde context uit de tijdlijn)
4. A — Assessment (Sense-making, werkhypothese, hiaten, risico bij inactiviteit)
5. R — Recommendation & Request (Concreet handelingsvoorstel)
6. I — Intervention (Reeds ondernomen stappen door de betrokkene)
7. I — Information / Read-Back (Verplichte gesloten lus / Tegenboekingstermijn)

Componenten van Protocol FH-01 (§7):
- Vier Epistemische Lagen: A. Bewijs (Memoriaal), B. Interpretatie (Journaal),
  C. Doel & Constraint (Ketengrootboek & Klok), D. Transformatie (Fluwelen Handschoen).
- 2-Staps Invoer-Filter: Stap 1 uitsluitend letterlijke tekst (zuiver Memoriaal + taalkundige
  lezingen); Stap 2 koppeling met Ketengrootboek-doelen en Tafel-weging.
- Drie IJkcontroles: 1. Inhoudscontrole, 2. Taalhandelingcontrole, 3. Ruimtecontrole.
- Twee Negatieve Invarianten: 1. Geen manipulatieve Agency Inversion,
  2. Sussen noch Demoniseren (verbod op adaptief overdrijven).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class SBARMessage:
    identification: str = ""
    situation: str = ""
    background: str = ""
    assessment: str = ""
    recommendation: str = ""
    intervention: str = ""
    read_back: str = ""
    metadata: Dict[str, str] = field(default_factory=dict)

    def to_text(self) -> str:
        """Genereert een gestructureerde uitgaande brieftekst volgens SBARIII."""
        lines = []
        if self.identification:
            lines.append(f"1. IDENTIFICATIE & DOSSIER:\n{self.identification.strip()}\n")
        if self.situation:
            lines.append(f"2. SITUATIE (ACUTE AANLEIDING):\n{self.situation.strip()}\n")
        if self.background:
            lines.append(f"3. ACHTERGROND (CONTEXT TIJDLIJN):\n{self.background.strip()}\n")
        if self.assessment:
            lines.append(f"4. BEOORDELING & RISICOANALYSE (ASSESSMENT):\n{self.assessment.strip()}\n")
        if self.recommendation:
            lines.append(f"5. CONCREET VERZOEK / AANBEVELING (REQUEST):\n{self.recommendation.strip()}\n")
        if self.intervention:
            lines.append(f"6. REEDS ONDERNOMEN ACTIES (INTERVENTIE):\n{self.intervention.strip()}\n")
        if self.read_back:
            lines.append(f"7. GESLOTEN LUS & ONTVANGSTBEVESTIGING (REPEAT-BACK):\n{self.read_back.strip()}\n")
        return "\n".join(lines).strip()


@dataclass
class ValidationReport:
    is_valid: bool
    missing_components: List[str]
    warnings: List[str]
    score: float  # Percentage compleetheid (0.0 - 1.0)
    details: Dict[str, bool]


@dataclass
class FH01Report:
    """Resultaat van de Protocol FH-01 toets (3 IJkcontroles + 2 Negatieve Invarianten)."""
    passed: bool
    inhoud_behouden: bool
    taalhandeling_zuiver: bool
    ruimte_intact: bool
    geen_agency_inversion: bool
    geen_sussen_of_demoniseren: bool
    ontbrekende_doelen: List[str]
    dictaat_zinnen: List[str]
    demonisering_termen: List[str]
    agency_inversion_treffers: List[str]
    speech_act_breakdown: Dict[str, int]
    warnings: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "ijkcontroles": {
                "1_inhoudscontrole": self.inhoud_behouden,
                "2_taalhandelingcontrole": self.taalhandeling_zuiver,
                "3_ruimtecontrole": self.ruimte_intact,
            },
            "negatieve_invarianten": {
                "1_geen_agency_inversion": self.geen_agency_inversion,
                "2_sussen_noch_demoniseren": self.geen_sussen_of_demoniseren,
            },
            "ontbrekende_doelen": self.ontbrekende_doelen,
            "dictaat_zinnen": self.dictaat_zinnen,
            "demonisering_termen": self.demonisering_termen,
            "agency_inversion_treffers": self.agency_inversion_treffers,
            "speech_act_breakdown": self.speech_act_breakdown,
            "warnings": self.warnings,
        }


class SBARProtocol:
    """Validator en generator voor het SBARIII overdrachtsprotocol en Protocol FH-01."""

    # Herkenningspatronen voor tekstuele concepten
    PATTERNS = {
        "identification": [
            r"1\.\s*identificatie", r"\bbetreft\b", r"\bdossier(?:nummer)?\b",
            r"\bkenmerk\b", r"\bgeachte\b"
        ],
        "situation": [
            r"2\.\s*situatie", r"\bsituatie\b", r"\bde aanleiding\b",
            r"\bhet acute probleem\b", r"\bhuidige situatie\b"
        ],
        "background": [
            r"3\.\s*achtergrond", r"\bachtergrond\b", r"\bvoorgeschiedenis\b",
            r"\bbestuurlijke context\b", r"\bmedische context\b"
        ],
        "assessment": [
            r"4\.\s*beoordeling", r"\bassessment\b", r"\bbeoordeling\b",
            r"\banalyse\b", r"\bconstatering\b", r"\brisico\b"
        ],
        "recommendation": [
            r"5\.\s*concreet verzoek", r"\baanbeveling\b", r"\bverzoek\b",
            r"\brecommendation\b", r"\bik verzoek u\b"
        ],
        "intervention": [
            r"6\.\s*reeds ondernomen", r"\binterventie\b", r"\bacties\b",
            r"\bmiddelen\b", r"\bvoorzorgsmaatregelen\b"
        ],
        "read_back": [
            r"7\.\s*gesloten lus", r"\bread-?back\b", r"\brepeat-?back\b",
            r"\bontvangstbevestiging\b", r"\bgesloten lus\b", r"\bbevestiging\b",
            r"\bbinnen\s+\d+\s+(?:dagen|weken)\b"
        ]
    }

    # Protocol FH-01 (§7.3 & §7.4) patronen:
    # Zinnen die de professionele bevoegdheid/beslissingsruimte van de ontvanger dicteren als voldongen feit
    DICTAAT_RUIMTE_PATTERNS = [
        r"\bu\s+moet\s+(?:als\s+arts|als\s+behandelaar|medisch)\s+vaststellen\b",
        r"\bik\s+draag\s+u\s+op\s+om\s+(?:de\s+diagnose|het\s+medisch\s+oordeel)\b",
        r"\bu\s+dient\s+(?:zonder\s+meer\s+)?de\s+diagnose\s+.*?\s+te\s+stellen\b",
        r"\bhet\s+staat\s+niet\s+ter\s+beoordeling\s+van\s+u\s+als\s+(?:arts|behandelaar)\b",
        r"\bu\s+bent\s+verplicht\s+mijn\s+medische\s+conclusie\s+over\s+te\s+nemen\b",
    ]

    # Negatieve Invariant 1: Manipulatieve Agency Inversion (verborgen fuik onder schijn van eigen idee)
    AGENCY_INVERSION_PATTERNS = [
        r"\bzoals\s+u\s+zelf\s+ongetwijfeld\s+al\s+had\s+besloten\b",
        r"\bu\s+zult\s+het\s+er\s+volledig\s+mee\s+eens\s+zijn\s+dat\s+u\s+fout\s+zat\b",
        r"\buiteraard\s+was\s+het\s+uw\s+eigen\s+voorstel\s+om\b",
    ]

    # Negatieve Invariant 2: Demoniseren / adaptief overdrijven (klerkenreflex, gildebaas, vijandtaal)
    DEMONISERING_PATTERNS = [
        r"\bklerkenreflex\b",
        r"\bgildebaas\b",
        r"\bepd-ramp(?:en)?\b",
        r"\bkwaadaardig(?:e)?\b",
        r"\bsabotage\b",
        r"\bcorrupt(?:e)?\b",
        r"\bonmenselijk\s+systeem\b",
        r"\bverschrikkelijke\s+bureaucraat\b",
    ]

    # Standaard replieken bij professionele kritiek
    DEFENSE_REFERENCE = "Civic_Helper/NOTITIE_COMMUNICATIEPROTOCOL_SBARIII.md"

    @classmethod
    def validate_text(cls, text: str) -> ValidationReport:
        """
        Toetst een vrije concepttekst op de aanwezigheid van SBARIII-elementen.
        Borgt dat uitgaande stukken niet vervallen in de 97% unstructured handoff failure rate.
        """
        details = {}
        missing = []
        warnings = []

        lower_text = text.lower()

        for comp, patterns in cls.PATTERNS.items():
            matched = any(re.search(pat, lower_text) for pat in patterns)
            details[comp] = matched
            if not matched:
                missing.append(comp)

        # Gesloten lus / Repeat-back is cruciaal voor de tegenboeking
        if not details.get("read_back", False):
            warnings.append(
                "Geen expliciete Read-Back / ontvangsttermijn aangetroffen. "
                "De tegenboeking kan niet sluiten zonder bevestigingstermijn."
            )

        # Assessment check
        if not details.get("assessment", False):
            warnings.append(
                "Assessment / Risicoanalyse ontbreekt. Volgens AHRQ is sense-making "
                "essentieel om de consequentie van inactiviteit te duiden."
            )

        score = (len(cls.PATTERNS) - len(missing)) / len(cls.PATTERNS)
        # We beschouwen een brief geldig als ten minste Situation, Background, Assessment en Recommendation aanwezig zijn
        core_valid = (
            details.get("situation", False) and
            details.get("background", False) and
            details.get("assessment", False) and
            details.get("recommendation", False)
        )

        return ValidationReport(
            is_valid=core_valid and len(missing) <= 2,
            missing_components=missing,
            warnings=warnings,
            score=score,
            details=details
        )

    @classmethod
    def validate_fh01_transform(
        cls,
        text: str,
        required_goals: Optional[List[str]] = None,
    ) -> FH01Report:
        """
        Toetst een uitgaand concept of een model-transformatie aan Protocol FH-01 (§7.3 en §7.4):
        - IJkcontrole 1 (Inhoudscontrole): Zijn alle opgegeven doelen/kernfeiten behouden?
        - IJkcontrole 2 (Taalhandelingcontrole): Classificeert zinnen en weert dictaten.
        - IJkcontrole 3 (Ruimtecontrole): Laat professionele beoordelingsruimte van de ontvanger intact.
        - Negatieve Invariant 1: Geen manipulatieve Agency Inversion.
        - Negatieve Invariant 2: Sussen noch Demoniseren.
        """
        lower_text = (text or "").lower()
        required_goals = [g.strip() for g in (required_goals or []) if g and g.strip()]

        # 1. Inhoudscontrole (en controle tegen sussen / stilzwijgend verlagen van doelen)
        ontbrekende_doelen = [
            goal for goal in required_goals
            if goal.lower() not in lower_text
        ]
        inhoud_behouden = len(ontbrekende_doelen) == 0

        # 2 & 3. Taalhandeling- en Ruimtecontrole
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", text or "") if s.strip()]
        speech_acts = {
            "informeren": 0,
            "verzoeken": 0,
            "begrenzen": 0,
            "dicteren_voldongen_feit": 0,
        }
        dictaat_zinnen: List[str] = []

        for sent in sentences:
            s_low = sent.lower()
            if any(re.search(pat, s_low) for pat in cls.DICTAAT_RUIMTE_PATTERNS):
                speech_acts["dicteren_voldongen_feit"] += 1
                dictaat_zinnen.append(sent)
            elif any(w in s_low for w in ("ik verzoek", "graag ontvang", "verzoek ik u", "kunt u", "wilt u")):
                speech_acts["verzoeken"] += 1
            elif any(w in s_low for w in ("uitsluitend schriftelijk", "wijs ik af", "termijn", "wettelijk", "bezwaar")):
                speech_acts["begrenzen"] += 1
            else:
                speech_acts["informeren"] += 1

        taalhandeling_zuiver = len(dictaat_zinnen) == 0
        ruimte_intact = len(dictaat_zinnen) == 0

        # Negatieve Invariant 1: Agency Inversion
        agency_treffers = [
            pat.replace(r"\b", "").replace(r"\s+", " ")
            for pat in cls.AGENCY_INVERSION_PATTERNS
            if re.search(pat, lower_text)
        ]
        geen_agency_inversion = len(agency_treffers) == 0

        # Negatieve Invariant 2: Sussen noch Demoniseren
        demon_treffers = [
            pat.replace(r"\b", "").replace(r"\s+", " ")
            for pat in cls.DEMONISERING_PATTERNS
            if re.search(pat, lower_text)
        ]
        geen_sussen_of_demoniseren = (len(demon_treffers) == 0) and inhoud_behouden

        warnings: List[str] = []
        if ontbrekende_doelen:
            warnings.append(
                f"FH-01 Inhoudscontrole / Anti-Sussen: Kernfeit of doel ontbreekt in transformatie: {', '.join(ontbrekende_doelen)}."
            )
        if dictaat_zinnen:
            warnings.append(
                "FH-01 Taalhandeling- & Ruimtecontrole: Zin schrijft het professionele oordeel van de ontvanger voor als voldongen feit. "
                "Herleid dit naar het neerleggen van de eigen hulpvraag."
            )
        if agency_treffers:
            warnings.append(
                "FH-01 Negatieve Invariant 1 geschonden: Manipulatieve Agency Inversion gedetecteerd. "
                "Leg grenzen en verzoeken open en rechtstreeks op tafel."
            )
        if demon_treffers:
            warnings.append(
                f"FH-01 Negatieve Invariant 2 geschonden (Demoniseren): Jargon/vijandbeeld aangetroffen ({', '.join(demon_treffers)}). "
                "Registreer het signaal in zijn exacte, onopgesmukte omvang."
            )

        passed = (
            inhoud_behouden
            and taalhandeling_zuiver
            and ruimte_intact
            and geen_agency_inversion
            and geen_sussen_of_demoniseren
        )

        return FH01Report(
            passed=passed,
            inhoud_behouden=inhoud_behouden,
            taalhandeling_zuiver=taalhandeling_zuiver,
            ruimte_intact=ruimte_intact,
            geen_agency_inversion=geen_agency_inversion,
            geen_sussen_of_demoniseren=geen_sussen_of_demoniseren,
            ontbrekende_doelen=ontbrekende_doelen,
            dictaat_zinnen=dictaat_zinnen,
            demonisering_termen=demon_treffers,
            agency_inversion_treffers=agency_treffers,
            speech_act_breakdown=speech_acts,
            warnings=warnings,
        )

    @classmethod
    def build_fh01_intake_prompts(
        cls,
        raw_incoming_text: str,
        keten_goals: str = "",
        tafel_context: str = "",
    ) -> Dict[str, str]:
        """
        Genereert het strikte 2-staps Invoer-Filter uit Protocol FH-01 (§7.2):
        - Stap 1 (Zuiver Memoriaal): Het model krijgt ALLEEN de letterlijke tekst te zien
          zonder doelen, toonregels, escalatiekaders of strategie.
        - Stap 2 (Koppeling met Ketengrootboek & De Tafel): Pas nadat Stap 1 is vastgelegd,
          worden de doelen uit het Ketengrootboek en de Tafel-weging toegevoegd.
        """
        step_1 = (
            "=== PROTOCOL FH-01 — STAP 1: ZUIVER MEMORIAAL (LAAG A & LAAG B) ===\n"
            "Je ontvangt hieronder uitsluitend de letterlijke tekst van een binnengekomen bericht.\n"
            "Er zijn bewust GEEN doelen, GEEN strategie en GEEN escalatiekaders meegegeven.\n"
            "Voer uitsluitend deze twee taken uit (sussen noch demoniseren):\n"
            "1. LAAG A (Memoriaal - Feiten): Registreer letterlijk wat er staat (afzender, datum, citaten, concrete mededeling).\n"
            "2. LAAG B (Journaal - Werkhypothesen): Noteer welke lezingen taalkundig mogelijk zijn, expliciet gelabeld als werkhypothese.\n\n"
            "--- BEGIN LETTERLIJKE TEKST ---\n"
            f"{raw_incoming_text.strip()}\n"
            "--- EINDE LETTERLIJKE TEKST ---"
        )
        step_2 = (
            "=== PROTOCOL FH-01 — STAP 2: KOPPELING MET KETENGROOTBOEK (LAAG C) & TRANSFORMATIE (LAAG D) ===\n"
            "Neem de neutrale feitenregistratie en taalkundige lezingen uit Stap 1 als vaststaand vertrekpunt.\n"
            "Koppel deze nu aan de onderstaande doelen en constraints uit het Ketengrootboek (Laag C) en de Tafel-weging:\n"
            "- Verlaag het doel van de burger NOOIT stilzwijgend om frictie te vermijden (verbod op sussen).\n"
            "- Blaas een professionele afbakening NIET op tot een vijandbeeld (verbod op demoniseren).\n"
            "- Pas de drie IJkcontroles toe (1. Inhoud 100% behouden, 2. Taalhandeling zuiver, 3. Professionele ruimte ontvanger intact).\n\n"
            f"--- LAAG C: DOELEN & CONSTRAINTS UIT KETENGROOTBOEK ---\n{keten_goals.strip() or 'Geen specifieke ketendoelen opgegeven.'}\n\n"
            f"--- LAAG D: TAFEL-WEGING ---\n{tafel_context.strip() or 'Standaard Fluwelen Handschoen (kort, feitelijk, waardig).'}"
        )
        return {
            "step_1_memoriaal_prompt": step_1,
            "step_2_koppeling_prompt": step_2,
        }

    @classmethod
    def create_template(
        cls,
        afzender: str,
        ontvanger: str,
        situatie: str,
        achtergrond: str,
        beoordeling: str,
        verzoek: str,
        interventies: str = "",
        termijn_dagen: int = 14
    ) -> SBARMessage:
        """Genereert een formeel SBARIII berichtobject."""
        read_back = (
            f"Conform het closed-loop communication principe verzoek ik u de ontvangst "
            f"van dit bericht en de gemaakte afspraken binnen {termijn_dagen} dagen "
            f"schriftelijk te bevestigen."
        )
        return SBARMessage(
            identification=f"Betrokkene: {afzender}\nOntvanger: {ontvanger}\nKader: Integraal dossierbeheer (SBARIII)",
            situation=situatie,
            background=achtergrond,
            assessment=beoordeling,
            recommendation=verzoek,
            intervention=interventies or "Eerder dossieronderzoek en feitelijke afstemming verricht.",
            read_back=read_back,
            metadata={"termijn_dagen": str(termijn_dagen)}
        )

    @classmethod
    def get_defense_reply(cls, objection_type: str) -> str:
        """Geeft de geijkte wetenschappelijke repliek bij professionele tegenwerpingen."""
        replies = {
            "format": (
                "Dit format volgt de internationale medische en bestuurlijke overdrachtsstandaard "
                "(AHRQ TeamSTEPPS / SBARIII, PMC9778833). Dit borgt dat acute situatie, "
                "relevante voorgeschiedenis, risicoanalyse en het concrete verzoek eenduidig gescheiden zijn."
            ),
            "assessment": (
                "Het onderdeel Assessment is geen autoritaire diagnose, maar transparante sense-making "
                "op basis van de dossierstukken (conform AHRQ richtlijn), inclusief de risico's bij inactiviteit."
            ),
            "read_back": (
                "De vraag om een schriftelijke ontvangstbevestiging (Repeat-Back) borgt dat beide kanten "
                "dezelfde stand van het dossier hanteren, conform de Joint Commission International richtlijnen."
            )
        }
        return replies.get(objection_type, f"Zie voor de volledige onderbouwing: {cls.DEFENSE_REFERENCE}")


if __name__ == "__main__":
    sample = SBARProtocol.create_template(
        afzender="Persoon A (dossierbeheer)",
        ontvanger="Wmo Consulent / Afdeling Sociaal",
        situatie="Hapering in de continuïteit van de overdracht rond ondersteuning.",
        achtergrond="Besluit d.d. 12 januari 2024 en medische rapportage revalidatie.",
        beoordeling="Uit de stukken blijkt een discrepantie tussen de geïndiceerde uren en de geleverde zorg.",
        verzoek="Aanpassing van het zorgplan en formele schriftelijke beschikking.",
        interventies="Contact opgenomen met zorgaanbieder; administratief dossier compleet gemaakt.",
        termijn_dagen=14
    )
    print("=== SBARIII DEMO TEMPLATE ===")
    print(sample.to_text())
    print("\n=== VALIDATIE CHECK ===")
    rep = SBARProtocol.validate_text(sample.to_text())
    print(f"Is Valid: {rep.is_valid}, Score: {rep.score * 100:.1f}%, Missing: {rep.missing_components}")
    fh = SBARProtocol.validate_fh01_transform(sample.to_text(), required_goals=["zorgplan", "beschikking"])
    print(f"FH-01 Passed: {fh.passed}, Speech acts: {fh.speech_act_breakdown}")
