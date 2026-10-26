"""Vier startvoorwaarden, daarna vier kiem-prompts aan agy.

De persoon typt geen PATH en geen terminal. Start dit bestand.
Het vraagt nooit om een API-sleutel op het scherm en schrijft geen sleutels in bestanden.
Met `--check` of `--test` voert het een snelle, netwerkvrije verificatie van de startvoorwaarden uit.
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path

ZAAD = Path(__file__).resolve().parent
HUB = ZAAD.parent
WERK = ZAAD / "werk"
PROFIEL = WERK / "profiel.txt"

KIEMEN = [
    (
        "1",
        "Lees AGENTS.md en CivicHelper/APPLICATIE_SPECIFICATIE.md. "
        "Verken of deze computer Windows of Linux is, welk mailprogramma of welke postbrug er is, "
        "en welke OCR- en spraakmiddelen beschikbaar zijn. "
        "Richt buiten git CivicHelper/werk in met 00_Kompas.md, tijdlijn.md en de takken.",
    ),
    (
        "2",
        "Controleer via Shared_Tools/model_bus.py en pii_mask.py welke modelhuizen bereikbaar zijn. "
        "Verifieer dat burgerservicenummer, bankrekening en huisadres lokaal worden gemaskeerd. "
        "Test dat de briefketen veto_gate.py, dan audit_engine.py, dan TwoGateDispatcher sluit. "
        "Verstuur geen post.",
    ),
    (
        "3",
        "Het PyQt-venster Civic Helper hoort de voorkant van jouzelf te zijn, agy in deze werkmap. "
        "Elke zin uit het venster komt bij jou binnen. "
        "Zet de starter op het bureaublad. Bouw geen tweede chatbot naast jezelf.",
    ),
    (
        "4",
        "Open het venster op werk/00_Kompas.md. "
        "Vraag in gewone taal welk briefje, welk loket of welk probleem vandaag als eerste op tafel ligt.",
    ),
]


def agy_pad():
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


def registreer(programma):
    if not programma:
        return "agy ontbreekt. Het script verzint geen installatie-URL."
    subprocess.run([programma, "install"], check=False)
    return "agy is geregistreerd."


def schrijf_profiel(naam, plaats, email):
    WERK.mkdir(parents=True, exist_ok=True)
    naam_s = naam.strip() or "De persoon aan dit venster"
    plaats_s = plaats.strip() or "Onbekend"
    email_s = email.strip()
    PROFIEL.write_text(
        f"Naam: {naam_s}\nWoonplaats: {plaats_s}\nE-mail: {email_s}\n",
        encoding="utf-8",
    )
    kompas = WERK / "00_Kompas.md"
    if kompas.exists():
        huidig = kompas.read_text(encoding="utf-8").strip()
        if "Wie: de persoon aan dit venster." in huidig:
            kompas.write_text(
                f"# Kompas\n\nWie: {naam_s} ({plaats_s}).\nE-mail: {email_s or 'nog niet ingevuld'}.\nOpen: nog geen loket.\n",
                encoding="utf-8",
            )


def werk_klaar():
    if str(ZAAD) not in sys.path:
        sys.path.insert(0, str(ZAAD))
    from hulp.lus import werkmap
    werkmap()
    keten_dir = ZAAD / "Ketengrootboek"
    keten_dir.mkdir(exist_ok=True)
    grootboek = keten_dir / "grootboek.json"
    if not grootboek.exists():
        grootboek.write_text("[]\n", encoding="utf-8")


def controleer_startvoorwaarden():
    """Verifieert de vier startvoorwaarden lokaal en zonder netwerkverkeer."""
    werk_klaar()
    from hulp.lus import test_briefketen_offline

    # 1. agy & werkmap
    prog = agy_pad()
    werk_ok = (WERK / "00_Kompas.md").exists() and (WERK / "tijdlijn.md").exists()

    # 2. PII-masker (BSN, IBAN, huisadres)
    for kandidaat in (HUB / "Shared_Tools", ZAAD / "gui"):
        if kandidaat.exists() and str(kandidaat) not in sys.path:
            sys.path.insert(0, str(kandidaat))
    import model_bus
    import pii_mask

    proef_zin = "BSN: 123456789, rekening NL91ABNA0417164300, adres Voorbeeldstraat 12, 1234 AB Voorbeeldstad."
    gemaskeerd, kluis = pii_mask.mask(proef_zin)
    hersteld = pii_mask.restore(gemaskeerd, kluis)
    masker_ok = (
        "123456789" not in gemaskeerd
        and "NL91ABNA0417164300" not in gemaskeerd
        and "Voorbeeldstraat 12" not in gemaskeerd
        and hersteld == proef_zin
    )

    # 3. Briefketen (Veto -> Audit -> TwoGateDispatcher) zonder netwerk
    brief_test = test_briefketen_offline()

    # 4. Modelbus-overzicht (zonder sleutels te tonen)
    huizen = model_bus.available()

    rapport = {
        "1_agy_aanwezig": bool(prog),
        "1_werkmap_gereed": werk_ok,
        "2_pii_masker_sluitend": masker_ok,
        "2_modelhuizen_in_omgeving": [k for k, v in huizen.items() if v],
        "3_briefketen_offline_geslaagd": brief_test["passed"],
        "3_poort_reden": brief_test["reason"],
        "4_venster_gereed": (ZAAD / "hulp" / "venster.py").exists(),
    }
    rapport["alle_voorwaarden_ok"] = (
        werk_ok and masker_ok and brief_test["passed"] and rapport["4_venster_gereed"]
    )
    return rapport


def geef_kiem(programma, tekst):
    subprocess.run(
        [programma, "--print", tekst, "--add-dir", str(HUB), "--dangerously-skip-permissions"],
        cwd=str(HUB),
        check=False,
    )


def scherm():
    from PyQt6.QtWidgets import QApplication, QFormLayout, QLineEdit, QPushButton, QWidget

    app = QApplication(sys.argv)
    venster = QWidget()
    venster.setWindowTitle("Civic Helper ontkiemt")
    form = QFormLayout(venster)
    naam = QLineEdit()
    plaats = QLineEdit()
    email = QLineEdit()
    email.setPlaceholderText("Eén gratis Gmail-adres")
    form.addRow("Naam", naam)
    form.addRow("Woonplaats", plaats)
    form.addRow("Gmail", email)
    knop = QPushButton("Klaar")
    form.addRow(knop)
    gekozen = {}

    def bewaar():
        gekozen["naam"] = naam.text()
        gekozen["plaats"] = plaats.text()
        gekozen["email"] = email.text()
        venster.close()

    knop.clicked.connect(bewaar)
    venster.resize(460, 220)
    venster.show()
    app.exec()
    return gekozen


def main():
    if "--check" in sys.argv or "--test" in sys.argv:
        rapport = controleer_startvoorwaarden()
        print(json.dumps(rapport, indent=2, ensure_ascii=False))
        sys.exit(0 if rapport["alle_voorwaarden_ok"] else 1)

    programma = agy_pad()
    print(registreer(programma))
    rapport = controleer_startvoorwaarden()
    print(json.dumps(rapport, indent=2, ensure_ascii=False))

    if not PROFIEL.exists():
        ingevuld = scherm()
        if ingevuld:
            schrijf_profiel(ingevuld.get("naam", ""), ingevuld.get("plaats", ""), ingevuld.get("email", ""))
    if not programma:
        print("Zonder agy gaan de kiem-prompts niet weg.")
        return
    if "--kiem" in sys.argv:
        for _nummer, tekst in KIEMEN:
            geef_kiem(programma, tekst)


if __name__ == "__main__":
    main()
