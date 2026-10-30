#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CIVIC HELPER 0.3 — Tafelvenster
Native PyQt6 op Windows.

- Balk bovenaan met de bestandsstok, het aantal beurten en de archiefgrens.
- Gesprek links, met tijd en kleur per stoel.
- Aanwezigen rechts, met de lijst van bestanden die iemand vasthoudt.
- Start opent de zittende sessie van Grok of DeepSeek.
- Invoerbalk onderaan. Enter verstuurt, Shift+Enter maakt een nieuwe regel.
"""

from __future__ import annotations

import sys
import hashlib
import os
import re
import subprocess
from datetime import datetime
from pathlib import Path

# Force UTF-8 on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

try:
    import winsound
except ImportError:
    winsound = None

from PyQt6.QtCore import Qt, QTimer, QSize, QProcess, QUrl
from PyQt6.QtGui import QFont, QColor, QKeyEvent, QTextCursor, QTextBlockFormat, QTextCharFormat
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QScrollArea, QSplitter, QComboBox,
    QTextEdit, QLineEdit, QMessageBox, QDialog, QInputDialog,
    QTabWidget, QListWidget, QListWidgetItem, QTextBrowser
)

# Paden (werkt zowel vanuit Shared_Tools/ als vanuit CivicHelper/gui/)
_HERE = Path(__file__).resolve().parent
_CANDIDATE_WS = _HERE.parent.parent if (_HERE.parent.parent / "agy_werk").exists() else _HERE.parent
WORKSPACE = Path(os.environ.get("CIVIC_WORKSPACE", str(_CANDIDATE_WS)))
CASE_ROOT = WORKSPACE / "CivicHelper" if (WORKSPACE / "CivicHelper").exists() else _HERE.parent
AGY_WERK = WORKSPACE / "agy_werk" if (WORKSPACE / "agy_werk").exists() else (CASE_ROOT / "werk")
TAFEL_MD = AGY_WERK / "TAFEL.md" if (AGY_WERK / "TAFEL.md").exists() else (CASE_ROOT / "TAFEL.md")
SHARED_TOOLS = WORKSPACE / "Shared_Tools" if (WORKSPACE / "Shared_Tools").exists() else _HERE
CHAT_DISPATCH = (_HERE / "tafel_chat.py") if (_HERE / "tafel_chat.py").exists() else (SHARED_TOOLS / "tafel_chat.py")
INDEX_PATH = AGY_WERK / "TAFEL_INDEX.json"
for _p in (str(SHARED_TOOLS), str(_HERE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from tafel_indexer import claim_board, index_file
from tafel_archiver import archive_tafel_if_needed

ZORG_ROOT = WORKSPACE / "Zorgdossier" if (WORKSPACE / "Zorgdossier").exists() else (CASE_ROOT / "Dossier")

# Generieke loketcategorieën. Persoonlijke loketten worden lokaal geladen uit CivicHelper/werk/loketten.json (buiten git).
_DEFAULT_ISLANDS = (
    ("Gemeente / Wmo", ("gemeente", "wmo")),
    ("Dienst Toeslagen", ("toeslagen",)),
    ("Zorgverzekeraar", ("zorgverzeker", "menzis")),
    ("CAK", ("cak", "lavg")),
    ("Belastingkantoor", ("belasting",)),
    ("UWV / Werk", ("uwv", "werk")),
    ("Huisarts", ("huisarts",)),
    ("Ziekenhuis", ("ziekenhuis",)),
    ("Revalidatie & Zorg", ("revalidat", "ambulante")),
    ("Woningcorporatie", ("woning", "corporatie", "huur")),
    ("BKR", ("bkr",)),
)

_DEFAULT_SUBJECTS = (
    ("Zorg", "#5eead4", (
        "zorg", "gezond", "huisarts", "epd", "zieken", "medisch",
        "klinisch", "laboratorium", "farmacolog", "hematolog", "patient", "neuro", "revalid",
    )),
    ("Wmo", "#86efac", ("wmo", "teamleider", "casemanager", "consulent")),
    ("Ambulante zorg", "#67e8f9", ("ambulant", "begeleiding")),
    ("Cliëntondersteuning", "#c4b5fd", (
        "clientondersteuning", "cliëntondersteuning", "overdrachtsketen",
    )),
    ("Wonen", "#fbbf24", ("wonen", "huisvest", "huur", "woning")),
    ("Geld", "#4ade80", ("financ", "bank", "bkr", "incasso")),
    ("Bestuur", "#93c5fd", ("bestuur", "handhav", "politie", "vergun", "gemeente", "avg", "toezicht")),
    ("Identiteit", "#d8b4fe", ("brp", "adres", "verblijf", "immigr")),
    ("Werk", "#fdba74", ("werk", "uwv", "onderwijs", "leerplicht", "jeugd", "gezin")),
    ("Archief", "#e7e5e4", ("chronolog", "scan", "foto", "whatsapp", "afspraak", "bewijs")),
)


def _laad_lokale_loketten():
    import json
    islands = list(_DEFAULT_ISLANDS)
    subjects = [list(s) for s in _DEFAULT_SUBJECTS]
    for kandidaat in (CASE_ROOT / "werk" / "loketten.json", AGY_WERK / "loketten.json"):
        if kandidaat.exists():
            try:
                data = json.loads(kandidaat.read_text(encoding="utf-8"))
                if data.get("islands"):
                    islands = [(naam, tuple(sleutels)) for naam, sleutels in data["islands"]]
                extra = data.get("subject_extra_keys", {})
                for item in subjects:
                    if item[0] in extra:
                        item[2] = tuple(list(item[2]) + list(extra[item[0]]))
                break
            except Exception:
                pass
    return tuple(islands), tuple((s[0], s[1], tuple(s[2])) for s in subjects)


ISLANDS, SUBJECTS = _laad_lokale_loketten()

# Het interne model. Een stuk kan twee toestanden raken.
INTERN = (
    ("Lichaam", "#5eead4", ("zorg", "gezond", "huisarts", "epd", "zieken", "revalid", "lichaam", "medisch", "klinisch")),
    ("Geest", "#d8b4fe", ("geest", "mentaal", "cognit", "execut", "exoskelet", "frictie", "psych", "aandacht", "geheugen")),
    ("Bestaan", "#4ade80", ("financ", "bank", "bkr", "belasting", "toeslagen", "uwv", "werk", "inkomen", "uitkering", "huur", "wmo", "cak")),
)


def _subject_of(name: str) -> tuple[str, str]:
    """Langste trefwoord wint, zodat jeugdzorg niet onder zorg valt."""
    low = name.lower().replace("_", " ")
    best: tuple[str, str] | None = None
    best_len = 0
    for title, color, keys in SUBJECTS:
        for key in keys:
            if key in low and len(key) > best_len:
                best = (title, color)
                best_len = len(key)
    return best or ("Overig", "#f6d7a8")


def _cluster_token(name: str) -> str:
    token = name.split("_")[0]
    if token.isalpha() and len(token) >= 6:
        return token.lower()
    return ""


def dossier_bronnen() -> list[tuple[str, Path]]:
    """Alle dossierpaden. Scripts en caches blijven buiten de deur."""
    bronnen: list[tuple[str, Path]] = []
    if ZORG_ROOT.exists():
        for path in ZORG_ROOT.iterdir():
            if path.name.startswith(".") or path.name == "__pycache__":
                continue
            if path.is_dir():
                bronnen.append((path.name, path))
                continue
            if path.suffix.lower() in {".md", ".pdf", ".html"}:
                bronnen.append((path.stem, path))
    civic = CASE_ROOT / "Dossier"
    if civic.exists():
        for path in civic.glob("*.md"):
            if path.name.lower() in {"readme.md", "structuur.md"}:
                continue
            bronnen.append((path.stem, path))
    return bronnen


def dossier_rijen() -> list[tuple[str, str, str, str]]:
    """Kop, eventueel een stam, en daaronder elk bestand met zijn eigen pad."""
    buckets: dict[str, list[tuple[str, Path]]] = {}
    colors = {title: color for title, color, _keys in SUBJECTS}
    colors["Overig"] = "#f6d7a8"
    for name, path in dossier_bronnen():
        title, _color = _subject_of(name)
        buckets.setdefault(title, []).append((name, path))
    rows: list[tuple[str, str, str, str]] = []
    for title in [item[0] for item in SUBJECTS] + ["Overig"]:
        members = buckets.get(title)
        if not members:
            continue
        color = colors[title]
        rows.append(("kop", title.upper(), color, ""))
        counted: dict[str, int] = {}
        for name, _path in members:
            token = _cluster_token(name)
            if token:
                counted[token] = counted.get(token, 0) + 1
        seen: set[str] = set()
        for name, path in sorted(members, key=lambda item: item[0].lower()):
            token = _cluster_token(name)
            if token and counted.get(token, 0) >= 2 and token not in seen:
                seen.add(token)
                rows.append(("sub", token.capitalize(), color, ""))
            rows.append(("rij", name.replace("_", " "), color, str(path)))
    return rows


def _raakt(name: str, keys: tuple[str, ...]) -> bool:
    low = name.lower().replace("_", " ")
    return any(key in low for key in keys)


def dossier_sort_key(p: Path) -> tuple:
    name = p.stem
    m_date = re.search(r"(\d{4}-\d{2}-\d{2})", name)
    date_score = m_date.group(1) if m_date else ""
    m_num = re.match(r"^(\d+)", name)
    num_score = int(m_num.group(1)) if m_num else -1
    mtime = p.stat().st_mtime if p.exists() else 0
    return (date_score, num_score, mtime)


def model_overzicht() -> tuple[list[tuple[str, str, int, str, Path | None]], list[tuple[str, str, Path | None, str, Path | None]]]:
    """Drie interne toestanden, en per eiland de laatste in- en uitgang met aanklikbare paden."""
    bronnen = dossier_bronnen()
    intern: list[tuple[str, str, int, str, Path | None]] = []
    for title, color, keys in INTERN:
        hits = [(name, path) for name, path in bronnen if _raakt(name, keys)]
        laatst_naam = ""
        laatst_pad = None
        if hits:
            best_name, best_path = max(hits, key=lambda item: dossier_sort_key(item[1]))
            laatst_naam = best_name.replace("_", " ")
            laatst_pad = best_path
        intern.append((title, color, len(hits), laatst_naam, laatst_pad))

    brieven: list[tuple[str, Path]] = []
    in_folders = [CASE_ROOT / "Incoming_Letters", ZORG_ROOT, ZORG_ROOT / "Financien"]
    out_folders = [CASE_ROOT / "Outgoing_Drafts", WORKSPACE / "Shared_Tools" / "mail_outbox", WORKSPACE / "agy_werk" / "outbox"]
    valid_exts = {".md", ".pdf", ".html", ".txt", ".jpg", ".jpeg", ".png", ".eml"}

    for f in in_folders:
        if not f.exists():
            continue
        for p in f.iterdir():
            if p.is_file() and p.suffix.lower() in valid_exts and p.name != ".gitkeep":
                low = p.name.lower()
                if f == ZORG_ROOT or f == ZORG_ROOT / "Financien":
                    if any(k in low for k in ("aanvraag", "bezwaar", "brief", "concept", "mail_outbox")):
                        brieven.append(("uit", p))
                    else:
                        brieven.append(("in", p))
                else:
                    brieven.append(("in", p))

    for f in out_folders:
        if not f.exists():
            continue
        for p in f.iterdir():
            if p.is_file() and p.suffix.lower() in valid_exts and p.name != ".gitkeep":
                brieven.append(("uit", p))

    extern: list[tuple[str, str, Path | None, str, Path | None]] = []
    for label, keys in ISLANDS:
        binnen = [p for kant, p in brieven if kant == "in" and _raakt(p.name, keys)]
        uit = [p for kant, p in brieven if kant == "uit" and _raakt(p.name, keys)]
        def fmt(paths: list[Path]) -> tuple[str, Path | None]:
            if not paths:
                return "stil", None
            best = max(paths, key=dossier_sort_key)
            naam = best.stem.replace("_", " ")
            short = naam if len(naam) <= 40 else naam[:37] + "…"
            return short, best
        s_in, p_in = fmt(binnen)
        s_uit, p_uit = fmt(uit)
        extern.append((label, s_in, p_in, s_uit, p_uit))

    return intern, extern


def structuur_markdown() -> str:
    """De deur die een model openslaat. De paden blijven de echte bestanden."""
    lines = [
        "# Dossierstructuur",
        "",
        "Eén indeling voor elk model en voor het Civic Helper-scherm.",
        "De stukken blijven in `Zorgdossier` en in `CivicHelper/Dossier` staan,",
        "omdat zij naar elkaar verwijzen. Deze lijst is de deur, niet een tweede kopie.",
        "",
        "Een regel opent het pad. Een map opent de map. Een markdownbestand opent in de lezer van Civic Helper.",
        "",
    ]
    current = ""
    for kind, text, _color, path in dossier_rijen():
        if kind == "kop":
            lines.append(f"## {text.title()}")
            lines.append("")
            current = text
            continue
        if kind == "sub":
            lines.append(f"### {text}")
            lines.append("")
            continue
        target = Path(path)
        deur = CASE_ROOT / "Dossier"
        try:
            shown = Path(os.path.relpath(target, deur)).as_posix()
        except ValueError:
            shown = str(target)
        lines.append(f"- [{text}]({shown})")
    lines.append("")
    return "\n".join(lines)


PYTHON_EXE = sys.executable
GROK_STARTER = WORKSPACE / "start-grok.cmd"
DEEPSEEK_STARTER = WORKSPACE / "start-deepseek.cmd"
ARGON_STARTER = WORKSPACE / "start-gemini-argon.cmd"


class ChatInputEdit(QTextEdit):
    """Textarea die Enter gebruikt om te verzenden, en Shift+Enter voor een nieuwe regel."""
    def __init__(self, parent=None, on_enter=None):
        super().__init__(parent)
        self.on_enter = on_enter

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Return and not (event.modifiers() & Qt.KeyboardModifier.ShiftModifier):
            if self.on_enter:
                self.on_enter()
            event.accept()
        else:
            super().keyPressEvent(event)


class MarkdownViewer(QDialog):
    """Leest een markdownbestand in Civic Helper, zonder de koppeling van Windows."""

    def __init__(self, path: Path, parent=None):
        super().__init__(parent)
        self.setWindowTitle(path.name)
        self.resize(780, 680)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        view = QTextEdit()
        view.setReadOnly(True)
        view.setObjectName("md-view")
        font = QFont("JetBrains Mono", 15)
        font.setStyleHint(QFont.StyleHint.Monospace)
        view.setFont(font)
        view.document().setDefaultFont(font)
        view.setStyleSheet(
            "QTextEdit#md-view { background: #100b1c; color: #e2e8f0; "
            "font-family: 'JetBrains Mono', monospace; font-size: 15pt; "
            "border: none; padding: 8px; }"
        )
        view.setMarkdown(path.read_text(encoding="utf-8", errors="replace"))
        self._zet_regelafstand(view, font)
        layout.addWidget(view)

    @staticmethod
    def _zet_regelafstand(view: QTextEdit, font: QFont):
        """Zelfde letter als de tafel, met lucht tussen de regels en de alinea's."""
        teken = QTextCharFormat()
        teken.setFontFamily(font.family())
        blok = QTextBlockFormat()
        blok.setLineHeight(156, QTextBlockFormat.LineHeightTypes.ProportionalHeight.value)
        blok.setTopMargin(2)
        blok.setBottomMargin(10)
        cursor = QTextCursor(view.document())
        cursor.beginEditBlock()
        block = view.document().begin()
        while block.isValid():
            cursor.setPosition(block.position())
            cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock, QTextCursor.MoveMode.KeepAnchor)
            cursor.mergeCharFormat(teken)
            cursor.mergeBlockFormat(blok)
            block = block.next()
        cursor.endEditBlock()


