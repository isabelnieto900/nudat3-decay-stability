import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from db import ground_states, setup_page
from style import MODE_ORDER, PALETTE, mode_label

A_C_MEV = 0.715

setup_page("Coulomb")

st.title("¿Por qué sube N/Z? Estimación coulombiana (gota líquida)")
st.markdown(
    "NuDat no exporta la energía de Coulomb, pero en el modelo de gota líquida (LDM)\n\n"
    "$$E_C \\approx a_C\\,\\frac{Z(Z-1)}{A^{1/3}}, \\qquad a_C \\approx "
    f"{A_C_MEV}\\ \\text{{MeV}}$$\n\n"
    "Se calcula con $Z$ y $A$ leídos de MySQL. Si la repulsión crece, el núcleo estable "
    "necesita relativamente más neutrones: ⟨N/Z⟩ debería crecer con el factor coulombiano."
)

gs = ground_states()
df = gs[(gs["A"] > 0) & gs["N_over_Z"].notna()].copy()
df["coulomb_factor"] = df["Z"] * (df["Z"] - 1) / np.power(df["A"], 1.0 / 3.0)
df["E_C_MeV_est"] = A_C_MEV * df["coulomb_factor"]

available = [m for m in MODE_ORDER if m in set(df["dominant_mode"])]
with st.sidebar:
    st.header("Parámetros")
    modes = st.multiselect(
        "Modos",
        available,
        default=[m for m in ["B-", "STABLE", "EC_BP"] if m in available],
        format_func=mode_label,
    )
    n_bins = st.slider("Nº de bins del factor de Coulomb", 5, 40, 12)
    color_scatter = st.checkbox("Colorear la dispersión por modo", value=False)

st.subheader("1 · Escala coulombiana frente a Z")
fig = px.scatter(
    df,
    x="Z",
    y="coulomb_factor",
    color="dominant_mode" if color_scatter else None,
    color_discrete_map=PALETTE,
    category_orders={"dominant_mode": available},
    opacity=0.4 if not color_scatter else 0.7,
    hover_data={"name": True, "A": True, "E_C_MeV_est": ":.1f"},
    labels={
        "coulomb_factor": "Z(Z−1)/A^(1/3)",
        "dominant_mode": "Modo",
        "E_C_MeV_est": "E_C est. (MeV)",
    },
)
if not color_scatter:
    fig.update_traces(marker=dict(color="#555555"))
fig.update_traces(marker=dict(size=4))
fig.update_layout(height=400)
st.plotly_chart(fig, width="stretch")

st.subheader("2 · ⟨N/Z⟩ frente al factor de Coulomb, por modo")
sub = df[df["dominant_mode"].isin(modes)].copy()
if sub.empty:
    st.info("Selecciona al menos un modo.")
    st.stop()

sub["C_bin"] = pd.cut(sub["coulomb_factor"], bins=n_bins)
agg = (
    sub.groupby(["C_bin", "dominant_mode"], observed=True)
    .agg(center=("coulomb_factor", "mean"), mean_nz=("N_over_Z", "mean"), n=("N_over_Z", "size"))
    .reset_index()
)

fig = go.Figure()
for mode in [m for m in available if m in modes]:
    part = agg[agg["dominant_mode"] == mode].sort_values("center")
    fig.add_trace(
        go.Scatter(
            x=part["center"],
            y=part["mean_nz"],
            mode="lines+markers",
            name=mode_label(mode),
            marker=dict(color=PALETTE[mode], size=8),
            line=dict(color=PALETTE[mode]),
            customdata=part["n"],
            hovertemplate="factor≈%{x:.0f}<br>⟨N/Z⟩=%{y:.3f}<br>n=%{customdata}",
        )
    )
fig.update_layout(
    height=440, xaxis_title="Z(Z−1)/A^(1/3)", yaxis_title="⟨N/Z⟩", hovermode="x unified"
)
st.plotly_chart(fig, width="stretch")

st.subheader("3 · Energía de Coulomb estimada por modo")
ec = (
    sub.groupby("dominant_mode")["E_C_MeV_est"]
    .agg(n="count", media_MeV="mean", mediana_MeV="median")
    .round(1)
    .sort_values("media_MeV")
    .reset_index()
)
ec.insert(1, "modo", ec["dominant_mode"].map(mode_label))
st.dataframe(ec, hide_index=True, width="stretch")

st.caption(
    "El factor coulombiano crece aproximadamente como $Z^{5/3}$. Si ⟨N/Z⟩ de los estables "
    "sube con él, el desplazamiento del valle hacia $N > Z$ es coherente con la repulsión "
    "electrostática entre protones."
)
