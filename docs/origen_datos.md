# Origen y documentación de los datos

## Fuente científica oficial

| Campo | Detalle |
|-------|---------|
| Organismo | National Nuclear Data Center (NNDC), Brookhaven National Laboratory |
| Producto | **NuDat 3.0** — Chart of Nuclides / nuclear structure & decay search |
| URL de consulta | https://www.nndc.bnl.gov/nudat3/ |
| Documentación de fuentes (oficial) | https://www.nndc.bnl.gov/nudat3/guide/#sources |
| Wallet Cards Search | https://www.nndc.bnl.gov/nudat3/indx_sigma.jsp |
| Bases subyacentes | Wallet Cards, ENSDF, AME 2020 (Wang et al.), ENDF/B — ver User Guide §Sources |
| AME 2020 | https://doi.org/10.1088/1674-1137/abddaf |
| Dominio | Física nuclear: isótopos, vidas medias, modos de decaimiento, excesos de masa, energías Q, energía de enlace |

NuDat permite buscar y exportar propiedades de nuclidos de forma interactiva (Wallet Cards, Chart of Nuclides, Advanced Plot). Los archivos de este proyecto son **exportaciones planas CSV** obtenidas desde esa interfaz; **no se modifican** una vez descargados (`data/raw/`).

## Metodología de obtención

1. Acceso a https://www.nndc.bnl.gov/nudat3/
2. **Wallet Cards**: descarga del conjunto de tarjetas (ground + isomeric states) → `walletcards.csv`
3. **Chart of Nuclides → Export → Data**: selección de datasets y exportación CSV (NuDat descarga con nombre `nndc_nudat_data_export (N).csv`). Por límites de la UI, los observables se exportaron en **varios CSV** y luego se documentaron los canónicos.

## Fechas de obtención

Fechas tomadas de la marca de tiempo del archivo en el sistema local (zona America/Bogota, UTC−5):

| Archivo | Fecha de obtención |
|---------|--------------------|
| `walletcards.csv` | 2026-09-20 ≈ 14:08 |
| `nndc_nudat_data_export (10).csv` | 2026-09-20 ≈ 15:22 |
| `nndc_nudat_data_export (12).csv` | 2026-09-20 ≈ 15:24 |
| `nndc_nudat_data_export (21).csv` | 2026-09-20 ≈ 15:29 |

Periodo temporal de los datos: NuDat refleja el estado **evaluado vigente** de ENSDF/NuDat en la fecha de descarga (no es una serie temporal de mediciones).

## Inventario de archivos canónicos

Ubicación: [`data/raw/`](../data/raw/). Cualquier export redundante o vacío se documenta en [`data/raw/_archive/`](../data/raw/_archive/).

| Archivo | Registros (aprox.) | Rol en el proyecto |
|---------|--------------------|--------------------|
| `walletcards.csv` | 4116 | Estados base e isómeros: modos, vida media, mass excess, abundancia |
| `nndc_nudat_data_export (10).csv` | 3150 | Vida media ya en segundos (Chart) |
| `nndc_nudat_data_export (12).csv` | 4105 | $Q_{\beta^-}$, $Q_{\mathrm{EC}}$, $Q_{\beta^+}$, BE/A, residual LDM |
| `nndc_nudat_data_export (21).csv` | 4105 | Pairing gap, $Q_{\alpha}$, $\Delta Q_{\alpha}$ (varias columnas salieron vacías) |

Clave de cruce entre Wallet (estado base) y Chart: $(Z, N)$ con $N = A - Z$ y $A = Z + N$.

---

## Descripción de variables

### 1. `walletcards.csv` (Wallet Cards)

Información de estados base e isoméricos por nuclido.

