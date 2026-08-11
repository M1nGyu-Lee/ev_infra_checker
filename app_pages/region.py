"""Single-region drilldown with yearly, monthly, and peak views."""

import altair as alt
import pandas as pd
import streamlit as st

from charger_dashboard.data import (
    METRIC_META,
    SIDO_ORDER,
    available_years,
    load_charge_annual,
    load_charge_panel,
    load_charger_annual,
    load_master,
    percent_change,
)
from charger_dashboard.ui import (
    data_status_notice,
    dataframe_download,
    insight_callout,
    metric_card,
    priority_banner,
    scope_notice,
    status_badge,
    year_selector,
)

priority_banner(
    1,
    "우리 지역의 공공급속 **이용·피크**를 자세히 보는 화면입니다.",
)

master = load_master()
panel = load_charge_panel()
charge_annual = load_charge_annual()
charger_annual = load_charger_annual()
year = year_selector(available_years(), key="region_year")

region = st.selectbox(
    "분석할 시·도",
    SIDO_ORDER,
    index=0,
    key="region_page_sido",
)
scope_notice()
data_status_notice(year)

current_rows = master[(master["연도"] == year) & (master["시도"] == region)]
if current_rows.empty:
    st.warning(f"{year}년 {region} 데이터가 없습니다.")
    st.stop()
current = current_rows.iloc[0]
previous_rows = master[
    (master["연도"] == year - 1) & (master["시도"] == region)
]
previous = previous_rows.iloc[0] if not previous_rows.empty else pd.Series()
allow_annual_delta = current["기간상태"] == "complete"

with st.container(horizontal=True):
    status_badge(str(current["기간상태"]), current["관측월수"])
    status_badge(str(current["설비상태"]))

with st.container(horizontal=True):
    metric_card(
        "전기차등록대수",
        current["전기차등록대수"],
        percent_change(current["전기차등록대수"], previous.get("전기차등록대수")),
    )
    metric_card(
        "활성충전기수",
        current["활성충전기수"],
        percent_change(
            current["활성충전기수"],
            previous.get("활성충전기수") if allow_annual_delta else pd.NA,
        ),
    )
    metric_card(
        "충전량_kWh",
        current["충전량_kWh"],
        percent_change(
            current["충전량_kWh"],
            previous.get("충전량_kWh") if allow_annual_delta else pd.NA,
        ),
    )
    metric_card(
        "활성기당충전량",
        current["활성기당충전량"],
        percent_change(
            current["활성기당충전량"],
            previous.get("활성기당충전량") if allow_annual_delta else pd.NA,
        ),
    )

tabs = st.tabs(["연도별 부담", "월별 이용", "피크·공급", "원자료"])

with tabs[0]:
    region_year = master[master["시도"] == region].dropna(
        subset=["활성충전기수"]
    )
    metric = st.segmented_control(
        "연도별 표시지표",
        ["EV천대당활성급속", "활성기당충전량", "충전량_kWh"],
        default="활성기당충전량",
        format_func=lambda value: METRIC_META[value]["label"],
        key="region_annual_metric",
    )
    meta = METRIC_META[metric]
    st.altair_chart(
        alt.Chart(region_year.dropna(subset=[metric]))
        .mark_line(point=True, color="#0F766E")
        .encode(
            x=alt.X("연도:O", title="연도"),
            y=alt.Y(f"{metric}:Q", title=f"{meta['label']} ({meta['unit']})"),
            tooltip=[
                alt.Tooltip("연도:O", title="연도"),
                alt.Tooltip(f"{metric}:Q", title=meta["label"], format=meta["format"]),
                alt.Tooltip("기간상태:N", title="기간 상태"),
            ],
        )
        .properties(height=410)
    )
    st.caption(meta["help"])

