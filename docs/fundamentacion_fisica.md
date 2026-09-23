# Investigación del fenómeno y fundamentación física

Documento correspondiente a la **primera etapa** del parcial: comprender el fenómeno, magnitudes, unidades, origen de los datos y pregunta científica.

---

## 1. Fenómeno estudiado

Se estudia cómo la composición $N$ (neutrones) y $Z$ (protones) de un núcleo determina el **modo de desintegración dominante** en el chart of nuclides: $\beta^-$ frente a captura electrónica / $\beta^+$, con los estables como referencia.

El **valle de estabilidad** —franja del plano $(N,Z)$ donde los núcleos son estables o de vida muy larga— motiva la predicción: lejos del valle hacia neutrones ricos se espera $\beta^-$; hacia deficientes en neutrones, EC/$\beta^+$.

## 2. Fundamento físico

- Un núcleo se describe por $Z$, $N$ y $A = Z + N$. La razón **$N/Z$** resume si hay exceso o déficit de neutrones.
- $\beta^-$ ($n \rightarrow p + e^- + \bar{\nu}_e$): típico de núcleos ricos en neutrones (alto $N/Z$).
- EC / $\beta^+$ (conversión $p \rightarrow n$): típico de núcleos deficientes en neutrones (bajo $N/Z$).
- $\alpha$ (emisión de $^4\mathrm{He}$) aparece sobre todo a $Z$ altos; aquí se registra como clase aparte.
- **Coulomb:** la repulsión entre protones crece ~$Z(Z-1)/A^{1/3}$ (término del modelo de gota líquida). Por eso, a $Z$ mayores, el valle exige un $N/Z$ más alto. NuDat no exporta esa energía como columna; se puede **estimar** a partir de $Z$ y $A$.
- La **vida media** $t_{1/2}$ y la etiqueta `STABLE` identifican el fondo del valle; el análisis cuantitativo de la pregunta usa $N/Z$ y el modo dominante en **estado base**.

## 3. Magnitudes involucradas y unidades

| Magnitud | Símbolo | Unidad | Rol |
|----------|---------|--------|-----|
| Número atómico | $Z$ | adimensional | protones; bins de frontera |
| Número de neutrones | $N$ | adimensional | neutrones; chart $N$–$Z$ |
| Número másico | $A$ | adimensional | $Z+N$ |
| Razón neutrón/protón | $N/Z$ | adimensional | predictor del modo |
| Factor Coulomb (LDM) | $Z(Z-1)/A^{1/3}$ | adimensional (× ~0.7 MeV) | estimado desde $Z$, $A$ |
| Modo dominante | — | categórico | `B-`, `EC_BP`, `STABLE`, … |
| Vida media | $t_{1/2}$ | **s** (unificada) | flag `STABLE` / contexto |
| Energía de nivel | $E$ | keV | base (`level_index=0`) vs isómero |
| Espín-paridad | $J^{\pi}$ | — | identidad del estado |

## 4. Origen de los datos

NuDat **no** es un experimento único: es un **portal de datos evaluados** del NNDC (Brookhaven). Los valores llegan de mediciones en laboratorios y se evalúan/compilan en bases oficiales que NuDat redistribuye ([User Guide — Data Sources](https://www.nndc.bnl.gov/nudat3/guide/#sources)).

Este proyecto usa:

- **Nuclear Wallet Cards** — modos de decaimiento, estados base/isómeros, $t_{1/2}$, mass excess ([búsqueda](https://www.nndc.bnl.gov/nudat3/indx_sigma.jsp)).
- **Chart of Nuclides → Export** — vida media ya en segundos (archivo canónico `(10)`).

Detalle de CSV y variables: [`origen_datos.md`](origen_datos.md).

## 5. Conjunto de datos de este proyecto

| Aspecto | Valor |
|---------|--------|
| Interfaz | NuDat 3 — Wallet Cards + Chart half-life |
| Fecha de descarga | 2026-09-20 |
| Registros Wallet | ~4116 (estados base + isómeros) |
| Registros Chart half-life | ~3150 nuclidos $(Z,N)$ |
| Naturaleza temporal | Snapshot evaluado |
| Variables centrales | $Z$, $N$, $A$, $N/Z$, modo dominante (GS) |

## 6. Significado físico de las variables centrales

- **$N/Z$**: posición relativa a la línea de estabilidad; predice cualitativamente $\beta^-$ (alto) vs EC/$\beta^+$ (bajo).
- **Decay Mode / branching**: canal(es) observados; el de mayor branching define el modo dominante.
- **Half-life / STABLE**: marca el fondo del valle.
- **Level Index / $J^{\pi}$ / mass excess**: identidad del estado (análisis de la pregunta en `level_index = 0`).

## 7. Pregunta científica del proyecto

> ¿Cómo se relaciona la razón $N/Z$ con el modo de desintegración dominante ($\beta^-$ frente a $\beta^+$/EC) en los estados base del chart of nuclides?

Esta pregunta orienta la limpieza (parseo de modos, $N=A-Z$), el modelo relacional de 4 tablas, las consultas SQL y las visualizaciones.

## 8. Referencias de acceso

| Recurso | URL |
|---------|-----|
| NuDat 3 (portal) | https://www.nndc.bnl.gov/nudat3/ |
| User Guide — Data Sources | https://www.nndc.bnl.gov/nudat3/guide/#sources |
| Nuclear Wallet Cards Search | https://www.nndc.bnl.gov/nudat3/indx_sigma.jsp |
| ENSDF | https://www.nndc.bnl.gov/ensdf/ |
