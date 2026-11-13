# Mathematische Brief-Generator & Dynamica van het Repair Budget (Schets v0.1)

> **Status:** Eerste formele schets.  
> **Auteur:** Xander Dupont / Agy aan De Tafel.  
> **Kernprincipe:** Een uitgaand bericht naar een instantie is geen subjectief literair product van een taalmodel, maar de unieke oplossing van een dynamisch variationeel optimalisatieprobleem onder strikte budget- en capaciteitsrandvoorwaarden over de tijd ($M^*$-synthese).

---

## 1. Toestandsruimte: De Ketenfout-Vector $\vec{\mathcal{E}}(t)$

Laat $\mathcal{H}$ de Hilbertruimte van het integrale burgerdossier zijn. Op tijdstip $t$ wordt de toestand gekarakteriseerd door de foutvector:

$$\vec{\mathcal{E}}(t) = \vec{X}_{\text{norm}}(t) - \vec{X}_{\text{actueel}}(t) \in \mathcal{H}$$

waarbij $\vec{\mathcal{E}}(t) = (\mathcal{E}_1, \mathcal{E}_2, \dots, \mathcal{E}_N)^T$ alle openstaande materiële, registratieve en procedurele breuken omvat (bijv. ontbrekende toeslagen, zwevende beslagafdrachten, onjuiste registraties in landelijke systemen).

Elke breuk $\mathcal{E}_i$ heeft een intrinsieke herstelenergie (repair work) $W(\mathcal{E}_i) \ge 0$ die nodig is om de post te vereffenen in het Ketengrootboek.

---

## 2. Tweezijdige Verwerkingscapaciteiten over Langere Termijn

Zowel de burger als het aangesproken loket $k$ beschikken over een dynamische verwerkingscapaciteit over de tijdhorizon $t \in [0, T]$:

### 2.1 Burgercapaciteit $C_{\text{cit}}(t)$ (Energetisch & Cognitief Budget)
$$C_{\text{cit}}(t) = C_{\text{base}} \cdot e^{-\lambda_{\text{stress}} t} + R_{\text{regen}}(t) - \sum_{j} \text{Load}_j(t)$$
- $\lambda_{\text{stress}}$: vervalfactor door bureaucratisch conflict en acute bestaansonzekerheid.
- $R_{\text{regen}}(t)$: herstelfactor door procedurele rust, voorspelbaarheid en ontlasting.
- Bij een geobjectiveerde medische functiebeperking of chronische uitputting is $C_{\text{cit}}(t)$ een harde biologische bovengrens.

### 2.2 Institutionele Loketcapaciteit $C_{\text{inst}}(L_k, t)$ (Ambtelijke Bandbreedte)
Voor een loket $L_k$ geldt:
$$C_{\text{inst}}(L_k, t) = \mu_k(t) \cdot \eta(L_k)$$
- $\mu_k$: basis-verwerkingssnelheid van het loket (bijv. 5 tot 10 minuten per ticket).
- $\eta(L_k) \in [0, 1]$: de **mandaatfactor** van de functionaris.
  - Uitvoerend inkomensconsulent / balie: $\eta \approx 0.05$ (geen bevoegdheid tot stelselwijziging of juridische herziening).
  - Coördinator / Team Minima: $\eta \approx 0.3$.
  - Functionaris Gegevensbescherming (FG) / Bezwaarjurist: $\eta \approx 0.8$.

---

## 3. Het Dynamische Repair Budget $B_{\text{repair}}(L_k, t, \Delta t)$

Het totale herstel van $\vec{\mathcal{E}}(t)$ kan nooit instantaan plaatsvinden ($\sum_i W(\mathcal{E}_i) \gg C_{\text{inst}} + C_{\text{cit}}$). Het herstelbudget over een discreet tijdsinterval $\Delta t$ is begrensd door het minimum van beide verwerkingsstromen:

$$B_{\text{repair}}(L_k, t, \Delta t) = \min \left( \int_{t}^{t+\Delta t} C_{\text{cit}}(\tau) \, d\tau, \;\; \int_{t}^{t+\Delta t} C_{\text{inst}}(L_k, \tau) \, d\tau \right)$$

