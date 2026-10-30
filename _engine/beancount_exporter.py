#!/usr/bin/env python3
"""
CIVIC HELPER — BEANCOUNT LEDGER GENERATOR & KETENGROOTBOEK EXPORTER
100% Python Standard Library. Zero external dependencies.

Vertaalt banktransacties (CSV / CAMT.053) en Ketengrootboek-posten naar
volledig sluitende dubbel-boekhouden Beancount ledgers (.beancount).
Compatibel met Beancount v2/v3 en Fava web interface.

Kern-invariant:
  Sum(Postings) == 0.00 EUR per transactie (Debet == Credit).
"""

from __future__ import annotations

import os
import re
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

# Institutionele matchers voor rekeningschema
CATEGORIE_PATRONEN: List[Tuple[str, str, str, re.Pattern]] = [
    # (Categorie, Account, Default Sign Type, Regex)
    ("Uitkering_Participatiewet", "Income:Uitkering:Participatiewet", "income",
     re.compile(r"participatiewet|bijstand|levensonderhoud|gemeente.*(uitk|sociaal|inkomen|werk)", re.I)),
    ("Uitkering_UWV", "Income:Uitkering:UWV", "income",
     re.compile(r"\buwv\b|uitvoeringsinstituut werknemersverzekeringen|ziektewet|wia|wao|ww-uitkering", re.I)),
    ("Uitkering_SVB", "Income:Uitkering:SVB", "income",
     re.compile(r"\bsvb\b|sociale verzekeringsbank|aow|anw|kinderbijslag", re.I)),
    ("Toeslagen_Zorg", "Income:Toeslagen:Zorgtoeslag", "income",
     re.compile(r"zorgtoeslag", re.I)),
    ("Toeslagen_Huur", "Income:Toeslagen:Huurtoeslag", "income",
     re.compile(r"huurtoeslag", re.I)),
    ("Toeslagen_Kind", "Income:Toeslagen:KindgebondenBudget", "income",
     re.compile(r"kindgebonden|kinderopvangtoeslag", re.I)),
    ("Toeslagen_Generiek", "Income:Toeslagen:Algemeen", "income",
     re.compile(r"toeslagen|belastingdienst/toeslagen", re.I)),
    ("Huur", "Expenses:Wonen:Huur", "expense",
     re.compile(r"huur|woningstichting|woningbouw|woonstichting|corporatie|lefier|nijestee|patrimonium|de huismeesters|wolderwijd", re.I)),
    ("Energie", "Expenses:Wonen:Energie", "expense",
     re.compile(r"energie|gas|stroom|eneco|essent|vattenfall|budget energie|greenchoice|innogy|oxxio", re.I)),
    ("Water", "Expenses:Wonen:Water", "expense",
     re.compile(r"waterbedrijf|waterbedrijf groningen|evides|dunea|vitens|brabant water|wml", re.I)),
    ("CAK_Zorg", "Expenses:Zorg:CAK", "expense",
     re.compile(r"\bcak\b|centraal administratie kantoor|wanbetalersregeling|zorginstituut", re.I)),
    ("Zorgverzekering", "Expenses:Zorg:Premie", "expense",
     re.compile(r"menzis|zilveren kruis|cz\b|vgz|onvz|dsr|zekur|ditzo|salland|de friesland|univé|unive", re.I)),
    ("Eigen_Risico", "Expenses:Zorg:EigenRisico", "expense",
     re.compile(r"eigen risico|eigen bijdrage zorg", re.I)),
    ("Incasso_Flanderijn", "Liabilities:Incasso:Flanderijn", "liability",
     re.compile(r"flanderijn", re.I)),
    ("Incasso_Syncasso", "Liabilities:Incasso:Syncasso", "liability",
     re.compile(r"syncasso", re.I)),
    ("Incasso_Cannock", "Liabilities:Incasso:Cannock", "liability",
     re.compile(r"cannock|chase", re.I)),
    ("Incasso_GGN", "Liabilities:Incasso:GGN", "liability",
     re.compile(r"\bggn\b", re.I)),
    ("Incasso_Deurwaarder", "Liabilities:Incasso:Deurwaarder", "liability",
     re.compile(r"deurwaarder|gerechtsdeurwaarder|intrum|coeo|modero|trivion|bazuin|jongerius|van arkel", re.I)),
    ("Belastingen_Lokaal", "Expenses:Belasting:GemeenteEnWaterschap", "expense",
     re.compile(r"noordelijk belastingkantoor|gblt|tribuut|bghu|bsgr|dowr|cocensus|waterschap|gemeentebelastingen", re.I)),
    ("Belastingdienst", "Liabilities:Belastingdienst", "liability",
     re.compile(r"belastingdienst", re.I)),
    ("Boodschappen", "Expenses:Levensonderhoud:Voeding", "expense",
     re.compile(r"albert heijn|ah to go|jumbo|lidl|aldi|plus supermarkt|coop\b|spar\b|dirk van den broek|dirk\b|ekoplaza", re.I)),
    ("Vervoer", "Expenses:Levensonderhoud:Vervoer", "expense",
     re.compile(r"ns-reizigers|ns groep|qbuzz|arriva|ov-chipkaart|connexxion|shell|bp station|totalenergies|tango|aviam", re.I)),
    ("Bankkosten", "Expenses:Financieel:Bankkosten", "expense",
     re.compile(r"kosten betaalpakket|kosten orv|bankkosten|vervaldatum kosten|vaste kosten betaal|provisie", re.I)),
]

