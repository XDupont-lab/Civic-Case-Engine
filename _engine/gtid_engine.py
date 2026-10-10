#!/usr/bin/env python3
"""
CIVIC CASE ENGINE — G-TID INSTITUTIONAL FIELD ENGINE (v1.0)
Pure Python Standard Library (Zero External Dependencies).

Gebaseerd op:
General Theory of Institutional Dynamics (G-TID) & Triadisch Resonantie Framework (TRF).

Kernstelling:
Instituten zijn geen monolithische objecten of statische vijanden, maar DYNAMISCHE VELDEN:
    I = { w, Psi_res, Delta_lambda, theta, T_H, GU_ext, GU_int }

De 'Hack':
Binnen een bureaucratisch instituut is de individuele uitvoerder (Wmo-consulent, klantmanager,
wijkverpleegkundige) vaak zélf gevangen in een lage-agency val (w_ambt -> 0) door zaaksystemen
(Gws4all/Socrates), afvinkprotocollen en angst voor berisping van kwaliteitsmedewerkers.

Door de ambtenaar te voorzien van een kant-en-klare, juridisch gedekte
'AMBTELIJKE BESLUITRECHTVAARDIGING' verhogen we hun eigen agency (w_ambt ^).
Hierdoor transformeert de ambtelijke frictie in een resonante bondgenootschap (Psi_res > 0).
"""

import os
import sys
import json
import re
from pathlib import Path

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

ENGINE_DIR = Path(__file__).resolve().parent
ROOT_DIR = ENGINE_DIR.parent

