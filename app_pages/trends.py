"""1순위"""

import streamlit as st

from charger_dashboard.data import (
    METRIC_META,
    SIDO_ORDER,
    load_charge_panel,
    load_national_charge_ev_monthly,
)
from charger_dashboard.ui import (
    dataframe_download,
    insight_callout,
    priority_banner,
    scope_notice,
)


def render():
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
            )

    st.markdown("#### 전국 EV와 공공급속 충전량")
    # [고급] Altair 이중축(layer + resolve_scale) → 선 차트 두 개로 분리
    nat_plot = nat.set_index("date")
    st.caption("전기차 등록대수")
    st.line_chart(nat_plot[["전기차등록대수"]].rename(columns={"전기차등록대수": "전기차 (대)"}))
    st.caption("공공급속 충전량 (kWh) — 축이 달라서 아래 따로 그립니다")
    st.line_chart(
        nat_plot[["충전량_kWh"]].rename(columns={"충전량_kWh": "충전량 (kWh)"})
    )
    st.caption("2025년은 1월부터 8월까지만 있습니다.")

    with st.form("trend_filters", border=True):
        selected_regions = st.multiselect(
            "비교할 시·도",
            SIDO_ORDER,
            default=["서울", "경기", "제주"],
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

    st.subheader("시·도별 공공급속 이용 추이")
    selected_metric = st.segmented_control(
        "표시지표",
        options=["충전량_kWh", "활성기당충전량"],
        format_func=lambda metric: METRIC_META[metric]["label"],
        default="충전량_kWh",
        key="trend_charge_metric",
    )
    if selected_metric is None:
        selected_metric = "충전량_kWh"
    meta = METRIC_META[selected_metric]

    # 날짜 × 시·도 표로 피벗 → st.line_chart가 시·도마다 선 하나
    pivot = panel_filtered.pivot_table(
        index="date",
        columns="시도",
        values=selected_metric,
        aggfunc="mean",
    )
    st.line_chart(pivot)
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
