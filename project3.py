import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import os
import plotly.graph_objects as go
from datetime import datetime, timedelta
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()
EXCHANGE_RATE_KEY = os.getenv("EXCHANGE_RATE_KEY")

st.set_page_config(layout="wide", page_title="PRO FX-Stock Analyzer", page_icon="💹")

# --- 전문 금융 플랫폼 스타일 CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
    
    .stApp { background-color: #0b0e14; color: #d1d5db; font-family: 'Inter', sans-serif; }
    
    .terminal-header {
        border-left: 5px solid #00ffcc;
        padding-left: 15px;
        margin-bottom: 30px;
    }
    .terminal-title { font-size: 26px; font-weight: 800; color: #ffffff; letter-spacing: -1px; }
    .terminal-sub { font-size: 13px; color: #00ffcc; font-family: 'JetBrains Mono'; }
    
    .metric-card {
        background: linear-gradient(145deg, #161b22, #1c2128);
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 20px;
        text-align: left;
    }
    .metric-label { font-size: 12px; color: #8b949e; text-transform: uppercase; letter-spacing: 1px; }
    .metric-value { font-size: 28px; font-weight: 700; margin: 8px 0; }
    .metric-delta { font-size: 14px; font-family: 'JetBrains Mono'; }
    
    .info-panel {
        background-color: #161b22;
        border-radius: 8px;
        padding: 15px;
        border-left: 4px solid #30363d;
    }
    </style>
    
    <div class="terminal-header">
        <div class="terminal-title">CURRENCY-ADJUSTED YIELD ANALYZER</div>
        <div class="terminal-sub">SYSTEM STATUS: OPERATIONAL // PORTFOLIO TRACKING ACTIVE</div>
    </div>
    """, unsafe_allow_html=True)

# 1. 환율 데이터 획득 (Cached)
@st.cache_data(ttl=3600)
def get_fx_rate():
    url = f"https://v6.exchangerate-api.com/v6/{EXCHANGE_RATE_KEY}/latest/USD"
    try:
        return requests.get(url).json().get('conversion_rates', {}).get('KRW', 1350.0)
    except:
        return 1350.0

# 2. 사이드바 설정 (요청 내용 반영)
with st.sidebar:
    st.header("입력 정보")
    ticker = st.text_input("종목 코드 (Ticker)", value="AAPL").upper()
    buy_date = st.date_input("매수일", value=datetime.now() - timedelta(days=365))
    
    # 매수 시점의 데이터 입력
    st.markdown("---")
    st.subheader("매수 당시 기준")
    buy_price_usd = st.number_input("매수 단가 (USD)", value=150.0)
    buy_rate_krw = st.number_input("매수 당시 환율 (KRW)", value=1200.0)
    quantity = st.number_input("보유 수량 (QUANTITY)", value=10, min_value=1)
    
    st.markdown("---")
    st.caption("PRO-LEVEL INVESTMENT ANALYSIS")

# 3. 로직 및 데이터 처리
try:
    current_price_usd = yf.Ticker(ticker).history(period="1d")['Close'].iloc[-1]
    current_rate_krw = get_fx_rate()

    # 수익률 계산 로직
    stock_return_pct = ((current_price_usd - buy_price_usd) / buy_price_usd) * 100
    fx_return_pct = ((current_rate_krw - buy_rate_krw) / buy_rate_krw) * 100
    
    # 원화 환산 통합 수익률
    total_buy_krw = buy_price_usd * buy_rate_krw * quantity
    total_curr_krw = current_price_usd * current_rate_krw * quantity
    total_return_pct = ((total_curr_krw - total_buy_krw) / total_buy_krw) * 100
    total_pnl_krw = total_curr_krw - total_buy_krw

    # 4. 메인 화면: Grid Metrics
    m1, m2, m3 = st.columns(3)
    
    with m1:
        color = "#ff4b4b" if stock_return_pct >= 0 else "#0083ff"
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Stock Performance (USD)</div>
                <div class="metric-value" style="color:{color}">{stock_return_pct:+.2f}%</div>
                <div class="metric-delta">USD {buy_price_usd} → {current_price_usd:,.2f}</div>
            </div>
            """, unsafe_allow_html=True)

    with m2:
        color = "#ff4b4b" if fx_return_pct >= 0 else "#0083ff"
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">FX Translation (KRW)</div>
                <div class="metric-value" style="color:{color}">{fx_return_pct:+.2f}%</div>
                <div class="metric-delta">KRW {buy_rate_krw} → {current_rate_krw:,.2f}</div>
            </div>
            """, unsafe_allow_html=True)

    with m3:
        color = "#ff4b4b" if total_return_pct >= 0 else "#0083ff"
        st.markdown(f"""
            <div class="metric-card" style="border: 1px solid {color}55;">
                <div class="metric-label">Total Net Return (Adj.)</div>
                <div class="metric-value" style="color:{color}">{total_return_pct:+.2f}%</div>
                <div class="metric-delta">Net P/L: ₩{total_pnl_krw:,.0f}</div>
            </div>
            """, unsafe_allow_html=True)

    # 5. 시각화: Attribution Chart
    st.markdown("### 📊 Profit Attribution Analysis")
    
    fig = go.Figure(go.Bar(
        x=["Stock Return", "FX Gain/Loss", "Total Yield"],
        y=[stock_return_pct, fx_return_pct, total_return_pct],
        marker_color=['#30363d', '#30363d', '#00ffcc'],
        text=[f"{stock_return_pct:+.1f}%", f"{fx_return_pct:+.1f}%", f"{total_return_pct:+.1f}%"],
        textposition='auto',
    ))
    
    fig.update_layout(
        template="plotly_dark",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        height=400,
        margin=dict(t=20, b=20, l=0, r=0),
        yaxis=dict(title="Return (%)", gridcolor="#30363d")
    )
    st.plotly_chart(fig, use_container_width=True)

    # 6. 인텔리전트 브리핑
    st.markdown("### 🧠 Operational Insight")
    
    with st.container():
        if stock_return_pct > 0 and fx_return_pct < 0:
            status, msg = "⚠️ CURRENCY EROSION", "주가 상승분이 환율 하락에 의해 잠식되고 있습니다."
        elif stock_return_pct < 0 and fx_return_pct > 0:
            status, msg = "🛡️ FX CUSHION ACTIVE", "자산 가치는 하락했으나 달러 강세가 손실을 방어 중입니다."
        elif stock_return_pct > 0 and fx_return_pct > 0:
            status, msg = "🚀 DUAL-ENGINE GROWTH", "주가와 환율의 동반 상승으로 수익이 극대화되었습니다."
        else:
            status, msg = "🚨 SYSTEMIC DRAWDOWN", "주가와 환율이 동시에 하락했습니다. 리스크 점검이 필요합니다."

        st.markdown(f"""
            <div class="info-panel">
                <b style="color:#00ffcc">{status}</b><br/>
                <span style="font-size:14px; color:#abb2bf;">{msg}</span>
            </div>
            """, unsafe_allow_html=True)

except Exception as e:
    st.error(f"ENGINE ERROR: {e}")