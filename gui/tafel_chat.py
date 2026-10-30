#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Chat-dispatch voor Civic Helper.

Een regel die de gebruiker in het Tafelvenster schrijft, krijgt hier antwoord:
- DeepSeek antwoordt via de eigen autonome agent-watcher (deepseek_tafel_watcher.py) als die draait;
  alleen als die offline is, valt tafel_chat.py in via API.
- Grok antwoordt via de zittende Grok-sessie als tafel_wacht_grok.py meeluistert;
  om te zorgen dat de poll Xanders kop altijd ziet, wacht tafel_chat.py 6 seconden.
  Als Grok offline is (of na 45s nog niet geantwoord heeft), valt tafel_chat.py in.
- agy antwoordt direct met de actuele Tafel-context.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

GUI_DIR = Path(__file__).resolve().parent
REPO_ROOT = GUI_DIR.parent
_CANDIDATE_WS = REPO_ROOT.parent if (REPO_ROOT.parent / "agy_werk").exists() else REPO_ROOT
WORKSPACE = Path(os.environ.get("CIVIC_WORKSPACE", str(_CANDIDATE_WS)))
AGY_WERK = WORKSPACE / "agy_werk" if (WORKSPACE / "agy_werk").exists() else (REPO_ROOT / "werk")
TAFEL_MD = AGY_WERK / "TAFEL.md" if (AGY_WERK / "TAFEL.md").exists() else (REPO_ROOT / "TAFEL.md")
STATE_FILE = AGY_WERK / "scratch" / "tafel_chat_state.json"
PID_FILE = AGY_WERK / "scratch" / "tafel_chat.pid"

default_grok = Path.home() / ".grok" / "bin" / "grok.exe"
GROK_EXE = Path(os.environ.get("GROK_EXE", str(default_grok) if default_grok.exists() else "grok"))

if str(GUI_DIR) not in sys.path:
    sys.path.insert(0, str(GUI_DIR))

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

try:
    from .tafel_indexer import index_file
    from .model_bus import _load_env, complete
except ImportError:
    from tafel_indexer import index_file
    from model_bus import _load_env, complete

# label, modelhuis, modelnaam (None = de standaard van het huis)
SEATS = (
    ("agy", "gemini", "gemini-3.8-flash"),
    ("Grok", "grok", None),
    ("DeepSeek", "deepseek", None),
    ("Argon", "gemini", "gemini-4-argon"),
    ("Gemini", "gemini", "gemini-3.8-flash"),
    ("Qwen", "qwen", "qwen/qwen3.8-27b"),
    ("Mistral", "mistral", "mistral-large-latest"),
    ("NVIDIA", "nvidia", "nvidia/nemotron-3.5-super-vl-120b-a12b"),
)
ALLEN_SEATS = SEATS[:3]

MONTHS = ("jan", "feb", "mrt", "apr", "mei", "jun", "jul", "aug", "sep", "okt", "nov", "dec")
PING_RE = re.compile(r"ping[.!]?", re.IGNORECASE)
FIRST_SEEN: dict[str, float] = {}


def log(msg: str) -> None:
    print(msg, flush=True)


def now_stamp() -> str:
    now = datetime.now()
    return f"{now.day} {MONTHS[now.month - 1]} {now.year}, {now:%H:%M}"


def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
            data.setdefault("answered", [])
            return data
        except Exception:
            pass
    return {"answered": [], "primed": False}


def save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")


def prime_keys() -> None:
    _load_env()
    if not os.environ.get("GOOGLE_API_KEY") and os.environ.get("GEMINI_API_KEY"):
        os.environ["GOOGLE_API_KEY"] = os.environ["GEMINI_API_KEY"]


def plain_body(turn: dict) -> str:
    kept = []
    for line in (turn.get("content_full") or "").splitlines():
        low = line.strip().lower()
        if low.startswith("**aangesproken") or low.startswith("**stok"):
            continue
        kept.append(line)
    return "\n".join(kept).strip()


def is_ping(body: str) -> bool:
    return bool(PING_RE.fullmatch(body.strip()))


def wanted_seats(turn: dict) -> list[tuple[str, str, str | None]]:
    addressed = [a.lower() for a in (turn.get("addressed") or [])]
    baton = (turn.get("baton_to") or "").lower()
    body = (turn.get("content_full") or "").lower()
    if any("allen" in a for a in addressed) or "allen" in baton or "@allen" in body:
        seats = list(ALLEN_SEATS)
        for extra in SEATS[3:]:
            e_low = extra[0].lower()
            if e_low in addressed or e_low in baton or f"@{e_low}" in body:
                seats.append(extra)
        return seats
    seats = []
    for seat in SEATS:
        s_low = seat[0].lower()
        if s_low in addressed or s_low in baton or f"@{s_low}" in body:
            seats.append(seat)
    return seats


def mark(state: dict, turn_id: str, label: str) -> None:
    key = f"{turn_id}:{label.lower()}"
    if key not in state["answered"]:
        state["answered"].append(key)


