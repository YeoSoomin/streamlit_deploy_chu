import streamlit as st
import pandas as pd
import io
import warnings
import geopandas as gpd
import folium
import plotly.express as px
from streamlit_folium import folium_static

# 경고 메시지 숨기기
warnings.filterwarnings("ignore")

# 페이지 설정
st.set_page_config(
    page_title="자전거사고 EDA",
    page_icon="🚲",
    layout="wide"
)

# 제목
st.title("자전거사고 다발지역 데이터 EDA")
# 참고 문헌 링크 첨부
st.caption("출처(https://www.data.go.kr/data/15094182/fileData.do)")

# 파일 업로더 설정
file = st.file_uploader("📁 파일을 업로드 해주세요.", type=["csv"])

# 파일이 업로드 되었을 때 처리
if file is not None:
    st.write(f"{file.name} 파일이 업로드 되었습니다.")
    df = pd.read_csv(io.StringIO(file.getvalue().decode("utf-8")))
else:
    df = pd.read_csv("C:/streamlit32/streamlit_deploy_chu/files/도로교통공단_자전거사고 다발지역 개별사고 정보_20201231.csv", encoding="UTF-8")

# 발생일을 날짜형으로 변환
df["발생일"] = pd.to_datetime(df["발생일"])

# 발생일에서 연도를 추출하여 '연도' 컬럼을 추가
df["연도"] = df["발생일"].dt.year
del df[df.columns[19]]

# 시작일, 종료일 설정
col1, col2 = st.columns(2)
startDate = df["발생일"].min()
endDate = df["발생일"].max()

with col1:
    date1 = pd.to_datetime(st.date_input("시작일", startDate))

with col2:
    date2 = pd.to_datetime(st.date_input("종료일", endDate))

df = df[(df["발생일"] >= date1) & (df["발생일"] <= date2)].copy()

# 지도 시각화 데이터 전처리(csv)
df_map = df.copy()
df_map["연도"] = df_map["발생일"].dt.year
df_map["다발지시군구"] = df_map["다발지시군구"].str.split().str[0]
df_map["다발지시군구"] = df_map["다발지시군구"].str.replace(r'[^\w\s]', '', regex=True).str.strip()

# 지도 시각화 데이터 전처리(JGSON)
gdf_korea_si = gpd.read_file("C:/streamlit32/streamlit_deploy_chu/files/gdf_korea_sido_2022.json")
gdf_korea_si["다발지시군구"] = gdf_korea_si["CTP_KOR_NM"]

# 그래프 시각화 데이터 전처리(csv)
df["다발지시군구"] = df["다발지시군구"].str.split().str[0].str.replace(r'[^\w]', '', regex=True).str.strip()

# 연도별 빈도수 계산
map_counts = df_map.groupby("연도")["다발지시군구"].value_counts().reset_index(name="빈도수")

# 필터링 사이드바 설정
st.sidebar.header("데이터 필터:")

# 연도 선택
year = st.sidebar.multiselect("연도 선택(복수 가능)", df["연도"].unique())

# 연도 필터링
if not year:
    df_year = df.copy()
    map_counts_year = map_counts.copy()
else:
    df_year = df[df["연도"].isin(year)]
    map_counts_year = map_counts[map_counts["연도"].isin(year)]

# 다발지시군구 선택
region = st.sidebar.multiselect("행정구역 선택(복수 가능)", df_year["다발지시군구"].unique())

# 다발지시군구 필터링
if not region:
    df_region = df_year.copy()
    map_counts_region = map_counts_year.copy()
else:
    df_region = df_year[df_year["다발지시군구"].isin(region)]
    map_counts_region = map_counts_year[map_counts_year["다발지시군구"].isin(region)]

# 필터링된 데이터프레임 출력
filtered_df = df_region
filtered_map_counts = map_counts_region

col = st.columns((4.7, 2), gap='medium')

# 지도 시각화 함수
def make_folium_map(input_df, input_geojson, input_column, input_color_theme):
    # Folium map 객체 생성
    map_center = [36.34, 127.77]  # 대한민국 중심 좌표
    folium_map = folium.Map(location=map_center, zoom_start=6, tiles="cartodbpositron")

    # Folium 지도에 제목 추가
    title = "다발지시군구별 사고 빈도수"
    title_html = f'<h3 align="center" style="font-size:20px"><b>{title}</b></h3>'
    folium_map.get_root().html.add_child(folium.Element(title_html))

    # Choropleth 맵 추가
    geo_json_data = input_geojson.to_json()
    folium.Choropleth(
        geo_data=geo_json_data,
        data=input_df,
        columns=("다발지시군구", input_column),
        key_on="feature.properties.다발지시군구",
        fill_color="BuPu",
        fill_opacity=0.7,
        line_opacity=0.5,
        legend_name="사고 빈도수"
    ).add_to(folium_map)

    return folium_map

