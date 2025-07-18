import streamlit as st
import requests
import time
from streamlit_autorefresh import st_autorefresh
import plotly.graph_objects as go
from datetime import datetime
import json
import plotly.express as px  # mag ook bovenaan je script
import requests  # als je dit nog niet hebt bovenin
import yfinance as yf
import pandas as pd
import streamlit as st

# API-key opslaan
CMC_API_KEY = "9dc43086-b4b2-43ca-b2e7-5f5dcfadf9fb"

def get_btc_dominance_cmc(api_key):
    url = "https://pro-api.coinmarketcap.com/v1/global-metrics/quotes/latest"
    headers = {
        "Accepts": "application/json",
        "X-CMC_PRO_API_KEY": api_key
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data["data"]["btc_dominance"]
    except Exception as e:
        st.error(f"Fout bij ophalen BTC Dominance via CMC: {e}")
        return None
        
def bepaal_altseason_fase(p7, p24, ath_dist, vol_ratio, vol_change, volat):
    # Fase 5: Decline
    if p7 < -10 and vol_change < -20 and vol_ratio < 0.8:
        return "Decline"
    # Fase 4: Peak
    if p7 > 40 and ath_dist < 20 and vol_ratio > 1.5 and volat > 7:
        return "Peak"
    # Fase 3: Momentum
    if 20 < p7 <= 40 and vol_ratio > 1.2 and vol_change > 15:
        return "Momentum"
    # Fase 2: Rising
    if 5 < p7 <= 20 and vol_ratio > 1 and p24 > 0:
        return "Rising"
    # Fase 1: Base
    if p7 <= 5 and vol_ratio <= 1 and ath_dist > 50:
        return "Base"
    return "Base"

def get_coin_sparkline_and_volume(coin_id):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}?localization=false&sparkline=true"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        market_data = data["market_data"]
        sparkline = market_data["sparkline_7d"]["price"]
        volume_today = market_data["total_volume"]["eur"]
        volumes = [v for v in sparkline[-168:]]  # laatste 7 dagen (24*7 = 168)
        return {
            "sparkline": sparkline,
            "volatility_7d": round(pd.Series(sparkline).std(), 2),
            "volume_ratio": round(volume_today / pd.Series(volumes).mean(), 2) if volumes else 1.0
        }
    except Exception as e:
        st.warning(f"❗️Geen sparkline voor {coin_id}: {e}")
        return {
            "sparkline": [],
            "volatility_7d": 4.0,
            "volume_ratio": 1.0
        }

   

# ========== CONFIGURATIE ==========
st.set_page_config(page_title="📈 Live Altcoin Prices", layout="centered")
tab1, tab2, tab3 = st.tabs(["📊 Live Altcoin Prices", "🧠 Altseason Insights", "📅 Investeringsplan & Exitstrategy" ])

st.markdown("""
    <style>
    .main {
        background-color: #000000;
        color: white;
    }
    div[data-testid="stDataFrame"] {
        background-color: #000000;
        color: white;
    }
    thead th {
        background-color: #111 !important;
        color: white !important;
    }
    tbody td {
        background-color: #000000 !important;
        color: white !important;
    }
    div[data-testid="column"] label, .stTextInput>div>div>input {
        color: white !important;
    }
    h1, h2, h3, h4, h5, h6, p {
        color: white !important;
    }
    </style>
""", unsafe_allow_html=True)

