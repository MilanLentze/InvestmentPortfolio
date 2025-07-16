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


    # ======= HARDGEKODEERDE PORTFOLIO =======
    PORTFOLIO = {
        "WIF":  {"aantal": 360.50809298, "inkoopprijs": 0.67645},
        "ZK":   {"aantal": 5268.41192482, "inkoopprijs": 0.04218},
        "RNDR": {"aantal": 72.35723437,   "inkoopprijs": 2.8543},
        "SUI":  {"aantal": 56.14946729,   "inkoopprijs": 2.5996},
        "LINK": {"aantal": 11.7140771,    "inkoopprijs": 11.9748},
        "STRK": {"aantal": 1218.53743738, "inkoopprijs": 0.10169},
        "FET":  {"aantal": 190.22287504,  "inkoopprijs": 0.60319},
        "INJ":  {"aantal": 7.94579095,    "inkoopprijs": 10.1083},
        "JUP":  {"aantal": 154.25295998,  "inkoopprijs": 0.38687}
    }
    CASH_EURO = 108.90


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
    st_autorefresh(interval=30_000, key="refresh")
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
   st.markdown("---")
   # === PORFOLIO BEREKENING OP BASIS VAN LIVE PRIJZEN ===
   st.markdown("---")
   st.markdown("<h4 style='color:#fff;'>📦 Portfolio Samenvatting</h4>", unsafe_allow_html=True)

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

           portfolio_rows.append({
               "Coin": sym,
               "Aantal": round(aantal, 2),
               "Inkoop (€)": round(inkoopprijs, 4),
               "Live (€)": round(price_now, 4),
               "Waarde (€)": round(current, 2),
               "Winst/Verlies (€)": round(winst, 2),
               "Rendement (%)": round(rendement_pct, 2)
           })

   df_portfolio = pd.DataFrame(portfolio_rows)
   st.dataframe(df_portfolio, use_container_width=True)

   # Samenvatting
   total_with_cash = total_current + CASH_EURO
   total_winst = total_current - total_invested
   total_rendement = (total_winst / total_invested) * 100 if total_invested > 0 else 0

   st.markdown(f"""
   <div style='background-color:#111; padding:15px; border-radius:10px; color:white;'>
       <h5>📈 Totaaloverzicht</h5>
       <ul>
           <li><b>Totale crypto waarde:</b> €{total_current:,.2f}</li>
           <li><b>Cash saldo:</b> €{CASH_EURO:,.2f}</li>
           <li><b>Totaalwaarde portfolio:</b> €{total_with_cash:,.2f}</li>
           <li><b>Totale winst/verlies:</b> €{total_winst:,.2f}</li>
           <li><b>Rendement:</b> {total_rendement:.2f}%</li>
       </ul>
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
        "AI": ["FET", "RNDR", "AGIX", "GRT", "TAO"],
        "ZK / Scaling": ["ZK", "STRK", "MANTA", "LRC"],
        "RWA": ["ONDO", "POLYX", "CFG"],
        "Gaming": ["IMX", "PYR", "GALA", "ILV"],
        "DePIN": ["HNT", "IOTX", "AKT", "RNDR"],
        "Oracle": ["LINK", "BAND", "TRB"]
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
        "Coin": ["FET", "STRK", "SUI", "ZK", "RNDR", "WIF", "INJ", "JUP"],
        "Allocatie %": ["20%", "20%", "15%", "15%", "10%", "10%", "5%", "5%"]
    }
    st.table(pd.DataFrame(july_data))

    # Augustus-allocatie
    st.subheader("📊 Allocatie – Augustus")
    aug_data = {
        "Coin": ["LINK", "INJ", "JUP", "ZK", "RNDR", "Cash buffer"],
        "Allocatie %": ["30%", "20%", "20%", "15%", "10%", "5%"]
    }
    st.table(pd.DataFrame(aug_data))

    # Exitstrategieën
    st.subheader("🚪 Exitstrategieën per Coin")

    st.markdown("### 🪙 WIF")
    st.markdown("""
    **Exitstrategie**  
    - Verkoop 40% bij 2x  
    - Verkoop 30% bij 3.5x  
    - Verkoop 20% bij 5x  
    - Laat 10% als moonbag of exit op hype top  
    
    **Uitleg**  
    Meme-coins stijgen snel en corrigeren hard.  
    Meestal mid-phase parabool.  
    Laatste winsten veiligstellen.  
    Meeliften op euforie of alles verkopen als hype piekt.
    """)

    st.markdown("### 🪙 FET")
    st.markdown("""
    **Exitstrategie**  
    - Verkoop 25% bij 3x  
    - Verkoop 35% bij 5x  
    - Verkoop 40% bij 8x of trailing stop  
    
    **Uitleg**  
    AI-coins pieken vaak vroeg. 3x is verstandig.  
    FET kan in fase 4 nog fors doorstijgen.  
    Laatste deel meelopen op AI-euforie of bij breakdown verkopen.
    """)
    
    st.markdown("### 🪙 STRK")
    st.markdown("""
    **Exitstrategie**  
    - Verkoop 30% bij 3x  
    - Verkoop 40% bij 5x  
    - Verkoop 30% via trailing vanaf 6x  
    
    **Uitleg**  
    ZK hype kan plots opkomen – winst vroeg nemen.  
    Piek meestal in één golf.  
    Laatste deel volgen met trailing stop voor piekmaximalisatie.
    """)
   
    st.markdown("### 🪙 RNDR")
    st.markdown("""
    **Exitstrategie**  
    - Verkoop 25% bij 2.5x  
    - Verkoop 35% bij 4x  
    - Verkoop 40% via trailing vanaf 5x  
    
    **Uitleg**  
    RNDR volgt AI-leiders, maar is iets trager.  
    AI tweede golf of hype push.  
    Laat laatste deel meelopen, maar stop-loss goed zetten.
    """)
    
    st.markdown("### 🪙 SUI")
    st.markdown("""
    **Exitstrategie**  
    - Verkoop 30% bij 3x  
    - Verkoop 40% bij 5x  
    - Verkoop 30% bij 6–7x of breakdown  
    
    **Uitleg**  
    L1’s stijgen vaak stabiel – blow-off rond 5x.  
    Daarna volledig uitstappen zodra hype over is.
    """)
    
    st.markdown("### 🪙 ZK")
    st.markdown("""
    **Exitstrategie**  
    - Verkoop 25% bij 3x  
    - Verkoop 35% bij 5x  
    - Verkoop 20% bij 8x  
    - Verkoop 20% via trailing stop  
    
    **Uitleg**  
    Accumuleert vaak langer – kleine winst vroeg.  
    ZK-fase begint dan door te breken.  
    Grote hypepiek – kans op rotatie.  
    Maximaliseer piek met stop (bv. -15% vanaf ATH).
    """)
       
    st.markdown("### 🪙 JUP")
    st.markdown("""
    **Exitstrategie**  
    - Verkoop 30% bij 2x  
    - Verkoop 40% bij 4x  
    - Verkoop 30% via trailing of news-based exit  
    
    **Uitleg**  
    Solana-infra coins kunnen snel pieken.  
    Momentum coin, gevoelig voor hype.  
    Volg hypecycli op X / Solana ecosysteem.
    """)
    
    st.markdown("### 🪙 INJ")
    st.markdown("""
    **Exitstrategie**  
    - Verkoop 20% bij 3x  
    - Verkoop 30% bij 5x  
    - Verkoop 30% bij 7x  
    - Verkoop 20% via trailing  
    
    **Uitleg**  
    Undervalued asset, piekt vaak laat.  
    Start van FOMO-fase voor underdogs.  
    Laatste piek in altseason voor dit type coin.  
    Laat meeliften als narratief oppakt.
    """)
    
    st.markdown("### 🪙 LINK")
    st.markdown("""
    **Exitstrategie**  
    - Verkoop 25% bij 2x  
    - Verkoop 35% bij 4x  
    - Verkoop 40% bij 6x  
    
    **Uitleg**  
    Late mover, breakout komt laat maar vaak krachtig.  
    Infra-plays pieken vaak als laatste.  
    Na breakout is het meestal snel over – dus afbouwen.
    """)

st.markdown("---")
st.markdown("---")
st.markdown("---")
st.markdown("---")
st.caption("Dashboard ontwikkeld door Milan")
