"""SQL de la app (basado en sql/queries.sql), con parámetros enlazados.

Parámetros usados:
  :w     ancho del bin de Z
  :z_min / :z_max  rango de Z
  :limit nº de filas
  :nuclide_id
"""

TABLE_COUNTS = """
SELECT 'element' AS tabla, COUNT(*) AS filas FROM element
UNION ALL SELECT 'nuclide', COUNT(*) FROM nuclide
UNION ALL SELECT 'nuclear_state', COUNT(*) FROM nuclear_state
UNION ALL SELECT 'decay_channel', COUNT(*) FROM decay_channel
"""

OVERVIEW = """
SELECT
  COUNT(*) AS n_gs,
  SUM(ns.is_stable) AS n_stable,
  MIN(n.Z) AS z_min,
  MAX(n.Z) AS z_max,
  MAX(n.A) AS a_max,
  MAX(CASE WHEN ns.is_stable = 1 THEN n.Z END) AS z_max_stable
FROM nuclear_state ns
JOIN nuclide n ON n.nuclide_id = ns.nuclide_id
WHERE ns.level_index = 0
"""

# 1) Conteo y N/Z medio (± σ) por modo dominante
MODE_SUMMARY = """
SELECT
  COALESCE(ns.dominant_mode, 'UNKNOWN') AS dominant_mode,
  COUNT(*) AS n_nuclides,
  ROUND(AVG(n.N / NULLIF(n.Z, 0)), 3) AS mean_N_over_Z,
  ROUND(STDDEV_SAMP(n.N / NULLIF(n.Z, 0)), 3) AS sd_N_over_Z
FROM nuclear_state ns
JOIN nuclide n ON n.nuclide_id = ns.nuclide_id
WHERE ns.level_index = 0
  AND n.Z BETWEEN :z_min AND :z_max
GROUP BY COALESCE(ns.dominant_mode, 'UNKNOWN')
ORDER BY n_nuclides DESC
"""

# 2) Min / media / max N/Z para β−, EC/β+ y estables
NZ_MINMAX = """
SELECT
  ns.dominant_mode,
  ROUND(MIN(n.N / NULLIF(n.Z, 0)), 3) AS min_nz,
  ROUND(AVG(n.N / NULLIF(n.Z, 0)), 3) AS mean_nz,
  ROUND(MAX(n.N / NULLIF(n.Z, 0)), 3) AS max_nz,
  COUNT(*) AS n
FROM nuclear_state ns
JOIN nuclide n ON n.nuclide_id = ns.nuclide_id
WHERE ns.level_index = 0
  AND ns.dominant_mode IN ('B-', 'EC_BP', 'STABLE')
  AND n.Z BETWEEN :z_min AND :z_max
GROUP BY ns.dominant_mode
ORDER BY mean_nz DESC
"""

# 3) Frontera N/Z por bins de Z (ancho :w)
FRONTIER = """
SELECT
  FLOOR(n.Z / :w) * :w AS Z_bin,
  ROUND(AVG(CASE WHEN ns.dominant_mode = 'B-' THEN n.N / NULLIF(n.Z, 0) END), 3) AS mean_nz_B,
  ROUND(AVG(CASE WHEN ns.dominant_mode = 'STABLE' THEN n.N / NULLIF(n.Z, 0) END), 3) AS mean_nz_STABLE,
  ROUND(AVG(CASE WHEN ns.dominant_mode = 'EC_BP' THEN n.N / NULLIF(n.Z, 0) END), 3) AS mean_nz_EC_BP,
  ROUND(AVG(CASE WHEN ns.dominant_mode = 'ALPHA' THEN n.N / NULLIF(n.Z, 0) END), 3) AS mean_nz_ALPHA,
  SUM(ns.dominant_mode = 'B-') AS n_B,
  SUM(ns.dominant_mode = 'STABLE') AS n_STABLE,
  SUM(ns.dominant_mode = 'EC_BP') AS n_EC_BP,
  SUM(ns.dominant_mode = 'ALPHA') AS n_ALPHA
FROM nuclear_state ns
JOIN nuclide n ON n.nuclide_id = ns.nuclide_id
WHERE ns.level_index = 0
  AND ns.dominant_mode IN ('B-', 'EC_BP', 'STABLE', 'ALPHA')
GROUP BY FLOOR(n.Z / :w) * :w
ORDER BY Z_bin
"""

