"""Reusable Streamlit presentation helpers (초보 친화 버전)."""

import math

import pandas as pd
import streamlit as st

from charger_dashboard.data import METRIC_META


def inject_app_styles():
    """사이드바·배경 색감만 조정 (본문 차트·표 레이아웃은 건드리지 않음)."""
    st.markdown(
        """
        <style>
        /* 메인 영역: 은은한 슬레이트 배경 */
        [data-testid="stAppViewContainer"] {
            background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
        }
        [data-testid="stMain"] {
            background: transparent;
        }

        /* 사이드바: 틸 톤 그라데이션 */
        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #f0fdfa 0%, #ecfeff 38%, #f8fafc 100%);
            border-right: 1px solid #cbd5e1;
        }
        section[data-testid="stSidebar"] > div:first-child {
            background: transparent;
        }

        /* 브랜드 → 페이지 네비 → 안내 패널 순서 */
        section[data-testid="stSidebar"] [data-testid="stSidebarContent"] {
            display: flex;
            flex-direction: column;
        }
        section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {
            display: contents;
        }
        .ev-sidebar-brand {
            order: 1;
            margin: 0.15rem 0 0.55rem;
            padding: 0.95rem 1rem;
            border-radius: 0.85rem;
            background: linear-gradient(135deg, #0f766e 0%, #115e59 100%);
            box-shadow: 0 2px 8px rgba(15, 118, 110, 0.22);
        }
        .ev-sidebar-brand-title {
            color: #ffffff;
            font-size: 1.12rem;
            font-weight: 700;
            line-height: 1.25;
        }
        .ev-sidebar-brand-tagline {
            color: #ccfbf1;
            font-size: 0.82rem;
            margin-top: 0.3rem;
            line-height: 1.35;
        }
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] {
            order: 2;
            padding-top: 0.15rem;
            padding-bottom: 0.35rem;
        }
        .ev-sidebar-panels {
            order: 3;
        }

        /* 페이지 네비 링크 */
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a {
            border-radius: 0.65rem;
            margin: 0.1rem 0;
        }
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a:hover {
            background: rgba(15, 118, 110, 0.08);
        }
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[aria-current="page"] {
            background: rgba(15, 118, 110, 0.14);
            color: #0f766e;
            font-weight: 600;
        }

        /* 안내 패널 카드 */
        .ev-sidebar-panel {
            background: rgba(255, 255, 255, 0.82);
            border: 1px solid #e2e8f0;
            border-left: 3px solid #0f766e;
            border-radius: 0.75rem;
            padding: 0.7rem 0.85rem;
            margin-bottom: 0.65rem;
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
        }
        .ev-sidebar-panel-muted {
            border-left-color: #0891b2;
            background: rgba(255, 255, 255, 0.72);
        }
        .ev-sidebar-panel-title {
            color: #0f766e;
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0.04em;
            text-transform: uppercase;
            margin-bottom: 0.45rem;
        }
        .ev-sidebar-list {
            margin: 0;
            padding-left: 1.05rem;
            color: #334155;
            font-size: 0.84rem;
            line-height: 1.45;
        }
        .ev-sidebar-list li {
            margin-bottom: 0.28rem;
        }
        .ev-sidebar-list li:last-child {
            margin-bottom: 0;
        }

        /* 사이드바 하단 page_link */
        section[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"] {
            border-radius: 0.65rem;
            background: rgba(255, 255, 255, 0.75);
            border: 1px solid #e2e8f0;
            margin-top: 0.25rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def format_value(value, metric):
    if value is None or pd.isna(value):
        return "데이터 없음"
    meta = METRIC_META[metric]
    return f"{value:{meta['format']}} {meta['unit']}"


def format_delta(value, suffix=" 전년 대비"):
    if value is None or pd.isna(value) or math.isinf(value):
        return None
    return f"{value:+.1f}%{suffix}"


def status_badge(status, month_count=None):
    """데이터 기간 상태를 짧은 문구로 표시 (st.caption)."""
    if status == "observed":
        st.caption("상태: 설비 관측")
    elif status == "complete":
        st.caption("상태: 완전연도")
    elif status == "partial":
        label = f"상태: 부분연도 · {int(month_count)}개월" if pd.notna(month_count) else "상태: 부분연도"
        st.caption(label)
    elif status == "source_stale":
        st.caption("상태: 원천 갱신 중단")
    else:
        st.caption("상태: 데이터 없음")


def metric_card(metric, value, delta=None, chart_data=None):
    meta = METRIC_META[metric]
    kwargs = {
        "label": meta["label"],
        "value": format_value(value, metric),
        "delta": format_delta(delta),
        "help": meta["help"],
        "border": True,
    }
    if chart_data is not None:
        kwargs["chart_data"] = chart_data
    st.metric(**kwargs)


def priority_banner(priority, description):
    """발표 순위를 한 줄로 표시."""
    labels = {
        1: "1순위 · 대국민 홍보",
        2: "2순위 · 급·완속 사업자",
        3: "3순위 · 전국 기초 총량",
    }
    label = labels.get(priority, f"{priority}순위")
    # [고급 · 주석 처리] HTML 뱃지
    # st.markdown(f'<span class="ev-priority">...</span>', unsafe_allow_html=True)
    st.markdown(f"**{label}** — {description}")


def insight_callout(title, body, *, tone="info"):
    """요약 박스. HTML 대신 Streamlit 기본 알림 사용."""
    # [고급 · 주석 처리] 초록 HTML 요약박스 (ev-insight 클래스)
    # st.markdown(f'<div class="ev-insight">...</div>', unsafe_allow_html=True)
    text = f"**{title}**\n\n{body}"
    if tone == "warning":
        st.warning(text)
    elif tone == "error":
        st.error(text)
    elif tone == "success":
        st.success(text)
    else:
        st.info(text)


def scope_notice():
    st.caption(
        "범위: 전기차=국토부 · 이용·활성기=**환경부 공공급속** "
        "(민간·한전·완속 충전량 미포함)"
    )


def data_status_notice(year):
    if year == 2025:
        st.warning(
            "2025년 충전량은 1월부터 8월까지 관측치입니다. 완전연도 합계 대신 "
            "2024년 1월부터 8월까지의 YTD 비교를 사용하세요.",
            icon=":material/calendar_month:",
        )
    elif year >= 2026:
        st.warning(
            "2026년은 EV 등록만 6월까지 있으며 환경부 충전량은 없습니다.",
            icon=":material/error:",
        )
    elif year >= 2023:
        st.caption(
            "2023년 이후 환경부 공공급속 설치 재고 원천이 갱신되지 않아 "
            "활성 충전기 기준 공급지표를 사용합니다."
        )


def year_selector(years, *, key, default=None, label="기준연도"):
    """페이지마다 연도 고르기. session_state 동기화는 쓰지 않음."""
    if not years:
        raise ValueError("선택 가능한 연도가 없습니다.")
    # [고급 · 주석 처리] 페이지끼리 연도를 맞추던 session_state 동기화
    # preferred = st.session_state.get("selected_year", default)
    preferred = default
    if preferred is None or preferred not in years:
        preferred = 2025 if 2025 in years else years[-1]
    idx = years.index(preferred)
    return int(st.selectbox(label, years, index=idx, key=key))


def chargeinfo_region_label(name):
    from charger_dashboard.data import CHARGEINFO_REGION_LABEL

    return CHARGEINFO_REGION_LABEL.get(str(name), str(name))


def hint_badge_html(hint):
    """설치 힌트 문구 (HTML 뱃지 대신 그냥 글자)."""
    # [고급 · 주석 처리] 색 있는 HTML pill
    # return f'<span style="...">{hint}</span>'
    return hint


def dataframe_download(df, filename, label="표 CSV 다운로드"):
    st.download_button(
        label,
        data=df.to_csv(index=False).encode("utf-8-sig"),
        file_name=filename,
        mime="text/csv",
        icon=":material/download:",
    )
