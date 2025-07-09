# Improved and modular version of your Streamlit app

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- Constants --- #
crypto_assets = ["BTC", "ETH", "Altcoins", "Stablecoins"]
traditional_assets = ["Stocks", "ETFs", "Bonds"]
cash_asset = ["Cash"]

all_assets = crypto_assets + traditional_assets + cash_asset

# --- Utility Functions --- #
def validate_allocation(allocation_dict):
    total = sum(allocation_dict.values())
    return total, abs(total - 100) < 0.01

def get_risk_based_allocation(risk_tolerance, expected_return):
    base = {
        "Low":     {"BTC": 5,  "ETH": 5,  "Altcoins": 0,  "Stablecoins": 20, "Stocks": 30, "ETFs": 25, "Bonds": 10, "Cash": 5},
        "Medium":  {"BTC": 15, "ETH": 10, "Altcoins": 5,  "Stablecoins": 15, "Stocks": 25, "ETFs": 20, "Bonds": 5,  "Cash": 5},
        "High":    {"BTC": 25, "ETH": 20, "Altcoins": 15, "Stablecoins": 5,  "Stocks": 20, "ETFs": 10, "Bonds": 0,  "Cash": 5},
    }
    allocation = base[risk_tolerance].copy()

    if expected_return > 15:
        allocation["BTC"] = min(allocation["BTC"] + 5, 35)
        allocation["ETH"] = min(allocation["ETH"] + 5, 25)
        allocation["Altcoins"] = min(allocation["Altcoins"] + 5, 20)
        allocation["Bonds"] = max(allocation["Bonds"] - 5, 0)
        allocation["Cash"] = max(allocation["Cash"] - 5, 0)
    elif expected_return < 8:
        allocation["Bonds"] = min(allocation["Bonds"] + 5, 20)
        allocation["Stablecoins"] = min(allocation["Stablecoins"] + 5, 30)
        allocation["BTC"] = max(allocation["BTC"] - 5, 0)
        allocation["Altcoins"] = max(allocation["Altcoins"] - 5, 0)

    total = sum(allocation.values())
    allocation = {k: round(v * 100 / total, 1) for k, v in allocation.items()}
    return allocation

def create_comparison_charts(current, suggested):
    fig = make_subplots(
        rows=1, cols=2,
        specs=[[{"type": "domain"}, {"type": "domain"}]],
        subplot_titles=("Current Allocation", "Suggested Allocation")
    )
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57', '#FF9FF3', '#54A0FF', '#5F27CD']

    fig.add_trace(go.Pie(labels=list(current.keys()), values=list(current.values()), name="Current", marker_colors=colors), 1, 1)
    fig.add_trace(go.Pie(labels=list(suggested.keys()), values=list(suggested.values()), name="Suggested", marker_colors=colors), 1, 2)
    fig.update_layout(title_text="Portfolio Allocation Comparison", title_x=0.5)
    return fig

def create_allocation_table(current, suggested):
    rows = []
    for asset in current:
        c = current[asset]
        s = suggested[asset]
        rows.append({
            "Asset Class": asset,
            "Current (%)": f"{c:.1f}%",
            "Suggested (%)": f"{s:.1f}%",
            "Change (%)": f"{s - c:+.1f}%",
            "Direction": "📈" if s > c else "📉" if s < c else "➡️"
        })
    return pd.DataFrame(rows)

# --- Main App --- #
def main():
    st.set_page_config(page_title="Portfolio Optimizer", layout="wide")
    st.title("💰 Portfolio Optimizer: Crypto & Stocks")

    with st.sidebar:
        st.header("🎯 Configure Portfolio")
        risk = st.selectbox("Risk Tolerance", ["Low", "Medium", "High"], index=1)
        exp_return = st.slider("Expected Annual Return (%)", 3.0, 25.0, 10.0, 0.5)
        st.markdown("---")
        st.header("📊 Current Allocation")

        current = {}
        st.subheader("Crypto")
        for asset in crypto_assets:
            current[asset] = st.slider(f"{asset} (%)", 0, 100, 10)

        st.subheader("Traditional")
        for asset in traditional_assets:
            current[asset] = st.slider(f"{asset} (%)", 0, 100, 10)

        st.subheader("Cash")
        current["Cash"] = st.slider("Cash (%)", 0, 100, 10)

    total, valid = validate_allocation(current)
    st.sidebar.markdown(f"**Total: {total:.1f}%** {'✅' if valid else '❌'}")

    if st.button("🚀 Optimize Portfolio") and valid:
        suggested = get_risk_based_allocation(risk, exp_return)
        st.success("Portfolio optimization complete!")

        st.plotly_chart(create_comparison_charts(current, suggested), use_container_width=True)
        st.dataframe(create_allocation_table(current, suggested), use_container_width=True)
    elif not valid:
        st.warning("Please ensure total allocation equals 100%.")

if __name__ == "__main__":
    main()