with tabs[1]:
    region_monthly = panel[panel["시도"] == region]
    metric = st.segmented_control(
        "월별 표시지표",
        ["충전량_kWh", "활성충전기수", "EV당충전량"],
        default="충전량_kWh",
        format_func=lambda value: METRIC_META[value]["label"],
        key="region_monthly_metric",
    )
    meta = METRIC_META[metric]
    st.altair_chart(
        alt.Chart(region_monthly)
        .mark_line(color="#2563EB")
        .encode(
            x=alt.X("date:T", title="기준월"),
            y=alt.Y(f"{metric}:Q", title=f"{meta['label']} ({meta['unit']})"),
            tooltip=[
                alt.Tooltip("기준월:N", title="기준월"),
                alt.Tooltip(f"{metric}:Q", title=meta["label"], format=meta["format"]),
            ],
        )
        .properties(height=420)
        .interactive(bind_y=False)
    )

with tabs[2]:
    left, right = st.columns(2)
    region_charge = charge_annual[charge_annual["시도"] == region]
    peak_rows = region_charge.dropna(subset=["평균초과율"])
    if not peak_rows.empty:
        latest_peak = peak_rows.sort_values("연도").iloc[-1]
        peak_pct = float(latest_peak["평균초과율"])
        if peak_pct >= 40:
            peak_msg = (
                f"{region}의 최근 관측연도({int(latest_peak['연도'])}) 피크월 충전량은 "
                f"월평균보다 **{peak_pct:.0f}%** 높습니다. "
                "평소보다 **이동·성수기 급속** 부담이 큰 유형일 수 있습니다."
            )
        else:
            peak_msg = (
                f"{region}의 최근 관측연도 피크 초과율은 **{peak_pct:.0f}%**입니다. "
                "상시 이용과 피크 차이가 상대적으로 작은 편입니다."
            )
        insight_callout("피크 이용 힌트", peak_msg)

    with left, st.container(border=True):
        st.markdown("**연도별 피크 월**")
        st.dataframe(
            region_charge[
                [
                    "연도",
                    "피크월",
                    "피크충전량",
                    "월평균충전량",
                    "평균초과율",
                    "기간상태",
                ]
            ],
            hide_index=True,
            column_config={
                "연도": st.column_config.NumberColumn("연도", format="%d"),
                "피크월": st.column_config.NumberColumn("피크 월", format="%d월"),
                "피크충전량": st.column_config.NumberColumn("피크 kWh", format="%.2f"),
                "월평균충전량": st.column_config.NumberColumn("월평균 kWh", format="%.2f"),
                "평균초과율": st.column_config.NumberColumn(
                    "평균 초과율", format="%.2f%%"
                ),
                "기간상태": st.column_config.TextColumn("상태"),
            },
        )
    with right, st.container(border=True):
        st.markdown("**설치 재고 및 신규 설치**")
        region_stock = charger_annual[charger_annual["시도"] == region]
        st.dataframe(
            region_stock,
            hide_index=True,
            column_config={
                "연도": st.column_config.NumberColumn("연도", format="%d"),
                "시도": None,
                "설치누적": st.column_config.NumberColumn("설치 누적", format="localized"),
                "신규설치": st.column_config.NumberColumn("신규 설치", format="localized"),
                "설비상태": st.column_config.TextColumn("상태"),
            },
        )
        st.caption("2023년 이후 빈 값은 설치 0기가 아니라 원천 갱신 중단입니다.")

with tabs[3]:
    raw = panel[panel["시도"] == region].sort_values("기준월", ascending=False)
    st.dataframe(
        raw.drop(columns=["date"]),
        hide_index=True,
        column_config={
            "기준월": st.column_config.TextColumn("기준월", pinned=True),
            "시도": None,
            "전기차등록대수": st.column_config.NumberColumn("EV", format="localized"),
            "충전량_kWh": st.column_config.NumberColumn("충전량", format="%.2f"),
            "충전횟수": st.column_config.NumberColumn("충전횟수", format="localized"),
            "충전시간_h": st.column_config.NumberColumn("충전시간", format="%.2f"),
            "활성충전기수": st.column_config.NumberColumn("활성기", format="localized"),
            "EV당충전량": st.column_config.NumberColumn("EV당 kWh", format="%.2f"),
            "EV당충전횟수": st.column_config.NumberColumn("EV당 횟수", format="%.2f"),
            "활성기당충전량": st.column_config.NumberColumn(
                "활성기당 kWh", format="%.2f"
            ),
        },
    )
    dataframe_download(raw.drop(columns=["date"]), f"{region}_monthly_detail.csv")
