# Civic Helper — specificatie

**Datum:** 17 oktober 2026
**Status:** De maat voor de bouw
**Venster:** Civic Helper
**Map:** `CivicHelper`

Dit document vervangt de eerdere specificatie. Die eerdere tekst beschreef een gesloten formulier met vaste zinnen. Dat formulier wordt niet gebouwd.

Er wordt in deze stap niets gebouwd. De bron onder `_engine/` wordt niet gewijzigd.

## Functie

De zorg, het openbaar bestuur en grote bedrijven knippen één mens en één bestaan in stukken. In de zorg wordt iemand opgeknipt in losse deelspecialismen en losse opnames. In het bestuur en de uitvoering, New Public Management, wordt één bestaan opgeknipt in gescheiden loketten, productcodes, uitbestede partijen en afgeschermde budgetten.

Een eiland sluit zijn eigen vinkje, en kijkt niet of het volgende eiland de overdracht oppakt. Het interne model van dat eiland ziet alleen het eigen deel. Wat erbuiten valt, heet al gauw niet voor dit loket, of gebrek aan medewerking.

Wat daarbij wordt weggeknipt, zijn de relaties en de ketens. Hoe meerdere aandoeningen over tientallen jaren op elkaar inwerken. Hoe besluiten van ziekenhuis, huisarts, gemeente, UWV, CAK, zorgverzekeraar, verhuurder en incasso in elkaar grijpen. De burger moet met zijn eigen geheugen de brug zijn tussen die eilandjes. Bij ziekte of hersenletsel valt hij in het gat daartussen.

De functie van deze applicatie is die opgeknipte ketens en relaties integraal herstellen.

Zij vraagt de versplinterde dossiers bij de losse eilandjes op. Zij legt de weggevallen verbindingen en de ontbrekende overdrachten bloot. Zij bouwt daaruit één beeld over de tijd. Een specialist of een loketambtenaar ziet één stuk in zijn eigen vakje. De applicatie herstelt de reeks en de wisselwerking tussen de delen. Met dat beeld voert zij het gesprek en de onderhandeling met de afzonderlijke loketten, zodat hun versmalde model wordt bijgesteld en de keten rond de persoon weer sluit.

Zij werkt in een doorlopende slag. Eerst haalt zij stap voor stap naar binnen wat buiten over de persoon vastligt, bij ziekenhuis, huisarts, gemeente, uitkeringsinstantie, CAK, zorgverzekeraar, BKR, verhuurder en bank, en zet dat op de eigen computer. Telkens als er een nieuwe pluk stukken binnenkomt, of in een gesprek een nieuw verband opduikt, draait zij daar een nieuwe analyse overheen. Het beeld wordt zo laag voor laag scherper.

## Intern model

Elke partij waarmee de persoon te maken krijgt draait op een eigen intern model van de werkelijkheid. Een medewerker, een afdeling, een arts, een woningcorporatie, een incassobureau of een overheidsorgaan. Dat model bepaalt wat die partij wel en niet kan zien, en hoe zij het gedrag van de persoon uitlegt.

Ook voordat een opgevraagd dossier binnen is, leest het programma aan een stroeve of formele reactie af welk model de andere kant draait. Waar een loket vermoeidheid, gebrek aan initiatief of gemiste afspraken invult als onwil, vecht het programma niet tegen die waarnemingen. Het legt onder precies diezelfde feiten de oorzaak die de stukken dragen, in de taal die dat loket kan verwerken, en zonder gezichtsverlies voor de ander. De zin mag zijn dat geen van beiden die link eerder had gelegd.

Tegen een incassobalie spreekt het programma het administratieve model aan. Geen levensverhaal. Geen erkenning van de schuld. Wel de vraag naar de titel en naar inzage. Tegen een arts spreekt het de meetreeks, het beeld en de tijdlijn aan. Tegen een teamleider spreekt het rust op de werkvloer aan, en een notitie waarmee hij intern ruimte kan maken.

Het programma schrijft zelf ook niet vanuit het model van een advocatenkantoor naar een lokaal Nederlands loket. Die toon legt daar de hulp stil.

Welke toon een loket opent, hangt af van twee dingen. Op welke schaal het zit: lokaal, regionaal, nationaal of privaat. En in welke bestuurscultuur het werkt. Het programma heeft geen vast keukentafelsjabloon. Het protocol schakelt mee met de kapstok. De kernel blijft dezelfde.

De voorbeelden hieronder zijn geen wetboeken die de bouwer vooraf voor de hele wereld uitschrijft. Namen, portalen, contracten, termijnen en regelingen veranderen. `domain_packs/` en `Landschap/` zijn kapstokken. Zodra een nieuw loket in beeld komt, tuigt het model die kapstok in de lokale werkmap op, samen met de persoon. Het werkt haar bij via `sync_landscape.py`, via binnengekomen brieven en via openbare bronnen.

Elke kapstok stelt dezelfde vier vragen. Hoe heet dit loket nu, wie voert uit, en wie mag beslissen. Welke toon opent hier de deur. Welk kanaal telt als bewijs, en welke termijn gaat lopen. Welke partijen zijn op dit moment in deze regio gecontracteerd, en waar zit het gat.

Nederland, lokaal. Gemeente, Wmo, wijkteam. De werktaal is het keukentafelgesprek. Een wetsartikel in de eerste brief wekt afweer en schuift het dossier naar Juridische Zaken. De wet blijft in de achterzak tot de voorkant dichtzit.

