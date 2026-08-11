"""Reusable Streamlit presentation helpers."""

from __future__ import annotations

import math

import pandas as pd
import streamlit as st

from charger_dashboard.data import METRIC_META


def inject_app_styles() -> None:
    """Global visual polish — teal/slate infra look, denser sidebar, softer cards."""
    st.markdown(
        """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Sans+KR:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
  font-family: "IBM Plex Sans KR", "IBM Plex Sans", sans-serif;
}

/* Main canvas */
.stApp {
  background:
    radial-gradient(1200px 500px at 10% -10%, #ccfbf1 0%, transparent 55%),
    radial-gradient(900px 400px at 100% 0%, #e2e8f0 0%, transparent 50%),
    #f8fafc;
}

/* Top nav */
[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #0f766e 0%, #115e59 42%, #0f172a 100%);
  border-right: none;
}
[data-testid="stSidebar"] * {
  color: #f8fafc !important;
}
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stCaption,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
  color: #ecfdf5 !important;
}
[data-testid="stSidebar"] div[data-baseweb="select"] > div {
  background-color: rgba(255,255,255,0.12);
  border-color: rgba(255,255,255,0.25);
}
[data-testid="stSidebar"] hr {
  border-color: rgba(255,255,255,0.2);
}

/* Title */
h1 {
  letter-spacing: -0.02em;
  font-weight: 700 !important;
  color: #0f172a !important;
  padding-top: 0.25rem !important;
}

/* Metric cards */
[data-testid="stMetric"] {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 14px;
  padding: 0.85rem 1rem;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
}
[data-testid="stMetricLabel"] {
  color: #64748b !important;
  font-weight: 500 !important;
}
[data-testid="stMetricValue"] {
  color: #0f172a !important;
  font-weight: 700 !important;
}

/* Bordered containers */
[data-testid="stVerticalBlockBorderWrapper"] {
  background: #ffffff;
  border: 1px solid #e2e8f0 !important;
  border-radius: 16px !important;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.04);
}

/* Tabs */
button[data-baseweb="tab"] {
  font-weight: 600;
}
button[data-baseweb="tab"][aria-selected="true"] {
  color: #0f766e !important;
}

/* Primary buttons / downloads */
.stDownloadButton button, .stFormSubmitButton button {
  border-radius: 10px !important;
  font-weight: 600 !important;
}

/* Insight strip */
.ev-insight {
  border-left: 4px solid #0f766e;
  background: linear-gradient(90deg, #ecfdf5 0%, #ffffff 70%);
  border-radius: 0 14px 14px 0;
  padding: 0.9rem 1.1rem;
  margin: 0.4rem 0 1rem 0;
  border: 1px solid #99f6e4;
  border-left-width: 4px;
}
.ev-insight-title {
  font-weight: 700;
  color: #134e4a;
  margin-bottom: 0.25rem;
  font-size: 0.95rem;
}
.ev-insight-body {
  color: #334155;
  font-size: 0.92rem;
  line-height: 1.55;
}
.ev-priority {
  display: inline-block;
  background: #0f766e;
  color: #ecfdf5;
  font-size: 0.75rem;
  font-weight: 600;
  padding: 0.2rem 0.55rem;
  border-radius: 999px;
  margin-right: 0.45rem;
  letter-spacing: 0.02em;
}
.ev-sidebar-brand {
  font-size: 1.05rem;
  font-weight: 700;
  margin-bottom: 0.15rem;
}
.ev-sidebar-sub {
  font-size: 0.8rem;
  opacity: 0.85;
  margin-bottom: 1rem;
}
</style>
        """,
        unsafe_allow_html=True,
    )


def format_value(value: float | int, metric: str) -> str:
    if value is None or pd.isna(value):
        return "데이터 없음"
    meta = METRIC_META[metric]
    return f"{value:{meta['format']}} {meta['unit']}"


def format_delta(value: float | None, suffix: str = " 전년 대비") -> str | None:
    if value is None or pd.isna(value) or math.isinf(value):
        return None
    return f"{value:+.1f}%{suffix}"


def status_badge(status: str, month_count: float | None = None) -> None:
    if status == "observed":
        st.badge("설비 관측", icon=":material/check_circle:", color="blue")
    elif status == "complete":
        st.badge("완전연도", icon=":material/check_circle:", color="green")
    elif status == "partial":
        label = f"부분연도 · {int(month_count)}개월" if pd.notna(month_count) else "부분연도"
        st.badge(label, icon=":material/calendar_month:", color="orange")
    elif status == "source_stale":
        st.badge("원천 갱신 중단", icon=":material/update_disabled:", color="red")
    else:
        st.badge("데이터 없음", icon=":material/info:", color="gray")


def metric_card(
    metric: str,
    value: float | int,
    delta: float | None = None,
    chart_data: list[float] | None = None,
) -> None:
    meta = METRIC_META[metric]
    kwargs = {
        "label": meta["label"],
        "value": format_value(value, metric),
        "delta": format_delta(delta),
        "help": meta["help"],
        "border": True,
        "chart_data": chart_data,
    }
    st.metric(**kwargs)


def priority_banner(priority: int, description: str) -> None:
    labels = {
        1: "1순위 · 대국민 홍보",
        2: "2순위 · 급·완속 사업자",
        3: "3순위 · 전국 기초 총량",
    }
    label = labels.get(priority, f"{priority}순위")
    st.markdown(
        f'<div style="margin:0.15rem 0 0.85rem 0;color:#475569;font-size:0.92rem;">'
        f'<span class="ev-priority">{label}</span>{description}</div>',
        unsafe_allow_html=True,
    )


def insight_callout(title: str, body: str, *, tone: str = "info") -> None:
    """Audience-facing takeaway strip (HTML) — avoids stacking many st.info boxes."""
    accent = {
        "info": "#0f766e",
        "warning": "#d97706",
        "success": "#059669",
        "error": "#dc2626",
    }.get(tone, "#0f766e")
    # lightweight markdown bold -> HTML
    safe_body = (
        body.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("\n", "<br/>")
    )
    while "**" in safe_body:
        safe_body = safe_body.replace("**", "<strong>", 1).replace("**", "</strong>", 1)
    st.markdown(
        f'<div class="ev-insight" style="border-left-color:{accent};">'
        f'<div class="ev-insight-title">{title}</div>'
        f'<div class="ev-insight-body">{safe_body}</div></div>',
        unsafe_allow_html=True,
    )


def scope_notice() -> None:
    st.caption(
        "범위: 전기차=국토부 · 이용·활성기=**환경부 공공급속** "
        "(민간·한전·완속 충전량 미포함)"
    )


def data_status_notice(year: int) -> None:
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


def dataframe_download(df: pd.DataFrame, filename: str, label: str = "표 CSV 다운로드") -> None:
    st.download_button(
        label,
        data=df.to_csv(index=False).encode("utf-8-sig"),
        file_name=filename,
        mime="text/csv",
        icon=":material/download:",
    )
