#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CIVIC CASE ENGINE — LANDSCAPE REALTIME SYNCHRONIZER (v1.0)
Pure Python Standard Library (Zero External Dependencies).

Doel:
Automatisch en realtime monitoren, extraheren en synchroniseren van het institutionele
landschap (Organisatie, Politiek Discours, Keten & Contracten) vanuit inkomende dossierstukken,
e-mails en openbare bestuursbronnen (RIS, Notubiz, TenderNed RSS, Bekendmakingen).

Functies:
1. Inbound Document/Mail Parser:
   Detecteert automatisch functionarissen, organisaties, functietitels, detacheringen
   (bijv. Maandag, BMC) en contactgegevens uit Markdown/tekst/briefbestanden.
2. Open Source OSINT & Beroepsscan Generator:
   Genereert schone zoekopdrachten voor publieke LinkedIn-profielen, beroepsregisters
   (SKJ, Registerplein, BIG) en gemeentelijke mandaatregisters.
3. Open Bestuursbronnen / RIS Watcher:
   Monitort RSS/Notubiz/Open Data feeds op trefwoorden (Wmo, NAH, sociaal domein, inhuur, wachtlijst).
4. Matrix Synchronizer:
   Houdt de drie canonieke bestanden bij (01_Organisatie.md, 02_Politiek_discours.md, 03_Keten_en_contracten.md)
   zonder handmatige notities of feiten te overschrijven.