Nederland, nationaal. CAK, Belastingdienst, UWV, BKR. Er is geen persoonlijke relatie. De brief is kort en vormvast, met een afgeschermde identiteitskopie. De termijn loopt op de achtergrond mee.

Duitsland, als voorbeeld. Een Behörde kan niets met een informele brief zonder dossiernummer en zonder paragraaf. Het noemen van de juiste bepaling, het bezwaar en de termijn geeft de ambtenaar de grond om te handelen.

Verenigd Koninkrijk. Het pakket `uk_housing` staat er. Zonder de wettelijke sleutelwoorden blijft een bericht hangen bij de klantenservice. Redelijke aanpassing onder de Equality Act 2010. De voorlopige huisvestingsplicht onder Housing Act sectie 188. De klachtentrap Stage 1 en Stage 2.

Frankrijk, als voorbeeld. De toon is hoog-formeel. Een gewone mail telt vaak pas met een aangetekend stuk en een formele aanmaning, of een verwijzing naar de Défenseur des droits.

Verenigde Staten, als voorbeeld. Rechten die niet in de eerste brief worden ingeroepen, kunnen vervallen. Denk aan de validatie van een schuld onder de FDCPA binnen dertig dagen, of een verzoek onder de ADA. Dit is het model waarop de meeste taalmodellen standaard zijn getraind. Het programma neemt die toon niet mee naar een Nederlands wijkteam.

De toets van `audit_engine.py` en `veto_gate.py` schakelt mee. Bij een lokaal Nederlands gesprek haalt zij overtollig wetsjargon uit de brief. Bij Duitsland, het Verenigd Koninkrijk, Frankrijk of de Verenigde Staten controleert zij of de verplichte paragraaf of de sleutelzin er wel in staat.

China, Polen en Italië zijn dezelfde soort voorbeelden. Het model tuigt het profiel op wanneer zo'n loket in beeld komt. Het schrijft die mappen niet van tevoren vol.

China, als voorbeeld. Een lokaal loket slaat dicht bij een aanval op het systeem. De brief doet een beleefd beroep op de centrale welzijnslijn en legt het probleem neer als een gat tussen twee balies dat samen dicht moet. Inzage loopt via artikel 45 van de PIPL. Het ticket op de 12345-lijn zet de interne beoordelingsklok van de afdeling aan. Onder de motorkap toetsen Qwen, via `Shared_Tools/Ask-Qwen.ps1`, en DeepSeek de ambtelijke formulering.

Polen, als voorbeeld. Een losse mail telt daar zelden. De ingang loopt via ePUAP, beleefd, met een beroep op de plicht van het ambt om de burger voor te lichten, artikel 8 en 9 van de KPA. Inzage is artikel 15 RODO. De termijn is dertig dagen, artikel 35 KPA. Blijft het stil, dan is de aanmaning naar het hogere orgaan artikel 37 KPA. Onder de motorkap toetsen een Pools bestuursmodel, Mistral en DeepSeek de termijnen.

Italië, als voorbeeld. Een gewone mail verdwijnt daar omdat niemand persoonlijk verantwoordelijk wil zijn. Verzending gaat via PEC, de gecertificeerde post. De brief vraagt hoffelijk naar de naam van de ambtenaar die voor dit dossier verantwoordelijk is, onder wet 241 van 1990, artikel 4 tot en met 6. De zorgvraag koppelt aan wet 104 van 1992. Inzage is artikel 22 van wet 241, plus artikel 15 van de AVG. Blijft het stil na dertig dagen, dan neemt de ambtenaar erboven het dossier over, artikel 2 lid 9-bis van wet 241. Onder de motorkap toetsen Mistral, Gemini en DeepSeek die artikelen.

Ook de taalmodellen zelf hebben een intern model dat in de weg kan zitten. Zij zijn getraind om te schrikken van persoonsgegevens en medische stukken, alsof die nog een geheim zijn. Overheden, zorginstellingen, verhuurders en bedrijven hebben allang grote profielen over de persoon, zichtbaar en onzichtbaar. De persoon gebruikt de modelhuizen om dat profiel boven tafel te krijgen. Het programma schiet daar niet in een privacy-kramp. Het weigert geen stukken. Het laat voor de analyse tussen de modelhuizen geen feiten weg. Het vraagt geen apart sein voor dat denkwerk. De persoon is de eigenaar van zijn dossier.

## Eigen regie en rust

Wie jarenlang geen administratie heeft kunnen doen, zit onder een berg brieven, oude verwijten en lopende termijnen. De applicatie neemt het kantoorwerk over. De persoon houdt het roer. Het programma maant hem niet tot rust.

De persoon hoeft zijn probleem niet eerst zelf te ordenen. Hij zegt in gewone taal, of via de microfoon, waar hij tegenaan loopt. Het programma houdt de draad over weken vast en legt telkens één voorstel voor.

De persoon hoeft zijn geschiedenis niet in één keer aan te leveren. Het beeld groeit tijdens gewone gesprekken. Valt er tijdens het praten een jaartal, een oud adres of de naam van een vroegere behandelaar, dan legt het programma dat stukje op zijn plek in de tijdlijn. Het gesprek wordt daar geen verhoor van.

Is er deze week een zwaar onderzoek of een belangrijk gesprek, dan houdt het programma niet-urgente brieven even vast. Het opent niet vijf gevechten tegelijk.

Het programma laat zien welk loket welk mandaat heeft. Een welwillende medewerker krijgt een haakje dat in zijn ruimte past. Mag hij niet beslissen, dan gaat de vraag naar degene die dat wel mag.

