#!/usr/bin/env python3
"""
CIVIC HELPER — TEST SUITE: BANK AUDIT & BEANCOUNT EXPORTER
100% Python Standard Library unittest. Zero external dependencies.
"""

import unittest
import os
import tempfile
from decimal import Decimal

from camt_parser import is_camt_xml, parse_camt
from beancount_exporter import (
    format_date_iso,
    format_amount,
    classify_transaction,
    generate_beancount_ledger,
    export_transactions_to_beancount_file
)
from bank_audit import parse_csv, analyze_bank_file

# Synthetisch CAMT.053 XML bestand voor testdoeleinden
SAMPLE_CAMT_XML = """<?xml version="1.0" encoding="UTF-8"?>
<Document xmlns="urn:iso:std:iso:20022:tech:xsd:camt.053.001.02">
  <BkToCstmrStmt>
    <Stmt>
      <Id>STMT-2026-10-001</Id>
      <CreDtTm>2026-10-26T12:00:00Z</CreDtTm>
      <Acct>
        <Id>
          <IBAN>NL91ABNA0417164300</IBAN>
        </Id>
      </Acct>
      <Bal>
        <Tp><CdOrPrtry><Cd>OPBD</Cd></CdOrPrtry></Tp>
        <Amt Ccy="EUR">1500.00</Amt>
        <CdtDbtInd>CRDT</CdtDbtInd>
        <Dt><Dt>2026-10-01</Dt></Dt>
      </Bal>
      <Bal>
        <Tp><CdOrPrtry><Cd>CLBD</Cd></CdOrPrtry></Tp>
        <Amt Ccy="EUR">2040.00</Amt>
        <CdtDbtInd>CRDT</CdtDbtInd>
        <Dt><Dt>2026-10-26</Dt></Dt>
      </Bal>
      <Ntry>
        <Amt Ccy="EUR">1200.00</Amt>
        <CdtDbtInd>CRDT</CdtDbtInd>
        <Sts>BOOK</Sts>
        <BookgDt><Dt>2026-10-20</Dt></BookgDt>
        <NtryDtls>
          <TxDtls>
            <Refs><EndToEndId>E2E-SOZ-202610</EndToEndId></Refs>
            <RltdPties>
              <Dbtr><Nm>Gemeente Voorbeeldstad</Nm></Dbtr>
              <DbtrAcct><Id><IBAN>NL22BNGH0285000000</IBAN></Id></DbtrAcct>
            </RltdPties>
            <RmtInf><Ustrd>Bijstand levensonderhoud norm Participatiewet 2026-10</Ustrd></RmtInf>
          </TxDtls>
        </NtryDtls>
      </Ntry>
      <Ntry>
        <Amt Ccy="EUR">580.00</Amt>
        <CdtDbtInd>DBIT</CdtDbtInd>
        <Sts>BOOK</Sts>
        <BookgDt><Dt>2026-10-21</Dt></BookgDt>
        <NtryDtls>
          <TxDtls>
            <Refs><EndToEndId>E2E-HUUR-202610</EndToEndId><MndtId>MND-GH-789</MndtId></Refs>
            <RltdPties>
              <Cdtr><Nm>Woningstichting Voorbeeldstad</Nm></Cdtr>
              <CdtrAcct><Id><IBAN>NL05RABO0123456789</IBAN></Id></CdtrAcct>
            </RltdPties>
            <RmtInf><Ustrd>Huur Voorbeeldstraat 9 Voorbeeldstad periode 2026-10</Ustrd></RmtInf>
          </TxDtls>
        </NtryDtls>
      </Ntry>
      <Ntry>
        <Amt Ccy="EUR">40.00</Amt>
        <CdtDbtInd>DBIT</CdtDbtInd>
        <Sts>BOOK</Sts>
        <BookgDt><Dt>2026-10-22</Dt></BookgDt>
        <NtryDtls>
          <TxDtls>
            <RltdPties>
              <Cdtr><Nm>Flanderijn en Van Eck Gerechtsdeurwaarders</Nm></Cdtr>
              <CdtrAcct><Id><IBAN>NL88INGB0001112233</IBAN></Id></CdtrAcct>
            </RltdPties>
            <RmtInf><Ustrd>Dossier: FL-2026-8819 Betaling aflossing</Ustrd></RmtInf>
          </TxDtls>
        </NtryDtls>
      </Ntry>
      <Ntry>
        <Amt Ccy="EUR">40.00</Amt>
        <CdtDbtInd>DBIT</CdtDbtInd>
        <Sts>BOOK</Sts>
        <BookgDt><Dt>2026-10-23</Dt></BookgDt>
        <NtryDtls>
          <TxDtls>
            <RltdPties>
              <Cdtr><Nm>Albert Heijn 1422</Nm></Cdtr>
            </RltdPties>
            <RmtInf><Ustrd>Betaalautomaat 14:32 Voorbeeldstad</Ustrd></RmtInf>
          </TxDtls>
        </NtryDtls>
      </Ntry>
    </Stmt>
  </BkToCstmrStmt>
</Document>
"""

