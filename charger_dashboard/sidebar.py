"""사이드바 안내 (모든 pages/ 화면에서 공통 호출)."""

import streamlit as st


def render_sidebar():
    with st.sidebar:
        st.markdown("**EV Infra Checker**")
        st.caption("공공급속 · 급·완속 보급 대시보드")
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
