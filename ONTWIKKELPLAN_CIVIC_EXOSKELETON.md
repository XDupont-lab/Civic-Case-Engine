# Civic Case Engine (Civic Exoskeleton) — Master Ontwikkelplan v1.0

**Status:** Vastgelegd & Operationeel  
**Auteur:** Civic Case Engine Project & Agy (Antigravity)  
**Datum:** 13 september 2026  
**Locatie:** E:\LLM_Workspace\Civic_Case_Engine\

---

## 1. Visie & Fundamentele Grondslag

De moderne burger-bureaucratie interface functioneert in de praktijk op basis van **structurele asymmetrische uitputting**:
* **Oneindige institutionele tijd vs. eindige menselijke energie:** Instanties beschikken over geautomatiseerde incassostraten, juridische afdelingen en ambtenaren die van 9 tot 5 betaald worden om procedures te volgen. De burger heeft uitsluitend zijn eigen zenuwstelsel, stress en fysieke/mentale reserves.
* **Executieve frictie als poortwachter:** Formulieren zijn complex, termijnen verstopt en dossiers gefragmenteerd. Burgers met chronische multimorbiditeit, NAH of acute bestaansonzekerheid lopen vast op de administratieve rompslomp.
* **De emotionele val:** Frustratie en angst worden door de bureaucratie direct bestempeld als "onbehoorlijk gedrag" of "weerstand", waardoor de inhoudelijke aanspraak van tafel wordt geveegd.

De **Civic Case Engine** is ontworpen als een **Civic Exoskeleton (Asymmetrie-Nivelleerder)**. Het compenseert de executieve belasting en kantelt de machtsbalans via vier kernpijlers:

1. **De Grote Omkering (Lastenverschuiving & Asymmetrie-opheffing):** In plaats van smeken om zorg of kwijtschelding, schiet de burger gestandaardiseerde, wettelijke sondes af (art. 15 AVG, art. 3:2 Awb). De instantie wordt wettelijk gedwongen om binnen fatale termijnen (30 dagen) zelf het speur- en collatiewerk in haar archieven te doen en haar wettelijke onderzoeks- en motiveringsplicht na te komen.
2. **Forensische Datakoppeling:** Wat geen sociaal advocaat kan bekostigen binnen een toevoeging: binnen seconden 10 jaar aan bankmutaties auditen, communicatielogs ontsluiten en contract- en zorgbreuken mathematisch dichtspijkeren.
3. **The Velvet Glove (De Fluwelen Handschoen):** De engine vangt emotionele frictie op en sublimeert deze naar formele, waardige, uiterst hoffelijke, maar juridisch onwrikbare teksten.
4. **Lokale Soevereiniteit:** Volledig lokaal op de eigen machine. Nul afhankelijkheid van commerciële cloud-diensten voor de data-opslag. 100% Python standaardbibliotheek, zero-pip installatiedruk.

### 1.1 De Conceptuele Taxonomie: Twee Complementaire Dimensies

In plaats van de beperkte noemer 'wrapper' of een verwarring tussen doel en techniek, rust het ontwerp op twee scherp gescheiden dimensies:

#### A. Functioneel-Filosofische Dimensie (Het 'Waarom' en 'Voor Wie')
1. **Maatschappelijk & Strategisch — Het Civic Exoskeleton (Burgerlijk Exoskelet):**  
   De asymmetrie-nivelleerder die de individuele burger voorziet van dezelfde institutionele documentatiekracht, juridische precisie en procedurele slagkracht als een overheidsorgaan of commercieel incassobedrijf.
2. **Cognitief & Neurologisch — Externe Executieve Functie (Cognitieve Prothese):**  
   Het systeem fungeert als een externe prothese voor het door NAH, chronische ziekte of stress overbelaste werkgeheugen. Het bewaakt termijnen, structureert feiten en dwingt strikte schriftelijkheid af om cognitieve energie te sparen.

