# 🛡️ Dialectisch Multi-Model Review Rapport: timeline_weaver.py

**Doelbestand:** `E:\LLM_Workspace\Civic_Case_Engine\_engine\timeline_weaver.py`  
**Opdracht:** Bekijk dit Python script voor de forensische tijdlijn- en bewijs-weaver kritisch. Toets op: 1. Logische en technische robuustheid (datum-parsing, CSV edge cases). 2. Forensische en juridische bruikbaarheid in bezwaar/beroep. 3. Wat ontbreekt er nog?

---

## 1. DeepSeek Audit (Logica, Code & Edge Cases)

# Kritische audit: `timeline_weaver.py`

## 1. Logische & technische robuustheid

### 1.1 Datum-parsing — fundamentele fouten

**`parse_dutch_date` — ISO-regex is ambiguïteit-blind.**
```python
r"\b(20\d{2})[-/.](0[1-9]|1[0-2])[-/.](0[1-9]|[12]\d|3[01])\b"
```
- Alleen `20xx`. Data vóór 2000 (bv. geboortedatum cliënt, oude beschikkingen) worden **stil genegeerd**. Voor een forensisch dossier is dat een gat.
- `[-/.]` accepteert `2026/05/12` en `2026.05.12` als ISO — juridisch onwenselijk: `2026.05.12` is in NL-notatie eerder `d.m.y`-achtig. Je introduceert valse positieven.
- Geen `datetime.strptime`-validatie op kalenderrealiteit vóór de `try` — die zit er wel, maar de regex matcht bv. `2026-02-30` en gooit dan stil `ValueError` → `pass` → `None`. **Stille drop van een parse-fout is forensisch onacceptabel**: je moet loggen dat een datum-achtige string niet parseerde.

**`parse_dutch_date` — NL-tekst regex is gevaarlijk breed.**
```python
r"\b(0?[1-9]|[12]\d|3[01])\s+([a-zA-Z]+)(?:\s+(20\d{2}))?\b"
```
- `[a-zA-Z]+` matcht élk woord. `"12 mei"` werkt, maar ook `"3 weken"`, `"5 dagen"`, `"2 keer"`. De `NL_MONTHS`-check vangt dat af — **mits** het woord exact in de dict staat. `"mei."` (met punt) faalt. `"Mei"` werkt (`.lower()`), `"MEI"` werkt. `"sept."` faalt. `"aug"` werkt, `"augustus"` werkt.
- **Jaar-default `2026` is een tijdbom.** Een WhatsApp-bericht `"12 mei"` uit 2024 wordt hard op 2026-05-12 gezet. In een juridisch dossier is dat **fabricage van een datum**. Erger: het script sorteert op die datum, dus één verkeerde default verschuift de hele ketenmatrix. Dit is de zwaarste fout in het script.
- Geen ondersteuning voor `12-05-2026`, `12/05/2026`, `12.05.2026` (NL-notatie). Alleen ISO en tekstueel. Bank-CSV's leveren juist `dd-mm-yyyy` → die vallen in `ingest_bank_csv` in de `d_digits`-tak, maar **niet** in `parse_dutch_date`. Inconsistent.
- `\b` na `(20\d{2})?` — als jaar ontbreekt matcht de regex t/m de maandnaam, prima. Maar `"12 mei 2026"` in een zin als `"op 12 mei 2026 om 14:00"` matcht correct. `"12 mei 2026"` in `"12 mei 20261"` matcht **niet** door `\b` — goed.

