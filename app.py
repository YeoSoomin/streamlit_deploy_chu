import streamlit as st
import pandas as pd
import numpy as np

from time import sleep

st.set_page_config(
  page_icon="🐡",
  page_title="스트림릿 배포하기",
  layout="wide"
)

st.header("현재 시각은")
st.subheader("과제 제출 10시간 전")