In binnengekomen dossiers staan oude fouten en stempels die telkens opnieuw tegen de persoon worden gebruikt. Het programma zet daar het feit uit dezelfde periode naast, uit de stukken of de uitslagen. Zo nodig zet het een correctie klaar. Dat is een aanvulling op het dossier, niet een ruzie op het scherm.

Voor een afspraak maakt het programma één pagina met de feiten en een briefje van drie punten. De persoon legt dat neer. Het gesprek blijft bij de afspraak van vandaag.

Eist een instantie een eigen formulier of een kopie van een identiteitsbewijs, dan vult het programma het formulier in en maakt het een afgeschermde kopie. Het burgerservicenummer en de machineregel zijn afgedekt. Er staat een datum op. Dat wordt één stuk, klaar om te versturen na het sein.

Levert een instantie, herstelt zij een fout, of verleent zij een ontheffing, dan zet het programma een kort bedankje klaar en markeert het spoor als afgerond. De berg slinkt zichtbaar.

## Vorm

De applicatie is geen gesloten programma. Zij heeft geen vaste zinnen en geen tabel van als-dit-dan-dat.

Zij gebruikt het beoordelingsvermogen van een model om op dat moment een oplossing te zoeken voor het concrete probleem van deze persoon. Zij past zich aan de omstandigheden aan.

Het model is het hart. De tijdlijn, de termijnklok, de spraak en het leesbaar maken van scans zijn middelen. Het model roept een middel aan wanneer de situatie daar om vraagt. Het zijn geen knoppen op een vast scherm.

Vast zijn de kernel in `ct_runtime/`, de vijf bouwstenen, het sein, het venster en de lijst onder `Niet`. Vrij zijn de kapstokken en de hulpmiddelen die in de lokale werkmap meegroeien.

De middelen in `_engine/` zijn het begin, niet het plafond. Elk dossier werpt vroeg of laat een obstakel op waar nog geen script voor klaarstaat. Een afwijkend formulier. Een nieuw soort afschrift. Een grafiek van jarenlange meetwaarden. Een koppeling die alleen op deze computer bestaat. Het model schrijft dan in de lokale werkmap zelf het hulpmiddel, en voert het uit. De persoon ziet het resultaat in gewone taal. Hij opent daar geen terminal voor en schrijft geen regel code. Een nieuw hulpmiddel komt niet in `_engine/` en niet in git. Het verstuurt geen post op eigen houtje. Daarvoor geldt het sein.

De persoon sleept geen mappen en houdt geen administratie bij. De applicatie doet dat werk. Zij zet de verzoeken klaar, volgt de reacties, en haalt de dossiers op waar ze binnenkomen.

Niet elk contact begint met een inzageverzoek. Het model kijkt met welk loket de persoon te maken heeft en kiest één stand.

1. Vragen. Eén gewoon gegeven ontbreekt.
2. Bevestigen. Na een gesprek of een mondelinge toezegging legt een korte mail vast wat er is afgesproken.
3. Wachten. De andere kant is aan zet. Er gaat niets weg.
4. Op de streep gaan staan. Een art. 15-verzoek, een vraag naar specificatie zonder de schuld te erkennen, of een harde termijn, als een loket weigert, stilvalt of doorverwijst zonder overdracht.

Een brief in een lopende onderhandeling is een zet die de relatie in beweging houdt. Het is geen eindvonnis.

Zegt iemand aan de telefoon meer dan hij daarna in drie regels mailt, dan is dat geen breuk die meteen dichtgetimmerd wordt. De bevestiging neemt de mondelinge opening mee en laat de ander ruimte. Zij vraagt of de persoon het te ruim heeft begrepen.

Dezelfde keten heeft verschillende adressen. De begeleider aan huis krijgt drie gewone zinnen over de afspraak. Het kantoor krijgt de administratieve stukken. De teamleider krijgt de afstemming over de voortgang van de hulp. De functionaris gegevensbescherming krijgt het inzageverzoek. Die lijnen gaan niet in één brief, en niet in een ongevraagde kopie naar elkaar.

Loopt een uitvoerend medewerker vast op de regels van zijn systeem, dan valt het programma die persoon niet aan. Het gebruikt wat er al in het dossier staat, vraagt een praktische bijstelling van de werkopdracht, of geeft een welwillende teamleider een stuk waarmee hij intern ruimte kan maken.

Over een medische vaststelling gaat het programma niet in discussie met het gemeenteloket. De onderbouwing komt via de huisarts of het revalidatiecentrum. Zit een hulporganisatie vast op een wachtlijst terwijl de zorgroute al loopt, dan steekt het programma daar geen energie meer in.

Een papieren brief op de deurmat, een foto op de telefoon, of een bestand uit een portaal mag de persoon in het venster geven. Het programma sorteert en leest daarna. Vraagt een instantie eerst een afgeschermde kopie van een identiteitsbewijs of een handeling in een portaal, dan bereidt het programma die stap voor. Een portaal is niet de enige weg.

Ziet het een verband tussen twee stukken, dan vraagt het of dat verband op de tijdlijn mag. Zegt de persoon dat er morgen een gesprek is, dan bereidt het programma dat gesprek voor.

## Grenzen

De persoon houdt het oordeel. Het programma stelt de brief voor. De persoon geeft het sein. Dan gaat de brief de deur uit, als gewone e-mail.

Zegt de persoon dat een datum, een bedrag of een status niet klopt, dan past het programma de tijdlijn, de klok en het kompas aan. Hij zegt dat in één zin, of met zijn stem. Hij hoeft niet in een bestand of een tabel te snijden.

