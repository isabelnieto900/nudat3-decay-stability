# Log de limpieza NuDat

Generado por `notebooks/02_clean_etl.ipynb`. Raw en `data/raw/` **no modificado**.

## Conteos

- nuclides (GS): 3371
- nuclear_states: 4116
- decay_channels: 6372
- STABLE (GS): 253
- resonancias (GS): 37

## Decisiones clave

- $t_{1/2}$ en segundos; Chart preferido en GS; `STABLE` → NULL + flag.
- Modo dominante por mayor branching; clases B-, EC_BP, ALPHA, IT, OTHER, STABLE.
- Chart deduplicado por (Z,N); columnas vacías de export 21 descartadas.
- $Q<0$ y BE/A=0 conservados; filtros solo en análisis.
- Isómeros en `nuclear_states`; análisis de valle/modos en GS (`nuclides`).

## Modos dominantes (GS)

- `B-`: 1377
- `EC_BP`: 1091
- `ALPHA`: 469
- `STABLE`: 253
- `OTHER`: 181

## MySQL

Carga OK (`src.load_db`): 119 elementos, 3371 nuclidos, 4116 estados, 6372 canales.
`decay_channel.mode_code` ampliado a `VARCHAR(64)`; parseo de branching admite notación científica (`1.13E-11`).
