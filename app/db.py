"""Conexión a MySQL (SQLAlchemy + PyMySQL) y carga cacheada de datos para la app."""

from __future__ import annotations

import os
import sys
from decimal import Decimal
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.load_db import database_url  # noqa: E402

import queries as Q  # noqa: E402
from style import format_half_life  # noqa: E402


@st.cache_resource
def get_engine():
    return create_engine(database_url(), pool_pre_ping=True)


@st.cache_data(ttl=600, show_spinner=False)
def run_query(sql: str, params: dict | None = None) -> pd.DataFrame:
    with get_engine().connect() as conn:
        df = pd.read_sql(text(sql), conn, params=params or {})
    # MySQL devuelve AVG/ROUND/SUM como DECIMAL → objetos Decimal en pandas
    for col in df.columns[df.dtypes == object]:
        values = df[col].dropna()
        if len(values) and all(isinstance(v, Decimal) for v in values):
            df[col] = df[col].astype(float)
    return df


def table_counts() -> pd.DataFrame:
    return run_query(Q.TABLE_COUNTS)


@st.cache_data(ttl=600, show_spinner=False)
def ground_states() -> pd.DataFrame:
    df = run_query(Q.GROUND_STATES)
    df["is_stable"] = df["is_stable"].astype(bool)
    df["N_over_Z"] = df["N_over_Z"].astype(float)
    df["log10_half_life_s"] = np.log10(df["half_life_s"].where(df["half_life_s"] > 0))
    df["half_life"] = [
        format_half_life(s, stable) for s, stable in zip(df["half_life_s"], df["is_stable"])
    ]
    return df


def setup_page(title: str) -> None:
    """Configura la página y detiene la ejecución si MySQL no responde o está vacía."""
    st.set_page_config(page_title=f"{title} · NuDat 3", layout="wide")
    host = os.getenv("MYSQL_HOST", "127.0.0.1")
    db = os.getenv("MYSQL_DATABASE", "nudat")
    st.sidebar.caption(f"MySQL: `{host}` / base `{db}`")

    try:
        counts = table_counts()
    except SQLAlchemyError as exc:
        st.error(
            f"No se pudo conectar a MySQL en `{host}`. "
            "Comprueba que los contenedores estén activos (`docker compose ps`)."
        )
        st.exception(exc)
        st.stop()

    if counts.set_index("tabla").loc["nuclear_state", "filas"] == 0:
        st.warning(
            "La base de datos está vacía. Carga los datos con:\n\n"
            "```bash\ndocker compose exec jupyter python -m src.load_db\n```"
        )
        st.stop()
