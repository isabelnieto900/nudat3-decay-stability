"""App Streamlit — NuDat 3: N/Z vs modo de desintegración dominante.

Ejecutar:  streamlit run app/Inicio.py
"""

import plotly.express as px
import streamlit as st

import queries as Q
from db import run_query, setup_page, table_counts
from style import MODE_ORDER, PALETTE, QUESTION, mode_label

setup_page("Inicio")

st.title("NuDat 3 — Estabilidad nuclear y modos de desintegración")
st.markdown(f"**Pregunta científica:** {QUESTION}")
st.caption(
    "Datos: [NuDat 3 (NNDC)](https://www.nndc.bnl.gov/nudat3/) → limpieza → MySQL "
    "(`element`, `nuclide`, `nuclear_state`, `decay_channel`). "
    "Todas las vistas consultan la base de datos relacional en vivo."
)

ov = run_query(Q.OVERVIEW).iloc[0]
counts = table_counts().set_index("tabla")["filas"]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Estados base (GS)", f"{int(ov['n_gs']):,}")
c2.metric("GS estables", f"{int(ov['n_stable']):,}")
c3.metric("Rango de Z", f"{int(ov['z_min'])} – {int(ov['z_max'])}")
c4.metric("Último Z con estables", int(ov["z_max_stable"]))

with st.expander("Filas por tabla en MySQL"):
    st.dataframe(counts.rename("filas").to_frame(), width="stretch")

st.subheader("¿Cuántos estados base hay por modo dominante?")
modes = run_query(Q.MODE_SUMMARY, {"z_min": 0, "z_max": 999})
modes["modo"] = modes["dominant_mode"].map(mode_label)
order = [m for m in MODE_ORDER if m in set(modes["dominant_mode"])]

col_plot, col_table = st.columns([3, 2])
with col_plot:
    fig = px.bar(
        modes,
        x="dominant_mode",
        y="n_nuclides",
        color="dominant_mode",
        color_discrete_map=PALETTE,
        category_orders={"dominant_mode": order},
        hover_data={"modo": True, "mean_N_over_Z": True, "dominant_mode": False},
        labels={"dominant_mode": "Modo dominante", "n_nuclides": "Nº de estados base"},
    )
    fig.update_layout(showlegend=False, height=380)
    st.plotly_chart(fig, width="stretch")
with col_table:
    st.dataframe(
        modes[["dominant_mode", "modo", "n_nuclides", "mean_N_over_Z", "sd_N_over_Z"]],
        hide_index=True,
        width="stretch",
    )

st.subheader("Recorrido de la exploración")
st.page_link("pages/1_Carta_de_nuclidos.py", label="1 · Carta de nuclidos N–Z por modo", icon=":material/grid_on:")
st.page_link("pages/2_NZ_por_modo.py", label="2 · Estadísticas y distribución de N/Z por modo", icon=":material/bar_chart:")
st.page_link("pages/3_Frontera_y_valle.py", label="3 · Frontera N/Z y valle de estabilidad por bins de Z", icon=":material/show_chart:")
st.page_link("pages/4_Coulomb.py", label="4 · ¿Por qué sube N/Z? Factor de Coulomb (LDM)", icon=":material/bolt:")
st.page_link("pages/5_Explorador.py", label="5 · Explorador de nuclidos, estados y canales", icon=":material/search:")
