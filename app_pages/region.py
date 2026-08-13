"""지역 상세: 연도별 부담 + 월별 피크 (1순위)."""

import pandas as pd
import streamlit as st

from charger_dashboard.charts import category_bar_chart
from charger_dashboard.data import (
    METRIC_META,
    SIDO_ORDER,
    available_years,
    load_charge_annual,
    load_charge_panel,
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


def render():
    priority_banner(
        1,
        "우리 지역의 공공급속 **이용·피크**를 자세히 보는 **탐색** 화면입니다. "
        "발표 본편은 **발표·정책 브리핑**을 먼저 보세요.",
    )

    master = load_master()
    panel = load_charge_panel()
    charge_annual = load_charge_annual()
    year = year_selector(available_years(), key="region_year")

    region = st.selectbox(
        "분석할 시·도",
        SIDO_ORDER,
        index=0,
        key="region_page_sido",
    )
    scope_notice()
    data_status_notice(year)

    current_rows = master[(master["year"] == year) & (master["sido_short"] == region)]
    if current_rows.empty:
        st.warning(f"{year}년 {region} 데이터가 없습니다.")
        st.stop()
    current = current_rows.iloc[0]
    previous_rows = master[
        (master["year"] == year - 1) & (master["sido_short"] == region)
    ]
    previous = previous_rows.iloc[0] if not previous_rows.empty else pd.Series()
    allow_annual_delta = current["data_status"] == "complete"

    status_badge(str(current["data_status"]), current["month_count"])
    status_badge(str(current["charger_stock_status"]))

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        metric_card(
            "ev_count",
            current["ev_count"],
            percent_change(current["ev_count"], previous.get("ev_count")),
        )
    with c2:
        metric_card(
            "active_charger_count",
            current["active_charger_count"],
            percent_change(
                current["active_charger_count"],
                previous.get("active_charger_count") if allow_annual_delta else pd.NA,
            ),
        )
    with c3:
        metric_card(
            "charge_kwh_sum",
            current["charge_kwh_sum"],
            percent_change(
                current["charge_kwh_sum"],
                previous.get("charge_kwh_sum") if allow_annual_delta else pd.NA,
            ),
        )
    with c4:
        metric_card(
            "kwh_per_active_charger",
            current["kwh_per_active_charger"],
            percent_change(
                current["kwh_per_active_charger"],
                previous.get("kwh_per_active_charger") if allow_annual_delta else pd.NA,
            ),
        )

    tabs = st.tabs(["연도별 부담", "월별 피크 조사", "원자료"])

    with tabs[0]:
        st.caption(
            f"{region}의 연도별 부담을 세 지표로 한눈에 봅니다. "
            "클릭 전환 없이 나란히 비교하세요."
        )
        region_year = master[master["sido_short"] == region].dropna(
            subset=["active_charger_count"]
        )
        annual_metrics = [
            "kwh_per_active_charger",
            "fast_per_1000_ev_active",
            "charge_kwh_sum",
        ]
        cols = st.columns(3)
        for col, metric in zip(cols, annual_metrics, strict=True):
            meta = METRIC_META[metric]
            with col, st.container(border=True):
                st.markdown(f"**{meta['label']}**")
                plot = region_year.dropna(subset=[metric]).set_index("year")[[metric]]
                plot = plot.rename(columns={metric: meta["label"]})
                # [고급] Altair mark_line → st.line_chart
                st.line_chart(plot)
                st.caption(meta["help"])

    with tabs[1]:
        region_monthly = panel[panel["sido_short"] == region].copy()
        region_charge = charge_annual[charge_annual["sido_short"] == region].copy()
        peak_rows = region_charge.dropna(subset=["peak_above_avg_pct", "peak_month"])

        if not peak_rows.empty:
            latest_peak = peak_rows.sort_values("year").iloc[-1]
            peak_pct = float(latest_peak["peak_above_avg_pct"])
            peak_month = int(latest_peak["peak_month"])
            peak_year = int(latest_peak["year"])
            if peak_pct >= 40:
                peak_msg = (
                    f"{region} **{peak_year}년** 피크는 **{peak_month}월**이고, "
                    f"월평균보다 **{peak_pct:.0f}%** 높습니다. "
                    "성수기·이동 수요에 급속이 몰리는 편으로 읽을 수 있습니다."
                )
                tone = "warning"
            else:
                peak_msg = (
                    f"{region} **{peak_year}년** 피크는 **{peak_month}월**, "
                    f"월평균 대비 초과율 **{peak_pct:.0f}%**입니다. "
                    "상시 이용과 피크 차이가 상대적으로 작은 편입니다."
                )
                tone = "info"
            insight_callout("월별 피크 한줄 요약", peak_msg, tone=tone)
        else:
            insight_callout(
                "월별 피크 한줄 요약",
                f"{region}의 피크월 집계가 충분하지 않습니다. 아래 월별 충전량 추이를 먼저 보세요.",
            )

        left, right = st.columns(2)
        with left, st.container(border=True):
            st.markdown("**월별 공공급속 충전량**")
            # [고급] Altair 피크 점·라벨 레이어 → 선만 + 아래 표로 피크월 표시
            month_line = region_monthly.set_index("date")[["charge_kwh_sum"]].rename(
                columns={"charge_kwh_sum": "충전량 (kWh)"}
            )
            st.line_chart(month_line)
            if not peak_rows.empty:
                peak_list = peak_rows[["year", "peak_month", "peak_kwh", "peak_above_avg_pct"]].rename(
                    columns={
                        "year": "연도",
                        "peak_month": "피크월",
                        "peak_kwh": "피크 kWh",
                        "peak_above_avg_pct": "평균 대비 초과(%)",
                    }
                )
                st.caption("연도별 피크월 (빨간 점 대신 표로 표시)")
                st.dataframe(peak_list, hide_index=True)

        with right, st.container(border=True):
            st.markdown("**연도별 피크월 · 평균 대비 초과율**")
            if peak_rows.empty:
                st.info("피크 집계가 없습니다.")
            else:
                peak_bar = peak_rows.set_index("year")[["peak_above_avg_pct"]].rename(
                    columns={"peak_above_avg_pct": "월평균 대비 초과 (%)"}
                )
                st.plotly_chart(
                    category_bar_chart(peak_bar),
                    use_container_width=True,
                    config={"displayModeBar": False},
                )
                st.caption("막대=피크월 충전량이 월평균보다 얼마나 높은지")

        if not peak_rows.empty:
            avg_excess = float(peak_rows["peak_above_avg_pct"].mean())
            common_month = int(peak_rows["peak_month"].mode().iloc[0])
            insight_callout(
                "피크 조사 인사이트",
                f"{region}은 관측 기간 평균 피크 초과율이 약 **{avg_excess:.0f}%**이고, "
                f"자주 잡히는 피크월은 **{common_month}월**입니다. "
                "초과율이 크면 평소 용량보다 **성수기·이동 급속** 대비가 더 중요합니다.",
            )

    with tabs[2]:
        raw = panel[panel["sido_short"] == region].sort_values("year_month", ascending=False)
        show_raw = raw.drop(columns=[c for c in ("date",) if c in raw.columns])
        st.dataframe(
            show_raw,
            hide_index=True,
            column_config={
                "year_month": st.column_config.TextColumn("기준월", pinned=True),
                "sido_short": None,
                "ev_count": st.column_config.NumberColumn("EV", format="localized"),
                "charge_kwh_sum": st.column_config.NumberColumn("충전량", format="%.2f"),
                "charge_count_sum": st.column_config.NumberColumn("충전횟수", format="localized"),
                "charge_hours_sum": st.column_config.NumberColumn("충전시간", format="%.2f"),
                "active_charger_count": st.column_config.NumberColumn("활성기", format="localized"),
                "kwh_per_ev": st.column_config.NumberColumn("EV당 kWh", format="%.2f"),
                "count_per_ev": st.column_config.NumberColumn("EV당 횟수", format="%.2f"),
                "kwh_per_active_charger": st.column_config.NumberColumn(
                    "활성기당 kWh", format="%.2f"
                ),
            },
        )
        drop_cols = [c for c in ("date",) if c in raw.columns]
        dataframe_download(raw.drop(columns=drop_cols), f"{region}_monthly_detail.csv")
