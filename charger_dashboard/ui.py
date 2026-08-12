"""Reusable Streamlit presentation helpers (초보 친화 버전)."""

from __future__ import annotations

import math

import pandas as pd
import streamlit as st

from charger_dashboard.data import METRIC_META


def inject_app_styles() -> None:
    """예전에는 여기에 긴 CSS를 넣었음. 지금은 기본 Streamlit 테마만 사용."""
    # [고급 · 주석 처리] 전역 CSS 주입 — 폰트·사이드바 그라데이션·카드 그림자 등
    # st.markdown("""<style>...</style>""", unsafe_allow_html=True)
    return


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
    }
    if chart_data is not None:
        kwargs["chart_data"] = chart_data
    st.metric(**kwargs)


def priority_banner(priority: int, description: str) -> None:
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


def insight_callout(title: str, body: str, *, tone: str = "info") -> None:
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


def year_selector(
    years: list[int],
    *,
    key: str,
    default: int | None = None,
    label: str = "기준연도",
) -> int:
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


def chargeinfo_region_label(name: str) -> str:
    from charger_dashboard.data import CHARGEINFO_REGION_LABEL

    return CHARGEINFO_REGION_LABEL.get(str(name), str(name))


def hint_badge_html(hint: str) -> str:
    """설치 힌트 문구 (HTML 뱃지 대신 그냥 글자)."""
    # [고급 · 주석 처리] 색 있는 HTML pill
    # return f'<span style="...">{hint}</span>'
    return hint


def dataframe_download(df: pd.DataFrame, filename: str, label: str = "표 CSV 다운로드") -> None:
    st.download_button(
        label,
        data=df.to_csv(index=False).encode("utf-8-sig"),
        file_name=filename,
        mime="text/csv",
        icon=":material/download:",
    )
