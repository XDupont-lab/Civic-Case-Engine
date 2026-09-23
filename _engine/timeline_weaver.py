#!/usr/bin/env python3
"""
CIVIC CASE ENGINE — CIVIC LEGAL KERNEL (FORENSIC TIMELINE & INTEGRITY WEAVER v2.0)
Civic Exoskeleton Forensic Evidence Engine.
Pure Python Standard Library (Zero External Dependencies).

Rol in de architectuur:
Het deterministische data-fundament van de Civic Legal Kernel. Extraheert en correleert
ongestructureerde data tot een onweerlegbare chronologie met SHA-256 integriteit.

Architectuur:
- Ingest van Bank-CSV's (ING, Rabo, ABN, Triodos, Bunq)
- Ingest van WhatsApp (zowel raw .txt exports als Markdown transcripties)
- Ingest van Android Call-logs (SQLite / content query epoch dumps)
- Ingest van E-mails & Brieven (.eml en brief-markdowns)
- Ingest van algemene dossiernotities

Forensische integriteit:
- SHA-256 verificatiehash per bronbestand
- Deduplicatie van overlappende gebeurtenissen
- Juridische verankering van institutionele stiltes (Awb, Wmo, AVG)
- Geen datum-fabricage: strikte datumvalidatie
"""

import os
import sys
import csv
import re
import json
import hashlib
import email
from email import policy
from email.parser import BytesParser
from datetime import datetime, timezone
from pathlib import Path
from collections import defaultdict

NL_MONTHS = {
    "januari": 1, "jan": 1,
    "februari": 2, "feb": 2,
    "maart": 3, "mrt": 3,
    "april": 4, "apr": 4,
    "mei": 5,
    "juni": 6, "jun": 6,
    "juli": 7, "jul": 7,
    "augustus": 8, "aug": 8,
    "september": 9, "sep": 9, "sept": 9,
    "oktober": 10, "okt": 10,
    "november": 11, "nov": 11,
    "december": 12, "dec": 12
}

