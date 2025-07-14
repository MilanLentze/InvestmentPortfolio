import streamlit as st
import requests
import time
from streamlit_autorefresh import st_autorefresh

# ========== CONFIGURATIE ==========
st.set_page_config(page_title="📈 Live Altcoin Prices", layout="centered")
st.title("📊 Live Altcoin Prices")
st.caption("Gegevens via CoinGecko & Jupiter · Prijzen in euro · Automatisch ververst elke 30 seconden")

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
    </style>
""", unsafe_allow_html=True)

# ===== AUTOVERVERSING (elke 30 sec) =====
st_autorefresh(interval=30_000, key="refresh")

# ===== COINGECKO IDs =====
COINS = {
    "WIF": "dogwifcoin",
    "ZK": "zksync",
    "RNDR": "render-token",
    "SUI": "sui",
    "LINK": "chainlink",
    "STRK": "starknet",
    "FET": "fetch-ai",
    "INJ": "injective-protocol",
    "JUP": "jupiter"  # Uitzondering: halen we op via Jupiter Aggregator API
}

# ===== FUNCTIE: JUP ophalen via Jupiter Aggregator API =====
def get_jup_price_from_jupiter():
    url = "https://quote-api.jup.ag/v6/price?ids=JUP"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        jup_data = data.get("data", {}).get("JUP", {})
        price = jup_data.get("price")
        return price
    except Exception as e:
        st.warning(f"Jupiter API fout: {e}")
        return None

# ===== FUNCTIE: Andere coins ophalen via CoinGecko =====
@st.cache_data(ttl=25)
def get_live_prices():
    ids = ",".join([v for k, v in COINS.items() if k != "JUP"])
    url = (
        f"https://api.coingecko.com/api/v3/simple/price"
        f"?ids={ids}&vs_currencies=eur&include_24hr_change=true"
    )
    try:
        time.sleep(1)  # om CoinGecko-spikes te vermijden
        response = requests.get(url, timeout=10)
        if response.status_code == 429:
            raise Exception("📉 API-limiet bereikt (429 Too Many Requests)")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Kon prijzen niet ophalen: {e}")
        return {}

# ===== PRIJZEN TONEN MET VERANDERING =====
prices = get_live_prices()

st.markdown("---")
for symbol, coingecko_id in COINS.items():
    # Speciaal geval: JUP via Jupiter API
    if symbol == "JUP":
        price = get_jup_price_from_jupiter()
        change = None  # Geen 24h-change beschikbaar
    else:
        data = prices.get(coingecko_id, {})
        price = data.get("eur", None)
        change = data.get("eur_24h_change", None)

    if price is not None:
        change_str = ""
        if change is not None:
            change_icon = "🔼" if change >= 0 else "🔽"
            color = "#10A37F" if change >= 0 else "#FF4B4B"
            change_str = f"{change_icon} <span style='color: {color};'>{change:.2f}%</span>"

        st.markdown(
            f"""
            <div style='padding: 10px 12px; border-bottom: 1px solid #333; display: flex; justify-content: sp
