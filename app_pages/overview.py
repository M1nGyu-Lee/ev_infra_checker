"""National and selected-region overview."""

import altair as alt
import pandas as pd
import streamlit as st

from charger_dashboard.charts import burden_scatter
from charger_dashboard.data import (
    METRIC_META,
    load_master,
    national_year,
    percent_change,
)
from charger_dashboard.ui import (
    data_status_notice,
    dataframe_download,
    metric_card,
    scope_notice,
    status_badge,
)

master = load_master()
year = int(st.session_state.selected_year)
region = st.session_state.selected_sido

scope_notice()
data_status_notice(year)

if region == "전국":
    current = national_year(master, year)
    previous = national_year(master, year - 1) if year - 1 in master["연도"].values else pd.Series()
    scope_label = "전국"
else:
    rows = master[(master["연도"] == year) & (master["시도"] == region)]
    current = rows.iloc[0] if not rows.empty else pd.Series()
    previous_rows = master[
        (master["연도"] == year - 1) & (master["시도"] == region)
    ]
    previous = previous_rows.iloc[0] if not previous_rows.empty else pd.Series()
    scope_label = region

if current.empty:
    st.warning(f"{year}년 {scope_label} 데이터가 없습니다.")
    st.stop()

with st.container(horizontal=True):
    status_badge(str(current.get("기간상태", "unavailable")), current.get("관측월수"))
    if year >= 2023:
        status_badge(str(current.get("설비상태", "source_stale")))

st.subheader(f"{year}년 {scope_label} 핵심지표")
allow_annual_delta = current.get("기간상태") == "complete"

metric_values = [
    ("전기차등록대수", current.get("전기차등록대수"), previous.get("전기차등록대수")),
    (
        "활성충전기수",
        current.get("활성충전기수"),
        previous.get("활성충전기수") if allow_annual_delta else pd.NA,
    ),
    (
        "충전량_kWh",
        current.get("충전량_kWh"),
        previous.get("충전량_kWh") if allow_annual_delta else pd.NA,
    ),
    (
        "활성기당충전량",
        current.get("활성기당충전량"),
        previous.get("활성기당충전량") if allow_annual_delta else pd.NA,
    ),
]
with st.container(horizontal=True):
    for metric, value, previous_value in metric_values:
        metric_card(metric, value, percent_change(value, previous_value))

trend_source = master.copy()
if region != "전국":
    trend_source = trend_source[trend_source["시도"] == region]
else:
    trend_source = pd.DataFrame(
        [dict(year=y, **national_year(master, int(y)).to_dict()) for y in sorted(master["연도"].unique())]
    )

trend_tabs = st.tabs(["전기차·활성기 추이", "충전량·부담", "지역 비교표"])
with trend_tabs[0]:
    left, right = st.columns(2)
    with left, st.container(border=True):
        st.markdown("**전기차 등록대수**")
        ev_chart = (
            alt.Chart(trend_source)
            .mark_line(point=True, color="#2563EB")
            .encode(
                x=alt.X("연도:O", title="연도"),
                y=alt.Y("전기차등록대수:Q", title="전기차 등록대수 (대)"),
                tooltip=[
                    alt.Tooltip("연도:O", title="연도"),
                    alt.Tooltip("전기차등록대수:Q", title="전기차", format=","),
                ],
            )
            .properties(height=330)
        )
        st.altair_chart(ev_chart)
    with right, st.container(border=True):
        st.markdown("**활성 급속충전기**")
        active_chart = (
            alt.Chart(trend_source.dropna(subset=["활성충전기수"]))
            .mark_line(point=True, color="#D97706")
            .encode(
                x=alt.X("연도:O", title="연도"),
                y=alt.Y("활성충전기수:Q", title="활성 급속충전기 (기)"),
                tooltip=[
                    alt.Tooltip("연도:O", title="연도"),
                    alt.Tooltip("활성충전기수:Q", title="활성기", format=","),
                ],
            )
            .properties(height=330)
        )
        st.altair_chart(active_chart)

with trend_tabs[1]:
    chart_data = trend_source.dropna(subset=["충전량_kWh"])
    left, right = st.columns(2)
    with left, st.container(border=True):
        st.markdown("**환경부 공공급속 충전량**")
        st.altair_chart(
            alt.Chart(chart_data)
            .mark_line(point=True, color="#0F766E")
            .encode(
                x=alt.X("연도:O", title="연도"),
                y=alt.Y("충전량_kWh:Q", title="충전량 (kWh)"),
                tooltip=[
                    alt.Tooltip("연도:O", title="연도"),
                    alt.Tooltip("충전량_kWh:Q", title="충전량", format=",.2f"),
                ],
            )
            .properties(height=330)
        )
    with right, st.container(border=True):
        st.markdown("**활성기당 충전량**")
        st.altair_chart(
            alt.Chart(chart_data.dropna(subset=["활성기당충전량"]))
            .mark_line(point=True, color="#DC2626")
            .encode(
                x=alt.X("연도:O", title="연도"),
                y=alt.Y(
                    "활성기당충전량:Q",
                    title="활성기당 충전량 (kWh/기)",
                ),
                tooltip=[
                    alt.Tooltip("연도:O", title="연도"),
                    alt.Tooltip(
                        "활성기당충전량:Q",
                        title="활성기당 kWh",
                        format=",.2f",
                    ),
                ],
            )
            .properties(height=330)
        )

with trend_tabs[2]:
    compare = master[master["연도"] == year].copy()
    display_columns = [
        "시도",
        "기간상태",
        "전기차등록대수",
        "활성충전기수",
        "충전량_kWh",
        "EV천대당활성급속",
        "활성기당충전량",
    ]
    display = compare[display_columns].sort_values(
        "활성기당충전량", ascending=False, na_position="last"
    )
    st.dataframe(
        display,
        hide_index=True,
        column_config={
            "시도": st.column_config.TextColumn("시·도", pinned=True),
            "기간상태": st.column_config.TextColumn("상태"),
            "전기차등록대수": st.column_config.NumberColumn("전기차", format="localized"),
            "활성충전기수": st.column_config.NumberColumn("활성기", format="localized"),
            "충전량_kWh": st.column_config.NumberColumn("충전량(kWh)", format="%.2f"),
            "EV천대당활성급속": st.column_config.NumberColumn(
                "EV 1,000대당 활성기", format="%.2f"
            ),
            "활성기당충전량": st.column_config.NumberColumn(
                "활성기당 kWh", format="%.2f"
            ),
        },
    )
    dataframe_download(display, f"sido_overview_{year}.csv")

if region == "전국" and year <= 2025:
    st.subheader("시·도별 공급–이용 부담")
    scatter_df = master[master["연도"] == year]
    if scatter_df["활성기당충전량"].notna().any():
        st.altair_chart(burden_scatter(scatter_df))
        st.caption(
            "왼쪽 위에 가까울수록 EV 대비 활성 급속기는 적고 활성기당 이용량은 높은 지역입니다. "
            "절대 부족 판정이 아닌 상대 비교입니다."
        )
