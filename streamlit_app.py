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
      <p>환경부 공공급속 · 국토부 EV · 환경부 급·완속 현황을 시·도·권역으로 비교하는 대시보드입니다.
      <strong>발표·정책 브리핑</strong>에서 스토리를 본 뒤, 필요하면 탐색 화면으로 들어가세요.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(
        """
        <div class="ev-home-card">
          <div class="rank">1순위 · 정책</div>
          <h3>발표·정책 브리핑</h3>
          <p>결론 → 정의 → 전국 신호 → 지역 후보 → 주의사항 순으로 읽습니다.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
with c2:
    st.markdown(
        """
        <div class="ev-home-card">
          <div class="rank">탐색</div>
          <h3>지도 · 추이 · 지역</h3>
          <p>필터로 시·도·연도를 바꿔 가며 자세히 비교합니다.</p>
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
          <p>환경부 급·완속 현황 8권역 사분면·급속 비중으로 설치 힌트를 줍니다.</p>
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
try:
    st.page_link(
        "pages/00_발표_브리핑.py",
        label="발표·정책 브리핑으로 이동",
        icon=":material/campaign:",
    )
except Exception:
    st.caption("왼쪽 메뉴에서 「발표·정책 브리핑」을 선택하세요.")

st.caption(
    "분석 단위는 시·도×연·월 집계입니다. 상대 비교이며 절대 부족·예산액 판정이 아닙니다. "
    "2025년 충전량은 1–8월(YTD) 기준으로 읽으세요."
)
