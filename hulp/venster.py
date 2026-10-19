"""Civic Helper. Navigatiescherm met een rail en routes voor groei."""

import sys
from pathlib import Path

from PyQt6.QtCore import QThread, Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lus

BLADEN = (
    ("bureau", "Bureau"),
    ("landschap", "Landschap"),
    ("dossiers", "Dossiers"),
    ("post", "Post en klokken"),
    ("omgeving", "Omgeving"),
)


class Draad(QThread):
    klaar = pyqtSignal(str)

    def __init__(self, werk):
        super().__init__()
        self.werk = werk

    def run(self):
        try:
            self.klaar.emit(self.werk())
        except Exception as exc:
            self.klaar.emit(f"Dit liep vast: {exc}")


class Venster(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Civic Helper")
        self.resize(1040, 700)
        self.draden = []
        self.brief = ""
        self.poort_open = False
        self.blad = "bureau"
        lus.werkmap()

        kern = QWidget()
        rij = QHBoxLayout(kern)
        rij.setContentsMargins(0, 0, 0, 0)
        rij.setSpacing(0)
        rij.addWidget(self._rail())
        rij.addWidget(self._veld(), 1)
        self.setCentralWidget(kern)
        self.setStyleSheet(
            "QMainWindow, QWidget { background: #f4efe6; color: #1c1915; }"
            "QLabel { color: #1c1915; }"
            "QTextEdit, QLineEdit { background: #fffdf8; color: #1c1915; font-size: 15px; border: 1px solid #e4dccb; }"
            "QPushButton#rail { background: transparent; color: #1c1915; text-align: left; padding: 12px 16px; font-size: 15px; border: none; }"
            "QPushButton#rail:checked { background: #fffdf8; font-weight: 600; }"
            "QPushButton#kaart { background: #fffdf8; color: #1c1915; text-align: left; padding: 14px; font-size: 15px; border: 1px solid #e4dccb; }"
            "QPushButton#actie { background: #1c1915; color: #f4efe6; padding: 8px 14px; border: none; }"
        )
        self.toon("bureau")

    def _rail(self):
        rail = QWidget()
        rail.setFixedWidth(210)
        kolom = QVBoxLayout(rail)
        kolom.setContentsMargins(8, 18, 8, 18)
        merk = QLabel("Civic Helper")
        merk.setStyleSheet("font-size: 18px; padding: 8px;")
        kolom.addWidget(merk)
        self.railknoppen = {}
        for sleutel, naam in BLADEN:
            knop = QPushButton(naam)
            knop.setObjectName("rail")
            knop.setCheckable(True)
            knop.clicked.connect(lambda _c=False, s=sleutel: self.toon(s))
            self.railknoppen[sleutel] = knop
            kolom.addWidget(knop)
        kolom.addStretch()
        return rail

    def _veld(self):
        veld = QWidget()
        kolom = QVBoxLayout(veld)
        kolom.setContentsMargins(28, 22, 28, 16)
        self.kop = QLabel("Bureau")
        self.kop.setStyleSheet("font-size: 28px;")
        self.stand = QTextEdit()
        self.stand.setReadOnly(True)
        self.stand.setMaximumHeight(180)
        self.kaarten = QVBoxLayout()
        onder = QHBoxLayout()
        self.zin = QLineEdit()
        self.zin.setPlaceholderText("Of zeg in één zin wat er speelt")
        self.zin.returnPressed.connect(self.op_zin)
        stuur = QPushButton("Naar agy")
        stuur.setObjectName("actie")
        stuur.clicked.connect(self.op_zin)
        onder.addWidget(self.zin)
        onder.addWidget(stuur)
        kolom.addWidget(self.kop)
        kolom.addWidget(self.stand)
        kolom.addLayout(self.kaarten)
        kolom.addStretch()
        kolom.addLayout(onder)
        return veld

    def toon(self, sleutel):
        self.blad = sleutel
        namen = dict(BLADEN)
        self.kop.setText(namen[sleutel])
        for kandidaat, knop in self.railknoppen.items():
            knop.setChecked(kandidaat == sleutel)
        self.stand.setPlainText(self._stand(sleutel))
        self._leeg(self.kaarten)
        for item in lus.prompts_voor(sleutel):
            knop = QPushButton(item["titel"])
            knop.setObjectName("kaart")
            knop.setCursor(Qt.CursorShape.PointingHandCursor)
            opdracht = item["tekst"]
            if item["id"] == "sein":
                knop.clicked.connect(self.op_sein)
            else:
                knop.clicked.connect(lambda _c=False, body=opdracht: self._stuur(body))
            self.kaarten.addWidget(knop)

    def _leeg(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _stand(self, sleutel):
        if sleutel == "bureau":
            return lus.lees_kompas().strip() + "\n\n" + lus.lees_tijdlijn()[-600:]
        if sleutel == "landschap":
            return "\n".join(f"{naam}: {staat}" for naam, staat in lus.stand_landschap())
        if sleutel == "dossiers":
            gevuld = lus.stand_bladen()
            regels = []
            for naam in lus.BLADEN:
                regels.append(f"{naam}: {'staat' if naam in gevuld else 'blad leeg'}")
            return "\n".join(regels)
        if sleutel == "post":
            return "Een brief wacht op het sein." if self.brief else "Nog geen brief die op het sein wacht."
        return lus.stand_omgeving() + "\n\n" + lus.stand_gereedschap()

    def _start(self, werk, terug):
        draad = Draad(werk)
        draad.klaar.connect(terug)
        self.draden.append(draad)
        draad.start()

    def _stuur(self, opdracht):
        extra = self.zin.text().strip()
        self.zin.clear()
        if extra:
            opdracht = opdracht + "\n\nDe persoon voegt toe:\n" + extra
        self.stand.append("\n\nDe opdracht gaat naar agy.")
        self._start(lambda: lus.antwoord(opdracht), self.stand.append)

    def op_zin(self):
        zin = self.zin.text().strip()
        if not zin:
            return
        self._stuur(zin)

    def op_sein(self):
        zin = self.zin.text().strip() or "Ik vraag om een schriftelijk antwoord op wat er openstaat."
        self.zin.clear()
        self.stand.append("\n\nIk zet de brief klaar. Er gaat nog niets weg.")
        self._start(lambda: self._toets(zin), self._brief_terug)

    def _toets(self, zin):
        concept = lus.concept_uit(zin)
        brief, poort = lus.toets_brief(concept)
        self.brief = brief
        self.poort_open = bool(poort.get("allowed"))
        return brief + "\n\n" + poort.get("reason", "")

    def _brief_terug(self, tekst):
        self.stand.append("\n" + tekst)
        if self.poort_open:
            pad = lus.sein(self.brief, "", "Verzoek")
            self.stand.append(f"\nHet mailprogramma gaat open. {pad}")
        else:
            self.stand.append("\nDe poort houdt de brief tegen. Er is niets verstuurd.")


def main():
    app = QApplication(sys.argv)
    venster = Venster()
    venster.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