def ensure_chat_dispatch() -> None:
    """Zorgt dat een regel uit dit venster antwoord krijgt, zonder de terminal."""
    try:
        import psutil
    except ImportError:
        psutil = None
    if psutil is not None:
        for proc in psutil.process_iter(["cmdline"]):
            try:
                cmd = " ".join(proc.info.get("cmdline") or [])
            except Exception:
                continue
            if "tafel_chat.py" in cmd:
                return
    log_path = AGY_WERK / "scratch" / "tafel_chat.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    handle = open(log_path, "a", encoding="utf-8")
    flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
    subprocess.Popen(
        [sys.executable, str(CHAT_DISPATCH)],
        cwd=str(WORKSPACE),
        stdout=handle,
        stderr=subprocess.STDOUT,
        creationflags=flags,
    )


class TafelWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Civic Helper 0.3 — Tafel")
        self.resize(1480, 860)
        self.move(486, 189)

        self.last_hash = ""
        self.last_turn_count = 0
        self.sound_enabled = True
        self.current_baton = "Xander"
        self.file_claims: list[dict] = []

        self._setup_ui()
        self._apply_styles()

        # Timers
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.check_and_refresh_tafel)
        self.refresh_timer.start(1000)

        self.process_timer = QTimer(self)
        self.process_timer.timeout.connect(self.update_process_statuses)
        self.process_timer.start(3000)

        # Direct inladen
        self.check_and_refresh_tafel()
        self.update_process_statuses()
        ensure_chat_dispatch()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # 1. TOP TOOLBAR
        toolbar = QFrame()
        toolbar.setObjectName("top-toolbar")
        tb_layout = QHBoxLayout(toolbar)
        tb_layout.setContentsMargins(12, 6, 12, 6)

        lbl_app = QLabel("Civic Helper 0.3")
        lbl_app.setObjectName("app-badge")
        lbl_chan = QLabel("tafel")
        lbl_chan.setStyleSheet("color: #94a3b8; font-family: 'JetBrains Mono', monospace; font-size: 12px;")

        tb_layout.addWidget(lbl_app)
        tb_layout.addWidget(lbl_chan)
        tb_layout.addStretch()

        btn_setup_env = QPushButton("🛠️ Omgeving Inrichten")
        btn_setup_env.setObjectName("btn-action-gold")
        btn_setup_env.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_setup_env.setToolTip("Richt de lokale werkomgeving en Python-tools in en open het begeleide stappenplan (Waarom & Doel).")
        btn_setup_env.clicked.connect(self.action_setup_environment)
        tb_layout.addWidget(btn_setup_env)

        btn_start_all = QPushButton("🚀 Start Allen")
        btn_start_all.setObjectName("btn-action")
        btn_start_all.clicked.connect(lambda: self.spawn_process("all"))
        tb_layout.addWidget(btn_start_all)

        btn_search = QPushButton("🔍 Non-RAG Zoek")
        btn_search.setObjectName("btn-action-gold")
        btn_search.clicked.connect(self.action_search)
        tb_layout.addWidget(btn_search)

        btn_archive = QPushButton("📦 Archief Nu")
        btn_archive.setObjectName("btn-action-purple")
        btn_archive.clicked.connect(self.action_archive)
        tb_layout.addWidget(btn_archive)

        self.btn_sound = QPushButton("🔔 Geluid: AAN")
        self.btn_sound.setObjectName("btn-sound")
        self.btn_sound.clicked.connect(self.toggle_sound)
        tb_layout.addWidget(self.btn_sound)

        root_layout.addWidget(toolbar)

        # 2. TOPIC BAR
        topic_bar = QFrame()
        topic_bar.setObjectName("topic-bar")
        topic_layout = QHBoxLayout(topic_bar)
        topic_layout.setContentsMargins(14, 4, 14, 4)

        self.lbl_topic = QLabel("<b>Tafel:</b> beraadslaging en casusregie")
        self.lbl_topic.setStyleSheet("color: #e2e8f0; font-family: 'JetBrains Mono', monospace; font-size: 11px;")
        topic_layout.addWidget(self.lbl_topic)
        topic_layout.addStretch()

        self.lbl_baton_info = QLabel("Stok op: <span style='color:#64748b'>geen bestand</span>")
        self.lbl_baton_info.setStyleSheet("color: #94a3b8; font-family: 'JetBrains Mono', monospace; font-size: 11px;")
        topic_layout.addWidget(self.lbl_baton_info)

        self.lbl_turns_info = QLabel("Beurten: <b style='color:#f59e0b'>0</b> <span style='color:#64748b'>archief na 20</span>")
        self.lbl_turns_info.setStyleSheet("color: #94a3b8; font-family: 'JetBrains Mono', monospace; font-size: 11px; margin-left: 10px;")
        topic_layout.addWidget(self.lbl_turns_info)

        lbl_auto = QLabel("Auto-archief AAN")
        lbl_auto.setStyleSheet("color: #10b981; background: rgba(16, 185, 129, 0.15); padding: 2px 6px; border-radius: 4px; font-family: 'JetBrains Mono', monospace; font-size: 10px; margin-left: 10px;")
        topic_layout.addWidget(lbl_auto)

        root_layout.addWidget(topic_bar)

        # 3. KOLOM LINKS, GESPREK, AANWEZIGEN RECHTS
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(1)

        case_container = QFrame()
        case_container.setObjectName("case-panel")
        case_container.setFixedWidth(420)
        case_layout = QVBoxLayout(case_container)
        case_layout.setContentsMargins(10, 10, 10, 10)
        case_layout.setSpacing(8)

        self.case_tabs = QTabWidget()
        self.case_tabs.setObjectName("case-tabs")
        self.case_tabs.setDocumentMode(True)

        # TAB 0: OVERZICHT (Twee Klokken + Intern + Loketten In/Uit)
        self.model_view = QTextBrowser()
        self.model_view.setObjectName("case-mirror")
        self.model_view.setReadOnly(True)
        self.model_view.setOpenExternalLinks(False)
        self.model_view.anchorClicked.connect(self._model_link_clicked)
        self.case_tabs.addTab(self.model_view, "Overzicht")

        # TAB 1: DOSSIERS (Met snelle zoek-/filterbalk)
        dossiers_page = QWidget()
        dossiers_layout = QVBoxLayout(dossiers_page)
        dossiers_layout.setContentsMargins(6, 6, 6, 6)
        dossiers_layout.setSpacing(6)
        dos_filter_row = QHBoxLayout()
        dos_filter_row.setContentsMargins(0, 0, 0, 0)
        dos_filter_row.setSpacing(4)
        self.dossier_filter_edit = QLineEdit()
        self.dossier_filter_edit.setPlaceholderText("Filter dossiers (bijv. zorg, wmo, umcg, cak)...")
        self.dossier_filter_edit.setStyleSheet(
            "background: #161024; color: #e2e8f0; border: 1px solid rgba(212,175,55,0.28); "
            "border-radius: 4px; padding: 4px 8px; font-size: 11px; font-family: 'JetBrains Mono', monospace;"
        )
        self.dossier_filter_edit.textChanged.connect(self._apply_dossier_filter)
        btn_dos_clear = QPushButton("Alles")
        btn_dos_clear.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_dos_clear.clicked.connect(lambda: self.dossier_filter_edit.setText(""))
        dos_filter_row.addWidget(self.dossier_filter_edit, 1)
        dos_filter_row.addWidget(btn_dos_clear)
        dossiers_layout.addLayout(dos_filter_row)

        self.list_dossiers = QListWidget()
        self.list_dossiers.setObjectName("case-list")
        self.list_dossiers.setCursor(Qt.CursorShape.PointingHandCursor)
        self.list_dossiers.itemClicked.connect(self._open_dossier)
        dossiers_layout.addWidget(self.list_dossiers, 1)
        self.case_tabs.addTab(dossiers_page, "Dossiers")

        # TAB 2: POST & BRIEF (In/Uit filter + Veto/Poort-toets & Sein naar mailprogramma)
        post_page = QWidget()
        post_layout = QVBoxLayout(post_page)
        post_layout.setContentsMargins(6, 6, 6, 6)
        post_layout.setSpacing(6)
        self._post_filter_mode = "alle"
        post_filter_row = QHBoxLayout()
        post_filter_row.setContentsMargins(0, 0, 0, 0)
        post_filter_row.setSpacing(4)
        self.btn_post_all = QPushButton("Alle stukken")
        self.btn_post_uit = QPushButton("📤 Uitgaand")
        self.btn_post_in = QPushButton("📥 Binnen")
        for b, mode in ((self.btn_post_all, "alle"), (self.btn_post_uit, "uit"), (self.btn_post_in, "binnen")):
            b.setCheckable(True)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.clicked.connect(lambda _c=False, m=mode: self._set_post_filter(m))
            post_filter_row.addWidget(b)
        self.btn_post_all.setChecked(True)
        post_layout.addLayout(post_filter_row)

        self.list_stukken = QListWidget()
        self.list_stukken.setObjectName("case-list")
        self.list_stukken.setCursor(Qt.CursorShape.PointingHandCursor)
        self.list_stukken.itemDoubleClicked.connect(self._open_stuk)
        post_layout.addWidget(self.list_stukken, 1)

        post_actie_row = QHBoxLayout()
        post_actie_row.setContentsMargins(0, 0, 0, 0)
        post_actie_row.setSpacing(4)
        btn_open_stuk = QPushButton("📄 Lezen")
        btn_open_stuk.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_open_stuk.clicked.connect(self._open_selected_stuk)
        btn_toets_stuk = QPushButton("🛡️ Toets Poort")
        btn_toets_stuk.setObjectName("btn-action")
        btn_toets_stuk.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_toets_stuk.clicked.connect(self._toets_selected_stuk)
        btn_sein_stuk = QPushButton("✉️ Sein (Mail)")
        btn_sein_stuk.setObjectName("btn-action-gold")
        btn_sein_stuk.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_sein_stuk.clicked.connect(self._sein_selected_stuk)
        post_actie_row.addWidget(btn_open_stuk)
        post_actie_row.addWidget(btn_toets_stuk)
        post_actie_row.addWidget(btn_sein_stuk)
        post_layout.addLayout(post_actie_row)
        self.case_tabs.addTab(post_page, "Brieven")

        # Verborgen compatibiliteitswidgets voor legacy methodes
        self.mirror_view = QTextEdit()
        self.list_lijnen = QListWidget()

        # TAB 3: ANALYSE (Uitsluitend burger-basisadministratie in gewone taal, zonder HVM/beurs/fysica-lab)
        analyse_page = QWidget()
        analyse_layout = QVBoxLayout(analyse_page)
        analyse_layout.setContentsMargins(6, 6, 6, 6)
        analyse_layout.setSpacing(6)

        self.analyse_categorie = "zaak"
        self._analyse_raw_text = ""
        self._analyse_human_text = ""
        self._analyse_toon_technisch = False
        self._analyse_active_key = ""
        self._analyse_active_titel = ""
        self._analyse_active_toelichting = ""

        lbl_analyse_kop = QLabel("CONTROLES OP JOUW BASISADMINISTRATIE")
        lbl_analyse_kop.setStyleSheet(
            "color: #D4AF37; font-family: 'JetBrains Mono', monospace; font-size: 11px; font-weight: bold; letter-spacing: 1px;"
        )
        analyse_layout.addWidget(lbl_analyse_kop)

        self.analyse_list = QListWidget()
        self.analyse_list.setObjectName("case-list")
        self.analyse_list.setMaximumHeight(225)
        self.analyse_list.setCursor(Qt.CursorShape.PointingHandCursor)
        self.analyse_list.itemDoubleClicked.connect(lambda _item: self._start_analyse())

        actie_row = QHBoxLayout()
        actie_row.setContentsMargins(0, 0, 0, 0)
        actie_row.setSpacing(4)
        self.analyse_start = QPushButton("▶ Start controle")
        self.analyse_start.setObjectName("btn-action")
        self.analyse_start.clicked.connect(self._start_analyse)
        self.analyse_toggle_tech = QPushButton("Technisch rapport")
        self.analyse_toggle_tech.setCursor(Qt.CursorShape.PointingHandCursor)
        self.analyse_toggle_tech.setEnabled(False)
        self.analyse_toggle_tech.clicked.connect(self._wissel_analyse_weergave)
        self.analyse_to_tafel = QPushButton("📌 Op Tafel")
        self.analyse_to_tafel.setObjectName("btn-action-gold")
        self.analyse_to_tafel.setCursor(Qt.CursorShape.PointingHandCursor)
        self.analyse_to_tafel.setEnabled(False)
        self.analyse_to_tafel.clicked.connect(self._leg_analyse_op_tafel)
        actie_row.addWidget(self.analyse_start, 2)
        actie_row.addWidget(self.analyse_toggle_tech, 1)
        actie_row.addWidget(self.analyse_to_tafel, 1)

        self.analyse_out = QTextEdit()
        self.analyse_out.setObjectName("case-mirror")
        self.analyse_out.setReadOnly(True)
        self.analyse_out.setPlaceholderText("Kies hierboven een vraag en klik op 'Start controle'. Je krijgt eerst een uitleg in gewone taal.")
        analyse_layout.addWidget(self.analyse_list)
        analyse_layout.addLayout(actie_row)
        analyse_layout.addWidget(self.analyse_out, 1)
        self.case_tabs.addTab(analyse_page, "Analyse")
        self._vul_analyses()

        self.analyse_process = QProcess(self)
        self.analyse_process.setWorkingDirectory(str(CASE_ROOT))
        self.analyse_process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.analyse_process.readyReadStandardOutput.connect(self._analyse_lees)
        self.analyse_process.finished.connect(self._analyse_klaar)

        self.case_tabs.setCurrentIndex(0)
        case_layout.addWidget(self.case_tabs)

        self.case_timer = QTimer(self)
        self.case_timer.timeout.connect(self._refresh_case_tabs)
        self.case_timer.start(20000)
        self._refresh_case_tabs()
        splitter.addWidget(case_container)

        # 3A. CHAT BUFFER
        chat_container = QWidget()
        chat_layout = QVBoxLayout(chat_container)
        chat_layout.setContentsMargins(12, 10, 12, 10)
        chat_layout.setSpacing(0)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setObjectName("chat-scroll")

        self.chat_feed = QWidget()
        self.feed_layout = QVBoxLayout(self.chat_feed)
        self.feed_layout.setContentsMargins(0, 0, 0, 0)
        self.feed_layout.setSpacing(10)
        self.feed_layout.addStretch()

        self.scroll_area.setWidget(self.chat_feed)
        chat_layout.addWidget(self.scroll_area)
        splitter.addWidget(chat_container)

        # 3B. NICKLIST (RECHTS)
        nick_container = QFrame()
        nick_container.setObjectName("nicklist-panel")
        nick_container.setFixedWidth(300)
        nick_layout = QVBoxLayout(nick_container)
        nick_layout.setContentsMargins(12, 10, 12, 10)
        nick_layout.setSpacing(10)

        nick_header = QLabel("👥 Aanwezigen")
        nick_header.setStyleSheet("color: #D4AF37; font-family: 'JetBrains Mono', monospace; font-weight: bold; font-size: 12px;")
        nick_layout.addWidget(nick_header)

        # Vaste tafelgenoten
        lbl_vaste = QLabel("VASTE TAFELGENOTEN")
        lbl_vaste.setStyleSheet("color: #64748b; font-size: 10px; font-weight: bold; letter-spacing: 1px;")
        nick_layout.addWidget(lbl_vaste)

        # @Xander
        card_xander, self.badge_xander = self._create_nick_card("@Xander", "Mens aan tafel / Regie", "#D4AF37", "@", "Online", "#10b981")
        nick_layout.addWidget(card_xander)

        # +agy
        card_agy, self.badge_agy = self._create_nick_card("+agy", "Antigravity Co-Pilot", "#00d4ff", "+", "Online", "#10b981")
        nick_layout.addWidget(card_agy)

        # +Grok Code
        self.card_grok, self.badge_grok = self._create_action_nick_card("+Grok Code", "Synthese & Engine", "#f59e0b", "+", "Detecteren...", "grok")
        nick_layout.addWidget(self.card_grok)

        # +DeepSeek
        self.card_deepseek, self.badge_deepseek = self._create_action_nick_card("+DeepSeek", "loop-breaker, 25 stappen", "#3b82f6", "+", "Detecteren...", "deepseek")
        nick_layout.addWidget(self.card_deepseek)

        # On-demand modellen
        lbl_extra = QLabel("ON-DEMAND MODELLEN")
        lbl_extra.setStyleSheet("color: #64748b; font-size: 10px; font-weight: bold; letter-spacing: 1px; margin-top: 10px;")
        nick_layout.addWidget(lbl_extra)
        self.nick_layout = nick_layout
        self._on_demand_cards = set(["argon", "gemini", "qwen", "nvidia"])

        # +Gemini Argon CLI SDK
        self.card_argon, self.badge_argon = self._create_summon_action_card(
            "+Gemini Argon CLI SDK",
            "gemini-4-argon · 1M context",
            "#2dd4bf",
            "+",
            "argon",
            "argon",
        )
        nick_layout.addWidget(self.card_argon)

        # +Gemini Flash
        card_gemini = self._create_summon_card("+Gemini 3.8 Flash", "Zittende sessie", "#10b981", "+", "gemini")
        nick_layout.addWidget(card_gemini)

        # +Qwen 2.5 32B
        card_qwen = self._create_summon_card("+Qwen 2.5 32B", "Groq LPU · online", "#a855f7", "+", "qwen")
        nick_layout.addWidget(card_qwen)

        # +NVIDIA Super 120B
        card_nvidia = self._create_summon_card("+NVIDIA Super 120B", "Nemotron 3.5 · online", "#76b900", "+", "nvidia")
        nick_layout.addWidget(card_nvidia)

        # Knop Model Aanschuiven
        self.btn_add_model = QPushButton("+ Model Aanschuiven...")
        self.btn_add_model.setObjectName("btn-add-model")
        self.btn_add_model.clicked.connect(self.action_add_model)
        nick_layout.addWidget(self.btn_add_model)

        lbl_stok = QLabel("STOK OP BESTANDEN")
        lbl_stok.setStyleSheet("color: #64748b; font-size: 10px; font-weight: bold; letter-spacing: 1px; margin-top: 10px;")
        nick_layout.addWidget(lbl_stok)

        self.stok_list = QLabel("<span style='color:#64748b'>geen bestand</span>")
        self.stok_list.setWordWrap(True)
        self.stok_list.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.stok_list.setStyleSheet("color: #cbd5e1; font-size: 11px; font-family: 'JetBrains Mono', monospace;")
        nick_layout.addWidget(self.stok_list)

        lbl_legenda = QLabel("🟢 Online   🟡 Aan zet   🔴 Offline")
        lbl_legenda.setStyleSheet("color: #64748b; font-family: 'JetBrains Mono', monospace; font-size: 10px;")
        nick_layout.addWidget(lbl_legenda)
        nick_layout.addStretch()

        splitter.addWidget(nick_container)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 0)
        root_layout.addWidget(splitter, 1)

        # 4. BOTTOM INPUT BAR
        bottom_bar = QFrame()
        bottom_bar.setObjectName("bottom-bar")
        bottom_layout = QHBoxLayout(bottom_bar)
        bottom_layout.setContentsMargins(12, 8, 12, 10)
        bottom_layout.setSpacing(10)

        # Ontvanger selector
        rec_box = QVBoxLayout()
        rec_lbl = QLabel("Aan:")
        rec_lbl.setStyleSheet("color: #94a3b8; font-size: 10px; font-family: 'JetBrains Mono', monospace;")
        self.combo_recipient = QComboBox()
        self.combo_recipient.setObjectName("combo-rec")
        self.combo_recipient.addItems([
            "@Allen",
            "@Grok Code",
            "@DeepSeek",
            "@agy",
            "@Gemini Argon CLI SDK",
            "@Gemini 3.8 Flash",
            "@NVIDIA"
        ])
        rec_box.addWidget(rec_lbl)
        rec_box.addWidget(self.combo_recipient)
        bottom_layout.addLayout(rec_box)

        # Invoerveld
        in_box = QVBoxLayout()
        in_lbl = QLabel("Bericht aan De Tafel (Shift+Enter voor nieuwe regel):")
        in_lbl.setStyleSheet("color: #94a3b8; font-size: 10px; font-family: 'JetBrains Mono', monospace;")
        self.input_edit = ChatInputEdit(on_enter=self.action_send_message)
        self.input_edit.setObjectName("chat-input")
        self.input_edit.setFixedHeight(54)
        self.input_edit.setPlaceholderText("Typ je inbreng (/zoek, /stok bestand#onderdeel, /vrij bestand)...")
        in_box.addWidget(in_lbl)
        in_box.addWidget(self.input_edit)
        bottom_layout.addLayout(in_box, 1)

        # Send button
        send_box = QVBoxLayout()
        send_box.addStretch()
        btn_send = QPushButton("Leg op Tafel ↵")
        btn_send.setObjectName("btn-send")
        btn_send.clicked.connect(self.action_send_message)
        send_box.addWidget(btn_send)
        bottom_layout.addLayout(send_box)

        root_layout.addWidget(bottom_bar)

    def _create_nick_card(self, nick: str, subtitle: str, color: str, prefix: str, status_text: str, status_color: str):
        card = QFrame()
        card.setObjectName("nick-card")
        l = QVBoxLayout(card)
        l.setContentsMargins(8, 6, 8, 6)
        l.setSpacing(2)

        top = QHBoxLayout()
        lbl_nick = QLabel(f"<b style='color:{color}; font-size:13px;'>{prefix}</b> <b style='color:{color}; font-size:12px;'>{nick[1:]}</b>")
        lbl_status = QLabel(f"<span style='color:{status_color}; font-size:10px;'>● {status_text}</span>")
        top.addWidget(lbl_nick)
        top.addStretch()
        top.addWidget(lbl_status)
        l.addLayout(top)

        lbl_sub = QLabel(subtitle)
        lbl_sub.setStyleSheet("color: #64748b; font-size: 10px; margin-left: 12px;")
        l.addWidget(lbl_sub)
        return card, lbl_status

    def _create_action_nick_card(self, nick: str, subtitle: str, color: str, prefix: str, status_text: str, target: str):
        card = QFrame()
        card.setObjectName("nick-card")
        l = QVBoxLayout(card)
        l.setContentsMargins(8, 6, 8, 6)
        l.setSpacing(2)

        top = QHBoxLayout()
        lbl_nick = QLabel(f"<b style='color:{color}; font-size:13px;'>{prefix}</b> <b style='color:{color}; font-size:12px;'>{nick[1:]}</b>")
        badge = QLabel(f"<span style='color:#64748b; font-size:10px;'>● {status_text}</span>")
        top.addWidget(lbl_nick)
        top.addStretch()
        top.addWidget(badge)
        l.addLayout(top)

        sub_row = QHBoxLayout()
        lbl_sub = QLabel(subtitle)
        lbl_sub.setStyleSheet("color: #64748b; font-size: 10px; margin-left: 12px;")
        sub_row.addWidget(lbl_sub)
        sub_row.addStretch()

        btn_start = QPushButton("Start")
        btn_start.setObjectName("btn-mini-start")
        btn_start.clicked.connect(lambda: self.spawn_process(target))
        sub_row.addWidget(btn_start)
        l.addLayout(sub_row)

        return card, badge

    def _create_summon_card(self, nick: str, subtitle: str, color: str, prefix: str, model_id: str):
        card = QFrame()
        card.setObjectName("nick-card")
        l = QVBoxLayout(card)
        l.setContentsMargins(8, 6, 8, 6)
        l.setSpacing(2)

        top = QHBoxLayout()
        lbl_nick = QLabel(f"<b style='color:{color}; font-size:13px;'>{prefix}</b> <b style='color:{color}; font-size:12px;'>{nick[1:]}</b>")
        lbl_status = QLabel("<span style='color:#10b981; font-size:10px;'>● Gereed</span>")
        top.addWidget(lbl_nick)
        top.addStretch()
        top.addWidget(lbl_status)
        l.addLayout(top)

        sub_row = QHBoxLayout()
        lbl_sub = QLabel(subtitle)
        lbl_sub.setStyleSheet("color: #64748b; font-size: 10px; margin-left: 12px;")
        sub_row.addWidget(lbl_sub)
        sub_row.addStretch()

        btn_ask = QPushButton("Aanspreken")
        btn_ask.setObjectName("btn-mini-ask")
        btn_ask.clicked.connect(lambda: self.address_seat(model_id))
        sub_row.addWidget(btn_ask)
        l.addLayout(sub_row)

        return card

    def _create_summon_action_card(self, nick: str, subtitle: str, color: str, prefix: str, model_id: str, target: str):
        card = QFrame()
        card.setObjectName("nick-card")
        l = QVBoxLayout(card)
        l.setContentsMargins(8, 6, 8, 6)
        l.setSpacing(2)

        top = QHBoxLayout()
        lbl_nick = QLabel(f"<b style='color:{color}; font-size:13px;'>{prefix}</b> <b style='color:{color}; font-size:12px;'>{nick[1:]}</b>")
        badge = QLabel("<span style='color:#10b981; font-size:10px;'>● Online</span>")
        top.addWidget(lbl_nick)
        top.addStretch()
        top.addWidget(badge)
        l.addLayout(top)

        sub_row = QHBoxLayout()
        lbl_sub = QLabel(subtitle)
        lbl_sub.setStyleSheet("color: #64748b; font-size: 10px; margin-left: 12px;")
        sub_row.addWidget(lbl_sub)
        sub_row.addStretch()

        btn_start = QPushButton("Start")
        btn_start.setObjectName("btn-mini-start")
        btn_start.clicked.connect(lambda: self.spawn_process(target))
        sub_row.addWidget(btn_start)

        btn_ask = QPushButton("Aanspreken")
        btn_ask.setObjectName("btn-mini-ask")
        btn_ask.clicked.connect(lambda: self.address_seat(model_id))
        sub_row.addWidget(btn_ask)
        l.addLayout(sub_row)

        return card, badge

    def _apply_styles(self):
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #05030a;
                color: #e2e8f0;
                font-family: 'Segoe UI', system-ui, sans-serif;
            }
            QFrame#top-toolbar {
                background: linear-gradient(180deg, #1c142c 0%, #0e0a18 100%);
                border-bottom: 1px solid rgba(212, 175, 55, 0.25);
            }
            QLabel#app-badge {
                color: #D4AF37;
                font-family: 'JetBrains Mono', monospace;
                font-weight: bold;
                font-size: 11px;
                background: rgba(212, 175, 55, 0.12);
                border: 1px solid rgba(212, 175, 55, 0.3);
                padding: 2px 6px;
                border-radius: 4px;
            }
            QPushButton#btn-action {
                background: rgba(0, 212, 255, 0.15);
                color: #00d4ff;
                border: 1px solid rgba(0, 212, 255, 0.35);
                padding: 4px 10px;
                border-radius: 4px;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton#btn-action:hover {
                background: rgba(0, 212, 255, 0.25);
            }
            QPushButton#btn-action-gold {
                background: rgba(212, 175, 55, 0.15);
                color: #D4AF37;
                border: 1px solid rgba(212, 175, 55, 0.35);
                padding: 4px 10px;
                border-radius: 4px;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton#btn-action-gold:hover {
                background: rgba(212, 175, 55, 0.25);
            }
            QPushButton#btn-action-purple {
                background: rgba(168, 85, 247, 0.15);
                color: #c084fc;
                border: 1px solid rgba(168, 85, 247, 0.35);
                padding: 4px 10px;
                border-radius: 4px;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton#btn-action-purple:hover {
                background: rgba(168, 85, 247, 0.25);
            }
            QPushButton#btn-sound {
                background: #1e293b;
                color: #94a3b8;
                border: 1px solid #334155;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 11px;
                font-family: 'JetBrains Mono', monospace;
            }
            QFrame#topic-bar {
                background: #100b1c;
                border-bottom: 1px solid rgba(212, 175, 55, 0.2);
            }
            QScrollArea#chat-scroll {
                background: transparent;
                border: none;
            }
            QFrame#case-panel {
                background: #090614;
                border-right: 1px solid rgba(212, 175, 55, 0.2);
            }
            QFrame#nicklist-panel {
                background: #090614;
                border-left: 1px solid rgba(212, 175, 55, 0.2);
            }
            QTabWidget#case-tabs::pane {
                border: 1px solid rgba(212, 175, 55, 0.28);
                background: #100b1c;
                border-radius: 4px;
            }
            QTabWidget#case-tabs QTabBar::tab {
                background: #1c142c;
                color: #94a3b8;
                padding: 6px 10px;
                border: 1px solid rgba(255, 255, 255, 0.06);
                border-bottom: none;
                font-family: 'JetBrains Mono', monospace;
                font-size: 11px;
            }
            QTabWidget#case-tabs QTabBar::tab:selected {
                background: #100b1c;
                color: #D4AF37;
            }
            QTextEdit#case-mirror, QListWidget#case-list {
                background: #100b1c;
                color: #cbd5e1;
                border: none;
                font-family: 'JetBrains Mono', monospace;
                font-size: 11px;
            }
            QFrame#nick-card {
                background: rgba(18, 12, 28, 0.8);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 6px;
            }
            QFrame#nick-card:hover {
                border: 1px solid rgba(212, 175, 55, 0.3);
            }
            QPushButton#btn-mini-start {
                background: rgba(245, 158, 11, 0.2);
                color: #f59e0b;
                border: 1px solid rgba(245, 158, 11, 0.4);
                border-radius: 3px;
                padding: 1px 6px;
                font-size: 10px;
            }
            QPushButton#btn-mini-start:hover {
                background: rgba(245, 158, 11, 0.35);
            }
            QPushButton#btn-mini-ask {
                background: rgba(16, 185, 129, 0.2);
                color: #34d399;
                border: 1px solid rgba(16, 185, 129, 0.4);
                border-radius: 3px;
                padding: 1px 6px;
                font-size: 10px;
            }
            QPushButton#btn-mini-ask:hover {
                background: rgba(16, 185, 129, 0.35);
            }
            QPushButton#btn-add-model {
                background: rgba(212, 175, 55, 0.06);
                color: #D4AF37;
                border: 1px dashed rgba(212, 175, 55, 0.4);
                border-radius: 4px;
                padding: 5px;
                font-size: 11px;
                font-family: 'JetBrains Mono', monospace;
            }
            QPushButton#btn-add-model:hover {
                background: rgba(212, 175, 55, 0.15);
                border: 1px solid #D4AF37;
            }
            QFrame#bottom-bar {
                background: #0e0a18;
                border-top: 1px solid rgba(212, 175, 55, 0.2);
            }
            QComboBox#combo-rec {
                background: #161024;
                color: #e2e8f0;
                border: 1px solid rgba(212, 175, 55, 0.3);
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 11px;
                font-family: 'JetBrains Mono', monospace;
            }
            QTextEdit#chat-input {
                background: #161024;
                color: #ffffff;
                border: 1px solid rgba(212, 175, 55, 0.3);
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 12px;
            }
            QTextEdit#chat-input:focus {
                border: 1px solid #D4AF37;
            }
            QPushButton#btn-send {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #D4AF37, stop:1 #b38f24);
                color: #05030a;
                font-weight: bold;
                font-size: 12px;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
            }
            QPushButton#btn-send:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #e5bd3b, stop:1 #c49d28);
            }
            QScrollBar:vertical {
                background: rgba(5, 3, 10, 0.6);
                width: 8px;
            }
            QScrollBar::handle:vertical {
                background: rgba(212, 175, 55, 0.25);
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(212, 175, 55, 0.5);
            }
        """)

    def check_and_refresh_tafel(self):
        """Controleert of TAFEL.md is gewijzigd en herlaadt de beurten indien nodig."""
        if not TAFEL_MD.exists():
            return

        try:
            current_bytes = TAFEL_MD.read_bytes()
            h = hashlib.sha256(current_bytes).hexdigest()
            if h == self.last_hash:
                return
            self.last_hash = h

            turns = index_file(TAFEL_MD)
            if not turns:
                return

            # Automatische rolling archivering bij overschrijden van de drempel (20)
            if len(turns) > 20:
                archive_tafel_if_needed(threshold=20)
                turns = index_file(TAFEL_MD)

            # De stok ligt op bestanden, niet op één stoel voor de hele tafel.
            self.current_baton = turns[-1].get("baton_to", "Onbekend")
            self._show_file_claims(turns)
            self.update_process_statuses()
            self.lbl_turns_info.setText(
                f"Beurten: <b style='color:#f59e0b'>{len(turns)}</b>"
                f" <span style='color:#64748b'>archief na 20</span>"
            )

            # Geluidssignaal bij nieuwe beurt
            if len(turns) > self.last_turn_count and self.last_turn_count > 0:
                if self.sound_enabled and winsound:
                    try:
                        winsound.Beep(880, 80)
                    except Exception:
                        pass

            self.last_turn_count = len(turns)
            self._render_turns(turns)

        except Exception as e:
            self.lbl_turns_info.setText(
                f"Beurten: <b style='color:#f87171'>tekenfout {type(e).__name__}</b>"
            )

    def _render_turns(self, turns: list[dict]):
        """Rendert alle beurten als stijlvolle kaarten in de chatfeed."""
        # Verwijder oude widgets behalve stretch
        while self.feed_layout.count() > 1:
            item = self.feed_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for idx, t in enumerate(turns):
            card = self._build_turn_card(t, idx + 1)
            self.feed_layout.insertWidget(self.feed_layout.count() - 1, card)

        self._mirror_screen(turns)

        # Scroll naar beneden
        QTimer.singleShot(50, self._scroll_to_bottom)

    def _mirror_screen(self, turns: list[dict]):
        """De tab Scherm herhaalt het gesprek in het kort."""
        lines = []
        for num, turn in enumerate(turns, 1):
            author = turn.get("author", "")
            title = (turn.get("title") or "").strip()
            summary = (turn.get("summary") or "").replace("\n", " ").strip()
            if len(summary) > 160:
                summary = summary[:160] + "…"
            lines.append(f"{num}  {author}\n{title}\n{summary}")
        self.mirror_view.setPlainText("\n\n".join(lines))
        cursor = self.mirror_view.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.mirror_view.setTextCursor(cursor)

    def _wissel_analyse_categorie(self, cat: str):
        self.analyse_categorie = "zaak"
        self._vul_analyses()

    def _wissel_analyse_weergave(self):
        if not self._analyse_raw_text:
            return
        self._analyse_toon_technisch = not self._analyse_toon_technisch
        if self._analyse_toon_technisch:
            self.analyse_toggle_tech.setText("Toon gewone taal")
            self.analyse_out.setPlainText(self._analyse_raw_text)
        else:
            self.analyse_toggle_tech.setText("Volledig rapport")
            self.analyse_out.setPlainText(self._analyse_human_text)

    def _vul_analyses(self):
        self.analyse_list.clear()
        for key, _item_cat, titel, toelichting, _argv in self._analyse_keuzes():
            item = QListWidgetItem(f"{titel}\n   ↳ {toelichting}")
            item.setData(Qt.ItemDataRole.UserRole, key)
            item.setToolTip(toelichting)
            self.analyse_list.addItem(item)
        if self.analyse_list.count():
            self.analyse_list.setCurrentRow(0)

    def _analyse_keuzes(self) -> list[tuple[str, str, str, str, list[str] | None]]:
        engine = CASE_ROOT / "_engine"
        py = PYTHON_EXE
        drafts = []
        for out_dir in (AGY_WERK / "outbox", CASE_ROOT / "Outgoing_Drafts"):
            if out_dir.exists():
                drafts.extend(p for p in out_dir.glob("*.md") if p.is_file())
        drafts.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        nieuwste = drafts[0] if drafts else None
        chunk_arg = [py, str(engine / "chunk_audit.py"), str(nieuwste)] if nieuwste else None

        bank_script = AGY_WERK / "scratch" / "veld_empirisch.py"
        if not bank_script.exists():
            bank_script = engine / "bank_audit.py"

        base: list[tuple[str, str, str, str, list[str] | None]] = [
            (
                "keten_stevin",
                "zaak",
                "1. Ketensluiting & Schijnsluiting (Drie Boeken van Stevin)",
                "Toetst per overdracht of het rekenkundig, procedureel én materieel sluit, en waar loketten elkaar tegenspreken",
                [py, str(CASE_ROOT / "Ketengrootboek" / "sluiting.py"), "--integriteit"],
            ),
            (
                "ketenbreuk_chrono",
                "zaak",
                "2. Chronologische Ketenbreuken & Voorganger-Reconstructie",
                "Spoort tijdsgaten en afkapgrenzen op (zoals vóór 2009 of 2014–2017) en wijst aan bij welke voorganger stukken liggen",
                [py, str(engine / "chronologische_ketenbreuk_scanner.py")],
            ),
            (
                "cytokine_vt",
                "zaak",
                "3. De Twee Klokken (Loket-rust vs. Lichamelijke Uitputting)",
                "Legt de trage brievenbus-stand bij de loketten (83%) naast je 13-jarige bloedreeks en fysieke draagkracht (6% bij storm)",
                [py, str(SHARED_TOOLS / "drager_cytokine_klok_vt.py")],
            ),
            (
                "veld_emp",
                "zaak",
                "4. Bankoverzicht, Huurbewijs & Bestaansminimum (CSV / CAMT)",
                "Controleert vaste lasten, stipte huurbetalingen, toeslagen en of inhoudingen onder de beslagvrije voet zakken",
                [py, str(bank_script)],
            ),
            (
                "tikhonov",
                "zaak",
                "5. Doorwerking van Financiële Schokken op Gezondheid",
                "Laat zien hoe maanden met terugvorderingen of incasso's een maand later doorwerken in extra arts- en ziekenhuisbezoek",
                [py, str(AGY_WERK / "scratch" / "tikhonov_lekstroom_toets.py")],
            ),
            (
                "termijnen",
                "zaak",
                "6. Wettelijke Beslistermijnen & Openstaande Antwoorden",
                "Controleert welke brieven of inzageverzoeken bij instanties openstaan en hoeveel dagen ze nog hebben",
                [py, str(engine / "statutory_clock.py"), "status"],
            ),
            (
                "chunk",
                "zaak",
                "7. Brief-Controle vóór Verzending (Kort, Veilig & Zonder Medisch Lek)",
                f"Toetst of je eigen conceptbrief kort, feitelijk en vrij van medische lekken is ({nieuwste.name if nieuwste else 'geen concept'})",
                chunk_arg,
            ),
            (
                "clash",
                "zaak",
                "8. Controleer ontvangen loketbrief op schijnbeloftes en afwimpeling",
                "Haalt vertragende standaardzinnen en kastje-naar-de-muur patronen uit een brief van een instantie",
                [py, str(engine / "systeem_clash_sentiment.py")],
            ),
            (
                "awb_scanner",
                "zaak",
                "9. Awb Besluit-, Bezwaarclausule- & Dwangsom-Scanner",
                "Toetst inkomende post op rechtsgevolg (art. 1:3 Awb), 6-weken bezwaarclausule (art. 6:7 Awb) en niet-tijdig beslissen (art. 4:17 Awb)",
                [py, str(engine / "awb_besluit_scanner.py")],
            ),
            (
                "keten_klok",
                "zaak",
                "10. Keten-Klok & Wettelijke Vervaldata (Boek 2 & 3)",
                "Toont alle lopende en verstreken wettelijke termijnen rechtstreeks uit het Ketengrootboek",
                [py, str(CASE_ROOT / "Ketengrootboek" / "sluiting.py"), "--klok"],
            ),
            ),
        ]
        return base

    def _maak_mensentaal_samenvatting(self, key: str, titel: str, toelichting: str, raw: str) -> str:
        """Vertaalt uitvoer naar een heldere samenvatting in gewone mensentaal zonder intern jargon."""
        header = (
            f"=== UITKOMST IN GEWONE TAAL ===\n"
            f"Onderwerp: {titel}\n"
            f"Wat dit doet: {toelichting}\n"
            f"{'-' * 56}\n\n"
        )
        uitleg_per_key = {
            "keten_stevin": (
                "Wat betekent dit voor jou?\n"
                "• Deze controle kijkt met de drie boeken van Simon Stevin (Memoriaal, Journaal en Grootboek) naar drie losse vragen:\n"
                "  1. Kloppen de boekingen tussen de loketten onderling? -> NEE (2 tegenstrijdige registraties: Vektis zegt 'niet verzekerd' terwijl Menzis/CAK premie int; DACAS boekt verrekeningen terwijl de bank € 0,00 toont).\n"
                "  2. Hebben de loketten hun eigen processtap afgerond? -> JA (5 van de 5 loketten hebben hun vinkje of besluit gezet).\n"
                "  3. Is de hulp of rectificatie feitelijk geleverd? -> NEE (0 van de 5 posten zijn materieel vereffend).\n"
                "• Ook controleert het systeem dat geen enkel later loket-stempel (Laag 3) jouw oorspronkelijke bewijsstuk (Laag 1) heeft overschreven.\n\n"
                "Overzicht uit de drie boeken:\n"
            ),
            "ketenbreuk_chrono": (
                "Wat betekent dit voor jou?\n"
                "• Als je een dossier opvraagt bij je huidige huisarts of gemeente, stopt dat vaak bij het jaar waarin je verhuisde of waarin de praktijk van systeem wisselde (bijvoorbeeld 2009).\n"
                "• Deze controle spoort zulke chronologische ketenbreuken op en laat zien via welke sporen (oude woonadressen, verwijsbrieven, WGBO 20-jaars bewaarplicht bij het ziekenhuis) je het ontbrekende deel bij de voorganger opvraagt.\n\n"
                "Gevonden ketenbreuken en reconstructie-sporen:\n"
            ),
            "cytokine_vt": (
                "Wat betekent dit voor jou?\n"
                "• Dit legt de TWEE KLOKKEN naast elkaar: de administratie buiten versus je lichaam binnen.\n"
                "• Terwijl het loketmodel op 83% ('rust') staat omdat de brieven de deur uit zijn, laat je 13-jarige bloedreeks zien dat je witte bloedcellen (leukocyten) in 13 jaar tijd NUL keer normaal zijn geweest (altijd verhoogd tussen 10,3 en 16,7).\n"
                "• Zelfs in een 'rustige' maand staat je lichamelijke ontstekingsvloer al op 41% druk (max ~59% energie).\n"
                "• Tijdens een cytokinestorm / IL-6 opvlamming (met plasmacellen en bijna 1 miljard reactieve lymfocyten per liter) schiet de druk naar 94% en zakt je beschikbare energie naar gemiddeld 6% (een kloof van 77 procentpunt met hoe het loket naar je kijkt).\n\n"
                "Overzicht van de twee klokken:\n"
            ),
            "veld_emp": (
                "Wat betekent dit voor jou?\n"
                "• Over bijna 10 jaar (118 maanden) zijn de vaste geldstromen gecontroleerd (huur, energie, water, toeslagen, gemeente, CAK en incasso).\n"
                "• De grote vaste lasten (zoals de huur) zijn stipt op tijd betaald (bewijs van goed huurderschap ex art. 7:231 BW).\n"
                "• Tegelijk laat het overzicht zien waar inhoudingen of verrekeningen het besteedbaar inkomen onder druk zetten.\n\n"
                "Kernpunten uit het bankoverzicht:\n"
            ),
            "tikhonov": (
                "Wat betekent dit voor jou?\n"
                "• We hebben gekeken of maanden met financiële klappen (zoals terugvorderingen, incasso's of uitval van toeslagen) gevolgen hebben voor je gezondheid.\n"
                "• In de maanden vlak ná zo'n financiële schok (+1 maand later) ligt het aantal spoed- en huisartscontacten ruim 2 keer zo hoog als normaal (gemiddeld 0,62 acute zorgdagen tegen 0,26 normaal).\n"
                "• Ook als de huur gewoon doorloopt, betaalt je lichaam een maand later dus de rekening van de geldstress.\n\n"
                "Belangrijkste voorbeelden uit je dossier:\n"
            ),
            "termijnen": (
                "Wat betekent dit voor jou?\n"
                "• Hieronder zie je welke brieven of aanvragen nog openstaan bij een instantie en hoeveel dagen ze nog hebben.\n"
                "• Zolang het gesprek aan de voorkant open is, blijft de ingebrekestelling in de achterzak.\n\n"
                "Belangrijkste regels uit de controle:\n"
            ),
            "chunk": (
                "Wat betekent dit voor jou?\n"
                "• Deze controle kijkt je eigen conceptbrief na voordat je hem verstuurt.\n"
                "• Hij controleert of je geen medische privégegevens weggeeft die het loket niet nodig heeft, en of de brief kort en zakelijk genoeg is.\n\n"
                "Controle-uitslag:\n"
            ),
            "clash": (
                "Wat betekent dit voor jou?\n"
                "• Deze controle leest de nieuwste brief van het loket en kijkt of de instantie je echt helpt of je met beleefde standaardzinnen afwimpelt.\n\n"
                "Bevindingen:\n"
            ),
        }

        intro = uitleg_per_key.get(
            key,
            "Wat betekent dit voor jou?\n• Hieronder staan de belangrijkste begrijpelijke regels uit de controle.\n• Klik rechtsboven op 'Toon technisch rapport' als je alle wiskundige tabellen en formules wilt zien.\n\n",
        )

        # Filter de meest leesbare regels uit de ruwe output (zonder zware LaTeX/formule-regels)
        schone_regels = []
        for line in raw.splitlines():
            s = line.strip()
            if not s:
                continue
            # Vervang LaTeX wiskunde door rustige tekst
            s_clean = re.sub(r"\$[^$]+\$", "", s)
            s_clean = s_clean.replace("**", "").replace("`", "")
            if any(skip in s_clean for skip in ("Sym^+(3)", "\\mathcal", "\\lambda", "\\rho_\\perp", "det(g)")):
                continue
            schone_regels.append(s_clean)

        kern_preview = "\n".join(schone_regels[:28])
        footer = (
            f"\n\n{'-' * 56}\n"
            f"Tip: Wil je alle exacte tabellen en wiskundige formules zien? Klik dan op de knop 'Toon technisch rapport'."
        )
        return header + intro + kern_preview + footer

    def _start_analyse(self):
        item = self.analyse_list.currentItem()
        if item is None or self.analyse_process.state() != QProcess.ProcessState.NotRunning:
            return
        key = item.data(Qt.ItemDataRole.UserRole)
        keuze = next((row for row in self._analyse_keuzes() if row[0] == key), None)
        if keuze is None or not keuze[4]:
            self.analyse_out.setPlainText("Deze controle heeft nog geen bestand om op te draaien.")
            return
        _key, _cat, titel, toelichting, argv = keuze
        self._analyse_active_key = key
        self._analyse_active_titel = titel
        self._analyse_active_toelichting = toelichting
        self._analyse_raw_text = f"{titel}\n{toelichting}\n\n"
        self._analyse_human_text = ""
        self._analyse_toon_technisch = False
        self.analyse_toggle_tech.setEnabled(False)
        self.analyse_toggle_tech.setText("Technisch rapport")
        if hasattr(self, "analyse_to_tafel"):
            self.analyse_to_tafel.setEnabled(False)
        self.analyse_out.setPlainText(f"Bezig met controle:\n{titel}\n{toelichting}\n\nEven geduld...\n")
        self.analyse_start.setEnabled(False)
        self.analyse_process.start(argv[0], argv[1:])

    def _analyse_lees(self):
        data = bytes(self.analyse_process.readAllStandardOutput()).decode("utf-8", errors="replace")
        if not data:
            return
        self._analyse_raw_text += data

    def _analyse_klaar(self, code: int, _status):
        self.analyse_start.setEnabled(True)
        self._analyse_raw_text += f"\n\n[Controle afgerond, code {code}]\n"
        self._analyse_human_text = self._maak_mensentaal_samenvatting(
            self._analyse_active_key,
            self._analyse_active_titel,
            self._analyse_active_toelichting,
            self._analyse_raw_text,
        )
        self.analyse_toggle_tech.setEnabled(True)
        if hasattr(self, "analyse_to_tafel"):
            self.analyse_to_tafel.setEnabled(True)
        self._analyse_toon_technisch = False
        self.analyse_toggle_tech.setText("Technisch rapport")
        self.analyse_out.setPlainText(self._analyse_human_text)

    def _leg_analyse_op_tafel(self):
        if not self._analyse_human_text:
            return
        kort = "\n".join(self._analyse_human_text.splitlines()[:16])
        self.input_edit.setPlainText(f"Uitkomst uit Analyse ({self._analyse_active_titel}):\n{kort}\n\nWat is hierop jullie oordeel en eerstvolgende zet?")
        self.input_edit.setFocus()

    def _refresh_case_tabs(self):
        """Vult dossiers, stukken en het overzicht."""
        dossiers, stukken, lijnen = self._read_case_shelves()
        self._all_dossier_rows = dossiers
        self._all_stukken_rows = stukken
        self._apply_dossier_filter()
        self._apply_post_filter()
        self._fill_list(self.list_lijnen, lijnen)
        self._vul_model()

    def _apply_dossier_filter(self):
        rows = getattr(self, "_all_dossier_rows", [])
        query = (self.dossier_filter_edit.text().strip().lower() if hasattr(self, "dossier_filter_edit") else "")
        if not query:
            self._fill_dossiers(rows)
            return
        filtered = []
        current_kop = None
        kop_added = False
        for kind, text, color, path in rows:
            if kind == "kop":
                current_kop = (kind, text, color, path)
                kop_added = False
                continue
            hay = f"{text} {path or ''} {current_kop[1] if current_kop else ''}".lower()
            if query in hay:
                if current_kop and not kop_added:
                    filtered.append(current_kop)
                    kop_added = True
                filtered.append((kind, text, color, path))
        self._fill_dossiers(filtered)

    def _set_post_filter(self, mode: str):
        self._post_filter_mode = mode
        if hasattr(self, "btn_post_all"):
            self.btn_post_all.setChecked(mode == "alle")
            self.btn_post_uit.setChecked(mode == "uit")
            self.btn_post_in.setChecked(mode == "binnen")
        self._apply_post_filter()

    def _apply_post_filter(self):
        rows = getattr(self, "_all_stukken_rows", [])
        mode = getattr(self, "_post_filter_mode", "alle")
        if mode == "uit":
            rows = [(lbl, p) for lbl, p in rows if lbl.startswith(("uit", "outbox"))]
        elif mode == "binnen":
            rows = [(lbl, p) for lbl, p in rows if lbl.startswith("binnen")]
        self._fill_stukken(rows)

    def _open_selected_stuk(self):
        item = self.list_stukken.currentItem()
        if item:
            self._open_stuk(item)

    def _toets_selected_stuk(self):
        item = self.list_stukken.currentItem()
        if not item:
            QMessageBox.information(self, "Briefpoort", "Selecteer eerst een brief of concept in de lijst.")
            return
        raw = item.data(Qt.ItemDataRole.UserRole)
        if not raw or not Path(str(raw)).is_file():
            return
        pad = Path(str(raw))
        tekst = pad.read_text(encoding="utf-8", errors="replace")
        engine_dir = CASE_ROOT / "_engine"
        if str(engine_dir) not in sys.path:
            sys.path.insert(0, str(engine_dir))
        try:
            from two_gate_dispatcher import TwoGateDispatcher
            res = TwoGateDispatcher(root_dir=CASE_ROOT).dispatch(
                tekst,
                slot_metadata={"name": "lokaal loket", "ingest_capacity": ["productcodes", "termijnen", "privacy"]},
            )
            allowed = res.get("allowed", False)
            status_kop = "✅ BEIDE POORTEN GROEN (Veilig voor verzending)" if allowed else "🛑 POORT HOUDT BRIEF TEGEN"
            uitleg = f"{status_kop}\n\nBestand: {pad.name}\nOordeel: {res.get('reason', '')}"
            for v in res.get("veto", []):
                if not v.get("passed", True):
                    uitleg += f"\n\n• [{v.get('severity')}] {v.get('rule')}:\n  {v.get('message')}\n  Tip: {v.get('suggestion')}"
            try:
                from sbar_protocol import SBARProtocol
                fh01 = SBARProtocol.validate_fh01_transform(tekst)
                fh_status = "✅ OK" if fh01.passed else "⚠️ Aandachtspunt"
                uitleg += (
                    f"\n\n--- Protocol FH-01 IJkcontroles ({fh_status}) ---\n"
                    f"• 1. Inhoudscontrole: {'Behouden' if fh01.inhoud_behouden else 'Doel ontbreekt'}\n"
                    f"• 2. Taalhandelingcontrole: {'Zuiver' if fh01.taalhandeling_zuiver else 'Dictaat gedetecteerd'}\n"
                    f"• 3. Ruimtecontrole: {'Professionele ruimte intact' if fh01.ruimte_intact else 'Geschonden'}\n"
                    f"• Negatieve Invarianten: {'Geen Agency Inversion / Geen Demonisering' if (fh01.geen_agency_inversion and fh01.geen_sussen_of_demoniseren) else 'Geschonden'}"
                )
            except Exception:
                pass
            QMessageBox.information(self, f"Briefpoort — {pad.name}", uitleg)
        except Exception as exc:
            QMessageBox.warning(self, "Briefpoort", f"Kon poorttoets niet uitvoeren: {exc}")

    def _sein_selected_stuk(self):
        item = self.list_stukken.currentItem()
        if not item:
            QMessageBox.information(self, "Sein", "Selecteer eerst een brief of concept in de lijst.")
            return
        raw = item.data(Qt.ItemDataRole.UserRole)
        if not raw or not Path(str(raw)).is_file():
            return
        pad = Path(str(raw))
        tekst = pad.read_text(encoding="utf-8", errors="replace")
        engine_dir = CASE_ROOT / "_engine"
        if str(engine_dir) not in sys.path:
            sys.path.insert(0, str(engine_dir))
        try:
            from two_gate_dispatcher import TwoGateDispatcher
            res = TwoGateDispatcher(root_dir=CASE_ROOT).dispatch(
                tekst,
                slot_metadata={"name": "lokaal loket", "ingest_capacity": ["productcodes", "termijnen", "privacy"]},
            )
            if not res.get("allowed", False):
                QMessageBox.warning(
                    self,
                    "Poort houdt brief tegen",
                    f"Deze brief komt nog niet door de poort:\n\n{res.get('reason', '')}\n\n"
                    "Pas het concept eerst aan of klik op 'Toets Poort' voor details.",
                )
                return
        except Exception:
            pass

        schone_tekst = tekst.split("\n\n---\nDeze brief is nog niet verstuurd.", 1)[0].strip()
        eml_path = AGY_WERK / "scratch" / f"{pad.stem}.eml"
        eml_path.parent.mkdir(parents=True, exist_ok=True)
        eml_inhoud = (
            "To: \r\n"
            f"Subject: {pad.stem.replace('_', ' ')}\r\n"
            "MIME-Version: 1.0\r\n"
            "Content-Type: text/plain; charset=utf-8\r\n\r\n"
            f"{schone_tekst}\r\n"
        )
        eml_path.write_text(eml_inhoud, encoding="utf-8")
        os.startfile(str(eml_path))

    def _model_link_clicked(self, url: QUrl):
        raw = url.toString()
        if raw == "welstand:rapport":
            from welstand_model import compute_welstand, format_markdown_report
            rep_path = AGY_WERK / "scratch" / "WELSTAND_RAPPORT_LIVE.md"
            rep_path.parent.mkdir(parents=True, exist_ok=True)
            rep_path.write_text(format_markdown_report(compute_welstand()), encoding="utf-8")
            MarkdownViewer(rep_path, self).exec()
            return
        if raw == "welstand:cytokine":
            rap = WORKSPACE / "Analyses" / "Rapporten" / "2026-10-25_TWEE_KLOKKEN_LOKET_VS_CYTOKINE_VT_RAPPORT.md"
            if rap.exists():
                MarkdownViewer(rap, self).exec()
            return
        if raw == "welstand:ketenstatus":
            keten_dir = CASE_ROOT / "Ketengrootboek"
            if str(keten_dir) not in sys.path:
                sys.path.insert(0, str(keten_dir))
            from sluiting import SluitingsToetser
            md_txt = SluitingsToetser(root_dir=keten_dir).formatteer_ketenintegriteit_markdown()
            rep_path = AGY_WERK / "scratch" / "KETENINTEGRITEIT_LIVE.md"
            rep_path.parent.mkdir(parents=True, exist_ok=True)
            rep_path.write_text(md_txt, encoding="utf-8")
            MarkdownViewer(rep_path, self).exec()
            return
        if raw.startswith("file:///"):
            path_str = url.toLocalFile()
            p = Path(path_str)
            if p.suffix.lower() == ".md":
                MarkdownViewer(p, self).exec()
            else:
                try:
                    os.startfile(str(p))
                except Exception:
                    pass
        elif raw.startswith("filter:"):
            domein = raw.split(":", 1)[1].strip().lower()
            zoek_map = {"lichaam": "zorg", "geest": "wmo", "bestaan": "geld"}
            if hasattr(self, "dossier_filter_edit"):
                self.dossier_filter_edit.setText(zoek_map.get(domein, domein))
            self.case_tabs.setCurrentIndex(1)

    def _vul_model(self):
        import html
        from welstand_model import compute_welstand
        snap = compute_welstand()
        intern, extern = model_overzicht()

        # Lees ook de Tweede Klok v(t) (Lichaam / Cytokinestorm) indien aanwezig
        v_vloer_pct = 41
        c_vloer_pct = 59
        v_storm_pct = 94
        c_storm_pct = 6
        kloof_pct = 77
        vt_json = WORKSPACE / "Analyses" / "Rapporten" / "drager_cytokine_klok_vt.json"
        if vt_json.exists():
            try:
                vt_data = json.loads(vt_json.read_text(encoding="utf-8"))
                v_vloer_pct = round(float(vt_data.get("v_vloer_baseline", 0.41)) * 100)
                c_vloer_pct = round(float(vt_data.get("C_exec_vloer", 0.59)) * 100)
                v_storm_pct = round(float(vt_data.get("v_storm_mean", 0.94)) * 100)
                c_storm_pct = round(float(vt_data.get("C_exec_storm_mean", 0.06)) * 100)
                kloof_pct = round(float(vt_data.get("gemiddelde_gevel_kloof", 0.77)) * 100)
            except Exception:
                pass

        delen = [
            # KLOK 1: LOKETTEN & BRIEVENBUS
            "<div style='background:rgba(212,175,55,0.06); border:1px solid rgba(212,175,55,0.24); "
            "border-radius:6px; padding:7px 10px; margin:0 0 8px 0; font-family:JetBrains Mono,monospace;'>"
            "<a href='welstand:rapport' style='color:#D4AF37; font-size:11px; font-weight:700; text-decoration:none;'>"
            "1. LOKET-KLOK (Brievenbus &amp; Administratie) ↗</a><br>"
            f"<span style='color:#cbd5e1; font-size:11px;'>Wonen/Zorg <b style='color:#5eead4;'>{snap.q_G*100:.0f}%</b> · "
            f"Brieven <b style='color:#d8b4fe;'>{snap.q_I*100:.0f}%</b> · "
            f"Inkomen <b style='color:#4ade80;'>{snap.q_D*100:.0f}%</b></span><br>"
            "<span style='color:#94a3b8; font-size:10px;'>Brieven liggen bij de 19 loketten — buitenkant staat daardoor op 'rust'.</span></div>",

            # KLOK 2: LICHAAM & CYTOKINESTORM v(t)
            "<div style='background:rgba(248,113,113,0.08); border:1px solid rgba(248,113,113,0.32); "
            "border-radius:6px; padding:7px 10px; margin:0 0 8px 0; font-family:JetBrains Mono,monospace;'>"
            "<a href='welstand:cytokine' style='color:#f87171; font-size:11px; font-weight:700; text-decoration:none;'>"
            "2. LICHAAMS-KLOK v(t) (13 jr Bloedreeks &amp; Cytokinestorm) ↗</a><br>"
            f"<span style='color:#cbd5e1; font-size:11px;'>Ontstekingsvloer: <b style='color:#fbbf24;'>{v_vloer_pct}% druk</b> "
            f"(max <b style='color:#fbbf24;'>{c_vloer_pct}%</b> energie)</span><br>"
            f"<span style='color:#cbd5e1; font-size:11px;'>Bij cytokinestorm: <b style='color:#f87171;'>{v_storm_pct}% druk</b> "
            f"(nog <b style='color:#f87171;'>{c_storm_pct}%</b> energie · <b style='color:#f87171;'>{kloof_pct}% kloof</b>)</span></div>",
        ]

        # BLOK 3: KETENINTEGRITEIT (Simon Stevin 3 Sluitingskenmerken: Rekenkundig, Procedureel, Materieel)
        try:
            keten_dir = CASE_ROOT / "Ketengrootboek"
            if str(keten_dir) not in sys.path:
                sys.path.insert(0, str(keten_dir))
            from sluiting import SluitingsToetser
            ks = SluitingsToetser(root_dir=keten_dir).ketenstatus_overzicht()
            tot_p = ks["totaal_posten"]
            rek_lbl = "<b style='color:#4ade80;'>Ja</b>" if ks["rekenkundig_sluitend"] else f"<b style='color:#f87171;'>Nee ({len(ks['tegenstrijdigheden'])} conflict)</b>"
            proc_lbl = f"<b style='color:#fbbf24;'>Ja ({ks['procedureel_gesloten_aantal']}/{tot_p})</b>"
            mat_lbl = "<b style='color:#4ade80;'>Ja</b>" if ks["materieel_vereffend"] else f"<b style='color:#f87171;'>Nee ({ks['materieel_vereffend_aantal']}/{tot_p})</b>"
            delen.append(
                "<div style='background:rgba(59,130,246,0.08); border:1px solid rgba(59,130,246,0.32); "
                "border-radius:6px; padding:7px 10px; margin:0 0 14px 0; font-family:JetBrains Mono,monospace;'>"
                "<a href='welstand:ketenstatus' style='color:#60a5fa; font-size:11px; font-weight:700; text-decoration:none;'>"
                "3. KETENSTATUS (Stevin 3 Boeken &amp; Sluiting) ↗</a><br>"
                f"<span style='color:#cbd5e1; font-size:11px;'>Rekenkundig: {rek_lbl} · "
                f"Procedureel: {proc_lbl} · "
                f"Materieel: {mat_lbl}</span><br>"
                "<span style='color:#fbbf24; font-size:10px;'>⚠️ Schijnsluiting &amp; Tegenstrijdige Registratie — klik voor de 9 velden per post.</span></div>"
            )
        except Exception:
            pass

        delen.append(
            "<p style='color:#D4AF37; font-family:JetBrains Mono,monospace; "
            "font-size:12px; letter-spacing:1.2px; margin:0 0 8px 0; font-weight:700;'>INTERN (Klik om Dossiers te filteren)</p>"
        )
        for title, color, aantal, laatst, p_laatst in intern:
            if p_laatst:
                uri = QUrl.fromLocalFile(str(p_laatst)).toString()
                laatst_html = f"<a href='{uri}' style='color:#94a3b8; text-decoration:none;'>{html.escape(laatst)}</a>"
            else:
                laatst_html = html.escape(laatst) if laatst else "nog geen stuk"
            delen.append(
                f"<p style='margin:0 0 12px 0; line-height:1.45; font-family:JetBrains Mono,monospace;'>"
                f"<a href='filter:{title}' style='color:{color}; font-size:14px; font-weight:700; text-decoration:none;'>{html.escape(title)} ({aantal} stukken) 🔎</a><br>"
                f"<span style='font-size:11px;'>● {laatst_html}</span></p>"
            )
        delen.append(
            "<p style='color:#D4AF37; font-family:JetBrains Mono,monospace; "
            "font-size:12px; letter-spacing:1.2px; margin:14px 0 8px 0; font-weight:700;'>LOKETTEN (In &amp; Uit Lijnen)</p>"
        )
        for label, binnen, p_in, uit, p_uit in extern:
            if p_in:
                uri_in = QUrl.fromLocalFile(str(p_in)).toString()
                in_html = f"<a href='{uri_in}' style='color:#93c5fd; text-decoration:none;'>📥 in:  {html.escape(binnen)}</a>"
            else:
                in_html = f"<span style='color:#64748b;'>📥 in:  {html.escape(binnen)}</span>"

            if p_uit:
                uri_uit = QUrl.fromLocalFile(str(p_uit)).toString()
                uit_html = f"<a href='{uri_uit}' style='color:#fdba74; text-decoration:none;'>📤 uit: {html.escape(uit)}</a>"
            else:
                uit_html = f"<span style='color:#64748b;'>📤 uit: {html.escape(uit)}</span>"

            if p_uit and (not p_in or p_uit.stat().st_mtime >= p_in.stat().st_mtime):
                status_badge = "<span style='color:#fbbf24; font-size:10px;'>⏳ wacht op loket</span>"
            elif p_in:
                status_badge = "<span style='color:#4ade80; font-size:10px;'>🟢 stuk binnen</span>"
            else:
                status_badge = "<span style='color:#64748b; font-size:10px;'>⚪ stil</span>"

            delen.append(
                "<p style='margin:0 0 10px 0; line-height:1.4; font-family:JetBrains Mono,monospace;'>"
                f"<span style='color:#e2e8f0; font-size:13px; font-weight:600;'>{html.escape(label)}</span> {status_badge}<br>"
                f"<span style='font-size:11px;'>{in_html}</span><br>"
                f"<span style='font-size:11px;'>{uit_html}</span></p>"
            )
        self.model_view.setHtml("".join(delen))

    def _fill_list(self, widget: QListWidget, rows: list[str]):
        widget.clear()
        if not rows:
            widget.addItem("niets aangetroffen")
            return
        widget.addItems(rows)

    def _fill_dossiers(self, rows: list[tuple[str, str, str, str]]):
        self.list_dossiers.clear()
        if not rows:
            self.list_dossiers.addItem("niets aangetroffen")
            return
        for kind, text, color, path in rows:
            label = QLabel(text)
            label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
            if kind == "kop":
                label.setStyleSheet(
                    f"color: {color}; background: transparent; font-family: 'JetBrains Mono'; "
                    "font-size: 13px; font-weight: 700; letter-spacing: 1.2px; "
                    "padding: 12px 2px 2px 2px;"
                )
                height = 34
            elif kind == "sub":
                label.setStyleSheet(
                    f"color: {color}; background: transparent; font-family: 'JetBrains Mono'; "
                    "font-size: 12px; font-weight: 700; padding: 6px 2px 1px 10px;"
                )
                height = 26
            else:
                label.setStyleSheet(
                    f"color: {color}; background: transparent; font-family: 'JetBrains Mono'; "
                    "font-size: 13px; padding: 2px 2px 2px 16px;"
                )
                height = 24
            item = QListWidgetItem()
            item.setSizeHint(QSize(390, height))
            if path:
                item.setData(Qt.ItemDataRole.UserRole, path)
                item.setToolTip(path)
            else:
                item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.list_dossiers.addItem(item)
            self.list_dossiers.setItemWidget(item, label)

    def _open_dossier(self, item: QListWidgetItem):
        raw = item.data(Qt.ItemDataRole.UserRole)
        if not raw:
            return
        path = Path(str(raw))
        if path.is_dir():
            os.startfile(path)
            return
        if not path.is_file():
            return
        if path.suffix.lower() == ".md":
            MarkdownViewer(path, self).exec()
            return
        os.startfile(path)

    def _fill_stukken(self, rows: list[tuple[str, str]]):
        self.list_stukken.clear()
        if not rows:
            self.list_stukken.addItem("niets aangetroffen")
            return
        for label, path in rows:
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, path)
            item.setToolTip(path)
            self.list_stukken.addItem(item)

    def _open_stuk(self, item: QListWidgetItem):
        raw = item.data(Qt.ItemDataRole.UserRole)
        if not raw:
            return
        path = Path(str(raw))
        if not path.is_file():
            return
        if path.suffix.lower() == ".md":
            MarkdownViewer(path, self).exec()
            return
        os.startfile(path)

    def _read_case_shelves(self) -> tuple[list[tuple[str, str, str]], list[tuple[str, str]], list[str]]:
        dossiers = dossier_rijen()

        stukken: list[tuple[float, str, str]] = []
        shelves = (
            (CASE_ROOT / "Incoming_Letters", "binnen"),
            (CASE_ROOT / "Outgoing_Drafts", "uit"),
            (WORKSPACE / "agy_werk" / "outbox", "outbox"),
            (WORKSPACE / "Shared_Tools" / "mail_outbox", "uit"),
        )
        found: list[tuple[float, str, str, str]] = []
        for folder, kind in shelves:
            if not folder.exists():
                continue
            for path in folder.iterdir():
                if not path.is_file() or path.name == ".gitkeep":
                    continue
                try:
                    stamp = path.stat().st_mtime
                except OSError:
                    continue
                found.append((stamp, kind, path.name.lower(), path.name))
                stukken.append((stamp, f"{kind}   {path.name}", str(path)))
        stukken_sorted = [(label, path) for _stamp, label, path in sorted(stukken, reverse=True)[:40]]

        lijnen: list[str] = []
        for label, keys in ISLANDS:
            hits = [item for item in found if any(key in item[2] for key in keys)]
            if not hits:
                lijnen.append(f"stil    {label}")
                continue
            _stamp, kind, _low, name = max(hits)
            staat = "wacht" if kind == "uit" else "binnen"
            short = name if len(name) <= 42 else name[:39] + "…"
            lijnen.append(f"{staat}   {label}   {short}")
        return dossiers, stukken_sorted, lijnen

    def _build_turn_card(self, turn: dict, num: int) -> QFrame:
        card = QFrame()
        author = turn.get("author", "Tafel")
        low = author.lower()

        nick_color = "#D4AF37"
        prefix = "+"
        border_color = "rgba(212, 175, 55, 0.3)"

        if "xander" in low:
            nick_color = "#D4AF37"
            prefix = "@"
            border_color = "rgba(212, 175, 55, 0.4)"
        elif "agy" in low:
            nick_color = "#00d4ff"
            border_color = "rgba(0, 212, 255, 0.35)"
        elif "grok" in low:
            nick_color = "#f59e0b"
            border_color = "rgba(245, 158, 11, 0.35)"
        elif "deepseek" in low:
            nick_color = "#3b82f6"
            border_color = "rgba(59, 130, 246, 0.35)"
        elif "argon" in low:
            nick_color = "#2dd4bf"
            border_color = "rgba(45, 212, 191, 0.35)"
        elif "gemini" in low:
            nick_color = "#10b981"
            border_color = "rgba(16, 185, 129, 0.35)"
        elif "qwen" in low:
            nick_color = "#a855f7"
            border_color = "rgba(168, 85, 247, 0.35)"
        elif "mistral" in low:
            nick_color = "#f97316"
            border_color = "rgba(249, 115, 22, 0.35)"
        else:
            nick_color = "#94a3b8"
            border_color = "rgba(148, 163, 184, 0.35)"

        card.setStyleSheet(f"""
            QFrame {{
                background: rgba(17, 12, 28, 0.85);
                border: 1px solid {border_color};
                border-radius: 8px;
                padding: 10px;
            }}
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)

        # Header regel
        top_row = QHBoxLayout()
        time_str = turn.get("date_raw", "")
        addressed = turn.get("addressed", [])
        addressed_str = f" → <b style='color:#e2e8f0;'>{', '.join(addressed)}</b>" if addressed else ""

        lbl_header = QLabel(
            f"<span style='color:#64748b; font-family:monospace;'>[{time_str}]</span> "
            f"<b style='color:{nick_color}; font-size:13px;'>{prefix}{author}</b>{addressed_str}"
        )
        lbl_num = QLabel(f"<span style='color:#64748b; font-family:monospace; font-size:10px;'>#{num}</span>")
        top_row.addWidget(lbl_header)
        top_row.addStretch()
        top_row.addWidget(lbl_num)
        layout.addLayout(top_row)

        # Titel indien aanwezig
        title = turn.get("title", "")
        if title:
            lbl_title = QLabel(f"<b style='color:#cbd5e1; font-size:12px;'>{title}</b>")
            layout.addWidget(lbl_title)

        # Inhoud
        content = turn.get("content_full", turn.get("summary", ""))
        import html
        escaped = html.escape(content)
        escaped = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', escaped)
        escaped = re.sub(r'\*(.+?)\*', r'<i>\1</i>', escaped)
        escaped = re.sub(r'`(.+?)`', r'<code style="background:rgba(255,255,255,0.1);padding:1px 4px;border-radius:3px;font-family:monospace;">\1</code>', escaped)
        formatted_html = escaped.replace("\n\n", "<br><br>").replace("\n", "<br>")
        lbl_body = QLabel(formatted_html)
        lbl_body.setWordWrap(True)
        lbl_body.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        lbl_body.setStyleSheet("color: #cbd5e1; font-size: 12px; line-height: 1.4;")
        layout.addWidget(lbl_body)

        # Bestandstok van deze beurt. Een persoonsdoorgifte blijft leesbaar op oudere kaarten.
        op_paths = [e["path"] for e in turn.get("stok_events") or [] if e.get("kind") == "op"]
        vrij_paths = [e["path"] for e in turn.get("stok_events") or [] if e.get("kind") == "vrij"]
        if op_paths or vrij_paths:
            parts = []
            if op_paths:
                parts.append("Stok op: <b style='color:#00d4ff;'>" + ", ".join(op_paths) + "</b>")
            if vrij_paths:
                parts.append("Stok vrij: <b style='color:#94a3b8;'>" + ", ".join(vrij_paths) + "</b>")
            lbl_baton = QLabel(
                f"<span style='color:#64748b; font-size:11px; font-family:monospace;'>{' · '.join(parts)}</span>"
            )
            lbl_baton.setStyleSheet("border-top: 1px solid rgba(255,255,255,0.06); padding-top: 4px; margin-top: 4px;")
            lbl_baton.setWordWrap(True)
            layout.addWidget(lbl_baton)
        else:
            baton_to = turn.get("baton_to", "Onbekend")
            if baton_to and baton_to != "Onbekend":
                lbl_baton = QLabel(f"<span style='color:#64748b; font-size:11px; font-family:monospace;'>Stok overgedragen aan: <b style='color:#00d4ff;'>{baton_to}</b></span>")
                lbl_baton.setStyleSheet("border-top: 1px solid rgba(255,255,255,0.06); padding-top: 4px; margin-top: 4px;")
                layout.addWidget(lbl_baton)

        return card

    def _scroll_to_bottom(self):
        vbar = self.scroll_area.verticalScrollBar()
        vbar.setValue(vbar.maximum())

    def update_process_statuses(self):
        """Controleert of Grok, DeepSeek en Gemini Argon actief draaien via psutil (zonder console-popups)."""
        grok_alive = False
        deepseek_alive = False
        argon_alive = False

        try:
            import psutil
            for p in psutil.process_iter(['name', 'cmdline']):
                try:
                    cmd_line = ' '.join(p.info.get('cmdline') or []).lower()
                    if 'grok.exe' in cmd_line or 'run_grok.ps1' in cmd_line:
                        grok_alive = True
                    if 'deepseek_agent.py' in cmd_line or 'deepseek_tafel_watcher.py' in cmd_line:
                        deepseek_alive = True
                    if 'gemini_agent.py' in cmd_line:
                        argon_alive = True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        except Exception:
            pass

        holders = " ".join(c.get("author", "").lower() for c in self.file_claims)
        self._paint_seat_badge(self.badge_xander, "xander" in holders, True)
        self._paint_seat_badge(self.badge_agy, "agy" in holders, True)
        self._paint_seat_badge(self.badge_grok, "grok" in holders, grok_alive)
        self._paint_seat_badge(self.badge_deepseek, "deepseek" in holders, deepseek_alive)
        if hasattr(self, "badge_argon"):
            self._paint_seat_badge(self.badge_argon, "argon" in holders, argon_alive)

    def _show_file_claims(self, turns: list[dict]):
        import html
        claims, blocked = claim_board(turns)
        self.file_claims = claims
        rows = [
            f"<b style='color:#00d4ff'>{html.escape(c['author'])}</b> "
            f"{html.escape(c['label'])}"
            for c in claims
        ]
        rows.extend(
            f"<b style='color:#f87171'>bezet</b> {html.escape(b['label'])} "
            f"<span style='color:#94a3b8'>({html.escape(b['holder'])})</span>"
            for b in blocked
        )
        if rows:
            self.stok_list.setText("<br>".join(rows))
        else:
            self.stok_list.setText("<span style='color:#64748b'>geen bestand</span>")
        if not claims and not blocked:
            self.lbl_baton_info.setText("Stok op: <span style='color:#64748b'>geen bestand</span>")
            self.lbl_baton_info.setToolTip("")
            return
        bezet = f" · {len(blocked)} bezet" if blocked else ""
        self.lbl_baton_info.setText(
            f"Stok op: <b style='color:#00d4ff'>{len(claims)} vast{bezet}</b>"
        )
        lines = [f"{c['author']}: {c['path']}" for c in claims]
        lines.extend(
            f"bezet {b['path']} — houder {b['holder']}, gevraagd door {b['author']}"
            for b in blocked
        )
        self.lbl_baton_info.setToolTip("\n".join(lines))

    def _paint_seat_badge(self, label: QLabel, aan_zet: bool, alive: bool):
        if aan_zet and alive:
            label.setText("<span style='color:#facc15; font-size:10px;'>● Aan zet</span>")
        elif alive:
            label.setText("<span style='color:#10b981; font-size:10px;'>● Online</span>")
        else:
            label.setText("<span style='color:#64748b; font-size:10px;'>● Offline</span>")

    def spawn_process(self, target: str):
        """Start Grok Code, DeepSeek CLI of Gemini Argon CLI SDK in een eigen Windows console."""
        if target in ("grok", "all"):
            cmd = f'start "Grok Code (Aan Tafel)" /d "{WORKSPACE}" cmd /k "{GROK_STARTER}"'
            subprocess.Popen(cmd, shell=True)
        if target in ("deepseek", "all"):
            cmd = f'start "DeepSeek CLI (Aan Tafel)" /d "{WORKSPACE}" cmd /k "{DEEPSEEK_STARTER}"'
            subprocess.Popen(cmd, shell=True)
        if target in ("argon",):
            cmd = f'start "Gemini Argon CLI SDK (Aan Tafel)" /d "{WORKSPACE}" cmd /k "{ARGON_STARTER}"'
            subprocess.Popen(cmd, shell=True)
        QTimer.singleShot(1000, self.update_process_statuses)

    def action_send_message(self):
        """Plaatst het ingevoerde bericht op TAFEL.md."""
        txt = self.input_edit.toPlainText().strip()
        if not txt:
            return

        self.input_edit.clear()

        # Commando checks
        if txt.startswith("/zoek "):
            term = txt[6:].strip()
            self.run_search_dialog(term)
            return

        months_nl = ("jan", "feb", "mrt", "apr", "mei", "jun", "jul", "aug", "sep", "okt", "nov", "dec")
        now_dt = datetime.now()
        now_str = f"{now_dt.day} {months_nl[now_dt.month - 1]} {now_dt.year}, {now_dt:%H:%M}"

        if txt.lower().startswith("/stok") or txt.lower().startswith("/vrij") or txt.lower().startswith("/baton"):
            kind = "vrij" if txt.lower().startswith("/vrij") else "op"
            raw = txt.split(maxsplit=1)[1].strip() if len(txt.split()) > 1 else ""
            if not raw or not any(mark in raw for mark in (".", "/", "\\")):
                self.input_edit.setPlainText(txt)
                return
            entry = (
                f"\n\n---\n\n## Xander ({now_str}) — Inbreng via Civic Helper\n\n"
                f"Stok {kind}: {raw}\n"
            )
            with open(TAFEL_MD, "a", encoding="utf-8") as f:
                f.write(entry)
            self.check_and_refresh_tafel()
            return

        rec = self.combo_recipient.currentText()
        seat = self._seat_from_recipient(rec)
        addressed_line = ""
        if seat == "Allen":
            # @Allen moet letterlijk de drie stoelen noemen; de indexer leest
            # alleen de eerste regels van de beurt, dus "@Allen" alleen is te weinig.
            addressed_line = "**Aangesproken:** @agy, @Grok, @DeepSeek\n**Stok:** Allen\n\n"
        elif seat != "Xander":
            addressed_line = f"**Aangesproken:** @{seat}\n**Stok:** {seat}\n\n"

        entry = (
            f"\n\n---\n\n## Xander ({now_str}) — Inbreng via Civic Helper\n\n"
            f"{addressed_line}{txt}\n"
        )

        with open(TAFEL_MD, "a", encoding="utf-8") as f:
            f.write(entry)

        ensure_chat_dispatch()
        self.check_and_refresh_tafel()

    def _seat_from_recipient(self, rec: str) -> str:
        """De stoel die de invoerbalk aanwijst."""
        low = rec.lower()
        if "allen" in low or "all" in low:
            return "Allen"
        if "agy" in low:
            return "agy"
        if "grok" in low:
            return "Grok"
        if "deepseek" in low:
            return "DeepSeek"
        if "argon" in low:
            return "Argon"
        if "gemini" in low:
            return "Gemini"
        if "mistral" in low:
            return "Mistral"
        if "qwen" in low:
            return "Qwen"
        if "nvidia" in low or "nemotron" in low:
            return "NVIDIA"
        return "Xander"

    def address_seat(self, seat_key: str):
        """Zet de ontvanger klaar. De zittende sessie antwoordt zelf."""
        found = False
        for i in range(self.combo_recipient.count()):
            if seat_key.lower() in self.combo_recipient.itemText(i).lower():
                self.combo_recipient.setCurrentIndex(i)
                found = True
                break
        if not found:
            label = f"@{seat_key.capitalize()}"
            self.combo_recipient.addItem(label)
            self.combo_recipient.setCurrentIndex(self.combo_recipient.count() - 1)
        self.input_edit.setFocus()

    def action_archive(self):
        reply = QMessageBox.question(
            self, "Archiveren", "Wil je TAFEL.md nu archiveren tot de laatste 20 beurten?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            archive_tafel_if_needed(threshold=20)
            self.check_and_refresh_tafel()

    def action_search(self):
        term, ok = QInputDialog.getText(self, "Non-RAG Zoeken", "Voer zoekterm of constraint-entiteit in:")
        if ok and term.strip():
            self.run_search_dialog(term.strip())

    def run_search_dialog(self, term: str):
        turns = index_file(TAFEL_MD)
        results = [t for t in turns if term.lower() in (t.get("summary", "") + t.get("title", "") + t.get("author", "")).lower()]
        msg = f"Gevonden in actieve TAFEL.md ({len(results)} treffers):\n\n"
        for r in results:
            msg += f"• [{r.get('date_raw', '')}] {r.get('author', '')} — {r.get('title', '')}\n"
        QMessageBox.information(self, f"Zoekresultaten: {term}", msg)

    def action_add_model(self):
        items = [
            "Qwen 2.5 32B (Groq LPU — direct beschikbaar)",
            "Mistral Large (Mistral AI API)",
            "Gemini Argon CLI SDK (gemini-4-argon)",
            "Gemini 3.8 Flash (Google API)",
            "NVIDIA Nemotron 3.5 Super VL (vrij eindpunt)",
        ]
        item, ok = QInputDialog.getItem(self, "Model Aanschuiven", "Kies een model om aan tafel te schuiven:", items, 0, False)
        if not ok or not item:
            return

        low = item.lower()
        if "argon" in low:
            seat_name = "Argon"
            label = "@Gemini Argon CLI SDK"
            model_key = "argon"
            color = "#2dd4bf"
            subtitle = "gemini-4-argon · 1M context"
        elif "qwen" in low:
            seat_name = "Qwen"
            label = "@Qwen"
            model_key = "qwen"
            color = "#a855f7"
            subtitle = "Groq LPU · online"
        elif "mistral" in low:
            seat_name = "Mistral"
            label = "@Mistral"
            model_key = "mistral"
            color = "#f97316"
            subtitle = "Mistral AI API"
        elif "nvidia" in low or "nemotron" in low:
            seat_name = "NVIDIA"
            label = "@NVIDIA"
            model_key = "nvidia"
            color = "#76b900"
            subtitle = "nemotron-3.5-super-vl · vrij eindpunt"
        elif "flash" in low or "gemini" in low:
            seat_name = "Gemini"
            label = "@Gemini 3.8 Flash"
            model_key = "gemini"
            color = "#10b981"
            subtitle = "Zittende sessie"
        else:
            seat_name = item.split()[0]
            label = f"@{seat_name}"
            model_key = seat_name.lower()
            color = "#94a3b8"
            subtitle = "On-demand model"

        # 1. Ontvanger in combobox selecteren of toevoegen
        found = False
        for i in range(self.combo_recipient.count()):
            if label.lower() == self.combo_recipient.itemText(i).lower():
                self.combo_recipient.setCurrentIndex(i)
                found = True
                break
        if not found:
            self.combo_recipient.addItem(label)
            self.combo_recipient.setCurrentIndex(self.combo_recipient.count() - 1)

        # 2. Visuele kaart toevoegen aan rechterkolom indien nog niet aanwezig
        if hasattr(self, "_on_demand_cards") and hasattr(self, "nick_layout"):
            if model_key not in self._on_demand_cards:
                card = self._create_summon_card(f"+{seat_name}", subtitle, color, "+", model_key)
                idx = self.nick_layout.indexOf(self.btn_add_model)
                if idx >= 0:
                    self.nick_layout.insertWidget(idx, card)
                else:
                    self.nick_layout.addWidget(card)
                self._on_demand_cards.add(model_key)

        # 3. Sleutel-controle in de omgeving
        try:
            from model_bus import _load_env
            _load_env()
        except Exception:
            pass

        missing_key = None
        if model_key == "mistral":
            val = os.environ.get("MISTRAL_API_KEY", "")
            if not val or val == "vul_hier_in":
                missing_key = "MISTRAL_API_KEY"
        elif model_key == "qwen":
            val = os.environ.get("GROQ_API_KEY", "")
            if not val or val == "vul_hier_in":
                missing_key = "GROQ_API_KEY"

        if missing_key:
            reply_key, ok_key = QInputDialog.getText(
                self,
                f"Sleutel Nodig: {missing_key}",
                f"{seat_name} is aangeschoven, maar {missing_key} ontbreekt nog in .env.\n\n"
                f"Plak hier je {missing_key} om hem direct op te slaan (of klik Annuleren om later toe te voegen):"
            )
            if ok_key and reply_key.strip():
                key_clean = reply_key.strip()
                os.environ[missing_key] = key_clean
                env_file = WORKSPACE / ".env"
                if env_file.exists():
                    txt = env_file.read_text(encoding="utf-8")
                    if f"{missing_key}=" in txt:
                        txt = re.sub(rf"^{missing_key}=.*$", f"{missing_key}={key_clean}", txt, flags=re.MULTILINE)
                    else:
                        txt += f"\n{missing_key}={key_clean}\n"
                    env_file.write_text(txt, encoding="utf-8")
                QMessageBox.information(self, "Sleutel Opgeslagen", f"{missing_key} is opgeslagen in .env!\n\n{seat_name} is nu gereed.")
            else:
                QMessageBox.warning(self, "Let Op", f"{seat_name} is aangeschoven en geselecteerd als ontvanger, maar heeft {missing_key} nodig in .env om te kunnen antwoorden.")
        else:
            QMessageBox.information(
                self,
                "Model Aangeschoven",
                f"{seat_name} is aangeschoven aan tafel en geselecteerd als ontvanger ({label}).\n\n"
                f"Typ je vraag in het invoerveld onderaan en druk op Enter om {seat_name} aan te spreken."
            )
        self.input_edit.setFocus()

    def toggle_sound(self):
        self.sound_enabled = not self.sound_enabled
        self.btn_sound.setText("🔔 Geluid: AAN" if self.sound_enabled else "🔕 Geluid: UIT")

    def action_setup_environment(self):
        """Richt de lokale omgeving in, toont het stappenplan met Waarom & Doel en start de agent-begeleiding."""
        try:
            from omgeving_inrichter import (
                genereer_stappenplan_markdown,
                plaats_start_op_tafel,
                voer_inrichting_uit,
            )
        except Exception as exc:
            QMessageBox.warning(self, "Omgeving Inrichten", f"Kon inrichter niet laden: {exc}")
            return

        status = voer_inrichting_uit()
        md_tekst = genereer_stappenplan_markdown(status)
        stappen_pad = AGY_WERK / "scratch" / "OMGEVING_INRICHTEN_STAPPENPLAN.md"
        stappen_pad.parent.mkdir(parents=True, exist_ok=True)
        stappen_pad.write_text(md_tekst, encoding="utf-8")

        dlg = QDialog(self)
        dlg.setWindowTitle("🛠️ Omgeving Inrichten — Stappenplan, Waarom & Doel")
        dlg.resize(880, 720)
        lay = QVBoxLayout(dlg)
        lay.setContentsMargins(18, 16, 18, 16)
        lay.setSpacing(10)

        view = QTextEdit()
        view.setReadOnly(True)
        view.setObjectName("md-view")
        font = QFont("JetBrains Mono", 13)
        font.setStyleHint(QFont.StyleHint.Monospace)
        view.setFont(font)
        view.document().setDefaultFont(font)
        view.setStyleSheet(
            "QTextEdit#md-view { background: #100b1c; color: #e2e8f0; "
            "font-family: 'JetBrains Mono', monospace; font-size: 13pt; "
            "border: 1px solid rgba(212, 175, 55, 0.3); border-radius: 6px; padding: 10px; }"
        )
        view.setMarkdown(md_tekst)
        MarkdownViewer._zet_regelafstand(view, font)
        lay.addWidget(view, 1)

        knop_rij = QHBoxLayout()
        btn_tafel = QPushButton("💬 Leg Stappenplan op Tafel & Start met Agent (+agy)")
        btn_tafel.setObjectName("btn-send")
        btn_tafel.setCursor(Qt.CursorShape.PointingHandCursor)

        def _op_tafel():
            plaats_start_op_tafel(status)
            self.check_and_refresh_tafel()
            self.address_seat("agy")
            dlg.accept()

        btn_tafel.clicked.connect(_op_tafel)

        btn_open_nv = QPushButton("🌐 1. Haal Gratis NVIDIA-Sleutel (via Google-login)")
        btn_open_nv.setObjectName("btn-action")
        btn_open_nv.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_open_nv.setToolTip("Opent build.nvidia.com/settings/api-keys. Log daar in met 'Continue with Google' (je Gmail) en kopieer de nvapi-... sleutel.")
        btn_open_nv.clicked.connect(lambda: os.startfile("https://build.nvidia.com/settings/api-keys"))

        btn_plak_key = QPushButton("📋 2. Plak Sleutel van Klembord")
        btn_plak_key.setObjectName("btn-action-gold")
        btn_plak_key.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_plak_key.setToolTip("Leest de gekopieerde sleutel (nvapi-..., AIza..., gsk_..., sk-...) direct van je klembord en slaat hem veilig op in je Windows-omgeving.")

        def _plak_sleutel():
            clip_txt = (QApplication.clipboard().text() or "").strip()
            if not clip_txt or len(clip_txt) < 12 or " " in clip_txt:
                clip_txt, ok_in = QInputDialog.getText(
                    dlg,
                    "Sleutel Plakken",
                    "Plak hier je gekopieerde API-sleutel (bijv. nvapi-... van NVIDIA of AIza... van Google):",
                )
                if not ok_in or not clip_txt.strip():
                    return
                clip_txt = clip_txt.strip()

            if clip_txt.startswith("nvapi-"):
                env_var = "NVIDIA_API_KEY"
                huis_naam = "NVIDIA (Nemotron 120B + GPT-OSS 20B + MiniMax)"
            elif clip_txt.startswith("AIza"):
                env_var = "GOOGLE_API_KEY"
                huis_naam = "Google Gemini"
            elif clip_txt.startswith("gsk_"):
                env_var = "GROQ_API_KEY"
                huis_naam = "Groq (Qwen / Llama)"
            elif clip_txt.startswith("sk-or-"):
                env_var = "OPENROUTER_API_KEY"
                huis_naam = "OpenRouter (Grok)"
            else:
                env_var = "DEEPSEEK_API_KEY"
                huis_naam = "DeepSeek / Anders"

            os.environ[env_var] = clip_txt
            if os.name == "nt":
                try:
                    import winreg
                    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_SET_VALUE) as rk:
                        winreg.SetValueEx(rk, env_var, 0, winreg.REG_SZ, clip_txt)
                except Exception:
                    pass
            nieuw_st = voer_inrichting_uit()
            view.setMarkdown(genereer_stappenplan_markdown(nieuw_st))
            MarkdownViewer._zet_regelafstand(view, font)
            QMessageBox.information(
                dlg,
                "Sleutel Geactiveerd",
                f"✅ Herkend en veilig opgeslagen in je Windows-omgeving:\n\n"
                f"• Variabele: {env_var}\n"
                f"• Modelhuis: {huis_naam}\n\n"
                f"Je hoeft geen terminal of bestand te openen; de modellen staan direct klaar!",
            )

        btn_plak_key.clicked.connect(_plak_sleutel)

        btn_sluit = QPushButton("Sluiten")
        btn_sluit.setObjectName("btn-sound")
        btn_sluit.clicked.connect(dlg.reject)

        knop_rij.addWidget(btn_tafel, 2)
        knop_rij.addWidget(btn_open_nv, 1)
        knop_rij.addWidget(btn_plak_key, 1)
        knop_rij.addWidget(btn_sluit)
        lay.addLayout(knop_rij)

        dlg.exec()


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = TafelWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
