# Modelo relacional — NuDat (decaimiento, N/Z y valle)

Documento de **diseño** (antes de crear/poblar MySQL). Justifica entidades a partir del fenómeno físico y de los CSV en `data/processed/`. El diagrama ER en DBeaver se generará al implementar la BD.

Fuente de datos limpios:

| CSV | Contenido |
|-----|-----------|
| `nuclides.csv` | Estados base + Q, BE/A, pairing (tabla de análisis) |
| `nuclear_states.csv` | Base + isómeros |
| `decay_channels.csv` | Canales parseados por estado |

---

## 1. Por qué no una sola tabla

Un CSV plano mezcla:

- identidad del **elemento** ($Z$, símbolo),
- identidad del **nuclido** ($Z$, $A$, $N$),
- **estado** cuántico (base vs isómero: energía, $J^\pi$, $t_{1/2}$),
- **canales** de decaimiento (varios por estado),
- observables de **masa/Q** (AME) y de **estructura** (BE/A, LDM, pairing).

Eso genera redundancia (el mismo $Z$ y símbolo se repiten miles de veces) y dificulta integridad (p. ej. un canal sin estado, o dos filas GS para el mismo $(Z,A)$).

La pregunta científica necesita JOINs naturales:

- $N/Z$ y modo → `nuclide` + `nuclear_state` (+ agregados de `decay_channel`),
- $Q$ vs $t_{1/2}$ → `nuclear_state` + `nuclide_qvalue`,
- valle → `nuclide_structure` + `nuclear_state`.

---

## 2. Entidades (visión física)

| Entidad | Qué representa en física | Cardinalidad típica |
|---------|--------------------------|---------------------|
| **Elemento** | Especie química: $Z$ protones, símbolo | ~1 por $Z$ |
| **Nuclido** | Isótopo $(Z,A)$ con $N=A-Z$ | ~3371 en este dataset |
| **Estado nuclear** | Nivel (base `level_index=0` o isómero) | 1..n por nuclido |
| **Canal de decaimiento** | Un modo + branching desde un estado | 0..n por estado |
| **Valores Q** | Energías disponibles de decaimiento (AME vía NuDat) | 0..1 por nuclido |
| **Estructura / valle** | BE/A, residual LDM, pairing gap | 0..1 por nuclido |

Los Q y la estructura se modelan aparte del estado porque en nuestros exports Chart vienen a nivel de **nuclido** $(Z,N)$, no por isómero; el análisis de valle/modos usa el **estado base**.

---

## 3. Diagrama entidad–relación (lógico)

```mermaid
erDiagram
  ELEMENT ||--o{ NUCLIDE : "tiene isótopos"
  NUCLIDE ||--o{ NUCLEAR_STATE : "tiene niveles"
  NUCLEAR_STATE ||--o{ DECAY_CHANNEL : "decae por"
  NUCLIDE ||--o| NUCLIDE_QVALUE : "tiene Q"
  NUCLIDE ||--o| NUCLIDE_STRUCTURE : "tiene BE/A"

  ELEMENT {
    smallint Z PK
    varchar symbol UK
  }

  NUCLIDE {
    int nuclide_id PK
    smallint Z FK
    smallint A
    smallint N
    varchar name
  }

  NUCLEAR_STATE {
    int state_id PK
    int nuclide_id FK
    smallint level_index
    double energy_keV
    varchar spin_parity
    double mass_excess_keV
    double abundance
    double half_life_s
    varchar half_life_source
    bool is_stable
    bool is_resonance
    varchar dominant_mode
    varchar decay_modes_raw
  }

  DECAY_CHANNEL {
    int channel_id PK
    int state_id FK
    varchar mode_code
    double branching_pct
  }

  NUCLIDE_QVALUE {
    int nuclide_id PK_FK
    double q_beta_minus_keV
    double q_ec_keV
    double q_beta_plus_keV
    double q_alpha_keV
    double delta_q_alpha_keV
  }

  NUCLIDE_STRUCTURE {
    int nuclide_id PK_FK
    double be_per_a_keV
    double be_ldm_residual_keV
    double pairing_gap_keV
  }
```

### Cardinalidades

| Relación | Tipo | Lectura |
|----------|------|---------|
| Elemento → Nuclido | 1 : N | Un elemento tiene muchos isótopos |
| Nuclido → Estado | 1 : N | Un isótopo tiene base (+ isómeros) |
| Estado → Canal | 1 : N | Un estado puede tener varios modos |
| Nuclido → Q-values | 1 : 0..1 | Como mucho un registro Q por nuclido |
| Nuclido → Structure | 1 : 0..1 | Como mucho un registro de valle por nuclido |

---

## 4. Atributos, claves y tipos lógicos

### `element`

| Atributo | Tipo lógico | Restricción | Origen |
|----------|-------------|-------------|--------|
| `Z` | entero | **PK** | Wallet / Chart |
| `symbol` | texto corto | **UNIQUE NOT NULL** | `element` |

### `nuclide`