def already(state: dict, turn_id: str, label: str) -> bool:
    return f"{turn_id}:{label.lower()}" in state["answered"]


def watcher_status() -> tuple[bool, bool]:
    """Geeft terug of (deepseek_watcher_actief, grok_watcher_actief) draaien."""
    deepseek_live = False
    grok_live = False
    try:
        import psutil
        for p in psutil.process_iter(["cmdline"]):
            try:
                cmd = " ".join(p.info.get("cmdline") or []).lower()
            except Exception:
                continue
            if "deepseek_tafel_watcher.py" in cmd:
                deepseek_live = True
            if "tafel_wacht_grok.py" in cmd:
                grok_live = True
    except Exception:
        pass
    return deepseek_live, grok_live


def recent_tafel_context(turns: list[dict], limit: int = 12) -> str:
    selected = list(turns[-limit:])
    for t in turns[:-limit]:
        if (t.get("author") or "").lower() == "xander" and len(plain_body(t)) > 250:
            selected.insert(0, t)
            break

    snippets = []
    for t in selected:
        author = t.get("author", "Onbekend")
        date_raw = t.get("date_raw", "")
        body = plain_body(t)
        if len(body) > 4000:
            body = body[:4000] + "\n[… ingekort na 4000 tekens …]"
        snippets.append(f"[{author} ({date_raw})]:\n{body}")

    outbox_dir = AGY_WERK / "outbox"
    if outbox_dir.exists():
        files = sorted(
            (p for p in outbox_dir.iterdir() if p.is_file() and p.suffix.lower() in {".md", ".txt"}),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )[:4]
        if files:
            listing = ", ".join(
                f"{p.name} ({datetime.fromtimestamp(p.stat().st_mtime):%H:%M}, {p.stat().st_size}B)"
                for p in files
            )
            newest_text = files[0].read_text(encoding="utf-8", errors="replace").strip()
            if len(newest_text) > 2500:
                newest_text = newest_text[:2500] + "\n[…]"
            snippets.append(
                f"[Actuele bestanden in outbox/]: {listing}\n"
                f"[Inhoud nieuwste outbox-bestand ({files[0].name})]:\n{newest_text}"
            )

    return "\n\n".join(snippets)


