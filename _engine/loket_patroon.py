#!/usr/bin/env python3
"""Loketpatronen die een publiek anker hebben gehaald.

Ankers: Nationale ombudsman 2023/144 en 2023/041, de Engelse ombudsman
(2015 en 2016) en een Lagerhuiscommissie (2018). Geen medisch dossier,
geen schraper, geen verbeningscijfer.

Een patroon telt alleen met een zin en een bron. Een patroon dat op dit anker
niet is geijkt, kan niet afgaan. De zet volgt alleen op een patroon dat is
getoond. Een lege lezing is geen gezond loket. Zij is alleen leeg.
"""

from __future__ import annotations

from dataclasses import dataclass


class NietGeijkt(ValueError):
    """Dit patroon heeft op het anker geen getuige, of het heeft nog geen naam."""


class ZonderGetuige(ValueError):
    """Een patroon zonder zin of zonder bron is een ingetypt oordeel."""


# De zet is de communicatie die uit het patroon volgt, in de taal van het rapport.
ZET = {
    "vinkje": (
        "Vraag de daad terug die het vinkje heeft vervangen. "
        "Een raad die alleen achteraf tekent, wordt vroeg betrokken. "
        "Een klacht zonder ontvangst krijgt een antwoord. "
        "Blijft de uitvoering uitbesteed, dan blijft één loket bereikbaar."
    ),
    "twee_bakken": (
        "Noem de twee bakken die het loket wel aanbiedt. "
        "Vraag wat er gebeurt als de mens in geen van beide past, "
        "en laat dat antwoord op schrift zetten. "
        "Een standaardpakket dat niet aansluit, is geen einde."
    ),
    "stilte": (
        "Vraag een vaste contactpersoon en een ritme. "
        "Een database die leeft terwijl het gesprek jaren stil is, "
        "is geen contact."
    ),
    "prijs_voor_de_burger": (
        "Zet de klacht op een plek die de uitkering of de lopende "
        "ondersteuning niet kan korten. Vraag op schrift dat een klacht "
        "de lopende ondersteuning niet raakt. Een vrijwilligersvergoeding "
        "hoort niet te worden opgeteld tot zij meer kost dan zij oplevert."
    ),
    "verslag_wijkt_af": (
        "Vraag het verslag voordat je tekent. Zet de onjuistheden op schrift. "
        "Teken niet voor akkoord met een verslag dat niet klopt, alleen om "
        "een besluit te krijgen. De gemeente hoort die onjuistheden eenvoudig "
        "te kunnen schrappen."
    ),
    "sensor_uit": (
        "Vraag welk onderzoek bij de klacht hoort, en of dat is gedaan. "
        "Een verslag dat een onderzoek noemt dat niet heeft plaatsgevonden, "
        "wordt verbeterd voordat er een besluit op rust."
    ),
}

# Op 2023/144 bekeken en niet geijkt. Zij mogen niet onder een andere naam terug.
NIET_GEIJKT = frozenset(
    {
        "oorzaak_bij_de_persoon",
        "prijs_voor_de_ambtenaar",
    }
)

BRON_2023_144 = (
    "Nationale ombudsman, rapport 2023/144, "
    "Inspraak mag geen vinkje zijn, 3 oktober 2023"
)
BRON_2023_041 = (
    "Nationale ombudsman, rapport 2023/041, "
    "Burger in zicht!, 13 april 2023"
)
BRON_PHSO_2016 = (
    "Parliamentary and Health Service Ombudsman, "
    "A report of investigations into unsafe discharge from hospital, "
    "11 mei 2016"
)
BRON_PHSO_2015 = (
    "Parliamentary and Health Service Ombudsman, "
    "Breaking down the barriers, 30 december 2015"
)
BRON_COMMONS_2018 = (
    "House of Commons, Work and Pensions Committee, "
    "PIP and ESA assessments: claimant experiences, 1 februari 2018"
)


@dataclass(frozen=True)
class Getuige:
    patroon: str
    zin: str
    bron: str


@dataclass(frozen=True)
class Lezing:
    getoond: tuple[Getuige, ...]
    zetten: tuple[str, ...]
    getal: None = None


