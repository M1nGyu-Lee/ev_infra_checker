"""Reusable Streamlit presentation helpers (초보 친화 버전)."""

import math

import pandas as pd
import streamlit as st

from charger_dashboard.data import METRIC_META


def inject_app_styles():
    """데이터 대시보드용 색감·레이아웃 스타일 (차트·데이터 로직은 변경하지 않음)."""
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Sans+KR:wght@400;500;600;700&display=swap');

        html, body, [class*="css"] {
            font-family: "IBM Plex Sans KR", "IBM Plex Sans", "Noto Sans KR", sans-serif;
        }

        [data-testid="stAppViewContainer"] {
            background:
                radial-gradient(ellipse 80% 50% at 0% -10%, rgba(15, 118, 110, 0.08), transparent 55%),
                radial-gradient(ellipse 60% 40% at 100% 0%, rgba(37, 99, 235, 0.06), transparent 50%),
                linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
        }
        [data-testid="stMain"] { background: transparent; }
        [data-testid="stHeader"] { background: rgba(248, 250, 252, 0.85); backdrop-filter: blur(8px); }

        .block-container {
            padding-top: 1.4rem;
            padding-bottom: 2.5rem;
            max-width: 1280px;
        }

        /* ── Sidebar ── */
        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0f766e 0%, #134e4a 42%, #0f172a 100%);
            border-right: none;
        }
        section[data-testid="stSidebar"] > div:first-child { background: transparent; }
        section[data-testid="stSidebar"] * { color: #e2e8f0 !important; }
        section[data-testid="stSidebar"] strong { color: #ffffff !important; }
        section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
        section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] li {
            color: #cbd5e1 !important;
        }
        section[data-testid="stSidebar"] hr {
            border-color: rgba(255,255,255,0.14);
        }
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a {
            border-radius: 0.65rem;
            margin: 0.12rem 0;
            color: #e2e8f0 !important;
        }
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a:hover {
            background: rgba(255,255,255,0.08);
        }
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[aria-current="page"] {
            background: rgba(45, 212, 191, 0.22);
            color: #ffffff !important;
            font-weight: 600;
            border-left: 3px solid #2dd4bf;
        }
        section[data-testid="stSidebar"] [data-testid="stExpander"] {
            background: rgba(255,255,255,0.06);
            border: 1px solid rgba(255,255,255,0.12);
            border-radius: 0.7rem;
            margin-bottom: 0.45rem;
        }
        section[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"] {
            border-radius: 0.65rem;
            background: rgba(255,255,255,0.08);
            border: 1px solid rgba(255,255,255,0.14);
            margin-top: 0.4rem;
        }
        section[data-testid="stSidebar"] [data-testid="stLogo"] {
            margin-bottom: 0.4rem;
        }

        /* ── Titles ── */
        h1 {
            letter-spacing: -0.02em;
            color: #0f172a !important;
            font-weight: 700 !important;
        }
        h2, h3 {
            color: #0f172a !important;
            font-weight: 600 !important;
        }

        /* ── Metric cards ── */
        [data-testid="stMetric"] {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 0.9rem;
            padding: 0.85rem 1rem;
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
        }
        [data-testid="stMetricLabel"] { color: #64748b !important; }
        [data-testid="stMetricValue"] { color: #0f172a !important; }

        /* ── Bordered containers ── */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background: #ffffff;
            border: 1px solid #e2e8f0 !important;
            border-radius: 1rem !important;
            box-shadow: 0 1px 3px rgba(15, 23, 42, 0.05);
        }

        /* ── Tabs ── */
        [data-testid="stTabs"] [role="tablist"] {
            gap: 0.25rem;
            border-bottom: 1px solid #e2e8f0;
            padding-bottom: 0.15rem;
        }
        [data-testid="stTabs"] button[role="tab"] {
            border-radius: 0.55rem 0.55rem 0 0;
            color: #64748b;
            font-weight: 500;
        }
        [data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
            color: #0f766e !important;
            background: rgba(15, 118, 110, 0.08);
            border-bottom: 2px solid #0f766e;
        }

        /* ── Alerts / insights ── */
        [data-testid="stAlert"] {
            border-radius: 0.85rem;
            border: 1px solid #e2e8f0;
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.03);
        }
        div[data-testid="stAlert"][kind="info"],
        .stAlert[data-baseweb="notification"] {
            background: linear-gradient(90deg, rgba(15,118,110,0.08), rgba(255,255,255,0.95));
        }

        /* ── Dataframes ── */
        [data-testid="stDataFrame"] {
            border: 1px solid #e2e8f0;
            border-radius: 0.85rem;
            overflow: hidden;
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.03);
        }

        /* ── Buttons ── */
        .stDownloadButton button, .stButton button {
            border-radius: 0.65rem;
            font-weight: 600;
        }

        /* ── Priority / section chrome ── */
        .ev-priority {
            display: inline-flex;
            align-items: center;
            gap: 0.45rem;
            background: linear-gradient(135deg, #0f766e, #0d9488);
            color: #ffffff;
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0.03em;
            padding: 0.28rem 0.7rem;
            border-radius: 999px;
            margin-right: 0.45rem;
            vertical-align: middle;
        }
        .ev-priority-wrap {
            margin: 0.15rem 0 0.85rem;
            padding: 0.85rem 1rem;
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-left: 4px solid #0f766e;
            border-radius: 0.85rem;
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
            color: #334155;
            line-height: 1.5;
        }
        .ev-hero {
            background: linear-gradient(135deg, #0f766e 0%, #115e59 55%, #1e3a5f 100%);
            color: #ffffff;
            border-radius: 1.1rem;
            padding: 1.35rem 1.5rem 1.45rem;
            margin-bottom: 1.1rem;
            box-shadow: 0 8px 24px rgba(15, 118, 110, 0.18);
        }
        .ev-hero h1 {
            color: #ffffff !important;
            margin: 0 0 0.4rem 0 !important;
            font-size: 1.65rem !important;
        }
        .ev-hero p {
            color: #ccfbf1;
            margin: 0;
            font-size: 0.95rem;
            line-height: 1.5;
        }
        .ev-layer-card {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 0.9rem;
            padding: 0.9rem 1rem;
            height: 100%;
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
            border-top: 3px solid #0f766e;
        }
        .ev-layer-card h4 {
            margin: 0 0 0.35rem 0;
            color: #0f766e;
            font-size: 0.95rem;
        }
        .ev-layer-card .q {
            color: #334155;
            font-size: 0.86rem;
            margin-bottom: 0.45rem;
            line-height: 1.4;
        }
        .ev-layer-card .meta {
            color: #64748b;
            font-size: 0.78rem;
            line-height: 1.35;
        }
        .ev-section-label {
            display: inline-block;
            font-size: 0.72rem;
            font-weight: 700;
            letter-spacing: 0.06em;
            text-transform: uppercase;
            color: #0f766e;
            background: rgba(15, 118, 110, 0.1);
            padding: 0.2rem 0.55rem;
            border-radius: 999px;
            margin-bottom: 0.55rem;
        }
        .ev-home-card {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 0.95rem;
            padding: 1rem 1.1rem;
            box-shadow: 0 1px 3px rgba(15, 23, 42, 0.05);
            height: 100%;
        }
        .ev-home-card .rank {
            font-size: 0.72rem;
            font-weight: 700;
            color: #0f766e;
            letter-spacing: 0.04em;
            text-transform: uppercase;
        }
        .ev-home-card h3 {
            margin: 0.25rem 0 0.4rem 0 !important;
            font-size: 1.05rem !important;
        }
        .ev-home-card p {
            margin: 0;
            color: #64748b;
            font-size: 0.88rem;
            line-height: 1.45;
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
        1: "1순위 · 정책 결정",
        2: "2순위 · 급·완속 사업자",
        3: "3순위 · 전국 기초 총량",
    }
    label = labels.get(priority, f"{priority}순위")
    st.markdown(
        f'<div class="ev-priority-wrap">'
        f'<span class="ev-priority">{label}</span>{description}'
        f"</div>",
        unsafe_allow_html=True,
    )


def insight_callout(title, body, *, tone="info"):
    """요약 박스. Streamlit 기본 알림 + 전역 스타일."""
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
    preferred = default
    if preferred is None or preferred not in years:
        preferred = 2025 if 2025 in years else years[-1]
    idx = years.index(preferred)
    return int(st.selectbox(label, years, index=idx, key=key))


def chargeinfo_region_label(name):
    from charger_dashboard.data import CHARGEINFO_REGION_LABEL

    return CHARGEINFO_REGION_LABEL.get(str(name), str(name))


def hint_badge_html(hint):
    """설치 힌트 문구."""
    return hint


def dataframe_download(df, filename, label="표 CSV 다운로드"):
    st.download_button(
        label,
        data=df.to_csv(index=False).encode("utf-8-sig"),
        file_name=filename,
        mime="text/csv",
        icon=":material/download:",
    )