# Bekende koppelingen met Ketengrootboek posten
KETEN_MATCHERS = [
    {
        "post_id": "POST-WONEN-WMO-001",
        "anker_feit": "EVT-CORP-20260715",
        "pattern": re.compile(r"woningstichting|woningcorporatie", re.I),
        "tag": "#keten_wonen"
    },
    {
        "post_id": "POST-CAK-SOZAWE-002",
        "anker_feit": "EVT-CAK-20260101",
        "pattern": re.compile(r"\bcak\b|wanbetalersregeling", re.I),
        "tag": "#bronheffing_cak"
    },
    {
        "post_id": "POST-TOESLAGEN-DACAS-003",
        "anker_feit": "EVT-TOESLAGEN-VEKTIS-20261020",
        "pattern": re.compile(r"toeslagen.*verrekening|dacas", re.I),
        "tag": "#dacas_verrekening"
    }
]

DEFAULT_ACCOUNTS = [
    "Assets:Bank:NL:Betaalrekening",
    "Income:Uitkering:Participatiewet",
    "Income:Uitkering:UWV",
    "Income:Uitkering:SVB",
    "Income:Toeslagen:Zorgtoeslag",
    "Income:Toeslagen:Huurtoeslag",
    "Income:Toeslagen:KindgebondenBudget",
    "Income:Toeslagen:Algemeen",
    "Income:Overig",
    "Expenses:Wonen:Huur",
    "Expenses:Wonen:Energie",
    "Expenses:Wonen:Water",
    "Expenses:Zorg:CAK",
    "Expenses:Zorg:Premie",
    "Expenses:Zorg:EigenRisico",
    "Liabilities:Incasso:Flanderijn",
    "Liabilities:Incasso:Syncasso",
    "Liabilities:Incasso:Cannock",
    "Liabilities:Incasso:GGN",
    "Liabilities:Incasso:Deurwaarder",
    "Liabilities:Belastingdienst",
    "Expenses:Belasting:GemeenteEnWaterschap",
    "Expenses:Levensonderhoud:Voeding",
    "Expenses:Levensonderhoud:Vervoer",
    "Expenses:Financieel:Bankkosten",
    "Expenses:Diversen:Onbekend",
    "Equity:Openingsbalans"
]

def format_date_iso(date_str: str) -> str:
    """Zet uiteenlopende datumformaten (YYYYMMDD, DD-MM-YYYY, YYYY-MM-DD) om naar YYYY-MM-DD."""
    d_clean = date_str.strip()
    if not d_clean:
        return datetime.now().strftime("%Y-%m-%d")
    
    # YYYY-MM-DD
    if re.match(r"^\d{4}-\d{2}-\d{2}$", d_clean):
        return d_clean
    # YYYYMMDD
    if re.match(r"^\d{8}$", d_clean):
        return f"{d_clean[:4]}-{d_clean[4:6]}-{d_clean[6:8]}"
    # DD-MM-YYYY or DD/MM/YYYY
    m = re.match(r"^(\d{1,2})[-/](\d{1,2})[-/](\d{4})$", d_clean)
    if m:
        day, month, year = m.groups()
        return f"{year}-{int(month):02d}-{int(day):02d}"
    return d_clean

def format_amount(amount_any: Any) -> Decimal:
    """Converteert getal of string naar schone Decimal met 2 decimalen."""
    if isinstance(amount_any, Decimal):
        return abs(amount_any)
    if isinstance(amount_any, (int, float)):
        return abs(Decimal(str(amount_any)))
    s = str(amount_any).replace("EUR", "").replace("€", "").strip()
    s = s.replace(".", "").replace(",", ".") if ("," in s and "." in s and s.find(".") < s.find(",")) else s.replace(",", ".")
    s = s.replace("+", "").replace("-", "").strip()
    try:
        return abs(Decimal(s))
    except Exception:
        return Decimal("0.00")

