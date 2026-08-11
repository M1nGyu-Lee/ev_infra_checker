"""EV and Ministry of Environment public fast-charger dashboard."""

import streamlit as st

from charger_dashboard.data import SIDO_ORDER, available_years
from charger_dashboard.ui import inject_app_styles

st.set_page_config(
    page_title="공공 급속충전 인프라 분석",
    page_icon=":material/ev_station:",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_app_styles()

years = available_years()
if "selected_year" not in st.session_state:
    st.session_state.selected_year = 2025 if 2025 in years else years[-1]
if "selected_sido" not in st.session_state:
    st.session_state.selected_sido = "전국"

page = st.navigation(
    {
        "1순위 · 대국민": [
            st.Page(
                "app_pages/map.py",
                title="시·도 지도",
                icon=":material/map:",
                default=True,
            ),
            st.Page(
                "app_pages/trends.py",
                title="급속 이용 추이",
                icon=":material/trending_up:",
            ),
            st.Page(
                "app_pages/region.py",
                title="지역 상세",
                icon=":material/location_on:",
            ),
        ],
        "2순위 · 사업자": [
            st.Page(
                "app_pages/supply_strategy.py",
                title="급·완속 설치 판단",
                icon=":material/electrical_services:",
            ),
        ],
        "3순위 · 기초": [
            st.Page(
                "app_pages/national_basics.py",
                title="EV·충전소 총량",
                icon=":material/analytics:",
            ),
        ],
        "참고": [
            st.Page(
                "app_pages/data_guide.py",
                title="데이터 안내",
                icon=":material/menu_book:",
            ),
        ],
    },
    position="top",
)

with st.sidebar:
    st.markdown(
        '<div class="ev-sidebar-brand">EV Infra Checker</div>'
        '<div class="ev-sidebar-sub">공공급속 · 급·완속 보급 대시보드</div>',
        unsafe_allow_html=True,
    )
    st.markdown("##### 공통 필터")
    st.selectbox(
        "기준연도",
        years,
        key="selected_year",
        help="모든 페이지가 공유하는 기준연도입니다.",
    )
    st.selectbox(
        "기준지역",
        ["전국", *SIDO_ORDER],
        key="selected_sido",
        help="전국 또는 한 개 시·도를 선택합니다.",
    )
    st.divider()
    st.markdown("##### 발표 구성")
    st.markdown(
        """
        1. **대국민** — 지도 · 이용 추이  
        2. **사업자** — 급·완속 설치 힌트  
        3. **기초** — 전국 총량·기간 상태
        """
    )
    st.divider()
    st.caption("환경부 공공급속 · 17시·도")
    st.caption("충전량 관측 2019-01 ~ 2025-08")
    st.caption("차지인포 급·완속 · 8권역")

st.title(f"{page.icon} {page.title}")
page.run()