class InstitutionalField:
    """Modelleert een institutioneel veld conform G-TID."""
    
    def __init__(self, entity_name, w_citizen=0.4, w_official=0.2, 
                 delta_lambda=2, t_h=0.3, theta=0.2, 
                 gu_ext=None, gu_int=None):
        self.entity_name = entity_name
        self.w_citizen = max(0.0, min(1.0, float(w_citizen)))
        self.w_official = max(0.0, min(1.0, float(w_official)))
        self.delta_lambda = max(1, int(delta_lambda))  # 1 (direct) tot 5 (diep bureaucratisch doof)
        self.t_h = max(0.0, min(1.0, float(t_h)))     # Harmonische temperatuur (tolerantie/maatwerk)
        self.theta = max(0.0, min(1.0, float(theta))) # Holonomisch geheugen / bias / frictiehistorie
        self.gu_ext = gu_ext or ["Awb", "Wmo 2015", "AVG"]
        self.gu_int = gu_int or ["Zorgbehoefte", "Beroepsethiek", "Leefbaarheid"]

    @property
    def psi_res(self) -> float:
        """
        Resonantie-intensiteit Psi_res:
        Meet de mate waarin interne beroepslogica (GU_int) en formele orde (GU_ext)
        synchroon kunnen lopen, gecorrigeerd voor scheidingskloven (Delta_lambda) en bias (theta).
        """
        base_pot = (self.w_official * 0.6) + (self.t_h * 0.4)
        friction = (0.12 * (self.delta_lambda - 1)) + (0.35 * self.theta)
        return round(base_pot - friction, 3)

    @property
    def material_legitimacy(self) -> float:
        """
        Materiële legitimiteit L = integral(Psi_res * w_citizen).
        Formele legitimiteit (GU_ext) kan 100% zijn terwijl L < 0 is.
        """
        effective_res = max(0.0, self.psi_res)
        return round(effective_res * self.w_citizen, 3)

    @property
    def regime(self) -> str:
        """Bepaalt de fasetoestand van het veld."""
        if self.t_h <= 0.15 and self.delta_lambda >= 4 and self.theta >= 0.5:
            return "BIFURCATIE_RISICO" # Systeem zit vast in zero-tolerance; dreigt te breken
        elif self.psi_res <= 0.05 or self.w_official < 0.20 or self.delta_lambda >= 3:
            return "MECHANISCHE_ORDE"  # Lage agency, hoge impedantie, ambtelijke protocol-klem
        elif self.psi_res >= 0.35 and self.w_official >= 0.30:
            return "HARMONISCHE_ORDE"  # Ruimte voor partnerschap en maatwerk
        else:
            return "VELD_TRANSITIE"    # Kantelpunt; interventie kan het systeem beide kanten op duwen

    @property
    def recommended_operator(self) -> str:
        """Selecteert de optimale cybernetische operator voor het burger-exoskelet."""
        r = self.regime
        if r == "BIFURCATIE_RISICO" or self.delta_lambda >= 4:
            return "SCHAAL_BYPASS_POLITIEK" # Ambtelijke keten is doof; spring naar Raad (art. 41 RvO) of Rechter
        elif r == "MECHANISCHE_ORDE":
            if self.w_official < 0.2:
                return "SAAIE_SONDE"       # Pure Awb/AVG dwangsomklok; appelleren aan rede faalt
            else:
                return "AGENCY_HACK_AMBTENAAR" # Geef de ambtenaar de rugdekking om ja te zeggen!
        elif r == "HARMONISCHE_ORDE":
            return "VELVET_GLOVE"          # Hoffelijk, coöperatief, inhoudelijk
        else:
            return "AGENCY_HACK_AMBTENAAR"

    def diagnose_summary(self) -> dict:
        return {
            "entity": self.entity_name,
            "regime": self.regime,
            "operator": self.recommended_operator,
            "w_citizen": self.w_citizen,
            "w_official": self.w_official,
            "delta_lambda": self.delta_lambda,
            "t_h": self.t_h,
            "theta": self.theta,
            "psi_res": self.psi_res,
            "material_legitimacy": self.material_legitimacy,
            "rationale": self._get_rationale()
        }

    def _get_rationale(self) -> str:
        r = self.regime
        if r == "MECHANISCHE_ORDE":
            return (f"Het orgaan opereert in Mechanische Orde (Psi_res={self.psi_res}). "
                    f"Ambtenaar heeft gering mandaat (w={self.w_official}) en impedantie is hoog (dL={self.delta_lambda}). "
                    f"Emotie of informeel overleg leidt tot uitputting. Vereist strakke formele kaders of kant-en-klare zaaksysteem-motivering.")
        elif r == "BIFURCATIE_RISICO":
            return (f"Kritieke systeemklem (T_H={self.t_h}, dL={self.delta_lambda}). "
                    f"Het orgaan tolereert geen uitzonderingen en is doof voor signalen van beneden. "
                    f"Aanbevolen actie: Schaal-bypass naar politiek/griffie (art. 41 RvO) of formele dwangsom.")
        elif r == "HARMONISCHE_ORDE":
            return (f"Gunstige veldconfiguratie (Psi_res={self.psi_res}). Ambtenaar bezit maatwerkruimte. "
                    f"Coöperatieve 'Velvet Glove' aanpak maximaliseert resultaat zonder onnodige juridische strijd.")
        else:
            return (f"Overgangsregime. Bied de behandelend professional direct ambtelijke rugdekking "
                    f"om het besluit in zijn/haar zaaksysteem te verankeren.")

    def generate_ambtelijke_besluitrechtvaardiging(self, subject="Maatwerkvoorziening Wmo", 
                                                  grounds=None, risks_averted=None) -> str:
        """
        DE KERN-HACK:
        Genereert een pasklare 'Besluitrechtvaardiging' die de ambtenaar zó in
        Gws4all / Socrates kan plakken. Hiermee verhogen we w_official.
        """
        grounds_list = grounds or [
            "Art. 2.3.5 lid 3 Wmo 2015 (dwingende plicht tot passende bijdrage aan zelfredzaamheid)",
            "Art. 3:4 lid 2 Awb (evenredigheidsbeginsel: nadelige gevolgen mogen niet onevenredig zijn)",
            "Art. 19 VN-verdrag Handicap (recht op zelfstandig leven en inclusie in de maatschappij)",
            "Medische objectivering conform Stuk 74 / ZorgDomein overdracht"
        ]
        
        risks_list = risks_averted or [
            "Voorkomt formele ingebrekestelling en dwangsom wegens niet tijdig beslissen (art. 4:17 Awb)",
            "Voorkomt gegrond bezwaarschrift met ambtelijke proceskostenveroordeling (art. 7:15 Awb)",
            "Voorkomt escalatie via politieke vragen gemeenteraad (art. 41 RvO Westerwolde)",
            "Elimineert aansprakelijkheid van het college voor acute zorgval en woningonleefbaarheid"
        ]

        text = []
        text.append(f"### 🏛️ G-TID AMBTELIJKE BESLUITRECHTVAARDIGING — INTERNE DOSSIERNOTITIE")
        text.append(f"*Opgesteld ten behoeve van behandelend consulent / regisseur bij: {self.entity_name}*")
        text.append(f"*Doel: Directe invoer in zaaksysteem (Gws4all / Socrates) ter ambtelijke en juridische dekking.*")
        text.append("")
        text.append(f"#### 1. Zaaksaanduiding & Onderwerp")
        text.append(f"- **Onderwerp:** {subject}")
        text.append(f"- **Veldstatus:** {self.regime} (Operator: {self.recommended_operator})")
        text.append(f"- **Materiële Legitimiteitsindex:** L = {self.material_legitimacy} / 1.0")
        text.append("")
        text.append(f"#### 2. Formele Grondslagen (Wettelijke Dekking)")
        for g in grounds_list:
            text.append(f"- {g}")
        text.append("")
        text.append(f"#### 3. Toetsing Evenredigheid & Bevoegdheid (Art. 3:4 Awb)")
        text.append(f"Toepassing van een generiek urenplafond of rigide afwijzingssjabloon is in casu strijdig met de ")
        text.append(f"doelstelling van de wet. Door toekenning van de gevraagde ondersteuning wordt voldaan aan de ")
        text.append(f"wettelijke compensatieplicht, terwijl het college handelt binnen zijn beleidsdiscretie.")
        text.append("")
        text.append(f"#### 4. Risico-analyse voor het Bestuursorgaan (Afgewende Systeemschade)")
        text.append(f"Met deze toewijzing borgt het orgaan rechtszekerheid en worden de volgende escalaties geneutraliseerd:")
        for r in risks_list:
            text.append(f"- [x] {r}")
        text.append("")
        text.append(f"#### 5. Concept-Besluittekst (Gereed voor Overname in Beschikking)")
        text.append(f"> \"Het college van burgemeester en wethouders van {self.entity_name} besluit, gelet op artikel 2.3.5 lid 3 ")
        text.append(f"> van de Wet maatschappelijke ondersteuning 2015 en artikel 3:4 van de Algemene wet bestuursrecht, ")
        text.append(f"> aan betrokkene de geïndiceerde maatwerkvoorziening toe te kennen. Uit de overgelegde objectiveerbare ")
        text.append(f"> feiten blijkt genoegzaam dat de voorziening noodzakelijk is ter waarborging van de zelfredzaamheid.\"")
        text.append("")
        text.append(f"---")
        text.append(f"*Advies: Toevoegen aan het fysieke zaaksysteem ter afsluiting van het dossier.*")
        
        return "\n".join(text)


