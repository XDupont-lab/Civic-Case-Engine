#!/usr/bin/env python3
"""
CIVIC HELPER — BANK LEDGER AUDITOR & KETENGROOTBOEK BRIDGE
100% Python Standard Library (No external dependencies).

Doel: Automatische extractie van institutionele patronen en export naar Beancount:
1. CAMT.053 XML & CSV Parsing (ING, Rabobank, ABN AMRO, SNS, ASN, Triodos)
2. Inkomensstromen & Verborgen Bronheffingen (Participatiewet / UWV / CAK / Beslagvrije voet)
3. Huurbetalingen & Punctualiteitscertificaat (Bescherming art. 7:231 BW)
4. Deurwaarders- & Incassodossiers (Dossiernummers en betaalgeschiedenis)
5. Toeslagen, Zorgverzekeraars & Lokale Belastingen
6. Automatische export naar Beancount-ledger (.beancount) en Ketengrootboek-koppeling
"""

import sys
import os
import csv
import re
from datetime import datetime
from decimal import Decimal
from collections import defaultdict
from typing import Dict, List, Optional, Any, Tuple

# Lokale modules
try:
    from camt_parser import is_camt_xml, parse_camt
    from beancount_exporter import (
        format_date_iso,
        format_amount,
        classify_transaction,
        generate_beancount_ledger,
        export_transactions_to_beancount_file
    )
except ImportError:
    from _engine.camt_parser import is_camt_xml, parse_camt
    from _engine.beancount_exporter import (
        format_date_iso,
        format_amount,
        classify_transaction,
        generate_beancount_ledger,
        export_transactions_to_beancount_file
    )

