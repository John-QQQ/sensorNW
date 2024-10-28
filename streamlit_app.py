import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
import h3
from openai import OpenAI
from docx import Document
from io import BytesIO

# 제목과 부제 추가
st.title("SKT MEMS센서 메타데이터 관리")
st.subheader("자연어 명령어를 통해 손쉽게 MEMS를 검색하세요")

# OpenAI API 키 설정
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# 지도에 사용할 색상 함수
def get_marker_color(status):
    if status == 'normal':
        return 'green'
    elif status == 'disc.':
        return 'red'
    else:
        return 'blue'

# H3 경계를 지도에 그리는 함수
def draw_h3_boundaries(map_object, boundary_coords, total_count, normal_count, disc_count):
    folium.PolyLine(boundary_coords, color="darkred", weight=4, opacity=0.8).add_to(map_object)
    lat_center = sum([lat for lat, lon in boundary_coords]) / len(boundary_coords)
    lon_center = sum([lon for lat, lon in boundary_coords]) / len(boundary_coords)
    main_label = f'{total_count}'
    sub_label = f'({normal_count} normal / {disc_count} disc.)'
    folium.Marker(
        location=[lat_center, lon_center],
        popup=f"센서 수: {main_label} {sub_label}",
        icon=folium.DivIcon(html=f"""
            <div style="text-align: center;">
                <span style="font-size: 14pt; font-weight: bold; color: darkblue">{main_label}</span>
                <span style="font-size: 10pt; color: darkblue">{sub_label}</span>
            </div>
        """)
    ).add_to(map_object)

# 'df'가 세션 상태에 없으면 None으로 초기화
if 'df' not in st.session_state:
    st.session_state.df = None

# 파일 업로드
uploaded_file = st.file_uploader("최신 현황 파일을 업로드하세요", type=["xlsx", "xls", "csv"])
if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.csv'):
            st.session_state.df = pd.read_csv(uploaded_file)
        else:
            st.session_state.df = pd.read_excel(uploaded_file, engine='openpyxl')
        st.subheader('업로드된 데이터')
        st.write(st.session_state.df)
    except Exception as e:
        st.error(f'파일 처리 중 오류 발생: {e}')

# '최신파일로 사용하기' 버튼
if st.button('최신파일로 사용하기'):
    try:
        st.write("최신 파일을 사용 중입니다.")
        st.session_state.df = pd.read_csv('Sensor_data_1024.csv')
        st.subheader('최신 파일 데이터')
        st.write(st.session_state.df.head())
    except Exception as e:
        st.error(f'최신 파일 불러오기 중 오류 발생: {e}')

# 현황 지도 보기 버튼
if st.session_state.df is not None:
    if st.button('현황 지도 보기'):
        if '위도' in st.session_state.df.columns and '경도' in st.session_state.df.columns and '연결상태' in st.session_state.df.columns:
            st.info("지도를 생성하고 있습니다...")

            try:
                # 지도 생성
                m = folium.Map(location=[st.session_state.df['위도'].mean(), st.session_state.df['경도'].mean()], zoom_start=12)

                # 마커 클러스터링 설정
                marker_cluster = MarkerCluster().add_to(m)

                # H3 인덱스별로 센서들을 클러스터링하기 위한 딕셔너리
                h3_dict = {}

                # 센서 데이터에 따라 H3 인덱스 계산 및 센서 개수 클러스터링
                for idx, row in st.session_state.df.iterrows():
                    lat, lon = row['위도'], row['경도']
                    h3_index = h3.latlng_to_cell(lat, lon, 5)
                    if h3_index not in h3_dict:
                        h3_dict[h3_index] = {
                            'total_count': 0,
                            'normal_count': 0,
                            'disc_count': 0,
                            'coords': h3.cell_to_boundary(h3_index)
                        }
                    h3_dict[h3_index]['total_count'] += 1
                    if row['연결상태'] == 'normal':
                        h3_dict[h3_index]['normal_count'] += 1
                    elif row['연결상태'] == 'disc.':
                        h3_dict[h3_index]['disc_count'] += 1

                    folium.Marker(
                        location=[lat, lon],
                        popup=f"연결상태: {row['연결상태']}",
                        icon=folium.Icon(color=get_marker_color(row['연결상태']))
                    ).add_to(marker_cluster)

                # H3 경계 및 센서 개수를 지도에 표시
                for h3_index, data in h3_dict.items():
                    boundary_coords = [(lat, lon) for lat, lon in data['coords']]
                    draw_h3_boundaries(
                        m,
                        boundary_coords,
                        data['total_count'],
                        data['normal_count'],
                        data['disc_count']
                    )

                # 지도를 HTML로 변환
                map_html = m._repr_html_()
                st.components.v1.html(map_html, width=700, height=500)
            except Exception as e:
                st.error(f"지도 생성 중 오류 발생: {e}")
        else:
            st.error("'위도', '경도', '연결상태' 컬럼이 데이터에 없습니다.")