**`ingest_bank_csv` — `d_digits`-heuristiek is foutgevoelig.**
```python
d_digits = re.sub(r"[^0-9]", "", d_str)
if len(d_digits) == 8:
    if int(d_digits[:4]) >= 2010:  # YYYYMMDD
    else:                          # DDMMYYYY
```
- `"01-02-2026"` → `01022026` → `int("0102") = 102 < 2010` → `datetime(2026, 02, 01)`. Correct.
- `"2026-02-01"` → `20260201` → `int("2026") >= 2010` → `datetime(2026, 02, 01)`. Correct.
- **Maar**: `"01-02-26"` (2-cijferig jaar, komt voor in oudere ING-exports) → `010226` → lengte 6 → **stil overgeslagen**. Gat.
- **En**: `"2026-2-1"` (geen leading zeros) → `202621` → lengte 6 → overgeslagen. Gat.
- **En**: bedrag-kolom met 8 cijfers wordt nooit als datum gelezen, maar een `Datum`-kolom met tekst `"zie bijlage"` → `d_digits=""` → lengte 0 → overgeslagen. OK, maar stil.
- **Kritiek**: `int(d_digits[:4]) >= 2010` is een gok. Een DDMMYYYY-datum `"12-05-2010"` → `12052010` → `int("1205") >= 2010` → **True** → `datetime(1205, 20, 10)` → `ValueError` → `pass` → **stil gedropt**. Elke DDMMYYYY-datum in mei-dec van jaren 2010-2031 met dag > 2010 onmogelijk... wacht: `int(d_digits[:4])` bij DDMMYYYY is `DDMM`. `"1205"` = 1205 < 2010 → False → correcte tak. Maar `"3112"` = 3112 ≥ 2010 → **True** → foutieve YYYYMMDD-tak → `datetime(3112, 12, ...)` → ValueError → stil gedropt. **Dus elke DDMMYYYY-datum met dag ≥ 20 en maand ≥ 10 wordt stil gedropt.** Dat is een reële klasse datums (okt-dec, dag 20-31).

**`ingest_bank_csv` — kolom-detectie fragiel.**
- `row.get("Naam / Omschrijving")` — exacte string. ING gebruikt `"Naam / Omschrijving"`, Rabobank `"Naam tegenpartij"`, ABN `"Naam tegenpartij"`, Bunq `"Counterparty"`. Alleen ING-variant + generieke fallbacks. **ABN/Rabo/Bunq-omschrijvingen worden gemist** → transacties vallen door alle `if`-takken → stil gedropt.
- `row.get("Bedrag (EUR)")` — ING-specifiek. ABN: `"Bedrag"`. Rabo: `"Bedrag"`. OK, fallback dekt. Maar **bedrag-teken**: ING levert `"1.234,56"` (komma-decimaal). `"-" in bedrag` werkt voor af/bij, maar het bedrag wordt **niet genormaliseerd** — `€ 1.234,56` in de summary is juridisch onbruikbaar als je later wilt sommeren. Geen `Decimal`-parsing.
- `af_bij` fallback `("Af" if "-" in bedrag else "Bij")` — als bedrag `"1.234,56-"` (trailing minus, sommige banken) → `"-" in bedrag` True → "Af". Correct. Maar als bedrag `"1.234,56"` en kolom `Af Bij` ontbreekt → "Bij". **Stille aanname**.
- **Geen deduplicatie.** Twee keer dezelfde CSV in de map (backup + origineel) → dubbele events. Voor een chronologie fataal.

### 1.2 WhatsApp-parsing