def parse_csv(file_path: str) -> Dict[str, Any]:
    """
    Parseert een bank-CSV van Nederlandse banken (ING, Rabobank, ABN AMRO, SNS, ASN, Triodos, etc.)
    en normaliseert deze naar een gestandaardiseerde lijst van transacties.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Bestand niet gevonden: {file_path}")

    # Detecteer encoding
    with open(file_path, "rb") as f:
        raw_bytes = f.read(8192)
    encoding = "utf-8-sig"
    for enc in ("utf-8-sig", "utf-8", "cp1252", "iso-8859-1"):
        try:
            raw_bytes.decode(enc)
            encoding = enc
            break
        except UnicodeDecodeError:
            continue

    transactions: List[Dict[str, Any]] = []
    own_iban = ""

    with open(file_path, mode="r", encoding=encoding, errors="replace") as f:
        first_line = f.readline()
        # Delimiter detectie
        if "\t" in first_line:
            delimiter = "\t"
        elif ";" in first_line:
            delimiter = ";"
        else:
            delimiter = ","
        f.seek(0)

        reader = csv.DictReader(f, delimiter=delimiter)
        for row in reader:
            # 1. Datum bepalen
            d_raw = (
                row.get("Datum") or row.get("datum") or row.get("Date") or 
                row.get("Transactiedatum") or row.get("Rentedatum") or ""
            ).strip()
            iso_date = format_date_iso(d_raw)

            # 2. Rekeningnummers
            rekening = (
                row.get("Rekening") or row.get("IBAN/BBAN") or 
                row.get("Rekeningnummer") or ""
            ).strip()
            if rekening and not own_iban and re.match(r"^[A-Z]{2}\d{2}", rekening):
                own_iban = rekening

            tegenrekening = (
                row.get("Tegenrekening") or row.get("Tegenrekening IBAN/BBAN") or 
                row.get("Tegenrekeningnummer") or ""
            ).strip()

            # 3. Naam tegenpartij
            naam = (
                row.get("Naam / Omschrijving") or row.get("Naam") or 
                row.get("Naam tegenpartij") or row.get("Tegenpartij") or 
                row.get("Naam tegenrekening") or ""
            ).strip()

            # 4. Mededelingen / Omschrijving
            med_parts = []
            for col in ("Mededelingen", "Omschrijving", "Omschrijving-1", "Omschrijving-2", "Omschrijving-3", "Mutatiesoort"):
                val = row.get(col)
                if val and val.strip():
                    med_parts.append(val.strip())
            mededelingen = " | ".join(med_parts)

            # Speciale check ABN AMRO waar naam soms in omschrijving staat
            if not naam and "TRTP/" in mededelingen:
                m_naam = re.search(r"NAME/([^/]+)", mededelingen)
                if m_naam:
                    naam = m_naam.group(1).strip()

            # 5. Bedrag en Af/Bij
            bedrag_raw = (
                row.get("Bedrag (EUR)") or row.get("Bedrag") or 
                row.get("Amount") or row.get("Transactiebedrag") or "0"
            ).strip()

            af_bij_raw = (
                row.get("Af Bij") or row.get("Af/Bij") or 
                row.get("Af / Bij") or row.get("Credit/Debit") or ""
            ).strip().lower()

            clean_amount = format_amount(bedrag_raw)

            if af_bij_raw in ("af", "debit", "d", "minus", "-"):
                af_bij = "Af"
            elif af_bij_raw in ("bij", "credit", "c", "plus", "+"):
                af_bij = "Bij"
            elif "-" in bedrag_raw:
                af_bij = "Af"
            else:
                af_bij = "Bij"

            transactions.append({
                "datum": iso_date,
                "bedrag": clean_amount,
                "af_bij": af_bij,
                "naam": naam,
                "tegenrekening": tegenrekening,
                "mededelingen": mededelingen,
                "end_to_end_id": "",
                "mandate_id": "",
                "currency": "EUR",
                "bron": "CSV"
            })

    return {
        "iban": own_iban,
        "statement_id": "",
        "datum": "",
        "opening_balance": None,
        "closing_balance": None,
        "transactions": transactions
    }

def analyze_bank_file(file_path: str, export_beancount: bool = True, custom_out: Optional[str] = None):
    """
    Voert forensische audit uit op bankbestand (CSV of CAMT.053 XML)
    en exporteert direct een sluitend Beancount grootboekbestand.
    """
    if not os.path.exists(file_path):
        print(f"[FOUT] Bestand niet gevonden: {file_path}")
        sys.exit(1)

    print("=" * 78)
    print("CIVIC HELPER — FORENSISCHE BANK AUDITOR & KETENGROOTBOEK BRIDGE")
    print("=" * 78)

    # 1. Parsen
    if is_camt_xml(file_path):
        print(f"[*] Formaat gedetecteerd: ISO 20022 CAMT.053 XML ({os.path.basename(file_path)})")
        data = parse_camt(file_path)
    else:
        print(f"[*] Formaat gedetecteerd: Bank CSV Export ({os.path.basename(file_path)})")
        data = parse_csv(file_path)

    transactions = data.get("transactions", [])
    own_iban = data.get("iban", "")
    op_balance = data.get("opening_balance")
    cl_balance = data.get("closing_balance")

    total_tx = len(transactions)
    if total_tx == 0:
        print("[!] Geen transacties gevonden in bestand.")
        return

    dates = [t["datum"] for t in transactions if t.get("datum")]
    date_min = min(dates) if dates else "Onbekend"
    date_max = max(dates) if dates else "Onbekend"

    print(f"[*] Rekening IBAN       : {own_iban or 'Niet gespecificeerd'}")
    print(f"[*] Totaal transacties  : {total_tx}")
    print(f"[*] Audit-periode       : {date_min} tot {date_max}")
    if op_balance:
        print(f"[*] Beginstand afschrift: EUR {op_balance['amount']:.2f} ({op_balance['date']})")
    if cl_balance:
        print(f"[*] Eindstand afschrift : EUR {cl_balance['amount']:.2f} ({cl_balance['date']})")
    print("-" * 78)

    # Categoriseer transacties voor forensische analyse
    records = defaultdict(list)
    dossier_nummers = defaultdict(set)

    for tx in transactions:
        cat, acc, keten = classify_transaction(
            tx.get("naam", ""), 
            tx.get("mededelingen", ""), 
            tx.get("tegenrekening", ""), 
            tx.get("af_bij", "Af")
        )
        tx_entry = {**tx, "categorie": cat, "account": acc, "keten": keten}
        records[cat].append(tx_entry)

        # Zoek dossiernummers / kenmerken in mededelingen
        full_text = f"{tx.get('naam', '')} {tx.get('mededelingen', '')}"
        m_dos = re.findall(r"(?:dossier|kenmerk|zaak|dossiernr|ref)\s*[:#.]?\s*([A-Za-z0-9\-./]{5,25})", full_text, re.I)
        for d in m_dos:
            if not re.match(r"^(IBAN|BIC|NL\d{2}|EUR)$", d, re.I):
                dossier_nummers[cat].add(d)

    # 1. Huurcontrole & Punctualiteit
    huur_tx = [r for r in records["Huur"] if r["af_bij"] == "Af"]
    print(f"\n[1] HUURBETALINGEN & BESTAANSZEKERHEID ({len(huur_tx)} geregistreerde betalingen)")
    if huur_tx:
        # Sorteer chronologisch
        huur_sorted = sorted(huur_tx, key=lambda x: x["datum"], reverse=True)
        laatste = huur_sorted[0]
        print(f"  * Laatste huurbetaling: {laatste['datum']} | EUR {laatste['bedrag']:.2f} aan '{laatste['naam']}'")
        print(f"  * Forensisch bewijs: {len(huur_tx)} huurbetalingen aangetroffen.")
        print(f"  * Juridische betekenis: Documenteert structureel huurderschap en betalingsdiscipline (art. 7:231 BW).")
    else:
        print("  * Geen expliciete huurtransacties gevonden.")

    # 2. Uitkering & Bronheffing
    uitk_tx = [r for r in transactions if "Uitkering" in classify_transaction(r["naam"], r["mededelingen"], r["tegenrekening"], r["af_bij"])[0] and r["af_bij"] == "Bij"]
    print(f"\n[2] INKOMENSSTROOM & UITKERINGEN ({len(uitk_tx)} bijschrijvingen)")
    if uitk_tx:
        uitk_sorted = sorted(uitk_tx, key=lambda x: x["datum"], reverse=True)
        for r in uitk_sorted[:3]:
            print(f"  * {r['datum']} | EUR {r['bedrag']:.2f} | {r['naam']} | {r['mededelingen'][:60]}")
        print("  * Audit-toets Bestaanszekerheid:")
        print("    Controleer of het ontvangen bedrag lager is dan de norm conform Participatiewet.")
        print("    Een structureel lagere overmaking duidt op geautomatiseerde verrekening of bronheffing.")
    else:
        print("  * Geen directe uitkeringsbijschrijvingen aangetroffen.")

    # 3. Deurwaarders & Incasso
    inc_tx = [r for r in transactions if "Incasso" in classify_transaction(r["naam"], r["mededelingen"], r["tegenrekening"], r["af_bij"])[0]]
    print(f"\n[3] DEURWAARDERS & INCASSO-DOSSIERS ({len(inc_tx)} registraties)")
    if inc_tx:
        inc_sorted = sorted(inc_tx, key=lambda x: x["datum"], reverse=True)
        for r in inc_sorted[:5]:
            print(f"  * {r['datum']} | {r['af_bij']} EUR {r['bedrag']:.2f} | {r['naam']} | {r['mededelingen'][:60]}")
        if dossier_nummers["Incasso_Deurwaarder"] or any("Incasso" in k and dossier_nummers[k] for k in dossier_nummers):
            alle_dossiers = set()
            for k, v in dossier_nummers.items():
                if "Incasso" in k:
                    alle_dossiers.update(v)
            if alle_dossiers:
                print(f"  * Geëxtraheerde dossierkenmerken: {', '.join(sorted(alle_dossiers))}")
    else:
        print("  * Geen directe incasso- of deurwaarderstransacties aangetroffen.")

    # 4. CAK & Zorg
    cak_tx = [r for r in transactions if "CAK" in classify_transaction(r["naam"], r["mededelingen"], r["tegenrekening"], r["af_bij"])[0]]
    print(f"\n[4] CAK & ZORGVOORZIENINGEN ({len(cak_tx)} registraties)")
    if cak_tx:
        cak_sorted = sorted(cak_tx, key=lambda x: x["datum"], reverse=True)
        for r in cak_sorted[:3]:
            print(f"  * {r['datum']} | {r['af_bij']} EUR {r['bedrag']:.2f} | {r['naam']} | {r['mededelingen'][:60]}")
        print("  * Juridische toets: Betreft dit bestuursrechtelijke premie ex art. 18d Zvw?")
        print("    Koppeling met Ketengrootboek: POST-CAK-SOZAWE-002 (toets op beslagvrije voet ex art. 475d Rv).")
    else:
        print("  * Geen directe CAK-transacties aangetroffen.")

    # 5. Toeslagen (Belastingdienst/Toeslagen)
    toeslag_tx = [r for r in transactions if "Toeslagen" in classify_transaction(r["naam"], r["mededelingen"], r["tegenrekening"], r["af_bij"])[0]]
    print(f"\n[5] DIENST TOESLAGEN & VERREKENINGEN ({len(toeslag_tx)} registraties)")
    if toeslag_tx:
        toeslag_sorted = sorted(toeslag_tx, key=lambda x: x["datum"], reverse=True)
        for r in toeslag_sorted[:3]:
            print(f"  * {r['datum']} | {r['af_bij']} EUR {r['bedrag']:.2f} | {r['naam']} | {r['mededelingen'][:60]}")

    # 6. Beancount Export
    if export_beancount:
        if custom_out:
            beancount_file = custom_out
        else:
            default_dir = os.path.join(os.path.dirname(__file__), "..", "Ketengrootboek")
            os.makedirs(default_dir, exist_ok=True)
            stem = os.path.splitext(os.path.basename(file_path))[0]
            beancount_file = os.path.join(default_dir, f"audit_{stem}.beancount")

        export_transactions_to_beancount_file(
            transactions=transactions,
            output_path=beancount_file,
            own_iban=own_iban,
            title=f"CivicHelper Audit — {os.path.basename(file_path)}",
            opening_balance=op_balance,
            closing_balance=cl_balance
        )
        print("\n" + "=" * 78)
        print(f"[*] BEANCOUNT LEDGER GEGENEREERD: {beancount_file}")
        print(f"    - Alle {total_tx} transacties sluitend geboekt (Debet == Credit).")
        print(f"    - Openen met Beancount / Fava: 'fava {beancount_file}'")
        print("=" * 78)

    print("\nAUDIT VOLTOOID. Ketenposten en bewijsstukken zijn gekoppeld.")
    print("=" * 78)

def main():
    args = sys.argv[1:]
    target_file = None
    custom_beancount = None

    i = 0
    while i < len(args):
        arg = args[i]
        if arg in ("--out", "-o") and i + 1 < len(args):
            custom_beancount = args[i + 1]
            i += 2
        elif not arg.startswith("--"):
            target_file = arg
            i += 1
        else:
            i += 1

    if not target_file:
        # Zoek in Incoming_Letters naar .csv of .xml
        incoming_dir = os.path.join(os.path.dirname(__file__), "..", "Incoming_Letters")
        if os.path.exists(incoming_dir):
            candidates = [
                os.path.join(incoming_dir, f) for f in os.listdir(incoming_dir)
                if f.lower().endswith(".csv") or f.lower().endswith(".xml")
            ]
            if candidates:
                target_file = candidates[0]

    if target_file:
        analyze_bank_file(target_file, export_beancount=True, custom_out=custom_beancount)
    else:
        print("Gebruik:")
        print("  python bank_audit.py <pad_naar_bestand.csv_of_camt.xml> [--out output.beancount]")
        print("Of plaats een bank .csv of .xml bestand in de map 'Incoming_Letters'.")

if __name__ == "__main__":
    main()