else:
    st.info("데이터를 먼저 업로드하거나 최신 파일을 사용하세요.")

# 데이터 필터링을 위한 사용자 입력받기
st.subheader("데이터 필터링")

def generate_filter_condition(user_query, columns):
   try:
       response = client.chat.completions.create(
           model="gpt-3.5-turbo",
           messages=[
               {"role": "system", "content": "데이터프레임을 분석하여 필터링 조건을 생성하는 전문가입니다. 사용자의 명령어를 기반으로 조건을 만족하는 코드 구문을 생성하세요. 예를 들어, '경북 영덕군에 설치된 센서'라는 요청이 있으면 'df[df[\"설치지역\"] == \"경북 영덕군\"]' 형태로 반환하세요."},
               {"role": "user", "content": f"데이터프레임의 다음 컬럼으로 필터링할 조건을 만들어 주세요:\n\n{columns}\n\n사용자 요청: '{user_query}'\n\n주석이나 설명 없이 순수한 코드만 반환해 주세요."}
           ]
       )
       filter_code = response.choices[0].message.content.strip()
       filter_code_lines = filter_code.splitlines()
       executable_code = filter_code_lines[0].strip() if filter_code_lines else ""
       return executable_code
   except Exception as e:
       st.error(f"필터링 조건 생성 중 오류 발생: {e}")
       return None

# 데이터가 있는 경우에만 필터링 기능 실행
if st.session_state.df is not None:
    user_query = st.text_input("데이터 필터링을 위한 자연어 명령을 입력하세요")
    if user_query:
        filter_code = generate_filter_condition(user_query, st.session_state.df.columns.tolist())
        if filter_code:
            try:
                df = st.session_state.df
                filtered_df = eval(filter_code)
                st.subheader("필터링된 데이터")
                st.write(filtered_df)
                
               # 필터링된 데이터를 Word로 저장
                if st.button("필터링된 데이터를 MS Word로 저장"):
                    doc = Document()
                    doc.add_heading("필터링된 MEMS 센서 데이터", 0)
                    
                    # 예시 파일과 유사한 형식으로 데이터 추가
                    for _, row in filtered_df.iterrows():
                        doc.add_paragraph("단말번호: " + str(row.get("단말번호", "")))
                        doc.add_paragraph("관측소 코드: " + str(row.get("관측소 코드", "")))
                        doc.add_paragraph("시설구분: " + str(row.get("시설구분", "")))
                        doc.add_paragraph("시설구분세부: " + str(row.get("시설구분세부", "")))
                        doc.add_paragraph("제조사: " + str(row.get("제조사", "")))
                        doc.add_paragraph("설치시점: " + str(row.get("설치시점", "")))
                        doc.add_paragraph("연결상태: " + str(row.get("연결상태", "")))
                        doc.add_paragraph("주소: " + str(row.get("주소", "")))
                        doc.add_paragraph("위도: " + str(row.get("위도", "")))
                        doc.add_paragraph("경도: " + str(row.get("경도", "")))
                        doc.add_paragraph("고도: " + str(row.get("고도", "")))
                        doc.add_paragraph("설치층: " + str(row.get("설치층", "")))
                        doc.add_paragraph("전체층: " + str(row.get("전체층", "")))
                        doc.add_paragraph("축보정: " + str(row.get("축보정", "")))
                        doc.add_paragraph("H3 Cell: " + str(row.get("H3 Cell", "")))
                        doc.add_paragraph("센서 품질: " + str(row.get("센서 품질", "")))
                        doc.add_paragraph("통신 품질: " + str(row.get("통신 품질", "")))
                        doc.add_paragraph("H3혼잡여부: " + str(row.get("H3혼잡여부", "")))
                        doc.add_paragraph("센서 교체 필요 여부: " + str(row.get("센서 교체 필요 여부", "")))
                        doc.add_paragraph("통신 품질 안정 여부: " + str(row.get("통신 품질 안정 여부", "")))
                        doc.add_paragraph("현장 설치 사진: " + str(row.get("현장 설치 사진", "")))
                        doc.add_paragraph("\n" + "-"*40 + "\n")
                    
                    # 임시 버퍼에 저장
                    buffer = BytesIO()
                    doc.save(buffer)
                    buffer.seek(0)
                    
                    st.success("데이터가 MS Word 파일로 저장되었습니다.")
                    st.download_button("다운로드: 필터링된 데이터 Word 파일", data=buffer, file_name="filtered_sensor_data.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
                    
            except SyntaxError as se:
                st.error(f"구문 오류 발생: {se}")
            except Exception as e_eval:
                st.error(f"필터링 코드 실행 중 오류 발생: {e_eval}")
else:
    st.warning("데이터를 먼저 업로드해주세요.")