```python
m_msg = re.match(r"^\*\s+\*\*([^(]+)\s*(?:\(([^)]+)\))?:\*\*\s*(.*)$", line)
```
- Vereist exact `* **Naam (tijd):** bericht`. Echte WhatsApp-exports zijn `[12-05-2026 14:23:45] Naam: bericht` of `12-05-2026, 14:23 - Naam: bericht`. **Geen enkele echte WhatsApp-export matcht deze regex.** Alleen handmatig geconverteerde Markdown. Dat is een bewuste keuze, maar dan moet de docstring dat zeggen — nu suggereert "zowel raw .txt als Markdown transcripties" iets anders. **De code ondersteunt geen raw .txt.**
- `([^(]+)` voor naam: naam met haakje erin breekt. Zeldzaam, acceptabel.
- `(?:\(([^)]+)\))?` voor tijd: `(14:23

---

## 2. Grok Audit (Strategie, Instituties & Velvet Glove)

**Strategische en institutionele review: CIVIC CASE ENGINE — Forensische Tijdlijn- & Bewijs-Weaver**

Het script is een serieuze poging tot zero-dependency forensische ordening van heterogene bronnen. Het denkt in ketens, stiltes en domeinen — precies de taal die bureaucratieën en bestuursrechters herkennen. Dat is strategisch sterk. Hieronder de toetsing op de gevraagde assen, in gewone zinnen, met scherpe kern.

### 1. Logische en technische robuustheid (datum-parsing, CSV edge cases)

**Datum-parsing**  
`parse_dutch_date` dekt ISO en Nederlandse maandnamen redelijk. Sterke punten: fallback naar 2026 bij ontbrekend jaar en tolerantie voor “12 mei”. Zwakke punten die in de praktijk breken:

- Geen ondersteuning voor “12-05-2026”, “12/5/26”, “mei 2026” zonder dag, of “12e mei”.  
- Geen validatie op onmogelijke datums voorbij de try/except (29 februari non-schrikkeljaar sneuvelt stil).  
- Defaultjaar 2026 is gevaarlijk: bij oudere dossiers of toekomstige runs verschuift alles ongemerkt.  
- WhatsApp-markdown en generic markdown hangen volledig aan de laatste `###`-datum. Een ontbrekende of foute header-datum verplaatst hele blokken. Geen per-regel datumextractie als fallback.  
- Call-logs gebruiken `fromtimestamp` zonder timezone-awareness. Epoch-ms uit Android kan UTC of lokaal zijn; dit creëert stille verschuivingen van uren die later als “tegenstrijdigheid” worden aangevallen.

**CSV edge cases**  
De bank-ingest is pragmatisch (delimiter-detectie, utf-8-sig, meerdere kolomnamen), maar breekbaar:

- Geen handling van geneste quotes, multiline-velden of banken die “Bedrag” als “-1.234,56” versus “-1234.56” aanleveren. De huidige bedrag-extractie is puur string; rekenkundige controle of normalisatie ontbreekt.  
- Datumlogica (8 digits) raadt volgorde op basis van jaartal ≥ 2010. Dat faalt bij Amerikaanse exports of oudere bestanden.  
- Geen deduplicatie: dezelfde transactie uit twee CSV’s (of bij herhaalde runs) verschijnt dubbel.  
- Lege of corrupte rijen worden stil overgeslagen; er is geen logging van verworpen regels. In forensische context is “wat is weggelaten” even belangrijk als wat erin staat.  
- Encoding `errors="replace"` is veilig maar vernietigt bewijs (vervangingskarakters). Beter: harde fail of aparte error-log.

**Algemene robuustheid**  
- Geen hash of checksum van bronbestanden → integriteitsaanval mogelijk (“dit bestand is later gewijzigd”).  
- Geen versie- of run-metadata in de output behalve timestamp.  
- Sorted events gooien events zonder `date_dt` weg; die verdwijnen spoorloos.  
- Anomaly-detectie (42 dagen) is hard-coded en domein-beperkt. Geen configureerbare termijnen per wet (Awb 4/6/8 weken, Wmo, Participatiewet).  
- Memory: alles in één lijst. Bij grote WhatsApp-archieven + jaren bankdata wordt dit traag en onoverzichtelijk, maar voor typische dossiers acceptabel.

**Kern oordeel techniek**: Werkbaar voor gecontroleerde, schone input. Niet production-grade forensisch. Een tegenpartij of rechter-commissaris die de parser laat nalopen, vindt snel edge-cases waarmee de hele chronologie “onbetrouwbaar” kan worden bestempeld. Dat is een machtslek.

### 2. Forensische en juridische bruikbaarheid in bezwaar/beroep

**Sterke hefbomen**  
- Domein-tags (Zorg, Financiën, Huisvesting, Bestuursrecht) + severity (Ketenbreuk, Stilte, Besluit) spreken de taal van de Awb en de bestuursrechter. “Institutionele stilte” na 42 dagen is een directe brug naar fatale termijnen en zorgplicht.  
- Raw quote + source_file in elke regel maakt de matrix citeerbaar. Dat is goud voor een bezwaarschrift of beroepschrift: “zie Master Chronologie, regel X, bron Y”.  
- Automatische detectie van ketenbreuken en stiltes levert kant-en-klare argumenten voor “nalaten”, “onredelijke vertraging” of “schending zorgplicht”.  
- Zero dependencies en pure standaardbibliotheek verlagen de drempel voor overlegging als bijlage (geen black-box-verwijt).