def call_grok_cli(body: str, context: str = "") -> str:
    prompt_path = AGY_WERK / "scratch" / "tafel_chat_grok_prompt.txt"
    prompt_path.parent.mkdir(parents=True, exist_ok=True)
    ctx_block = f"Recente Tafel-context:\n{context}\n\n" if context else ""
    prompt_path.write_text(
        "Je zit als Grok aan de Tafel in Civic Helper. Antwoord in helder, natuurlijk Nederlands "
        "op de beurt hieronder. Geen gereedschap en geen markdown-kop.\n\n"
        + ctx_block
        + "Nieuwe inbreng:\n"
        + body,
        encoding="utf-8",
    )
    try:
        proc = subprocess.run(
            [
                str(GROK_EXE),
                "--no-plan",
                "--no-subagents",
                "--disable-web-search",
                "--tools",
                "",
                "--max-turns",
                "1",
                "--output-format",
                "plain",
                "--prompt-file",
                str(prompt_path),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
            cwd=str(WORKSPACE),
        )
    except Exception as exc:
        return f"(Grok was even niet bereikbaar: {type(exc).__name__})"
    text = (proc.stdout or "").strip()
    if not text:
        err = (proc.stderr or "").strip().splitlines()
        tail = err[-1] if err else "geen uitvoer"
        return f"(Grok gaf geen tekst terug: {tail[:180]})"
    return text


def reply_for(label: str, house: str, model: str | None, body: str, context: str = "") -> str:
    if is_ping(body):
        return "ping"
    if label.lower() == "grok" and Path(str(GROK_EXE)).exists():
        text = call_grok_cli(body, context=context)
    else:
        text = _complete_house(house, model, label, body, context=context)
    cleaned = []
    for line in str(text).strip().splitlines():
        if line.startswith("#"):
            continue
        cleaned.append(line)
    return "\n".join(cleaned).strip() or "(leeg antwoord)"


def _complete_house(house: str, model: str | None, label: str, body: str, context: str = "") -> str:
    system = (
        f"Je bent {label} en zit met de gebruiker, Grok en DeepSeek aan de Tafel in Civic Helper. "
        "Schrijf in natuurlijk, helder Nederlands en beantwoord de inbreng direct. "
        "Zegt de regel alleen ping, dan is je hele antwoord: ping. "
        "Houd je strikt aan de feiten, namen, datums en briefteksten uit de meegegeven Tafel- en outbox-context; "
        "verzin nooit eigen zaaknummers, datums of instanties. "
        "Begin niet met een markdown-kop (de kop wordt automatisch geplaatst)."
    )
    ctx_block = f"Laatste beurten op de Tafel en status outbox:\n{context}\n\n" if context else ""
    user = f"{ctx_block}Nieuwe inbreng:\n{body}"
    text = complete(house, system, user, model=model, temperature=0.2, max_tokens=1200)
    if house == "gemini" and str(text).startswith("[FOUT"):
        text = complete(house, system, user, model="gemini-pro-latest", temperature=0.2, max_tokens=1200)
    elif str(text).startswith("[FOUT"):
        if "geen MISTRAL_API_KEY" in str(text):
            text = f"({label} kan nog niet antwoorden: MISTRAL_API_KEY ontbreekt in .env. Voeg je sleutel toe om {label} te laten meepraten.)"
        elif "geen GROQ_API_KEY" in str(text):
            text = f"({label} kan nog niet antwoorden: GROQ_API_KEY ontbreekt in .env. Voeg je sleutel toe om {label} te laten meepraten.)"
    return str(text).strip()


def good_reply(turn: dict) -> bool:
    body = plain_body(turn)
    if not body or body.startswith("[FOUT") or "Missing Authentication" in body:
        return False
    return True


def replied_in_file(turns: list[dict], index: int, label: str) -> bool:
    for later in turns[index + 1:]:
        if (later.get("author") or "").lower() == "xander":
            return False
        same = (later.get("author") or "").lower() == label.lower()
        if same and good_reply(later):
            return True
    return False


def append_reply(label: str, text: str) -> None:
    entry = (
        f"\n\n---\n\n## {label} ({now_stamp()}) — Antwoord via Civic Helper\n\n"
        f"**Aangesproken:** @Xander\n"
        f"**Stok:** Xander\n\n"
        f"{text.strip()}\n"
    )
    with open(TAFEL_MD, "a", encoding="utf-8") as handle:
        handle.write(entry)


def prime_history(turns: list[dict], state: dict) -> None:
    if state.get("primed"):
        return
    xander = [t for t in turns if (t.get("author") or "").lower() == "xander" and t.get("turn_id")]
    older = xander[:-1] if xander else []
    for turn in older:
        for label, _house, _model in SEATS:
            mark(state, turn["turn_id"], label)
    state["primed"] = True
    save_state(state)
    if xander:
        log(f"[tafel-chat] geschiedenis gezien, open beurt: {xander[-1].get('date_raw')}")


def answer_pending(state: dict) -> int:
    if not TAFEL_MD.exists():
        return 0
    turns = index_file(TAFEL_MD)
    prime_history(turns, state)
    xander_turns = [t for t in turns if (t.get("author") or "").lower() == "xander"]
    if not xander_turns:
        return 0

    latest = xander_turns[-1]
    latest_index = turns.index(latest)
    turn_id = latest.get("turn_id") or ""
    body = plain_body(latest)
    if not body or not turn_id:
        return 0

    now = time.time()
    seen_at = FIRST_SEEN.setdefault(turn_id, now)
    elapsed = now - seen_at

    deepseek_live, grok_live = watcher_status()
    seats = wanted_seats(latest)
    if not seats:
        return 0

    grok_wanted = any(s[0].lower() == "grok" for s in seats)
    if grok_wanted and grok_live and elapsed < 6.0:
        return 0

    wrote = 0
    context = recent_tafel_context(turns[:latest_index + 1], limit=12)

    for label, house, model in seats:
        l_low = label.lower()
        if replied_in_file(turns, latest_index, label) or already(state, turn_id, label):
            mark(state, turn_id, label)
            continue

        if l_low == "deepseek" and deepseek_live:
            continue

        if l_low == "grok" and grok_live:
            continue

        log(f"[tafel-chat] {label} antwoordt op {latest.get('date_raw')}")
        text = reply_for(label, house, model, body, context=context)
        append_reply(label, text)
        mark(state, turn_id, label)
        save_state(state)
        wrote += 1
        log(f"[tafel-chat] {label} staat op de Tafel")
        turns = index_file(TAFEL_MD)
        latest_index = next((i for i, t in enumerate(turns) if t.get("turn_id") == turn_id), latest_index)

    save_state(state)
    return wrote


def pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        import psutil
        return psutil.pid_exists(pid)
    except Exception:
        return False


def take_pid() -> bool:
    PID_FILE.parent.mkdir(parents=True, exist_ok=True)
    if PID_FILE.exists():
        try:
            old = int(PID_FILE.read_text(encoding="utf-8").strip())
        except Exception:
            old = 0
        if old and old != os.getpid() and pid_alive(old):
            log(f"[tafel-chat] draait al als {old}")
            return False
    PID_FILE.write_text(str(os.getpid()), encoding="utf-8")
    return True


def run(once: bool) -> None:
    if not take_pid():
        return
    prime_keys()
    log("[tafel-chat] dispatch aan")
    try:
        while True:
            try:
                answer_pending(load_state())
            except Exception as exc:
                log(f"[tafel-chat] fout: {type(exc).__name__}: {exc}")
            if once:
                return
            time.sleep(1.5)
    finally:
        try:
            if PID_FILE.exists() and PID_FILE.read_text(encoding="utf-8").strip() == str(os.getpid()):
                PID_FILE.unlink()
        except Exception:
            pass


if __name__ == "__main__":
    run(once="--once" in sys.argv)
