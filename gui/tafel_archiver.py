#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TAFEL ARCHIVER — Geautomatiseerde Rolling Archivering (Drempel: 20 beurten)
Pure Python Standard Library (Zero External Dependencies).

Bewaakt dat TAFEL.md nooit dichtslibt:
- Houdt altijd exact de laatste 20 beurten in de actieve TAFEL.md.
- Rolt oudere beurten automatisch door naar agy_werk/archief/tafel.
- Houdt in de kop één verwijzing naar die map.
- Triggert direct de tafel_indexer.py om de zoekindex up-to-date te houden.
"""

from __future__ import annotations

import sys
import os
import re
from datetime import datetime
from pathlib import Path

# Force UTF-8 console output on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

GUI_DIR = Path(__file__).resolve().parent
REPO_ROOT = GUI_DIR.parent
WORKSPACE = Path(os.environ.get("CIVIC_WORKSPACE", r"E:\LLM_Workspace" if Path(r"E:\LLM_Workspace").exists() else REPO_ROOT))
AGY_WERK = WORKSPACE / "agy_werk" if (WORKSPACE / "agy_werk").exists() else (REPO_ROOT / "werk")
TAFEL_MD = AGY_WERK / "TAFEL.md" if (AGY_WERK / "TAFEL.md").exists() else (REPO_ROOT / "TAFEL.md")
ARCHIVE_DIR = TAFEL_MD.parent / "archief" / "tafel"

if str(GUI_DIR) not in sys.path:
    sys.path.insert(0, str(GUI_DIR))

try:
    from .tafel_indexer import run_full_index, parse_date_iso
except ImportError:
    from tafel_indexer import run_full_index, parse_date_iso

MAX_ACTIVE_TURNS = 20

TURN_HEADER_REGEX = re.compile(
    r"^##\s+([a-zA-Z0-9_\-\.]+)\s*\(([^)]+)\)\s*(?:[—\-–]+\s*(.*))?$",
    re.MULTILINE
)


def archive_tafel_if_needed(threshold: int = MAX_ACTIVE_TURNS, dry_run: bool = False) -> bool:
    """Controleert of TAFEL.md meer beurten heeft dan de drempel, en archiveert indien nodig."""
    if not TAFEL_MD.exists():
        print(f"[!] TAFEL.md niet gevonden op {TAFEL_MD}.")
        return False

    content = TAFEL_MD.read_text(encoding="utf-8")
    matches = list(TURN_HEADER_REGEX.finditer(content))
    total_turns = len(matches)

    print(f"[*] Huidig aantal beurten in TAFEL.md: {total_turns} (Drempel: {threshold})")

    if total_turns <= threshold:
        print(f"[✓] TAFEL.md is binnen de norm (<= {threshold} beurten). Geen archivering nodig.")
        return False

    num_to_archive = total_turns - threshold

    xander_indices = [i for i, m in enumerate(matches) if m.group(1).strip().lower() == "xander"]
    if xander_indices:
        last_xander_idx = xander_indices[-1]
        if last_xander_idx < num_to_archive and (total_turns - last_xander_idx) <= (threshold + 5):
            num_to_archive = last_xander_idx

    if num_to_archive <= 0:
        print(f"[✓] Laatste beurt van Xander wordt vastgehouden op het actieve blad ({total_turns} beurten).")
        return False

    print(f"[*] {num_to_archive} oudere beurten worden gearchiveerd. De laatste {total_turns - num_to_archive} blijven actief.")

    split_match = matches[num_to_archive]
    split_pos = split_match.start()

    pre_text = content[:split_pos].rstrip()
    if pre_text.endswith("---"):
        split_pos = pre_text.rfind("---")

    first_turn_pos = matches[0].start()
    header_part = content[:first_turn_pos].strip()
    archive_body = content[first_turn_pos:split_pos].strip()
    retained_turns_body = content[split_pos:].strip()

    first_date_raw = matches[0].group(2)
    last_archived_date_raw = matches[num_to_archive - 1].group(2)
    start_iso = parse_date_iso(first_date_raw)
    end_iso = parse_date_iso(last_archived_date_raw)

    archive_filename = f"TAFEL_ARCHIEF_{start_iso}_tot_{end_iso}.md"
    archive_path = ARCHIVE_DIR / archive_filename

    counter = 1
    while archive_path.exists():
        archive_filename = f"TAFEL_ARCHIEF_{start_iso}_tot_{end_iso}_deel{counter}.md"
        archive_path = ARCHIVE_DIR / archive_filename
        counter += 1

    archive_full_content = f"# Tafelarchief {start_iso} t/m {end_iso}\n\n"
    archive_full_content += f"Geautomatiseerd gearchiveerd op {datetime.now().strftime('%Y-%m-%d %H:%M')}.\n\n"
    archive_full_content += "---\n\n"
    archive_full_content += archive_body + "\n"

    pointer = "*Oude beurten:* [archief/tafel](archief/tafel)"
    new_header_part = header_part
    if "*Oude beurten:*" not in new_header_part and "*Archief" not in new_header_part:
        new_header_part = new_header_part.rstrip() + "\n\n" + pointer + "\n"

    new_tafel_content = f"{new_header_part}\n\n---\n\n{retained_turns_body}\n"

    if dry_run:
        print(f"[DRY-RUN] Zou schrijven naar: {archive_path.name}")
        print(f"[DRY-RUN] Zou TAFEL.md verkleinen tot {len(retained_turns_body.splitlines())} regels.")
        return True

    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    archive_path.write_text(archive_full_content, encoding="utf-8")
    print(f"[✓] Archiefbestand aangemaakt: {archive_path.name} ({len(archive_full_content.splitlines())} regels)")

    TAFEL_MD.write_text(new_tafel_content, encoding="utf-8")
    print(f"[✓] TAFEL.md opgeschoond: bevat nu exact de laatste {threshold} beurten ({len(new_tafel_content.splitlines())} regels)")

    print("[*] Zoekindex bijwerken via tafel_indexer...")
    run_full_index()
    print("[✓] Indexering compleet.")

    return True


if __name__ == "__main__":
    threshold = MAX_ACTIVE_TURNS
    dry_run = "--dry-run" in sys.argv
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        threshold = int(sys.argv[1])
    archive_tafel_if_needed(threshold=threshold, dry_run=dry_run)
