"""Eerste lus van Civic Helper. Geen venster."""

import os
import re
import sys
from pathlib import Path

ENGINE = Path(__file__).resolve().parent.parent
WERK = ENGINE / "werk"
TAKKEN = ("zorg", "gemeente", "geld", "adressen", "verleden")
BLADEN = (
    "01 Zorg en gezondheid",
    "02 Huisvesting en wonen",
    "03 Financiën",
    "04 Bestuursrecht",
    "05 Handhaving en politie",
    "06 BRP en adres",
    "07 Jeugdzorg en gezin",
    "08 Werk en UWV",
    "09 Onderwijs",
    "10 Banken en BKR",
    "11 Verblijf",
    "12 Vergunningen",
)
KOMPAS_STUB = """# Kompas

Wie: de persoon aan dit venster.
Open: nog geen loket.
"""


def werkmap():
    WERK.mkdir(exist_ok=True)
    (WERK / "binnen").mkdir(exist_ok=True)
    (WERK / "takken").mkdir(exist_ok=True)
    (WERK / "archief").mkdir(exist_ok=True)
    kompas = WERK / "00_Kompas.md"
    if not kompas.exists():
        kompas.write_text(KOMPAS_STUB, encoding="utf-8")
    tijdlijn = WERK / "tijdlijn.md"
    if not tijdlijn.exists():
        tijdlijn.write_text("# Tijdlijn\n", encoding="utf-8")
    return WERK


def lees_kompas():
    return (werkmap() / "00_Kompas.md").read_text(encoding="utf-8")


def tak_voor(zin):
    tekst = (zin or "").lower()
    if any(w in tekst for w in ("arts", "ziekenhuis", "dossier", "lab", "zorg")):
        return "zorg"
    if any(w in tekst for w in ("gemeente", "wmo", "wijk", "loket")):
        return "gemeente"
    if any(w in tekst for w in ("incasso", "cak", "huur", "bank", "geld", "schuld")):
        return "geld"
    if any(w in tekst for w in ("adres", "verhuis")):
        return "adressen"
    if any(w in tekst for w in ("vroeger", "jaar", "toen")):
        return "verleden"
    return ""


def lees_tak(naam):
    if naam not in TAKKEN:
        return ""
    pad = werkmap() / "takken" / f"{naam}.md"
    if not pad.exists():
        return ""
    return pad.read_text(encoding="utf-8")[:4000]


def _agy():
    import shutil
    gevonden = shutil.which("agy")
    if gevonden:
        return gevonden
    for vast in (
        Path.home() / "AppData/Local/agy/bin/agy.exe",
        Path.home() / ".local/bin/agy",
    ):
        if vast.exists():
            return str(vast)
    return ""


