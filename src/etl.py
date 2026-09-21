"""ETL helpers for NuDat wallet cards + chart exports.

NOTE: La limpieza oficial del proyecto está en notebooks/02_clean_etl.ipynb
(notebook-only). Este módulo es un utilitario opcional / legado; no lo uses
como fuente de verdad frente al notebook 02.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"

WALLET = RAW / "walletcards.csv"
EXPORT_HL = RAW / "nndc_nudat_data_export (10).csv"
EXPORT_QBE = RAW / "nndc_nudat_data_export (12).csv"
EXPORT_PAIR = RAW / "nndc_nudat_data_export (21).csv"

HALF_LIFE_TO_SECONDS = {
    "ys": 1e-24,
    "zs": 1e-21,
    "as": 1e-18,
    "fs": 1e-15,
    "ps": 1e-12,
    "ns": 1e-9,
    "us": 1e-6,
    "µs": 1e-6,
    "ms": 1e-3,
    "s": 1.0,
    "m": 60.0,
    "h": 3600.0,
    "d": 86400.0,
    "y": 365.25 * 86400.0,
}


def _to_float(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def load_wallet() -> pd.DataFrame:
    df = pd.read_csv(WALLET)
    df = df.rename(
        columns={
            "Atomic Number (Z)": "Z",
            "Atomic Mass (A)": "A",
            "Level Index": "level_index",
            "Element": "element",
            "Level Energy": "level_energy",
            "Level Energy (Unit)": "level_energy_unit",
            "Level Energy (Error)": "level_energy_error",
            "Spin-Parity": "spin_parity",
            "Half-Life": "half_life_raw",
            "Half-Life (Unit)": "half_life_unit",
            "Half-Life (Error)": "half_life_error",
            "Abundance": "abundance",
            "Abundance (Error)": "abundance_error",
            "Mass Excess": "mass_excess_keV",
            "Mass Excess (Error)": "mass_excess_error",
            "Decay Modes": "decay_modes_raw",
            "Decay Width": "decay_width",
            "Decay Width (Unit)": "decay_width_unit",
        }
    )
    keep = [
        "Z",
        "A",
        "level_index",
        "element",
        "level_energy",
        "level_energy_unit",
        "level_energy_error",
        "spin_parity",
        "half_life_raw",
        "half_life_unit",
        "half_life_error",
        "abundance",
        "abundance_error",
        "mass_excess_keV",
        "mass_excess_error",
        "decay_modes_raw",
        "decay_width",
        "decay_width_unit",
    ]
    df = df[[c for c in keep if c in df.columns]].copy()
    df["N"] = df["A"] - df["Z"]
    df["level_energy_keV"] = _level_energy_to_keV(df)
    df["half_life_s_wallet"] = df.apply(
        lambda r: wallet_half_life_to_seconds(r["half_life_raw"], r["half_life_unit"]),
        axis=1,
    )
    df["is_stable_wallet"] = df["half_life_raw"].astype(str).str.upper().eq("STABLE")
    for col in [
        "mass_excess_keV",
        "mass_excess_error",
        "abundance",
        "abundance_error",
        "level_energy",
        "level_energy_error",
    ]:
        if col in df.columns:
            df[col] = _to_float(df[col])
    return df


def _level_energy_to_keV(df: pd.DataFrame) -> pd.Series:
    val = _to_float(df["level_energy"])
    unit = df["level_energy_unit"].astype(str).str.strip().str.lower()
    scale = unit.map({"kev": 1.0, "mev": 1e3, "ev": 1e-3}).fillna(1.0)
    return val * scale


def wallet_half_life_to_seconds(value, unit) -> Optional[float]:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = str(value).strip()
    if not text or text.upper() == "STABLE":
        return None
    try:
        number = float(text)
    except ValueError:
        return None
    if unit is None or (isinstance(unit, float) and pd.isna(unit)):
        return None
    u = str(unit).strip().lower()
    factor = HALF_LIFE_TO_SECONDS.get(u)
    if factor is None:
        return None
    return number * factor


def load_halflife_chart() -> pd.DataFrame:
    df = pd.read_csv(EXPORT_HL)
    df = df.rename(columns={"z": "Z", "n": "N", "halflife(Seconds)": "half_life_s_chart"})
    df["half_life_s_chart"] = _to_float(df["half_life_s_chart"])
    # Chart exports can list isomers as duplicate (Z,N); keep first ground-like row
    return df[["Z", "N", "half_life_s_chart"]].drop_duplicates(["Z", "N"], keep="first")


def load_q_and_be() -> pd.DataFrame:
    df = pd.read_csv(EXPORT_QBE)
    df = df.rename(
        columns={
            "z": "Z",
            "n": "N",
            "name": "name",
            "betaMinus": "q_beta_minus_keV",
            "betaMinusUncertainty": "q_beta_minus_unc",
            "electronCapture": "q_ec_keV",
            "electronCaptureUncertainty": "q_ec_unc",
            "positronEmission": "q_beta_plus_keV",
            "positronEmissionUncertainty": "q_beta_plus_unc",
            "bindingEnergy": "be_per_a_keV",
            "bindingEnergyUncertainty": "be_per_a_unc",
            "bindingEnergyLDMFit": "be_ldm_residual_keV",
            "bindingEnergyLDMFitUncertainty": "be_ldm_residual_unc",
        }
    )
    num_cols = [
        "q_beta_minus_keV",
        "q_beta_minus_unc",
        "q_ec_keV",
        "q_ec_unc",
        "q_beta_plus_keV",
        "q_beta_plus_unc",
        "be_per_a_keV",
        "be_per_a_unc",
        "be_ldm_residual_keV",
        "be_ldm_residual_unc",
    ]
    for c in num_cols:
        df[c] = _to_float(df[c])
    return df[["Z", "N", "name"] + num_cols].drop_duplicates(["Z", "N"], keep="first")


def load_pairing_alpha() -> pd.DataFrame:
    df = pd.read_csv(EXPORT_PAIR)
    df = df.rename(
        columns={
            "z": "Z",
            "n": "N",
            "name": "name_pair",
            "pairingGap": "pairing_gap_keV",
            "pairingGapUncertainty": "pairing_gap_unc",
            "alpha": "q_alpha_keV",
            "alphaUncertainty": "q_alpha_unc",
            "deltaAlpha": "delta_q_alpha_keV",
            "deltaAlphaUncertainty": "delta_q_alpha_unc",
        }
    )
    keep = [
        "Z",
        "N",
        "pairing_gap_keV",
        "pairing_gap_unc",
        "q_alpha_keV",
        "q_alpha_unc",
        "delta_q_alpha_keV",
        "delta_q_alpha_unc",
    ]
    for c in keep[2:]:
        df[c] = _to_float(df[c])
    return df[keep].drop_duplicates(["Z", "N"], keep="first")


_MODE_ALIASES = {
    "B-": "B-",
    "B+": "B+",
    "EC": "EC",
    "EC+B+": "EC+B+",
    "EC+B+?": "EC+B+",
    "IT": "IT",
    "A": "A",
    "α": "A",
}


def normalize_mode_token(token: str) -> str:
    t = token.strip().upper()
    t = t.replace("Α", "A")  # greek lookalike
    # strip trailing ? and spaces
    t = t.rstrip("?").strip()
    # NuDat uses B- , EC+B+, a for alpha
    if t.startswith("B-"):
        # B-, B-N, B-2N, B-A ...
        if t == "B-" or t.startswith("B-="):
            return "B-"
        if t.startswith("B-N") or t.startswith("B-2N") or t.startswith("B-3N"):
            return "B-n"
        if t.startswith("B-A"):
            return "B-a"
        return "B-"
    if t.startswith("EC+B+") or t == "EC+B+":
        return "EC+B+"
    if t.startswith("EC"):
        if "P" in t and t != "EC":
            return "ECp"
        return "EC"
    if t.startswith("B+"):
        return "B+"
    if t in {"A", "ALPHA"} or t.startswith("A=") or t == "A?":
        return "A"
    if t.startswith("IT"):
        return "IT"
    if t.startswith("N") and not t.startswith("NN"):
        return "n"
    if t.startswith("P"):
        return "p"
    if t.startswith("F"):
        return "SF"
    return t or "UNKNOWN"


def parse_decay_modes(raw: Optional[str]) -> list[dict]:
    """Parse wallet Decay Modes string into list of {mode_code, branching_pct}."""
    if raw is None or (isinstance(raw, float) and pd.isna(raw)):
        return []
    text = str(raw).strip()
    if not text:
        return []
    channels = []
    for part in text.split(","):
        part = part.strip()
        if not part:
            continue
        # patterns: "B- = 100", "B-n = 16 1", "EC = 100", "B- ~ 100"
        m = re.match(
            r"^(.+?)\s*(?:=|~)\s*([0-9]*\.?[0-9]+)\s*([0-9]*\.?[0-9]+)?\s*$",
            part,
        )
        if m:
            mode = normalize_mode_token(m.group(1))
            branching = float(m.group(2))
            channels.append({"mode_code": mode, "branching_pct": branching})
            continue
        # mode without branching
        mode = normalize_mode_token(part)
        channels.append({"mode_code": mode, "branching_pct": None})
    return channels


def dominant_mode_class(channels: list[dict], is_stable: bool) -> str:
    if is_stable:
        return "STABLE"
    if not channels:
        return "UNKNOWN"
    # Prefer highest branching; if none, first listed
    ranked = sorted(
        channels,
        key=lambda c: (-1 if c["branching_pct"] is None else -c["branching_pct"]),
    )
    code = ranked[0]["mode_code"]
    if code in {"B-", "B-n", "B-a"}:
        return "B-"
    if code in {"EC", "EC+B+", "B+", "ECp"}:
        return "EC_BP"
    if code == "A":
        return "ALPHA"
    if code == "IT":
        return "IT"
    return "OTHER"


def build_decay_channels(wallet: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for idx, r in wallet.iterrows():
        channels = parse_decay_modes(r.get("decay_modes_raw"))
        for ch in channels:
            rows.append(
                {
                    "wallet_row": idx,
                    "Z": int(r["Z"]),
                    "A": int(r["A"]),
                    "N": int(r["N"]),
                    "level_index": int(r["level_index"]),
                    "mode_code": ch["mode_code"],
                    "branching_pct": ch["branching_pct"],
                }
            )
    return pd.DataFrame(rows)


def build_nuclides() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    wallet = load_wallet()
    hl = load_halflife_chart()
    qbe = load_q_and_be()
    pair = load_pairing_alpha()

    # Ground states for chart join / main analysis table
    gs = wallet[wallet["level_index"] == 0].copy()
    gs["dominant_mode"] = [
        dominant_mode_class(parse_decay_modes(raw), bool(stable))
        for raw, stable in zip(gs["decay_modes_raw"], gs["is_stable_wallet"])
    ]

    merged = gs.merge(hl, on=["Z", "N"], how="left")
    merged = merged.merge(qbe, on=["Z", "N"], how="left")
    merged = merged.merge(pair, on=["Z", "N"], how="left")

    merged["half_life_s"] = merged["half_life_s_chart"].where(
        merged["half_life_s_chart"].notna(), merged["half_life_s_wallet"]
    )
    merged["is_stable"] = merged["is_stable_wallet"] | merged["dominant_mode"].eq("STABLE")
    merged.loc[merged["is_stable"], "half_life_s"] = pd.NA
    merged["N_over_Z"] = merged["N"] / merged["Z"].replace(0, pd.NA)
    if "name" not in merged.columns:
        merged["name"] = pd.NA
    merged["name"] = merged["name"].fillna(
        merged["A"].astype(int).astype(str) + merged["element"].astype(str)
    )

    # Full states table (including isomers) for nuclear_state
    states = wallet.copy()
    states["dominant_mode"] = [
        dominant_mode_class(parse_decay_modes(raw), bool(stable))
        for raw, stable in zip(states["decay_modes_raw"], states["is_stable_wallet"])
    ]
    states = states.merge(hl, on=["Z", "N"], how="left")
    states["half_life_s"] = states.apply(
        lambda r: (
            None
            if r["is_stable_wallet"]
            else (
                r["half_life_s_chart"]
                if r["level_index"] == 0 and pd.notna(r["half_life_s_chart"])
                else r["half_life_s_wallet"]
            )
        ),
        axis=1,
    )
    states["is_stable"] = states["is_stable_wallet"]

    decay_channels = build_decay_channels(wallet)
    return merged, states, decay_channels


def write_processed() -> dict[str, Path]:
    PROCESSED.mkdir(parents=True, exist_ok=True)
    nuclides, states, decay_channels = build_nuclides()

    nuclide_cols = [
        "Z",
        "N",
        "A",
        "element",
        "name",
        "spin_parity",
        "mass_excess_keV",
        "abundance",
        "half_life_s",
        "is_stable",
        "dominant_mode",
        "decay_modes_raw",
        "N_over_Z",
        "q_beta_minus_keV",
        "q_ec_keV",
        "q_beta_plus_keV",
        "be_per_a_keV",
        "be_ldm_residual_keV",
        "pairing_gap_keV",
        "q_alpha_keV",
        "delta_q_alpha_keV",
    ]
    nuclides_out = nuclides[nuclide_cols].sort_values(["Z", "A"]).reset_index(drop=True)

    state_cols = [
        "Z",
        "N",
        "A",
        "element",
        "level_index",
        "level_energy_keV",
        "spin_parity",
        "mass_excess_keV",
        "abundance",
        "half_life_s",
        "is_stable",
        "dominant_mode",
        "decay_modes_raw",
    ]
    states_out = states[state_cols].sort_values(["Z", "A", "level_index"]).reset_index(drop=True)

    paths = {
        "nuclides": PROCESSED / "nuclides.csv",
        "nuclear_states": PROCESSED / "nuclear_states.csv",
        "decay_channels": PROCESSED / "decay_channels.csv",
    }
    nuclides_out.to_csv(paths["nuclides"], index=False)
    states_out.to_csv(paths["nuclear_states"], index=False)
    decay_channels.to_csv(paths["decay_channels"], index=False)
    return paths


if __name__ == "__main__":
    paths = write_processed()
    for k, p in paths.items():
        df = pd.read_csv(p)
        print(f"{k}: {len(df)} rows -> {p}")
