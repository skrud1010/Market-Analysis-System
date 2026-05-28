import streamlit as st
import yfinance as yf
import requests
import os
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

# Load Environment Variables
load_dotenv()
EXCHANGE_RATE_KEY = os.getenv("EXCHANGE_RATE_KEY")

# Page Configuration
st.set_page_config(layout="wide", page_title="Professional Import Simulator")

# Theme-Adaptive Professional UI Styling
st.markdown("""
    <style>
    /* Main Header using Streamlit's native text color variable */
    .main-header {
        font-size: 32px;
        font-weight: 800;
        color: var(--text-color);
        text-align: left;
        padding-bottom: 15px;
        border-bottom: 2px solid var(--border-color, #3e444e);
        margin-bottom: 30px;
    }
    /* Cost Card leveraging secondary background for automatic light/dark adaptivity */
    .cost-card {
        background-color: var(--secondary-background-color);
        padding: 25px;
        border-radius: 12px;
        border: 1px solid var(--border-color, #30363d);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    /* Highlight text using the active primary theme color */
    .highlight {
        color: var(--primary-color);
        font-weight: bold;
    }
    </style>
    <div class="main-header">IMPORT COST ANALYSIS TERMINAL</div>
    """, unsafe_allow_html=True)

# Import Duty Rates Data Matrix
category_map = {
    "IT / Electronics (Laptop, Phone)": {"duty": 0.0, "tax": 0.1},
    "Apparel / Fashion (General)": {"duty": 0.13, "tax": 0.1},
    "Shoes / Bags": {"duty": 0.08, "tax": 0.1},
    "Processed Foods": {"duty": 0.30, "tax": 0.1},
    "Custom Settings": {"duty": 0.0, "tax": 0.1}
}

# Sidebar Control Panel
with st.sidebar:
    st.markdown("### Simulation Settings")
    use_yf = st.checkbox("Link Global Index / Stock", value=False)
    
    if use_yf:
        ticker = st.text_input("Enter Ticker", "AAPL")
        try:
            price_val = float(yf.Ticker(ticker).history(period="1d")['Close'].iloc[-1])
            st.caption(f"Latest Price: ${price_val:,.2f}")
        except Exception:
            st.caption("Invalid Ticker or Data Fetch Error")
            price_val = 1200.0
    else:
        price_val = st.number_input("Item Unit Price (USD)", value=1200.0)

    category = st.selectbox("Import Item Category", list(category_map.keys()))
    duty_rate = st.number_input("Applied Duty Rate", value=category_map[category]["duty"]) if category == "Custom Settings" else category_map[category]["duty"]
    
    ship_fee = st.number_input("Int'l Shipping Fee (USD)", value=45.0)

# Data Processing & Financial Calculation
def fetch_rate():
    url = f"https://v6.exchangerate-api.com/v6/{EXCHANGE_RATE_KEY}/latest/USD"
    try:
        return requests.get(url).json().get('conversion_rates', {}).get('KRW', 1350.0)
    except Exception:
        return 1350.0

try:
    ex_rate = fetch_rate()
    
    # Standard Trade Calculation: CIF Basis (Cost, Insurance and Freight)
    cif_usd = price_val + ship_fee
    cif_krw = cif_usd * ex_rate
    
    amt_duty = cif_krw * duty_rate
    amt_vat = (cif_krw + amt_duty) * 0.1
    final_cost = cif_krw + amt_duty + amt_vat

    # Main Grid Layout Configuration
    col_left, col_right = st.columns([6, 4])

    with col_left:
        st.subheader("Itemized Cost Breakdown")
        
        # Structure Analysis Table
        data = {
            "Component": ["Product Price (USD)", "Int'l Shipping Fee (USD)", "Exchange Rate (USD/KRW)", "Import Duty", "Import VAT"],
            "Details": [f"${price_val:,.2f}", f"${ship_fee:,.2f}", f"{ex_rate:,.2f} KRW", f"{duty_rate*100:.1f}%", "10.0%"],
            "Amount (KRW)": [
                f"{price_val * ex_rate:,.0f} KRW",
                f"{ship_fee * ex_rate:,.0f} KRW",
                f"{ex_rate:,.2f} KRW",
                f"{amt_duty:,.0f} KRW",
                f"{amt_vat:,.0f} KRW"
            ]
        }
        st.table(pd.DataFrame(data))

        # Contextual Market Intelligence Feedback
        st.markdown(f"**Current Market Analysis:** Import costs escalate sharply when the exchange rate exceeds 1,350 USD/KRW. The current rate is <span class='highlight'>{ex_rate:,.2f} KRW</span>.", unsafe_allow_html=True)

    with col_right:
        st.subheader("Total Estimated Import Cost")
        st.markdown(f"""
        <div class="cost-card">
            <p style="color: var(--text-color); opacity: 0.7; margin-bottom: 5px;">Total Estimated Cost</p>
            <h1 style="color: var(--primary-color); margin-top: 0; font-size: 42px;">{final_cost:,.0f} KRW</h1>
            <hr style="border-color: var(--border-color, #30363d);">
            <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                <span>Product Cost (Share)</span>
                <strong>{((cif_krw)/final_cost)*100:.1f}%</strong>
            </div>
            <div style="display: flex; justify-content: space-between; color: #ff7b72;">
                <span>Total Taxes (Duty + VAT)</span>
                <strong>{(amt_duty + amt_vat):,.0f} KRW</strong>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Visual Cost Breakdown Chart
        st.write("")
        cost_breakdown = pd.Series({"Base Cost": cif_krw, "Duty": amt_duty, "VAT": amt_vat})
        st.bar_chart(cost_breakdown)

except Exception as e:
    st.error(f"Data Connection Error: {e}")