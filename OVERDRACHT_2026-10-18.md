# Overdracht Civic Helper — Bijgewerkt 25 oktober 2026

> **BELANGRIJK VOOR ELKE AGENT (Actuele Stand 25 okt 2026):**
> - **Het actuele venster is `Civic Helper 0.3 — Tafel`** (`E:\LLM_Workspace\Shared_Tools\tafel_gui.py`, gesynchroniseerd met `CivicHelper/gui/tafel_gui.py`). Starten via `CivicHelper.cmd` of `start-tafel.cmd`.
> - **Werk NIET meer aan het oude roomwitte `hulp/venster.py`**; dat was de vroege tussenstap van 18 oktober en is volledig opgegaan in `Civic Helper 0.3 — Tafel` (met de 4 tabbladen `Overzicht | Dossiers | Brieven | Analyse`, de Twee Klokken én het 3-Boekenstelsel van Simon Stevin).
> - **Voor het 3-Boeken-Registratiesysteem (Memoriaal, Journaal, Grootboek):** lees direct **`CivicHelper/Ketengrootboek/AGENTS.md`**.

---

*(Historische notitie van 18 oktober 2026 hieronder bewaard ter referentie)*

Vers scherm: lees dit bestand. Daarna `APPLICATIE_SPECIFICATIE.md`. Bouw niet de hele tabel. De specificatie is de maat. Er is nog geen ontkieming gedraaid.



## Plakblok



We bouwen Civic Helper. De specificatie staat in `CivicHelper/APPLICATIE_SPECIFICATIE.md`. De overdracht van 18 oktober 2026 staat in `CivicHelper/OVERDRACHT_2026-10-18.md`. Het venster is een navigatiescherm, geen chat-terminal. De motor is `agy`, niet een kale modelaanroep. Eén gratis Gmail-adres is genoeg om te starten. De eerste lus is: venster open op `werk/00_Kompas.md`, één brief via veto dan audit dan poort dan sein, binnenkomst op de tijdlijn, één breuk in gewone taal. Een spoor is pas klaar als de overdracht sluit en naar het archief gaat.



## Functie



De zorg, het bestuur en grote bedrijven knippen één mens en één bestaan in stukken. De applicatie herstelt die ketens en relaties. Zij vraagt versplinterde dossiers op, legt ontbrekende overdrachten bloot, en bouwt één beeld over de tijd. Met dat beeld spreekt zij elk loket aan in het interne model van dat loket.



De berg administratie aan de keukentafel is het gevolg, niet de openingszin. Die staat onder `Eigen regie en rust`.



## Vorm



Geen gesloten formulier met vaste zinnen. Het model zoekt op dat moment een oplossing voor het concrete probleem. `agy` is het hart en heeft de handen. Het PyQt-venster is de kaart.



Links een rail: Bureau, Landschap, Dossiers, Post en klokken, Omgeving. In het midden wat er al staat, plus klikbare groeikaarten. Onderaan één zin. De opdrachten staan in `hulp/prompt_db.json`. Een klik stuurt die opdracht naar `agy`.



Papierkleur, donkere tekst. Geen browser, geen webview, geen Electron, geen genummerd menu, geen API-sleutel op het scherm.



## Wat vastligt



- Map blijft `CivicHelper`. Vensternaam is Civic Helper.

- Persoonlijk dossier blijft in `werk/`, buiten git. Niet in de openbare bestanden.

- Eén gratis Gmail-adres start `agy` en is de eerste postbus. Een extra modelhuis is geen drempel.

- Brief naar een loket: `veto_gate.py`, dan `audit_engine.py`, dan `TwoGateDispatcher`, dan het sein. Het programma verstuurt zelf niets.

- Lokaal Nederlands loket: de toets vult het dossier, de brief blijft kort. Artikel en dreigende termijn gaan de achterzak in.

- Andere schaal of ander land: de verplichte vorm hoort wel in de brief. Landen zijn voorbeelden aan een kapstok, geen encyclopedie die vooraf volgeschreven wordt.

- Naar een extern modelhuis gaan geen burgerservicenummer, rekeningnummer of huisadres. Diagnoses en briefteksten gaan wel mee. Geen privacy-kramp over het eigen dossier. Geen extra sein voor een analyse.

- Naar een loket gaan geen medische details mee die dat loket niet nodig heeft.

- `glue_check.py` en `Ketengrootboek/sluiting.py` toetsen overdracht en tegenboeking. Geen vector-RAG. Een breuk is een residu.

- Zwaar werk, zoals een modelaanroep, blijft van de draad van het venster af.

- `START.cmd` blijft het menu voor wie de motor bouwt.



## Wat er staat



- Specificatie: `CivicHelper/APPLICATIE_SPECIFICATIE.md`

- Venster: `CivicHelper/hulp/venster.py`

- Lus: `CivicHelper/hulp/lus.py`

- Opdrachten: `CivicHelper/hulp/prompt_db.json`

- Ontkiemen: `CivicHelper/ontkiem.py` en `Ontkiem.cmd`

- Venster starten: `CivicHelper/CivicHelper.cmd`

- Masker: `Shared_Tools/pii_mask.py`

- Modeldeur: `Shared_Tools/model_bus.py`

- Briefketen in `CivicHelper/_engine/audit_engine.py`: veto vooraf, korte brief bij een lokaal Nederlands loket, poort achteraf, sein ontbreekt in de tekst

- Korte regels in `AGENTS.md`, `Instap/01_ZORG.md`, `Instap/03_GEMEENTE_WMO.md`, `Instap/04_FINANCIEN.md`

- Tafelwacht, niet gestart: `Shared_Tools/tafel_wacht.py`

- PyQt6 is op deze Windows-computer geïnstalleerd

- `agy` staat in het PATH (of `%LOCALAPPDATA%\agy\bin\agy.exe`)

- Werkmap: `CivicHelper/werk/00_Kompas.md`. Die map is leeg van een echte zaak.



## Wat niet gedaan is



- `Ontkiem.cmd` is niet gestart. De vier kiem-prompts zijn niet naar `agy` gegaan.

- Er is geen brief verstuurd en geen dossier opgevraagd.

- De twaalf dossierbladen en het landschap zijn nog leeg. Het scherm zegt dat ook.

- Het venster is niet aangeklikt als proef van een echte opdracht aan `agy`.

- Een testrun zonder netwerk: een korte brief zonder medische details komt door beide poorten. Het woord diagnose gaat uit de brief naar een loket.

- De oude `Ask-*.ps1`-scripts zijn niet samengevoegd in `model_bus.py`. Die bus is de nieuwe deur.

- `tafel_wacht.py` draait niet.



## Volgende stap



Eén opdracht uit het venster naar `agy` laten lopen, en kijken of het blad daarna zichtbaar verandert. Niet de hele tabel bouwen. Niet opnieuw een chatvak maken.



Als het scherm nog niet bevalt: de rail en de kaarten zijn de richting. De tekening `CivicHelper/tekening/bureau.html` is het voorbeeld voor de indeling, niet een pagina om in de browser te openen.

