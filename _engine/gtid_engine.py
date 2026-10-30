#!/usr/bin/env python3
"""
CIVIC HELPER — G-TID veldkaart, eerste pass.

Dit is een uitlezing (Kamer 3). Geen veldvergelijking en geen nieuwe grondslag.

De stapel loopt één kant op:
  constraint-topologie → GDI-tetrade → coderingssleutel → drie kamers.
Een groene bijnaam hier betekent niet dat de machinekamer heel is.

G-TID (concept-draft) leent zeven namen als representatie van een instituut:
  w, Psi_res, Delta_lambda, theta, T_H, GU_ext, GU_int.
Dat is een taal voor een casusblad. Het is geen meting uit een brief.
De draft noemt materiële legitimiteit een integraal over een echt domein,
en het kader een diagnose. Geen blauwdruk.

E-ARM voegt hier één gezicht toe. De ruimte van de uitvoerder heeft een prijs
(berisping, productcode, kwaliteitscontrole). De hack verlaagt die prijs
met een zin die de behandelaar zelf tekent.

Agency stemt de koppeling tussen de formele orde en de praktijk.
De viabiliteitsruimte is iets anders. Deze module meet geen van beide.
Een brief is een chart. Het woord "postbus" is geen schaalsprong.
"""

import sys
from pathlib import Path

ENGINE_DIR = Path(__file__).resolve().parent
ROOT_DIR = ENGINE_DIR.parent

UNKNOWN = "niet afgelezen"

# Operatoren van deze kaart. Geen tetrade-namen, en geen verzendpoort.
VRAAG = "VRAAG"
GIFT = "GIFT"
WACHT = "WACHT"
VOLGENDE_SLUITING = "VOLGENDE_SLUITING"