SAMPLE_ING_CSV = """Datum;Naam / Omschrijving;Rekening;Tegenrekening;Code;Af Bij;Bedrag (EUR);Mutatiesoort;Mededelingen
20261020;Gemeente Voorbeeldstad;NL91INGB0001234567;NL22BNGH0285000000;GT;Bij;1250,50;Verzamelbetaling;Uitkering Participatiewet 2026-10
20261021;Woningstichting Voorbeeldstad;NL91INGB0001234567;NL05RABO0123456789;IC;Af;580,00;Incasso;Huur Voorbeeldstraat 9 Voorbeeldstad
20261022;Centraal Administratie Kantoor;NL91INGB0001234567;NL99INGB0999888777;IC;Af;160,00;Incasso;CAK Wanbetalersregeling Zvw dossier 441029
"""

SAMPLE_RABO_CSV = """"IBAN/BBAN","Munt","BIC","Volgnr","Datum","Rentedatum","Bedrag","Saldo na trn","Naam tegenpartij","Tegenrekening IBAN/BBAN","Naam uiteindelijke partij","Geïnitieerd door","Omschrijving-1","Omschrijving-2","Omschrijving-3"
"NL55RABO0999888777","EUR","RABONL2U","001","2026-10-15","2026-10-15","+123,00","+1123,00","Belastingdienst/Toeslagen","NL01INGB0001111111","","","Zorgtoeslag voorschot 2026","",""
"NL55RABO0999888777","EUR","RABONL2U","002","2026-10-16","2026-10-16","-45,50","+1077,50","Albert Heijn 1200","","","","Betaalpas Voorbeeldstad","",""
"NL55RABO0999888777","EUR","RABONL2U","003","2026-10-17","2026-10-17","-50,00","+1027,50","Syncasso Gerechtsdeurwaarders","NL44INGB0002223334","","","Dossier: SYNC-2026-9912 Termijnbedrag","",""
"""