def inspect_incoming_letter_for_gtid(letter_text: str) -> InstitutionalField:
    """
    Scant een inkomende ambtelijke brief of afwijzing en leidt de G-TID veldparameters af.
    """
    text_lower = letter_text.lower()
    
    # Bepaal entiteit
    entity = "Onbekend Bestuursorgaan"
    if "westerwolde" in text_lower:
        entity = "Gemeente Westerwolde"
    elif "oldambt" in text_lower:
        entity = "Gemeente Oldambt"
    elif "menzis" in text_lower:
        entity = "Menzis Zorgverzekeraar"
    elif "groninger huis" in text_lower or "huur" in text_lower:
        entity = "Woningcorporatie Groninger Huis"
    elif "uwv" in text_lower:
        entity = "Uitvoeringsinstituut Werknemersverzekeringen (UWV)"

    # Delta lambda: lagen / afstand
    delta_lambda = 2
    if any(k in text_lower for k in ["juridische zaken", "bezwaarschriftencommissie", "directeur", "college van b&w"]):
        delta_lambda = 3
    if any(k in text_lower for k in ["klantenservice", "callcenter", "afdeling verwerking", "postbus"]):
        delta_lambda = 4

    # Harmonische temperatuur T_H: zero-tolerance vs maatwerk
    t_h = 0.3
    if any(k in text_lower for k in ["onverbiddelijk", "strikte voorwaarde", "niet mogelijk", "geen uitzondering", "afgewezen"]):
        t_h = 0.1
    elif any(k in text_lower for k in ["in overleg", "maatwerk", "bijzondere omstandigheden", "coulance"]):
        t_h = 0.6

    # Ambtenaar agency w_official
    w_official = 0.2
    if any(k in text_lower for k in ["het systeem laat niet toe", "productcode", "standaardprocedure", "computer"]):
        w_official = 0.1
    elif any(k in text_lower for k in ["ik heb besloten", "in overleg met u", "ik kan toezeggen", "aangeboden"]):
        w_official = 0.45

    # Holonomisch geheugen / bias theta
    theta = 0.2
    if any(k in text_lower for k in ["herhaaldelijk", "reeds eerder medegedeeld", "bekend standpunt", "dossierhistorie"]):
        theta = 0.6

    return InstitutionalField(
        entity_name=entity,
        w_citizen=0.45,
        w_official=w_official,
        delta_lambda=delta_lambda,
        t_h=t_h,
        theta=theta
    )


