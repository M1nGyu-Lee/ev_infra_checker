"""Reusable Streamlit presentation helpers."""

from __future__ import annotations

import math

import pandas as pd
import streamlit as st

from charger_dashboard.data import METRIC_META


def format_value(value: float | int, 지표코드: str) -> str:
    if value is None or pd.isna(value):
        return "데이터 없음"
    meta = METRIC_META[metric]
    return f"{value:{meta['format']}} {meta['unit']}"


def format_delta(value: float | None, suffix: str = " 전년 대비") -> str | None:
    if value is None or pd.isna(value) or math.isinf(value):
        return None
    return f"{value:+.1f}%{suffix}"


def status_badge(status: str, 관측월수: float | None = None) -> None:
    if status == "observed":
        st.badge("설비 관측", icon=":material/check_circle:", color="blue")
    elif status == "complete":
        st.badge("완전연도", icon=":material/check_circle:", color="green")
    elif status == "partial":
        label = f"부분연도 · {int(month_count)}개월" if pd.notna(month_count) else "부분연도"
        st.badge(label, icon=":material/calendar_월:", color="orange")
    elif status == "source_stale":
        st.badge("원천 갱신 중단", icon=":material/update_disabled:", color="red")
    else:
        st.badge("데이터 없음", icon=":material/info:", color="gray")


def metric_card(
    지표코드: str,
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
    st.metric(
        **kwargs,
    )


def priority_banner(priority: int, description: str) -> None:
    labels = {
        1: "1순위 · 대국민 홍보",
        2: "2순위 · 급·완속 사업자",
        3: "3순위 · 전국 기초 총량",
    }
    st.caption(f"**{labels.get(priority, f'{priority}순위')}** — {description}")


def insight_callout(title: str, body: str, *, tone: str = "info") -> None:
    """Audience-facing one-screen takeaway. tone: info | warning | success."""
    icon = {
        "info": ":material/lightbulb:",
        "warning": ":material/priority_high:",
        "success": ":material/check_circle:",
    }.get(tone, ":material/lightbulb:")
    getattr(st, tone if tone in {"info", "warning", "success", "error"} else "info")(
        f"**{title}**  \n{body}",
        icon=icon,
    )


def scope_notice() -> None:
    st.info(
        "**분석 범위:** 전기차 등록은 국토교통부 기준, 이용량과 활성 충전기는 "
        "**환경부 공공급속 충전망** 기준입니다. 민간·한전·완속 충전량은 포함하지 않습니다.",
        icon=":material/info:",
    )


def data_status_notice(연도: int) -> None:
    if year == 2025:
        st.warning(
            "2025년 충전량은 1~8월 관측치입니다. 완전연도 합계 대신 "
            "2024년 1~8월과의 YTD 비교를 사용하세요.",
            icon=":material/calendar_월:",
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
