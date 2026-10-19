"""Vier startvoorwaarden, daarna vier kiem-prompts aan agy.

De persoon typt geen PATH en geen terminal. Start dit bestand.
Het stuurt agy pas aan nadat het scherm is ingevuld.
"""

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
        "Lees AGENTS.md en Civic_Case_Engine/APPLICATIE_SPECIFICATIE.md. "
        "Verken of deze computer Windows of Linux is, welk mailprogramma of welke postbrug er is, "
        "en welke OCR- en spraakmiddelen beschikbaar zijn. "
        "Richt buiten git Civic_Case_Engine/werk in met 00_Kompas.md, tijdlijn.md en de takken.",
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
    vast = Path(r"C:\Users\Gebruiker\AppData\Local\agy\bin\agy.exe")
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
    PROFIEL.write_text(
        f"Naam: {naam.strip()}\nWoonplaats: {plaats.strip()}\nE-mail: {email.strip()}\n",
        encoding="utf-8",
    )


def werk_klaar():
    sys.path.insert(0, str(ZAAD))
    from hulp.lus import werkmap
    werkmap()


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
    programma = agy_pad()
    print(registreer(programma))
    werk_klaar()
    if not PROFIEL.exists():
        ingevuld = scherm()
        if ingevuld:
            schrijf_profiel(ingevuld.get("naam", ""), ingevuld.get("plaats", ""), ingevuld.get("email", ""))
    if not programma:
        print("Zonder agy gaan de kiem-prompts niet weg.")
        return
    for _nummer, tekst in KIEMEN:
        geef_kiem(programma, tekst)


if __name__ == "__main__":
    main()
