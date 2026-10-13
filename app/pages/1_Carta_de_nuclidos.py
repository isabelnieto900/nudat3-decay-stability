import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from db import ground_states, setup_page
from style import MODE_ORDER, PALETTE, mode_label

setup_page("Carta de nuclidos")

st.title("Carta de nuclidos N–Z")
st.markdown(
    "Cada punto es el **estado base** de un nuclido (consulta 4 de `sql/queries.sql`: "
    "`nuclide` ⋈ `nuclear_state` ⋈ `element`, `level_index = 0`). "
    "$\\beta^-$ aparece a la derecha (exceso de neutrones), EC/$\\beta^+$ a la izquierda "
    "y los estables forman la franja central del valle."
)

gs = ground_states()
available = [m for m in MODE_ORDER if m in set(gs["dominant_mode"])]

with st.sidebar:
    st.header("Filtros")
    modes = st.multiselect(
        "Modos dominantes", available, default=available, format_func=mode_label
    )
    z_lo, z_hi = int(gs["Z"].min()), int(gs["Z"].max())
    z_range = st.slider("Rango de Z", z_lo, z_hi, (z_lo, z_hi))
    n_lo, n_hi = int(gs["N"].min()), int(gs["N"].max())
    n_range = st.slider("Rango de N", n_lo, n_hi, (n_lo, n_hi))
    color_by = st.radio("Colorear por", ["Modo dominante", "log₁₀ t½ (s)"])
    show_nz1 = st.checkbox("Línea N = Z", value=True)
    marker_size = st.slider("Tamaño de punto", 2, 12, 5)

sel = gs[
    gs["dominant_mode"].isin(modes)
    & gs["Z"].between(*z_range)
    & gs["N"].between(*n_range)
]

hover = {
    "name": True,
    "Z": True,
    "N": True,
    "A": True,
    "N_over_Z": ":.3f",
    "dominant_mode": True,
    "half_life": True,
    "decay_modes_raw": True,
}
labels = {
    "N_over_Z": "N/Z",
    "dominant_mode": "Modo",
    "half_life": "t½",
    "decay_modes_raw": "Modos (NuDat)",
    "log10_half_life_s": "log₁₀ t½ (s)",
}

if color_by == "Modo dominante":
    fig = px.scatter(
        sel,
        x="N",
        y="Z",
        color="dominant_mode",
        color_discrete_map=PALETTE,
        category_orders={"dominant_mode": available},
        hover_data=hover,
        labels=labels,
    )
else:
    fig = px.scatter(
        sel.dropna(subset=["log10_half_life_s"]),
        x="N",
        y="Z",
        color="log10_half_life_s",
        color_continuous_scale="Viridis",
        hover_data=hover,
        labels=labels,
    )
    stable = sel[sel["is_stable"]]
    fig.add_trace(
        go.Scatter(
            x=stable["N"],
            y=stable["Z"],
            mode="markers",
            marker=dict(color="black", size=marker_size, symbol="square"),
            name="Estable",
            text=stable["name"],
            hovertemplate="%{text}<br>N=%{x}<br>Z=%{y}<extra>Estable</extra>",
        )
    )

fig.update_traces(marker=dict(size=marker_size), selector=dict(mode="markers"))

if show_nz1 and len(sel):
    hi = int(max(sel["N"].max(), sel["Z"].max()))
    fig.add_trace(
        go.Scatter(
            x=[0, hi], y=[0, hi], mode="lines", name="N = Z",
            line=dict(color="gray", dash="dash", width=1), hoverinfo="skip",
        )
    )

fig.update_layout(
    height=680,
    xaxis_title="N (neutrones)",
    yaxis_title="Z (protones)",
    legend_title_text="Modo",
)
fig.update_xaxes(range=[n_range[0] - 2, n_range[1] + 2])
fig.update_yaxes(range=[z_range[0] - 2, z_range[1] + 2])
st.plotly_chart(fig, width="stretch")

c1, c2, c3 = st.columns(3)
c1.metric("Nuclidos mostrados", f"{len(sel):,}")
c2.metric("Estables en la selección", int(sel["is_stable"].sum()))
c3.metric("⟨N/Z⟩ de la selección", f"{sel['N_over_Z'].mean():.3f}" if len(sel) else "—")

st.info(
    "A $Z$ altos la franja negra de estables se adelgaza y desaparece: "
    "por encima de Pb/Bi solo quedan modos radiactivos ($\\beta$, $\\alpha$, fisión…). "
    "Usa los filtros para aislar un modo o una región."
)
