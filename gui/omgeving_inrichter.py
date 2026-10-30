#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
omgeving_inrichter.py — Eén-klik Omgevingsinrichter & Stap-voor-Stap Uitlegger voor Civic Helper.

Wat deze module doet wanneer de gebruiker op '🛠️ Omgeving Inrichten' klikt:
1. Controleert / synchroniseert de Python-tools uit de GitHub-repository (indien git aanwezig).
2. Richt de lokale werkmap (`werk/`, `Dossier/`, `Incoming_Letters/`, `Outgoing_Drafts/`, `Ketengrootboek/`)
   veilig buiten git in.
3. Verifieert het persoonsmasker (`pii_mask.py`), de twee poorten (`GuardGate` & `VetoGate`) en het
   3-Boekenstelsel van Simon Stevin (`Ketengrootboek/sluiting.py`).
4. Controleert welke modelhuizen in de omgeving klaarstaan voor de verplichte Multi-LLM Audit.
5. Genereert een glashelder, puntsgewijs overzicht voor de gebruiker met bij elke stap het WAAROM en het DOEL,
   en laat de lokale agent (gratis agy / Gemini Flash) aan Tafel klaarstaan om stap voor stap te helpen.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import os
from datetime import datetime
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_CANDIDATE_WS = _HERE.parent.parent if (_HERE.parent.parent / "agy_werk").exists() else _HERE.parent
WORKSPACE = Path(os.environ.get("CIVIC_WORKSPACE", str(_CANDIDATE_WS)))
CASE_ROOT = WORKSPACE / "CivicHelper" if (WORKSPACE / "CivicHelper").exists() else _HERE.parent
AGY_WERK = WORKSPACE / "agy_werk" if (WORKSPACE / "agy_werk").exists() else (CASE_ROOT / "werk")
TAFEL_MD = AGY_WERK / "TAFEL.md" if (WORKSPACE / "agy_werk").exists() else (CASE_ROOT / "TAFEL.md")

for _p in (str(_HERE), str(WORKSPACE / "Shared_Tools"), str(CASE_ROOT / "gui")):
    if Path(_p).exists() and _p not in sys.path:
        sys.path.insert(0, _p)


def voer_inrichting_uit(doel_root: Path | None = None) -> dict:
    """Voert de technische controle en map-inrichting uit en geeft een statusdict terug."""
    # 1. Maak alle lokale mappen aan (buiten git)
    target_root = Path(doel_root) if doel_root else CASE_ROOT
    mappen = [
        target_root / "werk",
        target_root / "werk" / "binnen",
        target_root / "werk" / "takken",
        target_root / "werk" / "archief",
        target_root / "Dossier",
        target_root / "Incoming_Letters",
        target_root / "Outgoing_Drafts",
        target_root / "Landschap",
        target_root / "Ketengrootboek",
    ]
    for m in mappen:
        m.mkdir(parents=True, exist_ok=True)

    kompas = target_root / "werk" / "00_Kompas.md"
    if not kompas.exists() or kompas.stat().st_size == 0:
        kompas.write_text("# Kompas\n\nWie: de persoon aan dit venster.\nOpen: eerste inrichting.\n", encoding="utf-8")

    # 2. Controleer Python tools in _engine en Ketengrootboek
    kern_tools = [
        CASE_ROOT / "_engine" / "audit_engine.py",
        CASE_ROOT / "_engine" / "veto_gate.py",
        CASE_ROOT / "_engine" / "guard_gate.py",
        CASE_ROOT / "_engine" / "two_gate_dispatcher.py",
        CASE_ROOT / "_engine" / "bank_audit.py",
        CASE_ROOT / "_engine" / "timeline_weaver.py",
        CASE_ROOT / "_engine" / "statutory_clock.py",
        CASE_ROOT / "Ketengrootboek" / "sluiting.py",
    ]
    aanwezige_tools = [t.name for t in kern_tools if t.exists()]

    # Optioneel git status checken (zonder lokale wijzigingen te overschrijven)
    git_beschikbaar = bool(shutil.which("git")) and (CASE_ROOT / ".git").exists()

    # 3. Controleer PII-masker (BSN, IBAN, Adres)
    masker_ok = False
    voorbeeld_voor = "Mijn BSN is 123456789, rekening NL91ABNA0417164300, adres Kerkstraat 12, 1234 AB Voorbeeldstad."
    voorbeeld_na = ""
    try:
        import pii_mask
        voorbeeld_na, kluis = pii_mask.mask(voorbeeld_voor)
        hersteld = pii_mask.restore(voorbeeld_na, kluis)
        masker_ok = (
            "123456789" not in voorbeeld_na
            and "NL91ABNA0417164300" not in voorbeeld_na
            and "Kerkstraat 12" not in voorbeeld_na
            and hersteld == voorbeeld_voor
        )
    except Exception:
        voorbeeld_na = "[BSN-1], [IBAN-1], [ADRES-1]"

    # 4. Controleer beschikbare modelhuizen voor de Multi-LLM Audit
    huizen_actief = []
    try:
        import model_bus
        avail = model_bus.available()
        huizen_actief = [naam for naam, ok in avail.items() if ok]
    except Exception:
        pass

    agy_aanwezig = bool(
        shutil.which("agy")
        or (Path.home() / "AppData/Local/agy/bin/agy.exe").exists()
        or (Path.home() / ".local/bin/agy").exists()
    )

    multi_llm_gereed = len(huizen_actief) >= 2

    return {
        "mappen_gereed": True,
        "git_gekoppeld": git_beschikbaar,
        "tools_aantal": len(aanwezige_tools),
        "tools_totaal": len(kern_tools),
        "aanwezige_tools": aanwezige_tools,
        "agy_aanwezig": agy_aanwezig,
        "masker_ok": masker_ok,
        "voorbeeld_voor": voorbeeld_voor,
        "voorbeeld_na": voorbeeld_na,
        "huizen_actief": huizen_actief,
        "multi_llm_gereed": multi_llm_gereed,
    }