class InstitutionalField:
    """Een instituut als veld, afgelezen voor zover iemand dat echt heeft gezien.

    Getallen die de aanroeper meegeeft blijven opgegeven. Ze worden niet
    omgerekend tot resonantie of legitimiteit.
    """

    def __init__(
        self,
        entity_name="onbekend",
        *,
        front_open=True,
        conversation_live=False,
        closure="open",
        coupling=UNKNOWN,
        deviation_cost=UNKNOWN,
        gu_ext=None,
        gu_int=None,
        fact="",
        w_official=None,
        w_citizen=None,
        hints=None,
        witnessed=False,
    ):
        self.entity_name = entity_name or "onbekend"
        self.front_open = bool(front_open)
        self.conversation_live = bool(conversation_live)
        self.closure = closure if closure in ("open", "zelfde", "volgende") else "open"
        self.coupling = coupling or UNKNOWN
        self.deviation_cost = deviation_cost or UNKNOWN
        self.gu_ext = list(gu_ext) if gu_ext else []
        self.gu_int = list(gu_int) if gu_int else []
        self.fact = (fact or "").strip()
        self.w_official = w_official
        self.w_citizen = w_citizen
        self.hints = list(hints or [])
        self.witnessed = bool(witnessed)

    @property
    def operator(self) -> str:
        """De volgende zet op deze kaart.

        Een lopend gesprek wacht. Een open voorkant krijgt een vraag of een
        cadeau-zin. De volgende balie komt pas als deze sluiting de behoefte
        niet draagt én de voorkant dicht is. Een brief alleen zet geen van
        die twee.
        """
        if self.conversation_live:
            return WACHT
        if self.front_open:
            return GIFT if self.fact else VRAAG
        if self.closure == "volgende":
            return VOLGENDE_SLUITING
        return GIFT if self.fact else VRAAG

    def coding_key(self) -> dict:
        """⟨R | σ | τ⟩ voor de naad. σ is de zichtbaarheid van deze chart."""
        return {
            "R": "de daad van de behandelaar ontmoet de constraint van de burger",
            "sigma": "een brief of een gok is een chart, geen veld",
            "tau": {
                "G": "de regeltekst die de daad al toelaat",
                "D": "de klok en de prijs van afwijken",
                "I": "of het zaaksysteem de behoefte kan zeggen",
            },
        }

    def card(self) -> dict:
        stated = "gezien" if self.witnessed else "opgegeven" if (
            self.w_official is not None or self.w_citizen is not None
        ) else UNKNOWN
        return {
            "kamer": 3,
            "entity": self.entity_name,
            "coupling": self.coupling,
            "gu_ext": self.gu_ext,
            "gu_int": self.gu_int,
            "closure": self.closure,
            "front_open": self.front_open,
            "conversation_live": self.conversation_live,
            "deviation_cost": self.deviation_cost,
            "w_official": self.w_official,
            "w_citizen": self.w_citizen,
            "w_status": stated,
            "operator": self.operator,
            "legitimacy": None,
            "hints": self.hints,
            "coding_key": self.coding_key(),
            "regime_nickname": None,
        }

    def gift_note(self, subject=""):
        """Interne zin voor de behandelaar. Geen beschikking, geen artikelen."""
        onderwerp = subject.strip()
        kosten = self.deviation_cost
        if kosten == UNKNOWN:
            kosten_zin = "Wat een regel buiten de standaardrekening haar kost, staat in dit stuk niet."
        else:
            kosten_zin = f"Een regel buiten de standaard kost haar nu dit: {kosten}."

        if self.fact:
            behoefte = self.fact
        else:
            behoefte = "De post is hier nog niet ingevuld."

        lines = [
            f"Memoriaal voor de behandelaar bij {self.entity_name}.",
            "Dit is geen brief naar de burger en geen beschikking.",
            "",
        ]
        if onderwerp:
            lines.append(f"Onderwerp: {onderwerp}.")
            lines.append("")
        if self.conversation_live:
            lines.append("Het journaal van dit gesprek loopt nog. Deze regel blijft in het klad.")
            lines.append("")
        lines.extend([
            f"In het journaal staat dit: {behoefte}",
            "",
            "Haar grootboek kan op groen staan terwijl de tegenboeking ontbreekt.",
            "Wat haar ruimte geeft, is een memoriaalregel die zij zelf tekent en die haar boek al kent.",
            "Daarmee kan zij de open post afletteren.",
            "Zij tekent de kwijting zelf. De verantwoordelijkheid blijft bij haar.",
            "",
            kosten_zin,
            "",
            "Of de twee boeken elkaar raken, is "
            + (self.coupling if self.coupling != UNKNOWN else "hier niet afgelezen")
            + ".",
        ])
        if self.operator == VOLGENDE_SLUITING:
            lines.extend([
                "",
                "Deze rekening kan de post niet dragen.",
                "De volgende boeking hoort in een ander boek, niet als een hardere regel in hetzelfde.",
            ])
        else:
            lines.extend([
                "",
                "Zolang dit journaal open is, hoort hier geen artikel en geen dreigement.",
            ])
        return "\n".join(lines)

    def generate_ambtelijke_besluitrechtvaardiging(self, subject="", grounds=None, risks_averted=None):
        """Oude naam. Geeft de cadeau-zin terug.

        grounds en risks_averted worden genegeerd. Een plakklare beschikking
        hoort niet in deze pass. De achterzak blijft een aparte aanroep.
        """
        del grounds, risks_averted
        return self.gift_note(subject=subject or "")

    def back_pocket(self) -> str:
        """De juridische achterzak. Alleen op verzoek, nooit in de kaart."""
        return "\n".join([
            "Achterzak, dicht.",
            "Artikelnummers, een ingebrekestelling en een concept-beschikking",
            "blijven hier tot de voorkant dicht is en iemand ze vraagt.",
        ])

    def diagnose_summary(self) -> dict:
        """Platte kaart voor bestaande aanroepers. Geen Psi en geen L."""
        card = self.card()
        return {
            "entity": card["entity"],
            "regime": None,
            "operator": card["operator"],
            "coupling": card["coupling"],
            "front_open": card["front_open"],
            "closure": card["closure"],
            "deviation_cost": card["deviation_cost"],
            "w_citizen": card["w_citizen"],
            "w_official": card["w_official"],
            "psi_res": None,
            "material_legitimacy": None,
            "hints": card["hints"],
            "rationale": self._rationale(),
        }

    def _rationale(self) -> str:
        op = self.operator
        if op == WACHT:
            return "Het journaal van dit gesprek loopt nog. Er gaat geen afsluiting uit."
        if op == VOLGENDE_SLUITING:
            return "Deze rekening draagt de post niet, en het journaal is gesloten."
        if op == GIFT:
            return "Er ligt een memoriaalregel klaar die de behandelaar zelf kan tekenen."
        return "Het journaal is nog open. Eerst vragen. De proefbalans is uit dit stuk niet opgemaakt."

    def markdown(self) -> str:
        card = self.card()
        hint_line = "; ".join(card["hints"]) if card["hints"] else "geen"
        sluiting = {"open": "nog niet gezien", "zelfde": "hetzelfde boek", "volgende": "een ander boek"}
        zet = {
            VRAAG: "eerst vragen",
            GIFT: "een memoriaalregel aanreiken",
            WACHT: "het journaal loopt nog",
            VOLGENDE_SLUITING: "boeken in een ander boek",
        }
        return "\n".join([
            "## Grootboekkaart",
            "",
            "Een brief is een stuk uit het journaal. Zij is de proefbalans niet.",
            "",
            f"- Boek: {card['entity']}",
            f"- Tegenboeking: {card['coupling']}",
            f"- Journaal nog open: {'ja' if card['front_open'] else 'nee'}",
            f"- Gesprek loopt: {'ja' if card['conversation_live'] else 'nee'}",
            f"- Waar de post hoort: {sluiting.get(card['closure'], card['closure'])}",
            f"- Prijs van een regel buiten de standaard: {card['deviation_cost']}",
            f"- Volgende zet: {zet.get(card['operator'], card['operator'])}",
            "- Proefbalans voor de mens: nog niet opgemaakt",
            f"- Hint uit het stuk: {hint_line}",
            "",
            self.gift_note(),
            "",
        ])


