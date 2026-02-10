import pandas as pd
import streamlit as st
import plotly.express as px

DATA_PATH = "data/processed/sweden_se_prices.csv"

AREA_INFO = {
    "SE1": {
        "label": "SE1 – Norra Norrland",
        "cities": "Luleå, Kiruna, Gällivare, Boden",
        "color": "#1f77b4",
    },
    "SE2": {
        "label": "SE2 – Norra Sverige",
        "cities": "Umeå, Sundsvall, Östersund, Skellefteå",
        "color": "#2ca02c",
    },
    "SE3": {
        "label": "SE3 – Mellansverige",
        "cities": "Stockholm, Uppsala, Västerås, Örebro, Linköping",
        "color": "#ff7f0e",
    },
    "SE4": {
        "label": "SE4 – Södra Sverige",
        "cities": "Malmö, Lund, Helsingborg, Växjö, Karlskrona",
        "color": "#d62728",
    },
}

COLOR_MAP = {v["label"]: v["color"] for v in AREA_INFO.values()}

st.set_page_config(page_title="Elpriser Sverige", layout="wide")

# Lite enkel styling
st.markdown(
    """
    <style>
      .block-container { padding-top: 1.0rem; padding-bottom: 2rem; }
      .small-note { color: #666; font-size: 0.92rem; margin-top: -8px; }
    </style>
    """,
    unsafe_allow_html=True,
)

@st.cache_data
def load_data():
    df = pd.read_csv(DATA_PATH)
    df["time_start"] = pd.to_datetime(df["time_start"], errors="coerce")
    df["time_end"] = pd.to_datetime(df["time_end"], errors="coerce")
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df = df.dropna(subset=["time_start", "price", "area"])

    df["area_name"] = df["area"].map(lambda a: AREA_INFO.get(a, {"label": a})["label"])
    df["hour"] = df["time_start"].dt.hour
    return df

df = load_data()

# ---------- HEADER ----------
st.title("⚡ Svenska elpriser – interaktiv analys")
st.markdown(
    '<div class="small-note">Källa: elprisetjustnu · Enhet: SEK/kWh · Upplösning: 15 min</div>',
    unsafe_allow_html=True,
)

