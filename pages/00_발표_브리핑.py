"""1순위 · 발표·정책 브리핑."""

import streamlit as st

from app_pages.briefing import render
from charger_dashboard.sidebar import render_sidebar

render_sidebar()
st.title("발표·정책 브리핑")
render()
