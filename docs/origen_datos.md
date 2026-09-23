# Origen y documentación de los datos

## Fuente científica oficial

| Campo | Detalle |
|-------|---------|
| Organismo | National Nuclear Data Center (NNDC), Brookhaven National Laboratory |
| Producto | **NuDat 3.0** — Chart of Nuclides / nuclear structure & decay search |
| URL de consulta | https://www.nndc.bnl.gov/nudat3/ |
| Documentación de fuentes | https://www.nndc.bnl.gov/nudat3/guide/#sources |
| Wallet Cards Search | https://www.nndc.bnl.gov/nudat3/indx_sigma.jsp |
| Dominio | Física nuclear: isótopos, vidas medias, modos de decaimiento |

Los archivos de este proyecto son **exportaciones planas CSV** desde NuDat; **no se modifican** una vez descargados (`data/raw/`).

## Metodología de obtención

1. Acceso a https://www.nndc.bnl.gov/nudat3/
2. **Wallet Cards**: descarga del conjunto (ground + isomeric states) → `walletcards.csv`
3. **Chart of Nuclides → Export → Data**: half-life en segundos → `nndc_nudat_data_export (10).csv`

## Fechas de obtención

| Archivo | Fecha de obtención |
|---------|--------------------|
| `walletcards.csv` | 2026-09-20 ≈ 14:08 |
| `nndc_nudat_data_export (10).csv` | 2026-09-20 ≈ 15:22 |

Periodo temporal: snapshot evaluado vigente en la fecha de descarga (no es serie de tiempo).

## Inventario de archivos canónicos

Ubicación: [`data/raw/`](../data/raw/). Exports redundantes: [`data/raw/_archive/`](../data/raw/_archive/).

| Archivo | Registros (aprox.) | Rol |
|---------|--------------------|-----|
| `walletcards.csv` | 4116 | Estados base e isómeros: modos, $t_{1/2}$, mass excess |
| `nndc_nudat_data_export (10).csv` | 3150 | Vida media en segundos (Chart) |

Clave de cruce Wallet (estado base) ↔ Chart: $(Z, N)$ con $N = A - Z$.

---

## Descripción de variables

### 1. `walletcards.csv` (Wallet Cards)

| Variable | Tipo / unidad | Significado físico |
|----------|---------------|-------------------|
| `Atomic Number (Z)` | entero | Número de protones |
| `Atomic Mass (A)` | entero | Número másico ($A = Z + N$) |
| `Level Index` | entero | 0 = estado base; >0 = isómero |
| `Element` | texto | Símbolo químico |
| `Level Energy` (+ Unit) | número + unidad | Energía del nivel → keV en limpieza |
| `Spin-Parity` | texto | $J^{\pi}$ |
| `Half-Life` (+ Unit) | número o `STABLE` | Valor de $t_{1/2}$ |
| `Abundance` | % | Abundancia natural (si aplica) |
| `Mass Excess` | keV | Exceso de masa |
| `Decay Modes` | texto | Modos y branching (p. ej. `B- = 100`) |
| `Decay Width` (+ Unit) | número | Ancho $\Gamma$ (resonancias) |

Notación en `Decay Modes`: `B-` = $\beta^-$, `EC` / `EC+B+` = captura electrónica / $\beta^+$, `a` = $\alpha$, `IT` = transición isomérica.

### 2. `nndc_nudat_data_export (10).csv` (Chart — Half-life)

| Variable | Tipo / unidad | Significado físico |
|----------|---------------|-------------------|
| `z` | entero | $Z$ |
| `n` | entero | $N$ |
| `halflife(Seconds)` | s | Vida media en segundos |

---

## Separación raw vs procesado

- **`data/raw/`**: evidencia de la fuente; archivos inmutables.
- **`data/processed/`**: parseo de modos, $N=A-Z$, unificación de $t_{1/2}$ y tablas listos para MySQL (`02_clean_etl.ipynb`).

## Referencia

NNDC NuDat 3: https://www.nndc.bnl.gov/nudat3/
