"""홈(시작) 화면. 실제 분석 페이지는 pages/ 폴더에 있습니다."""

import streamlit as st

from charger_dashboard.sidebar import render_sidebar
from charger_dashboard.ui import inject_app_styles

st.set_page_config(
    page_title="공공 급속충전 인프라 분석",
    page_icon=":material/ev_station:",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_app_styles()
render_sidebar()

st.markdown(
    """
    <div class="ev-hero">
      <h1>공공 급속충전 인프라 분석</h1>
      <p>환경부 공공급속 · 국토부 EV · 차지인포 급·완속을 시·도·권역으로 비교하는 대시보드입니다.
      왼쪽 메뉴에서 화면을 고른 뒤, 연도·스냅샷·시·도 필터를 먼저 맞추세요.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(
        """
        <div class="ev-home-card">
          <div class="rank">1순위 · 대국민</div>
          <h3>시·도 지도</h3>
          <p>이용·공급 부담을 지도와 순위로 한눈에 비교합니다.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
with c2:
    st.markdown(
        """
        <div class="ev-home-card">
          <div class="rank">1순위 · 대국민</div>
          <h3>급속 이용 추이</h3>
          <p>전국·시·도 월별 충전량·활성기 변화를 봅니다.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
with c3:
    st.markdown(
        """
        <div class="ev-home-card">
          <div class="rank">2순위 · 사업자</div>
          <h3>급·완속 설치 판단</h3>
          <p>차지인포 8권역 사분면·급속 비중으로 설치 힌트를 줍니다.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
with c4:
    st.markdown(
        """
        <div class="ev-home-card">
          <div class="rank">참고</div>
          <h3>데이터 안내</h3>
          <p>파일 계층·지표 정의·예측 방법론·해석 한계를 정리합니다.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("")
st.caption(
    "분석 단위는 시·도×연·월 집계입니다. 상대 비교이며 절대 부족 판정이 아닙니다. "
    "2025년 충전량은 1–8월(YTD) 기준으로 읽으세요."
)
