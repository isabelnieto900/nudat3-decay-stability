-- NuDat 3 — schema (4 tablas) alineado a la pregunta N/Z vs modo dominante
-- Init: docker-entrypoint-initdb.d / mysql < schema.sql

CREATE DATABASE IF NOT EXISTS nudat
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE nudat;

SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS decay_channel;
DROP TABLE IF EXISTS nuclear_state;
DROP TABLE IF EXISTS nuclide;
DROP TABLE IF EXISTS element;
SET FOREIGN_KEY_CHECKS = 1;

CREATE TABLE element (
  Z SMALLINT UNSIGNED NOT NULL COMMENT 'Número atómico (protones)',
  symbol VARCHAR(8) NOT NULL COMMENT 'Símbolo químico',
  PRIMARY KEY (Z),
  UNIQUE KEY uq_element_symbol (symbol)
) ENGINE=InnoDB;

CREATE TABLE nuclide (
  nuclide_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  Z SMALLINT UNSIGNED NOT NULL,
  A SMALLINT UNSIGNED NOT NULL COMMENT 'Número másico',
  N SMALLINT NOT NULL COMMENT 'Neutrones A-Z',
  name VARCHAR(32) NULL,
  PRIMARY KEY (nuclide_id),
  UNIQUE KEY uq_nuclide_za (Z, A),
  CONSTRAINT fk_nuclide_element FOREIGN KEY (Z) REFERENCES element (Z)
) ENGINE=InnoDB;

CREATE TABLE nuclear_state (
  state_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  nuclide_id INT UNSIGNED NOT NULL,
  level_index SMALLINT UNSIGNED NOT NULL DEFAULT 0 COMMENT '0=ground state',
  energy_keV DOUBLE NULL,
  spin_parity VARCHAR(32) NULL,
  mass_excess_keV DOUBLE NULL,
  abundance DOUBLE NULL,
  half_life_s DOUBLE NULL COMMENT 'NULL si STABLE o desconocida',
  half_life_source VARCHAR(16) NULL COMMENT 'chart|wallet|none',
  is_stable TINYINT(1) NOT NULL DEFAULT 0,
  is_resonance TINYINT(1) NOT NULL DEFAULT 0 COMMENT 'Solo decay width',
  dominant_mode VARCHAR(16) NULL COMMENT 'B-|EC_BP|ALPHA|IT|OTHER|STABLE|UNKNOWN',
  decay_modes_raw VARCHAR(512) NULL,
  PRIMARY KEY (state_id),
  UNIQUE KEY uq_state_nuclide_level (nuclide_id, level_index),
  KEY idx_state_mode (dominant_mode),
  KEY idx_state_halflife (half_life_s),
  CONSTRAINT fk_state_nuclide FOREIGN KEY (nuclide_id) REFERENCES nuclide (nuclide_id)
    ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE decay_channel (
  channel_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  state_id INT UNSIGNED NOT NULL,
  mode_code VARCHAR(64) NOT NULL,
  branching_pct DOUBLE NULL,
  PRIMARY KEY (channel_id),
  KEY idx_channel_mode (mode_code),
  CONSTRAINT fk_channel_state FOREIGN KEY (state_id) REFERENCES nuclear_state (state_id)
    ON DELETE CASCADE
) ENGINE=InnoDB;
