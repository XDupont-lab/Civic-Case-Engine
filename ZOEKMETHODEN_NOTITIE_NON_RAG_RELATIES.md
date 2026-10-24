# 🔍 ZOEKMETHODEN NOTITIE: RELATIES & INTERFACES BOVEN WOORDEN

### De Non-RAG Constraint Zoeker voor Complexe Dossiers & Ketenreconstructie



**Geldig vanaf:** 9 oktober 2026  

**Status:** Canoniek methodologisch navigatiedocument voor alle CLI-agenten (Agy, Grok, DeepSeek, Claude)  

**Locatie:** [`ZOEKMETHODEN_NOTITIE_NON_RAG_RELATIES.md`](ZOEKMETHODEN_NOTITIE_NON_RAG_RELATIES.md)  

**Theoretisch Fundament:** Constraint Topologie v1.0 / v2.0, Luhmanniaanse Operationele Geslotenheid, Dubbele Boekhouding (Ketengrootboek)



---



## 1. Het Fundamentele Probleem van Klassieke RAG & Woordzoekers



Wanneer een AI-agent een medisch, juridisch of gemeentelijk dossier benadert met klassieke **RAG (Retrieval-Augmented Generation)** of semantische vector-databases, begaat hij een categoriefout:



1. **Woorden als Objecten:** RAG hakt honderden pagina's PDF in willekeurige brokken (chunks van 500 tokens) en berekent vector-afstanden tussen losse woorden.

2. **De Illusie van Verbinding:** Als op pagina 10 het woord *"stoma"* staat en op pagina 80 *"schulden"*, ziet een vector-zoeker een associatie, maar begrijpt niets van de richting, de institutionele actor of de causale wetmatigheid.

3. **De Onzichtbaarheid van de Ketenbreuk:** Bij een ambtelijk verzuim of medische zorgval is het doorslaggevende bewijs juist **wat er NIET staat** (een geweigerde indicatie, een ontbrekende overdracht, een genegeerd verzoek). RAG en woordzoekers kunnen een afwezigheid per definitie niet ophalen.



---



## 2. Het Axioma: `Same Entity ≠ Same Constraint`



In onze methodologie geldt het ijzeren principe:

> **De vermelding van dezelfde entiteit (naam, BSN, adres of losse medische term) creëert GEEN verbinding.**  

> Alleen een **directe causale overdracht in toelaatbaarheid** tussen twee begrensde domeinen vormt een gerichte pijl ($f_{ij}: P_i \to P_j$).



Een dossier is geen wolk van woorden, maar een **gerichte graaf van interfaces**:

* **Domeinen (Patches $P_i$):** Hermetisch gescheiden institutionele of biologische eilanden (SEH Ziekenhuis, Huisartsenpraktijk, Sociaal Team Wmo, Participatiewet, Centraal Zenuwstelsel).

* **De Relatie ($f_{ij}$):** De formele handeling of fysiologische overdracht van $P_i$ naar $P_j$.

* **De Gedeelde Drager:** Het onveranderlijke feit dat getransporteerd moet worden (bijv. hygiënische overleving, zonulaire oogintegriteit, arbeidsongeschiktheid).

* **De Poort (Gate):** De wettelijke of fysiologische toelatingsconditie.

* **Het Residu ($\delta$):**

  - $\delta = 0 \to$ **ADMISSIBLE (Sluiting):** Zender boekt af (Debet), ontvanger boekt in (Credit), zorg of recht loopt door.

  - $\delta > 0 \to$ **GLUING FAILURE (Ketenbreuk):** Poort weigert, tegenboeking ontbreekt, de burger valt in het vacuüm.



---



## 3. De Instrumenten van de Non-RAG Zoeker in Deze Workspace



Elke agent beschikt in deze workspace over deterministische code om relaties te analyseren in plaats van woorden te raden:



### A. De Interface Registry (`Civic_Helper/interfaces.json`)

Hierin liggen alle getypeerde interfaces tussen zorg, wonen, geld en recht vastgelegd (in het openbare model: Voorbeeldstad):

* `IF-WONEN-WMO-001`: Noodsignaal woningcorporatie naar Wmo/sociaal wijkteam bij acute verloedering van de woonsituatie.

* `IF-CAK-SOZAWE-002`: Bestuursrechtelijke bronheffing wanbetalerspremie vs. toetsing Participatiewet (vrijwaring beslagvrije voet).

* `IF-WMO-LEEFBAARHEID-003`: Compensatieplicht leefbare woonruimte (Wmo art. 2.3.5) vs. signalering huurderzorg.