#### B. Technisch-Operationele Dimensie (Het 'Hoe' en de 'Code')
3. **Systeemtechnisch & Deterministisch — De Civic Legal Kernel (Machinekamer):**  
   De zuivere, lokale Python-infrastructuur (zero-dependency, standard library) die de procedurele status beheert: Awb-dwangsomklok (`statutory_clock.py`), SHA-256 integriteitsregister (`timeline_weaver.py`), en bundeling (`case_bundler.py`).
4. **AI-Engineering & Probabilistisch — Het Agentic Case Framework (Agentic Harness):**  
   De multi-model tuigage (`audit_engine.py`) met strikte epistemische scheiding:
   * **Grok-4.6 (live websearch):** Verifieert actuele wetgeving (`wetten.overheid.nl`), bewaakt 'The Velvet Glove' en analyseert institutionele machtsdynamiek.
   * **DeepSeek (statisch model zonder web):** Uitsluitend ingezet als *advocaat van de duivel* voor formele argumentatieleer, interne consistentie en het ontdekken van procedurele mazen; *geen* autoriteit over wetteksten of feiten.

### 1.2 De Cybernetische Lus & De Vijf Systeemlagen (L0 – L4)

Een lokale agent is geen brievenschrijver, maar een externe executieve lus die drie ontkoppelde klokken waarneemt en synchroniseert:
* **$\omega_c$ (Cliëntklok):** Leefwereld, lichaam, zorggat (continue biologische tijd).
* **$\omega_w$ (Protocolklok):** Systeemwereld, zaaksystemen (Gws4all, Socrates), productcodes (trage ambtelijke relaxatie).
* **$\omega_*$ (Procedurele Klok):** Discrete, wederzijds getuigde flank (Awb-dwangsom, AVG-termijn van 30 dagen, Zivver-logs). Dwingt $\omega_w$ tot aansluiting op $\omega_c$.

