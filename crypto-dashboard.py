import streamlit as st
import pandas as pd
import requests
import plotly.express as px

# ========== PAGE CONFIG ==========
st.set_page_config(page_title="📈 Crypto Portfolio Tracker", layout="wide")
st.title("📈 Crypto Portfolio & Strategie Dashboard")

# ========== SESSION STATE INITIALIZATION ==========
if "holdings" not in st.session_state:
    st.session_state.holdings = pd.DataFrame(columns=["Coin", "Aantal"])
if "cash" not in st.session_state:
    st.session_state.cash = 0.0
if "total_invested" not in st.session_state:
    st.session_state.total_invested = 0.0

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
            prices[coin] = r.json()[ids[coin]]['eur']
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
        df["Totale_Waarde"] = df["Aantal"] * df["Huidige_Prijs_EUR"]

        total_value = df["Totale_Waarde"].sum() + st.session_state.cash
        total_invested = st.session_state.total_invested
        total_profit = total_value - total_invested

        st.metric("Totale Inleg (EUR)", f"€{total_invested:,.2f}")
        st.metric("Totale Waarde (EUR)", f"€{total_value:,.2f}")
        st.metric("Totale Winst/Verlies", f"€{total_profit:,.2f}")
        st.metric("💶 Cash (EUR)", f"€{st.session_state.cash:,.2f}")

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

    st.markdown("---")
    st.subheader("💶 Contant Geld (EUR)")
    cash_input = st.number_input("Voer je cash in EUR in:", value=float(st.session_state.cash), step=10.0)

    st.subheader("💰 Totale Inleg (alle coins + cash)")
    invested_input = st.number_input("Voer je totale inlegbedrag in EUR in:", value=float(st.session_state.total_invested), step=10.0)

    if st.button("✅ Opslaan"):
        st.session_state.holdings = edited_df
        st.session_state.cash = cash_input
        st.session_state.total_invested = invested_input
        st.success("Holdings, cash en inleg opgeslagen!")

    st.download_button(
        label="📥 Download holdings als CSV",
        data=edited_df.to_csv(index=False),
        file_name="holdings.csv",
        mime="text/csv"
    )

# ========== Placeholder Tabs ==========
for i, name in enumerate([
    "Winststrategie",
    "Re-entry Plan",
    "Narratieven",
    "Event Kalender",
    "Watchlist",
    "Scenario Analyse",
    "Reflectie"
], start=2):
    with tabs[i]:
        st.header(f"🔧 {name}")
        uploaded = st.file_uploader(f"Upload {name} CSV", type="csv", key=name)
        if uploaded:
            df = pd.read_csv(uploaded)
            st.dataframe(df, use_container_width=True)
        else:
            st.info(f"Je kunt hier je {name.lower()} uploaden als CSV.")
