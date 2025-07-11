import streamlit as st
import requests
import hmac
import hashlib
import base64
import pandas as pd
import plotly.express as px
from datetime import datetime, timezone

# =============================
# Streamlit Config
# =============================
st.set_page_config(page_title="Crypto Dashboard", layout="wide")
st.title("📈 Crypto Portfolio & Strategie Dashboard")

# =============================
# API Keys from Streamlit Secrets
# =============================
API_KEY = st.secrets["OKX_API_KEY"]
SECRET_KEY = st.secrets["OKX_SECRET_KEY"]
PASSPHRASE = st.secrets["OKX_PASSPHRASE"]

# =============================
# OKX API Helpers
# =============================
def get_signature(timestamp, method, request_path, body=''):
    message = f'{timestamp}{method}{request_path}{body}'
    mac = hmac.new(SECRET_KEY.encode(), message.encode(), hashlib.sha256)
    return base64.b64encode(mac.digest()).decode()

def get_okx_balances():
    url = "https://www.okx.com/api/v5/asset/balances"
    timestamp = datetime.utcnow().replace(tzinfo=timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')
    headers = {
        'OK-ACCESS-KEY': API_KEY,
        'OK-ACCESS-SIGN': get_signature(timestamp, 'GET', '/api/v5/account/balance'),
        'OK-ACCESS-TIMESTAMP': timestamp,
        'OK-ACCESS-PASSPHRASE': PASSPHRASE,
        'Content-Type': 'application/json'
    }
    res = requests.get(url, headers=headers)
    return res.json()

# =============================
# Tabs voor alle onderdelen
# =============================
tabs = st.tabs([
    "📊 Portfolio",
    "📤 Winststrategie",
    "🔁 Re-entry Plan",
    "🧠 Narratieven",
    "📅 Event Kalender",
    "📦 Watchlist",
    "🧮 Scenario Analyse",
    "🧠 Reflectie"
])

# =============================
# Tab 1: Portfolio
# =============================
with tabs[0]:
    st.header("📊 Live Portfolio via OKX API")
    data = get_okx_balances()

    st.subheader("📦 API Response Debug (ruwe JSON output)")
    st.json(data)

    # Verwerking met controles
    if not isinstance(data, dict) or 'data' not in data:
        st.error("❌ Ongeldige API-response. Check of je API keys correct zijn en of je account assets bevat.")
        st.stop()

    if not data['data']:
        st.warning("⚠️ Je hebt geen balans op dit account of subaccount.")
        st.stop()

    first_entry = data['data'][0]
    if 'details' not in first_entry:
        st.error("🔒 API-response bevat geen 'details'. Mogelijk gebruik je het verkeerde wallettype (bv. Funding vs Trading).")
        st.stop()

    coins = first_entry['details']
    df = pd.DataFrame(coins)
    df['availBal'] = df['availBal'].astype(float)
    df = df[df['availBal'] > 0].sort_values('availBal', ascending=False)

    st.success("✅ Data succesvol opgehaald!")
    st.dataframe(df[['ccy', 'availBal']], use_container_width=True)

    fig = px.pie(df, names='ccy', values='availBal', title='Portfolio Allocatie')
    st.plotly_chart(fig, use_container_width=True)

    st.metric(label="📦 Totale Portfolio Waarde (units)", value=f"{df['availBal'].sum():.2f}")

# =============================
# Placeholder Tabs
# =============================
placeholders = [
    "Winststrategie",
    "Re-entry Plan",
    "Narratieven",
    "Event Kalender",
    "Watchlist",
    "Scenario Analyse",
    "Reflectie"
]

for i, name in enumerate(placeholders, start=1):
    with tabs[i]:
        st.header(f"🔧 {name}")
        uploaded = st.file_uploader(f"Upload {name} CSV", type="csv", key=name)
        if uploaded:
            df = pd.read_csv(uploaded)
            st.dataframe(df, use_container_width=True)
        else:
            st.info(f"Je kunt hier je {name.lower()} uploaden als CSV.")
