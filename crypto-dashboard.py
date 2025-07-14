import streamlit as st
import requests
import time
from streamlit_autorefresh import st_autorefresh
import plotly.graph_objects as go
from datetime import datetime


# ========== CONFIGURATIE ==========
st.set_page_config(page_title="📈 Live Altcoin Prices", layout="centered")
tab1, tab2 = st.tabs(["📊 Live Altcoin Prices", "🧠 Altseason Insights"])
st.title("📊 Live Altcoin Prices")
st.caption("Gegevens via CoinGecko · Prijzen in euro · Automatisch ververst elke 30 seconden")

st.markdown("""
    <style>
    body {
        background-color: #000000;
        color: #FFFFFF;
    }
    .stApp {
        background-color: #000000;
        color: #FFFFFF;
    }
    label, .stSelectbox label {
        color: #AAAAAA !important;
        font-weight: normal;
    }
    .css-16huue1 > label, .stCheckbox > div > label {
        color: #AAAAAA !important;
        font-weight: normal;
    }
    </style>
""", unsafe_allow_html=True)

with tab2:
    st.title("🧠 Altseason Insights")

    # 1. Macro Indicatoren
    st.subheader("📈 Macro Indicatoren")
    macro = st.selectbox("Kies macro-indicator", ["BTC Dominance", "ETH/BTC Ratio", "Fear & Greed Index"])
    st.info(f"Inzicht: {macro}")

    # 2. Kapitaalrotatie
    st.subheader("🔄 Kapitaalrotatie")
    rotation = st.selectbox("Kies segment", ["Blue Chips", "Narratief Coins", "Meme Coins"])
    st.info(f"Segment gekozen: {rotation}")

    # 3. Narratief Activiteit
    st.subheader("🔥 Narratief Activiteit")
    narrative = st.selectbox("Selecteer narratief", ["AI", "ZK / L2", "L1", "Meme", "DeFi", "Oracles"])
    st.info(f"Selectie: {narrative}")

    # 4. Momentum & Signalering
    st.subheader("⚡ Momentum & Signalering")
    momentum = st.selectbox("Kies signaal", ["Coins >30% (7d)", "Nieuwe ATHs", "Top 3 stijgers per week"])
    st.info(f"Momentum inzicht: {momentum}")

    # 5. Cycle Timing
    st.subheader("⏱️ Cycle Timing & Index")
    timing = st.selectbox("Kies timing-indicator", ["Halving Countdown", "Dagen sinds BTC-top", "Altseason Index"])
    st.info(f"Timing gekozen: {timing}")

    # 6. Analyse & Strategie (educatief)
    st.subheader("🧠 Analyse & Strategie")
    st.markdown("""
        > *Voorbeeldanalyse: We zitten momenteel in Fase 2. Mid caps tonen momentum. BTC dominance daalt licht. ETH trekt aan. Meme-coins reageren nog niet voluit.*
    """)
    st.download_button("📥 Download strategie (PDF)", data="PDF-content", file_name="strategie_altseason.pdf")

# ===== AUTOVERVERSING (elke 30 sec) =====
st_autorefresh(interval=30_000, key="refresh")

# ===== COINGECKO IDs & Narratieven =====
COINS = {
    "WIF": {"id": "dogwifcoin", "narrative": "Meme"},
    "ZK": {"id": "zksync", "narrative": "ZK / L2"},
    "RNDR": {"id": "render-token", "narrative": "AI / GPU"},
    "SUI": {"id": "sui", "narrative": "L1"},
    "LINK": {"id": "chainlink", "narrative": "Oracles"},
    "STRK": {"id": "starknet", "narrative": "ZK / L2"},
    "FET": {"id": "fetch-ai", "narrative": "AI"},
    "INJ": {"id": "injective-protocol", "narrative": "DeFi"},
    "JUP": {"id": "jupiter", "narrative": "Solana DEX"}
}

