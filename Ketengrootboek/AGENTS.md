# Ketengrootboek — Operationele Gids voor Agenten (Simon Stevin 3 Boeken & Werklexicon)

Dit is de deur voor elke agent (Agy, Grok, DeepSeek, Gemini) die met het registratiesysteem van **Civic Helper** werkt.

---

## 1. De Architectuur: De Drie Boeken van Simon Stevin

Het registratiesysteem scheidt **waarneming**, **overdracht** en **toestand** in drie boeken (`Ketengrootboek/sluiting.py`):

| Boek | Bestand / Functie | Wat erin staat | Harde Invariant |
| :--- | :--- | :--- | :--- |
| **Boek 1: Het Memoriaal** *(Laag 1 + Laag 3)* | `memoriaal.json` *(spiegel: `journaal.json`)* | **Laag 1 (Multimodale Waarneming):** `id`, `datum`, `type`, `modaliteit`, `actor`, `omschrijving`, `bewijsstuk`, `extra_bewijsstukken` (WAV/PDF/MD/CSV + SHA-256).<br>**Laag 3 (Interpretaties):** `interpretatie_historie` (hoe een loket het feit later classificeerde, met `betwist: true/false`). | **Niet-Overschrijvingsregel:** Een latere interpretatie of afwijzing (Laag 3) mag een oorspronkelijke waarneming (Laag 1) **nooit** wijzigen, verwijderen of vervangen. |
| **Boek 2: Het Journaal** *(Laag 2)* | `boek2_journaal.json` *(spiegel: `grootboek.json`)* | De gekoppelde overdrachten (`POST-...`) tussen Zender (`debet_rekening`) en Ontvanger (`credit_rekening`), inclusief `tafel_besluit` (kwalificatie/autorisatie aan de Tafel), `termijn` (`verval_datum`, `uiterste_datum`) en de controlevelden (`overdracht_velden`). | Een ontvangstbevestiging, automatische melding of doorverwijzing zonder uitvoering (`NIET_SLUITENDE_TYPES`) sluit **nooit** een overdrachtspost. |
| **Boek 3: Het Ketengrootboek & De Klok** | `ketengrootboek.json` *(spiegel: `saldo.json`)* | 100% automatisch afgeleide positie per rekening/loket (`rekeningen_grootboek`), de afgeleide **Klok** (`openstaande_termijnen`), en **terugwaartse herleidbaarheid** (`Rekening -> Post_ID -> Tafel_Besluit -> Feit_ID + SHA-256`). | Elke open verplichting én elke lopende termijn blijft zichtbaar op het loket tot er materieel sluitingsbewijs op schijf ligt. |

---

## 2. De Drie Onafhankelijke Sluitingskenmerken (Geen enkelvoudige statuskleur)

Elke overdracht én elke loketrekening wordt getoetst op **drie afzonderlijke booleans**:

1. **`rekenkundig_sluitend` (`True/False`):** Zijn de boekingen tussen de betrokken loketten onderling consistent? (`False` bij inter-loket tegenspraak, zoals Vektis *Status N onverzekerd* vs. Menzis/CAK *premie-incasso*, of DACAS *verrekening* vs. *€ 0,00 bankkasstroom*).
2. **`procedureel_gesloten` (`True/False`):** Heeft het loket zijn eigen processtap, ontvangstbevestiging, doorverwijzing of beschikking formeel afgerond?
3. **`materieel_vereffend` (`True/False`):** Is de onderliggende verplichting daadwerkelijk geleverd (`FASE_3_FEITELIJKE_REALISATIE`) met een bestaand bewijsbestand + SHA-256 op schijf?

### Afgeleide Keten-diagnoses & Onderbouwde Werklexicon-codes
- `(True, True, True)` $\rightarrow$ **`MATERIEEL_VEREFFEND`** (`KATHARSIS_VEREFFEND`)
- `(True, True, False)` $\rightarrow$ **`SCHIJNSLUITING`** (`ATE_LOKALE_AFSLUITING_ZONDER_KETENVERVOLG`: loket sluit procedure af, maar ketenverplichting staat materieel open)
- `(False, True, False)` $\rightarrow$ **`TEGENSTRIJDIGE_REGISTRATIE`** (`STASIS_TEGENSTRIJDIGE_WERKELIJKHEID`: twee administraties sluiten elk intern, maar boeken onverenigbare feiten)
- `(True, False, False)` $\rightarrow$ **`UITSTAANDE_OVERDRACHT`** (`MENIS_ONVEREFFEND_RESTANT`)

*Let op:* Gebruik Griekse Werklexicon-termen (`PROSOPON`, `STASIS`, `ATE`, `MENIS`) nooit als losse beschuldiging in een brief naar een loket, maar uitsluitend als onderbouwde analysecode in het dossier die verwijst naar een concreet Laag-1 bewijsstuk.

---

## 3. Commando's & Python-API voor Agenten

### A. Via de Command Line (CLI)
```powershell
# 1. Volledige proefbalans draaien en saldo.json bijwerken
python Ketengrootboek\sluiting.py ALL

# 2. Volledig 3-Boeken Ketenintegriteitsrapport (Grootboek + Journaal 9 velden + Memoriaal Laag 1/3)
python Ketengrootboek\sluiting.py --integriteit

# 3. Eén specifiek loket vanuit het Grootboek terugwaarts herleiden naar Journaal & Memoriaal
python Ketengrootboek\sluiting.py --rekening wmo

# 4. Alle 8 regressie- en ketenintegriteitstests draaien
python Ketengrootboek\test_sluiting.py -v

# 5. Bank Audit (CSV & CAMT.053 XML) en Beancount-Export draaien
python _engine\bank_audit.py [bestand]

# 6. Institutioneel Ketengrootboek & Bank exporteren naar Beancount (.beancount)
EXPORT_BEANCOUNT.cmd

# 7. Bank audit & Beancount testsuite draaien
python _engine\test_bank_audit.py -v
```

### B. Via Python (`SluitingsToetser`)
```python
from Ketengrootboek.sluiting import SluitingsToetser

toetser = SluitingsToetser()

# 1. Nieuwe waarneming in Boek 1 (Laag 1 — berekent SHA-256, weigert overschrijving van bestaand feit)
toetser.registreer_waarneming(
    feit_id="EVT-VOORBEELD-20261026",
    datum="2026-10-26",
    feit_type="schriftelijk_bewijs",
    actor="Afzender",
    omschrijving="Feitelijke waarneming uit het brondocument.",
    bewijsstuk="Incoming_Letters/voorbeeld.md",
)

# 2. Latere loket-interpretatie toevoegen in Boek 1 (Laag 3 — laat Laag 1 gegarandeerd intact)
toetser.registreer_interpretatie_op_feit(
    feit_id="EVT-CORP-20260715",
    classificatie="Loket stelt dat er geen hulpvraag was.",
    actor="Loket X",
    datum="2026-10-26",
    betwist=True,
    werklexicon_code="STASIS_BETEKENISVERSCHUIVING",
    grondslag_betwisting="Weerlegd door schriftelijk noodsignaal van 15 juli 2026.",
)
```
