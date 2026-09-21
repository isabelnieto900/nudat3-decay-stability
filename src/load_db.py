"""Load processed CSVs into MySQL.

Run inside the Jupyter container (MYSQL_HOST=mysql) or from the host
(MYSQL_HOST=127.0.0.1) after `docker compose up`.

Does NOT re-run cleaning; reads data/processed/ as produced by notebooks/02_clean_etl.ipynb.
"""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"


def database_url() -> str:
    host = os.getenv("MYSQL_HOST", "127.0.0.1")
    port = os.getenv("MYSQL_PORT", "3306")
    user = os.getenv("MYSQL_USER", "nudat")
    password = os.getenv("MYSQL_PASSWORD", "nudat")
    database = os.getenv("MYSQL_DATABASE", "nudat")
    return f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"


def get_engine():
    return create_engine(database_url(), pool_pre_ping=True)


def load_all() -> None:
    nuclides = pd.read_csv(PROCESSED / "nuclides.csv")
    states = pd.read_csv(PROCESSED / "nuclear_states.csv")
    channels = pd.read_csv(PROCESSED / "decay_channels.csv")

    for df in (nuclides, states):
        for col in ("is_stable", "is_resonance"):
            if col in df.columns:
                df[col] = df[col].fillna(False).astype(bool).astype(int)

    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text("SET FOREIGN_KEY_CHECKS=0"))
        for table in [
            "decay_channel",
            "nuclide_qvalue",
            "nuclide_structure",
            "nuclear_state",
            "nuclide",
            "element",
        ]:
            conn.execute(text(f"DELETE FROM {table}"))
        conn.execute(text("SET FOREIGN_KEY_CHECKS=1"))

        elements = (
            states[["Z", "element"]]
            .drop_duplicates("Z")
            .rename(columns={"element": "symbol"})
            .sort_values("Z")
        )
        elements.to_sql("element", conn, if_exists="append", index=False)

        # One nuclide row per (Z,A): prefer name from nuclides (GS chart join)
        base = states[["Z", "A", "N", "element"]].drop_duplicates(["Z", "A"])
        nuclide_rows = base.merge(
            nuclides[["Z", "A", "name"]], on=["Z", "A"], how="left"
        )
        nuclide_rows["name"] = nuclide_rows["name"].fillna(
            nuclide_rows["A"].astype(int).astype(str) + nuclide_rows["element"].astype(str)
        )
        nuclide_rows[["Z", "A", "N", "name"]].to_sql(
            "nuclide", conn, if_exists="append", index=False
        )

        id_map = pd.read_sql(text("SELECT nuclide_id, Z, A FROM nuclide"), conn)

        st = states.merge(id_map, on=["Z", "A"], how="left")
        st_out = st.rename(columns={"level_energy_keV": "energy_keV"})[
            [
                "nuclide_id",
                "level_index",
                "energy_keV",
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
        ]
        st_out.to_sql("nuclear_state", conn, if_exists="append", index=False)

        state_ids = pd.read_sql(
            text("SELECT state_id, nuclide_id, level_index FROM nuclear_state"),
            conn,
        ).merge(id_map, on="nuclide_id")

        ch = channels.merge(
            state_ids[["state_id", "Z", "A", "level_index"]],
            on=["Z", "A", "level_index"],
            how="inner",
        )
        ch[["state_id", "mode_code", "branching_pct"]].to_sql(
            "decay_channel", conn, if_exists="append", index=False
        )

        qv = nuclides.merge(id_map, on=["Z", "A"], how="inner")
        qv[
            [
                "nuclide_id",
                "q_beta_minus_keV",
                "q_ec_keV",
                "q_beta_plus_keV",
                "q_alpha_keV",
                "delta_q_alpha_keV",
            ]
        ].to_sql("nuclide_qvalue", conn, if_exists="append", index=False)

        struct = nuclides.merge(id_map, on=["Z", "A"], how="inner")
        struct[
            [
                "nuclide_id",
                "be_per_a_keV",
                "be_ldm_residual_keV",
                "pairing_gap_keV",
            ]
        ].to_sql("nuclide_structure", conn, if_exists="append", index=False)

    print("Load complete.")
    print("MYSQL_HOST =", os.getenv("MYSQL_HOST", "127.0.0.1"))
    with engine.connect() as conn:
        for table in [
            "element",
            "nuclide",
            "nuclear_state",
            "decay_channel",
            "nuclide_qvalue",
            "nuclide_structure",
        ]:
            n = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
            print(f"  {table}: {n}")


if __name__ == "__main__":
    load_all()
