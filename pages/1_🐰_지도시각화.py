import streamlit as st
import pandas as pd
import numpy as np

from time import sleep

st.set_page_config(
  page_icon="🐡",
  page_title="스트림릿 배포하기",
  layout="wide"
)

st.header("과제 3")
st.write("")
st.subheader("Choropleth 지도: 시군구별 출생률")
st.write("")

content01 = """
#### 1. 시군구별 출생률 데이터 전처리

- 중구, 동구 등과 같이 여러 시에 중복되는 이름을 가진 구는 시이름-구이름으로 기재되어있어 지도 데이터와 동일하게 바꾸는 작업이 필요하다.
    - 예) 대구-동구, 대전-동구

> 하지만 출생률 데이터를 수정하는 건 힘들거라 판단되어 대신 GeoJSON 파일 수정하였다.

- 서울특별시 25개 구의 출생률 데이터뿐만이 아니라 서울특별시의 출생률 또한 포함되어 있다.

> 서울특별시와 같이 여러 구로 구성된 시의 출생률 데이터는 필요 없어 제거하였다.
"""
st.markdown(content01, unsafe_allow_html=True)

@st.cache_data
def load_data():
    # CSV 파일 로드
    df_sigungu_cbr = pd.read_csv(
        "C:/chumin-quarto-32/chumin-quarto-32/data-visualization/연령별_출산율_및_합계출산율_행정구역별(시군구).csv",
        header=2,
        encoding='cp949'
    )
    # 필요한 열만 선택
    df_sigungu_cbr = df_sigungu_cbr[["전국", "0.721"]]
    df_sigungu_cbr.columns = ["행정구역", "출생률"]
    
    # 시 단위 데이터 제거
    si = [
        '서울특별시', '부산광역시', '대구광역시', '인천광역시', '광주광역시',
        '대전광역시', '울산광역시', '경기도', '강원특별자치도', '충청북도',
        '충청남도', '전라북도', '전라남도', '경상북도', '경상남도', '제주특별자치도'
    ]
    df_sigungu_cbr = df_sigungu_cbr[~df_sigungu_cbr['행정구역'].isin(si)]
    return df_sigungu_cbr

df_sigungu_cbr = load_data()
st.dataframe(df_sigungu_cbr)

content02 = """
#### 2. GeoJSON 파일 확인하기

- 출생률 데이터와 다르게 구 이름만 기재되어있다.
> 법정동 코드로 구별 가능하다.

- 이름이 중복되는 시/군/구가 존재한다. 
> 법정동 코드를 참고하여 중복되는 시/군/구는 시이름-구이름으로 바꾸어 행정구역 열에 저장하였다. 
"""
st.markdown(content02, unsafe_allow_html=True)

import geopandas as gpd
import streamlit as st

@st.cache_data
def load_geojson():
    # GeoJSON 파일 로드
    gdf_korea_sigungu = gpd.read_file("C:/chumin-quarto-32/chumin-quarto-32/data-visualization/대한민국시군구.json")
    return gdf_korea_sigungu

def update_region_names(gdf_korea_sigungu):
    # 중복된 시군구 이름 처리
    jungbok_counts = gdf_korea_sigungu['NAME'].value_counts()
    jungbok_names = jungbok_counts[jungbok_counts > 1].index

    gdf_korea_sigungu['행정구역'] = gdf_korea_sigungu['NAME']

    for name in jungbok_names:
        rows = gdf_korea_sigungu[gdf_korea_sigungu['NAME'] == name]
        for idx, row in rows.iterrows():
            bj_code = str(row['BJCD'])[:2]
            if bj_code == '29':
                region = '광주-'
            elif bj_code == '48':
                region = '경남-'
            elif bj_code == '41':
                region = '경기-'
            elif bj_code == '47':
                region = '경북-'
            elif bj_code == '51':
                region = '강원-'
            elif bj_code == '27':
                region = '대구-'
            elif bj_code == '30':
                region = '대전-'
            elif bj_code == '26':
                region = '부산-'
            elif bj_code == '11':
                region = '서울-'
            elif bj_code == '36':
                region = '세종-'
            elif bj_code == '31':
                region = '울산-'
            elif bj_code == '28':
                region = '인천-'
            elif bj_code == '46':
                region = '전남-'
            elif bj_code == '52':
                region = '전북-'
            elif bj_code == '50':
                region = '제주-'
            elif bj_code == '44':
                region = '충북-'
            elif bj_code == '42':
                region = '충남-'
            else:
                region = ''

            gdf_korea_sigungu.at[idx, '행정구역'] = region + row['NAME']
    return gdf_korea_sigungu

gdf_korea_sigungu = load_geojson()
gdf_korea_sigungu = update_region_names(gdf_korea_sigungu)
st.write(gdf_korea_sigungu[['NAME', 'BJCD', '행정구역']].head())

content03 = """
#### 3. 지도 시각화: 첫 번째 시도 
"""
st.markdown(content03, unsafe_allow_html=True)

import folium

zoong_shim = [36.34, 127.77]

