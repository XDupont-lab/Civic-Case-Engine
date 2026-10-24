#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CIVIC HELPER — SYSTEEM-CLASH SENTIMENT ANALYZER (v1.0)
Forensische Tekst- en Sentiment-Uitlezing gebaseerd op Schone Canon 06 & 11:
  - TRF v2.1: Scalaire Agency w(t) en GU_ext / GU_int Verhouding
  - TRF v3.5: 3-ODE Variabelen (w, theta_em, Psi_res)
  - G-TID & Systeem-Clash Dynamiek (Canon 11):
      * Wet 9 (Observer-Inhibitie & Naam-Bereidheid nu)
      * Monodromy-Cloaking Index (Oppervlakkige beleefdheid vs materiële constraint)
      * Klok-Asymmetrie (lambda_t vs v)
      * Harmonische Temperatuur T_H en Materiële Legitimiteit L
      * Clash-Regimes A t/m F en Mechanische Barbarij-Score (0–10)

Pure Python Standard Library (Zero External Dependencies).
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Force UTF-8 on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Lexicale en Structurele Signatuur-Patronen
# ---------------------------------------------------------------------------

# 1. Oppervlaktebeleefdheid & Sussers (Monodromy-Cloaking teller)
PATTERNS_CLOAKING_SURFACE = [
    r"\b(?:geachte|beste|hartelijk(?:e)?|vriendelijk(?:e)?)\b",
    r"\b(?:met vriendelijke groet|hoogachtend|fijn weekend|prettige dag)\b",
    r"\b(?:wij begrijpen dat|ik hoop dat u|wij vertrouwen erop|dank voor uw)\b",
    r"\b(?:tot onze spijt|wij betreuren|vervelend voor u|voor uw begrip)\b",
    r"\b(?:ter informatie|volledigheidshalve|voor alle duidelijkheid)\b",
    r"\b(?:bieden (?:wij|ik) (?:onze|mijn) excuses)\b",
]

# 2. Harde Constraint-Handhaving / Afwijzing (Onderstroom in Cloaking)
PATTERNS_CONSTRAINT_HARD = [
    r"\b(?:buiten behandeling|afgewezen|niet-ontvankelijk|ongegrond|afwijzing)\b",
    r"\b(?:geen sprake van|kan niet worden|wijzen wij af|niet gebleken)\b",
    r"\b(?:verval van recht|onherroepelijk|termijn is verstreken|te laat)\b",
    r"\b(?:dwangsom|invordering|beslag|incasso|verrekening|terugvordering)\b",
    r"\b(?:dient u|bent u verplicht|wordt u geacht|geen uitstel)\b",
    r"\b(?:geen fout in de systemen|geen systeemoverschrijdende contaminatie)\b",
]

# 3. Interne Proceswereld (GU_int: 'Paper State' & Zelfbehoud)
PATTERNS_GU_INT = [
    r"\b(?:systeem|systemen|applicatie|applicaties|kbb|dacas|suwinet)\b",
    r"\b(?:datafundament|ketenpartner|afdeling beroep|afdeling klachten)\b",
    r"\b(?:interne richtlijn|werkinstructie|procesverbaal|zaakskenmerk)\b",
    r"\b(?:dossiernummer|registratie|procedure|behandelprotocol|kpi)\b",
    r"\b(?:behandelaar|integraal team|toetsingskader|management)\b",
    r"\b(?:volgens protocol|conform beleid|standaardprocedure)\b",
]

# 4. Externe Materiële Realiteit (GU_ext: Feitelijke Wereld & Burgerrealiteit)
PATTERNS_GU_EXT = [
    r"\b(?:medisch|arts|huisarts|ziekenhuis|diagnose|behandeling|kliniek)\b",
    r"\b(?:bloedwaarde|wmo|huur|woning|dakloos|levensonderhoud|inkomen)\b",
    r"\b(?:kind|kinderen|gezin|echtscheiding|ongeval|trauma|nah)\b",
    r"\b(?:daadwerkelijk|feitelijk|bankrekening|betaling|euro|factuur)\b",
    r"\b(?:fysieke realiteit|bewijsstuk|getuige|oorspronkelijk)\b",
    r"\b(?:in persoon|gesproken met|thuisbezoek|geconstateerd ter plaatse)\b",
]

