import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

# Page configuration
st.set_page_config(
    page_title="Portfolio Optimizer: Crypto & Stocks",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-container {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 1rem 0;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

def validate_allocation(allocation_dict):
    """Validate that portfolio allocation sums to 100%"""
    total = sum(allocation_dict.values())
    return total, abs(total - 100) < 0.01

def get_risk_based_allocation(risk_tolerance, expected_return):
    """
    Generate optimized allocation based on risk tolerance and expected return
    This is a simplified model - in production, you'd use more sophisticated optimization
    """
    
    # Base allocations for different risk profiles
    risk_profiles = {
        "Low": {
            "BTC": 5, "ETH": 5, "Altcoins": 0, "Stablecoins": 20,
            "Stocks": 30, "ETFs": 25, "Bonds": 10, "Cash": 5
        },
        "Medium": {
            "BTC": 15, "ETH": 10, "Altcoins": 5, "Stablecoins": 15,
            "Stocks": 25, "ETFs": 20, "Bonds": 5, "Cash": 5
        },
        "High": {
            "BTC": 25, "ETH": 20, "Altcoins": 15, "Stablecoins": 5,
            "Stocks": 20, "ETFs": 10, "Bonds": 0, "Cash": 5
        }
    }
    
    base_allocation = risk_profiles[risk_tolerance].copy()
    
    # Adjust based on expected return
    if expected_return > 15:  # High return expectations
        # Increase crypto exposure
        base_allocation["BTC"] = min(base_allocation["BTC"] + 5, 35)
        base_allocation["ETH"] = min(base_allocation["ETH"] + 5, 25)
        base_allocation["Altcoins"] = min(base_allocation["Altcoins"] + 5, 20)
        # Reduce conservative assets
        base_allocation["Bonds"] = max(base_allocation["Bonds"] - 5, 0)
        base_allocation["Cash"] = max(base_allocation["Cash"] - 5, 0)
    elif expected_return < 8:  # Conservative expectations
        # Increase conservative assets
        base_allocation["Bonds"] = min(base_allocation["Bonds"] + 5, 20)
        base_allocation["Stablecoins"] = min(base_allocation["Stablecoins"] + 5, 30)
        # Reduce crypto exposure
        base_allocation["BTC"] = max(base_allocation["BTC"] - 5, 0)
        base_allocation["Altcoins"] = max(base_allocation["Altcoins"] - 5, 0)
    
    # Normalize to ensure sum = 100%
    total = sum(base_allocation.values())
    if total != 100:
        factor = 100 / total
        base_allocation = {k: round(v * factor, 1) for k, v in base_allocation.items()}
    
    return base_allocation

def generate_recommendations(current_allocation, suggested_allocation, risk_tolerance, expected_return):
    """Generate explanatory text for allocation changes"""
    recommendations = []
    
    for asset, current_pct in current_allocation.items():
        suggested_pct = suggested_allocation[asset]
        change = suggested_pct - current_pct
        
        if abs(change) > 1:  # Only show significant changes
            if change > 0:
                direction = "increase"
                emoji = "📈"
            else:
                direction = "decrease"
                emoji = "📉"
            
            # Asset-specific reasoning
            if asset == "BTC":
                reason = f"Bitcoin allocation adjusted based on {risk_tolerance.lower()} risk tolerance"
            elif asset == "ETH":
                reason = f"Ethereum exposure modified for {risk_tolerance.lower()} risk profile"
            elif asset == "Altcoins":
                reason = f"Altcoin allocation {'increased' if change > 0 else 'reduced'} due to risk preferences"
            elif asset == "Stablecoins":
                reason = f"Stablecoin buffer {'expanded' if change > 0 else 'reduced'} for portfolio stability"
            elif asset == "Stocks":
                reason = f"Stock allocation adjusted for {expected_return}% expected return target"
            elif asset == "ETFs":
                reason = f"ETF exposure modified for diversification and {risk_tolerance.lower()} risk"
            elif asset == "Bonds":
                reason = f"Bond allocation {'increased' if change > 0 else 'reduced'} based on risk tolerance"
            else:  # Cash
                reason = f"Cash position adjusted for liquidity management"
            
            recommendations.append(f"{emoji} **{direction.title()} {asset}** by {abs(change):.1f}%: {reason}")
    
    return recommendations

def create_comparison_charts(current_allocation, suggested_allocation):
    """Create side-by-side pie charts for current vs suggested allocation"""
    
    # Prepare data
    assets = list(current_allocation.keys())
    current_values = list(current_allocation.values())
    suggested_values = list(suggested_allocation.values())
    
    # Color scheme
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57', '#FF9FF3', '#54A0FF', '#5F27CD']
    
    # Create subplots
    fig = make_subplots(
        rows=1, cols=2,
        specs=[[{"type": "domain"}, {"type": "domain"}]],
        subplot_titles=("Current Allocation", "Suggested Allocation"),
        horizontal_spacing=0.1
    )
    
    # Current allocation pie chart
    fig.add_trace(go.Pie(
        labels=assets,
        values=current_values,
        name="Current",
        marker_colors=colors,
        textinfo='label+percent',
        textposition='inside',
        hole=0.3
    ), 1, 1)
    
    # Suggested allocation pie chart
    fig.add_trace(go.Pie(
        labels=assets,
        values=suggested_values,
        name="Suggested",
        marker_colors=colors,
        textinfo='label+percent',
        textposition='inside',
        hole=0.3
    ), 1, 2)
    
    fig.update_layout(
        title_text="Portfolio Allocation Comparison",
        title_x=0.5,
        showlegend=True,
        height=500,
        font=dict(size=12)
    )
    
    return fig

def create_allocation_table(current_allocation, suggested_allocation):
    """Create a comparison table of current vs suggested allocation"""
    
    data = []
    for asset in current_allocation.keys():
        current = current_allocation[asset]
        suggested = suggested_allocation[asset]
        change = suggested - current
        
        data.append({
            "Asset Class": asset,
            "Current (%)": f"{current:.1f}%",
            "Suggested (%)": f"{suggested:.1f}%",
            "Change (%)": f"{change:+.1f}%",
            "Change": "📈" if change > 0 else "📉" if change < 0 else "➡️"
        })
    
    df = pd.DataFrame(data)
    return df

# Main App
def main():
    st.markdown('<h1 class="main-header">💰 Portfolio Optimizer: Crypto & Stocks</h1>', unsafe_allow_html=True)
    
    # Sidebar for inputs
    st.sidebar.header("🎯 Portfolio Configuration")
    
    # Risk tolerance
    risk_tolerance = st.sidebar.selectbox(
        "Risk Tolerance",
        ["Low", "Medium", "High"],
        index=1,
        help="Select your risk tolerance level"
    )
    
    # Expected return
    expected_return = st.sidebar.slider(
        "Expected Annual Return (%)",
        min_value=3.0,
        max_value=25.0,
        value=10.0,
        step=0.5,
        help="Your target annual return percentage"
    )
    
    st.sidebar.markdown("---")
    st.sidebar.header("📊 Current Allocation")
    
    # Current allocation inputs
    current_allocation = {}
    
    # Crypto assets
    st.sidebar.subheader("💎 Crypto Assets")
    current_allocation["BTC"] = st.sidebar.slider("Bitcoin (BTC) %", 0, 100, 20, 1)
    current_allocation["ETH"] = st.sidebar.slider("Ethereum (ETH) %", 0, 100, 15, 1)
    current_allocation["Altcoins"] = st.sidebar.slider("Altcoins %", 0, 100, 10, 1)
    current_allocation["Stablecoins"] = st.sidebar.slider("Stablecoins %", 0, 100, 10, 1)
    
    # Traditional assets
    st.sidebar.subheader("📈 Traditional Assets")
    current_allocation["Stocks"] = st.sidebar.slider("Stocks %", 0, 100, 25, 1)
    current_allocation["ETFs"] = st.sidebar.slider("ETFs %", 0, 100, 15, 1)
    current_allocation["Bonds"] = st.sidebar.slider("Bonds %", 0, 100, 5, 1)
    current_allocation["Cash"] = st.sidebar.slider("Cash %", 0, 100, 0, 1)
    
    # Validate allocation
    total_allocation, is_valid = validate_allocation(current_allocation)
    
    if not is_valid:
        st.sidebar.markdown(f'<div class="warning-box">⚠️ Total allocation: {total_allocation:.1f}% (should be 100%)</div>', unsafe_allow_html=True)
    else:
        st.sidebar.markdown(f'<div class="success-box">✅ Total allocation: {total_allocation:.1f}%</div>', unsafe_allow_html=True)
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("🔍 Portfolio Analysis")
        
        # Display current portfolio metrics
        col_a, col_b, col_c = st.columns(3)
        
        with col_a:
            crypto_total = current_allocation["BTC"] + current_allocation["ETH"] + current_allocation["Altcoins"] + current_allocation["Stablecoins"]
            st.metric("Total Crypto Exposure", f"{crypto_total:.1f}%")
        
        with col_b:
            traditional_total = current_allocation["Stocks"] + current_allocation["ETFs"] + current_allocation["Bonds"]
            st.metric("Traditional Assets", f"{traditional_total:.1f}%")
        
        with col_c:
            st.metric("Cash Position", f"{current_allocation['Cash']:.1f}%")
    
    with col2:
        st.header("⚙️ Optimization")
        
        # Optimize button
        if st.button("🚀 Optimize Portfolio", type="primary", use_container_width=True):
            if is_valid:
                # Generate optimized allocation
                suggested_allocation = get_risk_based_allocation(risk_tolerance, expected_return)
                
                # Store in session state for persistence
                st.session_state['current_allocation'] = current_allocation
                st.session_state['suggested_allocation'] = suggested_allocation
                st.session_state['risk_tolerance'] = risk_tolerance
                st.session_state['expected_return'] = expected_return
                
                st.success("✅ Portfolio optimization complete!")
            else:
                st.error("❌ Please ensure total allocation equals 100%")
    
    # Display results if optimization has been run
    if 'suggested_allocation' in st.session_state:
        st.markdown("---")
        st.header("📊 Optimization Results")
        
        # Create comparison charts
        fig = create_comparison_charts(
            st.session_state['current_allocation'],
            st.session_state['suggested_allocation']
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Create allocation table
        st.subheader("📋 Detailed Allocation Comparison")
        df = create_allocation_table(
            st.session_state['current_allocation'],
            st.session_state['suggested_allocation']
        )
        st.dataframe(df, use_container_width=True)
        
        # Generate recommendations
        st.subheader("💡 Recommendations")
        recommendations = generate_recommendations(
            st.session_state['current_allocation'],
            st.session_state['suggested_allocation'],
            st.session_state['risk_tolerance'],
            st.session_state['expected_return']
        )
        
        if recommendations:
            for rec in recommendations:
                st.markdown(rec)
        else:
            st.info("🎯 Your current allocation is already well-optimized for your risk profile!")
        
        # Portfolio insights
        st.subheader("📈 Portfolio Insights")
        col1, col2 = st.columns(2)
        
        with col1:
            st.info(f"**Risk Profile:** {st.session_state['risk_tolerance']}")
            st.info(f"**Target Return:** {st.session_state['expected_return']:.1f}%")
        
        with col2:
            new_crypto_total = sum([st.session_state['suggested_allocation'][asset] for asset in ["BTC", "ETH", "Altcoins", "Stablecoins"]])
            new_traditional_total = sum([st.session_state['suggested_allocation'][asset] for asset in ["Stocks", "ETFs", "Bonds"]])
            
            st.info(f"**New Crypto Exposure:** {new_crypto_total:.1f}%")
            st.info(f"**New Traditional Assets:** {new_traditional_total:.1f}%")

if __name__ == "__main__":
    main()