Is er nog geen lokale mailverzending, dan loopt het venster niet vast. Na het sein opent het programma het bericht in het mailprogramma dat al op de computer staat, met ontvanger, onderwerp, tekst en bijlage. De persoon verstuurt het daar. Dat is de weg op een computer als die van Walter, waar Proton Bridge en Betterbird nog niet staan.

Instanties bellen om iets buiten het dossier af te doen. Uitgaande berichten blijven schriftelijk. Belt een instantie toch, dan zet het programma meteen een korte bevestigingsmail klaar, zodat een mondelinge toezegging niet verdwijnt.

Eén model alleen verzint een aanname, of laat een haakje vallen. Bij een belangrijke brief, een verweer of een integrale analyse vertrouwt de applicatie daarom niet op één model. Op het scherm praat de persoon met één stem. Daaronder toetsen verschillende modelfamilies het stuk, via `_engine/audit_engine.py` en `Shared_Tools/skeptic_filter_runner.py`. De persoon ziet dat gekibbel niet.

Die toets vult het dossier. Bij een brief aan een lokaal Nederlands team maakt zij de brief niet voller en niet juridischer. Voegt een model daar een wetsartikel, een kopie aan een collega of een dreigende termijn aan toe, dan gaat dat de achterzak in. De brief die weggaat wordt korter. Een volle brief klinkt daar als een advocatenkantoor en legt de praktische hulp stil. Bij een andere schaal of een andere bestuurscultuur controleert dezelfde toets of de verplichte vorm in de brief staat.

Bij een brief naar een loket haalt `veto_gate.py` eerst de medische details weg die dat loket niet nodig heeft. `guard_gate.py` kijkt of de persoon het aankan. Daarna toetst het andere modelhuis het stuk via `run_constructive_audit`. Een auditmodel wil soms zelf weer iets toevoegen. Daarom toetst `TwoGateDispatcher.dispatch` het eindresultaat nog een keer, voordat het voorstel op het scherm komt. De persoon ziet de brief die ook echt zou vertrekken.

Zolang een gesprek met een lokaal Nederlands loket nog open is, gaat er geen ingebrekestelling weg en noemt het programma geen dwangsombedrag. Een gat in de tijd mag het wel noemen. Het artikel en het bedrag blijven achter tot de persoon die voorkant sluit, en tot zij het sein geeft. Bij een landelijke balie of een andere bestuurscultuur hoort de verplichte vorm wel in de brief.

De echte grens voor gegevens ligt op twee plekken. Naar een loket toe krijgt een incassobalie, een verhuurder of een administratief loket geen medische details waarmee zij hun profiel over de persoon verder vullen. Dat doet `veto_gate.py` in de conceptbrief, vóór de audit. Naar de openbare code toe komt het persoonlijke dossier nooit in git, en niet op een centrale server van de applicatie.

Voor de integrale analyse zien de modelhuizen waarvan de sleutels in de omgeving staan het dossier wel. Zij hebben de diagnoses, de uitslagen, de datums en de briefteksten nodig. Het programma houdt die feiten niet achter uit een privacy-reflex, en het waarschuwt de persoon daar niet voor. Het enige dat het vóór die reis lokaal door een plaatshouder vervangt, zijn het burgerservicenummer, het bankrekeningnummer en het huisadres. Die zijn voor de redenering niet nodig. In het concept op de eigen computer zet het programma ze terug. Voor die toets vraagt het geen sein. Het sein geldt alleen wanneer er een bericht naar een echte persoon of instantie vertrekt.

Om te beginnen heeft de persoon geen betaald abonnement, geen creditcard en geen losse API-sleutel nodig. Eén gewoon, gratis Gmail-adres zet alles in gang. Dat adres activeert de gratis versie van `agy`, en het is meteen het eerste e-mailadres waarmee met instanties wordt gecommuniceerd. Een extra modelhuis in de omgeving kan later vanuit het lopende programma worden toegevoegd. Het is geen drempel om te starten. Het venster opent zonder een contract en zonder om een sleutel te vragen. De installatiepijn van oktober, met PATH, een Google-contract en een onleesbaar scherm, bepaalt hoe het venster opent. Zij haalt de functie niet weg.

## Veerkracht

Naarmate meer mensen met een model hun dossiers opvragen, loopt de druk op loketten op. De reflex is dan het kanaal afknijpen, of de tekst afwijzen omdat er een model aan te pas kwam. Het programma verstart daar niet. Het sleept de persoon niet een loopgravenoorlog in.

Het programma is geen brievengenerator. Het brengt een lange versnippering terug tot één korte vraag bij degene die erover gaat. Een medewerker is dan minder zoektijd kwijt.

Sluit een instantie het gewone e-mailadres, of dwingt zij een kort formulier, een portaal of papier af, dan past het programma de vorm aan. Het vat de kern samen binnen de tekenlimiet. Het vult het formulier voor. Het zet de brief klaar om af te drukken. Of het verlegt de route naar een ingang die open moet blijven, zoals de functionaris gegevensbescherming. De persoon hoeft niet te bellen.

Wijst een loket de inhoud af omdat de persoon een model gebruikte, of weigert het schriftelijk contact bij iemand die dat nodig heeft, dan zet het programma dat rustig recht. Het hulpmiddel ordent de feiten. Het staat niet ter discussie. De instantie weerlegt een keten alleen door schriftelijk te noemen welk feit of welk bronstuk niet klopt. De grond daarvoor, het VN-Verdrag Handicap, de WGBO en de AVG, blijft in de achterzak tot de afwijzing er is.

