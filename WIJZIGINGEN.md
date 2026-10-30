# Wijzigingen

## 2026-10-30

Open-Source Adoptie voor de Civic Case Engine (Batches 1, 3 en 4):

- **Cryptografische Chain-of-Custody & Contra-Boekingen (Batch 3, `Ketengrootboek/sluiting.py`, `_engine/beancount_exporter.py`):**
  - **Append-only Hash Chain (`sluiting.py --custody`):** Bouwt een cryptografische bewijsketen (SHA-256 gekoppeld aan de voorgaande hash) over alle Laag-1 waarnemingen in Boek 1 (Memoriaal), conform FRE 803(6) en art. 8:29 jo. 8:39 Awb (vrije bewijslevering). Slaat op in `chain_of_custody.jsonl` (afgeschermd in `.gitignore`).
  - **Contra-Boekingen & Status Betwist:** Vorderingen en transacties gekoppeld aan betwiste loket-interpretaties of ketenbreuken krijgen automatisch de metadata `vordering_status: "betwist"` en de Beancount-tag `#betwist` ter scheiding van formele claims en juridisch verweer.
  - **Unit Test Coverage:** `test_sluiting.py` uitgebreid met `test_cryptografische_chain_of_custody` (10 tests 100% geslaagd).
- **Lichtgewicht Awb Besluit-Detector (Batch 4, `_engine/awb_besluit_scanner.py`, `_engine/test_awb_besluit_scanner.py`):**
  - **100% Python Standard Library (0 dependencies):** Toetst inkomende stukken van overheidsinstanties op rechtsgevolg (art. 1:3 Awb), rechtsmiddelenclausules (art. 3:45 / 6:7 Awb, 6-wekentermijn), voorbereidingshandelingen (art. 6:3 Awb) en grond voor ingebrekestelling (art. 4:17 Awb).
  - **Human-in-the-Loop Veiligheidsgarantie:** Fungeert conform Tafel-afspraak strikt als suggestiefilter (`--json` of markdown besliskaart); start nooit autonoom termijnen zonder menselijke bevestiging aan De Tafel.
  - **Unit Test Coverage:** 4 gerichte unit tests toegevoegd in `test_awb_besluit_scanner.py` (alle 4 geslaagd).
- **Multi-LLM Dialectiek & Blinde Feiten-Extractie (Batch 1, `Shared_Tools/multi_llm_audit.py`):**
  - **Fase 1 Blinde Extractie:** Onafhankelijke voor-extractie van harde feitelijke waarnemingen via DeepSeek en Gemini Flash vóórdat het inhoudelijke debat start. Berekent concordantiescore en genereert consensustabellen en discrepantievlaggen.
  - **Deterministische Citaten- & Jurisprudentietoets:** Valideert geciteerde wetsartikelen (Awb, Wmo, AVG, UAVG, BW, Zvw, Woo) en ECLI-uitspraken automatisch tegen het standaardregister (`BEKEND` vs. `ONBEKEND / TE VERIFIËREN`).
- **Institutionele Condities & Poldermodel-Vertaler (`_engine/institutional_conditions.py`, `_engine/test_institutional_conditions.py`, `_engine/awb_besluit_scanner.py`):**
  - **5 Structurele Condities (Civic Decision Engine v13.0 adaptatie):** Deterministische detectie van `TRANSFER_OF_BURDEN` (omkering van inspanning), `PROCEDURAL_DEFLECTION` (loketfuik / vormdrempels), `REPEATED_CONTACT_WITHOUT_RESOLUTION` (institutionele amnesie), `INSTITUTIONAL_DELAY` (termijndruk) en `ESCALATION_WITHOUT_RESPONSE` (urgentietoename zonder tempo-aanpassing).
  - **Poldermodel & Fluwelen Handschoen (Protocol FH-01 integratie):** De condities fungeren strikt als interne diagnose voor De Tafel en de boekhouding. Per conditie wordt automatisch een hoffelijke, ontlastende Polder-handreiking gegenereerd die de ambtenaar zoekwerk bespaart, gezichtsverlies voorkomt en zijn professionele beslissingsruimte respecteert.
  - **Scanner-koppeling & Testdekking:** `awb_besluit_scanner.py` toont bij inkomende stukken direct de conditiediagnose én de diplomatieke conceptformulering. 5 nieuwe unittests toegevoegd in `test_institutional_conditions.py` (totaal 55 tests in CivicHelper slagen 100%).