with tab1:
    st.title("📊 Live Altcoin Prices")
    st.caption("Gegevens via CoinGecko · Prijzen in euro · Automatisch ververst elke 30 seconden")
    st_autorefresh(interval=45_000, key="refresh")
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
   

    # ===== COINGECKO IDs & Narratieven =====
    COINS = {
        "WIF": {"id": "dogwifcoin", "narrative": "Meme"},
        "ZK": {"id": "zksync", "narrative": "ZK / L2"},
        "RENDER": {"id": "render-token", "narrative": "AI / GPU"},
        "SUI": {"id": "sui", "narrative": "L1"},
        "DEGEN": {"id": "degen", "narrative": "SocialFi / Meme"},
        "STRK": {"id": "starknet", "narrative": "ZK / L2"},
        "FET": {"id": "fetch-ai", "narrative": "AI"},
        "INJ": {"id": "injective-protocol", "narrative": "DeFi"},
        "AEVO": {"id": "aevo-2", "narrative": "Options / Derivatives"},
    }
    
    # ======= HARDGEKODEERDE PORTFOLIO =======
    PORTFOLIO = {
        "WIF":  {"aantal": 360.50809298, "inkoopprijs": 0.67645},
        "ZK":   {"aantal": 5642.24306186, "inkoopprijs": 0.043023},
        "RENDER": {"aantal": 76.51597485,   "inkoopprijs": 2.9003},
        "SUI":  {"aantal": 56.14946729,   "inkoopprijs": 2.5996},
        "DEGEN": {"aantal": 40767.88288737,    "inkoopprijs": 0.0041699},
        "STRK": {"aantal": 1568.47270184, "inkoopprijs": 0.10724},
        "FET":  {"aantal": 190.22287504,  "inkoopprijs": 0.60319},
        "INJ":  {"aantal": 7.94579095,    "inkoopprijs": 10.1083},
        "AEVO":  {"aantal": 685.25251414,  "inkoopprijs": 0.10434}
    }
    CASH_EURO = 0

    # ===== FORMAT FUNCTIE VOOR PERCENTAGES =====
    def format_change(value):
        if value is None:
            return "<span style='color: #666;'>–</span>"
        icon = "🔼" if value >= 0 else "🔽"
        color = "#10A37F" if value >= 0 else "#FF4B4B"
        return f"{icon} <span style='color: {color};'>{value:.2f}%</span>"
  
    @st.cache_data(ttl=25)
    def get_multiple_cmc_data(api_key, symbols):
        url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
        headers = {
            "Accepts": "application/json",
            "X-CMC_PRO_API_KEY": api_key
        }
        params = {
            "symbol": ",".join(symbols),
            "convert": "EUR"
        }
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            raw_data = response.json().get("data", {})
    
            result = {}
            for sym in symbols:
                if sym in raw_data:
                    quote = raw_data[sym]["quote"]["EUR"]
                    result[sym] = {
                        "price": quote["price"],
                        "market_cap": quote.get("market_cap"),
                        "change_24h": quote.get("percent_change_24h", 0),
                        "change_7d": quote.get("percent_change_7d", 0),
                        "change_30d": quote.get("percent_change_30d", 0),
                        "ath": None  # Optioneel: later invullen
                    }
                else:
                    st.warning(f"⚠️ Geen data voor {sym} in CMC-response.")
            return result
    
        except Exception as e:
            st.error(f"Fout bij ophalen CMC-data: {e}")
            return {}

  
    
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
        "RENDER": "Fase 2-3 – Mid Caps & Narratieven",
        "SUI": "Fase 2 – Mid Caps & Narratieven",
        "DEGEN": "Fase 4 – FOMO & Memecoins",
        "STRK": "Fase 1-2 – Blue Chips & Mid C",
        "FET": "Fase 2 – Mid Caps & Narratieven",
        "INJ": "Fase 2 – Mid Caps & Narratieven",
        "AEVO": "Fase 3 – Hypefase / Narratiefpiek"
    }
    
    #======= Rendement X =======
    
    def calculate_expected_x_score_model(current_price, ath_price, current_marketcap, narrative, price_change_30d):
        # ====== Fallbacks voor missende data ======
        current_price = current_price or 0.0001  # voorkom deling door nul
        ath_price = ath_price or 0
        current_marketcap = current_marketcap or 1
        price_change_30d = price_change_30d if price_change_30d is not None else 0
    
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
    
        return round(min(expected_x, 15), 1)

    
    # ===== PRIJZEN TONEN MET VERANDERING =====
    # Ophalen van alle prijsdata via CMC
    symbols = list(COINS.keys())
    prices = get_multiple_cmc_data(CMC_API_KEY, symbols)
    
    coin_data = []
    
    for symbol, info in COINS.items():
        cmc = prices.get(symbol)
    
        if not cmc:
            continue  # sla over als geen data beschikbaar
    
        price = cmc.get("price")
        market_cap = cmc.get("market_cap")
        change_24h = cmc.get("change_24h", 0)
        change_7d = cmc.get("change_7d", 0)
        change_30d = cmc.get("change_30d", 0)
    
       # ===== Extra indicatoren =====
        ath_fallbacks = {
            "AEVO": 1.20,
            "DEGEN": 0.012
        }
        ath = cmc.get("ath") or ath_fallbacks.get(symbol, 0)
        distance_to_ath = max((1 - price / ath) * 100, 0) if ath > 0 else 100
        
        # Voor nu placeholder data – later vervang je dit met echte sparkline/volume data
        volume_ratio = 1.0  # TODO: vervangen met echte waarde
        volume_change_24h = cmc.get("change_24h", 0)  # tijdelijke benadering
        volatility_7d = 4.0  # TODO: via CoinGecko sparkline
        
        coingecko_id = info["id"]
        extra = get_coin_sparkline_and_volume(coingecko_id)
        
        volatility_7d = extra["volatility_7d"]
        volume_ratio = extra["volume_ratio"]

        fase = bepaal_altseason_fase(
            p7=change_7d,
            p24=change_24h,
            ath_dist=distance_to_ath,
            vol_ratio=volume_ratio,
            vol_change=volume_change_24h,
            volat=volatility_7d
        )
        fase_icons = {
            "Base": "⚙️",
            "Rising": "📈",
            "Momentum": "🚀",
            "Peak": "🧨",
            "Decline": "🛑"
        }
        fase_met_icoon = f"{fase_icons.get(fase, '')} {fase}"

    
        if price is not None:
            coin_data.append({
                "symbol": symbol,
                "price": price,
                "change_24h": change_24h,
                "change_7d": change_7d,
                "change_30d": change_30d,
                "narrative": info["narrative"],
                "altseason_phase": fase_met_icoon,
                "rendement_pct": (
                    ((price - PORTFOLIO[symbol]["inkoopprijs"]) / PORTFOLIO[symbol]["inkoopprijs"]) * 100
                    if symbol in PORTFOLIO else 0
                )

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
    header[7].markdown("**Rendement %**")
    
    for coin in coin_data:
        row = st.columns([1, 2, 2, 2, 2, 2, 2, 2])
        row[0].markdown(f"**{coin['symbol']}**")
        row[1].markdown(f"€ {coin['price']:.4f}")
        row[2].markdown(format_change(coin['change_24h']), unsafe_allow_html=True)
        row[3].markdown(format_change(coin['change_7d']), unsafe_allow_html=True)
        row[4].markdown(format_change(coin['change_30d']), unsafe_allow_html=True)
        row[5].markdown(coin['narrative'])
        row[6].markdown(coin['altseason_phase'])
        kleur = "#10A37F" if coin["rendement_pct"] >= 0 else "#FF4B4B"
        row[7].markdown(f"<span style='color:{kleur};'>{coin['rendement_pct']:.2f}%</span>", unsafe_allow_html=True)


    st.markdown("---")
    st.markdown("---")
    # === PORTFOLIO BEREKENING OP BASIS VAN LIVE PRIJZEN ===
    st.markdown("---")

    total_current = 0
    total_invested = 0
    portfolio_rows = []

    for coin in coin_data:
        sym = coin["symbol"]
        price_now = coin["price"]
        if sym in PORTFOLIO:
            aantal = PORTFOLIO[sym]["aantal"]
            inkoopprijs = PORTFOLIO[sym]["inkoopprijs"]
            invested = aantal * inkoopprijs
            current = aantal * price_now
            winst = current - invested
            rendement_pct = (winst / invested) * 100 if invested > 0 else 0

            total_current += current
            total_invested += invested

    # Samenvatting
    total_with_cash = total_current + CASH_EURO
    total_winst = total_current - total_invested
    total_rendement = (total_winst / total_invested) * 100 if total_invested > 0 else 0
    
    # Kleur voor winst/verlies en doel
    kleur_winst = "#10A37F" if total_winst >= 0 else "#FF4B4B"
    kleur_rendement = "#10A37F" if total_rendement >= 0 else "#FF4B4B"
    kleur_doel = "#10A37F" if total_with_cash >= 19737.67 else "#FF4B4B"
    
    # HTML-rendering in één blok
    # 1. Eerste blok: Portfolio Samenvatting
    st.markdown(f"""
    <div style='background-color:#111; padding:20px; border-radius:12px; color:white; font-size:18px;'>
        <h4 style='margin-bottom:15px;'>📦 Portfolio Samenvatting</h4>
        <h5 style='margin-bottom:10px;'>📘 <u>Totaaloverzicht</u></h5>
        <ul style='list-style-position: inside; line-height: 1.8;'>
            <li><b>Totaalwaarde portfolio:</b> €{total_with_cash:,.2f}</li>
            <li><b>Totale crypto waarde:</b> €{total_current:,.2f}</li>
            <li><b>Cash saldo:</b> €{CASH_EURO:,.2f}</li>
            <li><b>Totale winst/verlies:</b> <span style='color:{kleur_winst};'><b>€{total_winst:,.2f}</b></span></li>
            <li><b>Rendement:</b> <span style='color:{kleur_rendement};'><b>{total_rendement:.2f}%</b></span></li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # 2. Tweede blok: Doel & Scenario’s
    st.markdown(f"""
    <div style='background-color:#111; padding:20px; border-radius:12px; color:white; font-size:18px; margin-top:10px;'>
        <h5 style='margin-bottom:10px;'>🎯 <u>Doel & Scenario’s</u></h5>
        <ul style='list-style-position: inside; line-height: 1.8;'>
            <li><b>Doelwaarde:</b> <span style='color:{kleur_doel};'><b>€13.583,64</b></span></li>
            <li><b>Best Case:</b> €24.493,39</li>
            <li><b>Worst Case:</b> €8.566,03</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    # === DOEL PROGRESS CALCULATIE ===
    doelwaarde = 13583.64
    progress = min(total_with_cash / doelwaarde, 1.0)  # capped op 100%
    progress_percent = progress * 100
    euro_nodig = max(doelwaarde - total_with_cash, 0)
    
    # Dynamische kleur (rood <50%, geel <100%, groen =100%)
    if progress < 0.5:
        kleur_balk = "#FF4B4B"  # rood
    elif progress < 1:
        kleur_balk = "#FFD700"  # geel
    else:
        kleur_balk = "#10A37F"  # groen
    
    st.markdown(f"""
    <div style='background-color:#222; padding:12px 20px; border-radius:10px; margin-top:10px;'>
        <div style='font-size:16px; color:white; margin-bottom:5px;'>
            🚀 Voortgang naar doel: <b>{progress_percent:.1f}%</b>
        </div>
        <div style='width: 100%; background-color: #444; height: 20px; border-radius: 10px; overflow: hidden;'>
            <div style='width: {progress_percent:.1f}%; height: 100%; background-color: {kleur_balk};'></div>
        </div>
        <div style='font-size:14px; color:#bbb; margin-top:8px;'>
            Nog €{euro_nodig:,.2f} te gaan tot je doel.
        </div>
    </div>
    """, unsafe_allow_html=True)

#================= TAB 2 ===============
with tab2:
    st.title("🧠 Altseason Insights")
    st.markdown("""
        <style>
        div[data-testid="metric-container"] {
            background-color: transparent;
            border: 0px solid rgba(250, 250, 250, 0.2);
            padding: 10px;
            border-radius: 10px;
        }
        /* Label (bv. "Huidige BTC Dominance") */
        div[data-testid="metric-container"] label {
            color: white !important;
        }
        /* Waarde (bv. "63.63%") */
        div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
            color: white !important;
        }
        </style>
    """, unsafe_allow_html=True)

    # 1. Macro Indicatoren
    st.subheader("📈 Macro Indicatoren")
    macro = st.selectbox("Kies macro-indicator", ["BTC Dominance", "ETH/BTC Ratio", "Fear & Greed Index"])

    # 1.1 BTC Dominance
    if macro == "BTC Dominance":
        btc_dom = get_btc_dominance_cmc("9dc43086-b4b2-43ca-b2e7-5f5dcfadf9fb")
        if btc_dom is not None:
            st.metric(label="📊 Huidige BTC Dominance", value=f"{btc_dom:.2f}%")
            st.markdown(f"""
            - Een BTC dominance van **{btc_dom:.2f}%** betekent dat Bitcoin momenteel een aanzienlijk aandeel van de totale markt inneemt.
            - **>65%** – Bitcoinfase  
            - **60–65%** – Pre-Altseason / Rotatievoorfase  
            - **55–60%** – Opbouwfase (L1 grote caps stijgen fors)  
            - **50–55%** – Start Altseason (mid & Low caps breken uit)  
            - **45–50%** – Volledige Altseason / Piek (begin winst nemen)  
            - **<45%** – Blow-off fase / Markt oververhit (voor 45% alle winst eruit)
            """)
            st.caption("Bron: CoinMarketCap")

    # 1.2 ETH/BTC Ratio
    elif macro == "ETH/BTC Ratio":
        st.markdown("### 📉 ETH/BTC Ratio – Actuele Stand")

        def get_eth_btc_ratio():
            try:
                data = yf.download("ETH-BTC", period="1d", interval="1m", progress=False)
                if not data.empty:
                    return float(data["Close"].iloc[-1])
                else:
                    return None
            except Exception as e:
                st.error(f"Fout bij ophalen ETH/BTC ratio: {e}")
                return None

        eth_btc_ratio = get_eth_btc_ratio()
        if eth_btc_ratio is not None:
            st.metric(label="📉 ETH/BTC Ratio", value=f"{eth_btc_ratio:.4f}")
            st.markdown("""
            - **< 0.055** → vaak nog BTC-dominantie (early/pre-season)  
            - **0.06–0.07** → opbouwfase voor altseason
            - **> 0.07** → volwaardige altseason in zicht (ETH leidt de markt)
            - **> 0.08** → vaak piek/late fase van altseason (risico op topvorming)
            """)
        else:
            st.warning("Kon ETH/BTC ratio niet ophalen.")

    # 1.3 Fear & Greed Index
    elif macro == "Fear & Greed Index":
        st.markdown("### 😨😎 Fear & Greed Index – Crypto Sentiment")

        def get_fear_greed_index():
            url = "https://api.alternative.me/fng/?limit=1"
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                data = response.json()
                return int(data["data"][0]["value"]), data["data"][0]["value_classification"]
            except Exception as e:
                st.error(f"Fout bij ophalen Fear & Greed Index: {e}")
                return None, None

        index_value, classification = get_fear_greed_index()
        if index_value is not None:
            st.metric(label="📍 Huidige Index", value=f"{index_value}/100", delta=classification)
            st.markdown(f"""
            **Interpretatie:**
            - **0–24**: 😱 *Extreme Fear* → Markt in paniek → kans op koopmoment  
            - **25–49**: 😟 *Fear* → Negatief sentiment  
            - **50–74**: 🙂 *Greed* → Positieve vibe, kans op FOMO  
            - **75–100**: 🤪 *Extreme Greed* → Markt oververhit → tijd voor voorzichtigheid  

            > **Actuele status:** *{classification}*
            """)
            st.caption("Bron: alternative.me – Fear & Greed API")

    # 2. Kapitaalrotatie
    st.subheader("🔄 Kapitaalrotatie")

    st.markdown("""
    Bekijk hier de actuele altcoin rotatie en top 50 performance:
    
    👉 [Ga naar Blockchain Center – Altcoin Season Index](https://www.blockchaincenter.net/en/altcoin-season-index/)
    """)


    # 3. Narratief Activiteit
    st.subheader("🔥 Narratief Activiteit")
    
    narrative_sets = {
        "AI": ["FET", "RENDER", "AGIX", "GRT", "TAO"],
        "ZK / Scaling": ["ZK", "STRK", "MANTA", "LRC"],
        "RWA": ["ONDO", "POLYX", "CFG"],
        "Gaming": ["IMX", "PYR", "GALA", "ILV"],
        "DePIN": ["HNT", "IOTX", "AKT", "RENDER"],
        "Oracle": ["LINK", "BAND", "TRB"],
        "MEME": ["WIF", "PEPE", "DEGEN"]
    }
    
    selected_narrative = st.selectbox("Selecteer narratief", list(narrative_sets.keys()))
    selected_coins = narrative_sets[selected_narrative]
    selected_coins_with_btc = selected_coins + ["BTC"]
    
    headers = {
        "Accepts": "application/json",
        "X-CMC_PRO_API_KEY": CMC_API_KEY,
    }
    
    params = {
        "symbol": ",".join(selected_coins_with_btc),
        "convert": "USD"
    }
    
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        data = response.json()
    
        try:
            btc_7d = data["data"]["BTC"]["quote"]["USD"]["percent_change_7d"]
            growth_values = []
    
            for symbol in selected_coins:
                coin = data["data"].get(symbol)
                if coin:
                    change_7d = coin["quote"]["USD"]["percent_change_7d"]
                    verschil_btc = change_7d - btc_7d
                    growth_values.append(verschil_btc)
    
            if growth_values:
                avg_diff = sum(growth_values) / len(growth_values)
                kleur = "🟢" if avg_diff > 0 else "🔴"
                st.metric(label=f"Gemiddelde 7d groei t.o.v. BTC – {selected_narrative}", value=f"{avg_diff:.2f}%", delta=f"{kleur} tov BTC")
            else:
                st.warning("Geen geldige data voor geselecteerde coins.")
        except Exception as e:
            st.error(f"Fout bij berekenen gemiddelde verschil: {e}")
    else:
        st.error(f"Fout bij ophalen data: {response.status_code}")


#============= Tab 3 =============
with tab3:
    st.title("📅 Investeringsplan Juli & Augustus")

    # Juli-allocatie
    st.subheader("📊 Allocatie – Juli")
    july_data = {
        "Coin": ["STRK", "ZK", "SUI", "RENDER", "FET", "AEVO", "WIF", "INJ", "DEGEN"],
        "Allocatie %": ["20%", "15%", "15%", "10%", "10%", "10%", "10%", "5%", "5%"]
    }
    st.table(pd.DataFrame(july_data))

    # Augustus-allocatie
    st.subheader("📊 Allocatie – Augustus")
    aug_data = {
        "Coin": ["LINK", "INJ", "AEVO", "ZK", "RENDER", "Cash buffer"],
        "Allocatie %": ["30%", "20%", "20%", "15%", "10%", "5%"]
    }
    st.table(pd.DataFrame(aug_data))

    # Exitstrategieën
    st.subheader("🚪 Exitstrategieën per Coin")

    st.markdown("### 🪙 WIF")
    st.markdown("""
    **Exitstrategie**  
    🪙 WIF (Meme – piekt in Fase 4)
    30% bij 2x → Fase 3 (early hype/euforie)  
    40% bij 4x → Fase 4 (parabolisch momentum)  
    30% bij 6x → Fase 4 top of trailing stop -15%  
    Let op: explosief, maar snel terugval → trailing op laatste deel  
    
    **Uitleg**  
    Meme-coins stijgen snel en corrigeren hard.  
    Meestal mid-phase parabool.  
    Laatste winsten veiligstellen.  
    Meeliften op euforie of alles verkopen als hype piekt.
    """)

    st.markdown("### 🪙 FET")
    st.markdown("""
    **Exitstrategie**  
    25% bij 3x → Fase 2  
    35% bij 5x → Fase 3  
    40% bij 8x → trailing of Fase 4  
    AI push komt vaak vroeg, maar tweede piek is ook mogelijk  
    
    **Uitleg**  
    AI-coins pieken vaak vroeg. 3x is verstandig.  
    FET kan in fase 4 nog fors doorstijgen.  
    Laatste deel meelopen op AI-euforie of bij breakdown verkopen.
    """)
    
    st.markdown("### 🪙 STRK")
    st.markdown("""
    **Exitstrategie**  
    25% bij 3x → Fase 2  
    35% bij 5x → Fase 3  
    40% bij 8x → Fase 4 of trailing  
    Momentumcoin, kan hard en snel gaan – snel winstnemen  
    
    **Uitleg**  
    ZK hype kan plots opkomen – winst vroeg nemen.  
    Piek meestal in één golf.  
    Laatste deel volgen met trailing stop voor piekmaximalisatie.
    """)
   
    st.markdown("### 🪙 RENDER")
    st.markdown("""
    **Exitstrategie**  
    25% bij 3x → Fase 2 top  
    35% bij 5x → Fase 3 begin  
    40% bij 8x → Fase 3–4 overgang (trailing -15%)  
    AI kan cyclisch exploderen – trailing cruciaal in hype  
    
    **Uitleg**  
    RENDER volgt AI-leiders, maar is iets trager.  
    AI tweede golf of hype push.  
    Laat laatste deel meelopen, maar stop-loss goed zetten.
    """)
    
    st.markdown("### 🪙 SUI")
    st.markdown("""
    **Exitstrategie**  
    - 25% bij 2x → Fase 2–3 overgang  
    35% bij 4x → Fase 3  
    40% bij 6x → Fase 4  
    Meestal trage stijging, maar sterk blow-off topmoment  
    
    **Uitleg**  
    L1’s stijgen vaak stabiel – blow-off rond 5x.  
    Daarna volledig uitstappen zodra hype over is.
    """)
    
    st.markdown("### 🪙 ZK")
    st.markdown("""
    **Exitstrategie**  
    25% bij 3x → Fase 2 (breakout)  
    35% bij 5x → Fase 3  
    40% bij 8x → Fase 4 top of trailing stop  
    Structuur-play met late rotatie mogelijk – piekt vaak na AI  
    
    **Uitleg**  
    Accumuleert vaak langer – kleine winst vroeg.  
    ZK-fase begint dan door te breken.  
    Grote hypepiek – kans op rotatie.  
    Maximaliseer piek met stop (bv. -15% vanaf ATH).
    """)
       
    st.markdown("### 🪙 AEVO")
    st.markdown("""
    **Exitstrategie**  
    30% bij 3x → Fase 2  
    40% bij 5x → Fase 3  
    30% bij 7x → trailing of Fase 4  
    Afhankelijk van derivatenbuzz – scherp volgen op X en volume  
    
    **Uitleg**  
    AEVO speelt in op de groeiende Derivatives/Options-markt.  
    Wordt vaak laat wakker in de cycle, maar kan sterk presteren bij hype rond leverage of pro-trading tools.  
    Volg ontwikkelingen rond CEX-integraties en derivaten-volume op X.
    """)
    
    st.markdown("### 🪙 INJ")
    st.markdown("""
    **Exitstrategie**  
    25% bij 2x → Fase 2–3  
    35% bij 4x → Fase 3  
    40% bij 6x → Fase 4 top of trailing  
    Geen hypecoin, dus stabieler – piekt vaak laat  
    
    **Uitleg**  
    Undervalued asset, piekt vaak laat.  
    Start van FOMO-fase voor underdogs.  
    Laatste piek in altseason voor dit type coin.  
    Laat meeliften als narratief oppakt.
    """)
    
    st.markdown("### 🪙 DEGEN")
    st.markdown("""
    **Exitstrategie**  
    30% bij 2x → Fase 2 (early hype)  
    40% bij 3.5x → Fase 3  
    20% bij 5x → Fase 4  
    10% → moonbag of trailing bij extreme pump  
    High risk, high reward – momentumgedreven  
    
    **Uitleg**  
    Volatiele SocialFi/memecoin met explosief potentieel.  
    Kan snel 10–20x gaan, maar net zo hard terugvallen.  
    Zodra hype begint, fases strak afbouwen – timing is cruciaal.  
    """)

st.markdown("---")
st.markdown("---")
st.markdown("---")
st.markdown("---")
st.caption("Dashboard ontwikkeld door Milan")
