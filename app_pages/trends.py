"""Public fast-charging trends for general-audience briefing (priority 1)."""

import altair as alt
import pandas as pd
import streamlit as st

from charger_dashboard.charts import line_chart, paired_ytd_chart
from charger_dashboard.data import (
    METRIC_META,
    SIDO_ORDER,
    load_charge_panel,
    load_national_charge_ev_monthly,
    load_ytd_compare,
)
from charger_dashboard.ui import (
    dataframe_download,
    insight_callout,
    priority_banner,
    scope_notice,
)

priority_banner(
    1,
    "환경부 **공공급속** 이용이 어떻게 바뀌었는지, 한 화면에서 읽는 대국민용 추이입니다.",
)
scope_notice()

panel_all = load_charge_panel()
nat = load_national_charge_ev_monthly()
nat_complete = nat[nat["date"].dt.year <= 2024]
if len(nat_complete) >= 24:
    y2023 = nat_complete.loc[nat_complete["date"].dt.year == 2023, "충전량_kWh"].sum()
    y2024 = nat_complete.loc[nat_complete["date"].dt.year == 2024, "충전량_kWh"].sum()
    ev2023 = nat_complete.loc[nat_complete["date"].dt.year == 2023, "전기차등록대수"].iloc[-1]
    ev2024 = nat_complete.loc[nat_complete["date"].dt.year == 2024, "전기차등록대수"].iloc[-1]
    if y2023 > 0 and ev2023 > 0:
        charge_chg = (y2024 / y2023 - 1) * 100
        ev_chg = (ev2024 / ev2023 - 1) * 100
        insight_callout(
            "한눈에 보는 변화",
            f"2023→2024 전국 EV는 약 **{ev_chg:+.1f}%**, "
            f"환경부 공공급속 충전량은 약 **{charge_chg:+.1f}%**입니다. "
            "전기차는 늘어도 공공급속 이용이 함께 늘지 않으면, "
            "일상 충전은 **완속·거점**으로 옮겨 갔을 가능성이 큽니다. "
            "(환경부 공공급속만 해당 · 가설)",
            tone="info",
        )

st.markdown("#### 전국 EV와 공공급속 충전량")
base = alt.Chart(nat).encode(x=alt.X("date:T", title="월"))
ev_line = base.mark_line(color="#2563EB").encode(
    y=alt.Y("전기차등록대수:Q", title="전기차 등록대수 (대)", axis=alt.Axis(titleColor="#2563EB")),
)
kwh_line = base.mark_line(color="#0F766E").encode(
    y=alt.Y(
        "충전량_kWh:Q",
        title="공공급속 충전량 (kWh)",
        axis=alt.Axis(titleColor="#0F766E"),
    ),
)
st.altair_chart(
    alt.layer(ev_line, kwh_line).resolve_scale(y="independent").properties(height=280),
)
st.caption("파란선=EV, 초록선=공공급속 충전량(별도 축). 2025년은 1~8월만 있습니다.")

global_region = st.session_state.selected_sido
default_regions = [global_region] if global_region != "전국" else ["서울", "경기", "제주"]

with st.form("trend_filters", border=True):
    selected_regions = st.multiselect(
        "비교할 시·도",
        SIDO_ORDER,
        default=default_regions,
        max_selections=6,
        help="선이 지나치게 겹치지 않도록 최대 6개까지 선택할 수 있습니다.",
    )
    min_year, max_year = st.slider(
        "조회연도",
        min_value=2019,
        max_value=2026,
        value=(2019, 2025),
    )
    st.form_submit_button("필터 적용", icon=":material/filter_alt:")

if not selected_regions:
    st.info("비교할 시·도를 한 곳 이상 선택하세요.")
    st.stop()

panel_filtered = panel_all[
    panel_all["시도"].isin(selected_regions)
    & panel_all["연도"].between(min_year, min(max_year, 2025))
]

tabs = st.tabs(["공공급속 이용 추이", "2024–2025 YTD 비교"])

with tabs[0]:
    selected_metric = st.segmented_control(
        "표시지표",
        options=[
            "충전량_kWh",
            "활성충전기수",
            "EV당충전량",
            "활성기당충전량",
        ],
        format_func=lambda metric: METRIC_META[metric]["label"],
        default="충전량_kWh",
        key="trend_charge_metric",
    )
    meta = METRIC_META[selected_metric]
    st.altair_chart(
        line_chart(
            panel_filtered,
            x="date:T",
            y=f"{selected_metric}:Q",
            color="시도:N",
            y_title=f"{meta['label']} ({meta['unit']})",
            height=430,
        )
    )
    st.caption(meta["help"])

    detail_columns = [
        "기준월",
        "시도",
        "전기차등록대수",
        "충전량_kWh",
        "활성충전기수",
        "EV당충전량",
        "활성기당충전량",
    ]
    with st.expander("월별 상세 데이터"):
        detail = panel_filtered[detail_columns].sort_values(
            ["기준월", "시도"], ascending=[False, True]
        )
        st.dataframe(
            detail,
            hide_index=True,
            column_config={
                "기준월": st.column_config.TextColumn("기준월", pinned=True),
                "시도": st.column_config.TextColumn("시·도", pinned=True),
                "전기차등록대수": st.column_config.NumberColumn("EV", format="localized"),
                "충전량_kWh": st.column_config.NumberColumn("충전량", format="%.2f"),
                "활성충전기수": st.column_config.NumberColumn("활성기", format="localized"),
                "EV당충전량": st.column_config.NumberColumn("EV당 kWh", format="%.2f"),
                "활성기당충전량": st.column_config.NumberColumn(
                    "활성기당 kWh", format="%.2f"
                ),
            },
        )
        dataframe_download(detail, "charge_monthly_filtered.csv")

with tabs[1]:
    ytd = load_ytd_compare()
    ytd = ytd[ytd["시도"].isin(selected_regions)]
    view = st.segmented_control(
        "비교지표",
        ["charge_kwh", "active_charger"],
        format_func=lambda value: "충전량" if value == "charge_kwh" else "활성 충전기",
        default="charge_kwh",
        key="ytd_metric",
    )
    st.altair_chart(paired_ytd_chart(ytd, view))
    if view == "charge_kwh":
        table_columns = [
            "시도",
            "충전량_2024_YTD",
            "충전량_2025_YTD",
            "충전량_YTD증감률",
            "EV당충전량_2024_YTD",
            "EV당충전량_2025_YTD",
        ]
    else:
        table_columns = [
            "시도",
            "활성기_2024_YTD",
            "활성기_2025_YTD",
        ]
    table = ytd[table_columns]
    st.dataframe(
        table,
        hide_index=True,
        column_config={
            "시도": st.column_config.TextColumn("시·도", pinned=True),
            "충전량_2024_YTD": st.column_config.NumberColumn("2024 1~8월", format="%.2f"),
            "충전량_2025_YTD": st.column_config.NumberColumn("2025 1~8월", format="%.2f"),
            "충전량_YTD증감률": st.column_config.NumberColumn("증감률", format="%.2f%%"),
            "EV당충전량_2024_YTD": st.column_config.NumberColumn("2024 EV당 kWh", format="%.2f"),
            "EV당충전량_2025_YTD": st.column_config.NumberColumn("2025 EV당 kWh", format="%.2f"),
            "활성기_2024_YTD": st.column_config.NumberColumn("2024 활성기", format="localized"),
            "활성기_2025_YTD": st.column_config.NumberColumn("2025 활성기", format="localized"),
        },
    )
    st.caption("두 연도 모두 1~8월만 사용한 동일 기간 비교입니다.")