def create_map(gdf_korea_sigungu, df_sigungu_cbr):
    sigungu_map = folium.Map(location=zoong_shim, zoom_start=6, tiles="cartodbpositron")

    # 지도 제목 추가
    title = "시군구별 출생률"
    title_html = f'<h3 align="center" style="font-size:20px"><b>{title}</b></h3>'
    sigungu_map.get_root().html.add_child(folium.Element(title_html))

    geo_json_data = gdf_korea_sigungu.to_json()

    # Choropleth 지도 생성
    folium.Choropleth(
        geo_data=geo_json_data,  
        data=df_sigungu_cbr,      
        columns=("행정구역", "출생률"), 
        key_on="feature.properties.행정구역", 
        fill_color="BuPu",        
        fill_opacity=0.7,         
        line_opacity=0.5,         
        legend_name="시군구별 출생률"  
    ).add_to(sigungu_map)

    return sigungu_map

sigungu_map = create_map(gdf_korea_sigungu, df_sigungu_cbr)

st.components.v1.html(sigungu_map._repr_html_(), height=600)

content04 ="""
-   지도에 새까맣게 나오는 시군구가 있다.

> `df_singungu_cbr` 과 `geo_json_sigungu` 의 행정구역 열에 서로 중복되지 않는 데이터가 존재하기 때문에 이런 현상이 발생했을거라 판단하였다.
"""
st.markdown(content04, unsafe_allow_html=True)

content05 = """
#### 4. 데이터 검토하고 수정하기
"""
st.markdown(content05, unsafe_allow_html=True)

not_jungbok1 = df_sigungu_cbr[~df_sigungu_cbr['행정구역'].isin(gdf_korea_sigungu['행정구역'])]
not_jungbok2 = gdf_korea_sigungu[~gdf_korea_sigungu['행정구역'].isin(df_sigungu_cbr['행정구역'])]

col1, col2 = st.columns(2)

with col1:
    st.write("###### 출생률 데이터")
    st.write(not_jungbok1["행정구역"])

with col2:
    st.write("##### GeoJSON 파일")
    st.write(not_jungbok2[["BJCD", "행정구역"]])

content06="""
-   강서구, 북구, 고성군과 같이 중복되는 이름이라고 해서 무조건 앞에 시 이름이 붙는 건 아니다.

> 해당 데이터를 찾아내어 앞 세글자를 삭제하는 수정과정을 거쳤다.

-   고성군은 충청남도가 아닌 경상남도와 강원도에 위치한다.

> 충남-고성군 데이터는 잘못된 데이터이기 때문에 강원-고성군으로 바꾸어주었다.

-   경상북도 포항시 북구가 GeoJSON 파일에는 경북-북구로 출생률 데이터에는 포항-북구로 기재되어있다.

> 경북-북구를 포항-북구로 경북-남구를 포항-남구로 바꾸어주었다.

-   GeoJSON 파일에는 창원시라고 기재되어있지만 출생률 데이터에는 통합창원시라고 기재되어있다.

> GeoJSON 파일을 수정하였다.
"""
st.markdown(content06, unsafe_allow_html=True)

def remove_specific_prefix(region):
    regions_to_remove_prefix = [
        '서울-강서구', '경남-고성군', '부산-남구', '부산-동구', 
        '부산-북구', '부산-서구', '서울-중구'
    ]
    
    if region in regions_to_remove_prefix:
        return region[3:] 
    
    return region

gdf_korea_sigungu['행정구역'] = gdf_korea_sigungu['행정구역'].apply(remove_specific_prefix)

gdf_korea_sigungu.loc[gdf_korea_sigungu['행정구역'] == '경북-북구', '행정구역'] = '포항-북구'

gdf_korea_sigungu.loc[gdf_korea_sigungu['행정구역'] == '경북-남구', '행정구역'] = '포항-남구'

gdf_korea_sigungu.loc[gdf_korea_sigungu['행정구역'] == '충남-고성군', '행정구역'] = '강원-고성군'

gdf_korea_sigungu.loc[gdf_korea_sigungu['행정구역'] == '창원시', '행정구역'] = '통합창원시'

content07="""
#### 5. 지도 시각화: 두 번째 시도
"""
st.markdown(content07, unsafe_allow_html=True)

# 대한민국 중심에 해당하는 좌표계를 지도 중심으로 설정 
zoong_shim = [36.34, 127.77]

# folium 지도 생성
sigungu_map = folium.Map(
    location=zoong_shim,
    zoom_start=6, 
    tiles="cartodbpositron"
)

title = "시군구별 출생률"
title_html = f'<h3 align="center" style="font-size:20px"><b>{title}</b></h3>'
sigungu_map.get_root().html.add_child(folium.Element(title_html))

df_sigungu_cbr["행정구역"] = df_sigungu_cbr["행정구역"].str.strip()
geo_json_data = gdf_korea_sigungu.to_json()

folium.Choropleth(
    geo_data=geo_json_data,  
    data=df_sigungu_cbr,      
    columns=("행정구역", "출생률"), 
    key_on="feature.properties.행정구역",  
    fill_color="BuPu",  
    fill_opacity=0.7,   
    line_opacity=0.5,   
    legend_name="시군구별 출생률"  
).add_to(sigungu_map)

from streamlit.components.v1 import html
map_html = sigungu_map._repr_html_()
html(map_html, height=600)

