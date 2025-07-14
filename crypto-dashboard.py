import streamlit as st
import requests
import time

# ===== Streamlit Config =====
st.set_page_config(page_title="📈 Live Altcoin Prices", layout="wide")
st.title("📈 Live Prijzen van Altcoins (CoinGecko)")

# ===== CoinGecko coin IDs =====
COINS = {
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

# ===== API Call Function =====
@st.cache_data(ttl=60)  # cache data for 60 sec
def get_prices():
    ids = ",".join(COINS.values())
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies=eur"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        st.error("Fout bij ophalen van prijzen.")
        return {}

# ===== Price Display =====
def display_prices(prices):
    cols = st.columns(3)
    for i, (symbol, coingecko_id) in enumerate(COINS.items()):
        price = prices.get(coingecko_id, {}).get("eur", "N/A")
        with cols[i % 3]:
            st.metric(label=symbol, value=f"€ {price}")

# ===== Live Update =====
placeholder = st.empty()

while True:
    with placeholder.container():
        prices = get_prices()
        display_prices(prices)
    time.sleep(10)  # update elke 10 seconden