# 4) Estados base con Z, N, modo y vida media (base de la carta N–Z)
GROUND_STATES = """
SELECT
  n.nuclide_id,
  n.Z,
  n.N,
  n.A,
  n.name,
  e.symbol,
  n.N / NULLIF(n.Z, 0) AS N_over_Z,
  COALESCE(ns.dominant_mode, 'UNKNOWN') AS dominant_mode,
  ns.is_stable,
  ns.half_life_s,
  ns.spin_parity,
  ns.mass_excess_keV,
  ns.abundance,
  ns.decay_modes_raw
FROM nuclear_state ns
JOIN nuclide n ON n.nuclide_id = ns.nuclide_id
JOIN element e ON e.Z = n.Z
WHERE ns.level_index = 0
ORDER BY n.Z, n.N
"""

# 6) Subconsulta: modo mayoritario por bin de Z (ancho :w)
MAJORITY_MODE = """
SELECT
  t.Z_bin,
  t.dominant_mode AS majority_mode,
  t.n AS n_in_mode,
  t.mean_nz
FROM (
  SELECT
    FLOOR(n.Z / :w) * :w AS Z_bin,
    ns.dominant_mode,
    COUNT(*) AS n,
    ROUND(AVG(n.N / NULLIF(n.Z, 0)), 3) AS mean_nz
  FROM nuclear_state ns
  JOIN nuclide n ON n.nuclide_id = ns.nuclide_id
  WHERE ns.level_index = 0
    AND ns.dominant_mode IN ('B-', 'EC_BP', 'STABLE', 'ALPHA', 'OTHER')
  GROUP BY FLOOR(n.Z / :w) * :w, ns.dominant_mode
) AS t
WHERE t.n = (
  SELECT MAX(t2.n)
  FROM (
    SELECT FLOOR(n2.Z / :w) * :w AS Z_bin, ns2.dominant_mode, COUNT(*) AS n
    FROM nuclear_state ns2
    JOIN nuclide n2 ON n2.nuclide_id = ns2.nuclide_id
    WHERE ns2.level_index = 0
      AND ns2.dominant_mode IN ('B-', 'EC_BP', 'STABLE', 'ALPHA', 'OTHER')
    GROUP BY FLOOR(n2.Z / :w) * :w, ns2.dominant_mode
  ) AS t2
  WHERE t2.Z_bin = t.Z_bin
)
ORDER BY t.Z_bin
"""

# 7) Canales más frecuentes en estados base
TOP_CHANNELS = """
SELECT
  dc.mode_code,
  COUNT(*) AS n_channels,
  ROUND(AVG(dc.branching_pct), 1) AS mean_branching
FROM decay_channel dc
JOIN nuclear_state ns ON ns.state_id = dc.state_id
WHERE ns.level_index = 0
GROUP BY dc.mode_code
ORDER BY n_channels DESC
LIMIT :limit
"""

ELEMENTS = """
SELECT Z, symbol FROM element ORDER BY Z
"""

NUCLIDES_OF_ELEMENT = """
SELECT nuclide_id, A, N, name
FROM nuclide
WHERE Z = :z
ORDER BY A
"""

NUCLIDE_STATES = """
SELECT
  ns.state_id,
  ns.level_index,
  ns.energy_keV,
  ns.spin_parity,
  ns.half_life_s,
  ns.half_life_source,
  ns.is_stable,
  ns.is_resonance,
  ns.dominant_mode,
  ns.mass_excess_keV,
  ns.abundance,
  ns.decay_modes_raw
FROM nuclear_state ns
WHERE ns.nuclide_id = :nuclide_id
ORDER BY ns.level_index
"""

NUCLIDE_CHANNELS = """
SELECT
  ns.level_index,
  dc.mode_code,
  dc.branching_pct
FROM decay_channel dc
JOIN nuclear_state ns ON ns.state_id = dc.state_id
WHERE ns.nuclide_id = :nuclide_id
ORDER BY ns.level_index, dc.branching_pct DESC
"""
