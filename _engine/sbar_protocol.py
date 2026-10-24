#!/usr/bin/env python3
"""
CIVIC HELPER — SBARIII COMMUNICATION PROTOCOL & VALIDATOR
Pure Python Standard Library (Zero External Dependencies).

Onderbouwd door:
- AHRQ TeamSTEPPS 3.0 Curriculum (Repeat-Back Recommendations and Requests)
- Martínez-Fernández et al. (2022), PMC9778833 (Veerkracht + 97% failure ongestructureerde handoffs)
- Civic Helper: NOTITIE_COMMUNICATIEPROTOCOL_SBARIII.md

Componenten van SBARIII:
1. I — Identification (Identificatie van afzender, ontvanger en dossier)
2. S — Situation (De acute focus/vraag van vandaag)
3. B — Background (Geobjectiveerde context uit de tijdlijn)
4. A — Assessment (Sense-making, werkhypothese, hiaten, risico bij inactiviteit)
5. R — Recommendation & Request (Concreet handelingsvoorstel)
6. I — Intervention (Reeds ondernomen stappen door de betrokkene)
7. I — Information / Read-Back (Verplichte gesloten lus / Tegenboekingstermijn)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional


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
            lines.append(f"3. ACHTERGROND (CONTEXT TIJDLIN):\n{self.background.strip()}\n")
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


class SBARProtocol:
    """Validator en generator voor het SBARIII overdrachtsprotocol."""

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
    # Korte demonstratie / zelftest
    sample = SBARProtocol.create_template(
        afzender="Xander (dossierbeheer)",
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
