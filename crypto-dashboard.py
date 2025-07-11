import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import yfinance as yf
import numpy as np


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

# ====Calculate RSI=====
def calculate_rsi(ticker, period=14):
    try:
        data = yf.download(tickers=ticker, period="1mo", interval="1d", progress=False)
        close = data["Close"]
        delta = close.diff().dropna()
        gain = delta.where(delta > 0, 0.0)
        loss = -delta.where(delta < 0, 0.0)
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
        rs = avg_gain / avg_loss
        rsi = 100.0 - (100.0 / (1.0 + rs))
        return round(rsi.dropna().iloc[-1], 2)
    except Exception as e:
        return None


# ========== HELPER: GET COIN PRICES ==========
@st.cache_data(ttl=3600)
def get_ath_prices(coins):
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
    aths = {}
    for coin in coins:
        if coin in ids:
            url = f"https://api.coingecko.com/api/v3/coins/{ids[coin]}"
            r = requests.get(url)
            aths[coin] = r.json()["market_data"]["ath"]["eur"]
    return aths

@st.cache_data(ttl=3600)
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
            prices[coin] = r.json()[ids[coin]]["eur"]
    return prices

# ===RSI Tickers===
yf_tickers = {
    "WIF": "WIF-USD",
    "ZK": "ZK-USD",
    "RNDR": "RNDR-USD",
    "SUI": "SUI1-USD",
    "LINK": "LINK-USD",
    "STRK": "STRK-USD",
    "FET": "FET-USD",
    "INJ": "INJ-USD",
    "JUP": "JUP-USD"
}