Het systeem bewaakt vijf strikt gescheiden lagen (zie [CYBERNETISCHE_ARCHITECTUUR.md](file:///E:/LLM_Workspace/Civic_Case_Engine/CYBERNETISCHE_ARCHITECTUUR.md)):
1. **L0 — Cliënttoestand ($\omega_c$):** NAH, dysexecutie, interne context (lekt niet naar buiten).
2. **L1 — Landschap van Entiteiten:** Functionele slots, mandaat, zaaksystemen, ambtelijke `ingest-capaciteit` $\subseteq$ `{productcodes, termijnen, keten, klinisch, privacy}`. CV dient als bandbreedte-filter.
3. **L2 — Discours (optioneel):** Default UIT. Relais naar raadsgriffie/fracties bij claims over 'zelfreinigend vermogen'.
4. **L3 — Klokken ($\omega_*$):** Fatale termijnen, $t=0$, driftbewaking (telefoon = drift = directe schriftelijke bevestiging).
5. **L4 — Actie & Inhibitie (Dispatcher):** Handhaaft de gouden invariant:
   $$\mathbf{Crisiscommit} \oplus \mathbf{Saaie\ Sonde}$$
   *(Crisiscommit XOR Saaie Sonde. Nooit mengen in één document).*

---

## 2. Architectuur van het Framework

`
Civic_Case_Engine/
├── START.cmd                  # Centraal opstartmenu (frictieloos)
├── SWITCH_DOMAIN.cmd          # Wisselen tussen wetgevingsdomeinen
├── AUDIT_DRAFT.cmd            # Een-klik constructieve audit van brieven
├── AUDIT_BANK_CSV.cmd         # Forensische bankrekening-audit
├── README.md                  # Snelgids en introductie
├── DOCTRINE.md                # Actief geladen juridische doctrine
├── ONTWIKKELPLAN_CIVIC_EXOSKELETON.md # Dit masterplan
│
├── _engine/                   # De machinekamer (pure Python stdlib)
│   ├── audit_engine.py        # Universele constructieve auditor
│   ├── bank_audit.py          # Financiële bronheffing & woonstabiliteitsscanner
│   ├── timeline_weaver.py     # [Batch 1] Forensische tijdlijn & bewijskoppeling
│   ├── statutory_clock.py     # [Batch 2] Termijnen-, dwangsom- en AVG-klok
│   └── domain_packs/          # Modulaire rechtsdomeinen (kaders & jurisprudentie)
│       ├── nl_wmo/            # Wmo 2015, Awb, urennorm, compensatieplicht
│       ├── nl_schulden_oninbaar/ # Vbvv, beslagverbod, CAK-uitstroom, WIK
│       ├── nl_uwv/            # ZW, WIA, FML-weerlegging, art. 9 lid 2 PW
│       ├── nl_brp_adres/      # Briefadres afdwingen, VOW bestrijden
│       ├── nl_toeslagen/      # Terugvorderingen matigen, evenredigheid
│       └── uk_housing/        # Equality Act 2010, Section 21/8, disrepair
│
├── Dossier/                   # Het 12-delige domeinoverstijgende dossier
│   ├── 00_Master_Chronologie.md
│   ├── 01_Zorg_en_Gezondheid.md tot 12_Vergunningen_en_Toezicht.md
│
├── Probes/                    # Scherpe wettelijke uitvraag-mallen (AVG, Awb, Woo)
├── Incoming_Letters/          # Ontvangen post van instanties (analyseerbaar)
├── Outgoing_Drafts/           # Conceptbrieven en geauditeerde versies
└── Landschap/                 # Institutionele machtskaart (Keten, Politiek, Organisatie)
`

---

## 3. Uitwerkingsplan in 4 Batches

#### Batch 1: Forensische Tijdlijn- & Bewijs-Weaver (timeline_weaver.py) — [Gerealiseerd & Operationeel]
* **Doel:** Ongeordende bronnen (bank-CSV's, WhatsApp-exports, gespreksverslagen, e-mailheaders) automatisch ordenen en correleren tot een integrale Master_Chronologie.md.
* **Status:** Gerealiseerd via `_engine/timeline_weaver.py` en `WEAVE_TIMELINE.cmd`.
* **Bereikt resultaat:**
  * Ondersteuning voor ING, Rabobank, ABN AMRO, Triodos bank-CSV's, WhatsApp raw/markdown exports, Android telefoongesprek logs (epoch timestamps) en dossiernotities.
  * SHA-256 integriteitsregister gegenereerd voor elk bronbestand.
  * Automatische detectie van zorgbreuken en institutionele communicatiestiltes (art. 2.3.10 Wmo).
  * Succesvol gedraaid op voorbeeldcasussen: genereert integrale chronologie en hashes van feiten.

### Batch 2: Juridische Termijnen- & Dwangsommen Tracker (statutory_clock.py) — [Gerealiseerd & Operationeel]
* **Doel:** De fatale wettelijke termijnen van instanties proactief bewaken en automatisch overgaan tot rechtsgevolgen bij verzaking.
* **Status:** Gerealiseerd via `_engine/statutory_clock.py` en `CHECK_TERMIJNEN.cmd`.
* **Bereikt resultaat:**
  * Automatische berekening van de Awb-dwangsom (art. 4:17 Awb: € 23 / € 35 / € 45 per dag tot max. € 1.442).
  * Blokkeert premature, ongeldige ingebrekestellingen en handhaaft de 14-dagen opschortingstermijn na ontvangst.
  * Genereert met één commando een juridisch onwrikbare formele ingebrekestelling (`INGEBREKESTELLING_[ZAAK].md`).
  * Voorgeladen met de 4 generieke AVG-sondes (Woningcorporatie, Zorgverzekeraar, Gerechtsdeurwaarder, Sociale Dienst).

### Batch 3: Juridische Verdieping Domain Packs — [Gerealiseerd & Operationeel]
* **Doel:** De doctrines laden met harde wetgeving en jurisprudentie van de hoogste bestuursrechters (Centrale Raad van Beroep, Raad van State, Hoge Raad).
* **Status:** Volledig geactualiseerd naar v2.0/v2.1 in `_engine/domain_packs/`:
  1. `nl_wmo` (v2.1): CRvB 2016:1803 (verbod op resultaatsgericht indiceren/urennorm), CRvB 2018:3474 (bewijslast bij herindicatie), Art. 2.3.5 lid 3 Wmo, Art. 2.2.4 (cliëntondersteuning), Art. 2.3.6 (pgb), Art. 2.3.10 (verbod op feitelijke beëindiging).
  2. `nl_schulden_oninbaar` (v2.0): Wvbvv art. 475b-e Rv, Art. 447/448 Rv (absoluut beslagverbod noodzakelijke inboedel en medische hulpmiddelen), Feitelijke oninbaarheid & Art. 3:13 BW misbruik van bevoegdheid, HR 2016:2704 (vernietiging buitengerechtelijke kosten bij ondeugdelijke 14-dagenbrief), CAK-wanbetalersregeling uitstroom ex art. 18d-e Zvw.
  3. `nl_uwv` (v2.0): Deconstructie FML (Rubriek 1 & Rubriek 6 Standaard Duurbelastbaarheid in Arbeid), CRvB 2020:3342 (voorkeur behandelend sector / motiveringsplicht verzekeringsarts), CBBS-toetsing, Art. 9 lid 2 Participatiewet (medische arbeidsontheffing).
  4. `nl_toeslagen` (v2.0): ABRvS 2019:3535 (evenredigheidsbeginsel breekt alles-of-niets), Art. 13b Awir, Art. 47 Awir (hardheidsclausule), Art. 6:11 Awb (verschoonbare termijnoverschrijding bij ziekte/NAH).
  5. `nl_brp_adres` (v2.0): Art. 2.23 Wet BRP (recht op briefadres), Landelijke Circulaire BRP (verplichte ambtshalve toekenning), Verbod op VOW-uitschrijving zonder deugdelijk adresonderzoek, Art. 8 EVRM.

### Batch 4: Frictieloze Interface & Bundel-Exporter — [Gerealiseerd & Operationeel]
* **Doel:** De bediening van het Civic Exoskeleton zo intuïtief en prikkelarm mogelijk maken voor een burger met verminderde energie.
* **Status:** Gerealiseerd via `_engine/case_bundler.py`, `EXPORT_BUNDEL.cmd` en centraal geïntegreerd in `START.cmd`.
* **Bereikt resultaat:**
  * **Procesdossier Bundler:** Genereert met één klik een integraal dossier met frontispice, inhoudsopgave, actieve doctrine, uittreksel van de 905 feiten uit de master-chronologie, SHA-256 integriteitsregister, genummerde producties en formeel petitum.
  * **Twee formaten:** GitHub-flavored Markdown (`.md`) én printklare HTML (`.html`) met professionele typografie en CSS `@media print` pagina-einden (`page-break-after: always`), direct om te zetten naar PDF via de browser (Ctrl+P) zonder zware dependencies.
  * **One-Stop Hub:** `START.cmd` biedt een overzichtelijk 8-keuzemenu met alle modules binnen één handomdraai.

---

## 4. De Interactie met het Zorgdossier ("Living Lab")

* **Strikte Scheiding:**
  * [Civic_Case_Engine/](file:///E:/LLM_Workspace/Civic_Case_Engine/) blijft 100% geanonimiseerd, domein-agnostisch en openbaar overdraagbaar als software-framework.
  * Lokale operationele dossiers blijven strikt gescheiden van deze openbare repository.
* **Kruisbestuiving:**
  Elke innovatie die in de praktijk van complexe casussen wordt ontdekt (zoals de 10-jarige bank-audit of de telefoon-extractie) wordt direct gesteriliseerd en als generieke module in de Civic Case Engine geplaatst.