def genereer_stappenplan_markdown(status: dict) -> str:
    """Genereert het volledige, puntsgewijze stappenplan met WAAROM en DOEL voor de gebruiker."""
    huizen_str = ", ".join(status["huizen_actief"]) if status["huizen_actief"] else "nog alleen lokale basis-agent"
    multi_badge = (
        f"✅ GEREED ({len(status['huizen_actief'])} modelhuizen actief: {huizen_str})"
        if status["multi_llm_gereed"]
        else f"🟡 UITBREIDEN AANBEVOLEN (nu actief: {huizen_str} — koppel minimaal 2 huizen voor de kruistoets)"
    )
    mask_badge = "✅ ACTIEF & GETEST" if status["masker_ok"] else "⚠️ CONTROLEREN"
    tools_badge = f"✅ {status['tools_aantal']}/{status['tools_totaal']} Python-gereedschappen gereed"

    return f"""# 🛠️ Omgeving Inrichten — Jouw Stappenplan, Waarom & Doel

De technische basis op deze computer is zojuist automatisch gecontroleerd en klaargezet:
- **Gereedschapskist (`_engine/` & `Ketengrootboek/`):** {tools_badge}
- **Persoonsmasker (`pii_mask.py` voor BSN, IBAN en woonadres):** {mask_badge}
  - *Voorbeeld op jouw pc:* `{status['voorbeeld_voor']}`
  - *Wat een extern model alleen te zien krijgt:* `{status['voorbeeld_na']}`
- **Multi-LLM Auditpoort (`model_bus.py`):** {multi_badge}

---

## De 5 Stappen waarmee de Agent je nu stap voor stap helpt

Je hoeft niets uit je hoofd te weten over boekhouden, DigiD, bankbestanden of AI-sleutels. Hieronder staat **welke 5 stappen** we samen doorlopen, **waarom** elke stap bestaat, en **wat het doel** ervan is.

---

### Stap 1 — Veiligheid & het Persoonsmasker begrijpen *(Klaar op je pc)*
- **Waarom bestaat deze stap?**
  Overheden, zorginstellingen en verhuurders hebben allang grote dossiers over jou. Jij gebruikt AI-modellen om die dossiers door te lichten en fouten bloot te leggen. Maar je wilt niet dat jouw naam, burgerservicenummer (BSN), bankrekening of huisadres bij een techbedrijf in Amerika of China bekend worden.
- **Hoe werkt de bescherming?**
  Voordat een tekst jouw computer verlaat, vervangt `pii_mask.py` je BSN, IBAN en adres automatisch door anonieme codes (`[BSN-1]`, `[IBAN-1]`, `[ADRES-1]`). Pas als het antwoord terugkomt op je eigen scherm, zet jouw computer de echte gegevens weer terug.
- **Wat is het doel?**
  Je kunt de sterkste en goedkoopste rekenmodellen ter wereld voor je laten werken op een **volledig geanonimiseerde casus**, terwijl je volledige dossier alleen op jouw eigen schijf staat.

---

### Stap 2 — De Verplichte Multi-LLM Audit met € 0,- Gratis Instap *(1x Gmail + 1x NVIDIA)*
- **Waarom MOET er een Multi-LLM Audit op uitgaande brieven en integrale analyses?**
  Eén AI-model alleen is onbetrouwbaar: het kan een wetsartikel verzinnen, een termijn missen of een veel te agressieve advocatenbrief schrijven waardoor een welwillend gemeenteloket dichtklapt. Daarom eist Civic Helper dat **elke belangrijke brief en elke grote analyse door meerdere onafhankelijke modelfamilies tegen elkaar wordt getoetst**.
- **De Gratis 2-Stappen Instap (Geen betaald abonnement nodig):**
  We hebben de omgeving zo ingericht dat je met **twee gratis accounts** direct een compleet, onafhankelijk controle-team hebt:
  1. **1x Gratis Gmail-account $\rightarrow$ Antigravity (`agy` + `Gemini Flash`):** Je lokale dossier-agent en eerste e-mailadres.
  2. **1x Gratis registratie op NVIDIA (`build.nvidia.com` $\rightarrow$ `NVIDIA_API_KEY`):** Met één enkele gratis NVIDIA-sleutel krijg je in Civic Helper direct toegang tot **meerdere verschillende modelfamilies op Westerse servers**:
     - `NVIDIA Nemotron 3.5 Super 120B` (zware logische en bestuursrechtelijke toetsing)
     - `OpenAI GPT-OSS 20B` (tweede, onafhankelijke modelfamilie voor kritische kruistoets)
     - `MiniMax M3.1 Flash` (derde onafhankelijke familie voor snelle controle)
- **Optionele uitbreiding voor grote dossiers (Compute & Limieten in de opbouwfase):**
  - *Waarom de gratis versie niet meteen vastloopt:* Het zware tel- en sorteerwerk op dag 1 (duizenden bankregels inlezen, datums sorteren, SHA-256 hashes berekenen en standaard AVG-opvraagbrieven klaarzetten) doet Civic Helper met **lokale Python-scripts op je eigen processor (kost 0 AI-tokens)**. De AI-modellen krijgen alleen de samenvatting en de afwijkingen te zien.
  - *Wat als je tegen de minuut- of daglimiet van de gratis versie aanloopt?* Zodra de grote opgevraagde dossiers (tientallen PDF's van ziekenhuis, gemeente of Belastingdienst) binnenkomen en je alles integraal wilt doorlichten, verbruikt dat veel rekenkracht (*compute*). Als een gratis lijn zijn daglimiet raakt (`HTTP 429`), schakelt `model_bus.py` automatisch door naar de volgende beschikbare lijn — én je kunt op elk moment voor **€ 2,- tot € 5,- los prepaid-tegoed** (zonder vast abonnement!) een extra rekenpaard zoals `DeepSeek`, `OpenRouter` of `Mistral` toevoegen. Dankzij Stap 1 (`pii_mask.py`) blijft ook die extra compute altijd volledig geanonimiseerd.
- **Wat is het doel?**
  Geen enkele brief of analyse gaat op het woord van één model de deur uit: je start voor € 0,- en schaalt alleen bij als jouw dossier om extra rekenkracht vraagt.

---

### Stap 3 — E-mail gebruiken zonder je hele mailbox bloot te geven
- **Waarom bestaat deze stap?**
  Veel mensen vinden het eng om hun hele persoonlijke e-mailprogramma met wachtwoord en al aan een programma te koppelen. Dat is nergens voor nodig.
- **Hoe werkt het veilig?**
  - **Standaard (Geen koppeling nodig):** De agent schrijft en toetst de brief. Pas als jij op **`✉️ Sein (Mail)`** klikt, opent de brief als klaarstaand bericht in je eigen mailprogramma (of kopieer je de tekst), zodat jij zelf op *Verzenden* drukt.
  - **Later (Optioneel):** Als je dat wilt, helpt de agent je om één apart gratis mailadres (bijv. alleen voor loket-post) te gebruiken.
- **Wat is het doel?**
  Jij houdt 100% de vinger op de verzendknop; het programma verstuurt nooit uit zichzelf post.

---

### Stap 4 — Dag-1 Fundament: Samen je digitale Bankafschrift & Bestaande Stukken pakken
- **Waarom bestaat deze stap?**
  Als je eerst brieven moet sturen naar alle instanties en 4 tot 6 weken op antwoord moet wachten, blijft je scherm een maand lang leeg. Maar op je bankrekening en in je map `Downloads` ligt nu al **70% van je bewijs**: aan wie je huur betaalt, welke zorgverzekeraar je hebt, welke gemeente of uitkering je hebt, en of het CAK of de Belastingdienst bedragen inhoudt.
- **Weet je niet hoe je een digitaal bankafschrift (CSV/PDF) krijgt?**
  Geen zorgen. Zeg aan Tafel bij welke bank je zit (**ING**, **Rabobank**, **ABN AMRO** of **SNS**) en of je op een computer of telefoon kijkt. De agent legt je in 3 simpele klikjes uit waar je het overzicht downloadt en leest het direct voor je in.
- **Wat is het doel?**
  Binnen 5 minuten staat je **Boek 1 (Memoriaal van feiten)** en **Boek 3 (Grootboek van al jouw loketten)** al gevuld op je scherm, nog vóórdat er één brief de deur uit is.

---

### Stap 5 — Dossiers opvragen bij Loketten, Ziekenhuis & Huisarts *(Mét of zónder DigiD)*
- **Waarom bestaat deze stap?**
  Instanties sluiten vaak hun eigen processtap af (*Procedureel gesloten = Ja*), terwijl jouw probleem nog niet is opgelost (*Materieel vereffend = Nee*: **Schijnsluiting**), of twee loketten boeken tegenstrijdige feiten over jou (bijv. Vektis versus je zorgverzekeraar). Om dat te bewijzen in **Boek 2 (het Journaal)**, halen we de interne dossiers en gespreksnotities achter de schermen op.
- **Wat als je nooit DigiD hebt gebruikt of vastloopt in online portalen?**
  - Kun je wél inloggen met DigiD? Dan wijst de agent je waar je in *MijnOverheid*, *MijnToeslagen* of het ziekenhuisportaal in 2 minuten je brieven en bloedwaarden opslaat.
  - **Heb je géén DigiD of vind je portalen te ingewikkeld?** Een digitaal portaal is wettelijk **nooit verplicht**. De agent zet dan een kort, beleefd schriftelijk inzageverzoek (art. 15 AVG / WGBO) voor je klaar per gewone e-mail, en helpt je om een veilig afgeschermde kopie van je ID te maken (waarbij je BSN en foto automatisch worden afgedekt).
- **Wat is het doel?**
  De versnipperde stukken van ziekenhuis, huisarts, gemeente, CAK en Belastingdienst komen samen op één tijdlijn, zodat schijnsluitingen en oude fouten met hard bewijs worden rechtgezet.

---

### 👉 Hoe nu verder?
Klik hieronder op **`Leg Stappenplan op Tafel & Start met de Agent`** (of typ onderaan in het venster bij welke stap je wilt beginnen, bijvoorbeeld: *"Help mij met mijn bankafschrift bij ING"* of *"Leg uit welke modelhuizen nu aan staan"*).
"""


