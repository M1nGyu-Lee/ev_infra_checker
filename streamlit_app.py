"""홈(시작) 화면. 실제 분석 페이지는 pages/ 폴더에 있습니다."""

import streamlit as st

from charger_dashboard.sidebar import render_sidebar
from charger_dashboard.ui import inject_app_styles

# 앱 전체 설정은 홈(진입 파일)에서 한 번만
st.set_page_config(
    page_title="공공 급속충전 인프라 분석",
    page_icon=":material/ev_station:",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_app_styles()  # 지금은 비어 있음(기본 테마 사용)
render_sidebar()

st.title("공공 급속충전 인프라 분석")
st.markdown(
    """
    왼쪽(또는 위) **페이지 목록**에서 화면을 고르세요.

    | 구분 | 페이지 |
    |---|---|
    | 1순위 · 대국민 | 시·도 지도 · 급속 이용 추이 · 지역 상세 |
    | 2순위 · 사업자 | 급·완속 설치 판단 |
    | 3순위 · 기초 | EV·충전소 총량 |
    | 참고 | 데이터 안내 |

    > 예전 `st.navigation` / `st.Page` 방식은 주석 처리했습니다.
    > Streamlit이 `pages/` 폴더 파일을 자동으로 메뉴에 넣는 방식입니다.
    """
)

# [고급 · 주석 처리] st.navigation + st.Page 로 메뉴를 직접 구성하던 코드
# page = st.navigation({ "1순위": [st.Page("app_pages/map.py", ...)], ... })
# page.run()