- **Protocol FH-01 Code-Verankering, ModelBus-Integratie & Omgevingsoptimalisatie (`_engine/sbar_protocol.py`, `_engine/veto_gate.py`, `_engine/audit_engine.py`, `hulp/lus.py`, `gui/*`):**
  - **Protocol FH-01 in `_engine/sbar_protocol.py` & `_engine/veto_gate.py` (Veto 6):** Implementeert deterministische toetsing op de Drie IJkcontroles (*1. Inhoudscontrole*, *2. Taalhandelingcontrole*, *3. Ruimtecontrole*), de Twee Negatieve Invarianten (*geen Agency Inversion*, *sussen noch demoniseren*) en het 2-staps Invoer-Filter (`build_fh01_intake_prompts` / `audit_engine.py --incoming`).
  - **Dubbele-Klok Synchronisatie (Veto 5):** `VetoGate._find_active_clocks()` controleert nu zowel `Dossier/termijnen.json` als de openstaande termijnen in Boek 3 (`Ketengrootboek/ketengrootboek.json`).
  - **`_engine/audit_engine.py` op `model_bus.py` & `pii_mask.py`:** Volledige aansluiting van de dialectische brief-auditor op `gui/model_bus.py` en `gui/pii_mask.py` (automatische lokale PII-maskering en ondersteuning voor alle modelhuizen incl. gratis NVIDIA NIM en Gemini).
  - **Herstel `ontkiem.py --check` & `bootstrap.py --check`:** `test_briefketen_offline()` geïmplementeerd in `hulp/lus.py` zodat alle vier startvoorwaarden lokaal en netwerkvrij groen draaien.
  - **Tafelvenster & Synchronisatie (`gui/` <-> `Shared_Tools/`):** De 6 `gui/`-modules zijn 100% gelijkgetrokken met `Shared_Tools/`, ontdaan van hardcoded schijf-/gebruikerspaden, en in `tafel_gui.py` + `START.cmd` uitgebreid met de Awb Besluit-Scanner (controle 9), de Keten-Klok (controle 10) en de FH-01 poorttoets.
  - **Privacy & Hygiëne:** Drie historische `send_*.py` scripts in de root ontdaan van hardcoded wachtwoord-fallbacks en verplaatst naar `Shared_Tools/archief_sporen/`; zaakspecifieke namen uit `_engine/gtid_engine.py` en `_engine/guard_gate.py` verplaatst naar het lokale `werk/loketten.json`.


## 2026-10-29

Protocol FH-01, Epistemische Laagscheiding, Multimodale Ketenintegriteit & De Klok:

- **Protocol FH-01 (`NOTITIE_COMMUNICATIEPROTOCOL_SBARIII.md`):**
  - **Vier Epistemische Lagen:** Formele scheiding tussen Bewijs (`memoriaal.json` + SHA-256 brondocumenten), Interpretatie/Hypotheses (`boek2_journaal.json`), Doel- en constraintlaag (`ketengrootboek.json` & De Klok) en Transformatie (`TAFEL.md` / Fluwelen Handschoen).
  - **Invoer-Filter (2 Stappen):** Stap 1 toont het analyserende model uitsluitend de letterlijke tekst voor neutrale feitenregistratie en taalkundige lezingen (zonder doelstellingen, escalatiekaders of strategie). Pas in Stap 2 worden Ketengrootboek-doelen en Tafel-wegingen aangekoppeld.
  - **Drie IJkcontroles & Twee Negatieve Invarianten:** Inhoudscontrole (100% behoud van feiten en hulpvraag), Taalhandelingcontrole en Ruimtecontrole. Strikt verbod op Agency Inversion (geen verborgen fuiken) en verbod op adaptief overdrijven (sussen noch demoniseren).
- **Ketengrootboek v2.0 & De Klok (`Ketengrootboek/sluiting.py`, `Ketengrootboek/AGENTS.md`, `test_sluiting.py`):**
  - **Simon Stevin 3-Boekenstelsel:** Volledige ondersteuning voor Boek 1 (Het Memoriaal `memoriaal.json`), Boek 2 (Het Journaal `boek2_journaal.json`) en Boek 3 (Het Ketengrootboek `ketengrootboek.json`).
  - **Multimodale Verificatie:** Ondersteuning voor gekoppelde bewijsbundels (`extra_bewijsstukken`: audio/WAV/MP3, PDF, Markdown, XML/CSV) met SHA-256 integriteitscontrole.
  - **De Klok (`sluiting.py --klok`):** Berekent en rapporteert openstaande wettelijke termijnen, vervaldata en actuele dagen resterend direct vanuit Boek 2 en 3.
  - **Ketenintegriteitsrapport (`sluiting.py --integriteit`):** Genereert een compleet 3-boeken integraal auditverslag in Markdown.
- **Boekhoud-Sorteerder & Tafel-Oogster (`Ketengrootboek/tafel_sorteerder.py`):**
  - Deterministische bronparser voor het sorteren en SHA-256 verifiëren van bewijsstukken vanuit inkomende post, audio en e-mail naar de drie boeken.
- **Privacy & Git-Hygiëne (`.gitignore`, `Ketengrootboek/grootboek.json`):**
  - Persoonlijke casusboeken (`memoriaal.json`, `boek2_journaal.json`, `ketengrootboek.json`, `tafel_besluiten.json`) en verzonden correspondentie (`Outgoing_Letters/*`) hermetisch genegeerd.
  - Het openbare `grootboek.json` blijft strikt Voorbeeldstad en bevat het actuele v2.0-schema inclusief `tafel_besluit` en `termijn`.

## 2026-10-26

Stroomlijning van Civic Helper 0.3 — Tafel, Simon Stevin 3-Boekenstelsel en Beancount/CAMT-integratie:

