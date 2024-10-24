import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
import h3  # 최신 h3 라이브러리

# 지도에 사용할 색상 함수
def get_marker_color(status):
    if status == 'normal':
        return 'green'
    elif status == 'disc.':
        return 'red'
    else:
        return 'blue'  # 기타 상태에 대한 기본 색상

# H3 경계를 지도에 그리는 함수 (총센서수와 연결상태별로 표시)
def draw_h3_boundaries(map_object, boundary_coords, total_count, normal_count, disc_count):
    # 경계를 더 두껍고 짙게 그리기
    folium.PolyLine(boundary_coords, color="darkred", weight=4, opacity=0.8).add_to(map_object)
    # H3 경계 중심에 센서 개수를 굵고 크게 표시
    lat_center = sum([lat for lat, lon in boundary_coords]) / len(boundary_coords)
    lon_center = sum([lon for lat, lon in boundary_coords]) / len(boundary_coords)
    label = f'{total_count} ({normal_count} normal / {disc_count} disc.)'
    folium.Marker(
        location=[lat_center, lon_center],
        popup=f"센서 수: {label}",
        icon=folium.DivIcon(html=f'<div style="font-size: 14pt; font-weight: bold; color: darkblue">{label}</div>')
    ).add_to(map_object)

# 'df'가 세션 상태에 없으면 None으로 초기화
if 'df' not in st.session_state:
    st.session_state.df = None

# 파일 업로드
uploaded_file = st.file_uploader("최신 현황 파일을 업로드하세요", type=["xlsx", "xls", "csv"])

# 파일이 업로드되면 처리 후 세션 상태에 저장
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

# '최신파일로 사용하기' 버튼 클릭 시 'Sensor_data_1024.csv' 파일 로드
if st.button('최신파일로 사용하기'):
    try:
        st.write("최신 파일을 사용 중입니다.")
        st.session_state.df = pd.read_csv('Sensor_data_1024.csv')
        st.subheader('최신 파일 데이터')
        st.write(st.session_state.df.head())
    except Exception as e:
        st.error(f'최신 파일 불러오기 중 오류 발생: {e}')

# 지도 시각화 버튼
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
                    # H3 인덱스 계산
                    h3_index = h3.latlng_to_cell(lat, lon, 5)  # 해상도 5 사용
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

                    # 각 센서 설치 위치에 마커 추가 (클러스터링)
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

                # Streamlit에서 HTML을 사용하여 지도 표시
                st.components.v1.html(map_html, width=700, height=500)
            except Exception as e:
                st.error(f"지도 생성 중 오류 발생: {e}")
        else:
            st.error("'위도', '경도', '연결상태' 컬럼이 데이터에 없습니다.")
else:
    st.info("데이터를 먼저 업로드하거나 최신 파일을 사용하세요.")
