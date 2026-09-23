# Log de limpieza NuDat

Generado por `notebooks/02_clean_etl.ipynb`. Raw en `data/raw/` **no modificado**.

## Pregunta que orienta el ETL

¿Cómo se relaciona $N/Z$ con el modo de desintegración dominante ($\beta^-$ vs $\beta^+$/EC) en estados base?

## Conteos

- nuclides (GS): 3371
- nuclear_states: 4116
- decay_channels: 6372
- STABLE (GS): 253
- resonancias (GS): 37

## Decisiones clave

- $t_{1/2}$ en segundos; Chart preferido en GS; `STABLE` → NULL + flag.
- Modo dominante por mayor branching; clases B-, EC_BP, ALPHA, IT, OTHER, STABLE.
- Chart half-life deduplicado por (Z,N).
- Isómeros en `nuclear_states`; análisis N/Z–modo en GS (`level_index = 0`).
- MySQL: 4 tablas (`element`, `nuclide`, `nuclear_state`, `decay_channel`).

## Modos dominantes (GS)

- `B-`: 1378
- `EC_BP`: 1096
- `ALPHA`: 465
- `STABLE`: 253
- `OTHER`: 179
