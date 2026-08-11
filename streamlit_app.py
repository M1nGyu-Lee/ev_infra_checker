"""EV and Ministry of Environment public fast-charger dashboard."""

import streamlit as st

from charger_dashboard.data import available_years
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
    st.markdown("##### 이 앱에서 보는 것")
    st.markdown(
        """
        - **지도** — 시·도 이용·공급 부담  
        - **추이** — 공공급속 이용 변화  
        - **설치 판단** — 급·완속 사분면 힌트  
        - **총량** — 전국 규모·기간 상태
        """
    )
    st.divider()
    st.markdown("##### 데이터 범위")
    st.caption("환경부 공공급속 · 17시·도")
    st.caption("충전량 관측 2019-01부터 2025-08까지")
    st.caption("차지인포 급·완속 · 8권역(시·도 혼합)")
    st.divider()
    st.markdown("##### 읽기 팁")
    st.caption("각 페이지 안의 연도·스냅샷·시·도 필터를 먼저 맞춘 뒤 그래프를 비교하세요.")
    st.caption("상대 비교이며 절대 부족 판정이 아닙니다.")

st.title(f"{page.icon} {page.title}")
page.run()
