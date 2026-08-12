"""3순위 · EV·충전소 총량."""

import streamlit as st

from app_pages.national_basics import render
from charger_dashboard.sidebar import render_sidebar

render_sidebar()
st.title("EV·충전소 총량")
render()
