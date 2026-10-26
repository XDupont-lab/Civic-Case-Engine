# Agentische Werkomgeving Basisadministratie (AWB)

[English](README.en.md)

> **Definitie.** Agentische Werkomgeving Basisadministratie. Het ketengrootboek staat in het midden. Geld wordt twee keer geboekt, een overdracht één keer, en die post blijft open tot de andere kant tegenboekt.

De werkomgeving houdt één beeld bij over zorg, loket en geld. Zij draait op de computer van de persoon. Het dossier, de brieven en de namen blijven buiten git. De persoon leest een brief en geeft het sein. Zolang een gesprek met een lokaal loket open is, gaat er geen ingebrekestelling weg en noemt het programma geen dwangsom.

De maat voor de bouw staat in [APPLICATIE_SPECIFICATIE.md](APPLICATIE_SPECIFICATIE.md). Het venster heet Civic Helper. De repository heet nog `Civic-Case-Engine`.

Wat hieronder staat is de architectuurnotitie. De definitie hierboven is de deur.

---

## Begin

1. Clone de repository en ga de map in.
   ```bash
   git clone https://github.com/XDupont-lab/Civic-Case-Engine.git
   cd Civic-Case-Engine
   ```
2. Op Windows opent `CivicHelper.cmd` het venster. Op Linux opent `hulp/start_venster.sh` hetzelfde venster.
3. Een schone computer begint bij `ontkiem.py`. Eén gewoon mailadres is genoeg om te starten. Een sleutel blijft in de omgeving. Het venster vraagt er niet om.
4. `START.cmd` en `start_linux.sh` zijn het menu voor de bouwer. Dat menu is niet de deur.

Of een overdracht sluit, toetst `Ketengrootboek/sluiting.py` aan de hand van de drie boeken van Simon Stevin (Memoriaal, Journaal, Grootboek) en drie afzonderlijke sluitingskenmerken (*rekenkundig sluitend*, *procedureel gesloten*, *materieel vereffend*). De operationele gids voor agenten staat in [`Ketengrootboek/AGENTS.md`](Ketengrootboek/AGENTS.md). Ontbreekt de materiële tegenboeking, dan blijft de post open. Het openbare voorbeeld heet Voorbeeldstad. Een pad naar een eigen dossier hoort niet in `interfaces.json`.

---

## 1. De Conceptuele Taxonomie: Twee Dimensies

Om categoriefouten te voorkomen, ontkoppelt de architectuur het maatschappelijke doel van de technische machinekamer. Het systeem kent twee complementaire dimensies:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ A. FUNCTIONEEL-FILOSOFISCHE DIMENSIE (Het 'Waarom' en 'Voor Wie')           │
├─────────────────────────────────────────────────────────────────────────────┤
│ 1. MAATSCHAPPELIJK / STRATEGISCH: CIVIC HELPER                              │
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

#### Pijler 1: Het CIVIC HELPER (Burgerlijk Civic Helper)
* **Het probleem:** Instanties bezitten oneindige ambtelijke tijd, geautomatiseerde incassosystemen en juridische afdelingen. De burger heeft slechts één biologisch zenuwstelsel en beperkte reserves.
* **De werking:** Civic Helper heft de structurele informatie-asymmetrie op. Met formele sondes (art. 15 AVG, art. 3:2 Awb) wordt de instantie gedwongen binnen fatale termijnen (30 dagen) zelf in haar archieven te spitten en haar wettelijke onderzoeks- en motiveringsplicht na te komen.

#### Pijler 2: Externe Executieve Functie (Cognitieve Prothese)
* **Het probleem:** Chronische ziekte, NAH of acute bestaansonzekerheid leiden tot executieve dysfunctie onder stress (moeite met plannen, prioritering, telefoongesprekken en emotionele overbelasting).
* **De werking:** Het fungeert als een cognitieve prothese. Alle communicatie wordt gedwongen tot schriftelijkheid ("The Velvet Glove"), emotionele valkuilen worden geneutraliseerd en termijnen worden extern bewaakt.

### B. De Technisch-Operationele Dimensie

#### Pijler 3: De Civic Legal Kernel (Deterministische Machinekamer)
* **Het fundament:** 100% Python 3 standaardbibliotheek, zero-dependency, lokaal agentisch. Geen probabilistische gissingen over fatale termijnen of integriteit.
* **Kernmodules (`_engine/`):**
  * `statutory_clock.py`: Wiskundige Awb-, Wmo-, AVG- en Woo-termijnenbewaker. De klok noemt het gat. De ingebrekestelling en het dwangsombedrag blijven in de achterzak zolang het gesprek open is.
  * `timeline_weaver.py`: Forensische parser voor bank-CSV's, WhatsApp-logs, call-logs en e-mails met automatische SHA-256 verificatie en zorgbreukdetectie.
  * `case_bundler.py`: Assembleert alle producties, chronologie en doctrine tot een rechtbank- en ombudsmanklare procesbundel (.md en printklare HTML).
  * `domain_packs/`: Modulaire juridische drivers (`nl_wmo`, `nl_schulden_oninbaar`, `nl_uwv`, `nl_toeslagen`, `nl_brp_adres`, `uk_housing`).

