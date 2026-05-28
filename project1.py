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

# 1. 환경 설정
load_dotenv()
EXCHANGE_RATE_KEY = os.getenv("EXCHANGE_RATE_KEY") # 발급받으신 API 키를 .env에 넣어주세요.

st.set_page_config(layout="wide", page_title="Trade Analytics Terminal")

# 디자인 스타일링
st.markdown("""
    <style>
    .main-header {
        font-size: 28px; font-weight: 800; color: #ffcc00;
        padding: 10px; border-bottom: 2px solid #333; margin-bottom: 20px;
    }
    .metric-container {
        background-color: #1e1e1e; padding: 15px; border-radius: 10px;
    }
    </style>
    <div class="main-header"> 원자재-환율-관련주 상관관계 분석기</div>
    """, unsafe_allow_html=True)

# 2. 사이드바 제어판
with st.sidebar:
    st.header("🔍 분석 설정")
    
    # 분석 대상 설정
    asset_map = {
        "구리 (Copper)": {"ticker": "HG=F", "stock": "012330"}, # 현대모비스, 풍산 등
        "원유 (WTI)": {"ticker": "CL=F", "stock": "010950"}, # S-Oil, 한국석유 등
        "철강 (Steel)": {"ticker": "STRE", "stock": "004020"}, # 현대제철, POSCO홀딩스 등
        "천연가스": {"ticker": "NG=F", "stock": "036460"} # 한국가스공사
    }
    
    selected_asset = st.selectbox("원자재 선택", list(asset_map.keys()))
    related_stock = st.text_input("관련주 코드 (KOSPI)", value=asset_map[selected_asset]["stock"])
    
    currency_pair = st.selectbox("환율 기준", ["USD/KRW", "EUR/KRW", "JPY/KRW"])
    days = st.slider("분석 기간 (일)", 30, 730, 365)
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

# 3. 데이터 로딩 함수
@st.cache_data
def get_data(commodity_ticker, stock_ticker, start):
    # 원자재 데이터 (yfinance)
    commodity = yf.download(commodity_ticker, start=start)['Close']
    # 주가 데이터 (FinanceDataReader)
    stock = fdr.DataReader(stock_ticker, start=start)['Close']
    return commodity, stock

def get_exchange_rate(pair):
    # ExchangeRate-API 사용 예시 (기존에 사용하셨던 API 구조에 맞춤)
    base_currency = pair.split('/')[0]
    target_currency = pair.split('/')[1]
    url = f"https://v6.exchangerate-api.com/v6/{EXCHANGE_RATE_KEY}/pair/{base_currency}/{target_currency}"
    res = requests.get(url).json()
    return res.get('conversion_rate', 0)

# 4. 메인 분석 로직
try:
    with st.spinner('데이터를 통합 분석 중입니다...'):
        commodity_data, stock_data = get_data(asset_map[selected_asset]["ticker"], related_stock, start_date)
        current_rate = get_exchange_rate(currency_pair)

    # 1. 상단 핵심 지표 수정
    col1, col2, col3 = st.columns(3)
    with col1:
        # 시리즈의 마지막 값을 스칼라(숫자)로 변환하여 출력
        val_comm = float(commodity_data['Close'].iloc[-1])
        st.metric(f"현재 {selected_asset} 가격", f"{val_comm:,.2f}")
    with col2:
        st.metric(f"현재 {currency_pair} 환율", f"{current_rate:,.2f}")
    with col3:
        val_stock = float(stock_data['Close'].iloc[-1])
        st.metric("관련주 종가", f"{val_stock:,.0f}원")

    # 2. 상관관계 계산 부분 수정 (정확한 매칭을 위해 인덱스 기준 병합)
    st.subheader("시계열 상관관계 추이")
    
    # 두 시리즈를 하나의 데이터프레임으로 합쳐서 계산
    combined_df = pd.concat([commodity_data, stock_data], axis=1).dropna()
    combined_df.columns = ['Comm', 'Stock']
    
    # 상관계수 추출
    corr_value = combined_df['Comm'].corr(combined_df['Stock'])

    # ... (Plotly 그래프 부분은 동일) ...

    # 3. 인사이트 섹션 수정
    st.markdown("---")
    st.subheader("💡 무역 실무 전략 분석")
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.info(f"**상관관계 지수:** {corr_value:.2f}")
        # 상관관계 해석 로직
        if corr_value > 0.5:
            st.write("✅ 원자재 가격 상승 시 주가도 함께 상승하는 경향이 강합니다.")
        elif corr_value < -0.5:
            st.write("⚠️ 원자재 가격 상승이 기업 수익성에 부담을 주는 구조입니다.")
        else:
            st.write("⚖️ 현재 원자재가와 주가 간의 뚜렷한 동조화 현상은 보이지 않습니다.")

    with col_b:
        st.warning("**무역 전략 가이드**")
        if current_rate > 1350: # 예시 기준선
            st.write("- 현재 환율이 매우 높습니다. 수입 원재료 비중이 높은 경우 수익성 악화가 우려됩니다.")
        else:
            st.write("- 환율이 비교적 안정적입니다. 원자재 하락 시점이 매수 타이밍이 될 수 있습니다.")

except Exception as e:
    st.error(f"데이터 로드 중 오류 발생: {e}")
    st.info("사이드바에서 정확한 종목 코드와 API 키 설정을 확인해주세요.")