| Atributo | Tipo lógico | Restricción | Origen |
|----------|-------------|-------------|--------|
| `nuclide_id` | entero surrogate | **PK** | generado |
| `Z` | entero | **FK → element** | |
| `A` | entero | | |
| `N` | entero | $N=A-Z$ (app) | |
| `name` | texto | | Chart `name` o `A`+símbolo |
| | | **UNIQUE (Z, A)** | |

### `nuclear_state`

| Atributo | Tipo lógico | Restricción | Origen |
|----------|-------------|-------------|--------|
| `state_id` | entero | **PK** | generado |
| `nuclide_id` | entero | **FK → nuclide** ON DELETE CASCADE | |
| `level_index` | entero ≥ 0 | | Wallet |
| `energy_keV` | real | | nivel en keV |
| `spin_parity` | texto | | $J^\pi$ |
| `mass_excess_keV` | real | | puede ser negativo |
| `abundance` | real | | % natural; muchos NULL |
| `half_life_s` | real | NULL si estable/ausente | unificado a s |
| `half_life_source` | enum texto | `chart` / `wallet` / `none` | limpieza |
| `is_stable` | booleano | | |
| `is_resonance` | booleano | | solo $\Gamma$, sin $t_{1/2}$ |
| `dominant_mode` | texto | `B-`, `EC_BP`, `ALPHA`, `IT`, `OTHER`, `STABLE`, `UNKNOWN` | |
| `decay_modes_raw` | texto | | auditoría |
| | | **UNIQUE (nuclide_id, level_index)** | |

### `decay_channel`

| Atributo | Tipo lógico | Restricción | Origen |
|----------|-------------|-------------|--------|
| `channel_id` | entero | **PK** | generado |
| `state_id` | entero | **FK → nuclear_state** CASCADE | |
| `mode_code` | texto | p. ej. `B-`, `B-n`, `EC+B+`, `A` | parseo |
| `branching_pct` | real | NULL si no reportado | |

### `nuclide_qvalue`

| Atributo | Tipo lógico | Notas |
|----------|-------------|-------|
| `nuclide_id` | **PK = FK → nuclide** | 1:1 |
| `q_beta_minus_keV` | real | puede ser &lt; 0 (canal cerrado) |
| `q_ec_keV` | real | |
| `q_beta_plus_keV` | real | |
| `q_alpha_keV` | real | |
| `delta_q_alpha_keV` | real | $\Delta Q_\alpha$ |

### `nuclide_structure`

| Atributo | Tipo lógico | Notas |
|----------|-------------|-------|
| `nuclide_id` | **PK = FK → nuclide** | 1:1 |
| `be_per_a_keV` | real | BE/A (valle) |
| `be_ldm_residual_keV` | real | (BE−LDM)/A |
| `pairing_gap_keV` | real | |

**No se almacena** `N_over_Z`: se calcula en consulta (`N/Z`) para evitar desnormalización.

---

## 5. Normalización (breve)

- **1FN:** atributos atómicos; modos en filas de `decay_channel`, no lista sin parsear (se guarda `decay_modes_raw` solo como evidencia).
- **2FN:** atributos de estado dependen de `state_id`; Q/BE dependen del nuclido, no del isómero.
- **3FN:** símbolo del elemento no se repite en cada estado: vive en `element`.

Redundancia aceptada a propósito:

- `dominant_mode` en `nuclear_state` (derivado de canales) → acelera consultas de la pregunta; se puede regenerar desde `decay_channel` + reglas de limpieza.
- `decay_modes_raw` → trazabilidad hacia Wallet.

---

## 6. Mapeo CSV procesado → tablas

| CSV / columna | Tabla.columna |
|---------------|---------------|
| `element` único por Z | `element` |
| `Z,A,N,name` (GS) | `nuclide` |
| fila de `nuclear_states` | `nuclear_state` |
| fila de `decay_channels` | `decay_channel` (vía `state_id` de Z,A,level_index) |
| Q* de `nuclides` | `nuclide_qvalue` |
| BE/A, LDM, pairing de `nuclides` | `nuclide_structure` |

---

## 7. Consultas que el modelo debe soportar (vista previa)

1. Media de $N/Z$ por `dominant_mode` (GS: `level_index=0`).
2. $\log t_{1/2}$ vs $Q_{\beta^-}$ con JOIN estado–qvalue, filtro `dominant_mode='B-'`, `q>0`, no resonancia.
3. BE/A y residual LDM por modo (JOIN structure).
4. Frontera $N/Z$ $\beta^-$ vs EC_BP por bins de $Z$.
5. Listar canales de un isómero concreto.

---

## 8. Implementación siguiente (aún no hecha)

1. Alinear [`sql/schema.sql`](../sql/schema.sql) con este diseño (incluir `half_life_source`, `is_resonance`).
2. Crear BD en MySQL (Docker) y cargar desde `data/processed/` con un notebook/script de carga.
3. Abrir en **DBeaver**, generar diagrama ER y exportarlo como evidencia.

Este documento es la especificación a seguir en ese paso.