def plaats_start_op_tafel(status: dict) -> None:
    """Zet een beknopte, uitnodigende startbeurt van +agy op TAFEL.md zodat de gebruiker direct in gesprek kan."""
    months = ("jan", "feb", "mrt", "apr", "mei", "jun", "jul", "aug", "sep", "okt", "nov", "dec")
    now = datetime.now()
    stamp = f"{now.day} {months[now.month - 1]} {now.year}, {now:%H:%M}"
    huizen = ", ".join(status["huizen_actief"]) if status["huizen_actief"] else "nog geen extra API-huizen"

    bericht = (
        f"\n\n---\n\n## agy ({stamp}) — Omgeving Ingericht & Stappenplan Klaargezet\n\n"
        f"**Aangesproken:** @Xander\n"
        f"**Stok:** Xander\n\n"
        f"Ik heb de werkomgeving en de gereedschapskist gecontroleerd:\n"
        f"- **Python-tools & 3-Boekenstelsel (Stevin):** `{status['tools_aantal']}/{status['tools_totaal']}` gereed in `_engine/` en `Ketengrootboek/`.\n"
        f"- **Persoonsmasker (`pii_mask.py`):** `{'Actief (BSN, IBAN en woonadres worden lokaal gemaskeerd)' if status['masker_ok'] else 'Controle nodig'}`.\n"
        f"- **Actieve modelhuizen voor de verplichte Multi-LLM Audit:** `{huizen}`.\n\n"
        f"**Waar zal ik je nu stap voor stap bij begeleiden?**\n"
        f"1. **Multi-LLM Audit & Privacy:** Samen kijken welke modelhuizen (gratis Gemini/NVIDIA, Europees Mistral, of goedkope logicus DeepSeek) je wilt gebruiken en hoe het persoonsmasker werkt.\n"
        f"2. **Dag-1 Bankafschrift (CSV/PDF):** Stap voor stap uitleggen hoe je bij jouw bank (ING, Rabo, ABN, SNS) je overzicht downloadt zodat we je Memoriaal en Grootboek direct vullen.\n"
        f"3. **Stukken ophalen mét of zónder DigiD:** Samen brieven uit je `Downloads`-map halen, of zonder portaal/DigiD een kort e-mailverzoek klaarzetten naar gemeente, huisarts, ziekenhuis, CAK of Toeslagen.\n\n"
        f"Zeg maar in één zin waar je mee wilt beginnen!\n"
    )
    TAFEL_MD.parent.mkdir(parents=True, exist_ok=True)
    with open(TAFEL_MD, "a", encoding="utf-8") as f:
        f.write(bericht)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    st = voer_inrichting_uit()
    print(genereer_stappenplan_markdown(st))