### Het communicatieharnas als schild voor veerkracht (SBARIII)

Empirisch onderzoek (*Martínez-Fernández et al., 2022, PMC9778833*) toont aan dat gestandaardiseerde overdracht via SBAR de individuele veerkracht (*resilience*, CD-RISC) significant verhoogt (van 28.03 naar 38.46, $p=0.000$), terwijl de onvrede over falend management en institutionele bureaucratie gelijk blijft. 

De burger kan het disfunctionele stelsel niet in zijn eentje repareren. SBARIII fungeert als een cognitief harnas:
1. Het overbrugt de sociologische botsing tussen de holistische beleving van de burger en het detailgerichte/hiërarchische model van de instantie.
2. Het vangt het feit op dat 97% van de ongestructureerde overdrachten faalt.
3. Het dwingt een gesloten lus (*Repeat-Back / Tegenboeking*) af.
4. Bij professionele weerstand of kritiek op het format valt de applicatie direct terug op de formele notitie: `NOTITIE_COMMUNICATIEPROTOCOL_SBARIII.md`.

## Wat de persoon ziet

Geen log, dichtgetimmerd monolithisch bureaubladvenster dat probeert een compleet besturingssysteem na te bouwen. De interface volgt de **File-over-UI** filosofie: data leeft in open, duurzame bestanden (Markdown, JSON, HTML) en de interface past zich vloeiend aan de taak aan.

1. **De CLI-werkruimte (Agy / Terminal):** Voor directe regievoering, snelle zinnen, en het aanroepen van hulpmiddelen. Ondersteund door snelle inspectietools in de terminal zoals `glow` (voor markdown-weergave) en `yazi` (voor bestandsnavigatie).
2. **Natuurlijke OS-integratie (QuickLook / `ql`):** Inspectie van dossiers, bijlagen, brieven en scans met één spatiebalk via QuickLook direct vanuit Windows Explorer of via het commando `ql <bestand>`.
3. **Kennisgraaf en Tijdlijn (Obsidian):** Visueel overzicht over de 12 levensdomeinen, de ketenrelaties en de chronologie via Obsidian Graph View en Obsidian Canvas, rechtstreeks op de lokale markdown-bestanden buiten git.
4. **Standalone On-Demand Dashboards (Owl Visual Aesthetic):** Wanneer een complexe visuele synthese nodig is (zoals een ketenorganogram, contractenmatrix of overdrachtskaart), genereert het model een zelfstandig, lokaal HTML/SVG-artefact. Dit opent direct in de standaardbrowser met een rustige, ambient donkere esthetiek (`#05030a`, glasvlakken, goud- en cyaantinten) zonder lokale server of afhankelijkheden.

Whisper, het lezen van scans, en een diepe modelaanroep draaien in de achtergrond. De persoon hoeft geen terminalcommando's uit zijn hoofd te leren; een klik of een rustige zin in gewone taal volstaat.

## Middelen

Het model roept deze middelen aan. Het venster bouwt ze niet na.

