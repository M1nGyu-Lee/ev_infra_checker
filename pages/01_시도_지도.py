"""1순위 · 시·도 지도."""

import streamlit as st

from app_pages.map import render
from charger_dashboard.sidebar import render_sidebar

render_sidebar()
st.title("시·도 지도")
render()