# 5. Eufemisering & Afschuiving (Wet 9: Observer-Inhibitie nu)
PATTERNS_EUPHEMISMS = [
    r"\b(?:menselijke fout|menselijke vergissing|onvolkomenheid|hapering)\b",
    r"\b(?:misverstand|administratieve omissie|ongelukkige samenloop)\b",
    r"\b(?:communicatiestoornis|onduidelijkheid|vertraging in de afhandeling)\b",
    r"\b(?:technisch incident|niet optimaal verlopen|aandachtspunt)\b",
]

# 6. Directe Benoeming van Fouten / Aansprakelijkheid (Hoge nu)
PATTERNS_DIRECT_NAMING = [
    r"\b(?:onrechtmatig|onwettig|in strijd met de wet|datalek)\b",
    r"\b(?:schending van art|grove nalatigheid|onterechte vordering)\b",
    r"\b(?:verkeerde bsn|gegevens van een derde|geheime gegevens)\b",
    r"\b(?:aansprakelijk|schadevergoeding|herstelplicht|dwaling)\b",
]

# 7. Agency-Beperking van de Burger (w -> 0, Ondergrens-Breuk)
PATTERNS_AGENCY_KILLER = [
    r"\b(?:u moet|u dient|u bent verplicht|geen mogelijkheid)\b",
    r"\b(?:niet toegestaan|onmiddellijk|zonder nader uitstel)\b",
    r"\b(?:afschrift geweigerd|geen inzage|buiten de kaders)\b",
    r"\b(?:geen gehoor|gesloten loket|automatisch gegenereerd)\b",
]

# 8. Agency-Bevordering van de Burger (w -> 0.40 - 0.55, Gezond Maatwerk)
PATTERNS_AGENCY_PROMOTER = [
    r"\b(?:in overleg met u|u heeft de keuze|maatwerk|uw zienswijze)\b",
    r"\b(?:u kunt aangeven|wij nodigen u uit|in samenspraak|uw voorkeur)\b",
    r"\b(?:ruimte voor uitzondering|persoonlijk contact|gezamenlijk)\b",
    r"\b(?:herziening|opschorting in afwachting|u behoudt het recht)\b",
]

# 9. Klok-Asymmetrie (Snelle fatale burger-termijn vs trage institutionele termijn)
PATTERNS_CLOCK_ASYMMETRY_CITIZEN = [
    r"\b(?:binnen 14 dagen|binnen twee weken|binnen 48 uur|binnen 6 weken)\b",
    r"\b(?:uiterlijk vóór|voor deze datum|op straffe van)\b",
]
PATTERNS_CLOCK_ASYMMETRY_INSTITUTION = [
    r"\b(?:zo spoedig mogelijk|binnen afzienbare tijd|in beraad)\b",
    r"\b(?:verdaagd|verlengd met|onderzoek vergt tijd|wegens drukte)\b",
]


# ---------------------------------------------------------------------------
# Data-Klassen voor Resultaat
# ---------------------------------------------------------------------------

@dataclass
class SysteemClashScore:
    # Metadata
    source_name: str
    char_count: int
    line_count: int

    # TRF v2.1 Metrics
    agency_w: float                 # w(t) in [0.0, 1.0] (0=robot/dicht, 0.25=natuurlijk, 0.45=gezond, >0.75=zwevend)
    gu_ext_count: int               # Aantal materiële referenties
    gu_int_count: int               # Aantal interne proces/systeem referenties
    gu_ratio: float                 # GU_int / (GU_ext + GU_int) in [0.0, 1.0] (1.0 = 100% navelstaren / Paper State)

    # TRF v3.5 Metrics
    theta_em_rad: float             # Emergente fasehoek (verdraaiing / framing-drift) in [0, pi]
    theta_em_deg: float             # In graden
    psi_res: float                  # Resonantieveld in [-1.0, +1.0] (-1 = pure afweer, +1 = volledige harmonie)

    # G-TID & Systeem-Clash Metrics (Canon 11)
    name_readiness_nu: float        # nu in [0.0, 1.0] (Wet 9: 1=onomwonden benoemd, 0.3=eufemistisch, 0=ontkenning)
    monodromy_cloaking: float       # Cloaking index [0.0, 1.0] (oppervlakte-sussing vs materiële afwijzing)
    harmonic_temp_th: float         # T_H in [0.0, 1.0] (ruimte voor menselijke maat/uitzonderingen)
    clock_asymmetry: float          # Klok-asymmetrie [0.0, 1.0] (1.0 = maximale termijndruk op burger, traag loket)
    mechanical_barbary: float       # Schaal 0.0 - 10.0 (G-TID Tabel NL publieke sector)

    # Classificatie
    clash_regime: str               # 'Regime A' t/m 'Regime F'
    regime_title: str
    diagnose_summary: str
    key_findings: List[str]


