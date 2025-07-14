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

# ===== FUNCTIE: Prijzen ophalen =====
@st.cache(ttl=8)
