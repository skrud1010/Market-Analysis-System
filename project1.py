import streamlit as st
import pandas as pd
import yfinance as yf
import FinanceDataReader as fdr
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# 1. Environment & Config Setup
load_dotenv()
EXCHANGE_RATE_KEY = os.getenv("EXCHANGE_RATE_KEY")

st.set_page_config(layout="wide", page_title="Macro Markets Terminal")

# Custom UI Styling
st.markdown("""
    <style>
    .main-header {
        font-size: 28px; font-weight: 800; color: #ffcc00;
        padding: 10px; border-bottom: 2px solid #333; margin-bottom: 20px;
    }
    </style>
    <div class="main-header">Macro Markets: Commodity, Currency & Equity Analyzer</div>
    """, unsafe_allow_html=True)

# 2. Sidebar Control Panel
with st.sidebar:
    st.header("🔍 Analysis Settings")
    
    # Asset Mapping with corrected Steel Ticker (HRC=F)
    asset_map = {
        "Copper (HG=F)": {"ticker": "HG=F", "stock": "012330"}, 
        "Crude Oil (WTI)": {"ticker": "CL=F", "stock": "010950"}, 
        "Steel (HRC=F)": {"ticker": "HRC=F", "stock": "004020"}, 
        "Natural Gas": {"ticker": "NG=F", "stock": "036460"} 
    }
    
    selected_asset = st.selectbox("Select Commodity", list(asset_map.keys()))
    related_stock = st.text_input("Related KOSPI Stock Code", value=asset_map[selected_asset]["stock"])
    
    currency_pair = st.selectbox("Currency Pair Base", ["USD/KRW", "EUR/KRW", "JPY/KRW"])
    days = st.slider("Analysis Period (Days)", 30, 730, 365)
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

# 3. Data Loading Functions
@st.cache_data
def get_data(commodity_ticker, stock_ticker, start):
    commodity = yf.download(commodity_ticker, start=start)['Close'].squeeze()
    stock = fdr.DataReader(stock_ticker, start=start)['Close'].squeeze()
    return commodity, stock

def get_exchange_rate(pair):
    base_currency = pair.split('/')[0]
    target_currency = pair.split('/')[1]
    url = f"https://v6.exchangerate-api.com/v6/{EXCHANGE_RATE_KEY}/pair/{base_currency}/{target_currency}"
    try:
        res = requests.get(url).json()
        return res.get('conversion_rate', 0)
    except:
        return 0

# 4. Main Core Logic
try:
    with st.spinner('Integrating and analyzing market data...'):
        commodity_data, stock_data = get_data(asset_map[selected_asset]["ticker"], related_stock, start_date)
        current_rate = get_exchange_rate(currency_pair)

    # Safety Check: Prevent crash if dataset is empty
    if commodity_data.empty or stock_data.empty:
        st.error("⚠️ Failed to retrieve data for the selected ticker or period. Please check the stock code or timeframe.")
    else:
        # 1. Key Metrics Section
        col1, col2, col3 = st.columns(3)
        with col1:
            val_comm = float(commodity_data.iloc[-1])
            st.metric(f"Current {selected_asset} Price", f"{val_comm:,.2f}")
        with col2:
            st.metric(f"Current {currency_pair} FX Rate", f"{current_rate:,.2f}")
        with col3:
            val_stock = float(stock_data.iloc[-1])
            st.metric("Related Stock Close", f"{val_stock:,.0f} KRW")

        # 2. Time-Series Correlation Trend Chart
        st.subheader("Time-Series Price Mismatch & Correlation Trend")
        
        # Merge series on date index
        combined_df = pd.concat([commodity_data, stock_data], axis=1).dropna()
        combined_df.columns = ['Comm', 'Stock']
        
        corr_value = combined_df['Comm'].corr(combined_df['Stock'])

        # Plotly Dual-Axis Line Chart
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(
            go.Scatter(x=combined_df.index, y=combined_df['Comm'], name=f"{selected_asset}", line=dict(color='#ffcc00', width=2)),
            secondary_y=False,
        )
        fig.add_trace(
            go.Scatter(x=combined_df.index, y=combined_df['Stock'], name="Stock Price", line=dict(color='#00ccff', width=2)),
            secondary_y=True,
        )
        
        fig.update_layout(
            template="plotly_dark",
            hovermode="x unified",
            legend=dict(x=0, y=1.1, orientation="h"),
            margin=dict(l=20, r=20, t=40, b=20),
            height=450
        )
        fig.update_yaxes(title_text="Commodity Value", secondary_y=False)
        fig.update_yaxes(title_text="Stock Value (KRW)", secondary_y=True)
        
        st.plotly_chart(fig, use_container_width=True)

        # 3. Global Trade Strategy Insights
        st.markdown("---")
        st.subheader("💡 Global Trade Strategy Insights")
        
        col_a, col_b = st.columns(2)
        with col_a:
            st.info(f"**Correlation Coefficient:** {corr_value:.2f}")
            if corr_value > 0.5:
                st.write("✅ **Strong Positive Correlation:** Equity values tend to rise alongside commodity cost shocks. Strong pricing power or inventory gains detected.")
            elif corr_value < -0.5:
                st.write("⚠️ **Strong Negative Correlation:** Rising raw material indexes act as a critical cost burden, heavily compressing profit margins for the business.")
            else:
                st.write("⚖️ **Neutral Correlation:** Price changes in this specific commodity do not show a statistically meaningful direct impact on the stock price.")

        with col_b:
            st.warning("**Risk Management Guide**")
            if current_rate > 1350:
                st.write("- **FX Warning:** The exchange rate is significantly high. High exposure to imported raw components will cause severe margin degradation.")
            else:
                st.write("- **FX Stable:** Foreign currency exposure is stable. Focus on finding micro-entry points or supply chain adjustments based purely on raw commodity bottoms.")

except Exception as e:
    st.error(f"Error during data processing: {e}")
    st.info("Please verify the tickers and ensure your internet connection or API keys are configured properly.")