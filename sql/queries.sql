-- Scientific queries for the NuDat research question
USE nudat;

-- 1) Count ground states by dominant decay class
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

-- 2) N/Z percentiles by mode (β− vs EC/β+)
SELECT
  ns.dominant_mode,
  ROUND(MIN(n.N / NULLIF(n.Z, 0)), 3) AS min_nz,
  ROUND(AVG(n.N / NULLIF(n.Z, 0)), 3) AS mean_nz,
  ROUND(MAX(n.N / NULLIF(n.Z, 0)), 3) AS max_nz
FROM nuclear_state ns
JOIN nuclide n ON n.nuclide_id = ns.nuclide_id
WHERE ns.level_index = 0
  AND ns.dominant_mode IN ('B-', 'EC_BP', 'STABLE')
GROUP BY ns.dominant_mode;

-- 3) Mean frontier N/Z by Z-bin: where B- vs EC_BP dominate
SELECT
  FLOOR(n.Z / 10) * 10 AS Z_bin,
  ROUND(AVG(CASE WHEN ns.dominant_mode = 'B-' THEN n.N / NULLIF(n.Z, 0) END), 3) AS mean_nz_beta_minus,
  ROUND(AVG(CASE WHEN ns.dominant_mode = 'EC_BP' THEN n.N / NULLIF(n.Z, 0) END), 3) AS mean_nz_ec_bp,
  SUM(ns.dominant_mode = 'B-') AS n_beta_minus,
  SUM(ns.dominant_mode = 'EC_BP') AS n_ec_bp
FROM nuclear_state ns
JOIN nuclide n ON n.nuclide_id = ns.nuclide_id
WHERE ns.level_index = 0
  AND ns.dominant_mode IN ('B-', 'EC_BP')
GROUP BY FLOOR(n.Z / 10) * 10
ORDER BY Z_bin;

-- 4) Qβ− vs half-life for dominant β− emitters
SELECT
  n.name,
  n.Z,
  n.A,
  n.N / NULLIF(n.Z, 0) AS N_over_Z,
  q.q_beta_minus_keV,
  ns.half_life_s,
  LOG10(ns.half_life_s) AS log10_half_life_s
FROM nuclear_state ns
JOIN nuclide n ON n.nuclide_id = ns.nuclide_id
JOIN nuclide_qvalue q ON q.nuclide_id = n.nuclide_id
WHERE ns.level_index = 0
  AND ns.dominant_mode = 'B-'
  AND ns.is_stable = 0
  AND ns.is_resonance = 0
  AND ns.half_life_s IS NOT NULL
  AND ns.half_life_s > 0
  AND q.q_beta_minus_keV IS NOT NULL
  AND q.q_beta_minus_keV > 0
ORDER BY q.q_beta_minus_keV DESC;

-- 5) Aggregate correlation proxy: mean log t1/2 by Qβ− bins
SELECT
  FLOOR(q.q_beta_minus_keV / 2000) * 2000 AS Qb_bin_keV,
  COUNT(*) AS n,
  ROUND(AVG(LOG10(ns.half_life_s)), 3) AS mean_log10_t12,
  ROUND(AVG(q.q_beta_minus_keV), 1) AS mean_Qb
FROM nuclear_state ns
JOIN nuclide n ON n.nuclide_id = ns.nuclide_id
JOIN nuclide_qvalue q ON q.nuclide_id = n.nuclide_id
WHERE ns.level_index = 0
  AND ns.dominant_mode = 'B-'
  AND ns.is_resonance = 0
  AND ns.half_life_s > 0
  AND q.q_beta_minus_keV > 0
GROUP BY FLOOR(q.q_beta_minus_keV / 2000) * 2000
ORDER BY Qb_bin_keV;

-- 6) Same for EC / β+ using QEC
SELECT
  FLOOR(q.q_ec_keV / 2000) * 2000 AS Qec_bin_keV,
  COUNT(*) AS n,
  ROUND(AVG(LOG10(ns.half_life_s)), 3) AS mean_log10_t12,
  ROUND(AVG(q.q_ec_keV), 1) AS mean_Qec
FROM nuclear_state ns
JOIN nuclide n ON n.nuclide_id = ns.nuclide_id
JOIN nuclide_qvalue q ON q.nuclide_id = n.nuclide_id
WHERE ns.level_index = 0
  AND ns.dominant_mode = 'EC_BP'
  AND ns.is_resonance = 0
  AND ns.half_life_s > 0
  AND q.q_ec_keV > 0
GROUP BY FLOOR(q.q_ec_keV / 2000) * 2000
ORDER BY Qec_bin_keV;

-- 7) Valley: BE/A and LDM residual by dominant mode
SELECT
  ns.dominant_mode,
  COUNT(*) AS n,
  ROUND(AVG(s.be_per_a_keV), 1) AS mean_BE_A,
  ROUND(AVG(s.be_ldm_residual_keV), 1) AS mean_LDM_residual,
  ROUND(AVG(LOG10(NULLIF(ns.half_life_s, 0))), 3) AS mean_log10_t12
FROM nuclear_state ns
JOIN nuclide n ON n.nuclide_id = ns.nuclide_id
JOIN nuclide_structure s ON s.nuclide_id = n.nuclide_id
WHERE ns.level_index = 0
GROUP BY ns.dominant_mode
ORDER BY mean_BE_A DESC;

-- 8) Stable vs radioactive: structure comparison
SELECT
  ns.is_stable,
  COUNT(*) AS n,
  ROUND(AVG(s.be_per_a_keV), 1) AS mean_BE_A,
  ROUND(AVG(ABS(s.be_ldm_residual_keV)), 1) AS mean_abs_LDM_residual,
  ROUND(AVG(s.pairing_gap_keV), 1) AS mean_pairing_gap
FROM nuclear_state ns
JOIN nuclide n ON n.nuclide_id = ns.nuclide_id
JOIN nuclide_structure s ON s.nuclide_id = n.nuclide_id
WHERE ns.level_index = 0
GROUP BY ns.is_stable;

-- 9) Subquery: nuclides near max BE/A in their Z chain (valley core)
SELECT
  n.Z,
  n.A,
  n.name,
  s.be_per_a_keV,
  ns.dominant_mode,
  ns.is_stable
FROM nuclear_state ns
JOIN nuclide n ON n.nuclide_id = ns.nuclide_id
JOIN nuclide_structure s ON s.nuclide_id = n.nuclide_id
WHERE ns.level_index = 0
  AND s.be_per_a_keV = (
    SELECT MAX(s2.be_per_a_keV)
    FROM nuclide n2
    JOIN nuclide_structure s2 ON s2.nuclide_id = n2.nuclide_id
    WHERE n2.Z = n.Z
  )
ORDER BY n.Z;

-- 10) Channel-level: most common decay mode codes
SELECT
  dc.mode_code,
  COUNT(*) AS n_channels,
  ROUND(AVG(dc.branching_pct), 1) AS mean_branching
FROM decay_channel dc
GROUP BY dc.mode_code
ORDER BY n_channels DESC
LIMIT 20;