**Zwaktes die de machtsbalans ondermijnen**  
- De output is een Markdown-tabel, geen ondertekende, gehashte of notarieel vastgelegde export. In bezwaar/beroep wordt dit al snel “partijdig opgesteld overzicht” genoemd. Zonder hash-keten of originele bestandsbijlagen verliest het bewijskracht.  
- Actor-normalisatie ontbreekt. “Gemeente”, “0888889450”, “Sociale Zaken” blijven losse strings. Een bestuursorgaan zal zeggen: “niet aangetoond dat dit dezelfde instantie is”.  
- Geen expliciete koppeling aan wetsartikelen of beslistermijnen. De stilte-detector roept “42 dagen” maar noemt niet art. 4:13 Awb, art. 4:14, of sectorspecifieke termijnen. Daardoor blijft het feitelijk i.p.v. juridisch geladen.  
- Severity “Ketenbreuk” wordt getriggerd door keywords in WhatsApp. Dat is subjectief en aanvechtbaar (“selectieve framing”).  
- Geen onderscheid tussen feiten en duiding. De anomaly-context mengt samenvatting met interpretatie. Rechters willen feitenmatrix + aparte juridische duiding.  
- Call-logs en bankmutaties krijgen automatisch domein; dat kan over-interpretatie opleveren (een gemiste oproep ≠ zorgweigering).  
- Geen audit-trail van de weaver zelf: welke regex matchte, waarom severity X. Bij betwisting moet je kunnen uitleggen hoe het algoritme tot de conclusie kwam.

**Psychologische en institutionele effectiviteit (Velvet Glove)**  
Het document oogt professioneel en neutraal-technisch. Dat is hoffelijk. Tegelijk is de toon van de anomalies al beschuldigend (“Institutionele Stilte”, “Zorgval”). Dat kan de tegenpartij in de verdediging jagen en de rechter laten denken aan activistisch opgesteld bewijs. Beter: strikt feitelijke matrix + aparte, terughoudende “Signaal-detectie”-sectie met disclaimers (“mogelijke overschrijding van oriëntatietermijn; nader juridisch te duiden”).  

Menselijk: een chronologie die te “slim” anomalies labelt, wordt door ambtenaren en juristen als vijandig ervaren. Dan sluiten ze. Een chronologie die feiten onwrikbaar ordent en de lezer zelf de stilte laat voelen, is machtiger. De huidige versie zit ertussenin.

**Kern oordeel juridisch**: Bruikbaar als interne werkinstrument en als bijlage ter ondersteuning van een goed geschreven bezwaar. Nog niet als zelfstandig, onaanvechtbaar bewijsstuk. Het verschuift de bewijslast onvoldoende naar het bestuursorgaan omdat authenticiteit, volledigheid en neutraliteit nog te makkelijk betwistbaar zijn.

### 3. Wat ontbreekt er nog? (prioriteit voor machtsbalans)

Concrete hiaten die de institutionele slagkracht direct vergroten:

1. **Integriteitslaag**  
   SHA-256 van elk bronbestand + opname in de output. Run-ID, parser-versie, command-line argumenten. Zonder dit blijft het “een script dat de cliënt heeft gedraaid”.

2. **Configureerbare juridische termijnen**  
   Dictionary of YAML met Awb-termijnen, Wmo, Participatiewet, CAK-specifiek, etc. Anomaly-detectie moet “overschrijding wettelijke beslistermijn X” kunnen zeggen i.p.v. hard-coded 42 dagen.

3. **E-mail/brief-parser met header-extractie**  
   Het script noemt e-mails & brieven in de docstring maar implementeert ze niet. Message-ID, From, Date, Subject + body-anker zijn cruciaal voor correspondentie-ketens.

4. **Deduplicatie en event-merging**  
   Zelfde feit uit bank + WhatsApp + notitie moet één event met meerdere bronnen worden, niet drie regels.

5. **Actor- en entiteit-resolutie**  
   Simpele alias-
