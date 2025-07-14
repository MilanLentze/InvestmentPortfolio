import streamlit as st
import requests
import time
from streamlit_autorefresh import st_autorefresh

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

# ===== USER FILTERS & CONTROLS =====
sort_option = st.selectbox("🔃 Sorteer op", ["Verandering 24u", "Verandering 7d", "Verandering 30d", "Coin", "Prijs", "Verandering 24u"])
filter_enabled = st.checkbox("🔎 Toon alleen coins met > 5% stijging", value=True)

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
            "narrative": info["narrative"]
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

# ===== TABEL RENDEREN =====
st.markdown("---")
st.markdown("""
    <div style='padding: 10px 12px; border-bottom: 2px solid #666; display: grid;
    grid-template-columns: 80px 120px 120px 100px 100px auto; font-weight: bold;'>
        <span>Coin</span>
        <span>Prijs</span>
        <span>24u</span>
        <span>7d</span>
        <span>30d</span>
        <span>Narratief</span>
    </div>
""", unsafe_allow_html=True)

for coin in coin_data:
    st.markdown(f"""
        <div style='padding: 10px 12px; border-bottom: 1px solid #333;
        display: grid; grid-template-columns: 80px 120px 120px 100px 100px auto; align-items: center;'>
            <span style='color: white;'>{coin['symbol']}</span>
            <span style='color: #10A37F; font-family: monospace;'>€ {coin['price']:.4f}</span>
            <span>{format_change(coin['change_24h'])}</span>
            <span>{format_change(coin['change_7d'])}</span>
            <span>{format_change(coin['change_30d'])}</span>
            <span style='color: #AAAAAA;'>{coin['narrative']}</span>
        </div>
    """, unsafe_allow_html=True)

st.markdown("---")
st.caption("Dashboard ontwikkeld door Milan • Powered by Streamlit + CoinGecko")
