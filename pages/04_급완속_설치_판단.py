"""2순위 · 급·완속 설치 판단."""

import streamlit as st

from app_pages.supply_strategy import render
from charger_dashboard.sidebar import render_sidebar

render_sidebar()
st.title("급·완속 설치 판단")
render()
