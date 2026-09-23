# Civic Case Engine (Civic Exoskeleton) — Systeemarchitectuur & Referentie

> **Definitie:** Een lokaal, soeverein **Civic Exoskeleton**, aangedreven door een **Civic Legal Kernel** en een **Agentic Case Framework (Harness)**. Ontworpen als een **Externe Executieve Functie** om de structurele machtsasymmetrie tussen burger en bureaucratie op te heffen.

Het framework is 100% geanonimiseerd, domein-agnostisch en openbaar overdraagbaar. Het bevat géén persoonlijke dossiers; persoonlijke data en instantiespecifieke dossiers (zoals `Zaakdossier_Persoonlijk/` of `UK_Housing_Exoskeleton/`) worden separaat gekoppeld.

---

## 🚀 Snelle Start (1-Prompt Turnkey Replicatie)

### Voor Antigravity / Agy Agents:
Geef je agent deze prompt:
> *"Zet de Civic Case Engine lokaal voor me op door `SETUP_ALL.cmd` (of `python setup_environment.py`) uit te voeren."*

### Voor Menselijke Gebruikers (1-Klik):
1. **Clone de repository**:
   ```bash
   git clone https://github.com/XDupont-lab/Civic-Case-Engine.git
   cd Civic-Case-Engine
   ```
2. **Dubbelklik op `SETUP_ALL.cmd`**:
   * Installeert automatisch Python en Git via Windows Package Manager (`winget`) indien nog niet aanwezig.
   * Richt de virtuele AI-omgeving in (`.venv_bu`) inclusief Playwright Chromium browser voor portaal- en documentinzage.
   * Start de interactieve 5-stappen wizard (`bootstrap.py`) om jouw dossier en rechtsdomein te selecteren.
3. **Klaar voor actie**: Open `START.cmd` of stuur je opdrachten direct via je agent!

---

## 1. De Conceptuele Taxonomie: Twee Dimensies

