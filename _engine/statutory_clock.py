#!/usr/bin/env python3
"""
CIVIC CASE ENGINE — CIVIC LEGAL KERNEL (STATUTORY CLOCK & PENALTY TRACKER v2.0)
Civic Exoskeleton Deterministic State Machine.
Pure Python Standard Library (Zero External Dependencies).

Rol in de architectuur:
Het deterministische hart van de Civic Legal Kernel. Bewaakt wettelijke termijnen
en berekent Awb-dwangsommen zonder cognitieve belasting voor de burger.

Functies:
1. Mathematische bewaking van bestuursrechtelijke beslistermijnen (Awb, Wmo, AVG, Woo).
2. Blokkeert premature ingebrekestellingen (bescherming tegen niet-ontvankelijkheid).
3. Strikt onderscheid tussen verzenddatum en ontvangstdatum (art. 4:17 lid 3 Awb).
4. Nauwkeurige dwangsomstaffel (art. 4:17 lid 2 Awb) met behoud/bevriezing van opgebouwde vorderingen.
5. Ondersteuning voor verdaging (art. 4:15 Awb / art. 2.3.2 lid 2 Wmo).
6. Volledige CLI-statemachine: status, add, extend, set-received, set-decision, draft.
"""

import os
import sys
import json
from datetime import datetime, date, timedelta
from pathlib import Path

STATUTORY_RULES = {
    "AVG_INZAGE": {
        "name": "AVG Inzageverzoek",
        "days": 30, # 1 maand ex art. 12 lid 3 AVG
        "law_article": "Art. 12 lid 3 AVG",
        "description": "Wettelijke reactietermijn van één maand voor inzage in persoonsgegevens.",
        "action_on_expire": "Ingebrekestelling ex art. 4:17 Awb + Klacht Autoriteit Persoonsgegevens"
    },
    "WMO_ONDERZOEK": {
        "name": "Wmo Onderzoeksfase",
        "days": 42, # 6 weken ex art. 2.3.2 lid 1 Wmo 2015
        "law_article": "Art. 2.3.2 lid 1 Wmo 2015",
        "description": "College rondt het onderzoek binnen 6 weken na de melding af.",
        "action_on_expire": "Formele aanvraag maatwerkvoorziening indienen ex art. 2.3.5 lid 1 Wmo 2015"
    },
    "WMO_BESCHIKKING": {
        "name": "Wmo Beschikking na Aanvraag",
        "days": 14, # 2 weken ex art. 2.3.5 lid 2 Wmo 2015
        "law_article": "Art. 2.3.5 lid 2 Wmo 2015",
        "description": "College geeft de beschikking binnen 2 weken na ontvangst van de aanvraag.",
        "action_on_expire": "Ingebrekestelling ex art. 4:17 Awb (dwangsomklok)"
    },
    "AWB_AANVRAAG_ALGEMEEN": {
        "name": "Awb Algemene Beslistermijn",
        "days": 56, # 8 weken ex art. 4:13 lid 2 Awb
        "law_article": "Art. 4:13 lid 2 Awb",
        "description": "Redelijke termijn voor een beschikking (maximaal 8 weken na ontvangst aanvraag).",
        "action_on_expire": "Ingebrekestelling ex art. 4:17 Awb"
    },
    "AWB_BEZWAAR_BESLUIT": {
        "name": "Awb Beslissing op Bezwaar",
        "days": 42, # 6 weken ex art. 7:10 lid 1 Awb
        "law_article": "Art. 7:10 lid 1 Awb",
        "description": "Beslistermijn van 6 weken na afloop van de bezwaartermijn.",
        "action_on_expire": "Ingebrekestelling ex art. 4:17 Awb + Beroep niet tijdig beslissen art. 6:2 sub b Awb"
    },
    "WOO_VERZOEK": {
        "name": "Woo Informatieverzoek",
        "days": 28, # 4 weken ex art. 4.4 lid 1 Woo
        "law_article": "Art. 4.4 lid 1 Woo",
        "description": "Bestuursorgaan beslist binnen 4 weken op een Woo-verzoek.",
        "action_on_expire": "Ingebrekestelling ex art. 4:17 Awb"
    },
    "INGEBREKESTELLING_HERSTEL": {
        "name": "Awb Ingebrekestelling Hersteltermijn",
        "days": 14, # 2 weken ex art. 4:17 lid 3 Awb
        "law_article": "Art. 4:17 lid 3 Awb",
        "description": "Hersteltermijn van 2 weken na ontvangst van ingebrekestelling voordat dwangsom start.",
        "action_on_expire": "Wettelijke dwangsom loopt van rechtswege + Beroep Rechtbank"
    }
}

