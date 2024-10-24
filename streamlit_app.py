import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium



# 제목 표시
st.title('센서 데이터 분석')

# 파일 업로드
uploaded_file = st.file_uploader("최신 현황 파일을 업로드하세요", type=["xlsx", "xls", "csv"])

# '최신파일로 사용하기' 버튼
use_latest_file = st.button('최신파일로 사용하기')

# 파일 처리
if uploaded_file is not None:
    try:
        # 업로드된 파일을 처리
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file, engine='openpyxl')
        
        st.subheader('업로드된 데이터')
        st.write(df)
    except Exception as e:
        st.error(f'파일 처리 중 오류 발생: {e}')
elif use_latest_file:
    try:
        # 미리 올려놓은 파일 'Sensor_data_1024.csv' 읽기
        df = pd.read_csv('Sensor_data_1024.csv')
        st.subheader('최신 파일 데이터')
        st.write(df)
    except Exception as e:
        st.error(f'최신 파일 불러오기 중 오류 발생: {e}')
else:
    st.info("엑셀 또는 CSV 파일을 업로드하거나 최신 파일을 사용하세요.")

# 지도에 사용할 색상 함수
def get_marker_color(status):
    if status == 'normal':
        return 'green'
    elif status == 'disc.':
        return 'red'
    else:
        return 'blue'  # 기타 상태에 대한 기본 색상

# 지도 시각화 버튼
if st.button('현황 지도 보기'):
    if '위도' in df.columns and '경도' in df.columns and '상태' in df.columns:
        # 센서 위치를 표시할 지도 생성
        m = folium.Map(location=[df['위도'].mean(), df['경도'].mean()], zoom_start=12)
        
        # 센서 데이터에 따라 마커 추가
        for idx, row in df.iterrows():
            folium.Marker(
                location=[row['위도'], row['경도']],
                popup=f"상태: {row['상태']}",
                icon=folium.Icon(color=get_marker_color(row['상태']))
            ).add_to(m)
        
        # 지도 표시
        st_data = st_folium(m, width=700, height=500)
    else:
        st.error("데이터에 '위도', '경도', '상태' 컬럼이 필요합니다.")
        