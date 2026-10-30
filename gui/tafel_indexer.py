#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TAFEL INDEXER — Forensische Indexering van alle Beraadslagingen
Pure Python Standard Library (Zero External Dependencies).

Parseert alle historische archieven en de actieve TAFEL.md.
Bouwt een gestructureerd register op in TAFEL_INDEX.json met:
- Auteurs, tijdstempels, titels en regelnummers (klikbare links).
- Adressering (wie spreekt wie aan) en stok-doorgifte.
- Samenvattingen en trefwoorden.
- Herkenning van geparkeerde verkenningen ('parked' / onafgemaakte sporen).
"""

from __future__ import annotations

import sys
import os
import re
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Force UTF-8 console output on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

GUI_DIR = Path(__file__).resolve().parent
REPO_ROOT = GUI_DIR.parent
_CANDIDATE_WS = REPO_ROOT.parent if (REPO_ROOT.parent / "agy_werk").exists() else REPO_ROOT
WORKSPACE = Path(os.environ.get("CIVIC_WORKSPACE", str(_CANDIDATE_WS)))
AGY_WERK = WORKSPACE / "agy_werk" if (WORKSPACE / "agy_werk").exists() else (REPO_ROOT / "werk")
INDEX_PATH = AGY_WERK / "TAFEL_INDEX.json" if AGY_WERK.exists() else (REPO_ROOT / "TAFEL_INDEX.json")

# Regex voor de beurtkoppen: ## <Auteur> (<datum/tijd>) — <Titel>
TURN_HEADER_REGEX = re.compile(
    r"^##\s+([a-zA-Z0-9_\-\.]+)\s*\(([^)]+)\)\s*(?:[—\-–]+\s*(.*))?$",
    re.MULTILINE
)

# Regex voor stok-doorgifte. De laatste treffer in de beurt wint.
BATON_REGEX = re.compile(
    r"(?:(?:\*{0,2}stok\*{0,2}:|\*{0,2}stok:\*{0,2}|stok\s+(?:gaat\s+terug\s+naar|gaat\s+naar|ligt\s+bij|naar)|de\s+stok\s+is\s+voor))\s*@?([a-zA-Z0-9_\-\.]+)",
    re.IGNORECASE
)

SEAT_NAMES = {
    "xander": "Xander",
    "agy": "agy",
    "grok": "Grok",
    "deepseek": "DeepSeek",
    "argon": "Argon",
    "gemini": "Gemini",
    "walter": "Walter",
    "mistral": "Mistral",
    "qwen": "Qwen",
}

# Sleutelwoorden voor geparkeerde / onuitgewerkte verkenningen
PARKED_KEYWORDS = [
    "geparkeerd", "parkeren", "later oppakken", "geen gevolg",
    "verkenning", "openstaande vraag", "nog uitzoeken", "hypothese",
    "nog niet gebouwd", "pruttelen", "zijpad"
]


def clean_str(s: Optional[str]) -> str:
    return (s or "").strip()


def seat_name(raw: str) -> str:
    """Eén schrijfwijze voor de stoelen die aan tafel zitten."""
    key = clean_str(raw).lstrip("@").lower()
    return SEAT_NAMES.get(key, clean_str(raw).lstrip("@").capitalize())


STOK_OP_LINE = re.compile(r"^\s*(?:\*\*)?stok\s+op(?:\*\*)?\s*:\s*(.+?)\s*$", re.IGNORECASE)
STOK_VRIJ_LINE = re.compile(r"^\s*(?:\*\*)?stok\s+vrij(?:\*\*)?\s*:\s*(.+?)\s*$", re.IGNORECASE)


def split_claim_paths(raw: str) -> list[str]:
    """Haalt bestandspaden uit een stokregel. Komma, puntkomma of losse woorden."""
    out = []
    chunks = re.split(r"[,;]|\s+en\s+", clean_str(raw).strip("*"))
    for chunk in chunks:
        for piece in chunk.split():
            piece = piece.strip().strip("`").strip()
            if piece:
                out.append(piece)
    return out


def claim_key(path: str) -> str:
    return path.replace("\\", "/").strip("/").lower()


def file_and_part(path: str) -> tuple[str, str]:
    """Een pad en, na een hekje, het onderdeel. `tafel_gui.py#invoerbalk`."""
    raw = path.replace("\\", "/").strip().strip("`")
    part = ""
    if "#" in raw:
        raw, part = raw.split("#", 1)
        part = part.strip().lower()
    return claim_key(raw), part


def claim_label(path: str) -> str:
    file_key, part = file_and_part(path)
    parts = [p for p in file_key.split("/") if p]
    label = "/".join(parts[-2:]) if len(parts) >= 2 else (parts[-1] if parts else path)
    if part:
        label = f"{label}#{part}"
    return label


def stok_events(body_text: str) -> list[dict[str, str]]:
    """Stok op en Stok vrij, in de volgorde van de beurt."""
    events = []
    for line in body_text.splitlines():
        op = STOK_OP_LINE.match(line)
        if op:
            events.extend({"kind": "op", "path": p} for p in split_claim_paths(op.group(1)))
            continue
        vrij = STOK_VRIJ_LINE.match(line)
        if vrij:
            events.extend({"kind": "vrij", "path": p} for p in split_claim_paths(vrij.group(1)))
    return events


def _overlaps(held: dict, author: str, file_key: str, part: str) -> list[dict]:
    clashes = []
    for item in held.values():
        if item["author"].lower() == author.lower() or item["file"] != file_key:
            continue
        if not item["part"] or not part or item["part"] == part:
            clashes.append(item)
    return clashes


def _release(held: dict, author: str, file_key: str, part: str) -> None:
    author_l = author.lower()
    if part:
        key = f"{file_key}#{part}"
        item = held.get(key)
        if item and item["author"].lower() == author_l:
            held.pop(key, None)
        return
    for key in list(held):
        item = held[key]
        if item["file"] == file_key and item["author"].lower() == author_l:
            held.pop(key, None)


def claim_board(turns: list[dict]) -> tuple[list[dict], list[dict]]:
    held: dict[str, dict] = {}
    blocked: list[dict] = []
    for turn in turns:
        author = turn.get("author", "")
        for event in turn.get("stok_events") or []:
            file_key, part = file_and_part(event.get("path", ""))
            if not file_key:
                continue
            if event.get("kind") == "vrij":
                _release(held, author, file_key, part)
                continue
            clashes = _overlaps(held, author, file_key, part)
            if clashes:
                blocked.append({
                    "author": author,
                    "path": event["path"],
                    "label": claim_label(event["path"]),
                    "holder": clashes[0]["author"],
                    "holder_label": clashes[0]["label"],
                })
                continue
            if part:
                own_whole = held.get(file_key)
                if own_whole and own_whole["author"].lower() == author.lower():
                    held.pop(file_key, None)
                key = f"{file_key}#{part}"
            else:
                for key in list(held):
                    item = held[key]
                    if item["file"] == file_key and item["author"].lower() == author.lower():
                        held.pop(key, None)
                key = file_key
            held[key] = {
                "author": author,
                "label": claim_label(event["path"]),
                "path": event["path"],
                "file": file_key,
                "part": part,
            }
    still = []
    for block in blocked:
        file_key, part = file_and_part(block["path"])
        if _overlaps(held, block["author"], file_key, part):
            still.append(block)
    return list(held.values()), still


def active_file_claims(turns: list[dict]) -> list[dict]:
    held, _blocked = claim_board(turns)
    return held


def parse_date_iso(date_str: str) -> str:
    maanden = {
        "jan": "01", "feb": "02", "mrt": "03", "apr": "04",
        "mei": "05", "jun": "06", "jul": "07", "aug": "08",
        "sep": "09", "okt": "10", "nov": "11", "dec": "12"
    }
    low = date_str.lower()
    maanden.update({
        "jan": "01", "feb": "02", "mar": "03", "apr": "04",
        "may": "05", "jun": "06", "jul": "07", "aug": "08",
        "sep": "09", "oct": "10", "nov": "11", "dec": "12"
    })
    m = re.search(r"(\d{1,2})\s+([a-z]{3,4})\s*(20\d{2})?", low)
    if m:
        dag = f"{int(m.group(1)):02d}"
        maand = maanden.get(m.group(2)[:3], "01")
        jaar = m.group(3) or "2026"
        return f"{jaar}-{maand}-{dag}"
    return "2026-10-00"


def index_file(filepath: Path) -> List[Dict[str, Any]]:
    if not filepath.exists():
        return []

    text = filepath.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    matches = list(TURN_HEADER_REGEX.finditer(text))
    turns = []

    for idx, match in enumerate(matches):
        author = clean_str(match.group(1))
        date_raw = clean_str(match.group(2))
        title = clean_str(match.group(3)) or "Zonder titel"

        start_char = match.start()
        start_line = text.count("\n", 0, start_char) + 1

        if idx + 1 < len(matches):
            end_char = matches[idx + 1].start()
            end_line = text.count("\n", 0, end_char)
            body_text = text[match.end():end_char].strip()
        else:
            end_line = len(lines)
            body_text = text[match.end():].strip()

        addressed = []
        explicit_addr = re.search(
            r"^\s*\*{0,2}aangesproken(?:\s+door)?\*{0,2}\s*:\s*\*{0,2}(.+?)$",
            body_text,
            re.IGNORECASE | re.MULTILINE,
        )
        if explicit_addr:
            addr_line = explicit_addr.group(1)
            if re.search(r"\ballen\b", addr_line, re.IGNORECASE):
                for key in ("agy", "grok", "deepseek"):
                    if key != author.lower():
                        addressed.append(SEAT_NAMES[key])
            for key, label in SEAT_NAMES.items():
                if re.search(rf"\b{key}\b", addr_line, re.IGNORECASE):
                    if key != author.lower() and label not in addressed:
                        addressed.append(label)
        else:
            first_lines = "\n".join(body_text.splitlines()[:5])
            for key, label in SEAT_NAMES.items():
                if re.search(rf"\b{key}\b", first_lines, re.IGNORECASE):
                    if key != author.lower() and label not in addressed:
                        addressed.append(label)

        baton_to = "Onbekend"
        baton_matches = list(BATON_REGEX.finditer(body_text))
        if baton_matches:
            baton_to = seat_name(baton_matches[-1].group(1).rstrip(".,;:"))

        is_parked = any(k in body_text.lower() for k in PARKED_KEYWORDS)

        paragraphs = [p.strip() for p in body_text.split("\n\n") if p.strip() and not p.strip().startswith("---")]
        summary = paragraphs[0][:300] if paragraphs else ""

        keywords = set()
        for kw in ["Awb", "AVG", "Wmo", "CAK", "UWV", "LAVG", "Menzis", "Toeslagen", "C6", "SBARIII", "Velvet Glove"]:
            if re.search(rf"\b{re.escape(kw)}\b", body_text, re.IGNORECASE):
                keywords.add(kw)

        date_iso = parse_date_iso(date_raw)
        body_sig = hashlib.sha256(body_text.encode("utf-8", errors="replace")).hexdigest()[:12]
        turn_hash = hashlib.sha256(f"{date_raw}|{author}|{title}|{body_sig}".encode()).hexdigest()[:10]

        turn_entry = {
            "turn_id": f"TURN-{date_iso.replace('-', '')}-{author.upper()}-{turn_hash}",
            "file": filepath.name,
            "filepath": str(filepath),
            "start_line": start_line,
            "end_line": end_line,
            "author": author,
            "date_raw": date_raw,
            "date_iso": date_iso,
            "title": title,
            "addressed": addressed,
            "baton_to": baton_to,
            "stok_events": stok_events(body_text),
            "is_parked": is_parked,
            "summary": summary,
            "content_full": body_text,
            "keywords": sorted(list(keywords)),
            "line_count": end_line - start_line + 1,
        }
        turns.append(turn_entry)

    return turns


def run_full_index() -> Dict[str, Any]:
    roots = [AGY_WERK]
    if REPO_ROOT != AGY_WERK:
        roots.append(REPO_ROOT)
    archive_dirs = [d for root in roots for d in (root / "archief" / "tafel", root)]
    seen: set[str] = set()
    archive_files = []
    for archive_dir in archive_dirs:
        if not archive_dir.is_dir():
            continue
        for archive_path in archive_dir.glob("TAFEL_ARCHIEF_*.md"):
            if archive_path.name in seen:
                continue
            seen.add(archive_path.name)
            archive_files.append(archive_path)
    archive_files.sort(key=lambda p: p.name)
    tafel_live = AGY_WERK / "TAFEL.md"
    if not tafel_live.exists():
        tafel_live = REPO_ROOT / "TAFEL.md"

    all_turns = []

    for arc in archive_files:
        turns = index_file(arc)
        all_turns.extend(turns)

    if tafel_live.exists():
        live_turns = index_file(tafel_live)
        all_turns.extend(live_turns)

    database = {
        "updated_at": datetime.now().isoformat(),
        "total_turns": len(all_turns),
        "active_turns": len([t for t in all_turns if t["file"] == "TAFEL.md"]),
        "archived_turns": len([t for t in all_turns if t["file"] != "TAFEL.md"]),
        "turns": all_turns
    }

    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    INDEX_PATH.write_text(json.dumps(database, indent=2, ensure_ascii=False), encoding="utf-8")
    return database


if __name__ == "__main__":
    db = run_full_index()
    print(f"[*] TAFEL INDEXERING VOLTOOID:")
    print(f"    Totaal beurten geindexeerd: {db['total_turns']}")
    print(f"    In actieve TAFEL.md:        {db['active_turns']}")
    print(f"    In archiefbestanden:        {db['archived_turns']}")
    print(f"    Opgeslagen in:              {INDEX_PATH}")
