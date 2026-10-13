import plotly.express as px
import streamlit as st

import queries as Q
from db import ground_states, run_query, setup_page
from style import MODE_ORDER, PALETTE, mode_label

setup_page("N/Z por modo")

st.title("Razón N/Z por modo dominante")
st.markdown(
    "Estadísticos agregados en SQL (`JOIN` + `GROUP BY`, consultas 1 y 2) y distribución "
    "completa de $N/Z$ para comparar las familias $\\beta^-$, estables y EC/$\\beta^+$."
)

gs = ground_states()
available = [m for m in MODE_ORDER if m in set(gs["dominant_mode"])]

with st.sidebar:
    st.header("Filtros")
    z_lo, z_hi = int(gs["Z"].min()), int(gs["Z"].max())
    z_range = st.slider("Rango de Z", z_lo, z_hi, (max(z_lo, 1), z_hi))
    modes = st.multiselect(
        "Modos a comparar",
        available,
        default=[m for m in ["B-", "STABLE", "EC_BP"] if m in available],
        format_func=mode_label,
    )
    n_bins = st.slider("Bins del histograma", 10, 120, 40, step=5)
    dist_kind = st.radio("Gráfico de distribución", ["Caja", "Violín"], horizontal=True)

params = {"z_min": z_range[0], "z_max": z_range[1]}

st.subheader("1 · ⟨N/Z⟩ ± σ por modo dominante")
summary = run_query(Q.MODE_SUMMARY, params)
summary.insert(1, "modo", summary["dominant_mode"].map(mode_label))
col_t, col_p = st.columns([2, 3])
with col_t:
    st.dataframe(summary, hide_index=True, width="stretch")
with col_p:
    plot_df = summary.dropna(subset=["mean_N_over_Z"])
    fig = px.bar(
        plot_df,
        x="dominant_mode",
        y="mean_N_over_Z",
        error_y="sd_N_over_Z",
        color="dominant_mode",
        color_discrete_map=PALETTE,
        category_orders={"dominant_mode": available},
        labels={"dominant_mode": "Modo", "mean_N_over_Z": "⟨N/Z⟩"},
    )
    fig.update_layout(showlegend=False, height=340)
    st.plotly_chart(fig, width="stretch")

st.subheader("2 · Mínimo / media / máximo de N/Z (β⁻, estables, EC/β⁺)")
minmax = run_query(Q.NZ_MINMAX, params)
minmax.insert(1, "modo", minmax["dominant_mode"].map(mode_label))
st.dataframe(minmax, hide_index=True, width="stretch")

if len(minmax) == 3:
    m = minmax.set_index("dominant_mode")["mean_nz"]
    ordered = m.get("B-", 0) > m.get("STABLE", 0) > m.get("EC_BP", 0)
    msg = (
        f"⟨N/Z⟩(β⁻) = {m['B-']:.3f}  >  ⟨N/Z⟩(estable) = {m['STABLE']:.3f}  >  "
        f"⟨N/Z⟩(EC/β⁺) = {m['EC_BP']:.3f}"
    )
    (st.success if ordered else st.warning)(
        msg + (" — los estables quedan en el medio del valle." if ordered else "")
    )

st.subheader("3 · Distribución de N/Z")
sel = gs[gs["dominant_mode"].isin(modes) & gs["Z"].between(*z_range)].dropna(
    subset=["N_over_Z"]
)
if sel.empty:
    st.info("Selecciona al menos un modo.")
    st.stop()

order = [m for m in available if m in modes]
col_h, col_b = st.columns(2)
with col_h:
    fig = px.histogram(
        sel,
        x="N_over_Z",
        color="dominant_mode",
        color_discrete_map=PALETTE,
        category_orders={"dominant_mode": order},
        nbins=n_bins,
        barmode="overlay",
        opacity=0.55,
        labels={"N_over_Z": "N/Z", "dominant_mode": "Modo"},
    )
    fig.update_layout(height=420, yaxis_title="Conteo")
    st.plotly_chart(fig, width="stretch")
with col_b:
    plot = px.box if dist_kind == "Caja" else px.violin
    kwargs = {"points": False} if dist_kind == "Caja" else {"box": True, "points": False}
    fig = plot(
        sel,
        x="dominant_mode",
        y="N_over_Z",
        color="dominant_mode",
        color_discrete_map=PALETTE,
        category_orders={"dominant_mode": order},
        labels={"N_over_Z": "N/Z", "dominant_mode": "Modo"},
        **kwargs,
    )
    fig.update_layout(height=420, showlegend=False)
    st.plotly_chart(fig, width="stretch")

st.caption(
    "Las tres familias se solapan poco en $N/Z$: el modo dominante queda casi determinado "
    "por el lado del valle en que se encuentra el nuclido. Para ver cómo se desplaza el valle "
    "con $Z$, ir a **Frontera y valle**."
)
