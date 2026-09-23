-- Consultas científicas: N/Z vs modo de desintegración dominante
-- Estados base (level_index = 0).
USE nudat;

-- 1) Conteo y N/Z medio (± σ) por modo dominante
SELECT
  ns.dominant_mode,
  COUNT(*) AS n_nuclides,
  ROUND(AVG(n.N / NULLIF(n.Z, 0)), 3) AS mean_N_over_Z,
  ROUND(STDDEV_SAMP(n.N / NULLIF(n.Z, 0)), 3) AS sd_N_over_Z
FROM nuclear_state ns
JOIN nuclide n ON n.nuclide_id = ns.nuclide_id
WHERE ns.level_index = 0
GROUP BY ns.dominant_mode
ORDER BY n_nuclides DESC;

-- 2) Min / media / max N/Z para β−, EC/β+ y estables
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
GROUP BY ns.dominant_mode
ORDER BY mean_nz DESC;

-- 3) Frontera N/Z por bins de Z (B-, STABLE, EC_BP, ALPHA)
SELECT
  FLOOR(n.Z / 10) * 10 AS Z_bin,
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
GROUP BY FLOOR(n.Z / 10) * 10
ORDER BY Z_bin;

-- 4) Chart: Z, N, modo (base de la figura N–Z)
SELECT
  n.Z,
  n.N,
  n.A,
  n.name,
  n.N / NULLIF(n.Z, 0) AS N_over_Z,
  ns.dominant_mode,
  ns.is_stable
FROM nuclear_state ns
JOIN nuclide n ON n.nuclide_id = ns.nuclide_id
WHERE ns.level_index = 0
ORDER BY n.Z, n.N;

-- 5) Rangos de N/Z × modo (para histograma / tablas)
SELECT
  CASE
    WHEN n.N / NULLIF(n.Z, 0) < 1.0 THEN '<1.0'
    WHEN n.N / NULLIF(n.Z, 0) < 1.2 THEN '1.0–1.2'
    WHEN n.N / NULLIF(n.Z, 0) < 1.4 THEN '1.2–1.4'
    WHEN n.N / NULLIF(n.Z, 0) < 1.6 THEN '1.4–1.6'
    WHEN n.N / NULLIF(n.Z, 0) < 1.8 THEN '1.6–1.8'
    ELSE '≥1.8'
  END AS NZ_bin,
  ns.dominant_mode,
  COUNT(*) AS n
FROM nuclear_state ns
JOIN nuclide n ON n.nuclide_id = ns.nuclide_id
WHERE ns.level_index = 0
  AND n.Z > 0
  AND ns.dominant_mode IN ('B-', 'EC_BP', 'STABLE')
GROUP BY NZ_bin, ns.dominant_mode
ORDER BY NZ_bin, ns.dominant_mode;

-- 6) Subconsulta: modo mayoritario por bin de Z
SELECT
  t.Z_bin,
  t.dominant_mode AS majority_mode,
  t.n AS n_in_mode,
  t.mean_nz
FROM (
  SELECT
    FLOOR(n.Z / 10) * 10 AS Z_bin,
    ns.dominant_mode,
    COUNT(*) AS n,
    ROUND(AVG(n.N / NULLIF(n.Z, 0)), 3) AS mean_nz
  FROM nuclear_state ns
  JOIN nuclide n ON n.nuclide_id = ns.nuclide_id
  WHERE ns.level_index = 0
    AND ns.dominant_mode IN ('B-', 'EC_BP', 'STABLE', 'ALPHA', 'OTHER')
  GROUP BY FLOOR(n.Z / 10) * 10, ns.dominant_mode
) AS t
WHERE t.n = (
  SELECT MAX(t2.n)
  FROM (
    SELECT
      FLOOR(n2.Z / 10) * 10 AS Z_bin,
      ns2.dominant_mode,
      COUNT(*) AS n
    FROM nuclear_state ns2
    JOIN nuclide n2 ON n2.nuclide_id = ns2.nuclide_id
    WHERE ns2.level_index = 0
      AND ns2.dominant_mode IN ('B-', 'EC_BP', 'STABLE', 'ALPHA', 'OTHER')
    GROUP BY FLOOR(n2.Z / 10) * 10, ns2.dominant_mode
  ) AS t2
  WHERE t2.Z_bin = t.Z_bin
)
ORDER BY t.Z_bin;

-- 7) Canales más frecuentes (JOIN decay_channel; complejidad básica+)
SELECT
  dc.mode_code,
  COUNT(*) AS n_channels,
  ROUND(AVG(dc.branching_pct), 1) AS mean_branching
FROM decay_channel dc
JOIN nuclear_state ns ON ns.state_id = dc.state_id
WHERE ns.level_index = 0
GROUP BY dc.mode_code
ORDER BY n_channels DESC
LIMIT 15;