# ===== FORMAT FUNCTIE VOOR PERCENTAGES =====
def format_change(value):
    if value is None:
        return "<span style='color: #666;'>–</span>"
    icon = "🔼" if value >= 0 else "🔽"
    color = "#10A37F" if value >= 0 else "#FF4B4B"
    return f"{icon} <span style='color: {color};'>{value:.2f}%</span>"

# ===== PRIJZEN OPHALEN FUNCTIE =====
@st.cache_data(ttl=25)
def get_live_prices():
    ids = ",".join([info["id"] for info in COINS.values()])
    url = (
        f"https://api.coingecko.com/api/v3/coins/markets"
        f"?vs_currency=eur&ids={ids}"
        f"&price_change_percentage=24h,7d,30d"
    )
    try:
        time.sleep(1)
        response = requests.get(url, timeout=10)
        if response.status_code == 429:
            raise Exception("📉 API-limiet bereikt (429 Too Many Requests)")
        response.raise_for_status()
        return response.json()  # Lijst van coin dicts
    except Exception as e:
        st.error(f"Kon prijzen niet ophalen: {e}")
        return []

# ===== HISTORISCHE GRAFIEKDATA OPHALEN =====
@st.cache_data(ttl=1800)
def get_chart_data(coin_id):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=eur&days=7"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        prices = response.json().get("prices", [])
        # Timestamps naar datumstrings + prijs
        dates = [datetime.fromtimestamp(p[0]/1000).strftime('%d %b') for p in prices]
        values = [p[1] for p in prices]
        return dates, values
    except:
        return [], []

# ===== USER FILTERS & CONTROLS =====
sort_option = st.selectbox("🔃 Sorteer op", ["Verandering 24u", "Verandering 7d", "Verandering 30d", "Coin", "Prijs", "Altseason Piek Fase"])

#====== ALTCOIN FASES =========

ALTCOIN_PHASES = {
    "WIF": "Fase 4 – FOMO & Memecoins",
    "ZK": "Fase 2 – Mid Caps & Narratieven",
    "RNDR": "Fase 2-3 – Mid Caps & Narratieven",
    "SUI": "Fase 2 – Mid Caps & Narratieven",
    "LINK": "Fase 1 – Blue Chips & Infra",
    "STRK": "Fase 1-2 – Blue Chips & Mid C",
    "FET": "Fase 2 – Mid Caps & Narratieven",
    "INJ": "Fase 2 – Mid Caps & Narratieven",
    "JUP": "Fase 3 – Hypefase / Narratiefpiek"
}

#======= Rendement X =======
def calculate_expected_x_score_model(current_price, ath_price, current_marketcap, narrative, price_change_30d):
    # 1. ATH Score (max 10)
    ath_ratio = ath_price / current_price if current_price > 0 else 0
    ath_score = min(ath_ratio, 10)

    # 2. Narrative Score (max 5)
    narrative_scores = {
        "Meme": 5,
        "AI": 4.5,
        "AI / GPU": 4.5,
        "ZK / L2": 4,
        "L1": 3.5,
        "DeFi": 3.5,
        "Solana DEX": 3.5,
        "Oracles": 3
    }
    narrative_score = narrative_scores.get(narrative, 3)

    # 3. Marketcap Score (max 5)
    narrative_max_caps = {
        "Meme": 8_000_000_000,
        "AI": 20_000_000_000,
        "AI / GPU": 20_000_000_000,
        "ZK / L2": 12_000_000_000,
        "L1": 15_000_000_000,
        "Oracles": 10_000_000_000,
        "DeFi": 10_000_000_000,
        "Solana DEX": 8_000_000_000
    }
    potential_cap = narrative_max_caps.get(narrative, 10_000_000_000)
    marketcap_ratio = potential_cap / current_marketcap if current_marketcap > 0 else 0
    marketcap_score = min(marketcap_ratio, 5)

    # 4. Momentum Score (max 5)
    if price_change_30d > 50:
        momentum_score = 1
    elif price_change_30d > 20:
        momentum_score = 2
    elif price_change_30d > 0:
        momentum_score = 3
    elif price_change_30d > -10:
        momentum_score = 4
    else:
        momentum_score = 5

    # Gewogen optelling
    expected_x = (
        0.4 * ath_score +
        0.3 * narrative_score +
        0.2 * marketcap_score +
        0.1 * momentum_score
    )

    # Maximaal 15x, afgerond op 1 decimaal
    return round(min(expected_x, 15), 1)