class TestBankAuditAndBeancount(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_camt_detection_and_parsing(self):
        xml_path = os.path.join(self.temp_dir.name, "test_camt.xml")
        with open(xml_path, "w", encoding="utf-8") as f:
            f.write(SAMPLE_CAMT_XML)

        self.assertTrue(is_camt_xml(xml_path))

        data = parse_camt(xml_path)
        self.assertEqual(data["iban"], "NL91ABNA0417164300")
        self.assertEqual(data["statement_id"], "STMT-2026-10-001")
        self.assertEqual(data["opening_balance"]["amount"], Decimal("1500.00"))
        self.assertEqual(data["closing_balance"]["amount"], Decimal("2040.00"))

        txs = data["transactions"]
        self.assertEqual(len(txs), 4)

        # 1. Uitkering
        tx1 = txs[0]
        self.assertEqual(tx1["af_bij"], "Bij")
        self.assertEqual(tx1["bedrag"], Decimal("1200.00"))
        self.assertEqual(tx1["naam"], "Gemeente Voorbeeldstad")
        self.assertEqual(tx1["tegenrekening"], "NL22BNGH0285000000")
        self.assertEqual(tx1["end_to_end_id"], "E2E-SOZ-202610")

        # 2. Huur
        tx2 = txs[1]
        self.assertEqual(tx2["af_bij"], "Af")
        self.assertEqual(tx2["bedrag"], Decimal("580.00"))
        self.assertEqual(tx2["naam"], "Woningstichting Voorbeeldstad")
        self.assertEqual(tx2["mandate_id"], "MND-GH-789")

    def test_ing_csv_parsing(self):
        csv_path = os.path.join(self.temp_dir.name, "ing_test.csv")
        with open(csv_path, "w", encoding="utf-8") as f:
            f.write(SAMPLE_ING_CSV)

        data = parse_csv(csv_path)
        self.assertEqual(data["iban"], "NL91INGB0001234567")
        txs = data["transactions"]
        self.assertEqual(len(txs), 3)

        self.assertEqual(txs[0]["datum"], "2026-10-20")
        self.assertEqual(txs[0]["bedrag"], Decimal("1250.50"))
        self.assertEqual(txs[0]["af_bij"], "Bij")

        self.assertEqual(txs[1]["datum"], "2026-10-21")
        self.assertEqual(txs[1]["bedrag"], Decimal("580.00"))
        self.assertEqual(txs[1]["af_bij"], "Af")

    def test_rabo_csv_parsing(self):
        csv_path = os.path.join(self.temp_dir.name, "rabo_test.csv")
        with open(csv_path, "w", encoding="utf-8") as f:
            f.write(SAMPLE_RABO_CSV)

        data = parse_csv(csv_path)
        self.assertEqual(data["iban"], "NL55RABO0999888777")
        txs = data["transactions"]
        self.assertEqual(len(txs), 3)

        self.assertEqual(txs[0]["naam"], "Belastingdienst/Toeslagen")
        self.assertEqual(txs[0]["bedrag"], Decimal("123.00"))
        self.assertEqual(txs[0]["af_bij"], "Bij")

        self.assertEqual(txs[2]["naam"], "Syncasso Gerechtsdeurwaarders")
        self.assertEqual(txs[2]["bedrag"], Decimal("50.00"))
        self.assertEqual(txs[2]["af_bij"], "Af")

    def test_beancount_double_entry_balance_invariant(self):
        """
        Toetst de fundamentele Beancount invariant:
        Voor elke transactie moet de som van debet en credit exact gelijk zijn aan 0.00 EUR!
        """
        transactions = [
            {
                "datum": "2026-10-20",
                "bedrag": Decimal("1250.50"),
                "af_bij": "Bij",
                "naam": "Gemeente Voorbeeldstad",
                "tegenrekening": "NL22BNGH0285000000",
                "mededelingen": "Bijstand levensonderhoud"
            },
            {
                "datum": "2026-10-21",
                "bedrag": Decimal("580.00"),
                "af_bij": "Af",
                "naam": "Woningstichting Voorbeeldstad",
                "tegenrekening": "NL05RABO0123456789",
                "mededelingen": "Huur Voorbeeldstraat 9"
            },
            {
                "datum": "2026-10-22",
                "bedrag": Decimal("160.00"),
                "af_bij": "Af",
                "naam": "Centraal Administratie Kantoor",
                "tegenrekening": "NL99INGB0999888777",
                "mededelingen": "CAK Wanbetalersregeling Zvw"
            },
            {
                "datum": "2026-10-23",
                "bedrag": Decimal("45.00"),
                "af_bij": "Af",
                "naam": "Albert Heijn",
                "tegenrekening": "",
                "mededelingen": "Boodschappen"
            }
        ]

        ledger_text = generate_beancount_ledger(
            transactions=transactions,
            own_iban="NL91INGB0001234567",
            title="Test Audit Ledger"
        )

        # Controleer directives en headers
        self.assertIn('option "title" "Test Audit Ledger"', ledger_text)
        self.assertIn('option "operating_currency" "EUR"', ledger_text)
        self.assertIn("open Assets:Bank:NL:NL91INGB0001234567 EUR", ledger_text)
        self.assertIn("open Income:Uitkering:Participatiewet EUR", ledger_text)
        self.assertIn("open Expenses:Wonen:Huur EUR", ledger_text)
        self.assertIn("open Expenses:Zorg:CAK EUR", ledger_text)

        # Verifieer Ketengrootboek metadata tags
        self.assertIn("keten_post: \"POST-WONEN-WMO-001\"", ledger_text)
        self.assertIn("keten_post: \"POST-CAK-SOZAWE-002\"", ledger_text)

        # Verifieer rekenkundige sluiting per transactie
        # Parse blocks
        blocks = [b.strip() for b in ledger_text.split("\n\n") if b.strip()]
        for b in blocks:
            lines = b.split("\n")
            if lines[0].startswith("2026-"):
                # Dit is een transactie
                postings = []
                for line in lines[1:]:
                    line_s = line.strip()
                    if line_s.endswith("EUR") and not line_s.startswith("open") and not line_s.startswith("balance"):
                        # Extract amount
                        parts = line_s.rsplit(" ", 2)
                        amt_str = parts[-2]
                        postings.append(Decimal(amt_str))
                if postings:
                    self.assertEqual(len(postings), 2, f"Verwacht 2 benen in dubbel boekhouden: {lines[0]}")
                    balance_sum = sum(postings)
                    self.assertEqual(balance_sum, Decimal("0.00"), f"Boeking sluit niet op nul: {lines[0]}")

    def test_full_analyze_bank_file_pipeline(self):
        """Test volledige pipeline met bestandscreatie en beancount export."""
        xml_path = os.path.join(self.temp_dir.name, "test_camt_full.xml")
        out_beancount = os.path.join(self.temp_dir.name, "output.beancount")
        with open(xml_path, "w", encoding="utf-8") as f:
            f.write(SAMPLE_CAMT_XML)

        analyze_bank_file(xml_path, export_beancount=True, custom_out=out_beancount)
        self.assertTrue(os.path.exists(out_beancount))
        with open(out_beancount, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("Woningstichting Voorbeeldstad", content)
            self.assertIn("Flanderijn", content)


if __name__ == "__main__":
    unittest.main()