Om categoriefouten te voorkomen, ontkoppelt de architectuur het maatschappelijke doel van de technische machinekamer. Het systeem kent twee complementaire dimensies:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ A. FUNCTIONEEL-FILOSOFISCHE DIMENSIE (Het 'Waarom' en 'Voor Wie')           │
├─────────────────────────────────────────────────────────────────────────────┤
│ 1. MAATSCHAPPELIJK / STRATEGISCH: HET CIVIC EXOSKELETON                     │
│    Asymmetrie-nivelleerder — Heft de informatie-asymmetrie op en dwingt     │
│    het bestuursorgaan tot naleving van zijn wettelijke onderzoeksplicht.    │
│                                                                             │
│ 2. COGNITIEF / NEUROLOGISCH: EXTERNE EXECUTIEVE FUNCTIE (PROTHESE)          │
│    Vangt executieve frictie, NAH en stress op. Verschuift de zoek-, reken-   │
│    en bewaarlast naar de computer en dwingt strikte schriftelijkheid af.    │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ realiseert zich in
┌──────────────────────────────────────▼──────────────────────────────────────┐
│ B. TECHNISCH-OPERATIONELE DIMENSIE (Het 'Hoe' en de 'Code')                 │
├─────────────────────────────────────────────────────────────────────────────┤
│ 3. SYSTEEMTECHNISCH / DETERMINISTISCH: DE CIVIC LEGAL KERNEL                │
│    Pure Python stdlib (zero-pip). Beheert de procedurele staat, fatale      │
│    termijnen, Awb-dwangsommen (statutory_clock), SHA-256 en procesbundels.  │
│                                                                             │
│ 4. AI-ENGINEERING / PROBABILISTISCH: HET AGENTIC CASE FRAMEWORK (HARNESS)   │
│    Spant meerdere LLM's in met strikte epistemische rolverdeling. Geen      │
│    vrijblijvende babbelboxen, maar gerichte dialectische auditoren.          │
└─────────────────────────────────────────────────────────────────────────────┘
```

### A. De Functioneel-Filosofische Dimensie

#### Pijler 1: Het Civic Exoskeleton (Burgerlijk Exoskelet)
* **Het probleem:** Instanties bezitten oneindige ambtelijke tijd, geautomatiseerde incassosystemen en juridische afdelingen. De burger heeft slechts één biologisch zenuwstelsel en beperkte reserves.
* **De werking:** Het Exoskelet heft de structurele informatie-asymmetrie op. Met formele sondes (art. 15 AVG, art. 3:2 Awb) wordt de instantie gedwongen binnen fatale termijnen (30 dagen) zelf in haar archieven te spitten en haar wettelijke onderzoeks- en motiveringsplicht na te komen.

#### Pijler 2: Externe Executieve Functie (Cognitieve Prothese)
* **Het probleem:** Chronische ziekte, NAH of acute bestaansonzekerheid leiden tot executieve dysfunctie onder stress (moeite met plannen, prioritering, telefoongesprekken en emotionele overbelasting).
* **De werking:** Het fungeert als een cognitieve prothese. Alle communicatie wordt gedwongen tot schriftelijkheid ("The Velvet Glove"), emotionele valkuilen worden geneutraliseerd en termijnen worden extern bewaakt.

### B. De Technisch-Operationele Dimensie

#### Pijler 3: De Civic Legal Kernel (Deterministische Machinekamer)
* **Het fundament:** 100% Python 3 standaardbibliotheek, zero-dependency, lokaal soeverein. Geen probabilistische gissingen over fatale termijnen of integriteit.
* **Kernmodules (`_engine/`):**
  * `statutory_clock.py`: Wiskundige Awb-, Wmo-, AVG- en Woo-termijnenbewaker met automatische dwangsomteller (art. 4:17 Awb) en ingebrekestelling-generator.
  * `timeline_weaver.py`: Forensische parser voor bank-CSV's, WhatsApp-logs, call-logs en e-mails met automatische SHA-256 verificatie en zorgbreukdetectie.
  * `case_bundler.py`: Assembleert alle producties, chronologie en doctrine tot een rechtbank- en ombudsmanklare procesbundel (.md en printklare HTML).
  * `domain_packs/`: Modulaire juridische drivers (`nl_wmo`, `nl_schulden_oninbaar`, `nl_uwv`, `nl_toeslagen`, `nl_brp_adres`, `uk_housing`).

#### Pijler 4: Het Agentic Case Framework (Dialectisch Agentic Harness)
* **Het mechanisme:** `audit_engine.py` fungeert als tuigage (harness) voor externe AI-modellen via gerichte 'prompts as code'.
* **Strikte Epistemische Rolverdeling:**
  * **Native Grok-4.6 (CLI via grok.com):** Toegerust met *live websearch*. Verifieert geldende wetteksten en jurisprudentie rechtstreeks op overheidsservers (`wetten.overheid.nl`, `rechtspraak.nl`), toetst institutionele machtsdynamiek en bewaakt 'The Velvet Glove' (hoffelijk, ontwapenend, onwrikbaar).
  * **DeepSeek (API):** *Statisch parametrisch model zonder zoekfunctie*. Wordt **nooit** gebruikt als gezaghebbende bron voor actuele wetgeving of feiten (vanwege risico op hallucinaties), maar fungeert uitsluitend als *advocaat van de duivel*: genadeloze formele logica, interne consistentietoetsing en het opsporen van procedurele mazen en drogredenen.
  * **Dialectische Synthese:** Grok toetst DeepSeek op feiten en actuele wetten; DeepSeek toetst Grok op formele logica. De synthese levert een direct verzendbare, juridisch onaantastbare brief op.

---

## 2. De Cybernetische Architectuur: 3 Klokken & 5 Rigoureuze Lagen

> **Volledige specificatie:** Zie [CYBERNETISCHE_ARCHITECTUUR.md](file:///E:/LLM_Workspace/Civic_Case_Engine/CYBERNETISCHE_ARCHITECTUUR.md) en [NON_LINEAIRE_ANALYSE_EN_CONSTRAINT_TOPOLOGIE.md](file:///E:/LLM_Workspace/Civic_Case_Engine/NON_LINEAIRE_ANALYSE_EN_CONSTRAINT_TOPOLOGIE.md) (wiskundige en epistemische fundering via CT v1/v2).

Een lokale agent is geen brievenschrijver, maar een **externe executieve lus** die drie ontkoppelde klokken waarneemt en synchroniseert:
* **$\omega_c$ (Cliëntklok):** Leefwereld, lichaam, zorggat. Continue biologische tijd die niet kan pauzeren.
* **$\omega_w$ (Protocolklok):** Systeemwereld, zaaksystemen (Gws4all, Socrates), ambtelijke batches en productcodes. Neigt tot trage passieve relaxatie.
* **$\omega_*$ (Procedurele Klok):** De discrete, wederzijds getuigde flank (Awb-dwangsommen, AVG 30-dagen termijn, Zivver-logs, griffie-registratie). Dwingt $\omega_w$ mathematisch tot aansluiting op $\omega_c$.

### De Drie-Kamer-Architectuur (Methodologische Rolverdeling)
* **Kamer 1 (Fundering):** Axiomatische en juridische bodem (Awb, Wmo, AVG, Constraint Topologie). Waarborgt 100% sluitendheid.
* **Kamer 2 (Machinekamer):** Civic Legal Kernel & Agentic Harness. Berekent de wrijving ($D, D_t$), bewaakt de termijnen en vangt de slip op van Aristoteles' wielenparadox ($B > C$) via software-redundantie ($R > 0$).
* **Kamer 3 (Uitkamer / Cockpit):** Doelbewust verlieslijdende reductie. Prikkelarm actieplan voor de burger (slechts noodzakelijke handelingen). Bij institutionele blokkade ontgrendelt automatisch het **escalatiepad** naar Kamer 2.

### De Vijf Lagen (L0 – L4)
1. **L0 — Cliënttoestand ($\omega_c$):** Medische en existentiële feiten (NAH, zorgketen). Strikt *interne context*, lekt niet standaard naar uitgaande stukken.
2. **L1 — Landschap van Entiteiten:** Functionele slots, geen individuele karakters. Functie, wettelijk mandaat, vast vs flex, actieve zaaksystemen en ambtelijke `ingest-capaciteit` $\subseteq$ `{productcodes, termijnen, keten, klinisch, privacy}`. CV dient uitsluitend als bandbreedte-filter.
3. **L2 — Discours (optioneel, getriggerd):** Default UIT. Alleen actief bij een formele institutionele claim ("ons zelfreinigend vermogen werkt"). Relais naar griffie/fracties.
4. **L3 — Klokken ($\omega_*$):** Wettelijke termijnen, formele $t=0$, driftbewaking (telefoon = drift $\to$ dwingt direct schriftelijke bevestiging af). Eén actieve klok per conflictlijn.
5. **L4 — Actie & Inhibitie (De Dispatcher):** Bepaalt stuk, slot en toon.
   $$\mathbf{Crisiscommit} \oplus \mathbf{Saaie\ Sonde}$$
   *(Strikt exclusieve disjunctie: Crisiscommit XOR Saaie Sonde. Nooit beide in hetzelfde stuk).*

---

## 3. Directory-Structuur

```text
Civic_Case_Engine/
├── START.cmd                  # Centraal interactief opstartmenu (8 keuzen)
├── SWITCH_DOMAIN.cmd          # Modulair wisselen tussen juridische rechtsgebieden
├── AUDIT_DRAFT.cmd            # Een-klik dialectische multi-model audit
├── WEAVE_TIMELINE.cmd         # Forensische tijdlijn- en bewijs-weaver
├── CHECK_TERMIJNEN.cmd        # Termijnen-, dwangsommen- en AVG-statemachine
├── AUDIT_BANK_CSV.cmd         # Forensische bankmutatie- en huurscanner
├── EXPORT_BUNDEL.cmd          # Procesbundel exporteren met SHA-256 register
├── DOCTRINE.md                # Actief geladen juridische doctrine
├── ONTWIKKELPLAN_CIVIC_EXOSKELETON.md # Het master ontwikkelplan
├── README.md                  # Dit architectuurdocument
│
├── _engine/                   # De Civic Legal Kernel & Agentic Harness
│   ├── audit_engine.py        # Multi-model dialectic auditor (DeepSeek + Grok)
│   ├── case_bundler.py        # Procesdossier bundler (MD + Print HTML)
│   ├── statutory_clock.py     # Termijnen- en Awb-dwangsommen tracker
│   ├── timeline_weaver.py     # Forensische chronologie & hash weaver
│   ├── bank_audit.py          # Financiële bronheffingsscanner
│   └── domain_packs/          # Modulaire rechtsdomeinen (ECLI & wetsartikelen)
│       ├── nl_wmo/            # Wmo 2015, compensatieplicht, urennorm
│       ├── nl_schulden_oninbaar/ # Vbvv, beslagverbod art. 448 Rv, WIK
│       ├── nl_uwv/            # FML-deconstructie, duurbelastbaarheid, art. 9 PW
│       ├── nl_toeslagen/      # Evenredigheid, matiging art. 13b Awir
│       ├── nl_brp_adres/      # Art. 2.23 Wet BRP, VOW-bestrijding
│       └── uk_housing/        # Equality Act 2010, Housing Act 1996 Part VII
│
├── Dossier/                   # Gekoppelde casus-data en chronologie
│   ├── 00_Master_Chronologie.md / .json
│   ├── 01_Zorg_en_Gezondheid.md tot 12_Vergunningen_en_Toezicht.md
│   └── termijnen.json
│
├── Probes/                    # Scherpe wettelijke uitvraag-mallen (AVG / Awb)
├── Incoming_Letters/          # Ontvangen correspondentie van instanties
├── Outgoing_Drafts/           # Uitgaande concepten, audits en verfijnde brieven
└── Landschap/                 # Institutionele machtskaart (Keten, Politiek)
```

---

## 4. Hoe te Gebruiken

1. Start het centrale menu: dubbelklik op `START.cmd`.
2. Selecteer het gewenste domein via `[6] SWITCH_DOMAIN.cmd` (bijv. Wmo, Schulden, UWV of UK Housing).
3. Drop inkomende documenten in `Incoming_Letters/` of plaats een concept in `Outgoing_Drafts/`.
4. Draai een audit via `[1] AUDIT_DRAFT.cmd`: het Agentic Harness roept DeepSeek en Grok aan, toetst tegen de actieve doctrine en levert een kant-en-klaar verbeterd concept op.
5. Bewaak de wettelijke klok via `[3] CHECK_TERMIJNEN.cmd`.
6. Genereer een complete, geverifieerde procesbundel voor rechtbank of ombudsman via `[5] EXPORT_BUNDEL.cmd`.