Overschrijding van $B_{\text{repair}}$ in een enkele communicatiestap induceert instabiliteit en administratieve afweer.

---

## 4. De Frictie-Functional $\Phi(M, t)$

Elk uitgaand bericht $M$ induceert een systeemfrictie $\Phi(M, t)$:

$$\Phi(M, t) = \alpha \cdot \left[ \max\left(0, W_{\text{inst}}(M) - C_{\text{inst}}(L_k, t)\right) \right]^2 + \beta \cdot \|\vec{M} - \Pi_{\mathcal{V}_k}(\vec{M})\|^2 + \gamma \cdot P_{\text{rejection}}(M) + \delta \cdot W_{\text{cit}}(M)$$

waarbij:
1. $\alpha$-term: kwadratische bestraffing van ambtelijke overbelasting (overschrijding van het tijdsbudget van de ambtenaar leidt tot irritatie en formele blokkade).
2. $\beta$-term: bestraffing van **cross-domein besmetting** (projectie buiten de bevoegdheidsruimte $\mathcal{V}_k$).
3. $\gamma$-term: risico op formele afwijzing of doorverwijzing naar een gesloten loket.
4. $\delta$-term: belasting van de burger.

---

## 5. De Generatieve Formule voor het Optimale Bericht $M^*(t)$

Het te verzenden bericht $M^*(t)$ is het unieke argument dat de cumulatieve frictie en residuele ketenschuld minimaliseert over horizon $T$:

$$M^*(t) = \arg\min_{M} \int_{0}^{T} \left( \Phi(M(\tau), \tau) + \lambda \cdot \|\vec{\mathcal{E}}(\tau)\|^2 \right) d\tau$$

onderworpen aan de dwingende randvoorwaarden:

$$\begin{cases}
1. \quad W_{\text{inst}}(M^*) \le B_{\text{repair}}(L_k, t, \Delta t) & \text{(Capaciteitsbewaking over de termijn)} \\
2. \quad \Pi_{\mathcal{V}_j}(M^*) = 0 \quad \forall j \ne k & \text{(Orthogonaliteit: nul cross-domein lekken)} \\
3. \quad \frac{d}{dt} \|\vec{\mathcal{E}}(t)\| < 0 & \text{(Monotone reductie van ketenfouten)} \\
4. \quad W_{\text{cit}}(M^*) \le C_{\text{cit}}(t) & \text{(Bescherming van de biologische burgerkracht)}
\end{cases}$$

---

## 6. Operationele Parameter-Mapping (Van Wiskunde naar Brieftekst)

De wiskundige extremum-oplossing $M^*$ legt de fysieke structuur van de uitgaande brief deterministisch vast:

| Parameter in Formule | Fysieke Eigenschap van de Brief | Rekenregel / Gedrag |
|---|---|---|
| **Lengte $L(M^*)$** | Aantal woorden / tokens | $L(M^*) = \kappa_1 \cdot C_{\text{inst}}(L_k, t)$. Lage ambtelijke capaciteit $\implies$ strikt korte brief (max 50–100 woorden). |
| **Actie-Ariteit $\|A(M^*)\|$** | Aantal verzoeken per brief | $\|A(M^*)\| = \lfloor B_{\text{repair}} / W_{\text{atomic}} \rfloor \equiv 1$. Slechts één enkelvoudige handeling per beurt. |
| **Ontologisch Filter $\mathcal{M}_k$** | Toegestane woordenschat | $\operatorname{Vocab}(M^*) \subseteq \mathcal{V}_k$. Termen van andere instanties worden gemaskeerd met gewicht $\infty$. |
| **Termijn $\Delta t^*$** | Tick van de procedurele klok | $\Delta t^* = \tau_{\text{statutory}}(M^*)$. Kiest het langste wettelijke rustinterval (bijv. 8 weken Awb of 4 weken AVG) ter maximalisatie van $R_{\text{regen}}$. |
| **Entropie-Reductie $H \to 0$** | Vaste scalar verwijzingen | Context wordt uitsluitend als scalar kenmerk meegegeven (*"reeds bij u bekend onder nr X"*), waardoor ambtelijke zoektijd naar nul daalt. |

---

*Vastgelegd aan De Tafel ter verdere executable uitwerking in de Civic Engine.*