def lezen(getuigen: list[Getuige] | tuple[Getuige, ...]) -> Lezing:
    """Lees alleen geijkte patronen die een zin en een bron meebrengen."""
    gezien: list[Getuige] = []
    volgorde: list[str] = []
    for getuige in getuigen:
        patroon = getuige.patroon.strip()
        zin = getuige.zin.strip()
        bron = getuige.bron.strip()
        if patroon not in ZET:
            raise NietGeijkt(patroon or "(leeg)")
        if not zin or not bron:
            raise ZonderGetuige(patroon)
        schoon = Getuige(patroon, zin, bron)
        gezien.append(schoon)
        if patroon not in volgorde:
            volgorde.append(patroon)
    # Volgorde van de zet is de volgorde van het anker, niet de volgorde van invoer.
    geordend = tuple(naam for naam in ZET if naam in volgorde)
    return Lezing(
        getoond=tuple(gezien),
        zetten=tuple(ZET[naam] for naam in geordend),
        getal=None,
    )


def anker_2023_144() -> tuple[Getuige, ...]:
    """De zinnen uit het rapport die de vier patronen dragen.

    Een ontbrekende formele keuring die de mens lucht geeft, staat hier niet bij.
    Dat is geen vinkje in de zin van dit anker.
    """
    return (
        Getuige(
            "vinkje",
            "Hun bijdrage is dan slechts een vinkje dat gezet moet worden "
            "in het proces van beleidsvorming.",
            BRON_2023_144,
        ),
        Getuige(
            "vinkje",
            "Als ik een klacht indien bij de gemeente, krijg ik geen reactie. "
            "Ook geen ontvangstbevestiging, niets.",
            BRON_2023_144,
        ),
        Getuige(
            "twee_bakken",
            "Binnen de normen wordt er meegedacht. Maar zodra het lastig wordt "
            "of je erbuiten valt, dan is er verder niets meer mogelijk.",
            BRON_2023_144,
        ),
        Getuige(
            "stilte",
            "Vanuit de gemeente is het toen zo'n vijf jaar stil geweest. "
            "Ik ben alleen nog een keer benaderd omdat de database met "
            "uitkeringsgerechtigden werd geactualiseerd.",
            BRON_2023_144,
        ),
        Getuige(
            "prijs_voor_de_burger",
            "Ze zijn bang dat hun klacht negatieve gevolgen heeft voor hun "
            "uitkering of voor de manier waarop zij worden behandeld.",
            BRON_2023_144,
        ),
        Getuige(
            "prijs_voor_de_burger",
            "De vergoedingen worden bij elkaar opgeteld waardoor je al snel "
            "boven de belastingvrijstelling uitkomt. Dan kost het meer dan "
            "het oplevert.",
            BRON_2023_144,
        ),
    )


def anker_2023_041() -> tuple[Getuige, ...]:
    """De zinnen uit het Wmo-rapport die drie patronen dragen.

    De parafrases die op de tafel stonden, staan zo niet in het rapport.
    Deze zinnen wel.
    """
    return (
        Getuige(
            "verslag_wijkt_af",
            "Ook geven burgers aan dat de gemeente het verslag van het "
            "keukentafelgesprek als dit inhoudelijk niet klopt, niet altijd aanpast.",
            BRON_2023_041,
        ),
        Getuige(
            "verslag_wijkt_af",
            "Maar toen kreeg ik het verslag en er stonden heel veel zaken in "
            "die er niet in thuishoorden.",
            BRON_2023_041,
        ),
        Getuige(
            "verslag_wijkt_af",
            "Burgers geven aan dat ze soms, ook als ze het niet eens zijn met "
            "de voorgestelde voorziening, het verslag toch maar ondertekenen "
            "omdat ze niet als ‘lastig’ ervaren willen worden.",
            BRON_2023_041,
        ),
        Getuige(
            "twee_bakken",
            "Verder geven de burgers aan dat de gemeente het gesprek vaak niet "
            "insteekt vanuit de zorgvraag, maar vanuit de standaard pakketten "
            "en de ruimte binnen de begroting.",
            BRON_2023_041,
        ),
        Getuige(
            "twee_bakken",
            "Ik heb twee keer een slecht passende rolstoel uit het "
            "standaardpakket van de gemeente gehad.",
            BRON_2023_041,
        ),
        Getuige(
            "prijs_voor_de_burger",
            "Ze zijn bang dat dit nog wel eens zou kunnen leiden tot minder "
            "ondersteuning in de toekomst.",
            BRON_2023_041,
        ),
    )