"""

import sys
import os
import re
import json
import argparse
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Set

# Regex patronen voor detectie van ambtenaren, functies, detacheerders en contacten
ROLE_PATTERNS = [
    r"(?i)\b(Wmo[\s-]consulent(?:e)?)\b",
    r"(?i)\b(Casemanager(?:[\s\w]+)?)\b",
    r"(?i)\b(Teamleider(?:[\s\w]+)?)\b",
    r"(?i)\b(Wethouder(?:[\s\w]+)?)\b",
    r"(?i)\b(Kwaliteitsmedewerker(?:[\s\w]+)?)\b",
    r"(?i)\b(Beleidsadviseur(?:[\s\w]+)?)\b",
    r"(?i)\b(Afdelingshoofd(?:[\s\w]+)?)\b",
    r"(?i)\b(Functionaris Gegevensbescherming|FG)\b",
    r"(?i)\b(Cliëntondersteuner|Onafhankelijk cliëntondersteuner)\b",
    r"(?i)\b(Klantadviseur|Klantbegeleider)\b",
    r"(?i)\b(Toezichthouder Wmo)\b"
]

DETACHMENT_PATTERNS = [
    r"(?i)\b(Maandag(?:®)?)\b",
    r"(?i)\b(BMC(?:\s+Advies)?)\b",
    r"(?i)\b(Yacht)\b",
    r"(?i)\b(koen)\b",
    r"(?i)\b(CompetenSys)\b",
    r"(?i)\b(B&A(?:\s+Groep)?)\b",
    r"(?i)\b(ZZP(?:\'er)?|Zelfstandige zonder personeel)\b",
    r"(?i)\b(Gedetacheerd(?:[\s\w]+)?)\b"
]

EMAIL_PATTERN = re.compile(r"([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)")
PHONE_PATTERN = re.compile(r"(\b0[1-9][0-9]{1,2}[-\s]?[0-9]{6,7}\b|\b06[-\s]?[0-9]{8}\b)")

KEYWORDS_RIS = [
    "wmo", "nah", "begeleiding", "sociaal domein", "zorginkoop", "wachttijd",
    "wachtlijst", "inhuur", "dorpenzorg", "mandaat", "verordening", "pgb"
]

class LandscapeSynchronizer:
    def __init__(self, root_dir: Optional[Path] = None, target_dossier: Optional[Path] = None):
        self.root_dir = root_dir or Path(__file__).resolve().parent.parent
        self.landschap_dir = self.root_dir / "Landschap"
        self.target_dossier = target_dossier or self._resolve_target_dossier()

    def _resolve_target_dossier(self) -> Path:
        # Check standard locations
        candidates = [
            Path(r"E:\LLM_Workspace\Zorgdossier"),
            self.root_dir.parent / "Zorgdossier",
            self.root_dir.parent / "Zaakdossier",
            self.root_dir / "Landschap"
        ]
        for c in candidates:
            if c.exists() and c.is_dir():
                return c
        return self.landschap_dir

    def scan_dossier_for_actors(self, search_path: Optional[Path] = None) -> List[Dict[str, Any]]:
        """Scant Markdown en tekstbestanden in het dossier op personen, rollen, e-mails en detacheringen."""
        scan_dir = search_path or self.target_dossier
        findings = []
        seen_names = set()

        if not scan_dir.exists():
            return findings

        # Loop over alle relevante bestanden
        for p in scan_dir.glob("**/*.*"):
            if p.suffix.lower() not in [".md", ".txt", ".json", ".html"] or ".git" in str(p):
                continue

            try:
                with open(p, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
            except Exception:
                continue

            # Check voor e-mails
            emails = EMAIL_PATTERN.findall(content)
            # Check voor detachering
            det_matches = []
            for dp in DETACHMENT_PATTERNS:
                m = re.findall(dp, content)
                if m:
                    det_matches.extend(m)

            # Eenvoudige extractie van namen rond formele aanhef of handtekeningen
            # Bijv: "Met vriendelijke groet, \n Naam", "Consulent: Naam", etc.
            lines = content.splitlines()
            for i, line in enumerate(lines):
                for rp in ROLE_PATTERNS:
                    if re.search(rp, line):
                        role_match = re.search(rp, line).group(1)
                        # Kijk in dezelfde of volgende 2 regels naar een mogelijke naam
                        context_window = " ".join(lines[max(0, i-1):min(len(lines), i+3)])
                        
                        # Zoek capitalized words (2 of 3 woorden)
                        name_candidates = re.findall(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})\b", context_window)
                        for nc in name_candidates:
                            if nc.lower() in ["met vriendelijke", "gemeente midden", "algemene wet", "college van"]:
                                continue
                            if nc not in seen_names:
                                seen_names.add(nc)
                                findings.append({
                                    "name": nc,
                                    "role": role_match,
                                    "detachment": list(set(det_matches)) if det_matches else None,
                                    "file_origin": p.name,
                                    "emails": list(set(emails))[:2]
                                })
        return findings

    def generate_osint_queries(self, name: str, org: str = "Gemeente") -> Dict[str, str]:
        """Genereert schone, niet-ingelogde zoekopdrachten voor openbare bronnen en registers."""
        return {
            "linkedin_cv": f'site:linkedin.com/in/ "{name}" "{org}"',
            "mandaat_en_besluiten": f'"{name}" ("mandaat" OR "besluit" OR "college" OR "benoeming") filetype:pdf',
            "beroepsregisters": f'"{name}" ("SKJ" OR "Registerplein" OR "BIG-register" OR "Beroepscode")',
            "raadsinformatie": f'"{name}" site:gemeenteraad OR inurl:notubiz OR inurl:ibabs'
        }

    def poll_ris_rss(self, rss_url: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Pollt een openbare raadsinformatie RSS/Atom feed op relevante beleidsthema's."""
        updates = []
        try:
            req = urllib.request.Request(
                rss_url,
                headers={"User-Agent": "CivicCaseEngine/1.0 (Public Oversight Landscape Monitor)"}
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                root = ET.fromstring(response.read())

            # Parse RSS items
            for item in root.findall(".//item")[:limit]:
                title = item.findtext("title", "")
                link = item.findtext("link", "")
                pub_date = item.findtext("pubDate", "")
                description = item.findtext("description", "")

                text_to_check = f"{title} {description}".lower()
                matched_keywords = [kw for kw in KEYWORDS_RIS if kw in text_to_check]

                if matched_keywords:
                    updates.append({
                        "title": title,
                        "link": link,
                        "date": pub_date,
                        "keywords": matched_keywords,
                        "summary": description[:200]
                    })
        except Exception as e:
            updates.append({"error": f"Kon RIS feed niet ophalen: {e}"})

        return updates

    def sync_to_markdown_matrix(self, new_actors: List[Dict[str, Any]], dry_run: bool = False) -> str:
        """Voegt nieuw gedetecteerde actoren toe aan de organisatiekaart als ze nog niet bestaan."""
        org_file = None
        # Zoek eerst in target dossier (bv 21a_Landschap_01_Organisatie.md), anders in engine Landschap
        for cand in [
            self.target_dossier / "21a_Landschap_01_Organisatie.md",
            self.target_dossier / "01_Organisatie.md",
            self.landschap_dir / "01_Organisatie.md"
        ]:
            if cand.exists():
                org_file = cand
                break

        if not org_file:
            return "Geen organisatiekaart bestand gevonden."

        with open(org_file, "r", encoding="utf-8") as f:
            content = f.read()

        added_count = 0
        lines_to_add = []
        for actor in new_actors:
            name = actor["name"]
            if name.lower() not in content.lower():
                det_info = f" (Inhuur: {', '.join(actor['detachment'])})" if actor.get("detachment") else ""
                lines_to_add.append(
                    f"| {actor['role']}{det_info} | {name} | Publiek / Openbaar | Betrokken via dossier | Bron: {actor['file_origin']} ({datetime.now().strftime('%Y-%m-%d')}) |"
                )
                added_count += 1

        if not lines_to_add:
            return f"Geen nieuwe actoren gevonden. Organisatiekaart ({org_file.name}) is up-to-date."

        if dry_run:
            return f"[DRY-RUN] {added_count} actoren klaar voor synchronisatie naar {org_file.name}:\n" + "\n".join(lines_to_add)

        # Voeg toe aan tabel in bestand
        new_content = content
        if "| Post | Naam" in content:
            # Voeg in na de tabel header
            parts = content.split("|---|---|---|---|---|")
            if len(parts) == 2:
                new_table_rows = "\n" + "\n".join(lines_to_add)
                new_content = parts[0] + "|---|---|---|---|---|" + new_table_rows + parts[1]
                with open(org_file, "w", encoding="utf-8") as f:
                    f.write(new_content)
                return f"Succesvol {added_count} actoren gesynchroniseerd naar {org_file.name}."

        return f"Kon tabelstructuur in {org_file.name} niet automatisch patchen. Rijen handmatig toevoegen."

def main():
    parser = argparse.ArgumentParser(description="Civic Case Engine Landscape Realtime Synchronizer")
    parser.add_argument("--scan", action="store_true", help="Scan het actieve dossier op actoren en functies")
    parser.add_argument("--sync", action="store_true", help="Synchroniseer gedetecteerde actoren naar de organisatiekaart")
    parser.add_argument("--dry-run", action="store_true", help="Toon wijzigingen zonder bestanden aan te passen")
    parser.add_argument("--enrich", type=str, help="Genereer OSINT/Beroepsregister zoekopdrachten voor een naam")
    parser.add_argument("--poll-ris", type=str, help="Poll een RIS/Notubiz RSS feed URL op Wmo/sociaal domein updates")
    parser.add_argument("--json", action="store_true", help="Output in machine-readable JSON formaat")
    parser.add_argument("--dossier", type=str, help="Pad naar specifiek zaakdossier")

    args = parser.parse_args()

    target_dossier = Path(args.dossier) if args.dossier else None
    syncer = LandscapeSynchronizer(target_dossier=target_dossier)

    if args.enrich:
        queries = syncer.generate_osint_queries(args.enrich)
        if args.json:
            print(json.dumps(queries, indent=2))
        else:
            print(f"\n=== OSINT & Beroepsscan Zoekopdrachten voor: {args.enrich} ===")
            for k, q in queries.items():
                print(f"[{k.upper()}]:\n  {q}\n")
        return

    if args.poll_ris:
        updates = syncer.poll_ris_rss(args.poll_ris)
        if args.json:
            print(json.dumps(updates, indent=2))
        else:
            print(f"\n=== RIS / Raadsinformatie Updates ({len(updates)} matches) ===")
            for u in updates:
                print(f"- {u.get('date', '')} | {u.get('title', '')}")
                print(f"  Trefwoorden: {', '.join(u.get('keywords', []))}")
                print(f"  Link: {u.get('link', '')}\n")
        return

    if args.scan or args.sync:
        actors = syncer.scan_dossier_for_actors()
        if args.json:
            print(json.dumps(actors, indent=2))
        else:
            print(f"\n=== Gedetecteerde Actoren & Rollen in Dossier ({len(actors)} gevonden) ===")
            for a in actors:
                det = f" [Inhuur: {', '.join(a['detachment'])}]" if a.get('detachment') else ""
                print(f"* {a['name']} — {a['role']}{det} (gevonden in: {a['file_origin']})")
                if a.get("emails"):
                    print(f"  E-mail: {', '.join(a['emails'])}")

        if args.sync:
            res = syncer.sync_to_markdown_matrix(actors, dry_run=args.dry_run)
            print(f"\n[SYNCHRONISATIE RESULTAAT]:\n{res}")
        return

    # Default output als er geen vlaggen zijn
    parser.print_help()

if __name__ == "__main__":
    main()
