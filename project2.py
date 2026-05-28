import streamlit as st
import yfinance as yf
import requests
import os
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()
EXCHANGE_RATE_KEY = os.getenv("EXCHANGE_RATE_KEY")

# 페이지 설정
st.set_page_config(layout="wide", page_title="Professional Import Simulator")

# 전문가용 다크 테마 UI 적용
st.markdown("""
    <style>
    /* 메인 배경 및 폰트 설정 */
    .stApp {
        background-color: #0e1117;
        color: #e0e0e0;
    }
    /* 요청하신 제목 색상 수정 (White) */
    .main-header {
        font-size: 32px;
        font-weight: 800;
        color: #ffffff; /* 제목 색상 화이트 */
        text-align: left;
        padding-bottom: 15px;
        border-bottom: 2px solid #3e444e;
        margin-bottom: 30px;
    }
    /* 결과 카드 디자인 */
    .cost-card {
        background-color: #161b22;
        padding: 25px;
        border-radius: 12px;
        border: 1px solid #30363d;
        box-shadow: 0 10px 20px rgba(0,0,0,0.3);
    }
    /* 하이라이트 텍스트 */
    .highlight {
        color: #58a6ff;
        font-weight: bold;
    }
    /* 표 스타일 조정 */
    .stTable {
        background-color: #161b22;
        border-radius: 8px;
    }
    </style>
    <div class="main-header">🚢 IMPORT COST ANALYSIS TERMINAL</div>
    """, unsafe_allow_html=True)

# 품목별 관세율 데이터 (Dictionary)
category_map = {
    "IT/전자기기 (노트북, 폰)": {"duty": 0.0, "tax": 0.1},
    "의류/패션 (일반)": {"duty": 0.13, "tax": 0.1},
    "신발/가방": {"duty": 0.08, "tax": 0.1},
    "가공식품": {"duty": 0.30, "tax": 0.1},
    "직접 설정": {"duty": 0.0, "tax": 0.1}
}

# 사이드바 제어판
with st.sidebar:
    st.markdown("### 🛠️ 시뮬레이션 설정")
    use_yf = st.checkbox("해외 주가/상품 인덱스 연동", value=False)
    
    if use_yf:
        ticker = st.text_input("Ticker 입력", "AAPL")
        price_val = yf.Ticker(ticker).history(period="1d")['Close'].iloc[-1]
        st.caption(f"최신가: ${price_val:,.2f}")
    else:
        price_val = st.number_input("물품 단가 (USD)", value=1200.0)

    category = st.selectbox("수입 품목 분류", list(category_map.keys()))
    duty_rate = st.number_input("관세율 적용", value=category_map[category]["duty"]) if category == "직접 설정" else category_map[category]["duty"]
    
    ship_fee = st.number_input("국제 운송비 (USD)", value=45.0)

# 데이터 처리 및 계산
def fetch_rate():
    url = f"https://v6.exchangerate-api.com/v6/{EXCHANGE_RATE_KEY}/latest/USD"
    return requests.get(url).json().get('conversion_rates', {}).get('KRW', 1350.0)

try:
    ex_rate = fetch_rate()
    
    # 관세 계산의 정석: CIF 기준 (Cost, Insurance and Freight)
    cif_usd = price_val + ship_fee
    cif_krw = cif_usd * ex_rate
    
    amt_duty = cif_krw * duty_rate
    amt_vat = (cif_krw + amt_duty) * 0.1
    final_cost = cif_krw + amt_duty + amt_vat

    # 메인 레이아웃 구성
    col_left, col_right = st.columns([6, 4])

    with col_left:
        st.subheader("📋 상세 비용 명세")
        
        # 분석표 생성
        data = {
            "항목": ["물품 가격 (USD)", "국제 운송비 (USD)", "환율 (USD/KRW)", "수입 관세", "수입 부가세"],
            "상세 내역": [f"${price_val:,.2f}", f"${ship_fee:,.2f}", f"{ex_rate:,.2f}원", f"{duty_rate*100}%", "10%"],
            "금액(KRW)": [
                f"{price_val * ex_rate:,.0f}원",
                f"{ship_fee * ex_rate:,.0f}원",
                f"{ex_rate:,.2f}원",
                f"{amt_duty:,.0f}원",
                f"{amt_vat:,.0f}원"
            ]
        }
        st.table(pd.DataFrame(data))

        # 시각적 피드백
        st.markdown(f"**현재 시장 분석:** 환율이 1,350원 이상인 경우 수입 원가가 급격히 상승합니다. 현재 환율은 <span class='highlight'>{ex_rate:,.2f}원</span>입니다.", unsafe_allow_html=True)

    with col_right:
        st.subheader("💰 최종 수입 예상액")
        st.markdown(f"""
        <div class="cost-card">
            <p style="color: #8b949e; margin-bottom: 5px;">Total Estimated Cost</p>
            <h1 style="color: #58a6ff; margin-top: 0; font-size: 42px;">{final_cost:,.0f} 원</h1>
            <hr style="border-color: #30363d;">
            <div style="display: flex; justify-content: space-between;">
                <span>물품 원가(비중)</span>
                <span>{((cif_krw)/final_cost)*100:.1f}%</span>
            </div>
            <div style="display: flex; justify-content: space-between; color: #ff7b72;">
                <span>세금 합계(관세+부가세)</span>
                <span>{(amt_duty + amt_vat):,.0f}원</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # 도우미 차트
        st.write("")
        cost_breakdown = pd.Series({"원가": cif_krw, "관세": amt_duty, "부가세": amt_vat})
        st.bar_chart(cost_breakdown)

except Exception as e:
    st.error(f"데이터 연결 오류: {e}")