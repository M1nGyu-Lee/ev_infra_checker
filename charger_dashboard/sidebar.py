"""사이드바 — 브랜드(상단) · 페이지 네비(Streamlit) · 안내 패널."""

from pathlib import Path

import streamlit as st

from charger_dashboard.ui import inject_app_styles

BRAND_LOGO = Path(__file__).resolve().parent / "assets" / "brand_logo.png"


def render_sidebar():
    inject_app_styles()

    if BRAND_LOGO.exists():
        st.logo(str(BRAND_LOGO), size="large")

    with st.sidebar:
        st.markdown("**EV Infra Checker**")
        st.caption("공공급속 · 급·완속 보급 대시보드")
        st.divider()

        with st.expander("데이터 커버리지", expanded=True):
            st.markdown(
                """
                - EV · 충전량: **17시·도**
                - 충전량 관측: **2019-01 ~ 2025-08**
                - 차지인포 급·완속: **8권역**
                """
            )

        with st.expander("읽기 가이드", expanded=False):
            st.markdown(
                """
                - 페이지 안 **연도·스냅샷·시·도**를 먼저 맞춘 뒤 비교
                - **1순위** 지도 → 추이 → 지역 상세
                - **2순위** 급·완속 설치 판단 (차지인포)
                """
            )

        with st.expander("해석 주의", expanded=False):
            st.markdown(
                """
                - 시·도·권역 **상대 비교** (절대 부족 판정 아님)
                - 2025 충전량은 **1~8월** — YTD 비교 권장
                - 공공급속 ≠ 민간·완속·한전 전체
                """
            )

        try:
            st.page_link(
                "pages/06_데이터_안내.py",
                label="데이터 출처·한계 보기",
                icon=":material/info:",
            )
        except Exception:
            st.caption("데이터 안내 페이지에서 출처·한계를 확인하세요.")

        st.caption("공공 인프라 상대 비교 · 분석 계층 기반")