| Variable | Tipo / unidad | Significado físico |
|----------|---------------|-------------------|
| `Atomic Number (Z)` | entero | Número de protones |
| `Atomic Mass (A)` | entero | Número másico ($A = Z + N$) |
| `Level Index` | entero | 0 = estado base; >0 = isómero / nivel listado |
| `Element` | texto | Símbolo químico (p. ej. `Pb`; `NN` = neutrón) |
| `Level Energy (Modifier)` | texto | Calificador de la energía de nivel (si aplica) |
| `Level Energy` | número | Energía del nivel |
| `Level Energy (Unit)` | texto | Unidad (`keV`, `MeV`, …) |
| `Level Energy (Error)` | número | Incertidumbre de la energía |
| `Spin-Parity` | texto | Espín y paridad $J^{\pi}$ (p. ej. `0+`, `3/2-`) |
| `Half-Life (Modifier)` | texto | Calificador de la vida media |
| `Half-Life` | número o `STABLE` | Valor de $t_{1/2}$ o estable |
| `Half-Life (Unit)` | texto | `s`, `ms`, `m`, `h`, `d`, `y`, … |
| `Half-Life (Error)` | número / texto | Incertidumbre de $t_{1/2}$ |
| `Decay Width (Modifier)` | texto | Calificador del ancho de decaimiento |
| `Decay Width` | número | Ancho $\Gamma$ (resonancias / estados no ligados) |
| `Decay Width (Unit)` | texto | p. ej. `keV`, `MeV`, `eV` |
| `Decay Width (Error)` | número | Incertidumbre de $\Gamma$ |
| `Abundance (Modifier)` | texto | Calificador de abundancia isotópica |
| `Abundance` | % | Abundancia natural (si aplica) |
| `Abundance (Error)` | número | Incertidumbre de la abundancia |
| `Mass Excess` | keV (típ.) | Exceso de masa $\Delta = (M - A)\,u$ en energía |
| `Mass Excess (Unit)` | texto | Unidad del exceso de masa |
| `Mass Excess (Error)` | número | Incertidumbre del exceso de masa |
| `Decay Modes` | texto | Modos y branching (p. ej. `B- = 100`, `EC+B+ = 100`, `a = 100`) |

Notación frecuente en `Decay Modes`: `B-` = $\beta^-$, `EC` / `EC+B+` = captura electrónica / $\beta^+$, `a` = $\alpha$, `IT` = transición isomérica, `B-n` = $\beta^-$ seguida de neutrón, etc.

### 2. `nndc_nudat_data_export (10).csv` (Chart — Half-life)

| Variable | Tipo / unidad | Significado físico |
|----------|---------------|-------------------|
| `z` | entero | Número de protones $Z$ |
| `n` | entero | Número de neutrones $N$ |
| `halflife(Seconds)` | s | Vida media convertida a segundos |

### 3. `nndc_nudat_data_export (12).csv` (Chart — Qβ y valle)

| Variable | Tipo / unidad | Significado físico |
|----------|---------------|-------------------|
| `z`, `n` | enteros | $Z$, $N$ |
| `name` | texto | Etiqueta del nuclido (p. ej. `74Zn`) |
| `betaMinus` | keV | Energía disponible $Q_{\beta^-}$ |
| `betaMinusUncertainty` | keV | Incertidumbre de $Q_{\beta^-}$ |
| `electronCapture` | keV | Energía $Q_{\mathrm{EC}}$ |
| `electronCaptureUncertainty` | keV | Incertidumbre de $Q_{\mathrm{EC}}$ |
| `positronEmission` | keV | Energía $Q_{\beta^+}$ |
| `positronEmissionUncertainty` | keV | Incertidumbre de $Q_{\beta^+}$ |
| `bindingEnergy` | keV | Energía de enlace por nucleón (BE/A) |
| `bindingEnergyUncertainty` | keV | Incertidumbre de BE/A |
| `bindingEnergyLDMFit` | keV | Residual (BE − ajuste LDM)/A; proximidad al valle “suave” |
| `bindingEnergyLDMFitUncertainty` | keV | Incertidumbre del residual LDM |

Valores Q positivos indican canal energéticamente permitido (con el criterio habitual de NuDat/ENSDF).

### 4. `nndc_nudat_data_export (21).csv` (Chart — pairing / α)

| Variable | Tipo / unidad | Significado / estado en este export |
|----------|---------------|-------------------------------------|
| `z`, `n`, `name` | — | Identificación del nuclido |
| `spinAndParity` | texto | $J^{\pi}$ — **columna presente pero vacía** en este archivo |
| `massExcess(keV)`, `massExcessUncertainty` | keV | Exceso de masa — **vacías** aquí (sí están en Wallet) |
| `neutronSeparationEnergy`, … | keV | $S_n$ — **vacías** |
| `protonSeparationEnergy`, … | keV | $S_p$ — **vacías** |
| `pairingGap` | keV | Gap de apareamiento |
| `pairingGapUncertainty` | keV | Incertidumbre del pairing gap |
| `alpha` | keV | Energía $Q_{\alpha}$ |
| `alphaUncertainty` | keV | Incertidumbre de $Q_{\alpha}$ |
| `deltaAlpha` | keV | $\Delta Q_{\alpha}$ (diferencia sistemática reportada por NuDat) |
| `deltaAlphaUncertainty` | keV | Incertidumbre de $\Delta Q_{\alpha}$ |

---

## Separación raw vs procesado

- **`data/raw/`**: evidencia de la fuente; archivos inmutables.
- **`data/processed/`**: resultado de limpieza, parseo de modos, unificación de $t_{1/2}$ y join $(Z,N)$ (etapas posteriores del proyecto).

## Referencia

NNDC NuDat 3: https://www.nndc.bnl.gov/nudat3/