# ---------- AREA EXPLAINER ----------
st.markdown("## 🇸🇪 Sveriges elområden (ungefärlig täckning)")
cols = st.columns(4)
order = ["SE1", "SE2", "SE3", "SE4"]
for i, k in enumerate(order):
    a = AREA_INFO[k]
    with cols[i]:
        st.markdown(
            f"""
            <div style="
                padding:14px;
                border-radius:14px;
                background-color:{a['color']}22;
                border-left:6px solid {a['color']};
                min-height: 105px;
            ">
            <b>{a['label']}</b><br>
            <span style="color:#444;font-size:0.92rem;">Exempel på städer:</span><br>
            <span style="font-size:0.95rem;">{a['cities']}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.divider()

# ---------- FILTERS ----------
st.sidebar.header("Filter")

areas = sorted(df["area"].unique().tolist())
selected_areas = st.sidebar.multiselect(
    "Elområde",
    options=areas,
    default=areas,
    format_func=lambda a: AREA_INFO.get(a, {"label": a})["label"],
)

min_ts = df["time_start"].min()
max_ts = df["time_start"].max()
start_date, end_date = st.sidebar.date_input(
    "Datumintervall",
    value=(min_ts.date(), max_ts.date()),
    min_value=min_ts.date(),
    max_value=max_ts.date(),
)

start_hour, end_hour = st.sidebar.slider(
    "Tid på dygnet (0–23)",
    min_value=0,
    max_value=23,
    value=(0, 23),
    help="Filtrera på klockslag för att se när elen är dyrast (t.ex. 17–21).",
)

top_n = st.sidebar.slider("Topplista: antal dyraste tidpunkter", 5, 50, 10)

mask = (
    df["area"].isin(selected_areas)
    & (df["time_start"].dt.date >= start_date)
    & (df["time_start"].dt.date <= end_date)
    & (df["time_start"].dt.hour >= start_hour)
    & (df["time_start"].dt.hour <= end_hour)
)
f = df.loc[mask].copy()

# ---------- KPI ----------
if len(f) > 0:
    max_row = f.loc[f["price"].idxmax()]
    min_row = f.loc[f["price"].idxmin()]
else:
    max_row = None
    min_row = None

c1, c2, c3, c4 = st.columns(4)
c1.metric("Datapunkter", f"{len(f):,}".replace(",", " "))
c2.metric("Maxpris (SEK/kWh)", f"{f['price'].max():.3f}" if len(f) else "-")
c3.metric("Minpris (SEK/kWh)", f"{f['price'].min():.3f}" if len(f) else "-")
c4.metric("Dyrast vid", max_row["time_start"].strftime("%Y-%m-%d %H:%M") if max_row is not None else "-")

st.divider()

# =========================================================
# 1) PRIS ÖVER TID
# =========================================================
st.subheader("📈 1) Pris över tid per elområde")

fig1 = px.line(
    f.sort_values("time_start"),
    x="time_start",
    y="price",
    color="area_name",
    color_discrete_map=COLOR_MAP,
    labels={"time_start": "Tid", "price": "Pris (SEK/kWh)", "area_name": "Elområde"},
)
fig1.update_layout(hovermode="x unified", title="Prisvariation per elområde")
st.plotly_chart(fig1, use_container_width=True)

# =========================================================
# 2) GENOMSNITT PER ELOMRÅDE
# =========================================================
st.subheader("🏆 2) Genomsnittspris per elområde")

avg_df = (
    f.groupby(["area", "area_name"], as_index=False)["price"]
    .mean()
    .sort_values("price", ascending=False)
)

fig2 = px.bar(
    avg_df,
    x="area_name",
    y="price",
    color="area_name",
    color_discrete_map=COLOR_MAP,
    text_auto=".3f",
    labels={"area_name": "Elområde", "price": "Genomsnitt (SEK/kWh)"},
)
fig2.update_layout(showlegend=False)
st.plotly_chart(fig2, use_container_width=True)

# =========================================================
# 3) TOPP DYRAST (GRAF + TABELL)
# =========================================================
st.subheader(f"🔥 3) Topp {top_n} dyraste tidpunkter")

top = f.sort_values("price", ascending=False).head(top_n).copy()

fig3 = px.bar(
    top,
    x="price",
    y="time_start",
    color="area_name",
    color_discrete_map=COLOR_MAP,
    orientation="h",
    labels={"price": "Pris (SEK/kWh)", "time_start": "Tidpunkt", "area_name": "Elområde"},
)
fig3.update_layout(yaxis=dict(autorange="reversed"), title=f"Topp {top_n} dyraste tidpunkter")
st.plotly_chart(fig3, use_container_width=True)

st.dataframe(
    top[["area_name", "time_start", "time_end", "price"]]
    .rename(columns={"area_name": "Elområde", "time_start": "Start", "time_end": "Slut", "price": "Pris (SEK/kWh)"}),
    use_container_width=True,
    hide_index=True,
)

# =========================================================
# 4) DYGNSSMÖNSTER
# =========================================================
st.subheader("⏰ 4) Dygnsmönster: vilken timme är elen dyrast?")

hour_df = (
    f.groupby("hour", as_index=False)["price"]
    .mean()
    .sort_values("hour")
)

fig4 = px.bar(
    hour_df,
    x="hour",
    y="price",
    text_auto=".3f",
    labels={"hour": "Timme på dygnet (0=00:00, 18=18:00)", "price": "Genomsnitt (SEK/kWh)"},
)
fig4.update_layout(xaxis_tickmode="linear", xaxis_dtick=1)
st.plotly_chart(fig4, use_container_width=True)
