import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from datetime import datetime

# ========== PAGE CONFIG ==========
st.set_page_config(page_title="📈 Crypto Portfolio Tracker", layout="wide")
st.title("📈 Crypto Portfolio & Strategie Dashboard")

# ========== SESSION STATE INITIALIZATION ==========
if "holdings" not in st.session_state:
    st.session_state.holdings = pd.DataFrame(columns=["Coin", "Aantal", "Inleg_EUR"])
if "strategie" not in st.session_state:
    st.session_state.strategie = pd.DataFrame(columns=["Coin", "3x", "5x", "10x"])
if "reentry" not in st.session_state:
    st.session_state.reentry = pd.DataFrame(columns=["Coin", "Re-entry Prijs"])
if "narratieven" not in st.session_state:
    st.session_state.narratieven = pd.DataFrame(columns=["Coin", "Narratief"])
if "events" not in st.session_state:
    st.session_state.events = pd.DataFrame(columns=["Datum", "Titel", "Coin"])
if "watchlist" not in st.session_state:
    st.session_state.watchlist = pd.DataFrame(columns=["Coin", "Waarom"])
if "scenario" not in st.session_state:
    st.session_state.scenario = pd.DataFrame(columns=["Coin", "Groei %", "Dalings %"])
if "reflectie" not in st.session_state:
    st.session_state.reflectie = ""

# ========== HELPER: GET COIN PRICES ==========
@st.cache_data(ttl=60)
def get_prices(coins):
    ids = {
        "WIF": "dogwifcoin",
        "ZK": "zksync",
        "RNDR": "render-token",
        "SUI": "sui",
        "LINK": "chainlink",
        "STRK": "starknet",
        "FET": "fetch-ai",
        "INJ": "injective-protocol",
        "JUP": "jupiter-exchange"
    }
    prices = {}
    for coin in coins:
        if coin in ids:
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids[coin]}&vs_currencies=eur"
            r = requests.get(url)
            try:
                prices[coin] = r.json()[ids[coin]]['eur']
            except (KeyError, TypeError):
                prices[coin] = None
    return prices

# ========== TABS ==========
tabs = st.tabs([
    "📊 Portfolio",
    "✍️ Handmatige Invoer",
    "📤 Winststrategie",
    "🔁 Re-entry Plan",
    "🧠 Narratieven",
    "📅 Event Kalender",
    "📦 Watchlist",
    "🧮 Scenario Analyse",
    "🧠 Reflectie"
])

# ========== TAB 1: Portfolio ==========
with tabs[0]:
    st.header("📊 Portfolio Live Waarde")

    if st.session_state.holdings.empty:
        st.warning("⚠️ Voeg eerst je holdings toe in het tabblad '✍️ Handmatige Invoer'")
    else:
        df = st.session_state.holdings.copy()
        coins = df["Coin"].tolist()
        prices = get_prices(coins)
        df["Huidige_Prijs_EUR"] = df["Coin"].map(prices)
        df = df.dropna(subset=["Huidige_Prijs_EUR"])
        df["Totale_Waarde"] = df["Aantal"] * df["Huidige_Prijs_EUR"]
        df["Winst/Verlies"] = df["Totale_Waarde"] - df["Inleg_EUR"]

        total_value = df["Totale_Waarde"].sum()
        total_invested = df["Inleg_EUR"].sum()
        total_profit = total_value - total_invested

        st.metric("Totale Inleg (EUR)", f"€{total_invested:,.2f}")
        st.metric("Totale Waarde (EUR)", f"€{total_value:,.2f}")
        st.metric("Totale Winst/Verlies", f"€{total_profit:,.2f}")

        st.dataframe(df, use_container_width=True)

        fig = px.pie(df, names="Coin", values="Totale_Waarde", title="Portfolio Allocatie")
        st.plotly_chart(fig, use_container_width=True)

# ========== TAB 2: Handmatige Invoer ==========
with tabs[1]:
    st.header("✍️ Handmatige Invoer van Holdings")
    edited_df = st.data_editor(
        st.session_state.holdings,
        num_rows="dynamic",
        use_container_width=True,
        key="editor"
    )
    if st.button("✅ Opslaan"):
        st.session_state.holdings = edited_df
        st.success("Holdings opgeslagen!")
    st.download_button("📥 Download holdings als CSV", data=edited_df.to_csv(index=False), file_name="holdings.csv", mime="text/csv")

# ========== TAB 3: Winststrategie ==========
with tabs[2]:
    st.header("📤 Winststrategie per Coin")
    strategie_edit = st.data_editor(
    st.session_state.strategie,
    num_rows="dynamic",
    use_container_width=True,
    key="strategie_editor"
)

if st.button("✅ Strategie opslaan"):
    st.session_state.strategie = strategie_edit
    st.success("Strategie opgeslagen!")

    if st.button("💾 Opslaan Strategie"):
        st.session_state.strategie = winst_df
        st.success("Strategie opgeslagen!")

# ========== TAB 4: Re-entry ==========
with tabs[3]:
    st.header("🔁 Re-entry Zones")
    reentry_df = st.data_editor(
        st.session_state.reentry,
        num_rows="dynamic",
        use_container_width=True,
        key="reentry"
    )
    if st.button("💾 Opslaan Re-entry"):
        st.session_state.reentry = reentry_df
        st.success("Re-entry plan opgeslagen!")

# ========== TAB 5: Narratieven ==========
with tabs[4]:
    st.header("🧠 Coin Narratieven")
    narratief_df = st.data_editor(
        st.session_state.narratieven,
        num_rows="dynamic",
        use_container_width=True,
        key="narratief"
    )
    if st.button("💾 Opslaan Narratieven"):
        st.session_state.narratieven = narratief_df
        st.success("Narratieven opgeslagen!")

# ========== TAB 6: Event Kalender ==========
with tabs[5]:
    st.header("📅 Belangrijke Events")
    events_df = st.data_editor(
        st.session_state.events,
        num_rows="dynamic",
        use_container_width=True,
        key="events"
    )
    if st.button("💾 Opslaan Events"):
        st.session_state.events = events_df
        st.success("Event kalender opgeslagen!")

# ========== TAB 7: Watchlist ==========
with tabs[6]:
    st.header("📦 Watchlist Coins")
    watchlist_df = st.data_editor(
        st.session_state.watchlist,
        num_rows="dynamic",
        use_container_width=True,
        key="watchlist"
    )
    if st.button("💾 Opslaan Watchlist"):
        st.session_state.watchlist = watchlist_df
        st.success("Watchlist opgeslagen!")

# ========== TAB 8: Scenario Analyse ==========
with tabs[7]:
    st.header("🧮 Scenario Analyse")
    scenario_df = st.data_editor(
        st.session_state.scenario,
        num_rows="dynamic",
        use_container_width=True,
        key="scenario"
    )
    if st.button("💾 Opslaan Scenario's"):
        st.session_state.scenario = scenario_df
        st.success("Scenario's opgeslagen!")

# ========== TAB 9: Reflectie ==========
with tabs[8]:
    st.header("🧠 Reflectie op je Strategie")
    reflectie = st.text_area("Wat heb je geleerd? Wat wil je anders doen?", value=st.session_state.reflectie, height=200)
    if st.button("💾 Opslaan Reflectie"):
        st.session_state.reflectie = reflectie
        st.success("Reflectie opgeslagen!")
