import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

import queries as Q
from db import run_query, setup_page
from style import PALETTE, mode_label

setup_page("Frontera y valle")

st.title("Frontera N/Z y valle de estabilidad a lo largo de Z")
st.markdown(
    "⟨N/Z⟩ por modo en bins de $Z$ (consulta 3, agregación condicional con `CASE`) "
    "y modo mayoritario por bin (consulta 6, subconsulta correlacionada)."
)

with st.sidebar:
    st.header("Parámetros")
    width = st.select_slider("Ancho del bin de Z", options=[2, 5, 10, 20], value=10)
    curves = st.multiselect(
        "Curvas de la frontera",
        ["B-", "STABLE", "EC_BP", "ALPHA"],
        default=["B-", "STABLE", "EC_BP", "ALPHA"],
        format_func=mode_label,
    )

frontier = run_query(Q.FRONTIER, {"w": width})
frontier = frontier.astype(float)
frontier["Z_bin"] = frontier["Z_bin"].astype(int)

st.subheader("1 · Frontera ⟨N/Z⟩ por modo")
markers = {"B-": "circle", "STABLE": "triangle-up", "EC_BP": "square", "ALPHA": "diamond"}
col_of = {"B-": "mean_nz_B", "STABLE": "mean_nz_STABLE", "EC_BP": "mean_nz_EC_BP", "ALPHA": "mean_nz_ALPHA"}
n_of = {"B-": "n_B", "STABLE": "n_STABLE", "EC_BP": "n_EC_BP", "ALPHA": "n_ALPHA"}

fig = go.Figure()
for mode in curves:
    fig.add_trace(
        go.Scatter(
            x=frontier["Z_bin"],
            y=frontier[col_of[mode]],
            mode="lines+markers",
            name=mode_label(mode),
            marker=dict(symbol=markers[mode], size=9, color=PALETTE[mode]),
            line=dict(color=PALETTE[mode]),
            customdata=frontier[n_of[mode]],
            hovertemplate="Z∈[%{x}, %{x}+" + str(width) + ")<br>⟨N/Z⟩=%{y:.3f}<br>n=%{customdata:.0f}",
        )
    )
fig.add_hline(y=1.0, line_dash="dash", line_color="gray", annotation_text="N/Z = 1")
fig.update_layout(
    height=460, xaxis_title=f"Z (inicio del bin de {width})", yaxis_title="⟨N/Z⟩",
    hovermode="x unified",
)
st.plotly_chart(fig, width="stretch")

with st.expander("Tabla de la frontera (resultado SQL)"):
    st.dataframe(frontier, hide_index=True, width="stretch")

st.subheader("2 · El valle: solo estados base estables")
valley = frontier[["Z_bin", "mean_nz_STABLE", "n_STABLE"]]
fig = make_subplots(
    rows=1, cols=2,
    subplot_titles=("⟨N/Z⟩ de los estables", "Nº de estados base estables por bin"),
)
fig.add_trace(
    go.Scatter(
        x=valley["Z_bin"], y=valley["mean_nz_STABLE"], mode="lines+markers",
        marker=dict(symbol="triangle-up", size=9, color=PALETTE["STABLE"]),
        line=dict(color=PALETTE["STABLE"]), name="⟨N/Z⟩ estables",
    ),
    row=1, col=1,
)
fig.add_hline(y=1.0, line_dash="dash", line_color="gray", row=1, col=1)
fig.add_trace(
    go.Bar(
        x=valley["Z_bin"], y=valley["n_STABLE"], marker_color="#444444",
        name="Nº estables", width=width * 0.8,
    ),
    row=1, col=2,
)
fig.update_xaxes(title_text="Z (bin)")
fig.update_yaxes(title_text="⟨N/Z⟩", row=1, col=1)
fig.update_yaxes(title_text="Nº GS estables", row=1, col=2)
fig.update_layout(height=400, showlegend=False)
st.plotly_chart(fig, width="stretch")

st.subheader("3 · Modo mayoritario por bin de Z")
maj = run_query(Q.MAJORITY_MODE, {"w": width})
maj["Z_bin"] = maj["Z_bin"].astype(int)
maj["modo"] = maj["majority_mode"].map(mode_label)
col_p, col_t = st.columns([3, 2])
with col_p:
    fig = px.bar(
        maj,
        x="Z_bin",
        y="n_in_mode",
        color="majority_mode",
        color_discrete_map=PALETTE,
        hover_data={"mean_nz": ":.3f", "modo": True},
        labels={"Z_bin": "Z (bin)", "n_in_mode": "Nº en el modo mayoritario", "majority_mode": "Modo"},
    )
    fig.update_traces(width=width * 0.8)
    fig.update_layout(height=380)
    st.plotly_chart(fig, width="stretch")
with col_t:
    st.dataframe(maj, hide_index=True, width="stretch", height=380)

st.subheader("Conclusiones (calculadas con los datos actuales)")
with_stable = valley.dropna(subset=["mean_nz_STABLE"])
with_stable = with_stable[with_stable["n_STABLE"] > 0]
if with_stable.empty:
    st.warning("No hay estados base estables en la base de datos.")
else:
    first, last = with_stable.iloc[0], with_stable.iloc[-1]
    peak = with_stable.loc[with_stable["mean_nz_STABLE"].idxmax()]
    z_first, z_last, z_peak = int(first["Z_bin"]), int(last["Z_bin"]), int(peak["Z_bin"])
    no_stable_bins = frontier.loc[frontier["Z_bin"] > z_last, "Z_bin"].tolist()
    st.markdown(
        f"""
1. **Estables a $Z$ pequeños → $N/Z \\sim 1$.** En el bin $Z \\in [{z_first}, {z_first + width})$
   ⟨N/Z⟩ de los estables es **{first['mean_nz_STABLE']:.3f}** (casi $N \\approx Z$).
2. **Al subir $Z$, $N/Z$ crece por la repulsión coulombiana.** Alcanza **{peak['mean_nz_STABLE']:.3f}**
   en el bin $Z \\in [{z_peak}, {z_peak + width})$; las curvas $\\beta^-$ y EC/$\\beta^+$
   suben en paralelo, manteniendo $\\beta^- >$ estable $>$ EC/$\\beta^+$.
3. **A $Z$ muy grandes deja de haber estabilidad.** El último bin con estables es
   $Z \\in [{z_last}, {z_last + width})$; en los bins que empiezan en
   {', '.join(str(b) for b in no_stable_bins) if no_stable_bins else '—'} no hay ningún estado base estable.
"""
    )
