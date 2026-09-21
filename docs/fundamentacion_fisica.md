# Investigación del fenómeno y fundamentación física

Documento correspondiente a la **primera etapa** del parcial: comprender el fenómeno, magnitudes, unidades, origen de los datos y pregunta científica.

---

## 1. Fenómeno estudiado

Se estudia la **estabilidad e inestabilidad de los núcleos atómicos** en el chart of nuclides: cómo la composición $N$ (neutrones) y $Z$ (protones) determina si un nuclido es estable o radiactivo, y por qué canal decae ($\beta^-$, captura electrónica / $\beta^+$, $\alpha$, etc.).

El eje empírico es el **valle de estabilidad**: región del plano $(N,Z)$ donde la energía de enlace por nucleón es máxima (o la vida media es muy larga). Fuera del valle, el núcleo tiende a transformar nucleones o emitir partículas hasta acercarse a esa región.

## 2. Fundamento físico (resumen)

- Un núcleo se describe por $Z$, $N$ y $A = Z + N$.
- La **energía de enlace** $B$ mide cuánta energía hay que aportar para separar el núcleo en nucleones libres; suele reportarse como **BE/A** ($B/A$).
- El **modelo de gota líquida (LDM)** aproxima $B$ con términos de volumen, superficie, Coulomb, asimetría y apareamiento. El residual **(BE − LDM)/A** indica desviaciones (capas, deformación).
- Si el núcleo hijo tiene menor masa (mayor enlace), el canal está abierto: la diferencia de masa es la **energía Q** del proceso.
  - $\beta^-$: $n \rightarrow p + e^- + \bar{\nu}_e$; típico de núcleos ricos en neutrones (alto $N/Z$).
  - EC / $\beta^+$: conversión $p \rightarrow n$; típico de núcleos deficientes en neutrones (bajo $N/Z$).
  - $\alpha$: emisión de $^4\mathrm{He}$; frecuente en $Z$ altos.
- La **vida media** $t_{1/2}$ cuantifica la tasa de decaimiento. En $\beta$ (teoría de Fermi), a mayor energía disponible (mayor $Q$), en promedio decaimientos más rápidos (vidas más cortas), con gran dispersión por estructura nuclear.

## 3. Magnitudes involucradas y unidades

| Magnitud | Símbolo | Unidad habitual en NuDat | Rol |
|----------|---------|--------------------------|-----|
| Número atómico | $Z$ | adimensional | protones |
| Número de neutrones | $N$ | adimensional | neutrones |
| Número másico | $A$ | adimensional | $Z+N$ |
| Razón neutrón/protón | $N/Z$ | adimensional | posición respecto al valle |
| Vida media | $t_{1/2}$ | s, ms, min, h, d, y (aquí unificada a **s**) | estabilidad temporal |
| Modo de decaimiento | — | categórico (+ % branching) | canal dominante |
| Exceso de masa | $\Delta$ | keV | masas nucleares |
| Energías Q | $Q_{\beta^-}$, $Q_{\mathrm{EC}}$, $Q_{\beta^+}$, $Q_{\alpha}$ | keV | apertura y “fuerza” del canal |
| BE/A | $B/A$ | keV | profundidad del valle |
| Residual LDM | (BE−LDM)/A | keV | desviación respecto a gota líquida |
| Pairing gap | — | keV | efecto even–odd / apareamiento |
| Espín-paridad | $J^{\pi}$ | — | estado cuántico del nivel |
| Energía de nivel | $E$ | keV / MeV | base vs isómero |

## 4. Cómo se “producen” estos datos (no son un telescopio)

NuDat **no** es un experimento único: es un **portal de datos evaluados** del NNDC (Brookhaven). Los valores llegan de mediciones en laboratorios (espectrometría $\gamma$, trampas de Penning, tiempo de vuelo, decaimiento $\beta/\alpha$, etc.) y se **evalúan y compilan** en bases oficiales que NuDat redistribuye.