| Wanneer de situatie dit vraagt | Aanroep | Wat er vandaag al kan |
|---|---|---|
| Alles op één tijdlijn | `_engine/timeline_weaver.py`, `TimelineWeaver` en `auto_scan_directory` | De wever leest csv, WhatsApp-tekst, bellijsten, `.eml` en markdown. Hij schrijft `00_Master_Chronologie.md` en een json ernaast. |
| Een gat tussen twee momenten | `TimelineWeaver.detect_anomalies` | De methode ziet een stilte en koppelt daar nu meteen een wetsartikel aan. Het model mag het gat noemen. Het artikel en het bedrag spreekt het pas uit als de persoon de voorkant heeft gesloten. |
| Of een overdracht sluit, en welk residu blijft liggen | `_engine/glue_check.py`, `GlueChecker.evaluate_interface`, op een interface uit `interfaces.json` | Geen vector-RAG. Dezelfde naam is nog geen dezelfde overdracht. Het oordeel is `ADMISSIBLE` of `GLUING_FAILURE`. Het residu is wat de ontvanger niet heeft ingeboekt. |
| Of de tegenboeking er is | `Ketengrootboek/sluiting.py`, `SluitingsToetser`, één post of `ALL` | De zender boekt af. De ontvanger boekt in. Ontbreekt de tegenboeking, dan is de uitkomst `GLUING_FAILURE`. Ontbreekt het bewijsstuk, dan is de uitkomst `UNDECIDED`. `ALL` ververst `saldo.json`. |
| SBARIII overdrachtsstandaard en gesloten lus | `_engine/sbar_protocol.py`, `SBARProtocol` | Toetst concepten op I-S-B-A-R-I-I conform AHRQ TeamSTEPPS en PMC9778833. Borgt de verplichte Read-Back eis. Biedt formele replieken via `NOTITIE_COMMUNICATIEPROTOCOL_SBARIII.md`. |
| Een termijn van een instantie | `_engine/statutory_clock.py`, `StatutoryClockManager` | `add_clock` zet een klok op een instantie, een type en een verzenddatum. `evaluate_status` leest de stand. `generate_ingebrekestelling` schrijft een brief. Die brief wordt niet gemaakt zolang het gesprek open is. |
| De post in de gaten houden | `Shared_Tools/check_mail.py`, op de post die al op deze computer binnenkomt | Een reactie van een instantie wordt gezien. Het model leest haar en zet het antwoord klaar. |
| Een inzageverzoek | een art. 15 AVG-brief, digitaal, met de termijn van één maand | De tekst verschijnt in het venster. Na het sein van de persoon gaat zij als e-mail weg. Een portaal is geen voorwaarde. |
| Binnengekomen dossiers | de bijlage, de download of het bestand uit de post | Het programma pakt ze op, legt ze lokaal geordend weg, maakt scans tot tekst, en zet ze op de tijdlijn. |
| Een opname | Whisper, lokaal, zoals nu al gebruikt | De opname wordt tekst. Daarna kan de wever haar plaatsen. |
| Een scan of een PDF | Het OCR-middel dat op deze computer al draait | De scan wordt tekst. Daarna kan de wever haar plaatsen. |
| Een concept toetsen voordat de persoon het ziet | `_engine/two_gate_dispatcher.py`, `TwoGateDispatcher.dispatch` | Bij een brief naar een loket eerst `veto_gate.py`, dan de audit, dan nog eens `TwoGateDispatcher` als eindslot. `guard_gate.py` kijkt of de persoon het aankan. |
| Een loketpatroon lezen | `_engine/loket_patroon.py`, `lezen` | Alleen een geijkt patroon, met een zin en een bron. Zonder die twee weigert de functie. Het model verzint geen patroon. |
| Bankafschriften | `_engine/bank_audit.py`, `analyze_csv` | Leest een bank-csv op uitkering, huur, toeslagen, CAK, energie en incasso. |
| De kapstok voor een rechtsgebied of een bestuurscultuur | `_engine/domain_packs/`, met `nl_wmo`, `nl_schulden_oninbaar`, `nl_uwv`, `nl_brp_adres`, `nl_toeslagen` en `uk_housing` als startvoorbeelden | Geeft de grenzen, de toon en de klok. Bij een lokaal Nederlands gesprek blijft de wettekst van het scherm af tot de voorkant sluit. Bij een ander profiel blijft de verplichte vorm in de brief. Komt er een nieuw domein, een andere gemeente of een ander land, dan tuigt het model in de lokale werkmap zelf een profiel aan die kapstok op. |
| Een brief versturen na het sein | `Shared_Tools/agy_mail.py`, `draft_email` en daarna `send_smtp` | Eerst het concept. Na het sein gaat het als gewone e-mail. De verzenddatum gaat naar de termijnklok. `send_via_phone` is niet de weg. Ontbreekt `send_smtp`, dan opent het venster het bericht in het mailprogramma van de computer. |
| Stukken bundelen | `_engine/case_bundler.py`, `build_case_bundle` | Eén pakket met tijdlijn en het SHA-256-controlegetal van de bronstukken. |
| Het veranderende landschap bijhouden | `_engine/sync_landscape.py`, `LandscapeSynchronizer`, en de lokale map `Landschap/` | Houdt organisaties, mandaten en contracten bij uit binnengekomen brieven en uit RIS, Notubiz en Bekendmakingen. Verandert een loket van naam, medewerker of contract, dan werkt het programma het landschap bij. De brief gaat naar degene die nu mag beslissen. |
| Een labreeks naast een oude bewering | `Shared_Tools/medical_dossier_analyzer.py`, `parse_lab_data` en `generate_longitudinal_plot` | Zet de uitslagen van een periode op een rij. Het weerleggen van een stempel doet het model met die rij en met de tijdlijn, niet dit script alleen. |
| Wetenschappelijke literatuur en consensus | `Shared_Tools/pubmed_probe.py`, `PubMedProbe` | Haalt peer-reviewed evidentie, systematic reviews en richtlijnen op via de officiële NCBI E-utilities API. Weerlegt luie stempels en borgt epistemische pariteit. |
| De persoon spreekt in plaats van te typen | `Shared_Tools/luister.py` en `Shared_Tools/voice_console.py` | `record_audio` maakt van spraak tekst. Het model maakt daar de volgende stap van. |
| Een conceptbrief door een ander modelhuis laten toetsen | `_engine/audit_engine.py`, `run_constructive_audit` met `is_critical=True` | Het ene huis schrijft. Een ander huis toetst feiten, termijnen en waar het loket onderuit kan. De functie schrijft `AUDIT_REPORT_` en de aangescherpte brief `REFINED_`. De sleutels blijven in de omgeving. Burgerservicenummer, bankrekening en huisadres zijn dan al vervangen door een plaatshouder. |
| Een verband in een analyse zeven | `Shared_Tools/skeptic_filter_runner.py`, `execute_skeptic_audit`, volgens `Shared_Tools/MULTI_LLM_AUDIT_PROTOCOL.md` | Drie families: critic, skeptic en de derde stem. Een breuk telt pas als de skeptic haar op de bronplek niet weerlegt, en de derde stem dezelfde breuk uit alleen dat bronstuk haalt. |
| De systeemtoestand doorrekenen | `ct_runtime/kernel.py`, `resolution.py`, `interlock.py`, `ledger.py`, `egress.py` | Houdt elk levensdomein in een eigen vak, met hooguit vier koppelingen. Een ontbrekende tegenboeking is een fout, geen stilte. Loopt informeel overleg leeg, dan schakelt `resolution.py` over naar de harde termijn. Zakt de speelruimte in, dan remt of stopt `interlock.py`. `egress.py` haalt de interne rekenwoorden uit de tekst voordat die naar buiten gaat. |

`auto_scan_directory` leest geen PDF en geen audio. Eerst tekst, dan de tijdlijn. Dat is de volgorde van de middelen, niet een formulier voor de persoon.

