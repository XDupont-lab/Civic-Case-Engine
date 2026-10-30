#!/usr/bin/env python3
"""
CIVIC HELPER — INSTITUTIONELE CONDITIES & POLDERMODEL-VERTALER (v1.0)
Pure Python Standard Library (Zero External Dependencies).

Gebaseerd op de civiele patroontaxonomie van Civic Decision Engine (Moloney, v13.0),
vertaald naar de Nederlandse bestuursrechtelijke context en geconditioneerd door
Protocol FH-01 (De Fluwelen Handschoen & Het Poldermodel):

De 5 Structurele Condities:
1. TRANSFER_OF_BURDEN:
   Verantwoordelijkheid voor opzoekwerk, verificatie of voortgang wordt verplaatst naar de burger,
   terwijl de instantie over de stukken beschikt of wettelijk gehouden is het dossier te beheren.
2. PROCEDURAL_DEFLECTION:
   Procedurele mechanismen, poortwachters, portaaleisen of doorverwijzingen worden gebruikt
   als alternatief voor inhoudelijke behandeling.
3. REPEATED_CONTACT_WITHOUT_RESOLUTION:
   Burger doet herhaaldelijk dezelfde melding of vraag, maar elk contact start opnieuw
   bij stap nul zonder accumulatie van institutioneel inzicht.
4. INSTITUTIONAL_DELAY:
   Verstrijken van redelijke of wettelijke termijnen (Awb, AVG, Wmo) zonder formele
   beslissing of rechtmatige verdaging.
5. ESCALATION_WITHOUT_RESPONSE:
   Feitelijke urgentie, medische noodzaak of schade neemt toe, maar de ambtelijke
   reactie blijft ongewijzigd in een trage of niet-passende modus.

HET POLDERMODEL-PRINCIPE (Negatieve Invariant Protocol FH-01):
- De conditie is een INTERNE DIAGNOSE voor De Tafel en de boekhouding.
- De conditie wordt NOOIT als strijdbare aanklacht naar de ambtenaar of behandelaar gestuurd.
- De Polder-vertaler formuleert een hoffelijke, ontlastende handreiking die de ambtenaar
  gezichtsverlies bespaart en hem helpt het dossier direct vlot te trekken.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
import re
import sys
from typing import Any, Dict, List, Optional


# Nederlandse canonieke vertaling en taxonomie
NEDERLANDSE_TERMEN: Dict[str, str] = {
    # 5 Structurele condities
    "TRANSFER_OF_BURDEN": "Lastenverplaatsing",
    "PROCEDURAL_DEFLECTION": "Loketomleiding",
    "REPEATED_CONTACT_WITHOUT_RESOLUTION": "Dossier-amnesie",
    "INSTITUTIONAL_DELAY": "Termijnoverschrijding",
    "ESCALATION_WITHOUT_RESPONSE": "Urgentiekloof",
    # 4 Diagnostische signalen
    "Evidence Strength": "Bewijskracht",
    "Deadline Pressure": "Termijndruk",
    "Escalation Readiness": "Escalatierijpheid",
    "Case Momentum": "Dossierdynamiek",
    # Trajectoria
    "Stable": "Stabiel",
    "Deteriorating": "Verslechterend",
    "Improving": "Verbeterend",
    # Ketenbegrippen
    "Chain of Custody": "Bewijsketen (onveranderlijk)",
    "Public Record": "Vastgelegd dossierstuk",
    "Verification Hash": "Verificatie-hash (SHA-256)",
}


@dataclass
class ConditionDefinition:
    code: str
    code_en: str
    name_nl: str
    description: str
    indicators: List[str]
    polder_principe: str
    verboden_toon: List[str]  # Wat we NOOIT zeggen (adversarieel)
    polder_handreiking_sjabloon: str  # De Fluwelen Handschoen formulering


CONDITIES_TAXONOMIE: Dict[str, ConditionDefinition] = {
    "LASTENVERPLAATSING": ConditionDefinition(
        code="LASTENVERPLAATSING",
        code_en="TRANSFER_OF_BURDEN",
        name_nl="Lastenverplaatsing (Omkering van inspanning)",
        description=(
            "De instantie vraagt de burger om stukken, bewijzen of bevestigingen aan te leveren "
            "waarover de instantie zelf al beschikt of die wettelijk in haar eigen beheer horen."
        ),
        indicators=[
            r"\bkunt u (?:ons )?(?:alsnog )?(?:een kopie|bewijsstukken|specificaties) (?:van |toezenden|sturen)\b",
            r"\bhebben wij (?:uw|de) (?:gegevens|stukken|aanvraag) nog niet (?:ontvangen|aangetroffen)\b",
            r"\bdient u zelf contact op te nemen met\b",
            r"\bverzoeken wij u (?:opnieuw|wederom) (?:het formulier|de gegevens) in te vullen\b",
            r"\bvinden wij niet terug in ons systeem\b",
        ],
        polder_principe=(
            "Ontlast de ambtenaar door het zoekwerk voor hem te doen zónder verwijt. "
            "Bied de exacte vindplaats, datum en kenmerk van de eerdere aanlevering direct aan."
        ),
        verboden_toon=[
            "U heeft dit zelf al",
            "U bent nalatig met uw archief",
            "U keert de bewijslast om",
            "Zoek het zelf maar uit in uw eigen systeem",
        ],
        polder_handreiking_sjabloon=(
            "Om u zoekwerk in het archief te besparen, treft u hierbij de exacte datum ({datum}) "
            "en het dossierkenmerk ({kenmerk}) van het eerdere schrijven waarin deze bescheiden reeds "
            "zijn aangeleverd. Mocht het nodig zijn, treft u de bewijsstukken hierbij nogmaals als bijlage "
            "aan, zodat u direct over alle informatie beschikt om het dossier te behandelen."
        ),
    ),
    "LOKETOMLEIDING": ConditionDefinition(
        code="LOKETOMLEIDING",
        code_en="PROCEDURAL_DEFLECTION",
        name_nl="Loketomleiding (Procedurele afleiding)",
        description=(
            "De instantie werpt een procedurele, digitale of formele drempel op, of verwijst "
            "zonder warme overdracht door naar een ander loket, waardoor de inhoudelijke vraag blijft liggen."
        ),
        indicators=[
            r"\bwij zijn niet bevoegd\b|\bhoort niet bij onze afdeling\b",
            r"\bdit verzoek kunt u uitsluitend via (?:het portaal|de website|digid)\b",
            r"\bverwijzen wij u door naar\b|\bmoet u zich wenden tot\b",
            r"\bniet in behandeling genomen wegens het ontbreken van (?:een formulier|handtekening)\b",
            r"\btelefonisch contact opnemen via ons algemene nummer\b",
        ],
        polder_principe=(
            "Erken de rol van de ambtenaar en sluit aan bij art. 2:1 Awb en collegiaal bestuur. "
            "Bevestig de inhoudelijke kern en vraag vriendelijk om een warme doorgeleiding."
        ),
        verboden_toon=[
            "U stuurt me van het kastje naar de muur",
            "U weigert uw werk te doen",
            "Dit is een bureaucratische schijnvertoning",
            "U bent verplicht mij te helpen",
        ],
        polder_handreiking_sjabloon=(
            "Dank voor uw toelichting over de interne bevoegdheidsverdeling. Gelet op de samenhang "
            "van het dossier en artikel 2:1 Awb bevestig ik dat het verzoek ziet op {onderwerp}. "
            "Ik stel het bijzonder op prijs als u dit schrijven intern warm wilt doorgeleiden naar de "
            "juiste behandelaar ({doel_loket}), zodat de continuïteit en de lopende termijn gewaarborgd blijven."
        ),
    ),
    "DOSSIER_AMNESIE": ConditionDefinition(
        code="DOSSIER_AMNESIE",
        code_en="REPEATED_CONTACT_WITHOUT_RESOLUTION",
        name_nl="Dossier-amnesie (Herhaald contact zonder cumulatie)",
        description=(
            "Burger heeft reeds meerdere malen contact gehad, maar de reactie toont geen "
            "opbouw op eerdere toezeggingen of reeds vastgestelde feiten."
        ),
        indicators=[
            r"\bnaar aanleiding van uw (?:eerste )?bericht\b",
            r"\blangs deze weg informeren wij u voor het eerst\b",
            r"\bwij hebben geen eerdere correspondentie\b",
            r"\been nieuwe medewerker is aangesteld\b|\bnieuwe consulent\b",
            r"\bopnieuw een intakegesprek\b|\bweer van voren af aan\b",
        ],
        polder_principe=(
            "Reconstrueer de gezamenlijke tijdlijn zonder verwijt over verloop of personeelswisselingen. "
            "Geef de nieuwe behandelaar een kant-en-klaar handvat om direct in te stappen."
        ),
        verboden_toon=[
            "Elke keer weer een andere consulent",
            "U leest uw eigen dossiers niet",
            "Ik word er doodziek van dat ik alles opnieuw moet uitleggen",
            "Uw organisatie lijdt aan institutioneel geheugenverlies",
        ],
        polder_handreiking_sjabloon=(
            "Terugkoppelend op ons eerdere overleg van {datum_vorig} en ter verwelkoming van uw "
            "betrokkenheid als nieuwe behandelaar, vat ik hierbij kort de reeds gezamenlijk vastgestelde "
            "uitgangspunten samen: {kernpunten}. Hiermee sluiten we naadloos aan op het eerdere traject "
            "en kunnen we gezamenlijk toewerken naar de afhandeling."
        ),
    ),
    "TERMIJNOVERSCHRIJDING": ConditionDefinition(
        code="TERMIJNOVERSCHRIJDING",
        code_en="INSTITUTIONAL_DELAY",
        name_nl="Termijnoverschrijding (Structurele vertraging)",
        description=(
            "Het overschrijden van de wettelijke of aangekondigde beslistermijn zonder tijdige, "
            "gemotiveerde verdaging of besluit."
        ),
        indicators=[
            r"\bwegens (?:grote )?achterstanden\b|\bdrukke werkzaamheden\b",
            r"\bonze excuses voor de vertraging\b|\bheeft langer geduurd dan verwacht\b",
            r"\bnog geen beslissing kunnen nemen\b",
            r"\bvroegtijdig afhandelen is niet gelukt\b",
            r"\btermijn is verstreken\b",
        ],
        polder_principe=(
            "Herinner zakelijk aan de wettelijke termijn en bied een concrete, realistische "
            "sluitingsdatum aan. Houd de formele ingebrekestelling als stille waarborg in de achterzak."
        ),
        verboden_toon=[
            "U overtreedt stelselmatig de wet",
            "U krijgt van mij direct een dwangsom",
            "U laat mij bewust in de kou staan",
            "Onbekwame ambtenarij",
        ],
        polder_handreiking_sjabloon=(
            "Met het oog op de wettelijke beslistermijn (artikel {artikel_termijn} Awb), die op {datum_verval} "
            "is verstreken, vraag ik u vriendelijk naar de stand van zaken rond het besluit. "
            "Ik begrijp dat werkdruk een rol kan spelen; om verdere escalatie of formele termijnstappen "
            "te voorkomen, verneem ik graag uiterlijk {datum_voorstel} uw inhoudelijke besluit."
        ),
    ),
    "URGENTIEKLOOF": ConditionDefinition(
        code="URGENTIEKLOOF",
        code_en="ESCALATION_WITHOUT_RESPONSE",
        name_nl="Urgentiekloof (Zorgtoename zonder tempo-aanpassing)",
        description=(
            "De gezondheidstoestand, acute zorgvraag of bestaansonzekerheid van de burger verslechtert, "
            "maar de ambtelijke behandelstroom blijft hangen in reguliere lage-urgentie modus."
        ),
        indicators=[
            r"\bvolgt de normale procedure\b|\bstaat op de wachtlijst\b",
            r"\bgeen voorrang mogelijk\b|\bgeen spoedindicatie\b",
            r"\bstandaard behandeltermijn van \d+ weken\b",
            r"\bafwijzing van het spoedverzoek\b",
        ],
        polder_principe=(
            "Objectiveer de toegenomen medische of maatschappelijke feiten via neutrale deskundigenwaarneming "
            "(bijv. huisarts, specialist). Geef de instantie de formele onderbouwing om een spoed- of maatwerkpad te rechtvaardigen."
        ),
        verboden_toon=[
            "Als ik doodga is het jullie schuld",
            "U heeft geen greintje menselijkheid",
            "U weigert te zien dat ik instort",
            "Bureaucratische moordenaars",
        ],
        polder_handreiking_sjabloon=(
            "Gelet op de recente feitelijke wijziging in de medische belastbaarheid, zoals geobjectiveerd door "
            "{behandelaar} op {datum_diagnose}, hecht ik eraan u deze gegevens ter hand te stellen. "
            "Deze informatie biedt uw afdeling de feitelijke grondslag om binnen uw vigerende beleidskader "
            "een passende maatwerkvoorziening of versnelde prioritering te honoreren."
        ),
    ),
}

# Alias mapping voor Engelse CDE v13 codes naar Nederlandse codes
ALIASSEN_ENGELS_NAAR_NL: Dict[str, str] = {
    "TRANSFER_OF_BURDEN": "LASTENVERPLAATSING",
    "PROCEDURAL_DEFLECTION": "LOKETOMLEIDING",
    "REPEATED_CONTACT_WITHOUT_RESOLUTION": "DOSSIER_AMNESIE",
    "INSTITUTIONAL_DELAY": "TERMIJNOVERSCHRIJDING",
    "ESCALATION_WITHOUT_RESPONSE": "URGENTIEKLOOF",
}


@dataclass
class ConditionMatch:
    code: str
    code_en: str
    name_nl: str
    confidence: float
    indicators_found: List[str]
    description: str
    polder_principe: str
    polder_handreiking: str
    verboden_toon: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "code_en": self.code_en,
            "name_nl": self.name_nl,
            "confidence": self.confidence,
            "indicators_found": self.indicators_found,
            "description": self.description,
            "polder_principe": self.polder_principe,
            "polder_handreiking": self.polder_handreiking,
            "verboden_toon": self.verboden_toon,
        }


class InstitutionalConditionsAnalyzer:
    """Analyseert documenten en ketenhistorie op de 5 structurele condities

    en genereert Fluwelen Handschoen / Poldermodel handelingsadviezen.
    """

    def __init__(self, taxonomie: Optional[Dict[str, ConditionDefinition]] = None):
        self.taxonomie = taxonomie or CONDITIES_TAXONOMIE

    def scan_tekst(
        self,
        tekst: str,
        context: Optional[Dict[str, Any]] = None
    ) -> List[ConditionMatch]:
        """Scant inkomende brieftekst en optionele dossiercontext op condities."""
        ctx = context or {}
        matches: List[ConditionMatch] = []
        tekst_schoon = tekst.replace("\r\n", "\n")

        for code, defn in self.taxonomie.items():
            gevonden_patronen = []
            for pat in defn.indicators:
                m = re.search(pat, tekst_schoon, re.IGNORECASE)
                if m:
                    gevonden_patronen.append(m.group(0))

            # Context-gedreven indicatoren (bijv. eerdere contactmomenten of termijndruk)
            if code in ("DOSSIER_AMNESIE", "REPEATED_CONTACT_WITHOUT_RESOLUTION"):
                contact_count = ctx.get("eerdere_contacten_count", 0)
                if contact_count >= 3:
                    gevonden_patronen.append(f"Ketenhistorie: {contact_count} eerdere contacten zonder sluiting")
            elif code in ("TERMIJNOVERSCHRIJDING", "INSTITUTIONAL_DELAY"):
                dagen_open = ctx.get("dagen_openstaand", 0)
                wettelijke_termijn_dagen = ctx.get("wettelijke_termijn_dagen", 0)
                if wettelijke_termijn_dagen > 0 and dagen_open > wettelijke_termijn_dagen:
                    gevonden_patronen.append(f"Klok: {dagen_open} dagen verstreken (termijn was {wettelijke_termijn_dagen})")
            elif code in ("URGENTIEKLOOF", "ESCALATION_WITHOUT_RESPONSE"):
                if ctx.get("medische_urgentie_verhoogd", False) and ctx.get("spoed_afgewezen", False):
                    gevonden_patronen.append("Ketenfeit: Verhoogde urgentie geregistreerd maar standaardpad gehandhaafd")

            if gevonden_patronen:
                conf = min(0.95, 0.60 + 0.15 * len(gevonden_patronen))
                
                # Vul het poldersjabloon in met contextvariabelen
                handreiking = defn.polder_handreiking_sjabloon.format(
                    datum=ctx.get("datum", "recente datum"),
                    kenmerk=ctx.get("kenmerk", "uw kenmerk"),
                    onderwerp=ctx.get("onderwerp", "het lopende verzoek"),
                    doel_loket=ctx.get("doel_loket", "de bevoegde afdeling"),
                    datum_vorig=ctx.get("datum_vorig", "onlangs"),
                    kernpunten=ctx.get("kernpunten", "de eerder besproken uitgangspunten"),
                    artikel_termijn=ctx.get("artikel_termijn", "4:13"),
                    datum_verval=ctx.get("datum_verval", "de vervaldatum"),
                    datum_voorstel=ctx.get("datum_voorstel", "binnen twee weken"),
                    behandelaar=ctx.get("behandelaar", "de behandelend arts"),
                    datum_diagnose=ctx.get("datum_diagnose", "recente datum"),
                )

                matches.append(ConditionMatch(
                    code=code,
                    code_en=defn.code_en,
                    name_nl=defn.name_nl,
                    confidence=round(conf, 2),
                    indicators_found=gevonden_patronen,
                    description=defn.description,
                    polder_principe=defn.polder_principe,
                    polder_handreiking=handreiking,
                    verboden_toon=defn.verboden_toon,
                ))

        return matches

    def genereer_diagnose_rapport(
        self,
        matches: List[ConditionMatch],
        document_naam: str = "Inkomend stuk"
    ) -> str:
        """Genereert een helder, intern diagnoserapport voor De Tafel conform Protocol FH-01."""
        if not matches:
            return (
                f"### Interne Conditie-Diagnose: `{document_naam}`\n"
                f"- **Status:** 🟢 Geen structurele institutional delay of deflectie gedetecteerd.\n"
                f"- **Advies:** Reguliere inhoudelijke beantwoording volstaat."
            )

        md = [
            f"### Interne Conditie-Diagnose: `{document_naam}`",
            f"- **Geconstateerde patronen:** {len(matches)} structurele condities herkend",
            f"- **Doctrine-garantie:** *Interne diagnose uitsluitend voor dossier en De Tafel. Nooit als verwijt naar buiten.*",
            "",
            "| Conditie | Zekerheid | Aangetroffen indicatoren | Poldermodel Handreiking (Fluwelen Handschoen) |",
            "|---|---|---|---|",
        ]

        for m in matches:
            ind_str = "<br>• ".join(m.indicators_found[:3])
            md.append(
                f"| **{m.code}**<br>*{m.name_nl}* | `{int(m.confidence*100)}%` | "
                f"• {ind_str} | {m.polder_principe} |"
            )

        md.append("\n#### Voorgestelde Fluwelen Handschoen Formuleringen (SBARIII / FH-01):\n")
        for m in matches:
            md.append(f"**Bij {m.code}:**")
            md.append(f"> \"{m.polder_handreiking}\"\n")
            md.append(f"*Vermijd strijdbare toon zoals:* `{', '.join(m.verboden_toon[:2])}`\n")

        return "\n".join(md)


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

    if len(sys.argv) < 2:
        print("Gebruik: python institutional_conditions.py <bestand.md|tekst> [--json]")
        sys.exit(1)

    invoer = sys.argv[1]
    is_json = "--json" in sys.argv

    p = Path(invoer)
    if p.is_file():
        tekst = p.read_text(encoding="utf-8", errors="replace")
        naam = p.name
    else:
        tekst = invoer
        naam = "Tekst-invoer"

    analyzer = InstitutionalConditionsAnalyzer()
    matches = analyzer.scan_tekst(tekst)

    if is_json:
        print(json.dumps([m.to_dict() for m in matches], indent=2, ensure_ascii=False))
    else:
        print(analyzer.genereer_diagnose_rapport(matches, document_naam=naam))


if __name__ == "__main__":
    main()