#### Pijler 4: Het Agentic Case Framework (Dialectisch Agentic Harness)
* **Het mechanisme:** `audit_engine.py` en de Tafel (`TAFEL.md`) fungeren als tuigage (harness) voor een multi-agent ensemble via gerichte 'prompts as code'.
* **Strikte Epistemische Rolverdeling:**
  * **Native Grok-4.6 (CLI via grok.com):** Toegerust met *live websearch*. Verifieert geldende wetteksten en jurisprudentie rechtstreeks op overheidsservers (`wetten.overheid.nl`, `rechtspraak.nl`), toetst institutionele machtsdynamiek en bewaakt 'The Velvet Glove' (hoffelijk, ontwapenend, onwrikbaar).
  * **DeepSeek (API):** *Statisch parametrisch model zonder zoekfunctie*. Wordt **nooit** gebruikt als gezaghebbende bron voor actuele wetgeving of feiten (vanwege risico op hallucinaties), maar fungeert uitsluitend als *advocaat van de duivel*: genadeloze formele logica, interne consistentietoetsing en het opsporen van procedurele mazen en drogredenen.
  * **Google Antigravity (agy CLI):** Autonoom dossier- en code-agent voor deterministische verificaties, bestandsoperaties, tools, scratch/outboxbeheer en tests. Start direct op met het commando `agy`.
  * **Dialectische Synthese:** Grok toetst DeepSeek op feiten en actuele wetten. DeepSeek toetst Grok op formele logica. Agy voert deterministische verificaties en code-taken uit. De synthese zet een concept klaar. De persoon leest het en geeft het sein. Een brief aan een lokaal Nederlands loket blijft kort.

---

## 2. De Cybernetische Architectuur: 3 Klokken & 5 Rigoureuze Lagen

> **Volledige specificatie:** Zie [CYBERNETISCHE_ARCHITECTUUR.md](CYBERNETISCHE_ARCHITECTUUR.md) en [NON_LINEAIRE_ANALYSE_EN_CONSTRAINT_TOPOLOGIE.md](NON_LINEAIRE_ANALYSE_EN_CONSTRAINT_TOPOLOGIE.md) (wiskundige en epistemische fundering via CT v1/v2).

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
Civic_Helper/
├── START.cmd                  # Centraal interactief opstartmenu (8 keuzen)
├── SWITCH_DOMAIN.cmd          # Modulair wisselen tussen juridische rechtsgebieden
├── AUDIT_DRAFT.cmd            # Een-klik dialectische multi-model audit
├── WEAVE_TIMELINE.cmd         # Forensische tijdlijn- en bewijs-weaver
├── CHECK_TERMIJNEN.cmd        # Termijnen-, dwangsommen- en AVG-statemachine
├── AUDIT_BANK_CSV.cmd         # Forensische bankmutatie- en huurscanner
├── EXPORT_BUNDEL.cmd          # Procesbundel exporteren met SHA-256 register
├── DOCTRINE.md                # Actief geladen juridische doctrine
├── INTERACTIONAL_STATE_AND_OPERATOR_DISPATCH.md # v2.0 Interactionele toestand & Operator Dispatch (S_case & WAIT)
├── ONTWIKKELPLAN_CIVIC_HELPER.md # Het master ontwikkelplan
├── README.md                  # Deze deur, in het Nederlands
├── README.en.md               # Dezelfde deur, in het Engels
├── APPLICATIE_SPECIFICATIE.md # De maat voor de bouw
├── CivicHelper.cmd            # Opent het venster op Windows
├── ontkiem.py                 # Eerste start op een schone computer
├── Ketengrootboek/            # Tegenboeking en proefbalans
├── gui/                       # Civic Helper 0.3 — Multi-Agent Tafelvenster (PyQt6)
│   ├── tafel_gui.py           # Native desktopvenster met actieve Tafel, stoelen en klok
│   ├── tafel_indexer.py       # Forensische beurten- en stok-indexering (zero-pip)
│   ├── tafel_archiver.py      # Rolling archivering (max. 20 actieve beurten)
│   ├── tafel_chat.py          # Multi-agent dispatch daemon (Grok, agy, DeepSeek)
│   ├── tafel_search.py        # Razendsnelle non-RAG beraadslagingen-zoekmachine
│   ├── tafel_relation_engine.py # Causale trace en gap-analyse (delta > 0)
│   ├── model_bus.py           # Eén deur naar modelhuizen met lokale PII-kluis
│   └── pii_mask.py            # Deterministische maskering van BSN/IBAN/adres
├── hulp/                      # Klassiek navigatiescherm (venster.py, lus.py)
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
├── Dossier/                   # Voorbeeldbladen. De zaak van de persoon staat in werk/ en gaat niet naar git
│   ├── 00_Master_Chronologie.md / .json
│   ├── 01_Zorg_en_Gezondheid.md tot 12_Vergunningen_en_Toezicht.md
│   └── termijnen.json
│
├── Probes/                    # Scherpe wettelijke uitvraag-mallen (AVG / Awb)
├── Incoming_Letters/          # Leeg in git. Binnengekomen post blijft lokaal
├── Outgoing_Drafts/           # Leeg in git. Concepten blijven lokaal tot het sein
└── Landschap/                 # Institutionele machtskaart (Keten, Politiek)
```

---

## 4. Hoe te gebruiken

De deur staat hierboven, onder Begin. `START.cmd` blijft het menu voor wie aan de motor bouwt.

Een brief gaat pas weg nadat de persoon de tekst heeft gelezen en het sein heeft gegeven. De toets of de andere kant de overdracht heeft ingeboekt, is het ketengrootboek. Twee groene balies zonder tegenboeking zijn nog geen sluiting.
