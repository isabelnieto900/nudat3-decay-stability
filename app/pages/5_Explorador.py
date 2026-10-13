import plotly.express as px
import streamlit as st

import queries as Q
from db import ground_states, run_query, setup_page
from style import MODE_ORDER, PALETTE, format_half_life, mode_label

setup_page("Explorador")

st.title("Explorador de nuclidos, estados y canales")

tab_nuc, tab_channels, tab_table = st.tabs(
    ["Nuclido individual", "Canales más frecuentes", "Tabla de estados base"]
)

gs = ground_states()

def render_nuclide() -> None:
    elements = run_query(Q.ELEMENTS)
    z_options = elements["Z"].tolist()
    symbol_of = dict(zip(elements["Z"], elements["symbol"]))
    default_z = z_options.index(26) if 26 in z_options else 0

    col_e, col_n = st.columns(2)
    z = col_e.selectbox(
        "Elemento", z_options, index=default_z, format_func=lambda v: f"{symbol_of[v]} (Z = {v})"
    )
    isotopes = run_query(Q.NUCLIDES_OF_ELEMENT, {"z": int(z)})
    if isotopes.empty:
        st.info("Este elemento no tiene nuclidos en la base de datos.")
        return
    names = dict(zip(isotopes["nuclide_id"], isotopes["name"]))
    ids = isotopes["nuclide_id"].tolist()
    stable = gs[gs["is_stable"] & (gs["Z"] == z)]
    if stable.empty:
        default_id = ids[len(ids) // 2]
    else:
        default_id = int(stable.loc[stable["abundance"].fillna(0).idxmax(), "nuclide_id"])
    nuclide_id = col_n.selectbox(
        "Isótopo", ids, index=ids.index(default_id), format_func=lambda i: names[i]
    )

    chain = gs[gs["Z"] == z].copy()
    chain["seleccionado"] = chain["nuclide_id"] == nuclide_id
    fig = px.scatter(
        chain,
        x="A",
        y="N_over_Z",
        color="dominant_mode",
        color_discrete_map=PALETTE,
        category_orders={"dominant_mode": [m for m in MODE_ORDER if m in set(chain["dominant_mode"])]},
        symbol="seleccionado",
        symbol_map={True: "star", False: "circle"},
        hover_data={"name": True, "half_life": True, "seleccionado": False},
        labels={"A": "A (número másico)", "N_over_Z": "N/Z", "dominant_mode": "Modo"},
        title=f"Cadena isotópica de {symbol_of[z]}: N/Z y modo dominante (estados base)",
    )
    fig.update_traces(marker=dict(size=11))
    fig.update_layout(height=380)
    st.plotly_chart(fig, width="stretch")

    states = run_query(Q.NUCLIDE_STATES, {"nuclide_id": int(nuclide_id)})
    channels = run_query(Q.NUCLIDE_CHANNELS, {"nuclide_id": int(nuclide_id)})
    row = isotopes.set_index("nuclide_id").loc[nuclide_id]

    st.subheader(names[nuclide_id])
    gs_state = states[states["level_index"] == 0]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Z / N / A", f"{z} / {int(row['N'])} / {int(row['A'])}")
    c2.metric("N/Z", f"{row['N'] / z:.3f}" if z else "—")
    if not gs_state.empty:
        g = gs_state.iloc[0]
        c3.metric("Modo dominante (GS)", mode_label(g["dominant_mode"] or "UNKNOWN"))
        c4.metric("t½ (GS)", format_half_life(g["half_life_s"], bool(g["is_stable"])))

    states_view = states.copy()
    states_view["t½"] = [
        format_half_life(s, bool(stb)) for s, stb in zip(states_view["half_life_s"], states_view["is_stable"])
    ]
    st.markdown("**Estados nucleares** (`nuclear_state`; `level_index = 0` es el estado base)")
    st.dataframe(
        states_view[
            ["level_index", "energy_keV", "spin_parity", "t½", "half_life_s", "half_life_source",
             "dominant_mode", "abundance", "mass_excess_keV", "decay_modes_raw"]
        ],
        hide_index=True,
        width="stretch",
    )

    st.markdown("**Canales de desintegración** (`decay_channel` ⋈ `nuclear_state`)")
    if channels.empty:
        st.caption("Sin canales registrados (nuclido estable o sin datos de ramificación).")
    else:
        col_t, col_p = st.columns([2, 3])
        col_t.dataframe(channels, hide_index=True, width="stretch")
        plot_ch = channels.dropna(subset=["branching_pct"]).copy()
        if not plot_ch.empty:
            plot_ch["estado"] = "nivel " + plot_ch["level_index"].astype(str)
            fig = px.bar(
                plot_ch,
                x="branching_pct",
                y="mode_code",
                color="estado",
                orientation="h",
                barmode="group",
                labels={"branching_pct": "Ramificación (%)", "mode_code": "Canal"},
            )
            fig.update_layout(height=300)
            col_p.plotly_chart(fig, width="stretch")


with tab_nuc:
    render_nuclide()

with tab_channels:
    st.markdown(
        "Canales más frecuentes en estados base (consulta 7: `decay_channel` ⋈ `nuclear_state`, "
        "`GROUP BY mode_code`)."
    )
    top_n = st.slider("Nº de canales", 5, 40, 15)
    top = run_query(Q.TOP_CHANNELS, {"limit": int(top_n)})
    col_p, col_t = st.columns([3, 2])
    with col_p:
        fig = px.bar(
            top.iloc[::-1],
            x="n_channels",
            y="mode_code",
            orientation="h",
            color="mean_branching",
            color_continuous_scale="Blues",
            labels={
                "n_channels": "Nº de canales",
                "mode_code": "Canal",
                "mean_branching": "Ramificación media (%)",
            },
        )
        fig.update_layout(height=max(350, 22 * len(top)))
        st.plotly_chart(fig, width="stretch")
    with col_t:
        st.dataframe(top, hide_index=True, width="stretch")

with tab_table:
    st.markdown("Estados base con filtros; descarga el resultado como CSV.")
    available = [m for m in MODE_ORDER if m in set(gs["dominant_mode"])]
    f1, f2, f3 = st.columns(3)
    modes = f1.multiselect("Modos", available, default=available, format_func=mode_label)
    z_lo, z_hi = int(gs["Z"].min()), int(gs["Z"].max())
    z_range = f2.slider("Rango de Z", z_lo, z_hi, (z_lo, z_hi), key="table_z")
    nz = gs["N_over_Z"].dropna()
    nz_range = f3.slider(
        "Rango de N/Z", float(nz.min()), float(nz.max()), (float(nz.min()), float(nz.max())), step=0.01
    )
    text = st.text_input("Buscar por nombre (p. ej. 'U', '238U', 'Fe')", "")

    view = gs[
        gs["dominant_mode"].isin(modes)
        & gs["Z"].between(*z_range)
        & (gs["N_over_Z"].between(*nz_range) | gs["N_over_Z"].isna())
    ]
    if text:
        view = view[view["name"].str.contains(text, case=False, na=False)]

    cols = ["name", "symbol", "Z", "N", "A", "N_over_Z", "dominant_mode", "half_life",
            "half_life_s", "spin_parity", "abundance", "mass_excess_keV", "decay_modes_raw"]
    st.caption(f"{len(view):,} estados base")
    st.dataframe(view[cols], hide_index=True, width="stretch", height=480)
    st.download_button(
        "Descargar CSV",
        view[cols].to_csv(index=False).encode("utf-8"),
        file_name="nudat_ground_states_filtrado.csv",
        mime="text/csv",
    )
