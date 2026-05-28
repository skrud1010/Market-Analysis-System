import streamlit as st
import pandas as pd
import FinanceDataReader as fdr
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

# 1. 페이지 설정: 레이아웃을 'wide'로 설정하여 공간 활용 극대화
st.set_page_config(layout="wide", page_title="Professional Trading Terminal", page_icon="📈")

# 2. 고도화된 CSS 스타일링
st.markdown("""
    <style>
    /* 전체 배경 및 폰트 */
    .stApp { background-color: #0e1117; color: #ffffff; }
    
    /* 헤더 스타일 */
    .main-header {
        font-size: 28px; font-weight: 800; letter-spacing: -1px;
        color: #00d4ff; text-align: left; padding: 10px 0;
        border-bottom: 2px solid #1e2130; margin-bottom: 20px;
    }
    
    /* 지표 카드 커스텀 */
    div[data-testid="metric-container"] {
        background-color: #1e2130; border: 1px solid #2d3139;
        padding: 15px; border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    div[data-testid="stMetricValue"] { color: #ffffff !important; font-size: 24px !important; }
    div[data-testid="stMetricLabel"] { color: #808495 !important; font-size: 14px !important; }
    
    /* 사이드바 스타일 */
    .css-1d391kg { background-color: #161b22; }
    </style>
    <div class="main-header">PRO-TERMINAL | Market Analysis System</div>
    """, unsafe_allow_html=True)

# 3. 사이드바 구성
with st.sidebar:
    st.title("🕹️ Control Panel")
    market = st.radio("MARKET", ["US STOCK", "KOREA STOCK"])
    
    if market == "US STOCK":
        ticker_list = ["AAPL", "MSFT", "NVDA", "TSLA", "GOOGL", "AMZN"]
    else:
        ticker_list = ["005930", "000660", "035420", "005380", "068270"]
        
    symbol = st.selectbox("SYMBOL", ticker_list)
    days = st.select_slider("PERIOD", options=[30, 60, 90, 180, 365], value=180)
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

# 4. 데이터 로딩 (보조지표 추가)
@st.cache_data
def get_pro_data(symbol, start):
    df = fdr.DataReader(symbol, start)
    # 기술적 보조지표 계산
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['MA60'] = df['Close'].rolling(window=60).mean()
    return df

@st.cache_data
def get_yf_info(symbol, market):
    yf_sym = symbol + ".KS" if market == "KOREA STOCK" else symbol
    return yf.Ticker(yf_sym).info

try:
    df = get_pro_data(symbol, start_date)
    info = get_yf_info(symbol, market)

    # --- UI 레이아웃 구성 ---
    
    # 상단 5개 Metrics (대시보드 핵심 지표)
    m1, m2, m3, m4, m5 = st.columns(5)
    last_close = df['Close'].iloc[-1]
    day_diff = last_close - df['Close'].iloc[-2]
    pct_diff = (day_diff / df['Close'].iloc[-2]) * 100
    
    unit = "$" if market == "US STOCK" else "₩"
    m1.metric("PRICE", f"{unit}{last_close:,.0f}")
    m2.metric("CHANGE", f"{day_diff:+.2f}", f"{pct_diff:.2f}%")
    m3.metric("HIGH (24H)", f"{df['High'].iloc[-1]:,.0f}")
    m4.metric("LOW (24H)", f"{df['Low'].iloc[-1]:,.0f}")
    m5.metric("VOLUME", f"{df['Volume'].iloc[-1]:,.0f}")

    # 좌측 차트(7) : 우측 정보(3) 비율로 분할
    left_col, right_col = st.columns([7, 3])

    with left_col:
        st.subheader("Technical Analysis")
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                           vertical_spacing=0.05, row_heights=[0.7, 0.3])

        # 1. 캔들스틱 및 이동평균선
        fig.add_trace(go.Candlestick(
            x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
            name='Price', increasing_line_color='#ff4b4b', decreasing_line_color='#0083ff'
        ), row=1, col=1)
        
        fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], name='MA20', line=dict(color='#ffea00', width=1)), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['MA60'], name='MA60', line=dict(color='#00ff88', width=1)), row=1, col=1)

        # 2. 거래량 차트
        fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name='Volume', marker_color='#333b4d'), row=2, col=1)

        fig.update_layout(
            template="plotly_dark", height=650, margin=dict(t=30, b=0, l=0, r=0),
            xaxis_rangeslider_visible=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig, use_container_width=True)

    with right_col:
        st.subheader("Market Summary")
        # 기업 정보 요약 카드
        with st.container():
            st.markdown(f"""
            <div style="background-color: #1e2130; padding: 20px; border-radius: 10px; border-left: 5px solid #00d4ff;">
                <h4 style="margin:0;">{info.get('longName', symbol)}</h4>
                <p style="color: #808495; font-size: 13px;">{info.get('sector', 'N/A')} | {info.get('industry', 'N/A')}</p>
                <hr style="border: 0.5px solid #2d3139;">
                <p style="font-size: 14px;"><b>PE Ratio:</b> {info.get('trailingPE', '-')}</p>
                <p style="font-size: 14px;"><b>52W High:</b> {info.get('fiftyTwoWeekHigh', '-'):,}</p>
                <p style="font-size: 14px;"><b>52W Low:</b> {info.get('fiftyTwoWeekLow', '-'):,}</p>
                <p style="font-size: 14px;"><b>Dividend:</b> {info.get('dividendYield', 0)*100:.2f}%</p>
            </div>
            """, unsafe_allow_html=True)
            
        st.write("") # 간격
        st.subheader("Status Check")
        # RSI를 이용한 직관적인 상태 게이지 대신 텍스트 알림
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rsi = 100 - (100 / (1 + (gain/loss))).iloc[-1]
        
        if rsi > 70: st.error(f"⚠️ OVERBOUGHT (RSI: {rsi:.1f})")
        elif rsi < 30: st.success(f"✅ OVERSOLD (RSI: {rsi:.1f})")
        else: st.info(f"⚖️ NEUTRAL (RSI: {rsi:.1f})")

except Exception as e:
    st.error(f"System Error: {e}")