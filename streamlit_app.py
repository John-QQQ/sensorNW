import streamlit as st
import pandas as pd

# 제목 표시
st.title('센서 데이터 분석')

# 파일 업로드
uploaded_file = st.file_uploader("최신 현황 파일을 업로드하세요", type=["xlsx", "xls", "csv"])

# '최신파일로 사용하기' 버튼
use_latest_file = st.button('저장된 데이터로 분석하기')

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