def classify_transaction(naam: str, mededelingen: str, tegenrekening: str, af_bij: str) -> Tuple[str, str, Optional[Dict[str, str]]]:
    """
    Bepaalt de categorie, Beancount tegenrekening en eventuele Ketengrootboek metadata.
    """
    full_text = f"{naam} {mededelingen} {tegenrekening}".strip()
    
    # 1. Ketengrootboek match
    keten_info = None
    for km in KETEN_MATCHERS:
        if km["pattern"].search(full_text):
            keten_info = {
                "post_id": km["post_id"],
                "anker_feit": km["anker_feit"],
                "tag": km["tag"]
            }
            break

    # 2. Rekening categorisering
    for cat_name, account, kind, pattern in CATEGORIE_PATRONEN:
        if pattern.search(full_text):
            return cat_name, account, keten_info

    # 3. Fallbacks
    if af_bij == "Bij":
        return "Overige_Inkomsten", "Income:Overig", keten_info
    else:
        return "Onbekende_Uitgaven", "Expenses:Diversen:Onbekend", keten_info

def generate_beancount_ledger(
    transactions: List[Dict[str, Any]],
    own_iban: str = "",
    title: str = "CivicHelper Ketengrootboek Bank Audit",
    opening_balance: Optional[Dict[str, Any]] = None,
    closing_balance: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Genereert een complete, 100% sluitende Beancount ledger tekst.
    """
    lines: List[str] = []
    lines.append(f"; {'=' * 76}")
    lines.append(f"; CIVIC HELPER — FORENSISCH KETENGROOTBOEK LEDGER")
    lines.append(f"; Gegenereerd op: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"; Epistemische Pariteit: Dubbel Boekhouden aan de Burgerkant")
    lines.append(f"; {'=' * 76}\n")

    lines.append(f'option "title" "{title}"')
    lines.append('option "operating_currency" "EUR"\n')

    # Bepaal eerste transactiedatum voor open-directives
    earliest_date = "2020-01-01"
    clean_txs = []
    for tx in transactions:
        iso_date = format_date_iso(str(tx.get("datum", "")))
        amt = format_amount(tx.get("bedrag", 0))
        af_bij = tx.get("af_bij", "Af")
        clean_txs.append({
            **tx,
            "iso_date": iso_date,
            "clean_amt": amt,
            "af_bij": af_bij
        })
        if iso_date and iso_date < earliest_date:
            earliest_date = f"{iso_date[:4]}-01-01"

    # Account Openings
    lines.append("; --- REKENINGSCHEMA (OPEN DECLARATIONS) ---")
    asset_account = f"Assets:Bank:NL:{own_iban.replace(' ', '')}" if own_iban else "Assets:Bank:NL:Betaalrekening"
    lines.append(f"{earliest_date} open {asset_account} EUR")
    for acc in DEFAULT_ACCOUNTS:
        if acc != "Assets:Bank:NL:Betaalrekening":
            lines.append(f"{earliest_date} open {acc} EUR")
    lines.append("")

    # Opening balance posting indien aanwezig
    if opening_balance and opening_balance.get("amount") is not None:
        op_date = format_date_iso(str(opening_balance.get("date", earliest_date)))
        op_amt = Decimal(str(opening_balance["amount"]))
        lines.append("; --- OPENINGSBALANS SALDO ---")
        lines.append(f'{op_date} * "Bank" "Beginstand bankafschrift"')
        lines.append(f"  {asset_account:45} {op_amt:10.2f} EUR")
        lines.append(f"  {'Equity:Openingsbalans':45} {-op_amt:10.2f} EUR\n")

    # Sorteer transacties chronologisch
    clean_txs.sort(key=lambda x: (x["iso_date"], x.get("naam", "")))

    lines.append("; --- TRANSACTIES & POSTEN ---")
    for tx in clean_txs:
        date_str = tx["iso_date"]
        amt = tx["clean_amt"]
        af_bij = tx["af_bij"]
        naam = (tx.get("naam") or "Onbekende Tegenpartij").replace('"', "'").strip()
        mededelingen = (tx.get("mededelingen") or "").replace('"', "'").strip()
        tegenrekening = (tx.get("tegenrekening") or "").strip()
        end_to_end = (tx.get("end_to_end_id") or "").strip()
        mandate_id = (tx.get("mandate_id") or "").strip()

        cat, counter_account, keten_info = classify_transaction(naam, mededelingen, tegenrekening, af_bij)

        # Transactiekop
        tag_str = f" {keten_info['tag']}" if keten_info else ""
        lines.append(f'{date_str} * "{naam}" "{mededelingen[:80]}"{tag_str}')

        # Metadata
        lines.append(f'  instantie: "{cat}"')
        if tegenrekening:
            lines.append(f'  tegenrekening: "{tegenrekening}"')
        if end_to_end:
            lines.append(f'  end_to_end_id: "{end_to_end}"')
        if mandate_id:
            lines.append(f'  mandate_id: "{mandate_id}"')
        if keten_info:
            lines.append(f'  keten_post: "{keten_info["post_id"]}"')
            lines.append(f'  keten_anker: "{keten_info["anker_feit"]}"')

        # Dubbel-boekhouden postings (Debet == Credit Invariant)
        if af_bij == "Af":
            # Uitgaande kasstroom: Bank vermindert (-), Tegenrekening (Expense/Liability) vermeerdert (+)
            lines.append(f"  {asset_account:45} -{amt:.2f} EUR")
            lines.append(f"  {counter_account:45}  {amt:.2f} EUR")
        else:
            # Inkomende kasstroom: Bank vermeerdert (+), Tegenrekening (Income/Reimbursement) vermindert (-)
            lines.append(f"  {asset_account:45}  {amt:.2f} EUR")
            lines.append(f"  {counter_account:45} -{amt:.2f} EUR")
        lines.append("")

    # Closing balance check directive
    if closing_balance and closing_balance.get("amount") is not None:
        cl_date = format_date_iso(str(closing_balance.get("date", datetime.now().strftime("%Y-%m-%d"))))
        cl_amt = Decimal(str(closing_balance["amount"]))
        lines.append("; --- EINDBALANS CONTROLE (BALANCE ASSERTION) ---")
        lines.append(f"{cl_date} balance {asset_account} {cl_amt:.2f} EUR\n")

    return "\n".join(lines)

def export_transactions_to_beancount_file(
    transactions: List[Dict[str, Any]],
    output_path: str,
    own_iban: str = "",
    title: str = "CivicHelper Ketengrootboek Bank Audit",
    opening_balance: Optional[Dict[str, Any]] = None,
    closing_balance: Optional[Dict[str, Any]] = None,
) -> str:
    """Schrijft de gegenereerde Beancount data naar een bestand."""
    content = generate_beancount_ledger(
        transactions=transactions,
        own_iban=own_iban,
        title=title,
        opening_balance=opening_balance,
        closing_balance=closing_balance
    )
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
    return output_path

def export_ketengrootboek_to_beancount(
    keten_dir: Optional[str] = None,
    output_path: Optional[str] = None
) -> str:
    """
    Exporteert het institutionele Ketengrootboek (grootboek.json + journaal.json)
    naar een sluitend Beancount-ledgerbestand.
    """
    import json
    if not keten_dir:
        keten_dir = os.path.join(os.path.dirname(__file__), "..", "Ketengrootboek")
    if not output_path:
        output_path = os.path.join(keten_dir, "ketengrootboek_audit.beancount")

    grootboek_path = os.path.join(keten_dir, "boek2_journaal.json")
    if not os.path.exists(grootboek_path):
        grootboek_path = os.path.join(keten_dir, "grootboek.json")

    journaal_path = os.path.join(keten_dir, "memoriaal.json")
    if not os.path.exists(journaal_path):
        journaal_path = os.path.join(keten_dir, "journaal.json")

    posts = []
    if os.path.exists(grootboek_path):
        with open(grootboek_path, "r", encoding="utf-8") as f:
            posts = json.load(f)

    feiten = {}
    if os.path.exists(journaal_path):
        with open(journaal_path, "r", encoding="utf-8") as f:
            for feit in json.load(f):
                feiten[feit.get("id")] = feit

    # Haal indien beschikbaar ook de 3-Boeken Ketenintegriteitsbeoordeling op uit SluitingsToetser
    toets_per_post = {}
    try:
        import sys
        if keten_dir not in sys.path:
            sys.path.insert(0, keten_dir)
        from sluiting import SluitingsToetser
        toetser = SluitingsToetser(root_dir=keten_dir)
        for r in toetser.ketenstatus_overzicht().get("resultaten", []):
            toets_per_post[r["post_id"]] = r
    except Exception:
        pass

    lines = []
    lines.append("; " + "=" * 76)
    lines.append("; CIVIC HELPER — INSTITUTIONEEL KETENGROOTBOEK LEDGER (SIMON STEVIN 3 BOEKEN)")
    lines.append(f"; Gegenereerd op: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("; Beancount vlag: '*' = Materieel Vereffend | '!' = Schijnsluiting / Conflict")
    lines.append("; " + "=" * 76 + "\n")
    lines.append('option "title" "CivicHelper Ketengrootboek Overdrachten"')
    lines.append('option "operating_currency" "EUR"\n')

    # Accounts inventariseren
    accounts = set()
    accounts.add("Equity:Ketenvereffening")
    for post in posts:
        deb = "Assets:Keten:" + re.sub(r"[^A-Za-z0-9]", "", post.get("debet_rekening", "Burger"))
        crd = "Liabilities:Keten:" + re.sub(r"[^A-Za-z0-9]", "", post.get("credit_rekening", "Loket"))
        accounts.add(deb)
        accounts.add(crd)

    lines.append("; --- REKENINGSCHEMA (OPEN DECLARATIONS) ---")
    for acc in sorted(accounts):
        lines.append(f"2020-01-01 open {acc} EUR")
    lines.append("")

    lines.append("; --- OVERDRACHTEN EN OVERHEIDSVORDERINGEN ---")
    for post in posts:
        pid = post.get("post_id", "POST-ONBEKEND")
        pnaam = post.get("naam", "Ketenoverdracht").replace('"', "'")
        deb = "Assets:Keten:" + re.sub(r"[^A-Za-z0-9]", "", post.get("debet_rekening", "Burger"))
        crd = "Liabilities:Keten:" + re.sub(r"[^A-Za-z0-9]", "", post.get("credit_rekening", "Loket"))
        anker_id = post.get("anker_feit", "")
        tegen_id = post.get("tegen_feit", "")

        datum = "2026-01-01"
        bewijsstuk = ""
        if anker_id in feiten:
            datum = feiten[anker_id].get("datum", datum)
            bewijsstuk = feiten[anker_id].get("bewijsstuk", "")

        t_res = toets_per_post.get(pid, {})
        mat_ok = t_res.get("materieel_vereffend", False)
        flag = "*" if mat_ok else "!"
        diag = t_res.get("keten_diagnose", "")
        # Bepaal of de vordering formeel betwist is (Laag 3 interpretatie of ketenbreuk)
        anker_obj = feiten.get(anker_id, {})
        tegen_obj = feiten.get(tegen_id, {})
        is_betwist = any(ip.get("betwist") for ip in anker_obj.get("interpretatie_historie", [])) or \
                     any(ip.get("betwist") for ip in tegen_obj.get("interpretatie_historie", [])) or \
                     ("niet gesloten" in str(diag).lower() or "ketenbreuk" in str(diag).lower())
        vordering_status = "betwist" if is_betwist else "vastgesteld"

        tags = []
        if diag:
            tags.append(f"#{diag.lower().replace(' ', '_').replace('/', '_')}")
        if is_betwist:
            tags.append("#betwist")
        tag_diag = f" {' '.join(tags)}" if tags else ""

        lines.append(f'{datum} {flag} "{post.get("debet_rekening", "")}" "{pnaam}"{tag_diag}')
        lines.append(f'  post_id: "{pid}"')
        lines.append(f'  vordering_status: "{vordering_status}"')
        if anker_id:
            lines.append(f'  anker_feit: "{anker_id}"')
        if tegen_id:
            lines.append(f'  tegen_feit: "{tegen_id}"')
        if bewijsstuk:
            lines.append(f'  bewijsstuk: "{bewijsstuk}"')
        if t_res:
            lines.append(f'  rekenkundig_sluitend: "{"Ja" if t_res.get("rekenkundig_sluitend") else "Nee"}"')
            lines.append(f'  procedureel_gesloten: "{"Ja" if t_res.get("procedureel_gesloten") else "Nee"}"')
            lines.append(f'  materieel_vereffend: "{"Ja" if mat_ok else "Nee"}"')
            lines.append(f'  keten_diagnose: "{diag}"')
            lines.append(f'  werklexicon_code: "{t_res.get("werklexicon_code", "")}"')

        # 1 eenheid ketenverplichting (EUR 1.00 nomineel of sluitend)
        lines.append(f"  {deb:45}  1.00 EUR")
        lines.append(f"  {crd:45} -1.00 EUR\n")

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return output_path