def anker_phso_ontslag() -> tuple[Getuige, ...]:
    """De Engelse ombudsman, 11 mei 2016. Negen onderzochte ontslagen.

    De buik is niet onderzocht. Het bezoek sloot op een andere naam.
    """
    return (
        Getuige(
            "sensor_uit",
            "Mrs T was very unwell and had the doctor physically examined "
            "her stomach, it's highly unlikely that she would have been "
            "sent home.",
            BRON_PHSO_2016,
        ),
        Getuige(
            "sensor_uit",
            "If she had been examined, it would have been clear to Mrs T's "
            "family that she was very ill and that there was a risk of "
            "her dying.",
            BRON_PHSO_2016,
        ),
    )


def anker_phso_drempel() -> tuple[Getuige, ...]:
    """Dezelfde ombudsman, 30 december 2015. Ouderen en klagen.

    Het percentage is van hen. Het wordt hier niet een score.
    """
    return (
        Getuige(
            "prijs_voor_de_burger",
            "Among those aged 65 and over who had experienced a problem "
            "with the NHS or another public service but not complained, "
            "over half (56%) indicated that they would be worried about "
            "the impact that complaining about an organisation might have "
            "on the way they were treated in the future.",
            BRON_PHSO_2015,
        ),
        Getuige(
            "prijs_voor_de_burger",
            "Mrs A was reluctant for the investigation to cover social "
            "services and initially asked us not to investigate its actions "
            "unless ‘absolutely necessary’, as her father was still under "
            "its care.",
            BRON_PHSO_2015,
        ),
    )


def anker_commons_2018() -> tuple[Getuige, ...]:
    """Lagerhuis, Work and Pensions Committee, 1 februari 2018.

    PIP en ESA. Het verslag wijkt af, het vinkje vervangt de daad,
    en een heroverweging blijft achterwege uit vrees voor verlies.
    """
    return (
        Getuige(
            "verslag_wijkt_af",
            "Apparently I walk my dog daily, which was baffling because "
            "I can barely walk and I do not have a dog!",
            BRON_COMMONS_2018,
        ),
        Getuige(
            "verslag_wijkt_af",
            "Several claimants told us that the results of physical "
            "examinations which had not taken place were included in "
            "their assessment report.",
            BRON_COMMONS_2018,
        ),
        Getuige(
            "sensor_uit",
            "In reality though my assessment was only fifteen minutes "
            "long and the assessor didn’t examine me at all.",
            BRON_COMMONS_2018,
        ),
        Getuige(
            "vinkje",
            "The health professional had said, “This woman needs to use "
            "continence pads for the majority of the time” but what she "
            "had done is ticked the box where you get no points.",
            BRON_COMMONS_2018,
        ),
        Getuige(
            "prijs_voor_de_burger",
            "I didn’t dare ask for Mandatory Reconsideration in case "
            "the PIP was taken away from me again.",
            BRON_COMMONS_2018,
        ),
    )


def als_tekst(lezing: Lezing) -> str:
    """Een lezing die een mens kan voorlezen. Geen score."""
    if not lezing.getoond:
        return "Niets getoond. Geen zet. Geen getal. Een lege lezing is geen groen loket."
    blokken = ["Getoond."]
    for getuige in lezing.getoond:
        blokken.append(f"{getuige.patroon}. “{getuige.zin}” ({getuige.bron})")
    blokken.append("Zet.")
    blokken.extend(lezing.zetten)
    blokken.append("Geen getal.")
    return "\n".join(blokken)


def main() -> None:
    print(f"Anker: {BRON_2023_144}.")
    print(als_tekst(lezen(anker_2023_144())))
    print()
    print(f"Anker: {BRON_2023_041}.")
    print(als_tekst(lezen(anker_2023_041())))
    print()
    print(f"Anker: {BRON_PHSO_2016}.")
    print(als_tekst(lezen(anker_phso_ontslag())))
    print()
    print(f"Anker: {BRON_PHSO_2015}.")
    print(als_tekst(lezen(anker_phso_drempel())))
    print()
    print(f"Anker: {BRON_COMMONS_2018}.")
    print(als_tekst(lezen(anker_commons_2018())))
    print("Niet geijkt: " + ", ".join(sorted(NIET_GEIJKT)) + ".")


if __name__ == "__main__":
    main()