def sha256_file(filepath):
    """Berekent SHA-256 hash van een bestand voor forensische integriteit."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

class TimelineEvent:
    def __init__(self, date_dt, time_str, domain, actor, summary, raw_quote, source_file, file_hash="", severity="Normaal"):
        self.date_dt = date_dt
        self.iso_date = date_dt.strftime("%Y-%m-%d") if date_dt else "Onbekend"
        self.time_str = time_str or ""
        self.domain = domain        # Zorg, Financien, Huisvesting, Bestuursrecht, Correspondentie
        self.actor = actor
        self.summary = summary
        self.raw_quote = raw_quote
        self.source_file = source_file
        self.file_hash = file_hash[:12] if file_hash else ""
        self.severity = severity    # Normaal, Ketenbreuk, Besluit, Betaling, Stilte

    def signature(self):
        """Unieke signature voor deduplicatie."""
        clean_s = re.sub(r"\W+", "", self.summary.lower())
        return f"{self.iso_date}_{self.actor.lower()}_{clean_s[:40]}"

    def to_dict(self):
        return {
            "iso_date": self.iso_date,
            "time": self.time_str,
            "domain": self.domain,
            "actor": self.actor,
            "summary": self.summary,
            "raw_quote": self.raw_quote,
            "source_file": self.source_file,
            "file_hash": self.file_hash,
            "severity": self.severity
        }

class TimelineWeaver:
    def __init__(self):
        self.events = []
        self.seen_signatures = set()
        self.source_hashes = {} # filepath -> sha256
        self.parse_warnings = []

    def add_event(self, event):
        sig = event.signature()
        if sig not in self.seen_signatures:
            self.seen_signatures.add(sig)
            self.events.append(event)

    def parse_dutch_date(self, text, fallback_year=None):
        """
        Robuuste datum-parser:
        - ISO: 2026-05-12, 1998-11-20
        - NL-notatie: 12-05-2026, 12/05/2026, 12.05.2026
        - Tekstueel: '12 mei 2026', '30 januari 2024'
        Geen willekeurige jaartal-fabricage.
        """
        # 1. ISO check (1900-2099)
        m_iso = re.search(r"\b((?:19|20)\d{2})-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])\b", text)
        if m_iso:
            try:
                return datetime(int(m_iso.group(1)), int(m_iso.group(2)), int(m_iso.group(3)))
            except ValueError:
                pass

        # 2. NL numeriek: DD-MM-YYYY of DD/MM/YYYY
        m_num = re.search(r"\b(0?[1-9]|[12]\d|3[01])[-/.](0?[1-9]|1[0-2])[-/.](19\d{2}|20\d{2})\b", text)
        if m_num:
            try:
                return datetime(int(m_num.group(3)), int(m_num.group(2)), int(m_num.group(1)))
            except ValueError:
                pass

        # 3. NL tekstueel: '12 mei 2026' of '12 mei' met expliciet fallback_year
        m_nl = re.search(r"\b(0?[1-9]|[12]\d|3[01])\s+([a-zA-Z]{3,10})(?:\s+((?:19|20)\d{2}))?\b", text)
        if m_nl:
            day = int(m_nl.group(1))
            month_str = m_nl.group(2).lower().rstrip(".")
            year_str = m_nl.group(3)
            if month_str in NL_MONTHS:
                month = NL_MONTHS[month_str]
                year = int(year_str) if year_str else fallback_year
                if year:
                    try:
                        return datetime(year, month, day)
                    except ValueError:
                        pass
        return None

    def ingest_bank_csv(self, file_path):
        """Ondersteunt ING, Rabobank, ABN AMRO, Triodos, Bunq."""
        p = Path(file_path)
        if not p.exists():
            return
        
        f_hash = sha256_file(p)
        self.source_hashes[p.name] = f_hash

        with open(p, mode="r", encoding="utf-8-sig", errors="replace") as f:
            first_line = f.readline()
            delim = ";" if ";" in first_line else ","
            f.seek(0)
            reader = csv.DictReader(f, delimiter=delim)
            
            for row in reader:
                # Kolommen normaliseren
                row_clean = {k.strip().lower(): v.strip() for k, v in row.items() if k}
                
                # Datum extractie
                d_str = (row_clean.get("datum") or row_clean.get("date") or 
                         row_clean.get("transactiedatum") or row_clean.get("boekdatum") or "")
                
                dt = None
                # Probeer formele formaten
                for fmt in ("%Y%m%d", "%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%d.%m.%Y"):
                    try:
                        dt = datetime.strptime(d_str.strip(), fmt)
                        break
                    except ValueError:
                        pass
                
                if not dt:
                    d_clean = re.sub(r"[^0-9]", "", d_str)
                    if len(d_clean) == 8:
                        # Als formaat YYYYMMDD is:
                        if int(d_clean[:4]) in range(1990, 2040):
                            try: dt = datetime(int(d_clean[:4]), int(d_clean[4:6]), int(d_clean[6:8]))
                            except ValueError: pass
                        # Als formaat DDMMYYYY is:
                        elif int(d_clean[4:8]) in range(1990, 2040):
                            try: dt = datetime(int(d_clean[4:8]), int(d_clean[2:4]), int(d_clean[0:2]))
                            except ValueError: pass

                if not dt:
                    continue

                # Tegenpartij & Omschrijving
                naam = (row_clean.get("naam / omschrijving") or row_clean.get("naam") or 
                        row_clean.get("naam tegenpartij") or row_clean.get("tegenpartij") or 
                        row_clean.get("counterparty") or "")
                
                mededeling = (row_clean.get("mededelingen") or row_clean.get("omschrijving") or 
                              row_clean.get("verrijking") or row_clean.get("details") or "")
                
                bedrag_str = (row_clean.get("bedrag (eur)") or row_clean.get("bedrag") or 
                              row_clean.get("amount") or "0").replace("€", "").strip()
                
                af_bij = (row_clean.get("af bij") or row_clean.get("af/bij") or 
                          row_clean.get("credit/debit") or ("Af" if "-" in bedrag_str else "Bij"))

                comb = f"{naam} {mededeling}".lower()
                domain = None
                severity = "Betaling"
                summary = ""

                # Sleutelcategorieën
                if re.search(r"huur|woningstichting|woonstichting|woningbouw|verhuur|corporatie", comb):
                    domain = "Huisvesting"
                    summary = f"Huurbetaling: € {bedrag_str} aan {naam}"
                elif re.search(r"\bcak\b|centraal administratie kantoor", comb):
                    domain = "Financien"
                    summary = f"CAK Inhouding/Premie: € {bedrag_str} ({naam})"
                    severity = "Besluit"
                elif re.search(r"flanderijn|syncasso|cannock|deurwaarder|ggn|intrum|coeo", comb):
                    domain = "Financien"
                    summary = f"Incasso/Deurwaarder betaling: € {bedrag_str} ({naam})"
                elif re.search(r"participatiewet|bijstand|sociale zaken|sozawe|gemeente|uwv|svb", comb):
                    domain = "Financien"
                    summary = f"Inkomensstroom (Uitkering/UWV): € {bedrag_str} ({naam})"
                elif re.search(r"thuisgenoten|curaxl|zorg|huisarts|apotheek|ziekenhuis|martini|umcg", comb):
                    domain = "Zorg"
                    summary = f"Zorg-betaling/declaratie: € {bedrag_str} ({naam})"

                if domain:
                    self.add_event(TimelineEvent(
                        date_dt=dt,
                        time_str="",
                        domain=domain,
                        actor=naam or "Bankinstelling",
                        summary=summary,
                        raw_quote=f"Bedrag: {bedrag_str} ({af_bij}), Mededeling: {mededeling[:140]}",
                        source_file=p.name,
                        file_hash=f_hash,
                        severity=severity
                    ))

    def ingest_whatsapp_file(self, file_path):
        """Ondersteunt zowel ruwe .txt WhatsApp exports als Markdown transcripties."""
        p = Path(file_path)
        if not p.exists():
            return
        
        f_hash = sha256_file(p)
        self.source_hashes[p.name] = f_hash
        current_dt = None

        # Regexes voor ruwe exports:
        # Formaat 1: [12-05-2026, 14:23:45] Naam: Bericht
        # Formaat 2: 12-05-2026, 14:23 - Naam: Bericht
        re_raw1 = re.compile(r"^\[(\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4}),?\s+(\d{1,2}:\d{2}(?::\d{2})?)\]\s+([^:]+):\s*(.*)$")
        re_raw2 = re.compile(r"^(\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4}),?\s+(\d{1,2}:\d{2})\s+-\s+([^:]+):\s*(.*)$")
        # Markdown formaat: * **Naam (HH:MM):** Bericht
        re_md = re.compile(r"^\*\s+\*\*([^(]+)\s*(?:\(([^)]+)\))?:\*\*\s*(.*)$")

        with open(p, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                # Header check in markdown
                if line.startswith("###"):
                    dt = self.parse_dutch_date(line)
                    if dt:
                        current_dt = dt
                    continue

                dt_event = None
                time_str = ""
                actor = ""
                quote = ""

                # Test raw export 1
                m1 = re_raw1.match(line)
                if m1:
                    d_raw, time_str, actor, quote = m1.groups()
                    dt_event = self.parse_dutch_date(d_raw)

                # Test raw export 2
                if not dt_event:
                    m2 = re_raw2.match(line)
                    if m2:
                        d_raw, time_str, actor, quote = m2.groups()
                        dt_event = self.parse_dutch_date(d_raw)

                # Test markdown format
                if not dt_event and current_dt:
                    mmd = re_md.match(line)
                    if mmd:
                        actor = mmd.group(1).strip()
                        time_str = mmd.group(2).strip() if mmd.group(2) else ""
                        quote = mmd.group(3).strip()
                        dt_event = current_dt

                if dt_event and quote:
                    q_low = quote.lower()
                    domain = "Correspondentie"
                    severity = "Normaal"

                    if any(w in q_low for w in ["zorg", "indicatie", "marcel", "ellen", "willie", "thuisgenoten", "curaxl", "huisarts", "beatrixoord", "hulp", "wmo"]):
                        domain = "Zorg"
                    elif any(w in q_low for w in ["huur", "woning", "corporatie", "verhuur"]):
                        domain = "Huisvesting"
                    elif any(w in q_low for w in ["cak", "geld", "inkomen", "uitkering", "deurwaarder", "flanderijn"]):
                        domain = "Financien"
                    elif any(w in q_low for w in ["besluit", "beschikking", "gemeente", "bezwaar", "verordening"]):
                        domain = "Bestuursrecht"

                    # Ketenbreuken markeren
                    if any(w in q_low for w in ["stopgezet", "opgezegd", "afspraken niet nagekomen", "voelde ongemakkelijk", "plots contact verbroken", "niet meer langskomen"]):
                        severity = "Ketenbreuk"

                    summary = f"WhatsApp {actor}: {quote[:90]}..." if len(quote) > 90 else f"WhatsApp {actor}: {quote}"
                    self.add_event(TimelineEvent(
                        date_dt=dt_event,
                        time_str=time_str,
                        domain=domain,
                        actor=actor,
                        summary=summary,
                        raw_quote=quote,
                        source_file=p.name,
                        file_hash=f_hash,
                        severity=severity
                    ))

    def ingest_call_log(self, file_path):
        """Leest Android SQLite / content query call logs met epoch-ms timestamps."""
        p = Path(file_path)
        if not p.exists():
            return
        
        f_hash = sha256_file(p)
        self.source_hashes[p.name] = f_hash

        known_contacts = {
            "0201234567": "Dr. Voorbeeld (Huisartsenpraktijk)",
            "0612345678": "Begeleider A (Zorgorganisatie X)",
            "0888889450": "Gemeente / Instantie",
            "+31888889450": "Gemeente / Instantie"
        }

        with open(p, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                m = re.search(r"number=([^,]+).*?date=(\d+).*?duration=(\d+).*?type=(\d+)", line)
                if m:
                    num = m.group(1).strip()
                    epoch_ms = int(m.group(2).strip())
                    duration_sec = int(m.group(3).strip())
                    call_type = int(m.group(4).strip())

                    type_str = {1: "Inkomend", 2: "Uitgaand", 3: "Gemist", 5: "Geweigerd"}.get(call_type, "Oproep")
                    # Timezone aware local conversion
                    dt = datetime.fromtimestamp(epoch_ms / 1000.0)
                    contact_name = known_contacts.get(num, f"Nummer {num}")

                    domain = "Zorg" if any(w in contact_name for w in ["Huisarts", "Zorgorganisatie", "Zorg", "Begeleider"]) else "Correspondentie"
                    summary = f"Telefoongesprek ({type_str}, {duration_sec}s) met {contact_name}"

                    self.add_event(TimelineEvent(
                        date_dt=dt,
                        time_str=dt.strftime("%H:%M"),
                        domain=domain,
                        actor=contact_name,
                        summary=summary,
                        raw_quote=f"Nummer: {num}, Duur: {duration_sec}s, Type: {type_str}",
                        source_file=p.name,
                        file_hash=f_hash,
                        severity="Normaal"
                    ))

    def ingest_email_file(self, file_path):
        """Leest .eml e-mails en extracteert formele headers en citaten."""
        p = Path(file_path)
        if not p.exists():
            return
        
        f_hash = sha256_file(p)
        self.source_hashes[p.name] = f_hash

        try:
            with open(p, "rb") as f:
                msg = BytesParser(policy=policy.default).parse(f)
            
            date_raw = msg.get("Date")
            from_raw = msg.get("From", "Onbekend")
            subj_raw = msg.get("Subject", "(Geen onderwerp)")
            
            dt = None
            if date_raw:
                try:
                    dt = email.utils.parsedate_to_datetime(date_raw)
                    # Convert to naive local
                    dt = dt.astimezone().replace(tzinfo=None)
                except Exception:
                    pass

            if dt:
                domain = "Bestuursrecht" if any(w in (from_raw + subj_raw).lower() for w in ["gemeente", "wmo", "besluit", "beschikking", "cak", "flanderijn"]) else "Correspondentie"
                summary = f"E-mail van {from_raw}: {subj_raw}"
                self.add_event(TimelineEvent(
                    date_dt=dt,
                    time_str=dt.strftime("%H:%M"),
                    domain=domain,
                    actor=from_raw[:50],
                    summary=summary,
                    raw_quote=f"Onderwerp: {subj_raw}, Van: {from_raw}",
                    source_file=p.name,
                    file_hash=f_hash,
                    severity="Besluit" if "besluit" in subj_raw.lower() else "Normaal"
                ))
        except Exception as e:
            self.parse_warnings.append(f"Fout bij inlezen .eml {p.name}: {e}")

    def ingest_generic_markdown(self, file_path):
        """Scant willekeurige Markdown dossiernotities op gedateerde paragrafen en feiten."""
        p = Path(file_path)
        if not p.exists() or p.name.startswith(("00_Master_", "REVIEW_")):
            return

        f_hash = sha256_file(p)
        self.source_hashes[p.name] = f_hash

        with open(p, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if len(line) < 15:
                    continue
                
                dt = self.parse_dutch_date(line)
                if dt:
                    clean_text = re.sub(r"^[\s#*\-]+", "", line)
                    domain = "Zorg" if any(w in clean_text.lower() for w in ["arts", "zorg", "wmo", "nah", "ziek"]) else "Correspondentie"
                    self.add_event(TimelineEvent(
                        date_dt=dt,
                        time_str="",
                        domain=domain,
                        actor=f"Dossiernotitie ({p.stem[:25]})",
                        summary=clean_text[:110],
                        raw_quote=clean_text[:200],
                        source_file=p.name,
                        file_hash=f_hash,
                        severity="Normaal"
                    ))

    def detect_anomalies(self):
        """
        Detecteert juridisch relevante stiltes en ketenbreuken:
        - Stilte > 30 dagen (AVG termijn ex art. 12 lid 3 AVG)
        - Stilte > 42 dagen (Wmo onderzoeksfase ex art. 2.3.2 lid 1 Wmo)
        - Stilte > 56 dagen (Fatale beslistermijn Awb ex art. 4:13 Awb)
        """
        sorted_events = sorted([e for e in self.events if e.date_dt], key=lambda x: x.date_dt)
        anomalies = []

        for i in range(len(sorted_events) - 1):
            e1 = sorted_events[i]
            e2 = sorted_events[i+1]
            diff_days = (e2.date_dt - e1.date_dt).days

            if diff_days >= 30 and (e1.domain in ["Zorg", "Bestuursrecht"] or e2.domain in ["Zorg", "Bestuursrecht"]):
                jur_grondslag = "Art. 4:13 Awb (Redelijke beslistermijn geschonden)"
                if diff_days >= 56:
                    jur_grondslag = "Art. 2.3.5 Wmo / 4:17 Awb (Fatale 8-wekentermijn overschreden; dwangsom verschuldigd)"
                elif diff_days >= 42:
                    jur_grondslag = "Art. 2.3.2 lid 1 Wmo (Onderzoekstermijn 6 weken overschreden)"
                elif "avg" in e1.summary.lower():
                    jur_grondslag = "Art. 12 lid 3 AVG (Wettelijke reactietermijn van 30 dagen overschreden)"

                anomalies.append({
                    "type": "Institutionele Stilte",
                    "start": e1.iso_date,
                    "end": e2.iso_date,
                    "duration_days": diff_days,
                    "jur_grond": jur_grondslag,
                    "context": f"Stilte van {diff_days} dagen na {e1.actor} ({e1.summary}) tot {e2.actor} ({e2.summary})."
                })

        # Ketenbreuken filteren
        breaks = [e for e in sorted_events if e.severity == "Ketenbreuk"]
        for b in breaks:
            anomalies.append({
                "type": "Ketenbreuk / Zorgval",
                "start": b.iso_date,
                "end": b.iso_date,
                "duration_days": 0,
                "jur_grond": "Art. 2.3.10 Wmo jo. Art. 3:46 Awb (Onrechtmatige feitelijke beëindiging zonder besluit)",
                "context": f"Breuk geconstateerd bij {b.actor}: \"{b.raw_quote[:150]}\""
            })

        return anomalies

    def generate_markdown(self, output_path=None):
        """Genereert de complete 00_Master_Chronologie.md met integriteitsregister."""
        sorted_events = sorted([e for e in self.events if e.date_dt], key=lambda x: (x.date_dt, x.time_str))
        anomalies = self.detect_anomalies()

        md = []
        md.append("# 00 — Master Chronologie & Forensische Ketenmatrix\n")
        md.append(f"**Gegenereerd:** {datetime.now().strftime('%Y-%m-%d %H:%M')}  ")
        md.append(f"**Totaal aantal unieke geverifieerde feiten:** {len(sorted_events)}  ")
        if sorted_events:
            md.append(f"**Gedekte Periode:** {sorted_events[0].iso_date} tot {sorted_events[-1].iso_date}\n")
        md.append("---\n")

        # 1. Forensisch Integriteitsregister
        md.append("## 1. Forensisch Integriteitsregister (SHA-256 Verificatie)\n")
        md.append("| Bronbestand | SHA-256 Checksum |")
        md.append("|---|---|")
        for fname, fhash in sorted(self.source_hashes.items()):
            md.append(f"| `{fname}` | `{fhash}` |")
        md.append("\n---\n")

        # 2. Signaaltabel Anomalieën
        if anomalies:
            md.append("## 2. Gedetecteerde Zorgbreuken & Institutionele Stiltes\n")
            md.append("| Type | Periode | Duur | Juridische Kwalificatie & Grondslag | Feitelijke Context |")
            md.append("|---|---|---|---|---|")
            for a in anomalies:
                per_str = f"{a['start']}" if a['duration_days'] == 0 else f"{a['start']} t/m {a['end']}"
                duur_str = f"{a['duration_days']} dagen" if a['duration_days'] > 0 else "Direct"
                md.append(f"| **{a['type']}** | {per_str} | {duur_str} | *{a['jur_grond']}* | {a['context']} |")
            md.append("\n---\n")

        # 3. Integrale Chronologische Ketenmatrix
        md.append("## 3. Integrale Forensische Ketenmatrix\n")
        md.append("| Datum (Tijd) | Domein | Actor | Feitelijke Gebeurtenis | Bron [Hash] & Hard Citaat |")
        md.append("|---|---|---|---|---|")
        for e in sorted_events:
            t_str = f" ({e.time_str})" if e.time_str else ""
            dt_label = f"**{e.iso_date}**{t_str}"
            sev_marker = " ⚠️" if e.severity == "Ketenbreuk" else ""
            quote_clean = e.raw_quote.replace("|", "/").replace("\n", " ")[:140]
            hash_tag = f"[{e.file_hash}]" if e.file_hash else ""
            md.append(f"| {dt_label}{sev_marker} | `{e.domain}` | {e.actor} | {e.summary} | *{e.source_file}* {hash_tag}: \"{quote_clean}\" |")

        result = "\n".join(md)

        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(result)
            print(f"[+] Master Chronologie succesvol gegenereerd: {output_path}")

        # JSON Export
        json_path = Path(output_path).with_suffix(".json") if output_path else None
        if json_path:
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump([e.to_dict() for e in sorted_events], f, indent=2)
            print(f"[+] Machine-leesbare JSON opgeslagen: {json_path}")

        return result

def auto_scan_directory(target_dir, output_file=None):
    weaver = TimelineWeaver()
    tdir = Path(target_dir)

    print(f"[*] Forensische scan gestart voor: {tdir}")
    
    # 1. Bank CSVs
    for f in tdir.glob("**/*.csv"):
        print(f"  -> Ingesting Bank CSV: {f.name}")
        weaver.ingest_bank_csv(f)

    # 2. WhatsApp (.txt en .md)
    for f in tdir.glob("**/*whatsapp*"):
        if f.suffix in [".txt", ".md"]:
            print(f"  -> Ingesting WhatsApp: {f.name}")
            weaver.ingest_whatsapp_file(f)

    # 3. Call-logs
    for f in tdir.glob("**/call_log*.txt"):
        print(f"  -> Ingesting Call Log: {f.name}")
        weaver.ingest_call_log(f)

    # 4. E-mails (.eml)
    for f in tdir.glob("**/*.eml"):
        print(f"  -> Ingesting E-mail: {f.name}")
        weaver.ingest_email_file(f)

    # 5. Overige gedateerde dossiers
    for f in tdir.glob("**/*.md"):
        if not any(x in f.name.lower() for x in ["whatsapp", "00_master", "review_"]):
            weaver.ingest_generic_markdown(f)

    if not output_file:
        output_file = tdir / "00_Master_Chronologie.md"

    weaver.generate_markdown(output_file)
    print(f"[+] Succes: {len(weaver.events)} unieke feiten geweven.")

if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

    if len(sys.argv) < 2:
        print("Gebruik: python timeline_weaver.py <map_met_bronnen> [optioneel_output_bestand]")
        sys.exit(1)
    
    in_dir = sys.argv[1]
    out_f = sys.argv[2] if len(sys.argv) > 2 else None
    auto_scan_directory(in_dir, out_f)
