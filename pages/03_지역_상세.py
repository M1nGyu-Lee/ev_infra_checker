"""1순위 · 지역 상세."""

import streamlit as st

from app_pages.region import render
from charger_dashboard.sidebar import render_sidebar

render_sidebar()
st.title("지역 상세")
render()
