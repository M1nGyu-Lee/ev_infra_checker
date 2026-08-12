"""1순위 · 급속 이용 추이."""

import streamlit as st

from app_pages.trends import render
from charger_dashboard.sidebar import render_sidebar

render_sidebar()
st.title("급속 이용 추이")
render()