def calculate_dwangsom(days_overdue):
    """
    Wettelijke staffel artikel 4:17 lid 2 Awb:
    - Dag 1 t/m 14: € 23 per dag (max € 322)
    - Dag 15 t/m 28: € 35 per dag (max € 490)
    - Dag 29 t/m 42: € 45 per dag (max € 630)
    - Maximum: over ten hoogste 42 dagen, tot € 1.442,00.
    """
    if days_overdue <= 0:
        return 0.0
    
    days = min(days_overdue, 42)
    total = 0.0
    
    t1 = min(days, 14)
    total += t1 * 23.0
    
    if days > 14:
        t2 = min(days - 14, 14)
        total += t2 * 35.0
        
    if days > 28:
        t3 = min(days - 28, 14)
        total += t3 * 45.0
        
    return total

class StatutoryClockManager:
    def __init__(self, data_file=None):
        if not data_file:
            base_dir = Path(__file__).resolve().parent.parent
            self.data_file = base_dir / "Dossier" / "termijnen.json"
        else:
            self.data_file = Path(data_file)
        
        self.clocks = []
        self.load()

    def load(self):
        if self.data_file.exists():
            try:
                with open(self.data_file, "r", encoding="utf-8") as f:
                    self.clocks = json.load(f)
            except Exception as e:
                print(f"[!] Waarschuwing: Kon {self.data_file} niet laden: {e}")
                self.clocks = []
        else:
            self.clocks = []

    def save(self):
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump(self.clocks, f, indent=2, ensure_ascii=False)

    def add_clock(self, clock_id, authority, clock_type, sent_date_str, reference="", notes="", court_district="Noord-Nederland"):
        """Voegt een nieuwe termijnklok toe."""
        if clock_type not in STATUTORY_RULES:
            raise ValueError(f"Onbekend type termijn: {clock_type}. Kies uit: {list(STATUTORY_RULES.keys())}")
        
        dt_sent = datetime.strptime(sent_date_str, "%Y-%m-%d").date()
        rule = STATUTORY_RULES[clock_type]
        deadline = dt_sent + timedelta(days=rule["days"])
        
        clock = {
            "id": clock_id,
            "authority": authority,
            "type": clock_type,
            "law_article": rule["law_article"],
            "sent_date": sent_date_str,
            "deadline": deadline.strftime("%Y-%m-%d"),
            "original_deadline": deadline.strftime("%Y-%m-%d"),
            "reference": reference,
            "court_district": court_district,
            "notes": notes,
            "status": "LOPEND",
            "extension_days": 0,
            "extension_reason": None,
            "ingebrekestelling_sent_date": None,
            "ingebrekestelling_received_date": None,
            "decision_date": None,
            "frozen_dwangsom": None
        }
        
        self.clocks = [c for c in self.clocks if c["id"] != clock_id]
        self.clocks.append(clock)
        self.save()
        print(f"[+] Klok '{clock_id}' aangemaakt. Deadline: {clock['deadline']} ({rule['law_article']})")

    def extend_clock(self, clock_id, extra_days, reason="Rechtsgeldig verdagingsbesluit bestuursorgaan"):
        """Registreert een rechtsgeldige verdaging ex art. 4:15 Awb."""
        clock = next((c for c in self.clocks if c["id"] == clock_id), None)
        if not clock:
            print(f"[!] Fout: Klok '{clock_id}' niet gevonden.")
            return
        
        current_deadline = datetime.strptime(clock["deadline"], "%Y-%m-%d").date()
        new_deadline = current_deadline + timedelta(days=int(extra_days))
        clock["deadline"] = new_deadline.strftime("%Y-%m-%d")
        clock["extension_days"] = clock.get("extension_days", 0) + int(extra_days)
        clock["extension_reason"] = reason
        self.save()
        print(f"[+] Klok '{clock_id}' verdaagd met {extra_days} dagen naar {clock['deadline']}. Reden: {reason}")

    def set_received_date(self, clock_id, received_date_str):
        """Legt de datum vast waarop de ingebrekestelling door de instantie is ontvangen."""
        clock = next((c for c in self.clocks if c["id"] == clock_id), None)
        if not clock:
            print(f"[!] Fout: Klok '{clock_id}' niet gevonden.")
            return
        
        datetime.strptime(received_date_str, "%Y-%m-%d") # validatie
        clock["ingebrekestelling_received_date"] = received_date_str
        self.save()
        print(f"[+] Ontvangstdatum voor '{clock_id}' geregistreerd: {received_date_str}")

    def set_decision(self, clock_id, decision_date_str):
        """Registreert ontvangst van het formele besluit en bevriest eventueel opgebouwde dwangsom."""
        clock = next((c for c in self.clocks if c["id"] == clock_id), None)
        if not clock:
            print(f"[!] Fout: Klok '{clock_id}' niet gevonden.")
            return
        
        dt_dec = datetime.strptime(decision_date_str, "%Y-%m-%d").date()
        clock["decision_date"] = decision_date_str
        clock["status"] = "AFGEROND"
        
        # Berekening bevroren dwangsom
        dwangsom = 0.0
        rec_str = clock.get("ingebrekestelling_received_date") or clock.get("ingebrekestelling_sent_date")
        if rec_str:
            rec_dt = datetime.strptime(rec_str, "%Y-%m-%d").date()
            herstel_deadline = rec_dt + timedelta(days=14)
            overdue_days = (dt_dec - herstel_deadline).days
            dwangsom = calculate_dwangsom(overdue_days)
            
        clock["frozen_dwangsom"] = dwangsom
        self.save()
        print(f"[+] Besluit voor '{clock_id}' geregistreerd op {decision_date_str}.")
        if dwangsom > 0:
            print(f"    💰 Opeisbare verbeurde dwangsom bevroren op: € {dwangsom:.2f}")

    def evaluate_status(self, today=None):
        """Berekent dynamisch de actuele status en openstaande vorderingen."""
        if not today:
            today = date.today()
        elif isinstance(today, str):
            today = datetime.strptime(today, "%Y-%m-%d").date()

        evaluated = []
        total_open_dwangsom = 0.0

        for c in self.clocks:
            deadline = datetime.strptime(c["deadline"], "%Y-%m-%d").date()
            
            if c.get("decision_date"):
                status = f"AFGEROND (Besluit op {c['decision_date']})"
                dwangsom = c.get("frozen_dwangsom", 0.0)
                days_diff = (datetime.strptime(c["decision_date"], "%Y-%m-%d").date() - deadline).days
            else:
                diff = (today - deadline).days
                days_diff = diff
                if diff < 0:
                    status = f"LOPEND (nog {-diff} dagen tot deadline)"
                    dwangsom = 0.0
                elif diff == 0:
                    status = "FATALE DAG (vandaag verstrijkt de wettelijke termijn!)"
                    dwangsom = 0.0
                else:
                    status = f"IN VERZUIM ({diff} dagen overschreden ⚠️)"
                    rec_str = c.get("ingebrekestelling_received_date") or c.get("ingebrekestelling_sent_date")
                    if rec_str:
                        rec_dt = datetime.strptime(rec_str, "%Y-%m-%d").date()
                        herstel_deadline = rec_dt + timedelta(days=14)
                        overdue_dwangsom = (today - herstel_deadline).days
                        dwangsom = calculate_dwangsom(overdue_dwangsom)
                    else:
                        dwangsom = 0.0

            total_open_dwangsom += dwangsom
            item = dict(c)
            item["current_status"] = status
            item["days_diff"] = days_diff
            item["dwangsom_accrued"] = dwangsom
            evaluated.append(item)
            
        return evaluated, total_open_dwangsom

    def print_status_table(self, today=None):
        evaluated, total_dwangsom = self.evaluate_status(today)
        print("\n" + "=" * 95)
        print("          CIVIC CASE ENGINE — STATUS WETTELIJKE TERMIJNEN & DWANGSOMMEN")
        print("=" * 95)
        if not evaluated:
            print("Geen actieve termijnklokken geregistreerd.")
            return

        for c in evaluated:
            print(f"\n[ID: {c['id']}] Instantie: {c['authority']} (Kenmerk: {c.get('reference', '-')})")
            print(f"  Type: {STATUTORY_RULES[c['type']]['name']} ({c['law_article']})")
            print(f"  Verzonden: {c['sent_date']} | Deadline: {c['deadline']}", end="")
            if c.get("extension_days", 0) > 0:
                print(f" (verdaagd met +{c['extension_days']}d)")
            else:
                print()
            print(f"  Status: {c['current_status']}")
            
            if c['dwangsom_accrued'] > 0:
                print(f"  💰 Opeisbare dwangsom: € {c['dwangsom_accrued']:.2f} (max € 1.442,00)")
            
            if "IN VERZUIM" in c['current_status'] and not c.get("ingebrekestelling_sent_date"):
                print("  🚨 ACTIE VEREIST: Stuur direct een formele Ingebrekestelling (art. 4:17 Awb)!")
            elif c.get("ingebrekestelling_sent_date") and not c.get("ingebrekestelling_received_date"):
                print("  ℹ️ TIP: Registreer ontvangstdatum via 'set-received' voor onwrikbare dwangsomstart.")

        print("\n" + "-" * 95)
        print(f"TOTAAL GECUMULEERDE DWANGSOMVORDERINGEN: € {total_dwangsom:.2f}")
        print("=" * 95)

    def generate_ingebrekestelling(self, clock_id, client_name="Voorbeeld Burger", client_address="Hoofdstraat 1, 1000 AA Amsterdam", dry_run=False, force=False):
        """Genereert een formele ingebrekestelling ex art. 4:17 Awb (met blokkade voor premature verzending)."""
        clock = next((c for c in self.clocks if c["id"] == clock_id), None)
        if not clock:
            print(f"[!] Fout: Klok met ID '{clock_id}' niet gevonden.")
            return None

        today = date.today()
        deadline = datetime.strptime(clock["deadline"], "%Y-%m-%d").date()

        # Harde blokkade voor premature ingebrekestelling
        if today <= deadline and not force:
            days_left = (deadline - today).days
            print(f"\n[BLOKKADE] Premature ingebrekestelling afgewezen!")
            print(f"De wettelijke termijn voor '{clock['authority']}' loopt nog {days_left} dagen (tot {clock['deadline']}).")
            print("Een premature ingebrekestelling is van rechtswege ongeldig en leidt tot afwijzing van proceskosten.")
            print("Gebruik --force om deze waarschuwing te negeren indien er sprake is van een eerdere fatale datum.")
            return None

        today_str = today.strftime("%d-%m-%Y")
        sent_dt = datetime.strptime(clock["sent_date"], "%Y-%m-%d").strftime("%d-%m-%Y")
        deadline_dt = deadline.strftime("%d-%m-%Y")
        rule = STATUTORY_RULES[clock["type"]]
        court = clock.get("court_district", "Noord-Nederland")

        doc = []
        doc.append(f"# Formele Ingebrekestelling wegens Niet Tijdig Beslissen (ex art. 4:17 Awb)\n")
        doc.append(f"**Aan:**  \nHet College van Burgemeester en Wethouders van de Gemeente {clock['authority']}  \n(Ter attentie van de afdeling Juridische Zaken / Bezwaar & Beroep)\n")
        doc.append(f"**Van:**  \n{client_name}  \n{client_address}\n")
        doc.append(f"**Datum verzending:** {today_str}  ")
        doc.append(f"**Kenmerk / Referentie:** {clock.get('reference', 'Zaakdossier / Awb')}  ")
        doc.append(f"**Onderwerp:** Ingebrekestelling ex artikel 4:17 Algemene wet bestuursrecht — Niet tijdig beslissen op {rule['name']}\n")
        doc.append("---\n")
        doc.append("Geacht College,\n")
        doc.append(f"Ondergetekende, {client_name}, stelt uw College hierbij formeel **in gebreke** wegens het overschrijden van de wettelijke beslistermijn.\n")
        doc.append("### Feitelijke en wettelijke grondslag:")
        doc.append(f"1. Op **{sent_dt}** heeft ondergetekende een formele aanvraag / melding ingediend betreffende: *{rule['name']}*.")
        doc.append(f"2. Ingevolge **{rule['law_article']}** bedraagt de wettelijke termijn voor uw handelen of beschikken maximaal **{rule['days']} dagen**.")
        doc.append(f"3. Deze termijn is op **{deadline_dt}** ongebruikt verstreken, zonder dat ondergetekende een deugdelijk gemotiveerd verdagingsbesluit of de vereiste beschikking heeft ontvangen.")
        doc.append(f"4. Uw College verkeert derhalve sinds **{deadline_dt}** van rechtswege in verzuim.\n")
        doc.append("### Aanzegging dwangsom (Artikel 4:17 Awb):")
        doc.append("Ingevolge artikel 4:17 lid 3 van de Algemene wet bestuursrecht geef ik uw College hierbij een termijn van **twee weken** (14 kalenderdagen) na de dag van ontvangst van deze brief om alsnog de vereiste beschikking bekend te maken.\n")
        doc.append("Indien uw College na afloop van deze tweewekentermijn nog steeds in gebreke blijft, verbeurt uw College ingevolge artikel 4:17 lid 1 en 2 Awb een dwangsom aan ondergetekende voor elke dag dat het verzuim voortduurt, te weten:")
        doc.append("- De eerste 14 dagen: € 23,00 per dag;")
        doc.append("- De volgende 14 dagen: € 35,00 per dag;")
        doc.append("- De daaropvolgende 14 dagen: € 45,00 per dag;")
        doc.append("tot een maximum van € 1.442,00 (over ten hoogste 42 dagen).\n")
        doc.append(f"### Voorbehoud direct beroep bij de Rechtbank {court} (Artikel 6:2 sub b Awb):")
        doc.append(f"Mocht na het verstrijken van de hersteltermijn nog geen besluit zijn genomen, dan zal ondergetekende onverwijld rechtstreeks **beroep instellen bij de Bestuursrechter van de Rechtbank {court}** wegens het niet tijdig nemen van een besluit (ex art. 6:2 sub b jo. art. 7:1 lid 1 sub f Awb), waarbij tevens vergoeding van de proceskosten en de vaststelling van de opgelopen dwangsom zal worden gevorderd.\n")
        doc.append("Met vriendelijke groet,\n\n\n")
        doc.append(f"{client_name}")

        output_dir = self.data_file.parent.parent / "Outgoing_Drafts"
        output_dir.mkdir(parents=True, exist_ok=True)
        filename = f"INGEBREKESTELLING_{clock['id']}_{today.strftime('%Y%m%d')}.md"
        out_path = output_dir / filename

        with open(out_path, "w", encoding="utf-8") as f:
            f.write("\n".join(doc))

        if not dry_run:
            clock["ingebrekestelling_sent_date"] = today.strftime("%Y-%m-%d")
            self.save()
            print(f"[+] Formele ingebrekestelling gegenereerd en geregistreerd: {out_path}")
        else:
            print(f"[DRY-RUN] Concept-ingebrekestelling gegenereerd (niet geregistreerd als verzonden): {out_path}")

        return out_path