# ===== PRIJZEN TONEN MET VERANDERING =====
prices = get_live_prices()

coin_data = []
for symbol, info in COINS.items():
    match = next((coin for coin in prices if coin["id"] == info["id"]), None)
    if not match:
        continue

    price = match.get("current_price")
    ath = match.get("ath")
    market_cap = match.get("market_cap")
    change_24h = match.get("price_change_percentage_24h_in_currency")
    change_7d = match.get("price_change_percentage_7d_in_currency")
    change_30d = match.get("price_change_percentage_30d_in_currency")

    expected_x = calculate_expected_x_score_model(
        current_price=price,
        ath_price=ath,
        current_marketcap=market_cap,
        narrative=info["narrative"],
        price_change_30d=change_30d
    )

    if price is not None and change_24h is not None:
        coin_data.append({
            "symbol": symbol,
            "price": price,
            "change_24h": change_24h,
            "change_7d": change_7d,
            "change_30d": change_30d,
            "narrative": info["narrative"],
            "altseason_phase": ALTCOIN_PHASES.get(symbol, "Onbekend"),
            "expected_x": expected_x
        })


# Sorteren
if sort_option == "Coin":
    coin_data = sorted(coin_data, key=lambda x: x["symbol"])
elif sort_option == "Prijs":
    coin_data = sorted(coin_data, key=lambda x: x["price"], reverse=True)
elif sort_option == "Verandering 24u":
    coin_data = sorted(coin_data, key=lambda x: x["change_24h"], reverse=True)
elif sort_option == "Verandering 7d":
    coin_data = sorted(coin_data, key=lambda x: x["change_7d"], reverse=True)
elif sort_option == "Verandering 30d":
    coin_data = sorted(coin_data, key=lambda x: x["change_30d"], reverse=True)
elif sort_option == "Altseason Piek Fase":
    coin_data = sorted(coin_data, key=lambda x: x["altseason_phase"], reverse=False)
    
    
# ===== RENDER DE TABEL =====
st.markdown("---")

# ===== TABEL WEERGAVE MET STREAMLIT KOLLOMEN =====
st.markdown("---")
st.markdown("""<h4 style='color:#fff;'>📊 Coin Tabel</h4>""", unsafe_allow_html=True)
header = st.columns([1, 2, 2, 2, 2, 2, 2, 2])
header[0].markdown("**Coin**")
header[1].markdown("**Prijs**")
header[2].markdown("**24u**")
header[3].markdown("**7d**")
header[4].markdown("**30d**")
header[5].markdown("**Narratief**")
header[6].markdown("**Altseason Piek Fase**")
header[7].markdown("**Verwacht X**")

for coin in coin_data:
    row = st.columns([1, 2, 2, 2, 2, 2, 2, 2])
    row[0].markdown(f"**{coin['symbol']}**")
    row[1].markdown(f"€ {coin['price']:.4f}")
    row[2].markdown(format_change(coin['change_24h']), unsafe_allow_html=True)
    row[3].markdown(format_change(coin['change_7d']), unsafe_allow_html=True)
    row[4].markdown(format_change(coin['change_30d']), unsafe_allow_html=True)
    row[5].markdown(coin['narrative'])
    row[6].markdown(coin['altseason_phase'])
    row[7].markdown(f"{coin['expected_x']}x")

st.markdown("---")
st.caption("Dashboard ontwikkeld door Milan • Powered by Streamlit + CoinGecko")