De tabel is het startpakket. Mist er voor een nieuw probleem een middel, dan bouwt het model dat middel bij in de lokale werkmap en gebruikt het vanaf dat moment mee. Het antwoord is nooit dat daar geen functie voor is.

Een overdrachtsblad van één pagina en een briefje van drie punten maakt het programma zelf. Er is daar nog geen apart script voor. Een afgeschermde identiteitskopie maakt de bouwer in het venster. Hij haalt het persoonlijke script daarvoor niet de openbare map in. Een bedankje is een gewone mail via `agy_mail.py`, geen los script per instantie.

Het model zoekt niet met een woordwolk en niet met een vectorbank. De toets op een verband is de gerichte overdracht en het residu, via `glue_check.py`, en de tegenboeking via `Ketengrootboek/sluiting.py`, zoals `ZOEKMETHODEN_NOTITIE_NON_RAG_RELATIES.md` voorschrijft. Debet, credit en journaalpost blijven in die motor. Op het scherm zegt het model in gewone taal wie heeft afgesloten en wie de overdracht niet heeft ingeboekt.

Onder die toets rust de analyse op vijf bouwstenen. Hun formules en vaktermen komen niet op het scherm en niet in een brief.

1. Overdrachten tussen eilandjes. `glue_check.py`, `interfaces.json` en `sluiting.py`. Op het scherm: wie heeft afgesloten, wie de overdracht heeft laten vallen, en waar het gat zit.
2. Het interne model van het andere loket. `sync_landscape.py` en de vier gespreksstanden. Op het scherm: hoe dit loket aangesproken wordt zodat er beweging komt.
3. Wat de opknipping uit elkaar haalde, weer op één tijdlijn. `guard_gate.py`, `gtid_engine.py` en `timeline_weaver.py`. Lichaam en wet, lopende stromen, en wat er geregistreerd staat. Op het scherm: hoe gezondheid, energie, wonen, inkomen en gemeentebesluiten over de jaren op elkaar inwerken.
4. De speelruimte van de persoon. `Shared_Tools/trf_guard.py` en `two_gate_dispatcher.py`. Op het scherm: welke sporen veilig lopen, wanneer er gedoseerd wordt voor een zwaar moment, en waar nu één actie nodig is.
5. Dezelfde feit in de taal van de ontvanger. `domain_packs/` en `veto_gate.py`. Gewone taal, de taal van de arts, of de taal van bestuur en incasso. Op het scherm: een brief of een overdrachtsblad zonder een theoretische term.

Die vijf bouwstenen draaien op de kernel in `ct_runtime/`. `kernel.py` houdt de vakken uit elkaar. `ledger.py` boekt de overdracht. `resolution.py` kiest het moment waarop praten overgaat in een termijn. `interlock.py` bewaakt of de persoon nog speelruimte heeft. `egress.py` filtert de rekenwoorden bij de uitgang. Op het scherm blijft gewone taal.

Wat binnenkomt, legt het programma lokaal geordend weg, buiten git. De tijdlijn, de klok en het zaakkompas komen in diezelfde werkmap. Het kompas heet daar `00_Kompas.md`. Het blijft kort. Er staat in wie de persoon is, en welke sporen nu openstaan. Bij het openen leest het model dat bestand, zodat de persoon zijn verhaal niet opnieuw hoeft te doen. Dit is niet `00_MASTER_KOMPAS.md`.

Een omgeving die maanden meegroeit, slipt dicht als alles op één hoop belandt. De diepte per onderwerp ligt in losse takken in de werkmap: zorg, gemeente, geld, adressen en het verleden. Het model opent alleen de tak waar de zin van dat moment over gaat. Is een spoor afgerond, dan verhuizen de tussenversies en de kladjes naar het archief. Op het kompas blijft één regel staan.

Het openbare voorbeeld in de motor blijft Voorbeeldstad. Het persoonlijke dossier wordt niet naar die voorbeeldmap gekopieerd.

## Bouw en ontkiemen

Het venster is geen los script zonder handen dat buiten de CLI-agent om een kale tekst-API aanroept. De motor onder het venster is de lokale CLI-agent zelf (`agy`). Alleen die agent leest bestanden, stuurt `_engine/` en `ct_runtime/` aan, en bouwt in de lokale werkmap een nieuw hulpmiddel wanneer een obstakel opduikt.

De motor onder het venster is `agy`, niet een los script zonder handen. Om het zaadje op een schone computer te laten ontkiemen is voor de persoon één startgegeven nodig: één gratis Gmail-adres.

`ontkiem.py` neemt de installatie uit handen. Het registreert de gratis `agy` en Python in het systeempad, zonder dat de persoon een terminal bedient. Het koppelt datzelfde Gmail-adres als het eerste adres voor inkomende en uitgaande post. Het pakt deze map uit als het zaadje. Het stuurt daarna de kiem-prompts naar `agy`: verken dit besturingssysteem en het mailprogramma, richt buiten git `werk/` en `00_Kompas.md` in, koppel het PyQt-venster met `agy` zelf als motor, en open het venster voor het eerste gesprek. Op dag één kan `agy` de toets met gescheiden blikken zelf draaien. Een extra modelhuis komt later, vanuit het venster.

De eerste lus blijft klein. De bouwer hangt niet alle middelen uit de tabel in het eerste venster. De tabel en `ct_runtime/` liggen klaar. `agy` roept ze aan, of bouwt ze bij, wanneer de zaak daarom vraagt.