def main():
    print("=" * 72)
    print("   🏛️  CIVIC CASE ENGINE — G-TID INSTITUTIONAL FIELD DIAGNOSTICS")
    print("=" * 72)
    print()

    # Zoek naar recente inkomende brief of concept in Outgoing_Drafts
    incoming_dir = ROOT_DIR / "Incoming_Letters"
    recent_files = sorted(incoming_dir.glob("*.eml")) + sorted(incoming_dir.glob("*.txt")) + sorted(incoming_dir.glob("*.md"))
    
    sample_text = ""
    target_entity = "Gemeente Westerwolde (Sociaal Domein)"
    
    if recent_files:
        latest = recent_files[-1]
        print(f"[*] Analyseren van recent ontvangen stuk: {latest.name}")
        try:
            with open(latest, "r", encoding="utf-8", errors="ignore") as f:
                sample_text = f.read()
        except Exception:
            pass

    if sample_text:
        field = inspect_incoming_letter_for_gtid(sample_text)
    else:
        # Default Wmo veldconfiguratie
        field = InstitutionalField(
            entity_name=target_entity,
            w_citizen=0.45,
            w_official=0.20,
            delta_lambda=3,
            t_h=0.20,
            theta=0.40
        )

    diag = field.diagnose_summary()
    print(f"\n[+] Entiteit:              {diag['entity']}")
    print(f"[+] G-TID Veldregime:      {diag['regime']}")
    print(f"[+] Aanbevolen Operator:   {diag['operator']}")
    print(f"[+] Resonantie (Psi_res):  {diag['psi_res']}")
    print(f"[+] Materiële Legitimiteit (L): {diag['material_legitimacy']}")
    print(f"[+] Impedantielagen (dL):  {diag['delta_lambda']}")
    print(f"[+] Ambtenaar Agency (w):  {diag['w_official']}")
    print(f"\n[+] Diagnose-analyse:")
    print(f"    {diag['rationale']}\n")

    # Genereer de ambtelijke besluitrechtvaardiging (De Hack)
    print("-" * 72)
    hack = field.generate_ambtelijke_besluitrechtvaardiging()
    print(hack)
    print("-" * 72)

    # Optioneel opslaan in Outgoing_Drafts
    out_path = ROOT_DIR / "Outgoing_Drafts" / "G_TID_BESLUITRECHTVAARDIGING_AMBTENAAR.md"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(hack)
    print(f"\n[✓] Besluitrechtvaardiging opgeslagen als: {out_path.name}")


if __name__ == "__main__":
    main()