- **Tafelvenster (`gui/tafel_gui.py` & `gui/omgeving_inrichter.py`):**
  - Linkerkolom gestroomlijnd van 6 naar 4 tabbladen (`Overzicht | Dossiers | Brieven | Analyse`).
  - `Overzicht` toont in gewone taal de **Twee Klokken** (*1. Loket-klok* vs. *2. Lichaams-klok `v(t)`*) én **3. Ketenstatus (Simon Stevin 3 Boeken & Sluiting)**.
  - `Dossiers` voorzien van live zoek-/filterbalk; `Brieven` voorzien van In/Uit-filter, directe poorttoets (`🛡️ Toets Poort`) en verzendsein (`✉️ Sein`).
  - Nieuwe werkbalkknop **`🛠️ Omgeving Inrichten`** die de lokale mappen en Python-tools inricht, een live `pii_mask.py` zelfproef toont, het 5-stappenplan met *Waarom & Doel* uitlegt en twee 1-klik knoppen biedt voor de gratis NVIDIA-sleutel (inloggen met hetzelfde Gmail-account en plakken vanaf klembord zonder terminal).
- **3-Boekenstelsel van Simon Stevin & Ketenintegriteitslaag (`Ketengrootboek/sluiting.py`, `Ketengrootboek/AGENTS.md`, `test_sluiting.py`):**
  - Elke overdracht wordt getoetst op **drie onafhankelijke sluitingskenmerken**: `rekenkundig_sluitend`, `procedureel_gesloten` en `materieel_vereffend`, met afgeleide diagnoses (`MATERIEEL_VEREFFEND`, `SCHIJNSLUITING`, `TEGENSTRIJDIGE_REGISTRATIE`, `UITSTAANDE_OVERDRACHT`) en onderbouwde Werklexicon-analysecodes (`ATE`, `STASIS`, `PROSOPON`, `MENIS`).
  - **Niet-Overschrijvingsinvariant (Laag 1 vs. Laag 3):** Een latere loket-interpretatie (`interpretatie_historie`) mag een oorspronkelijke waarneming in het Memoriaal nooit wijzigen of vervangen (`verifieer_niet_overschrijving`).
  - **Boek 3 (`bouw_rekeningen_grootboek` & `herleid_rekening`):** Reconstrueert de positie per loket met terugwaartse herleidbaarheid naar het Journaal en het Memoriaal.
- **CAMT.053 & Beancount Dubbel-Boekhouden (`_engine/camt_parser.py`, `_engine/beancount_exporter.py`, `_engine/bank_audit.py`, `_engine/test_bank_audit.py`):**
  - 0-token lokale verwerking van bank-CSV's en ISO 20022 CAMT.053 XML naar sluitende `.beancount`-ledgers ($\sum = 0,00\text{ EUR}$), gekoppeld aan de 3 sluitingskenmerken (`*` = materieel vereffend, `!` = schijnsluiting/conflict).
- **Scheiding tussen zaak en programma & Modelbus (`gui/model_bus.py`):**
  - Zaakspecifieke namen verplaatst naar `werk/loketten.json` buiten git; `Ketengrootboek/*.beancount` toegevoegd aan `.gitignore`.
  - Gratis 2-stappen instap (1x Gmail + 1x gratis NVIDIA NIM voor meerdere onafhankelijke modelfamilies: `Nemotron 120B`, `OpenAI GPT-OSS 20B`, `MiniMax M3.1 Flash`) ingebouwd in `model_bus.py`.

## 2026-10-20

De naam op de deur is Agentische Werkomgeving Basisadministratie. Het ketengrootboek staat in de definitie, in het Nederlands en in het Engels.

- `README.md` opent met die definitie en wijst naar `README.en.md`. De deur is `CivicHelper.cmd` of `hulp/start_venster.sh`. `START.cmd` blijft het menu voor de bouwer.
- `README.en.md` is de Engelse deur in dezelfde repository. Er is geen tweede GitHub.
- Lokale `file:///`-links en paden naar deze schijf zijn uit de gevolgde notities gehaald.
- `interfaces.json` wijst niet meer naar het persoonlijke dossier. Getuigenissen die daar lagen, staan nu op `lokaal/buiten-git.md`. Namen van behandelaren zijn uit dat bestand.
- `sync_landscape.py` leest het dossier uit `CCE_DOSSIER`, of uit `werk/`, `Dossier/` of `Landschap/` in deze repository.
- `sluiting.py` en `glue_check.py` zoeken een getuige in de repository, niet op een vaste schijfletter.
- `CivicHelper.cmd` en `Ontkiem.cmd` starten Python van het pad. Zij noemen geen gebruikersprofiel.
- `hulp/lus.py` en `ontkiem.py` zoeken `agy` op het pad, en daarna in de thuismap.

De oude commits bewaren de vorige `interfaces.json`. Die geschiedenis is niet herschreven.

De about-regel van de repository hoort dezelfde definitie te dragen als de eerste alinea van de README.

In dezelfde notitie is daarna de belofte van een meteen verzendbare brief geschrapt. De klok noemt het gat. De ingebrekestelling blijft in de achterzak zolang het gesprek open is. Het concept wacht op het sein.
