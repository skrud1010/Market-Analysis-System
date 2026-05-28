import streamlit as st
import pandas as pd
import requests
import yfinance as yf
import matplotlib.pyplot as plt
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
# ---------------------------
# Streamlit 기본 설정
# ---------------------------
st.set_page_config(
    page_title="외환보유고 & 거시경제 대시보드",
    layout="wide"
)

st.title("📊 외환 보유고 및 거시 경제 지표 대시보드")
st.caption("공식 기관 데이터 기반 거시경제 & 주식시장 연계 분석")

# ---------------------------
# 1. 한국은행 ECOS API 설정
# ---------------------------
ECOS_API_KEY = "ECOS_API_KEY"  # ← 반드시 발급 필요 (한국은행 공식)
BASE_URL = "https://ecos.bok.or.kr/api"

# ---------------------------
# 2. 한국은행 API 함수
# ---------------------------
@st.cache_data(ttl=86400)
def get_ecos_data(stat_code, item_code, start, end):
    url = f"{BASE_URL}/StatisticSearch/{ECOS_API_KEY}/json/kr/1/1000/{stat_code}/M/{start}/{end}/{item_code}"
    res = requests.get(url)
    data = res.json()

    # ❗ 오류 응답 처리
    if "StatisticSearch" not in data:
        st.error("한국은행 ECOS API 응답 오류")
        st.json(data)  # 실제 응답 구조 확인용
        return pd.DataFrame(columns=["TIME", "DATA_VALUE"])

    rows = data["StatisticSearch"]["row"]
    df = pd.DataFrame(rows)

    df["TIME"] = pd.to_datetime(df["TIME"], format="%Y%m")
    df["DATA_VALUE"] = pd.to_numeric(df["DATA_VALUE"])

    return df[["TIME", "DATA_VALUE"]]


# ---------------------------
# 3. 외환보유액 / 기준금리
# ---------------------------
with st.spinner("한국은행 데이터 불러오는 중..."):
    fx_reserve = get_ecos_data(
        stat_code="722Y001",      # 외환보유액
        item_code="010000",
        start="201801",
        end="202412"
    )

    interest_rate = get_ecos_data(
        stat_code="722Y001",      # 기준금리 (예시 코드)
        item_code="020000",
        start="201801",
        end="202412"
    )

# ---------------------------
# 4. KOSPI 지수 (yfinance)
# ---------------------------
@st.cache_data
def get_kospi():
    kospi = yf.download("^KS11", start="2018-01-01")
    kospi = kospi.reset_index()
    return kospi[["Date", "Close"]]

kospi_df = get_kospi()

# ---------------------------
# 5. 환율 API (이미 있다고 가정)
# ---------------------------
def get_exchange_rate():
    """
    실제 사용하는 환율 API로 교체하세요.
    """
    # TODO: 실제 API 연동
    # return 1385.23
    return 1420.50  # 임계치 테스트용

usd_krw = get_exchange_rate()

# ---------------------------
# 6. 알림 로직
# ---------------------------
ALERT_THRESHOLD = 1400

if usd_krw >= ALERT_THRESHOLD:
    st.error(
        f"🚨 환율 경고: USD/KRW {usd_krw}원\n"
        "➡ 주식 비중 축소 또는 현금·달러 비중 확대 고려"
    )
else:
    st.success(
        f"✅ 환율 안정: USD/KRW {usd_krw}원"
    )

# ---------------------------
# 7. 시각화
# ---------------------------
st.subheader("📈 거시 지표 vs 주식시장")

fig, ax1 = plt.subplots(figsize=(12, 6))

ax1.plot(fx_reserve["TIME"], fx_reserve["DATA_VALUE"], label="외환보유액", linewidth=2)
ax1.set_ylabel("외환보유액 (백만 달러)")
ax1.legend(loc="upper left")

ax2 = ax1.twinx()
ax2.plot(kospi_df["Date"], kospi_df["Close"], color="orange", label="KOSPI")
ax2.set_ylabel("KOSPI 지수")
ax2.legend(loc="upper right")

st.pyplot(fig)

# ---------------------------
# 8. 데이터 테이블
# ---------------------------
with st.expander("📄 원본 데이터 보기"):
    st.write("외환보유액")
    st.dataframe(fx_reserve.tail())

    st.write("기준금리")
    st.dataframe(interest_rate.tail())

    st.write("KOSPI")
    st.dataframe(kospi_df.tail())