# 지도 시각화 출력 (Folium Map)
with col[0]:
    year_str = ", ".join(map(str, [int(y) for y in year]))  
    region_str = ", ".join(region)   
    st.markdown(f'#### {year_str} {region_str} 사고 다발 구역 자전거 사고 빈도수')
    folium_map = make_folium_map(filtered_map_counts, gdf_korea_si, "빈도수", "BuPu")
    folium_static(folium_map)

# 사고 빈도수
with col[1]:
    st.markdown('#### 사고 빈도수 상세')

    # 사고 빈도수를 기준으로 시도별로 데이터 정렬
    df_selected_year_sorted = filtered_map_counts.groupby("다발지시군구")["빈도수"].sum().reset_index()
    df_selected_year_sorted = df_selected_year_sorted.sort_values("빈도수", ascending=False)

    # 선택된 카테고리
    selected_category = "자전거 사고 빈도수"

    # 데이터프레임 출력
    st.dataframe(df_selected_year_sorted,
                 column_order=("다발지시군구", "빈도수"),
                 hide_index=True,
                 width=500,
                 column_config={
                     "다발지시군구": st.column_config.TextColumn(
                         "시도명",
                     ),
                     "빈도수": st.column_config.ProgressColumn(
                         str(selected_category),
                         format="%d",  # 정수형으로 포맷
                         min_value=0,
                         max_value=int(df_selected_year_sorted["빈도수"].max()),  # int로 변환
                     )})
 
# '발생일'에서 월을 추출하여 'month_year' 컬럼 추가
filtered_df["month_year"] = filtered_df["발생일"].dt.to_period("M")

# 연도와 지역을 기반으로 필터링
filtered_df_year_region = filtered_df[(filtered_df["연도"].isin(year)) & (filtered_df["다발지시군구"].isin(region))]

# 월별 빈도수 계산
linechart = filtered_df_year_region.groupby(
    filtered_df_year_region["month_year"].dt.strftime("%Y : %b")
)["다발지시군구"].count().reset_index(name="빈도수")

# 시계열 그래프 생성
fig2 = px.line(
    linechart, 
    x="month_year", y="빈도수", 
    labels={"빈도수": "사고 빈도수"},
    height=500, width=1000,
    template="gridon"
)

# 색상 그라디언트 적용
fig2.update_traces(line=dict(color='#4A76AF', width=2))  # 여기에서 색상 적용

# 그래프 출력
st.markdown("#### 시계열 분석")
st.plotly_chart(fig2, use_container_width=True)

# 데이터 보기
with st.expander("시계열 데이터 보기:"):
    st.dataframe(linechart)  # pandas 스타일링 없이 데이터만 출력
    csv = linechart.to_csv(index=False).encode("utf-8")
    st.download_button('Download Data', data=csv, file_name="TimeSeries.csv", mime="text/csv")

# 사고유형에서 앞부분만 선택 (ooo - ooo 형태에서 'ooo' 추출)
filtered_df["사고유형_간소화"] = filtered_df["사고유형"].str.split(" - ").str[0]

# 두 개의 컬럼 레이아웃 설정
chart1, chart2 = st.columns(2)

# 사고유형별 빈도수 원 그래프
with chart1:
    st.subheader("사고유형별 빈도")
    accident_type_counts = filtered_df["사고유형_간소화"].value_counts().reset_index()
    accident_type_counts.columns = ["사고유형", "빈도"]

    # Plotly 원 그래프 생성
    fig1 = px.pie(
        accident_type_counts, 
        values="빈도", 
        names="사고유형", 
        template="plotly_dark"
    )
    fig1.update_traces(
        text=accident_type_counts["사고유형"], 
        textposition="inside"
    )
    st.plotly_chart(fig1, use_container_width=True)

# 법규위반사항별 빈도수 원 그래프
with chart2:
    st.subheader("법규위반사항별 빈도")
    law_violation_counts = filtered_df["법규위반사항"].value_counts().reset_index()
    law_violation_counts.columns = ["법규위반사항", "빈도"]

    # Plotly 원 그래프 생성
    fig2 = px.pie(
        law_violation_counts, 
        values="빈도", 
        names="법규위반사항", 
        template="gridon"
    )
    fig2.update_traces(
        text=law_violation_counts["법규위반사항"], 
        textposition="inside"
    )
    st.plotly_chart(fig2, use_container_width=True)

# 가해자 성별 및 연령대 시각화
col1, col2 = st.columns(2)

