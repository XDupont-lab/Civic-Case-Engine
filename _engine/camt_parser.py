#!/usr/bin/env python3
"""
CIVIC HELPER — CAMT.053 / CAMT.052 XML BANK STATEMENT PARSER
100% Python Standard Library (xml.etree.ElementTree). Zero external dependencies.

Ondersteunt:
- ISO 20022 camt.053.001.02 / camt.053.001.04 / camt.053.001.08 (Dagafschriften)
- ISO 20022 camt.052.001.02 / camt.052.001.04 / camt.052.001.08 (Tussentijdse rapporten)
- Automatische namespace-resolutie (onafhankelijk van exacte XSD-versie)
- Extractie van rekeningen, openings-/sluitingssaldo, tegenpartij IBAN, mandaat-ID's en gestructureerde omschrijvingen
"""

import sys
import os
import re
from decimal import Decimal
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Any

def _local_tag(tag: str) -> str:
    """Verwijdert XML namespace prefix (bijv. '{urn:iso:...}Stmt' -> 'Stmt')."""
    return tag.split("}", 1)[1] if "}" in tag else tag

def _find_elem(parent: ET.Element, target_tag: str) -> Optional[ET.Element]:
    """Vindt eerste directe of indirecte kind-element op basis van de lokale tag."""
    for elem in parent.iter():
        if _local_tag(elem.tag) == target_tag:
            return elem
    return None

def _find_all_elems(parent: ET.Element, target_tag: str) -> List[ET.Element]:
    """Vindt alle elementen met een bepaalde lokale tag onder parent."""
    return [e for e in parent.iter() if _local_tag(e.tag) == target_tag]

def _elem_text(parent: Optional[ET.Element], target_tag: str, default: str = "") -> str:
    """Haalt tekst op van eerste kind met tag target_tag."""
    if parent is None:
        return default
    elem = _find_elem(parent, target_tag)
    if elem is not None and elem.text:
        return elem.text.strip()
    return default

def is_camt_xml(file_path: str) -> bool:
    """Controleert of een bestand een CAMT XML bankbestand is."""
    if not os.path.exists(file_path) or not file_path.lower().endswith(".xml"):
        return False
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            header = f.read(2048)
            return "camt.053" in header or "camt.052" in header or "BkToCstmrStmt" in header or "BkToCstmrAcctRpt" in header
    except Exception:
        return False

