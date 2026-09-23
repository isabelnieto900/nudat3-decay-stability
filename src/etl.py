"""ETL helpers for NuDat wallet cards + Chart half-life export.

NOTE: La limpieza oficial del proyecto está en notebooks/02_clean_etl.ipynb
(notebook-only). Este módulo es un utilitario opcional; la fuente de verdad
es el notebook 02.
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
            "Spin-Parity": "spin_parity",
            "Half-Life": "half_life_raw",
            "Half-Life (Unit)": "half_life_unit",
            "Abundance": "abundance",
            "Mass Excess": "mass_excess_keV",
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
        "spin_parity",
        "half_life_raw",
        "half_life_unit",
        "abundance",
        "mass_excess_keV",
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
    for col in ["mass_excess_keV", "abundance", "level_energy"]:
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
    return df[["Z", "N", "half_life_s_chart"]].drop_duplicates(["Z", "N"], keep="first")


def normalize_mode_token(token: str) -> str:
    t = token.strip().upper()
    t = t.replace("Α", "A")
    t = t.rstrip("?").strip()
    if t.startswith("B-"):
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
        m = re.match(
            r"^(.+?)\s*(?:=|~)\s*([0-9]*\.?[0-9]+)\s*([0-9]*\.?[0-9]+)?\s*$",
            part,
        )
        if m:
            mode = normalize_mode_token(m.group(1))
            branching = float(m.group(2))
            channels.append({"mode_code": mode, "branching_pct": branching})
            continue
        mode = normalize_mode_token(part)
        channels.append({"mode_code": mode, "branching_pct": None})
    return channels


def dominant_mode_class(channels: list[dict], is_stable: bool) -> str:
    if is_stable:
        return "STABLE"
    if not channels:
        return "UNKNOWN"
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

    states = wallet.copy()
    states["is_resonance"] = (
        states["decay_width"].notna()
        & states["half_life_raw"].isna()
        & ~states["is_stable_wallet"]
    )
    states["dominant_mode"] = [
        dominant_mode_class(parse_decay_modes(raw), bool(stable))
        for raw, stable in zip(states["decay_modes_raw"], states["is_stable_wallet"])
    ]
    states = states.merge(hl, on=["Z", "N"], how="left")
    states["is_stable"] = states["is_stable_wallet"] | states["dominant_mode"].eq("STABLE")

    def pick_half_life(row):
        if row["is_stable"]:
            return pd.NA
        if row["level_index"] == 0 and pd.notna(row.get("half_life_s_chart")):
            return row["half_life_s_chart"]
        return row["half_life_s_wallet"]

    states["half_life_s"] = states.apply(pick_half_life, axis=1)
    states["half_life_source"] = states.apply(
        lambda r: (
            "none"
            if r["is_stable"]
            else (
                "chart"
                if r["level_index"] == 0 and pd.notna(r.get("half_life_s_chart"))
                else ("wallet" if pd.notna(r["half_life_s_wallet"]) else "none")
            )
        ),
        axis=1,
    )

    gs = states[states["level_index"] == 0].copy()
    gs["name"] = gs["A"].astype(int).astype(str) + gs["element"].astype(str)
    gs["N_over_Z"] = gs["N"] / gs["Z"].replace(0, pd.NA)

    decay_channels = build_decay_channels(wallet)
    return gs, states, decay_channels


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
        "half_life_source",
        "is_stable",
        "is_resonance",
        "dominant_mode",
        "decay_modes_raw",
        "N_over_Z",
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
        "half_life_source",
        "is_stable",
        "is_resonance",
        "dominant_mode",
        "decay_modes_raw",
    ]
    states_out = states[state_cols].sort_values(["Z", "A", "level_index"]).reset_index(drop=True)

    ch_out = decay_channels[["Z", "A", "N", "level_index", "mode_code", "branching_pct"]]

    paths = {
        "nuclides": PROCESSED / "nuclides.csv",
        "nuclear_states": PROCESSED / "nuclear_states.csv",
        "decay_channels": PROCESSED / "decay_channels.csv",
    }
    nuclides_out.to_csv(paths["nuclides"], index=False)
    states_out.to_csv(paths["nuclear_states"], index=False)
    ch_out.to_csv(paths["decay_channels"], index=False)
    return paths


if __name__ == "__main__":
    paths = write_processed()
    for k, p in paths.items():
        df = pd.read_csv(p)
        print(f"{k}: {len(df)} rows -> {p}")
