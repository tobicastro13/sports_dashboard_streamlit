import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# ── PAGE CONFIG ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ScoutVision | Football Analytics",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── STYLES ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    [data-testid="stAppViewContainer"] { background-color: #0d1117; }
    [data-testid="stSidebar"] { background-color: #161b22; }
    h1, h2, h3, h4 { color: #e6edf3; }
    .metric-card {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 16px;
        text-align: center;
    }
    .metric-value { font-size: 2rem; font-weight: 700; color: #58a6ff; }
    .metric-label { font-size: 0.85rem; color: #8b949e; margin-top: 4px; }
    .badge-league {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
        background: #1f6feb;
        color: #e6edf3;
    }
    div[data-testid="metric-container"] {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 12px 16px;
    }
    div[data-testid="metric-container"] label { color: #8b949e !important; }
    div[data-testid="metric-container"] div[data-testid="stMetricValue"] { color: #58a6ff !important; }
</style>
""", unsafe_allow_html=True)

# ── WORLD CUP 2026 SQUADS (manual mapping, FBref nationality codes) ─────────────
WC2026_NATIONS = {
    "Argentina": "ar ARG", "France": "fr FRA", "England": "eng ENG",
    "Germany": "de GER", "Spain": "es ESP", "Portugal": "pt POR",
    "Brazil": "br BRA", "Netherlands": "nl NED", "Belgium": "be BEL",
    "Italy": "it ITA", "Croatia": "hr CRO", "Uruguay": "uy URU",
    "Mexico": "mx MEX", "USA": "us USA", "Canada": "ca CAN",
    "Norway": "no NOR", "Denmark": "dk DEN", "Switzerland": "ch SUI",
    "Austria": "at AUT", "Poland": "pl POL", "Türkiye": "tr TUR",
    "Morocco": "ma MAR", "Senegal": "sn SEN", "Japan": "jp JPN",
    "South Korea": "kr KOR", "Australia": "au AUS", "Ecuador": "ec ECU",
    "Colombia": "co COL", "Chile": "cl CHI", "Iran": "ir IRN",
    "Saudi Arabia": "sa KSA", "Ghana": "gh GHA", "Cameroon": "cm CMR",
    "Nigeria": "ng NGA", "Ivory Coast": "ci CIV", "Tunisia": "tn TUN",
    "Algeria": "dz ALG", "Egypt": "eg EGY", "Qatar": "qa QAT",
    "South Africa": "za RSA", "Serbia": "rs SRB", "Ukraine": "ua UKR",
    "Scotland": "sct SCO", "Czech Republic": "cz CZE", "Slovakia": "sk SVK",
    "Hungary": "hu HUN", "Greece": "gr GRE",
}

LEAGUE_FLAGS = {
    "eng Premier League": "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League",
    "es La Liga": "🇪🇸 La Liga",
    "de Bundesliga": "🇩🇪 Bundesliga",
    "it Serie A": "🇮🇹 Serie A",
    "fr Ligue 1": "🇫🇷 Ligue 1",
}

POS_MAP = {
    "GK": "Goalkeeper",
    "DF": "Defender", "DF,MF": "Defender", "MF,DF": "Defender",
    "MF": "Midfielder", "MF,FW": "Midfielder", "FW,MF": "Midfielder",
    "FW": "Attacker", "FW,DF": "Attacker",
}

# ── DATA LOAD ──────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_csv("players_data_light-2025_2026.csv")

    # Clean numeric columns
    numeric_cols = ["Gls", "Ast", "G+A", "MP", "Starts", "Min", "90s",
                    "TklW", "Int", "SoT", "Saves", "Save%", "CS"]
    for c in numeric_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

    # Position group
    df["pos_group"] = df["Pos"].map(POS_MAP).fillna("Other")

    # per-90 metrics
    df["G_per90"]   = np.where(df["90s"] > 0, df["Gls"] / df["90s"], 0)
    df["A_per90"]   = np.where(df["90s"] > 0, df["Ast"] / df["90s"], 0)
    df["GA_per90"]  = np.where(df["90s"] > 0, df["G+A"] / df["90s"], 0)
    df["TklW_per90"] = np.where(df["90s"] > 0, df["TklW"] / df["90s"], 0)
    df["Int_per90"]  = np.where(df["90s"] > 0, df["Int"] / df["90s"], 0)

    # Start %
    df["Start_pct"] = np.where(df["MP"] > 0, df["Starts"] / df["MP"] * 100, 0)

    # League clean name
    df["League"] = df["Comp"].map(LEAGUE_FLAGS).fillna(df["Comp"])

    # Age as int
    df["Age"] = pd.to_numeric(df["Age"], errors="coerce").fillna(0).astype(int)

    # WC2026 flag – match on Nation code prefix (2-letter)
    wc_codes = set()
    for v in WC2026_NATIONS.values():
        wc_codes.add(v.split()[0])  # e.g. "ar", "fr"

    df["Nation_code"] = df["Nation"].str.split().str[0].str.lower()
    df["WC2026"] = df["Nation_code"].isin(wc_codes)

    return df

df = load_data()

# ── SIDEBAR ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚽ ScoutVision")
    st.markdown("*Football Analytics · Big 5 · 2025-26*")
    st.markdown("---")

    page = st.radio(
        "Navegación",
        ["🏠 Overview", "🔍 Scout Board", "🏆 Ligas", "🌍 Mundial 2026"],
        label_visibility="collapsed",
    )
    st.markdown("---")

    # Global filters
    st.markdown("**Filtros Globales**")
    leagues_avail = sorted(df["Comp"].unique())
    selected_leagues = st.multiselect("Liga", leagues_avail, default=leagues_avail,
                                      format_func=lambda x: LEAGUE_FLAGS.get(x, x))

    pos_avail = ["Goalkeeper", "Defender", "Midfielder", "Attacker"]
    selected_pos = st.multiselect("Posición", pos_avail, default=pos_avail)

    age_range = st.slider("Edad", int(df["Age"].min()), int(df["Age"].max()),
                          (int(df["Age"].min()), int(df["Age"].max())))

    min_90s = st.slider("Mínimo 90s jugados", 0, int(df["90s"].max()), 5)

    st.markdown("---")
    st.markdown("**Tobias Castro**")
    st.markdown("Sports Analytics Portfolio")
    st.markdown("[LinkedIn](https://www.linkedin.com/)")

# ── FILTER ─────────────────────────────────────────────────────────────────────
mask = (
    df["Comp"].isin(selected_leagues) &
    df["pos_group"].isin(selected_pos) &
    df["Age"].between(age_range[0], age_range[1]) &
    (df["90s"] >= min_90s)
)
dff = df[mask].copy()

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 1 — OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════
if page == "🏠 Overview":
    st.title("ScoutVision — Big 5 Leagues · 2025-26")
    st.markdown("*Datos reales FBref · Tobias Castro | Sports Analytics*")
    st.markdown("---")

    # KPIs
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Jugadores", f"{len(dff):,}")
    col2.metric("Equipos", dff["Squad"].nunique())
    col3.metric("Goles totales", int(dff["Gls"].sum()))
    col4.metric("Asistencias", int(dff["Ast"].sum()))
    col5.metric("Minutos jugados", f"{int(dff['Min'].sum()):,}")

    st.markdown("---")
    col_l, col_r = st.columns(2)

    with col_l:
        st.subheader("Top 15 Goleadores")
        top_scorers = (
            dff[dff["pos_group"] != "Goalkeeper"]
            .nlargest(15, "Gls")[["Player", "Squad", "League", "Gls", "Ast", "G+A", "90s"]]
            .reset_index(drop=True)
        )
        top_scorers.index += 1
        st.dataframe(top_scorers, use_container_width=True, height=400)

    with col_r:
        st.subheader("Distribución de Goles por Liga")
        goals_league = dff.groupby("Comp")["Gls"].sum().reset_index()
        goals_league["Liga"] = goals_league["Comp"].map(LEAGUE_FLAGS).fillna(goals_league["Comp"])
        fig = px.bar(
            goals_league.sort_values("Gls", ascending=True),
            x="Gls", y="Liga", orientation="h",
            color="Gls", color_continuous_scale="Blues",
            template="plotly_dark",
        )
        fig.update_layout(showlegend=False, coloraxis_showscale=False,
                          plot_bgcolor="#0d1117", paper_bgcolor="#0d1117")
        st.plotly_chart(fig, use_container_width=True)

    col_l2, col_r2 = st.columns(2)

    with col_l2:
        st.subheader("G+A per 90 por Posición")
        fig2 = px.box(
            dff[dff["90s"] >= 10],
            x="pos_group", y="GA_per90",
            color="pos_group",
            template="plotly_dark",
            labels={"pos_group": "Posición", "GA_per90": "G+A per 90"},
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        fig2.update_layout(showlegend=False, plot_bgcolor="#0d1117", paper_bgcolor="#0d1117")
        st.plotly_chart(fig2, use_container_width=True)

    with col_r2:
        st.subheader("Edad vs G+A per 90 (≥10 partidos)")
        scatter_df = dff[(dff["90s"] >= 10) & (dff["pos_group"] != "Goalkeeper")]
        fig3 = px.scatter(
            scatter_df, x="Age", y="GA_per90",
            color="pos_group", hover_name="Player",
            hover_data={"Squad": True, "League": True, "Gls": True, "Ast": True},
            template="plotly_dark",
            labels={"Age": "Edad", "GA_per90": "G+A per 90", "pos_group": "Posición"},
            color_discrete_sequence=px.colors.qualitative.Set2,
            opacity=0.7, size_max=8,
        )
        fig3.update_layout(plot_bgcolor="#0d1117", paper_bgcolor="#0d1117")
        st.plotly_chart(fig3, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 2 — SCOUT BOARD
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🔍 Scout Board":
    st.title("🔍 Scout Board")
    st.markdown("Identificá talentos ocultos con métricas avanzadas per-90")
    st.markdown("---")

    col_f1, col_f2 = st.columns(2)
    with col_f1:
        metric_x = st.selectbox("Eje X", ["G_per90", "A_per90", "GA_per90", "TklW_per90", "Int_per90", "Start_pct"],
                                 format_func=lambda x: x.replace("_per90","").replace("_"," ") + (" per 90" if "per90" in x else ""))
    with col_f2:
        metric_y = st.selectbox("Eje Y", ["GA_per90", "G_per90", "A_per90", "TklW_per90", "Int_per90", "Start_pct"],
                                 format_func=lambda x: x.replace("_per90","").replace("_"," ") + (" per 90" if "per90" in x else ""))

    scout_df = dff[dff["90s"] >= min_90s].copy()

    fig_scout = px.scatter(
        scout_df,
        x=metric_x, y=metric_y,
        color="pos_group",
        size="90s",
        hover_name="Player",
        hover_data={
            "Squad": True, "League": True, "Age": True,
            "Gls": True, "Ast": True, "90s": True,
            "Start_pct": ":.1f",
        },
        template="plotly_dark",
        color_discrete_sequence=px.colors.qualitative.Set2,
        opacity=0.75,
    )

    # Add quadrant lines at medians
    mx = scout_df[metric_x].median()
    my = scout_df[metric_y].median()
    fig_scout.add_hline(y=my, line_dash="dash", line_color="#30363d", opacity=0.6)
    fig_scout.add_vline(x=mx, line_dash="dash", line_color="#30363d", opacity=0.6)

    fig_scout.update_layout(
        height=550,
        plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
        legend_title="Posición",
    )
    st.plotly_chart(fig_scout, use_container_width=True)

    st.markdown("---")
    st.subheader("🏅 Rankings — Top performers per 90")

    tab1, tab2, tab3, tab4 = st.tabs(["⚽ Goleadores", "🎯 Asistidores", "🛡️ Defensores", "📊 Porteros"])

    with tab1:
        top_g = (scout_df[scout_df["pos_group"] != "Goalkeeper"]
                 .nlargest(20, "G_per90")[["Player","Squad","League","Age","Gls","Ast","90s","G_per90","Start_pct"]]
                 .reset_index(drop=True))
        top_g.index += 1
        top_g["G_per90"] = top_g["G_per90"].round(3)
        top_g["Start_pct"] = top_g["Start_pct"].round(1).astype(str) + "%"
        st.dataframe(top_g, use_container_width=True)

    with tab2:
        top_a = (scout_df[scout_df["pos_group"] != "Goalkeeper"]
                 .nlargest(20, "A_per90")[["Player","Squad","League","Age","Gls","Ast","90s","A_per90","Start_pct"]]
                 .reset_index(drop=True))
        top_a.index += 1
        top_a["A_per90"] = top_a["A_per90"].round(3)
        top_a["Start_pct"] = top_a["Start_pct"].round(1).astype(str) + "%"
        st.dataframe(top_a, use_container_width=True)

    with tab3:
        top_d = (scout_df[scout_df["pos_group"] == "Defender"]
                 .nlargest(20, "TklW_per90")[["Player","Squad","League","Age","TklW","Int","90s","TklW_per90","Int_per90","Start_pct"]]
                 .reset_index(drop=True))
        top_d.index += 1
        top_d["TklW_per90"] = top_d["TklW_per90"].round(3)
        top_d["Start_pct"] = top_d["Start_pct"].round(1).astype(str) + "%"
        st.dataframe(top_d, use_container_width=True)

    with tab4:
        gk_df = scout_df[scout_df["pos_group"] == "Goalkeeper"].copy()
        gk_df["Save%"] = pd.to_numeric(gk_df["Save%"], errors="coerce").fillna(0)
        top_gk = gk_df.nlargest(20, "Saves")[["Player","Squad","League","Age","Saves","Save%","CS","MP","Start_pct"]].reset_index(drop=True)
        top_gk.index += 1
        top_gk["Save%"] = top_gk["Save%"].round(1).astype(str) + "%"
        top_gk["Start_pct"] = top_gk["Start_pct"].round(1).astype(str) + "%"
        st.dataframe(top_gk, use_container_width=True)

    st.markdown("---")
    st.subheader("🔎 Búsqueda por Jugador")
    search = st.text_input("Escribí el nombre del jugador")
    if search:
        result = df[df["Player"].str.contains(search, case=False, na=False)]
        if len(result):
            st.dataframe(result.reset_index(drop=True), use_container_width=True)
        else:
            st.info("No se encontraron jugadores con ese nombre.")

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 3 — LIGAS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🏆 Ligas":
    st.title("🏆 Comparativa de Ligas")
    st.markdown("Big 5 European Leagues · 2025-26")
    st.markdown("---")

    lig = dff[dff["90s"] >= 5].copy()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Promedio G+A per 90 por Liga")
        avg_ga = (lig[lig["pos_group"] != "Goalkeeper"]
                  .groupby("Comp")["GA_per90"].mean()
                  .reset_index()
                  .sort_values("GA_per90", ascending=False))
        avg_ga["Liga"] = avg_ga["Comp"].map(LEAGUE_FLAGS).fillna(avg_ga["Comp"])
        fig = px.bar(avg_ga, x="Liga", y="GA_per90", color="Liga",
                     template="plotly_dark", text_auto=".3f",
                     color_discrete_sequence=px.colors.qualitative.Set2)
        fig.update_layout(showlegend=False, plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
                          xaxis_title=None)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Distribución de Edad por Liga")
        fig2 = px.violin(lig, x="Comp", y="Age", color="Comp",
                         template="plotly_dark", box=True,
                         labels={"Comp": "Liga", "Age": "Edad"},
                         color_discrete_sequence=px.colors.qualitative.Set2)
        fig2.update_xaxes(tickvals=list(LEAGUE_FLAGS.keys()),
                          ticktext=[v.split(" ", 1)[1] for v in LEAGUE_FLAGS.values()])
        fig2.update_layout(showlegend=False, plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
                           xaxis_title=None)
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Start % promedio por Liga (indicador de titularidad)")
    start_lig = lig.groupby("Comp")["Start_pct"].mean().reset_index().sort_values("Start_pct", ascending=False)
    start_lig["Liga"] = start_lig["Comp"].map(LEAGUE_FLAGS).fillna(start_lig["Comp"])
    fig3 = px.bar(start_lig, x="Liga", y="Start_pct", color="Liga",
                  template="plotly_dark", text_auto=".1f",
                  color_discrete_sequence=px.colors.qualitative.Set2)
    fig3.update_layout(showlegend=False, plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
                       yaxis_title="Start % promedio", xaxis_title=None)
    st.plotly_chart(fig3, use_container_width=True)

    st.subheader("Tabla de estadísticas por Liga")
    league_table = (
        lig.groupby("Comp").agg(
            Jugadores=("Player", "count"),
            Equipos=("Squad", "nunique"),
            Goles=("Gls", "sum"),
            Asistencias=("Ast", "sum"),
            Avg_G_per90=("G_per90", "mean"),
            Avg_A_per90=("A_per90", "mean"),
            Avg_Start_pct=("Start_pct", "mean"),
        ).round(3).reset_index()
    )
    league_table["Comp"] = league_table["Comp"].map(LEAGUE_FLAGS).fillna(league_table["Comp"])
    league_table.columns = ["Liga","Jugadores","Equipos","Goles","Asistencias","G/90 prom","A/90 prom","Start% prom"]
    st.dataframe(league_table, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 4 — MUNDIAL 2026
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🌍 Mundial 2026":
    st.title("🌍 FIFA World Cup 2026")
    st.markdown("Los jugadores de las Big 5 que estarán en el Mundial · USA/Canada/México")
    st.markdown("*48 selecciones · 104 partidos · 11 junio – 19 julio 2026*")
    st.markdown("---")

    wc_df = dff[dff["WC2026"] & (dff["90s"] >= 5)].copy()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Jugadores WC2026", len(wc_df))
    col2.metric("Selecciones representadas", wc_df["Nation_code"].nunique())
    col3.metric("Goles anotados (2025-26)", int(wc_df["Gls"].sum()))
    col4.metric("Asistencias", int(wc_df["Ast"].sum()))

    st.markdown("---")

    col_l, col_r = st.columns(2)

    with col_l:
        st.subheader("Top 20 Goleadores rumbo al Mundial")
        top_wc = (wc_df[wc_df["pos_group"] != "Goalkeeper"]
                  .nlargest(20, "Gls")[["Player","Nation","Squad","League","Age","Gls","Ast","G+A","90s","G_per90"]]
                  .reset_index(drop=True))
        top_wc.index += 1
        top_wc["G_per90"] = top_wc["G_per90"].round(3)
        st.dataframe(top_wc, use_container_width=True, height=480)

    with col_r:
        st.subheader("Goles por Selección (jugadores Big 5)")
        nation_goals = (wc_df.groupby("Nation")["Gls"].sum()
                        .reset_index().nlargest(20,"Gls"))
        fig = px.bar(nation_goals, x="Gls", y="Nation", orientation="h",
                     color="Gls", color_continuous_scale="Blues",
                     template="plotly_dark")
        fig.update_layout(showlegend=False, coloraxis_showscale=False,
                          plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
                          yaxis_title=None)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("🌟 Estrellas del Mundial 2026")
    st.markdown("*Jugadores clave con temporada 2025-26 destacada*")

    # Featured players
    stars = ["Erling Haaland", "Kylian Mbappé", "Harry Kane", "Martin Ødegaard",
             "Florian Wirtz", "Cole Palmer", "Lamine Yamal", "Vinicius Junior"]
    star_df = df[df["Player"].isin(stars)][["Player","Nation","Squad","League","Age","Gls","Ast","G+A","90s","G_per90","A_per90","Start_pct"]].copy()
    star_df["G_per90"] = star_df["G_per90"].round(3)
    star_df["A_per90"] = star_df["A_per90"].round(3)
    star_df["Start_pct"] = star_df["Start_pct"].round(1).astype(str) + "%"

    if len(star_df):
        st.dataframe(star_df.reset_index(drop=True), use_container_width=True)
    else:
        # fallback: top players from WC nations
        fallback = wc_df.nlargest(10, "Gls")[["Player","Nation","Squad","League","Age","Gls","Ast","G+A"]]
        st.dataframe(fallback.reset_index(drop=True), use_container_width=True)

    st.markdown("---")
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("G+A per 90 — Jugadores en Mundial (por Liga)")
        fig2 = px.box(wc_df[(wc_df["90s"] >= 10) & (wc_df["pos_group"] != "Goalkeeper")],
                      x="Comp", y="GA_per90",
                      color="Comp", template="plotly_dark",
                      labels={"Comp": "Liga", "GA_per90": "G+A per 90"},
                      color_discrete_sequence=px.colors.qualitative.Set2)
        fig2.update_xaxes(tickvals=list(LEAGUE_FLAGS.keys()),
                          ticktext=[v.split(" ",1)[1] for v in LEAGUE_FLAGS.values()])
        fig2.update_layout(showlegend=False, plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
                           xaxis_title=None)
        st.plotly_chart(fig2, use_container_width=True)

    with col_b:
        st.subheader("Distribución de Edad — Jugadores en Mundial")
        fig3 = px.histogram(wc_df, x="Age", nbins=15, color="pos_group",
                            template="plotly_dark",
                            labels={"Age": "Edad", "count": "Jugadores", "pos_group": "Posición"},
                            color_discrete_sequence=px.colors.qualitative.Set2,
                            barmode="stack")
        fig3.update_layout(plot_bgcolor="#0d1117", paper_bgcolor="#0d1117")
        st.plotly_chart(fig3, use_container_width=True)

    st.markdown("---")
    st.info("💡 **Nota metodológica:** WC 2026 qualification data basada en clasificados confirmados hasta la fecha de corte del dataset. Algunos jugadores pueden no estar disponibles por lesión.")
    st.caption("📊 Datos: FBref 2025-26 Big 5 Leagues | Tobias Castro — Sports Analytics Portfolio")
