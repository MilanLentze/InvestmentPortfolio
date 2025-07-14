import streamlit as st
import requests
from streamlit_autorefresh import st_autorefresh

# ========== CONFIGURATIE ==========
st.set_page_config(page_title="📈 Live Altcoin Prices", layout="centered")
st.title("📊 Live Altcoin Prices")
st.caption("Gegevens via CoinGecko · Prijzen in euro · Automatisch ververst elke 10 seconden")

# ===== AUTOVERVERSING (elke 10 sec) =====
st_autorefresh(interval=10_000, key="refresh")

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
    "JUP": "jupiter"
}

# ===== PRIJZEN OPHALEN FUNCTIE =====
@st.cache_data(ttl=8)
def get_live_prices():
    ids = ",".join(COINS.values())
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies=eur"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Kon prijzen niet ophalen: {e}")
        return {}

# ===== PRIJZEN TONEN =====
prices = get_live_prices()

st.markdown("---")
for symbol, coingecko_id in COINS.items():
    price = prices.get(coingecko_id, {}).get("eur", None)
    if price is not None:
        st.markdown(
            f"""
            <div style='padding: 10px 0; border-bottom: 1px solid #eee;'>
                <strong style='font-size: 1.2rem;'>{symbol}</strong><br>
                <span style='font-size: 1.8rem; color: #10A37F;'>€ {price:,.4f}</span>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.warning(f"{symbol}: prijs niet gevonden")
