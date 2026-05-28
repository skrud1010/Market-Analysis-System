import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import os
import plotly.graph_objects as go
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load Environment Variables
load_dotenv()
EXCHANGE_RATE_KEY = os.getenv("EXCHANGE_RATE_KEY")

st.set_page_config(layout="wide", page_title="PRO FX-Stock Analyzer", page_icon="💹")

# --- Theme-Adaptive Professional Financial Terminal CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
    
    /* Responsive Header Design using Streamlit Theme Variables */
    .terminal-header {
        border-left: 5px solid var(--primary-color, #00ffcc);
        padding-left: 15px;
        margin-bottom: 30px;
    }
    .terminal-title { 
        font-size: 26px; 
        font-weight: 800; 
        color: var(--text-color); 
        letter-spacing: -1px; 
    }
    .terminal-sub { 
        font-size: 13px; 
        color: var(--primary-color, #00ffcc); 
        font-family: 'JetBrains Mono', monospace; 
    }
    
    /* Metric Cards adapted for both Light & Dark Modes */
    .metric-card {
        background-color: var(--secondary-background-color);
        border: 1px solid var(--border-color, #30363d);
        border-radius: 12px;
        padding: 20px;
        text-align: left;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    .metric-label { 
        font-size: 12px; 
        color: var(--text-color); 
        opacity: 0.6;
        text-transform: uppercase; 
        letter-spacing: 1px; 
    }
    .metric-value { 
        font-size: 28px; 
        font-weight: 700; 
        margin: 8px 0; 
    }
    .metric-delta { 
        font-size: 14px; 
        font-family: 'JetBrains Mono', monospace;
        color: var(--text-color);
        opacity: 0.8;
    }
    
    /* Intelligence Briefing Panel Setup */
    .info-panel {
        background-color: var(--secondary-background-color);
        border-radius: 8px;
        padding: 15px;
        border-left: 4px solid var(--border-color, #30363d);
    }
    </style>
    
    <div class="terminal-header">
        <div class="terminal-title">CURRENCY-ADJUSTED YIELD ANALYZER</div>
        <div class="terminal-sub">SYSTEM STATUS: OPERATIONAL // PORTFOLIO TRACKING ACTIVE</div>
    </div>
    """, unsafe_allow_html=True)

# 1. Fetch live exchange rate data (Cached)
@st.cache_data(ttl=3600)
def get_fx_rate():
    url = f"https://v6.exchangerate-api.com/v6/{EXCHANGE_RATE_KEY}/latest/USD"
    try:
        return requests.get(url).json().get('conversion_rates', {}).get('KRW', 1350.0)
    except Exception:
        return 1350.0

# 2. Sidebar Control Panel
with st.sidebar:
    st.header("Input Information")
    ticker = st.text_input("Stock Ticker", value="AAPL").upper()
    buy_date = st.date_input("Purchase Date", value=datetime.now() - timedelta(days=365))
    
    st.markdown("---")
    st.subheader("Purchase Baseline")
    buy_price_usd = st.number_input("Purchase Price (USD)", value=150.0)
    buy_rate_krw = st.number_input("Purchase FX Rate (KRW)", value=1200.0)
    quantity = st.number_input("Quantity Held", value=10, min_value=1)
    
    st.markdown("---")
    st.caption("PRO-LEVEL INVESTMENT ANALYSIS")

# 3. Core Logic & Financial Calculations
try:
    current_price_usd = float(yf.Ticker(ticker).history(period="1d")['Close'].iloc[-1])
    current_rate_krw = get_fx_rate()

    # Calculate partitioned returns
    stock_return_pct = ((current_price_usd - buy_price_usd) / buy_price_usd) * 100
    fx_return_pct = ((current_rate_krw - buy_rate_krw) / buy_rate_krw) * 100
    
    # Calculate fully consolidated KRW return metrics
    total_buy_krw = buy_price_usd * buy_rate_krw * quantity
    total_curr_krw = current_price_usd * current_rate_krw * quantity
    total_return_pct = ((total_curr_krw - total_buy_krw) / total_buy_krw) * 100
    total_pnl_krw = total_curr_krw - total_buy_krw

    # 4. Main Matrix Grid Display
    m1, m2, m3 = st.columns(3)
    
    # Global Trading Color Logic (Green for Profit, Blue/Red adaptive)
    c_stock = "#00cc66" if stock_return_pct >= 0 else "#ff4d4d"
    c_fx = "#00cc66" if fx_return_pct >= 0 else "#ff4d4d"
    c_total = "#00cc66" if total_return_pct >= 0 else "#ff4d4d"
    
    with m1:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Stock Performance (USD)</div>
                <div class="metric-value" style="color:{c_stock}">{stock_return_pct:+.2f}%</div>
                <div class="metric-delta">USD {buy_price_usd:,.2f} → {current_price_usd:,.2f}</div>
            </div>
            """, unsafe_allow_html=True)

    with m2:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">FX Translation (KRW)</div>
                <div class="metric-value" style="color:{c_fx}">{fx_return_pct:+.2f}%</div>
                <div class="metric-delta">KRW {buy_rate_krw:,.1f} → {current_rate_krw:,.1f}</div>
            </div>
            """, unsafe_allow_html=True)

    with m3:
        st.markdown(f"""
            <div class="metric-card" style="border: 1px solid {c_total}77;">
                <div class="metric-label">Total Net Return (Adj.)</div>
                <div class="metric-value" style="color:{c_total}">{total_return_pct:+.2f}%</div>
                <div class="metric-delta">Net P/L: ₩{total_pnl_krw:,.0f}</div>
            </div>
            """, unsafe_allow_html=True)

    # 5. Data Visualization Area: Performance Attribution Chart
    st.markdown("---")
    st.subheader("Profit Attribution Analysis")
    
    fig = go.Figure(go.Bar(
        x=["Stock Return", "FX Gain/Loss", "Total Yield"],
        y=[stock_return_pct, fx_return_pct, total_return_pct],
        marker_color=['#6e7681', '#8b949e', '#00ffcc'],
        text=[f"{stock_return_pct:+.1f}%", f"{fx_return_pct:+.1f}%", f"{total_return_pct:+.1f}%"],
        textposition='auto',
    ))
    
    # Grid color adjust mapping for dynamic look
    fig.update_layout(
        template="plotly_dark",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        height=380,
        margin=dict(t=20, b=20, l=10, r=10),
        yaxis=dict(title="Return (%)", gridcolor="rgba(128,128,128,0.2)")
    )
    st.plotly_chart(fig, use_container_width=True)

    # 6. Strategic Operational Insight Briefing
    st.markdown("### Operational Insight")
    
    if stock_return_pct > 0 and fx_return_pct < 0:
        status, msg = "CURRENCY EROSION", "Asset value gains are currently being heavily compressed or eroded by the weakening of the foreign exchange rate."
    elif stock_return_pct < 0 and fx_return_pct > 0:
        status, msg = "FX CUSHION ACTIVE", "Although the underlying asset value declined, the strength of the USD is effectively cushioning and mitigating net portfolio losses."
    elif stock_return_pct > 0 and fx_return_pct > 0:
        status, msg = "DUAL-ENGINE GROWTH", "Optimal conditions met. Simultaneous upward movements in both stock equity and the foreign currency rate have maximized net yields."
    else:
        status, msg = "SYSTEMIC DRAWDOWN", "Simultaneous correction observed in both asset prices and currency rates. Strategic risk review and position checking required."

    st.markdown(f"""
        <div class="info-panel">
            <b style="color:var(--primary-color, #00ffcc); font-family: 'JetBrains Mono';">{status}</b><br/>
            <span style="font-size:14px; color:var(--text-color); opacity: 0.85;">{msg}</span>
        </div>
        """, unsafe_allow_html=True)

except Exception as e:
    st.error(f"ENGINE CORE ERROR: {e}")