* `IF-ZORG-OVERDRACHT-004`: Ontslagoverdracht medisch specialist (tweede lijn) naar eerstelijns huisarts en wijkzorg.

* `IF-INDICATIE-POORT-005`: Formele zorgvraag met poortconditie en achterlating van een administratief of diagnostisch residu.



### B. De Deterministische Relatie-Toetser (`glue_check.py`)

Toetst of een relatie juridisch en procedureel sluit:

```powershell

# Eén specifieke relatie toetsen (bijv. Voorbeeldstad wonen-Wmo):

python _engine/glue_check.py IF-WONEN-WMO-001



# Alle interfaces integraal toetsen:

python _engine/glue_check.py ALL

```



### C. Het Ketengrootboek & Sluiting (`sluiting.py`)

Toetst de boekhoudkundige pariteit van de verzorgingsstaat (Debet = Credit):

```powershell

python Ketengrootboek/sluiting.py ALL

```



### D. De Non-RAG Theorie-Atlas voor het Wetenschappelijke Notion-Corpus (`non_rag_theory_engine.py`)

Voor het lokale theoriecorpus geldt exact hetzelfde verbod op losse woordzoekers en TF-IDF associaties (`Same Word ≠ Same Constraint`). De deterministische theorie-engine stript alle 1.146 oude TF-IDF `Graph Weaver`-links en indexeert elk document als een getypeerde Patch $P_i$ (`SCHONE_CANON`, `CANON_KERN`, `TYPE_A_MATH_TRANSLATION`, `TYPE_B_APPLIED_LENS`, `EXPLORATION_WORKBENCH`, `ARCHIEF_SUPERSEDED`) met gerichte interfaces (`UPSTREAM_ANCHOR`, `LATERAL_BRIDGE`, `DOWNSTREAM_APPLICATION` met *Direction Lock*, `SUPERSEDED_BY`):

```powershell

# Bouw/ververs de Non-RAG Theorie-Atlas (Shared_Tools/theory_atlas_non_rag.json):

python ../Shared_Tools/non_rag_theory_engine.py build



# Toon de Oogst-Radar per 3D+1 domein (zonder Archief- of TF-IDF ruis):

python ../Shared_Tools/non_rag_theory_engine.py harvest-radar



# Inspecteer het Patch-Paspoort, Contract (Π_ref, GU-log, Gate) en de in/uit-pijlen van een stuk:

python ../Shared_Tools/non_rag_theory_engine.py inspect "Kepler"



# Volg de zuivere Non-RAG relatie-keten vanaf een start-patch:

python ../Shared_Tools/non_rag_theory_engine.py trace "Periode-ring" -d 2



# Voer de Direction-Lock & Π/Gate Contract Audit uit op het theorie-corpus:

python ../Shared_Tools/non_rag_theory_engine.py glue-check

```



---



## 4. Werkprotocol voor CLI-Agenten (Agy, Grok, DeepSeek, Claude)



Wanneer een vraag van de gebruiker binnenkomt over de geschiedenis, de medische stand of een instantie:



1. **VERBODEN:** Ga niet blindelings `grep -i <woord>` of `search_rag` draaien om losse alinea's tekst op te lepelen.

2. **STAP 1 — Identificeer de Relatie:**  

   Welke twee domeinen botsen hier? Wie was de zendende partij ($P_{\text{bron}}$)? Wie was de ontvangende partij ($P_{\text{doel}}$)? Wat was de materiële overdracht?

3. **STAP 2 — Zoek de Poort & het Residu:**  

   Heeft de ontvangende partij de overdracht formeel aanvaard? Zo nee, welk residu $\delta$ is er in de registers achtergebleven? (Bijv: een weigering of gebrek aan intake die wél een schriftelijk dossierfeit of wettelijk verzuim achterlaat).

4. **STAP 3 — Raadpleeg & Verrijk `interfaces.json`:**  

   Kijk of de relatie al gedefinieerd is in `interfaces.json`. Zo nee, voeg de nieuwe causale pijl toe met een SHA-256 brongetuige.

5. **STAP 4 — Construeer het Bewijs:**  

   Presenteer de bevinding niet als een meningsuiting of emotioneel narratief, maar als een **gesloten causale keten** met getuigen, poorten en residuen.



Dit garandeert dat elke AI-agent die in deze workspace opereert direct overschakelt van *tekst-nabootser* naar *forensisch systeem-analist*.

