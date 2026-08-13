"""1순위 · 발표 브리핑."""

import streamlit as st

from app_pages.briefing import render
from charger_dashboard.sidebar import render_sidebar

render_sidebar()
st.markdown("## 공공급속, 어디에 먼저")
st.caption("발표 시연 · 환경부 공공급속 · 국토부 EV · 연도·지표를 바꿔 같은 지도를 다시 봅니다")
render()
