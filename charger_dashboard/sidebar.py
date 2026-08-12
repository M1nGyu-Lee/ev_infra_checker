"""사이드바 — 브랜드(상단) · 페이지 네비(Streamlit) · 안내 패널."""

import streamlit as st

from charger_dashboard.ui import inject_app_styles

BRAND_HTML = """
<div class="ev-sidebar-brand">
  <div class="ev-sidebar-brand-title">EV Infra Checker</div>
  <div class="ev-sidebar-brand-tagline">공공급속 · 급·완속 보급 대시보드</div>
</div>
"""


def render_sidebar():
    inject_app_styles()

    with st.sidebar:
        st.markdown(BRAND_HTML, unsafe_allow_html=True)
        st.markdown('<div class="ev-sidebar-panels">', unsafe_allow_html=True)

        st.markdown(
            """
            <div class="ev-sidebar-panel">
              <div class="ev-sidebar-panel-title">데이터 커버리지</div>
              <ul class="ev-sidebar-list">
                <li>EV · 충전량: <strong>17시·도</strong></li>
                <li>충전량 관측: <strong>2019-01 ~ 2025-08</strong></li>
                <li>차지인포 급·완속: <strong>8권역</strong></li>
              </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div class="ev-sidebar-panel">
              <div class="ev-sidebar-panel-title">읽기 가이드</div>
              <ul class="ev-sidebar-list">
                <li>페이지 안 <strong>연도·스냅샷·시·도</strong>를 먼저 맞춘 뒤 비교</li>
                <li><strong>1순위</strong> 지도 → 추이 → 지역 상세</li>
                <li><strong>2순위</strong> 급·완속 설치 판단 (차지인포)</li>
              </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div class="ev-sidebar-panel ev-sidebar-panel-muted">
              <div class="ev-sidebar-panel-title">해석 주의</div>
              <ul class="ev-sidebar-list">
                <li>시·도·권역 <strong>상대 비교</strong> (절대 부족 판정 아님)</li>
                <li>2025 충전량은 <strong>1~8월</strong> — YTD 비교 권장</li>
                <li>공공급속 ≠ 민간·완속·한전 전체</li>
              </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

        try:
            st.page_link(
                "pages/06_데이터_안내.py",
                label="데이터 출처·한계 보기",
                icon=":material/info:",
            )
        except Exception:
            st.caption("데이터 안내 페이지에서 출처·한계를 확인하세요.")

        st.caption("EV Infra Checker · 공공 인프라 상대 비교 도구")
        st.markdown("</div>", unsafe_allow_html=True)
