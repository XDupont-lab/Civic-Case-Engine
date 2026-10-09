# Interactional State Architecture & Operator Dispatch (Civic Case Engine v2.0)

> **Kernaxioma:** Een civiele agent is geen documentvalidator en geen brievenschrijver. Hij modelleert en moduleert de **interactionele toestand** tussen institutionele actoren over vier discrete verdiepingen, en voorkomt vroegtijdige reductie van de toestandsruimte.

**Datum:** 7 oktober 2026  
**Status:** Normatieve Architectuurspecificatie voor de Civic Case Engine Harness & Dialectische Auditoren  
**Referentie:** Casus Dupont vs. Sociaal Team Oost (Lennart Top / Concept 51), CAK, Menzis, LAVG, Midwerk  

---

## 1. De Tripartite Toestandsvector ($\mathcal{S}_{\text{case}}$)

Klassieke agentische architecturen (waaronder Grok Build en standaard legal-LLM's) begaan een fundamentele ontwerpfout: zij modelleren een dossier als een **eendimensionale, deterministische documentvalidatie**:
$$\text{input} \longrightarrow \text{interpretatie} \longrightarrow \text{canonieke versie} \longrightarrow \text{inconsistenties opsporen} \longrightarrow \text{reparatie} \longrightarrow \text{verzenden}$$

Zodra er een wet, verjaringstermijn of termijnoverschrijding wordt gedetecteerd, dwingt het model een binaire sluiting af (*"legaliseer alles, sluit de status, eis een beschikking"*).

In de Civic Case Engine v2.0 wordt de toestand van een dossier gemodelleerd als een **tripartite vector**:

$$\mathcal{S}_{\text{case}} = \begin{pmatrix} \mathbf{L} & \text{(Legal State)} \\ \mathbf{F} & \text{(Factual State)} \\ \mathbf{I} & \text{(Interactional State)} \end{pmatrix}$$

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. LEGAL STATE (L) — Deterministisch & Formeel (De Civic Legal Kernel)     │
│    Wettelijke termijnen (Awb 4:13/4:17, AVG 12 lid 3), besluitstatussen,    │
│    formele aanspraken, dwangsomklokken, procesbundels, sha256-bewijshashes.  │
├─────────────────────────────────────────────────────────────────────────────┤
│ 2. FACTUAL STATE (F) — Epistemisch Register (Het Ketengrootboek)            │
│    Feitenconstellatie: Vaststaand, Gerapporteerd, Betwist, Onbekend.        │
│    Decompositie van vorderingen, posten en medische gebeurtenissen.         │
├─────────────────────────────────────────────────────────────────────────────┤
│ 3. INTERACTIONAL STATE (I) — Dialectisch & Relationeel (Het Agentic Harness)│
│    Actor-identiteit, Institutionele Verdieping (Floor), Open Gesprek,       │
│    Lopende Interne Afstemming, Laatste Menselijke Toezegging,               │
│    Verwachte Volgende Zet, Escalatietemperatuur (Warm ↔ Bevroren).          │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Het Gouden Invariant van de Toestandsruimte:
> **Onzekerheid $\neq$ Fout.**  
> In een bestuurlijke relatie is een uitspraak als *"Ik moet dit nog met mijn collega bespreken"* geen ontbrekende specificatie die moet worden geëlimineerd, maar **actuele, waardevolle informatie over de toestand van de relatie**. De agent moet deze toestand *conserveren*, niet platwalsen.

---

## 2. De Vier Institutionele Verdiepingen (Interactionele Regimes)

De Civic Case Engine erkent dat "de overheid" niet bestaat als één generieke ontvanger. Dezelfde burgerlijke feiten vereisen op verschillende institutionele schalen een fundamenteel ander interactieregime:

| Verdieping (Floor) | Domein & Doelwitten | Primaire Dynamiek | Toelaatbaar Instrumentarium | Fataal Risico bij LLM-Overkill |
| :--- | :--- | :--- | :--- | :--- |
| **I. Lokaal & Ruraal** | Sociaal Team Oost, Wmo-consulent, Gebiedsregisseur | Keukentafelgesprek, collegiale loyaliteit, handelingsverlegenheid bij multimorbiditeit. De mens aan de telefoon is het reddende kanaal. | Open vraag, persoonlijke spiegeling, beleidsnotitie als hulpmiddel, informeel meedenken. | Formele brieven met Awb-dwangsommen dwingen het team in de kramp $\to$ dossier naar Juridische Zaken $\to$ zorg bevriest. |
| **II. Regionaal Zorg** | Syncope, Huisarts, UMCG Beatrixoord, MEE Noord | Praktische zorgcontinuïteit, medische triage, intercollegiaal overleg. | Korte zakelijke afstemming (3 regels), verwijsbrieven, feitelijke beschikbaarheid. | Bestuursrechtelijke betogen verstoren de zorgrelatie en wekken wantrouwen bij behandelaars. |
| **III. Landelijk Publiek** | CAK, Menzis, BKR, Belastingdienst, FG-loketten | Onpersoonlijke zaaksystemen, wettelijke termijnen, privacy-balies. | Art. 15 AVG inzage, formele stuiting, DigiD/ID-verificatie. Eerst eenvoudige vraag, termijn in de achterzak. | Direct citeren van EVRM of Hoge Raad in openingsmail leidt tot opschaling naar speciale dossiers/juristen. |
| **IV. Incasso & Executie** | LAVG, Flanderijn, Gerechtsdeurwaarders | Vorderingen, titel-onderzoek, verjaring, kostenstaffel (WIK). | Pure dossieropvraag (art. 15 AVG) zonder schulderkenning (art. 3:318 BW), specificatie-eisen. | Voortijdige betalingsvoorstellen of schulderkenning heropenen verjaarde vorderingen. |

---

## 3. De Operator Dispatch ($\Omega$): Het Vierkants-Model

In plaats van de blinde drang van generatieve AI om bij elke beurt tekst te produceren (*"Prompt $\implies$ Schrijf brief"*), beschikt het Harness van de Civic Case Engine over een discrete viervoudige operator-set $\Omega$:

$$\Omega = \{\mathbf{ASK}, \; \mathbf{CONFIRM}, \; \mathbf{WAIT}, \; \mathbf{ESCALATE}\}$$

```
                           [ Evaluatie van S_case ]
                                       │
                  ┌────────────────────┼────────────────────┐
                  ▼                    ▼                    ▼
               [ ASK ]            [ CONFIRM ]            [ WAIT ]
         Informatie ontbreekt   Relatie loopt /      Andere actor heeft
          of specificatie nodig  toezegging gedaan    open toezegging
                                                            │
                                                            │ Grens bereikt /
                                                            │ Front gesloten
                                                            ▼
                                                       [ ESCALATE ]
                                                  Juridische Kernel aan:
                                                  Awb, Dwangsom, Dagvaarding
```

### 1. `ASK` (De Open Vraag)
- **Conditie:** Feiten ontbreken in het Ketengrootboek ($\mathbf{F}$ is incompleet) of bevoegdheid is onduidelijk.
- **Actie:** Korte, gerichte vraag zonder juridische dreigementen. Ruimte laten voor antwoord.

### 2. `CONFIRM` (De Relationele Spiegel)
- **Conditie:** Mondeling contact heeft plaatsgevonden, relatietemperatuur is werkbaar/coöperatief.
- **Actie:** Een warm, menselijk bericht dat het besprokene samenvat in de vragende vorm (*"Zeg het als ik dit te ruim zie"*). Geen dwingende stipulations, geen CC aan collega's met wie nog overlegd moet worden.

### 3. `WAIT` (De Strategische Rust — Heilige Invariant)
- **Conditie:** De andere actor heeft de actieve zet (bijv. leidinggevende stemt intern af, huisbezoek staat gepland, termijn loopt nog).
- **Formele Representatie:**
  ```json
  {
    "action": "WAIT",
    "reason": "OTHER_ACTOR_HAS_OPEN_COMMITMENT",
    "target_actor": "Lennart Top (Sociaal Team Oost)",
    "legal_risk": "LOW",
    "relational_risk_if_escalated": "CRITICAL",
    "timeout": "2026-10-09T17:00:00"
  }
  ```
- **Betekenis:** Geen brief sturen is een **actieve, gevalideerde systeemkeuze**. Het voorkomt dat het model de toestand verstoort.

### 4. `ESCALATE` (Het Juridische Schild)
- **Conditie:** De procedurele termijn is fataal verstreken én de interactionele voorkant is formeel/feitelijk gesloten (geen reactie, weigering van zorg, onrechtmatige incasso).
- **Actie:** De Civic Legal Kernel activeert de harde procedurele instrumenten: formele ingebrekestelling (art. 4:17 Awb), klacht bij de Autoriteit Persoonsgegevens, dagvaarding of verzoekschrift.

---

## 4. De Poortwachter voor Juridisering (The Law Gating Invariant)

De meest cruciale wet van de Civic Case Engine is de ontkoppeling tussen de detectie van een rechtsgrond en de activatie van juridische actie:

$$\text{Law Detected} \centernot\implies \text{Activate Legal Protocol}$$

$$\text{Law Detected} \land (\mathbf{I}.\text{front\_status} == \text{CLOSED}) \implies \text{Activate Legal Protocol}$$

### Niet-Monotone Kwaliteitsfunctie
In code-ontwikkeling is kwaliteit monotoon stijgend met specificatie. In burger-bureaucratie interacties is de kwaliteitsfunctie $Q(m)$ over een bericht $m$ **strikt niet-monotoon**:

$$Q(m) = f(\text{Relevantie}) - \alpha \cdot \mathbb{I}(\text{Juridische Overkill}) \cdot \text{Relatieschade}$$

- **Te weinig informatie:** $Q(m) < 0$ (onduidelijk, niet-handelbaar).
- **Optimaal (Het Fluwelen Middenpad):** $Q(m) = \max$ (concrete vraag/spiegeling, ademruimte voor de ambtenaar, wet in de achterzak).
- **Juridische audit-overkill:** $Q(m) \ll 0$ (Awb-artikelen, termijnen, dreigementen $\implies$ ontvanger verliest handelingsbekwaamheid $\implies$ juridische bevriezing).

---

## 5. Constraint-Topologische Grondslag: Vroegtijdige Toestandsruimtereductie

In termen van **Constraint Topologie (CT)** en de **Schaal-als-Constraint-Topologie (SCT)**:

1. **Admissibility is primitief:** Een brief die door drie LLM-audits komt als *"hermetisch, foutloos en verzendklaar"* is wiskundig en syntactisch **composable**. Maar op Verdieping I (lokaal sociaal team) is die brief sociaal en relationeel **inadmissible** omdat hij de lokale sluiting opblaast.
2. **Data Processing Inequality (DPI) op de interactie:** Zodra een auditor de open toestand forceert tot één binaire juridische eis, vindt er een onomkeerbare projectie plaats. De functionele informatie over de relatie wordt vernietigd:
   $$I(\text{Toekomstige Zorg}; \text{Open Dialoog}) > I(\text{Toekomstige Zorg}; \text{Geforceerd Processtuk})$$
3. **Het Tussenobject (Artifact):** Het Agentic Case Framework dwingt te allen tijde af dat concepten als **boundary objects** buiten de automatische verzendcyclus blijven. De mens in de lus toetst of de interactionele toestand $\mathbf{I}$ gerespecteerd wordt vóórdat een transitie plaatsvindt.

---

## 6. Implementatie in de Repository

Deze specificatie legt het formele fundament voor de implementatie in:
- `_engine/case_state_machine.py` (De tripartite toestand $\mathcal{S}_{\text{case}}$);
- `_engine/operator_dispatch.py` (De dispatch $\Omega$ met `WAIT` als first-class citizen);
- `_engine/floor_registry.py` (De 4 interactionele verdiepingen en hun filterregels);
- `_engine/veto_gate.py` (De blokkade op premature juridisering).
