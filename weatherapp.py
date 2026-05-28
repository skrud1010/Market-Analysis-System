import streamlit as st
import requests
from dotenv import load_dotenv
from openai import OpenAI
import os
import pandas as pd
import FinanceDataReader as fdr
df_krx = fdr.StockListing('KRX') # 코스피, 코스닥, 코넥스 전체 리스트

# 환경변수 로드
load_dotenv()
openai_key = os.getenv("open_api_key")
weather_key = os.getenv("weather_api_key")

client = OpenAI(api_key=openai_key)


#CSS 스타일 정의(사용자 정의 스타일 적용)
# custom_style=f""
#     <style>
#     <

def get_weekly_weather(city):
    # 5일/3시간 간격 예보 API (무료 플랜 기준)
    url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={weather_key}&units=metric&lang=kr"
    response = requests.get(url).json()
    return response

# st.markdown('<span class ="main-header"')
st.title("📅 주간 날씨 & 스타일 가이드")

city = st.text_input("도시를 입력하세요", "Seoul")

if st.button("일주일 날씨와 코디 확인하기"):
    data = get_weekly_weather(city)
    
    if data.get("list"):
        st.subheader(f"✨ {city}의 향후 날씨 예보")
        
        # 데이터 처리를 위한 리스트
        daily_data = []
        
        # 3시간 간격 데이터 중 매일 정오(12:00) 데이터만 추출 (약 5일치)
        for forecast in data['list']:
            if "12:00:00" in forecast['dt_txt']:
                date = forecast['dt_txt'].split(" ")[0]
                temp = forecast['main']['temp']
                desc = forecast['weather'][0]['description']
                daily_data.append({"날짜": date, "기온(°C)": temp, "상태": desc})
        
        # 1. 예보 표 출력
        df = pd.DataFrame(daily_data)
        st.table(df)

        # 2. GPT 코디 추천 (데이터가 많으므로 요약 요청)
        weather_summary = "\n".join([f"{d['날짜']}: {d['기온(°C)']}도, {d['상태']}" for d in daily_data])
        
        prompt = f"""
        다음은 {city}의 향후 며칠간 날짜별 날씨 정보입니다:
        {weather_summary}
        
        위 날씨 정보를 바탕으로 각 날짜별로 적절한 '의상 코디'를 추천해줘. 
        분석가처럼 깔끔하게 리스트 형태로 출력해주고, 전체적인 주간 패션 팁도 한 줄 덧붙여줘.
        """
        
        with st.spinner("GPT가 주간 코디를 분석 중입니다..."):
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}]
            )
            st.markdown("---")
            st.markdown("### 👔 날짜별 추천 코디")
            st.write(response.choices[0].message.content)
            
    else:
        st.error("데이터를 가져오지 못했습니다. 도시 영문명을 확인해 주세요.")