# ---------------------------------------------------------------------------
# Core Analyzer Engine
# ---------------------------------------------------------------------------

class SysteemClashAnalyzer:
    """Voert deterministische constraint- en clash-sentimentanalyse uit op brondocumenten."""

    def __init__(self):
        pass

    def _count_matches(self, text: str, patterns: List[str]) -> Tuple[int, List[str]]:
        count = 0
        found = []
        low = text.lower()
        for p in patterns:
            matches = re.findall(p, low)
            if matches:
                count += len(matches)
                found.extend(matches)
        return count, found

    def analyze_text(self, text: str, source_name: str = "tekst") -> SysteemClashScore:
        char_count = len(text)
        line_count = len(text.splitlines())

        # 1. Telling van indicatoren
        n_cloak_surf, found_cloak_surf = self._count_matches(text, PATTERNS_CLOAKING_SURFACE)
        n_const_hard, found_const_hard = self._count_matches(text, PATTERNS_CONSTRAINT_HARD)
        n_gu_int, found_gu_int = self._count_matches(text, PATTERNS_GU_INT)
        n_gu_ext, found_gu_ext = self._count_matches(text, PATTERNS_GU_EXT)
        n_euphemisms, found_euphemisms = self._count_matches(text, PATTERNS_EUPHEMISMS)
        n_direct_name, found_direct_name = self._count_matches(text, PATTERNS_DIRECT_NAMING)
        n_agency_kill, found_agency_kill = self._count_matches(text, PATTERNS_AGENCY_KILLER)
        n_agency_prom, found_agency_prom = self._count_matches(text, PATTERNS_AGENCY_PROMOTER)
        n_clock_cit, _ = self._count_matches(text, PATTERNS_CLOCK_ASYMMETRY_CITIZEN)
        n_clock_inst, _ = self._count_matches(text, PATTERNS_CLOCK_ASYMMETRY_INSTITUTION)

        # 2. Berekening TRF v2.1 Scalaire Agency w(t)
        # Baseline = w_nat = 0.25 (ambtelijk Nederlands rustniveau)
        # Promoters verhogen w, Killers drukken w naar 0
        total_agency_tokens = n_agency_kill + n_agency_prom
        if total_agency_tokens == 0:
            agency_w = 0.25
        else:
            shift = (n_agency_prom - n_agency_kill) / (total_agency_tokens + 2.0)
            agency_w = max(0.02, min(0.95, 0.25 + 0.35 * shift))

        # Als er harde constraints zijn en nul agency_promoters:
        if n_const_hard > 0 and n_agency_prom == 0:
            agency_w = max(0.04, agency_w * 0.70)

        # 3. Berekening GU_ratio (Paper State Index)
        total_gu = n_gu_ext + n_gu_int
        if total_gu == 0:
            gu_ratio = 0.50
        else:
            gu_ratio = round(n_gu_int / total_gu, 3)

        # 4. Berekening TRF v3.5 Variabelen (theta_em & psi_res)
        # theta_em (Fasehoek / verdraaiing): gestuurd door eufemismen en interne procesverschuiving
        distortion_density = (n_euphemisms * 1.5 + n_gu_int * 0.4) / max(1.0, math.sqrt(line_count + 1))
        theta_em_rad = min(math.pi, distortion_density * 0.55)
        theta_em_deg = round(math.degrees(theta_em_rad), 1)

        # psi_res (Resonantieveld): ethiek vs frictie [-1.0, +1.0]
        # Direct benoemen en agency geven is positief; eufemisering en constraint-drang is negatief
        pos_weight = n_direct_name * 1.2 + n_agency_prom * 1.0 + n_gu_ext * 0.3
        neg_weight = n_const_hard * 1.1 + n_euphemisms * 1.3 + n_agency_kill * 1.0 + n_gu_int * 0.4
        tot_weight = pos_weight + neg_weight
        if tot_weight == 0:
            psi_res = 0.0
        else:
            psi_res = round((pos_weight - neg_weight) / tot_weight, 3)

        # 5. G-TID Veldcoördinaten (Canon 11)
        # Wet 9: Naam-Bereidheid nu in [0.0, 1.0]
        if n_direct_name > 0 and n_euphemisms == 0:
            name_readiness_nu = 0.95
        elif n_direct_name > 0 and n_euphemisms > 0:
            # Mengvorm: erkent wel iets, maar eufemiseert tegelijk
            name_readiness_nu = round(0.40 + 0.30 * (n_direct_name / (n_direct_name + n_euphemisms)), 2)
        elif n_euphemisms > 0:
            name_readiness_nu = 0.30
        elif n_const_hard > 0:
            name_readiness_nu = 0.15  # Ontkenning / weigering
        else:
            name_readiness_nu = 0.50

        # Monodromy-Cloaking: Hoge oppervlakte-sussing + Harde constraint
        if n_cloak_surf > 0 and n_const_hard > 0:
            cloaking = min(1.0, 0.40 + 0.15 * math.log(1 + n_cloak_surf * n_const_hard))
        elif n_cloak_surf > 0 and n_euphemisms > 0:
            cloaking = min(0.80, 0.30 + 0.12 * math.log(1 + n_cloak_surf * n_euphemisms))
        else:
            cloaking = 0.10

        # Harmonische Temperatuur T_H in [0.0, 1.0] (Tolerantie voor menselijke maat)
        if n_agency_prom > 0 or n_direct_name > 0:
            harmonic_temp_th = round(min(1.0, 0.15 + 0.20 * (n_agency_prom + n_direct_name)), 2)
        else:
            harmonic_temp_th = round(max(0.02, 0.12 - 0.02 * n_const_hard), 2)

        # Klok-Asymmetrie
        if n_clock_cit > 0 and n_clock_inst > 0:
            clock_asymmetry = 0.85
        elif n_clock_cit > 0:
            clock_asymmetry = 0.70
        elif n_clock_inst > 0:
            clock_asymmetry = 0.50
        else:
            clock_asymmetry = 0.20

        # Mechanische Barbarij-Score (0.0 t/m 10.0, conform G-TID Zes Sectoren Snapshot)
        # Componenten: lage agency, negatieve psi_res, hoge cloaking, lage T_H, hoge GU_ratio
        barb_agency = (1.0 - agency_w) * 3.0
        barb_psi = max(0.0, -psi_res) * 2.5
        barb_cloak = cloaking * 2.0
        barb_th = (1.0 - harmonic_temp_th) * 1.5
        barb_gu = gu_ratio * 1.0
        mechanical_barbary = round(min(10.0, barb_agency + barb_psi + barb_cloak + barb_th + barb_gu), 1)

        # 6. Clash-Regime Classificatie (Wetten 10-13 & Regimes A t/m F)
        if "beslag" in text.lower() or "dwangbevel" in text.lower() or "ontruiming" in text.lower():
            clash_regime = "Regime A"
            regime_title = "Destructief / Executoriaal (Fysieke/financiële uitschakeling)"
        elif "buiten behandeling" in text.lower() or "uitschrijving" in text.lower() or "ontzegd" in text.lower():
            clash_regime = "Regime B"
            regime_title = "Displacement / Uitsluiting (Verdrijving uit het loket/systeem)"
        elif n_gu_int > n_gu_ext and n_const_hard > 0 and agency_w < 0.20:
            clash_regime = "Regime C"
            regime_title = "Administratieve Uitholling (Kastje-naar-de-muur zonder heropbouw)"
        elif "verplicht traject" in text.lower() or "onder curatele" in text.lower():
            clash_regime = "Regime D"
            regime_title = "Dwangmatige Substraat-Onderwerping (Geforceerde aanpassing)"
        elif psi_res >= -0.10 and name_readiness_nu >= 0.60:
            clash_regime = "Regime E"
            regime_title = "Symmetrische Exchange-Dialoog (Contractueel feitenrespect)"
        elif psi_res > 0.40 and agency_w >= 0.40:
            clash_regime = "Regime F"
            regime_title = "Harmonische Sluiting (Vrijwillige samenwerking & herstel)"
        else:
            clash_regime = "Regime C"
            regime_title = "Administratieve Uitholling & Institutioneel Zelfbehoud"

        # 7. Sleutelbevindingen formuleren
        findings = []
        if cloaking >= 0.50:
            findings.append(f"Hoge Monodromy-Cloaking ({cloaking:.2f}): formele/sussende toonzetting maskeert een harde materiële afwijzing of blokkade.")
        if name_readiness_nu <= 0.35:
            euphemism_sample = ", ".join(list(set(found_euphemisms))[:3]) if found_euphemisms else "geen"
            findings.append(f"Observer-Inhibitie actief (nu={name_readiness_nu:.2f}): structurele systeemhaperingen worden eufemistisch afgewenteld ({euphemism_sample}).")
        if agency_w < 0.15:
            findings.append(f"Ondergrens-Breuk in Agency (w={agency_w:.2f}): de burger of professional aan de balie heeft feitelijk 0 reële handelingsruimte.")
        if gu_ratio >= 0.65:
            findings.append(f"Paper State dominantie (GU_int {gu_ratio*100:.0f}%): communicatie cirkelt primair rond eigen interne applicaties en procesbehoud.")
        if clock_asymmetry >= 0.65:
            findings.append("Klok-Asymmetrie: fatale termijndruk op de burger gekoppeld aan vage/trage institutionele doorlooptijd.")
        if not findings:
            findings.append("Geen acute pathologische clash-indicatoren gedetecteerd; communicatie verloopt relatief evenwichtig.")

        # Diagnose-samenvatting
        diagnose = (
            f"Document toont karakteristieken van {clash_regime} ({regime_title}). "
            f"Agency w={agency_w:.2f}, Faseverdraaiing theta_em={theta_em_deg}°, "
            f"Naambereidheid nu={name_readiness_nu:.2f}, Mechanische Barbarij-Score: {mechanical_barbary}/10."
        )

        return SysteemClashScore(
            source_name=source_name,
            char_count=char_count,
            line_count=line_count,
            agency_w=round(agency_w, 3),
            gu_ext_count=n_gu_ext,
            gu_int_count=n_gu_int,
            gu_ratio=gu_ratio,
            theta_em_rad=round(theta_em_rad, 3),
            theta_em_deg=theta_em_deg,
            psi_res=psi_res,
            name_readiness_nu=name_readiness_nu,
            monodromy_cloaking=round(cloaking, 3),
            harmonic_temp_th=harmonic_temp_th,
            clock_asymmetry=round(clock_asymmetry, 3),
            mechanical_barbary=mechanical_barbary,
            clash_regime=clash_regime,
            regime_title=regime_title,
            diagnose_summary=diagnose,
            key_findings=findings,
        )


