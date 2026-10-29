# Wijzigingen

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
