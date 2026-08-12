"""1순위 · 발표·정책 브리핑."""

import streamlit as st

from app_pages.briefing import render
from charger_dashboard.sidebar import render_sidebar

render_sidebar()
st.title("정책 우선순위 브리핑")
st.caption("늘려야 하나 → 어디에 먼저 → 종합")
render()