# ---------------------------------------------------------------------------
# Terminal UI & Formattering
# ---------------------------------------------------------------------------

def _render_bar(val: float, max_val: float = 1.0, length: int = 15) -> str:
    norm = max(0.0, min(1.0, val / max_val))
    filled = int(round(norm * length))
    return "█" * filled + "░" * (length - filled)


def print_score_report(score: SysteemClashScore) -> None:
    print("=" * 74)
    print(f"  🏛️  CIVIC HELPER — SYSTEEM-CLASH SENTIMENT ANALYZER")
    print(f"  Gebaseerd op Schone Canon 06 (TRF 2.1 & 3.5) & 11 (G-TID & Clash-Wetten)")
    print("=" * 74)
    print(f"  Bronstuk:     {score.source_name}")
    print(f"  Omvang:       {score.line_count} regels, {score.char_count} tekens")
    print("-" * 74)

    # 1. TRF Dashboard
    print("  [1] TRF v2.1 & v3.5 SCALAIRE TRAJECT-METRIEKEN")
    print(f"    • Agency w(t)          : {score.agency_w:.3f}  [{_render_bar(score.agency_w)}]  "
          f"({'Ondergrens-breuk (dicht)' if score.agency_w < 0.15 else 'Asymmetrisch' if score.agency_w < 0.30 else 'Evenwichtig'})")
    print(f"    • Faseverdraaiing θ_em : {score.theta_em_deg:5.1f}°  [{_render_bar(score.theta_em_rad, math.pi)}]  "
          f"({'Ernstige framing-drift' if score.theta_em_deg > 45 else 'Gematigd' if score.theta_em_deg > 15 else 'Zuiver'})")
    print(f"    • Resonantieveld Ψ_res : {score.psi_res:+.3f}  [{_render_bar((score.psi_res + 1.0)/2.0)}]  "
          f"({'Hoge frictie / afweer' if score.psi_res < -0.3 else 'Neutraal' if score.psi_res <= 0.2 else 'Resonant'})")
    print(f"    • GU-Verhouding        : {score.gu_ratio*100:4.1f}% interne procesfocus (GU_ext: {score.gu_ext_count}, GU_int: {score.gu_int_count})")
    print()

    # 2. G-TID & Systeem-Clash Coördinaten
    print("  [2] G-TID VELDCOÖRDINATEN & CLASH-DYNAMIEK (Canon 11)")
    print(f"    • Naambereidheid ν (Wet 9) : {score.name_readiness_nu:.2f}  [{_render_bar(score.name_readiness_nu)}]  "
          f"({'Volledig' if score.name_readiness_nu > 0.8 else 'Eufemistisch' if score.name_readiness_nu >= 0.3 else 'Inhibitie/Ontkenning'})")
    print(f"    • Monodromy-Cloaking       : {score.monodromy_cloaking:.2f}  [{_render_bar(score.monodromy_cloaking)}]  "
          f"({'Kritiek (sussende façade)' if score.monodromy_cloaking >= 0.50 else 'Laag'})")
    print(f"    • Harmonische Temp. T_H    : {score.harmonic_temp_th:.2f}  [{_render_bar(score.harmonic_temp_th)}]  "
          f"({'Zero-Tolerance vinklijst' if score.harmonic_temp_th < 0.10 else 'Ruimte voor menselijke maat'})")
    print(f"    • Klok-Asymmetrie          : {score.clock_asymmetry:.2f}  [{_render_bar(score.clock_asymmetry)}]  "
          f"({'Sterk asymmetrisch (burger onder druk)' if score.clock_asymmetry >= 0.60 else 'Symmetrisch'})")
    print()

    # 3. Eindclassificatie
    print("  [3] CLASSIFICATIE & DIAGNOSE")
    print(f"    • Actief Clash-Regime      : {score.clash_regime} — {score.regime_title}")
    print(f"    • Mechanische Barbarij     : {score.mechanical_barbary:.1f} / 10.0  "
          f"[{_render_bar(score.mechanical_barbary, 10.0)}]")
    print()
    print("  Belangrijkste waarnemingen:")
    for f in score.key_findings:
        print(f"    ⚠️  {f}")
    print("=" * 74)


