"""1순위 · 발표 브리핑."""

import streamlit as st

from app_pages.briefing import render
from charger_dashboard.sidebar import render_sidebar

render_sidebar()
st.markdown("## 공공급속 이용 부담과 배치 방향")
st.caption("시·도·연도·기간을 바꾸면 같은 그래프가 따라갑니다")
render()