def _entity_hint(text_lower: str) -> str:
    """Een naam in de brief is een etiket. Geen diagnose."""
    for needle, name in (
        ("westerwolde", "Gemeente Westerwolde"),
        ("oldambt", "Gemeente Oldambt"),
        ("menzis", "Menzis Zorgverzekeraar"),
        ("woningcorporatie", "Woningcorporatie"),
        ("uwv", "UWV"),
    ):
        if needle in text_lower:
            return name
    loketten_pad = ROOT_DIR / "werk" / "loketten.json"
    if loketten_pad.is_file():
        try:
            import json
            for label, keys in json.loads(loketten_pad.read_text(encoding="utf-8")).get("islands", []):
                if any(k in text_lower for k in keys):
                    return label
        except Exception:
            pass
    return "onbekend"


def inspect_incoming_letter_for_gtid(letter_text: str) -> InstitutionalField:
    """Lees een brief als chart.

    Woorden mogen een hint geven. Ze zetten de voorkant niet dicht, ze kiezen
    geen volgende balie, en ze vullen geen legitimiteit in.
    """
    text_lower = (letter_text or "").lower()
    hints = []
    if any(k in text_lower for k in ("geen uitzondering", "strikte voorwaarde", "niet mogelijk")):
        hints.append("de tekst verdraagt weinig variatie")
    if any(k in text_lower for k in ("klantenservice", "callcenter", "postbus")):
        hints.append("de afzender lijkt een loket")
    if any(k in text_lower for k in ("productcode", "het systeem laat niet toe", "standaardprocedure")):
        hints.append("het zaaksysteem lijkt de daad al dicht te zetten")
    if any(k in text_lower for k in ("in overleg", "maatwerk", "ik kan toezeggen")):
        hints.append("er is een menselijke stem in de tekst")

    return InstitutionalField(
        entity_name=_entity_hint(text_lower),
        front_open=True,
        conversation_live=False,
        closure="open",
        coupling=UNKNOWN,
        deviation_cost=UNKNOWN,
        hints=hints,
        witnessed=False,
    )


def main():
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    print("G-TID veldkaart — eerste pass")
    print("Kamer 3. Een brief meet het veld niet.")
    print()

    incoming_dir = ROOT_DIR / "Incoming_Letters"
    sample = ""
    if incoming_dir.is_dir():
        files = sorted(incoming_dir.glob("*.eml")) + sorted(incoming_dir.glob("*.txt")) + sorted(incoming_dir.glob("*.md"))
        if files:
            latest = files[-1]
            print(f"Tekst gezien als chart: {latest.name}")
            sample = latest.read_text(encoding="utf-8", errors="ignore")

    field = inspect_incoming_letter_for_gtid(sample) if sample else InstitutionalField(
        entity_name="onbekend",
        hints=["geen brief aangeboden"],
    )
    print(field.markdown())
    print("Er is niets weggeschreven. De achterzak blijft dicht.")


if __name__ == "__main__":
    main()
