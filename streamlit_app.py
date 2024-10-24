import streamlit as st
import pandas as pd

# 제목 표시
st.title('센서 데이터 분석')

# 파일 업로드
uploaded_file = st.file_uploader("최신 현황 파일을 업로드하세요", type=["xlsx", "xls"])

# '최신파일로 사용하기' 버튼
use_latest_file = st.button('최근 저장된 데이터로 사용하기')

# 파일 처리
if uploaded_file is not None:
    try:
        # 사용자가 업로드한 파일을 Pandas로 읽기
        df = pd.read_excel(uploaded_file, engine='openpyxl')
        st.subheader('업로드된 데이터')
        st.write(df)
    except Exception as e:
        st.error(f'오류 발생: {e}')
elif use_latest_file:
    try:
        # 미리 올려놓은 파일 'Sensor_data_1024.xlsx' 읽기
        df = pd.read_excel('Sensor_data_1024.xlsx', engine='openpyxl')
        st.subheader('최신 파일 데이터')
        st.write(df)
    except Exception as e:
        st.error(f'오류 발생: {e}')
else:
    st.info("엑셀 파일을 업로드하거나 최신 파일을 사용하세요.")
