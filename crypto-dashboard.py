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
    label, .stSelectbox label, .stCheckbox > div {
        color: #AAAAAA !important;
        font-weight: normal;
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
    "JUP": "jupiter"
}

# ===== PRIJZEN OPHALEN FUNCTIE =====
@st.cache_data(ttl=25)
def get_live_prices():
    ids = ",".join(COINS.values())
    url = (
        f"https://api.coingecko.com/api/v3/simple/price"
        f"?ids={ids}&vs_currencies=eur&include_24hr_change=true"
    )
    try:
        time.sleep(1)
        response = requests.get(url, timeout=10)
        if response.status_code == 429:
            raise Exception("📉 API-limiet bereikt (429 Too Many Requests)")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Kon prijzen niet ophalen: {e}")
        return {}

# ===== USER FILTERS & CONTROLS =====
sort_option = st.selectbox("🔃 Sorteer op", ["Coin", "Prijs", "Verandering 24u"])
filter_enabled = st.checkbox("🔎 Toon alleen coins met > 5% stijging", value=True)

# ===== PRIJZEN TONEN MET VERANDERING =====
prices = get_live_prices()

# Voorverwerken
coin_data = []
for symbol, coingecko_id in COINS.items():
    data = prices.get(coingecko_id, {})
    price = data.get("eur", None)
    change = data.get("eur_24h_change", None)
    if price is not None and change is not None:
        coin_data.append({"symbol": symbol, "price": price, "change": change})

# Filteren
if filter_enabled:
    coin_data = [c for c in coin_data if c["change"] > 5]

# Sorteren
if sort_option == "Coin":
    coin_data = sorted(coin_data, key=lambda x: x["symbol"])
elif sort_option == "Prijs":
    coin_data = sorted(coin_data, key=lambda x: x["price"], reverse=True)
elif sort_option == "Verandering 24u":
    coin_data = sorted(coin_data, key=lambda x: x["change"], reverse=True)

# ===== HEADER + TABEL RENDEREN =====
st.markdown("---")
st.markdown(
    """
    <div style='padding: 10px 12px; border-bottom: 2px solid #666; display: grid; grid-template-columns: 80px 120px auto; font-weight: bold;'>
        <span>Coin</span>
        <span>Prijs</span>
        <span>Verandering 24u</span>
    </div>
    """,
    unsafe_allow_html=True
)

for coin in coin_data:
    change_icon = "🔼" if coin["change"] >= 0 else "🔽"
    color = "#10A37F" if coin["change"] >= 0 else "#FF4B4B"
    change_str = f"{change_icon} <span style='color: {color};'>{coin['change']:.2f}%</span>"

    st.markdown(
        f"""
        <div style='padding: 10px 12px; border-bottom: 1px solid #333; display: grid; grid-template-columns: 80px 120px auto; align-items: center;'>
            <span style='font-size: 0.95rem; color: white;'>{coin['symbol']}</span>
            <span style='font-size: 0.95rem; color: #10A37F; font-family: monospace;'>€ {coin['price']:.4f}</span>
            <span style='font-size: 0.95rem;'>{change_str}</span>
        </div>
        """,
        unsafe_allow_html=True
    )

st.markdown("---")
st.markdown("---")
st.markdown("---")
st.markdown("---")
st.markdown("---")
st.markdown("---")
st.caption("Dashboard ontwikkeld door Milan • Powered by Streamlit + CoinGecko")