def parse_camt(file_path: str) -> Dict[str, Any]:
    """
    Parseert een ISO 20022 CAMT.053 of CAMT.052 XML bestand.
    
    Retourneert een dict met:
      - 'iban': Eigen IBAN rekeningnummer
      - 'statement_id': ID van het afschrift
      - 'datum': Datum van afschrift (YYYY-MM-DD)
      - 'opening_balance': {'amount': Decimal, 'currency': str, 'date': str, 'status': str}
      - 'closing_balance': {'amount': Decimal, 'currency': str, 'date': str, 'status': str}
      - 'transactions': List van gestandaardiseerde transacties
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"CAMT-bestand niet gevonden: {file_path}")

    tree = ET.parse(file_path)
    root = tree.getroot()

    # Zoek Stmt (camt.053) of Rpt (camt.052)
    statements = _find_all_elems(root, "Stmt")
    if not statements:
        statements = _find_all_elems(root, "Rpt")
    if not statements:
        # Misschien is root zelf het Stmt element
        if _local_tag(root.tag) in ("Stmt", "Rpt"):
            statements = [root]

    all_tx: List[Dict[str, Any]] = []
    own_iban = ""
    statement_id = ""
    stmt_date = ""
    op_balance = None
    cl_balance = None

    for stmt in statements:
        if not statement_id:
            statement_id = _elem_text(stmt, "Id")
        if not own_iban:
            # Stmt/Acct/Id/IBAN
            acct_elem = _find_elem(stmt, "Acct")
            if acct_elem is not None:
                own_iban = _elem_text(acct_elem, "IBAN")

        # Saldobalansen (OPBD = Opening, CLBD = Closing)
        bal_elems = _find_all_elems(stmt, "Bal")
        for b in bal_elems:
            tp_code = _elem_text(b, "Cd")
            amt_elem = _find_elem(b, "Amt")
            amt_val = Decimal(amt_elem.text.strip()) if (amt_elem is not None and amt_elem.text) else Decimal("0.00")
            ccy = amt_elem.get("Ccy", "EUR") if amt_elem is not None else "EUR"
            cdt_dbt = _elem_text(b, "CdtDbtInd")
            b_date = _elem_text(b, "Dt")
            if not b_date:
                dt_elem = _find_elem(b, "Dt")
                b_date = _elem_text(dt_elem, "Dt") if dt_elem is not None else ""

            bal_dict = {
                "amount": amt_val if cdt_dbt != "DBIT" else -amt_val,
                "currency": ccy,
                "date": b_date,
                "type": tp_code
            }
            if tp_code in ("OPBD", "PRCD"):
                op_balance = bal_dict
            elif tp_code in ("CLBD", "ITBD"):
                cl_balance = bal_dict

        # Transacties (Ntry)
        entries = _find_all_elems(stmt, "Ntry")
        for ntry in entries:
            # Boekingsdatum
            bookg_dt_elem = _find_elem(ntry, "BookgDt")
            datum = ""
            if bookg_dt_elem is not None:
                datum = _elem_text(bookg_dt_elem, "Dt")
                if not datum:
                    datum = _elem_text(bookg_dt_elem, "DtTm")[:10]
            if not datum:
                # Fallback ValDt
                val_dt_elem = _find_elem(ntry, "ValDt")
                if val_dt_elem is not None:
                    datum = _elem_text(val_dt_elem, "Dt")

            # Bedrag en Credit/Debit
            amt_elem = _find_elem(ntry, "Amt")
            amt_str = amt_elem.text.strip() if (amt_elem is not None and amt_elem.text) else "0.00"
            bedrag = Decimal(amt_str)
            ccy = amt_elem.get("Ccy", "EUR") if amt_elem is not None else "EUR"

            cdt_dbt = _elem_text(ntry, "CdtDbtInd", "CRDT")
            af_bij = "Bij" if cdt_dbt == "CRDT" else "Af"

            # Details
            tx_dtls = _find_all_elems(ntry, "TxDtls")
            if not tx_dtls:
                # Als er geen onderliggende TxDtls zijn, parse de Ntry direct
                tx_dtls = [ntry]

            for tx in tx_dtls:
                # Tegenpartij naam en IBAN
                naam = ""
                tegenrekening = ""
                end_to_end_id = ""
                mandate_id = ""

                # Afschrijving (DBIT) -> Tegenpartij is Creditor (Cdtr)
                # Bijschrijving (CRDT) -> Tegenpartij is Debtor (Dbtr)
                rltd_parties = _find_elem(tx, "RltdPties")
                if rltd_parties is not None:
                    if af_bij == "Af":
                        naam = _elem_text(_find_elem(rltd_parties, "Cdtr"), "Nm")
                        if not naam:
                            naam = _elem_text(_find_elem(rltd_parties, "UltmtCdtr"), "Nm")
                        cdtr_acct = _find_elem(tx, "CdtrAcct")
                        if cdtr_acct is not None:
                            tegenrekening = _elem_text(cdtr_acct, "IBAN")
                    else:
                        naam = _elem_text(_find_elem(rltd_parties, "Dbtr"), "Nm")
                        if not naam:
                            naam = _elem_text(_find_elem(rltd_parties, "UltmtDbtr"), "Nm")
                        dbtr_acct = _find_elem(tx, "DbtrAcct")
                        if dbtr_acct is not None:
                            tegenrekening = _elem_text(dbtr_acct, "IBAN")

                # Fallback als naam leeg is
                if not naam:
                    naam = _elem_text(tx, "Nm")
                if not tegenrekening:
                    tegenrekening = _elem_text(tx, "IBAN")

                # Referenties
                refs = _find_elem(tx, "Refs")
                if refs is not None:
                    end_to_end_id = _elem_text(refs, "EndToEndId")
                    if end_to_end_id in ("NOTPROVIDED", "NONE"):
                        end_to_end_id = ""
                    mandate_id = _elem_text(refs, "MndtId")

                # Omschrijving / Mededelingen
                rmt_inf = _find_elem(tx, "RmtInf")
                mededelingen_parts = []
                if rmt_inf is not None:
                    # Ongestructureerd
                    for u in _find_all_elems(rmt_inf, "Ustrd"):
                        if u.text and u.text.strip():
                            mededelingen_parts.append(u.text.strip())
                    # Gestructureerd
                    strd = _find_elem(rmt_inf, "Strd")
                    if strd is not None:
                        ref = _elem_text(strd, "Ref")
                        if ref:
                            mededelingen_parts.append(f"Ref: {ref}")

                mededelingen = " | ".join(mededelingen_parts)

                # Als tx een specifiek bedrag heeft
                sub_amt_elem = _find_elem(tx, "Amt")
                sub_bedrag = Decimal(sub_amt_elem.text.strip()) if (sub_amt_elem is not None and sub_amt_elem.text) else bedrag

                all_tx.append({
                    "datum": datum,
                    "bedrag": sub_bedrag,
                    "af_bij": af_bij,
                    "naam": naam,
                    "tegenrekening": tegenrekening,
                    "mededelingen": mededelingen,
                    "end_to_end_id": end_to_end_id,
                    "mandate_id": mandate_id,
                    "currency": ccy,
                    "bron": "CAMT.053"
                })

    return {
        "iban": own_iban,
        "statement_id": statement_id,
        "datum": stmt_date,
        "opening_balance": op_balance,
        "closing_balance": cl_balance,
        "transactions": all_tx
    }