# ========== TABS ==========
tabs = st.tabs([
    "📊 Portfolio",
    "✍️ Handmatige Invoer",
    "📤 Winststrategie",
    "🔁 Re-entry Plan",
    "🧮 Narratieven",
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

# ========== Tabs ==========
with tabs[2]:
    st.header("📤 Winststrategie")

    # Vooringevulde strategieën per coin
    strategie = {
        "WIF": [(2, 30), (3.5, 40), (5, 20), ("moonbag", 10)],
        "ZK": [(3, 20), (5, 30), (8, 30), ("moonbag", 20)],
        "RNDR": [(3, 20), (5, 30), (7, 30), ("moonbag", 20)],
        "SUI": [(2.5, 25), (4, 30), (6, 25), ("moonbag", 20)],
        "LINK": [(2, 25), (4, 35), (6, 20), ("moonbag", 20)],
        "STRK": [(2.5, 25), (4.5, 30), (7, 25), ("moonbag", 20)],
        "FET": [(3, 20), (5, 30), (8, 30), ("moonbag", 20)],
        "INJ": [(2.5, 25), (4, 30), (6.5, 25), ("moonbag", 20)],
        "JUP": [(2, 30), (3.5, 30), (5, 30), ("moonbag", 10)],
    }

    holdings = st.session_state.holdings.copy()
    if holdings.empty:
        st.warning("⚠️ Voeg eerst je holdings toe in '✍️ Handmatige Invoer'")
    else:
        st.subheader("📊 Winststrategie per Coin")

        for _, row in holdings.iterrows():
            coin = row["Coin"]
            aantal = row["Aantal"]
            if coin in strategie:
                st.markdown(f"#### 💰 {coin}")
                plan = strategie[coin]
                verkoopplan = []
                for stap in plan:
                    multiplier, percentage = stap
                    if multiplier == "moonbag":
                        coins = aantal * percentage / 100
                        st.write(f"Hou {percentage}% over als **moonbag**: {coins:.2f} {coin}")
                    else:
                        coins = aantal * percentage / 100
                        st.write(f"Verkoop {percentage}% ({coins:.2f} {coin}) bij {multiplier}x winst")

with tabs[3]:
    st.header("🔁 Re-entry Plan (op basis van ATH + RSI)")

    if st.session_state.holdings.empty:
        st.warning("⚠️ Voeg eerst je holdings toe.")
    else:
        df = st.session_state.holdings.copy()
        coins = df["Coin"].tolist()
        prices = get_prices(coins)
        aths = get_ath_prices(coins)

        reentry_data = []

        for coin in coins:
            prijs = prices.get(coin)
            ath = aths.get(coin)
            if not prijs or not ath:
                continue

            drawdown = round((1 - prijs / ath) * 100, 2)
            yf_symbol = yf_tickers.get(coin)
            rsi = calculate_rsi(yf_symbol) if yf_symbol else None

            advies = "⏳ Nog wachten"
            if drawdown >= 60 and rsi is not None and rsi <= 40:
                advies = "✅ Re-entry zone (drawdown + RSI)"
            elif drawdown >= 60:
                advies = "⚠️ Drawdown ok, RSI hoog"
            elif rsi is not None and rsi <= 40:
                advies = "⚠️ RSI laag, maar drawdown beperkt"

            reentry_data.append({
                "Coin": coin,
                "Huidige Prijs (€)": prijs,
                "ATH (€)": ath,
                "% Onder ATH": f"{drawdown}%",
                "RSI (14d)": rsi if rsi is not None else "n.v.t.",
                "Advies": advies
            })

        reentry_df = pd.DataFrame(reentry_data)
        st.dataframe(reentry_df, use_container_width=True)
        
with tabs[4]:
    st.header("🧠 Narratieven per Coin")

    holdings = st.session_state.holdings.copy()
    coins = holdings["Coin"].tolist() if not holdings.empty else []

    if not coins:
        st.warning("⚠️ Voeg eerst je holdings toe.")
    else:
        st.markdown("### 🤖 Automatische Narratief Generator")

        selected_coin = st.selectbox("Kies een coin", coins)
        if st.button("🔍 Genereer Narratief", key="gen_narratief"):
            with st.spinner("Narratief wordt opgehaald..."):
                # Simuleer AI-respons (hier zou de echte OpenAI-call komen)
                narratieven = {
                    "WIF": "Dogwifhat (WIF) is een meme coin op Solana, bekend om zijn community en virale karakter. Potentie bij sterke meme-cycles.",
                    "ZK": "ZKSync is een Layer 2-oplossing gebaseerd op zero-knowledge proofs. Belangrijk binnen het schaalbaarheidsnarratief van Ethereum.",
                    "RNDR": "Render biedt GPU rendering via een gedecentraliseerd netwerk, essentieel voor AI en metaverse toepassingen.",
                    "SUI": "Sui is een high-performance Layer 1 blockchain gericht op snellere UX en schaalbaarheid, gebouwd door ex-Meta developers.",
                    "LINK": "Chainlink is de toonaangevende oracle provider voor smart contracts en cruciaal voor Web3-infra.",
                    "STRK": "Starknet is een ZK-rollup Layer 2 netwerk met sterke backing en unieke developer tooling.",
                    "FET": "Fetch.ai richt zich op AI-agenten die autonoom opereren in gedecentraliseerde omgevingen.",
                    "INJ": "Injective is een gedecentraliseerd trading-ecosysteem met sterke interoperabiliteit en focus op DeFi-innovatie.",
                    "JUP": "Jupiter is een DEX-aggregator op Solana en speelt een centrale rol in de Solana DeFi-infrastructuur."
                }
                narratief = narratieven.get(selected_coin, "Nog geen narratief beschikbaar voor deze coin.")
                st.success(f"**{selected_coin}**: {narratief}")

# ========== TAB 6: Reflectie ==========
with tabs[5]:
    st.header("🧠 Reflectie Notitieboek")

    if "reflectie_notes" not in st.session_state:
        st.session_state.reflectie_notes = []

    st.subheader("➕ Nieuwe notitie")
    with st.form("reflectie_form", clear_on_submit=True):
        new_note = st.text_area("Wat wil je reflecteren of onthouden?", height=150)
        submitted = st.form_submit_button("➕ Voeg toe")
        if submitted and new_note.strip():
            st.session_state.reflectie_notes.insert(0, {"text": new_note.strip(), "editing": False})
            st.success("Notitie toegevoegd ✅")

    if st.session_state.reflectie_notes:
        st.subheader("📚 Je notities")

        for i, note in enumerate(st.session_state.reflectie_notes):
            col1, col2, col3 = st.columns([6, 1, 1])

            if note.get("editing"):
                edited_text = col1.text_area(f"✏️ Bewerken (notitie {i+1})", value=note["text"], key=f"edit_{i}")
                if col2.button("💾", key=f"save_{i}"):
                    st.session_state.reflectie_notes[i]["text"] = edited_text.strip()
                    st.session_state.reflectie_notes[i]["editing"] = False
                    st.success("Notitie bijgewerkt ✅")
                if col3.button("❌", key=f"cancel_{i}"):
                    st.session_state.reflectie_notes[i]["editing"] = False
            else:
                col1.markdown(f"**{i+1}.** {note['text']}")
                if col2.button("✏️", key=f"editbtn_{i}"):
                    st.session_state.reflectie_notes[i]["editing"] = True
                if col3.button("🗑️", key=f"delbtn_{i}"):
                    st.session_state.reflectie_notes.pop(i)
                    st.success("Notitie verwijderd 🗑️")
                    st.experimental_rerun()  # Herlaad om indexproblemen te voorkomen
    else:
        st.info("Je hebt nog geen reflecties opgeslagen.")
