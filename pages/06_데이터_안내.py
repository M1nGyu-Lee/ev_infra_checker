"""참고 · 데이터 안내."""

import streamlit as st

from app_pages.data_guide import render
from charger_dashboard.sidebar import render_sidebar

render_sidebar()
st.title("데이터 안내")
render()