De eerste lus is dit. Het venster gaat open op `00_Kompas.md`. Er gaat één brief weg, in de volgorde `veto_gate.py`, dan `run_constructive_audit`, dan `TwoGateDispatcher`, dan het sein. Een reactie of een dossier komt binnen op de tijdlijn. Het programma noemt in gewone taal de breuk en de volgende zet.

1. Het venster opent zonder commando. Het model leest `00_Kompas.md` uit de lokale werkmap, en alleen de tak waar het gesprek over gaat. Het volgt de post die al op deze computer binnenkomt. De sleutel komt uit de omgeving. Ontbreekt de postbrug, dan blijft het venster open en loopt het versturen via het mailprogramma van de computer.
2. Het model zet een brief klaar in de stand die bij dit loket en dit land hoort. `veto_gate.py` haalt eerst weg wat dat loket niet mag zien. Daarna toetst een tweede modelhuis het concept via `run_constructive_audit`. Die toets vult het dossier. Een brief aan een lokaal Nederlands team blijft kort. Een wetsartikel, een kopie of een dreigende termijn uit die toets gaat daar de achterzak in. Bij een andere schaal of cultuur controleert de toets of de verplichte vorm erin staat. Daarna toetst `TwoGateDispatcher` het eindresultaat nog een keer. De persoon leest het stuk en geeft het sein. Dan gaat het als e-mail weg, via `agy_mail.py`.
3. Een reactie komt binnen. Het model ziet haar, herkent uitstel, bewaakt de termijn van één maand, en zet het antwoord klaar. Wegsturen wacht op het sein.
4. De dossiers komen binnen, als bijlage, als download of via een portaal. Het model pakt ze op, ordent ze lokaal, maakt ze tot tekst, en legt de tijdlijn.
5. Op die tijdlijn toetst het programma de overdracht met `glue_check.py` en de tegenboeking met `sluiting.py`. Een breuk is een residu. Een woord dat twee keer voorkomt is dat niet. Een verband in de analyse telt pas na `execute_skeptic_audit`. Daarna noemt het de cascade of de open termijn, in gewone taal.

Elk van deze vijf is klaar als de persoon hem niet zelf als kantoorwerk hoeft te doen. Zij zijn niet het einde. Komt er een obstakel waar geen middel voor is, dan bouwt het model dat middel in de werkmap, en gaat het daarmee verder.

## Niet

- De map of de repository hernoemen.
- Een browser-app, een tabblad, een lokale webserver, of een webview.
- Een zware berekening op de draad van het venster, zodat het scherm bevriest.
- Een pagina met vijf vaste zinnen en een wachtzin.
- Zeggen dat er geen functie voor is, als het obstakel nieuw is.
- Een nieuw hulpmiddel in `_engine/` of in git zetten. Het komt in de lokale werkmap.
- Van de bouwer een encyclopedie van alle landen en gemeenten eisen. Die profielen groeien in de lokale werkmap.
- Een knoppenbord met de middelen als menu.
- Van de persoon verwachten dat zij mappen aanlegt, stukken sorteert of de administratie bijhoudt. Een foto van een papieren brief, of een bestand uit een portaal, mag wel in het venster. Het programma sorteert daarna.
- Post die weggaat zonder dat de persoon de tekst heeft gezien en het sein heeft gegeven.
- De persoon bij elke analyse om een extra sein vragen. Het sein is alleen voor post naar een persoon of een instantie.
- Uit een privacy-reflex een dossierstuk weigeren te lezen, of feiten weghouden uit de analyse tussen de modelhuizen. De persoon onderzoekt zijn eigen dossier.
- Een burgerservicenummer, een bankrekeningnummer of een huisadres meesturen naar een extern modelhuis.
- OAuth of een contract als voorwaarde om te beginnen.
- Een gesloten portaal als enige weg naar een dossier.
- Vastlopen als een e-mailadres dichtgaat, of de persoon laten bellen omdat een loket dat eist.
- Een tekst intrekken omdat een loket zegt dat er een model aan te pas kwam.
- Electron, of een nieuw account in een wolk.
- Het persoonlijke dossier in git.
- Een ingebrekestelling als eerste antwoord.
- Vector-RAG, een brokkenbank, of een los woord als bewijs van een verband.
- Debet, credit, journaalpost of memoriaal op het scherm. Die woorden blijven in `sluiting.py`.
- Formules of vaktermen van de vijf bouwstenen op het scherm of in een brief.
- Interne rekenwoorden uit `ct_runtime/` in een brief. `egress.py` haalt ze eruit.
- Een belangrijke brief of een integrale analyse de deur uit op het woord van één model.
- Het gekibbel tussen de modelhuizen op het scherm.
- Een brief aan een lokaal team voller of juridischer maken omdat een tweede model een artikel, een kopie of een termijn toevoegde.

## Klaar

De specificatie is klaar als een bouwer hieruit zonder een tweede ontwerp de eerste lus kan bouwen. Het venster gaat open op `00_Kompas.md`. Na de toets en het sein gaat één brief weg. Het binnengekomen stuk komt op de tijdlijn. Het programma wijst in gewone taal de breuk en de volgende zet aan. De tabel met middelen en `ct_runtime/` hoeven in de eerste week niet in het scherm gebouwd te worden. Zij liggen klaar als het zaad dat het model aanroept en uitbouwt zodra de zaak daarom vraagt.

De applicatie heeft haar werk voor een spoor pas gedaan als de stukken binnen zijn, de breuk op het scherm staat, en met dat beeld de overdracht bij het loket of de behandelaar weer sluit. De tegenboeking is er. Het spoor verhuist als afgerond naar het archief. De persoon heeft daar rust.