Según el [User Guide — Data Sources](https://www.nndc.bnl.gov/nudat3/guide/#sources):

> *The data used within NuDat is obtained and derived from a variety of trusted sources.*

### Nuclear Wallet Cards

Interfaz de búsqueda: [Nuclear Wallet Cards Search](https://www.nndc.bnl.gov/nudat3/indx_sigma.jsp)

- Half-life  
- Decay Mode  
- Ground and Isomeric State Information Table  
- Level Energy  
- $J^{\pi}$

### ENSDF (Evaluated Nuclear Structure Data File)

Estructura y excitación (en NuDat completo; **no son el eje** de este proyecto):  
$E(2^+)$, $E(4^+)$, $E(3^-)$, $E(4^+)/E(2^+)$, $\beta_2$, $B(E2;4\rightarrow 2)/B(E2;2\rightarrow 0)$, …

### Atomic Mass Evaluation 2020 (M. Wang et al.)

Artículo: [Chinese Physics C — AME 2020](https://iopscience.iop.org/article/10.1088/1674-1137/abddaf) ([DOI](https://doi.org/10.1088/1674-1137/abddaf))

Masas y cantidades derivadas:  
Mass Excess, $Q_{\beta^-}$, $Q_{\mathrm{EC}}$, $Q_{\beta^+}$, $S_n$, $S_p$, $Q_{\alpha}$, $\Delta Q_{\alpha}$, $Q_{2\beta^-}$, $Q_{2\mathrm{EC}}$, $Q_{\mathrm{ECp}}$, $Q_{\beta^- n}$, BE/A, BE−LDM fit, pairing gap.

Parámetros LDM usados en NuDat (Bertsch et al., citados en el User Guide): volumen 15.74063 MeV, superficie 17.61628 MeV, simetría 23.42742 MeV, Coulomb 0.71544 MeV, pairing 12.59898 MeV.

### ENDF/B-VII.1

Secciones y rendimientos de fisión (tampoco eje de este proyecto):  
$\sigma(n,\gamma)$, $\sigma(n,F)$, FY de $^{235}\mathrm{U}$, $^{239}\mathrm{Pu}$, $^{252}\mathrm{Cf}$, …

**Puerta de acceso usada:** [NuDat 3](https://www.nndc.bnl.gov/nudat3/).  
Detalle de archivos CSV y variables exportadas: [`origen_datos.md`](origen_datos.md).

## 5. Conjunto de datos de este proyecto (características)

| Aspecto | Valor |
|---------|--------|
| Interfaz | NuDat 3 — Wallet Cards + Chart Export |
| Fecha de descarga | 2026-09-20 |
| Registros Wallet | ~4116 (estados base + isómeros) |
| Registros Chart (por export) | ~3150–4105 nuclidos $(Z,N)$ |
| Naturaleza temporal | Snapshot evaluado (no serie de tiempo) |
| Variables centrales aquí | $Z$, $N$, $A$, modos, $t_{1/2}$, $Q_{\beta^-}$ / $Q_{\mathrm{EC}}$ / $Q_{\beta^+}$, BE/A, residual LDM, pairing, $Q_{\alpha}$ |

## 6. Significado físico de las variables que sí usamos

- **$N/Z$**: ubicada al lado rico en neutrones o en protones del valle; predice cualitativamente $\beta^-$ vs EC/$\beta^+$.  
- **Decay Mode / branching**: canal(es) observados y su fracción.  
- **Half-life**: escala temporal del decaimiento; `STABLE` ≈ no se observa decaimiento en escalas geológicas/experimentales relevantes.  
- **$Q_{\beta^-}$, $Q_{\mathrm{EC}}$, $Q_{\beta^+}$** (AME): energía disponible; correlacionan (ruidosamente) con $\log t_{1/2}$.  
- **BE/A y BE−LDM**: mapa del valle; estables suelen concentrarse cerca del máximo de BE/A.  
- **Pairing gap**: contribución de apareamiento (even–even más ligados).  
- **Mass excess**: base de las Q; también en Wallet Cards.  
- **Level Energy / $J^{\pi}$**: distinguen estado base vs isómero.

## 7. Pregunta científica del proyecto

> ¿Cómo evoluciona la razón $N/Z$ frente al modo de desintegración dominante ($\beta^-$ frente a $\beta^+$/EC), cuál es la correlación entre la energía de decaimiento ($Q_{\beta^-}$, $Q_{\mathrm{EC}}$) y la vida media observada, y cómo se sitúa ese comportamiento respecto al valle de estabilidad medido por BE/A y el residual respecto al modelo de gota líquida?

Esta pregunta orienta limpieza, modelo relacional, consultas SQL y visualizaciones.

## 8. Referencias de acceso (enlaces)

| Recurso | URL |
|---------|-----|
| NuDat 3 (portal) | https://www.nndc.bnl.gov/nudat3/ |
| User Guide — **Data Sources** | https://www.nndc.bnl.gov/nudat3/guide/#sources |
| Nuclear Wallet Cards Search | https://www.nndc.bnl.gov/nudat3/indx_sigma.jsp |
| AME 2020 (Wang et al., *Chinese Physics C*) | https://iopscience.iop.org/article/10.1088/1674-1137/abddaf |
| DOI AME 2020 | https://doi.org/10.1088/1674-1137/abddaf |
| ENSDF | https://www.nndc.bnl.gov/ensdf/ |
| ENDF | https://www.nndc.bnl.gov/endf/ |

La sección [Data Sources del User Guide](https://www.nndc.bnl.gov/nudat3/guide/#sources) es la referencia oficial del mapa Wallet Cards / ENSDF / AME 2020 / ENDF descrito en la sección 4.
