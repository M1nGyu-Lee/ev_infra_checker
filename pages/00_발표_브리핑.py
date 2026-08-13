"""1순위 · 발표 브리핑."""

import streamlit as st

from app_pages.briefing import render
from charger_dashboard.sidebar import render_sidebar

render_sidebar()
st.markdown("## 발표 브리핑")
st.caption("위에서 그래프를 고르고, 각 그래프 안에서 시·도와 연도를 바꿉니다.")
render()