# 가해자 성별 빈도수 막대 그래프
with col1:
    st.subheader("가해자 성별 및 연령대 분포 막대 그래프")

    # 가해자 성별 빈도 계산
    gender_counts = filtered_df["가해자성별"].value_counts().reset_index()
    gender_counts.columns = ["가해자성별", "명"]

    # Plotly 막대 그래프 생성
    fig1 = px.bar(
        gender_counts, 
        x="가해자성별", 
        y="명", 
        text="명",
        color="가해자성별",
        template="plotly_dark",
        title="가해자 성별 분포"
    )
    fig1.update_traces(texttemplate='%{text}', textposition='outside')
    st.plotly_chart(fig1, use_container_width=True)

# 가해자 연령대 분포 막대 그래프
with col2:
    st.subheader("😨")
    # '가해자연령'에서 '세' 문자 제거
    filtered_df["가해자연령"] = filtered_df["가해자연령"].str.replace(r'[^0-9]', '', regex=True)

    # 문자를 숫자로 변환 
    filtered_df["가해자연령"] = pd.to_numeric(filtered_df["가해자연령"], errors='coerce')

    # NaN 값은 제거
    filtered_df = filtered_df.dropna(subset=["가해자연령"])

    # 가해자 연령을 10년 단위로 구간화
    bins = [0, 9, 19, 29, 39, 49, 59, 69, 200]
    labels = ["0세~9세", "10세~19세", "20세~29세", "30세~39세", "40세~49세", "50세~59세", "60세~69세", "70세~"]
    filtered_df["가해자연령대"] = pd.cut(filtered_df["가해자연령"], bins=bins, labels=labels, right=True)

    # 가해자 연령대 분포 계산
    age_group_counts = filtered_df["가해자연령대"].value_counts().sort_index().reset_index()
    age_group_counts.columns = ["가해자연령대", "명"]

    # Plotly 막대 그래프 생성
    fig2 = px.bar(
        age_group_counts, 
        x="가해자연령대", 
        y="명", 
        text="명",
        color="가해자연령대",
        template="gridon",
        title="가해자 연령대 분포"
    )
    fig2.update_traces(texttemplate='%{text}', textposition='outside')
    st.plotly_chart(fig2, use_container_width=True)

# 피해자 성별 및 연령대 시각화
col1, col2 = st.columns(2)

# 피해자 성별 분포 막대 그래프
with col1:
    st.subheader("피해자 성별 및 연령대 막대 그래프")

    # 피해자 성별 빈도 계산
    gender_counts = filtered_df["피해자성별"].value_counts().reset_index()
    gender_counts.columns = ["피해자성별", "명"]

    # Plotly 막대 그래프 생성
    fig1 = px.bar(
        gender_counts, 
        x="피해자성별", 
        y="명", 
        text="명",
        color="피해자성별",
        template="plotly_dark",
        title="피해자 성별 분포"
    )
    fig1.update_traces(texttemplate='%{text}', textposition='outside')
    st.plotly_chart(fig1, use_container_width=True)

# 피해자 연령대 분포 막대 그래프
with col2:
    st.subheader("😢")
    # '피해자연령'에서 '세' 문자 제거
    filtered_df["피해자연령"] = filtered_df["피해자연령"].str.replace(r'[^0-9]', '', regex=True)

    # 문자를 숫자로 변환 
    filtered_df["피해자연령"] = pd.to_numeric(filtered_df["피해자연령"], errors='coerce')

    # NaN 값은 제거
    filtered_df = filtered_df.dropna(subset=["피해자연령"])

    # 피해자 연령을 10년 단위로 구간화
    bins = [0, 9, 19, 29, 39, 49, 59, 69, 200]
    labels = ["0세~9세", "10세~19세", "20세~29세", "30세~39세", "40세~49세", "50세~59세", "60세~69세", "70세~"]
    filtered_df["피해자연령대"] = pd.cut(filtered_df["피해자연령"], bins=bins, labels=labels, right=True)

    # 피해자 연령대 분포 계산
    age_group_counts = filtered_df["피해자연령대"].value_counts().sort_index().reset_index()
    age_group_counts.columns = ["피해자연령대", "명"]

    # Plotly 막대 그래프 생성
    fig2 = px.bar(
        age_group_counts, 
        x="피해자연령대", 
        y="명", 
        text="명",
        color="피해자연령대",
        template="gridon",
        title="피해자 연령대 분포"
    )
    fig2.update_traces(texttemplate='%{text}', textposition='outside')
    st.plotly_chart(fig2, use_container_width=True)

st.write("#### 데이터세트 상세")
st.write(filtered_df)
