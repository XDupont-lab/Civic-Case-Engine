# 🔍 ZOEKMETHODEN NOTITIE: RELATIES & INTERFACES BOVEN WOORDEN
### De Non-RAG Constraint Zoeker voor Complexe Dossiers & Ketenreconstructie

**Geldig vanaf:** 9 oktober 2026  
**Status:** Canoniek methodologisch navigatiedocument voor alle CLI-agenten (Agy, Grok, DeepSeek, Claude)  
**Locatie:** [`E:\LLM_Workspace\Civic_Case_Engine\ZOEKMETHODEN_NOTITIE_NON_RAG_RELATIES.md`](file:///E:/LLM_Workspace/Civic_Case_Engine/ZOEKMETHODEN_NOTITIE_NON_RAG_RELATIES.md)  
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

### A. De Interface Registry (`Civic_Case_Engine/interfaces.json`)
Hierin liggen alle geverifieerde interfaces tussen zorg, wonen, geld en recht vastgelegd:
* `IF-WONEN-WMO-001`: Overdracht leefbaarheidssignaal verhuurder naar Wmo.
* `IF-CAK-SOZAWE-002`: Beslagvrije voet en bronheffing CAK vs Participatiewet.
* `IF-MED-TRAUMA-OOG-004`: Causale schokgolf van AZG 1999 (hamertrauma) naar UMCG 2020 (lensluxatie OD), bevestigd door oogartsen Van Arnhem en Bult-Wasmann.
* `IF-MED-WASSIEE-GATE-005`: Institutionele poortweigering Dr. Wassiee (2018) met achterlating van diagnostisch residu `N80.00 status na hoofdletsel`.
* `IF-MED-SEPSIS-OVERDRACHT-006`: Pacioli-breuk tussen IC-ontslag Martini (mei 2016) en ontbreken van wijkverpleging/stoma-opvang.
* `IF-MED-INFLAM-NEURO-007`: 13-jarige bloedspiegel (leukocyten 10.3–16.7, lymfo's 7.3) als gesloten neuro-inflammatoire lus (*Sickness Behavior*).

### B. De Deterministische Relatie-Toetser (`glue_check.py`)
Toetst of een relatie juridisch en klinisch sluit:
```powershell
# Eén specifieke relatie toetsen:
python E:\LLM_Workspace\Civic_Case_Engine\_engine\glue_check.py IF-MED-TRAUMA-OOG-004

# Alle interfaces integraal toetsen:
python E:\LLM_Workspace\Civic_Case_Engine\_engine\glue_check.py ALL
```

### C. Het Ketengrootboek & Sluiting (`sluiting.py`)
Toetst de boekhoudkundige pariteit van de verzorgingsstaat (Debet = Credit):
```powershell
python E:\LLM_Workspace\Civic_Case_Engine\Ketengrootboek\sluiting.py ALL
```

---

## 4. Werkprotocol voor CLI-Agenten (Agy, Grok, DeepSeek, Claude)

Wanneer een vraag van de gebruiker binnenkomt over de geschiedenis, de medische stand of een instantie:

1. **VERBODEN:** Ga niet blindelings `grep -i <woord>` of `search_rag` draaien om losse alinea's tekst op te lepelen.
2. **STAP 1 — Identificeer de Relatie:**  
   Welke twee domeinen botsen hier? Wie was de zendende partij ($P_{\text{bron}}$)? Wie was de ontvangende partij ($P_{\text{doel}}$)? Wat was de materiële overdracht?
3. **STAP 2 — Zoek de Poort & het Residu:**  
   Heeft de ontvangende partij de overdracht formeel aanvaard? Zo nee, welk residu $\delta$ is er in de dossiers achtergebleven? (Bijv: een weigering van een neuroloog die wél resulteert in een ICPC-code `N80.00`).
4. **STAP 3 — Raadpleeg & Verrijk `interfaces.json`:**  
   Kijk of de relatie al gedefinieerd is in `interfaces.json`. Zo nee, voeg de nieuwe causale pijl toe met een SHA-256 brongetuige.
5. **STAP 4 — Construeer het Bewijs:**  
   Presenteer de bevinding aan Xander of de behandelend arts niet als een meningsuiting, maar als een **gesloten causale keten**.

Dit garandeert dat elke AI-agent die in deze workspace opereert direct overschakelt van *tekst-nabootser* naar *forensisch systeem-analist*.