if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

    manager = StatutoryClockManager()
    
    if len(sys.argv) < 2 or sys.argv[1] in ["--help", "-h"]:
        print("Gebruik van Statutory Clock:")
        print("  python statutory_clock.py status                          -> Toon actueel overzicht van alle termijnen & dwangsommen")
        print("  python statutory_clock.py add <id> <inst> <type> <datum>  -> Voeg een klok toe (datum formaat: JJJJ-MM-DD)")
        print("  python statutory_clock.py extend <id> <dagen> [reden]     -> Registreer een verdaging (art. 4:15 Awb)")
        print("  python statutory_clock.py set-received <id> <datum>       -> Registreer ontvangstdatum van ingebrekestelling")
        print("  python statutory_clock.py set-decision <id> <datum>       -> Registreer formeel besluit (bevriest dwangsom)")
        print("  python statutory_clock.py draft <id> [--force] [--dry-run] -> Genereer formele ingebrekestelling (art. 4:17 Awb)")
        print(f"\nOndersteunde termijntypes: {', '.join(STATUTORY_RULES.keys())}")
        sys.exit(0)

    cmd = sys.argv[1].lower()
    if cmd == "status":
        manager.print_status_table()
    elif cmd == "add":
        if len(sys.argv) < 6:
            print("Fout: Verwacht: python statutory_clock.py add <id> <instantie> <type> <datum_JJJJ-MM-DD> [referentie] [rechtbank]")
            sys.exit(1)
        cid, inst, ctype, dt_s = sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5]
        ref = sys.argv[6] if len(sys.argv) > 6 else ""
        court = sys.argv[7] if len(sys.argv) > 7 else "Noord-Nederland"
        manager.add_clock(cid, inst, ctype, dt_s, reference=ref, court_district=court)
    elif cmd == "extend":
        if len(sys.argv) < 4:
            print("Fout: Verwacht: python statutory_clock.py extend <id> <extra_dagen> [reden]")
            sys.exit(1)
        reason = sys.argv[4] if len(sys.argv) > 4 else "Rechtsgeldig verdagingsbesluit bestuursorgaan"
        manager.extend_clock(sys.argv[2], int(sys.argv[3]), reason)
    elif cmd == "set-received":
        if len(sys.argv) < 4:
            print("Fout: Verwacht: python statutory_clock.py set-received <id> <datum_JJJJ-MM-DD>")
            sys.exit(1)
        manager.set_received_date(sys.argv[2], sys.argv[3])
    elif cmd == "set-decision":
        if len(sys.argv) < 4:
            print("Fout: Verwacht: python statutory_clock.py set-decision <id> <datum_JJJJ-MM-DD>")
            sys.exit(1)
        manager.set_decision(sys.argv[2], sys.argv[3])
    elif cmd in ["draft", "draft-ingebrekestelling"]:
        if len(sys.argv) < 3:
            print("Fout: Geef het ID van de klok op.")
            sys.exit(1)
        force_flag = "--force" in sys.argv
        dry_flag = "--dry-run" in sys.argv
        manager.generate_ingebrekestelling(sys.argv[2], force=force_flag, dry_run=dry_flag)
    else:
        print(f"Onbekend commando: '{cmd}'. Gebruik --help voor een overzicht.")
