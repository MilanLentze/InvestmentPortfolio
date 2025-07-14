import streamlit as st
import requests
import time
from streamlit_autorefresh import st_autorefresh
import plotly.graph_objects as go
from datetime import datetime


# ========== CONFIGURATIE ==========
st.set_page_config(page_title="📈 Live Altcoin Prices", layout="centered")
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
filter_enabled = st.checkbox("🔎 Toon alleen coins met > 5% stijging", value=True)

#====== ALTCOIN FASES =========

ALTCOIN_PHASES = {
    "WIF": "Fase 4 – FOMO & Memecoins",
    "ZK": "Fase 2 – Mid Caps & Narratieven",
    "RNDR": "Fase 2-3 – Mid Caps & Narratieven",
    "SUI": "Fase 2 – Mid Caps & Narratieven",
    "LINK": "Fase 1 – Blue Chips & Infra",
    "STRK": "Fase 1-2 – Blue C & Infra/Mid Caps",
    "FET": "Fase 2 – Mid Caps & Narratieven",
    "INJ": "Fase 2 – Mid Caps & Narratieven",
    "JUP": "Fase 3 – Hypefase / Narratiefpiek"
}

# ===== PRIJZEN TONEN MET VERANDERING =====
prices = get_live_prices()

coin_data = []
for symbol, info in COINS.items():
    match = next((coin for coin in prices if coin["id"] == info["id"]), None)
    if not match:
        continue
    price = match.get("current_price")
    change_24h = match.get("price_change_percentage_24h_in_currency")
    change_7d = match.get("price_change_percentage_7d_in_currency")
    change_30d = match.get("price_change_percentage_30d_in_currency")

    if price is not None and change_24h is not None:
        coin_data.append({
            "symbol": symbol,
            "price": price,
            "change_24h": change_24h,
            "change_7d": change_7d,
            "change_30d": change_30d,
            "narrative": info["narrative"],
            "altseason_phase": ALTCOIN_PHASES.get(symbol, "Onbekend")
        })

# Filteren
if filter_enabled:
    coin_data = [c for c in coin_data if c["change_24h"] > 5]

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
header = st.columns([1, 2, 2, 2, 2, 2, 2])
header[0].markdown("**Coin**")
header[1].markdown("**Prijs**")
header[2].markdown("**24u**")
header[3].markdown("**7d**")
header[4].markdown("**30d**")
header[5].markdown("**Narratief**")
header[6].markdown("**Altseason Piek Fase**")

for coin in coin_data:
    row = st.columns([1, 2, 2, 2, 2, 2, 2])
    row[0].markdown(f"**{coin['symbol']}**")
    row[1].markdown(f"€ {coin['price']:.4f}")
    row[2].markdown(format_change(coin['change_24h']), unsafe_allow_html=True)
    row[3].markdown(format_change(coin['change_7d']), unsafe_allow_html=True)
    row[4].markdown(format_change(coin['change_30d']), unsafe_allow_html=True)
    row[5].markdown(coin['narrative'])
    row[6].markdown(coin['altseason_phase'])

st.markdown("---")
st.caption("Dashboard ontwikkeld door Milan • Powered by Streamlit + CoinGecko")