# ---------------------------------------------------------------------------
# CLI & Auto-Discovery
# ---------------------------------------------------------------------------

def find_target_document(explicit_path: Optional[str] = None) -> Path:
    if explicit_path:
        p = Path(explicit_path)
        if p.exists():
            return p
        raise FileNotFoundError(f"Bestand niet gevonden: {explicit_path}")

    # Zoek nieuwste draft in Outgoing_Drafts
    workspace = Path(r"E:\LLM_Workspace")
    civic = workspace / "CivicHelper"
    drafts_dir = civic / "Outgoing_Drafts"
    if drafts_dir.exists():
        drafts = sorted(
            [f for f in drafts_dir.glob("*.md") if f.is_file()],
            key=lambda f: f.stat().st_mtime,
            reverse=True,
        )
        if drafts:
            return drafts[0]

    # Zoek nieuwste document in Zorgdossier
    zorg_dir = workspace / "Zorgdossier"
    if zorg_dir.exists():
        zorg_docs = sorted(
            [f for f in zorg_dir.glob("*.md") if f.is_file() and not f.name.startswith("README")],
            key=lambda f: f.stat().st_mtime,
            reverse=True,
        )
        if zorg_docs:
            return zorg_docs[0]

    raise FileNotFoundError("Geen analyseerbaar document aangetroffen in Outgoing_Drafts of Zorgdossier.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Civic Helper Systeem-Clash Sentiment Analyzer (TRF 2.1, 3.5, Canon 11)")
    parser.add_argument("file", nargs="?", default=None, help="Pad naar het te analyseren tekst- of markdownbestand")
    parser.add_argument("--json", action="store_true", help="Uitvoer als JSON in plaats van geformatteerd rapport")
    parser.add_argument("--text", type=str, default=None, help="Rechtstreekse tekstinvoer i.p.v. bestand")
    args = parser.parse_args()

    analyzer = SysteemClashAnalyzer()

    if args.text:
        content = args.text
        source_name = "Directe tekstinvoer"
    else:
        try:
            target_file = find_target_document(args.file)
            content = target_file.read_text(encoding="utf-8", errors="replace")
            source_name = target_file.name
        except Exception as e:
            print(f"FOUT: Kon geen doeldocument openen: {e}", file=sys.stderr)
            return 1

    score = analyzer.analyze_text(content, source_name=source_name)

    if args.json:
        print(json.dumps(asdict(score), indent=2, ensure_ascii=False))
    else:
        print_score_report(score)

    return 0


if __name__ == "__main__":
    sys.exit(main())