def antwoord(zin):
    """De zin gaat naar agy. agy heeft de handen. Een kale modelbus niet."""
    import subprocess
    programma = _agy()
    if not programma:
        return "agy staat niet op deze computer. Start ontkiem.py. Het venster kan zonder agy niets bijbouwen."
    tak = tak_voor(zin)
    prompt = (
        "Je bent de motor achter het venster Civic Helper. "
        "Lees werk/00_Kompas.md en alleen de tak die bij deze zin hoort. "
        "Antwoord in gewone Nederlandse zinnen. Eén volgende zet. "
        "Verstuur geen post. Een brief aan een lokaal Nederlands loket blijft kort, zonder wetsartikel.\n\n"
        f"Tak: {tak or 'geen'}\nDe persoon zegt:\n{zin}"
    )
    klaar = subprocess.run(
        [programma, "--print", prompt, "--add-dir", str(ENGINE.parent), "--dangerously-skip-permissions"],
        cwd=str(ENGINE.parent),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    tekst = (klaar.stdout or "").strip()
    if tekst:
        return tekst
    fout = (klaar.stderr or "").strip()
    return fout or "agy gaf geen antwoord."


def concept_uit(zin):
    """Korte brief. De artikelen blijven uit de tekst."""
    return (
        "Geachte heer, mevrouw,\n\n"
        f"{zin.strip()}\n\n"
        "Ik ontvang uw antwoord graag uitsluitend schriftelijk per e-mail.\n\n"
        "Met vriendelijke groet\n"
    )


def _strip_klinisch(tekst):
    engine = ENGINE / "_engine"
    if str(engine) not in sys.path:
        sys.path.insert(0, str(engine))
    from veto_gate import CLINICAL_KEYWORDS, VetoGate

    poort = VetoGate(root_dir=ENGINE).check_draft(
        tekst,
        slot_metadata={"name": "lokaal loket", "ingest_capacity": ["productcodes", "termijnen", "privacy"]},
    )
    klinisch = any(
        item.get("rule") == "VETO_1_PAYLOAD_SLOT_INGEST" and not item.get("passed", True)
        for item in poort.get("results", [])
    )
    if not klinisch:
        return tekst, poort
    stukken = re.split(r"(?<=[.!?])\s+", tekst)
    gehouden = [s for s in stukken if not any(re.search(pat, s, re.IGNORECASE) for pat in CLINICAL_KEYWORDS)]
    gehouden.append("Gelet op mijn medische belastbaarheid verzoek ik alle stukken uitsluitend digitaal aan te leveren.")
    return " ".join(gehouden), poort


def toets_brief(tekst):
    """Veto, dan de audit, dan nog eens de poort. De brief wordt niet verstuurd."""
    gestript, _poort_voor = _strip_klinisch(tekst)
    pad = werkmap() / "concept.md"
    pad.write_text(gestript, encoding="utf-8")
    engine = ENGINE / "_engine"
    if str(engine) not in sys.path:
        sys.path.insert(0, str(engine))
    from audit_engine import run_constructive_audit
    from two_gate_dispatcher import TwoGateDispatcher

    run_constructive_audit(pad, is_critical=False)
    verfijnd = ENGINE / "Outgoing_Drafts" / "REFINED_concept.md"
    brief = verfijnd.read_text(encoding="utf-8") if verfijnd.exists() else gestript
    poort = TwoGateDispatcher(root_dir=ENGINE).dispatch(
        brief,
        slot_metadata={"name": "lokaal loket", "ingest_capacity": ["productcodes", "termijnen", "privacy"]},
    )
    return brief, poort


def sein(brief, aan, onderwerp):
    """Het sein opent het mailprogramma. Er gaat hier niets zelf de deur uit."""
    eml = werkmap() / "brief.eml"
    inhoud = (
        f"To: {aan}\r\n"
        f"Subject: {onderwerp}\r\n"
        "MIME-Version: 1.0\r\n"
        "Content-Type: text/plain; charset=utf-8\r\n"
        "\r\n"
        f"{brief}\r\n"
    )
    eml.write_text(inhoud, encoding="utf-8")
    if sys.platform == "win32":
        os.startfile(eml)  # noqa: S606 — het sein opent het eigen mailprogramma
    else:
        import subprocess
        subprocess.Popen(["xdg-open", str(eml)])
    return str(eml)


def nieuwe_bestanden(gezien):
    vers = []
    for pad in (werkmap() / "binnen").iterdir():
        if pad.is_file() and pad.name not in gezien:
            vers.append(pad)
    return vers


def zet_op_tijdlijn(pad):
    regel = f"\n- {pad.name} binnengekomen.\n"
    if pad.suffix.lower() in {".txt", ".md", ".eml"}:
        stuk = pad.read_text(encoding="utf-8", errors="replace")[:500].replace("\n", " ")
        regel = f"\n- {pad.name}: {stuk}\n"
    with (werkmap() / "tijdlijn.md").open("a", encoding="utf-8") as bestand:
        bestand.write(regel)
    return regel.strip()


def lees_tijdlijn():
    return (werkmap() / "tijdlijn.md").read_text(encoding="utf-8")[-2000:]


def stand_omgeving():
    agy = "agy is aanwezig." if _agy() else "agy ontbreekt nog. De route is ontkiem.py."
    return (
        f"{agy}\n"
        f"Werkmap: {werkmap()}\n"
        "De post wordt gelezen als de brug op deze computer er is.\n"
        "Groei: een mailprogramma koppelen, of een extra modelhuis, vanuit hier. Niet als drempel om te starten."
    )


def stand_dossiers():
    takken = [naam for naam in TAKKEN if (werkmap() / "takken" / f"{naam}.md").exists()]
    binnen = [pad.name for pad in (werkmap() / "binnen").iterdir() if pad.is_file()]
    return (
        lees_kompas().strip()
        + "\n\nTakken die er al zijn: "
        + (", ".join(takken) if takken else "nog geen.")
        + "\nBinnengekomen bestanden: "
        + (", ".join(binnen) if binnen else "nog geen.")
        + "\n\nGroei: een nieuw loket krijgt een tak. Een afgerond spoor gaat naar het archief."
    )


def prompts():
    import json
    pad = Path(__file__).resolve().parent / "prompt_db.json"
    return json.loads(pad.read_text(encoding="utf-8"))


def prompts_voor(route):
    return [item for item in prompts() if item.get("route") == route]


def stand_bladen():
    aanwezig = []
    for naam in BLADEN:
        if (werkmap() / "bladen" / f"{naam}.md").exists():
            aanwezig.append(naam)
    return aanwezig


def stand_landschap():
    wortel = werkmap() / "landschap"
    cellen = ("Organisatie", "Politiek discours", "Medialandschap", "Keten en contracten", "Intern model")
    if not wortel.exists():
        return [(naam, "blad leeg") for naam in cellen]
    regels = []
    for naam in cellen:
        pad = wortel / f"{naam}.md"
        regels.append((naam, "staat" if pad.exists() and pad.stat().st_size > 0 else "blad leeg"))
    return regels


def stand_gereedschap():
    aanwezig = []
    kandidaten = [
        ENGINE / "_engine" / "glue_check.py",
        ENGINE / "_engine" / "statutory_clock.py",
        ENGINE / "_engine" / "timeline_weaver.py",
        ENGINE.parent / "ct_runtime" / "kernel.py",
        ENGINE.parent / "Shared_Tools" / "model_bus.py",
        ENGINE.parent / "Shared_Tools" / "pii_mask.py",
    ]
    for pad in kandidaten:
        if pad.exists():
            aanwezig.append(pad.name)
    return (
        "Aanwezig: " + ", ".join(aanwezig) + ".\n"
        "Dit is het zaad, niet een menu om alles tegelijk aan te zetten.\n"
        "Groei: als een obstakel nieuw is, bouwt agy het hulpmiddel in de werkmap."
    )


def breuk_zin(zin):
    gevonden = re.search(r"IF-[A-Z0-9-]+", zin or "")
    if not gevonden:
        return ""
    engine = ENGINE / "_engine"
    if str(engine) not in sys.path:
        sys.path.insert(0, str(engine))
    import json
    from glue_check import GlueChecker

    data = json.loads((ENGINE / "interfaces.json").read_text(encoding="utf-8"))
    gekozen = [item for item in data if item.get("id") == gevonden.group(0)]
    if not gekozen:
        return ""
    oordeel = GlueChecker(root_dir=ENGINE).evaluate_interface(gekozen[0])
    if oordeel.verdict == "GLUING_FAILURE":
        return f"De overdracht {oordeel.interface_id} sluit niet. Wat de ontvanger niet heeft ingeboekt, blijft liggen."
    return f"De overdracht {oordeel.interface_id} sluit."
