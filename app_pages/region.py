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
        "우리 지역의 공공급속 **이용·피크**를 자세히 보는 화면입니다.",
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

    status_badge(str(current["기간상태"]), current["관측월수"])
    status_badge(str(current["설비상태"]))

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        metric_card(
            "전기차등록대수",
            current["전기차등록대수"],
            percent_change(current["전기차등록대수"], previous.get("전기차등록대수")),
        )
    with c2:
        metric_card(
            "활성충전기수",
            current["활성충전기수"],
            percent_change(
                current["활성충전기수"],
                previous.get("활성충전기수") if allow_annual_delta else pd.NA,
            ),
        )
    with c3:
        metric_card(
            "충전량_kWh",
            current["충전량_kWh"],
            percent_change(
                current["충전량_kWh"],
                previous.get("충전량_kWh") if allow_annual_delta else pd.NA,
            ),
        )
    with c4:
        metric_card(
            "활성기당충전량",
            current["활성기당충전량"],
            percent_change(
                current["활성기당충전량"],
                previous.get("활성기당충전량") if allow_annual_delta else pd.NA,
            ),
        )

    tabs = st.tabs(["연도별 부담", "월별 피크 조사", "원자료"])

    with tabs[0]:
        st.caption(
            f"{region}의 연도별 부담을 세 지표로 한눈에 봅니다. "
            "클릭 전환 없이 나란히 비교하세요."
        )
        region_year = master[master["시도"] == region].dropna(
            subset=["활성충전기수"]
        )
        annual_metrics = [
            "활성기당충전량",
            "EV천대당활성급속",
            "충전량_kWh",
        ]
        cols = st.columns(3)
        for col, metric in zip(cols, annual_metrics, strict=True):
            meta = METRIC_META[metric]
            with col, st.container(border=True):
                st.markdown(f"**{meta['label']}**")
                plot = region_year.dropna(subset=[metric]).set_index("연도")[[metric]]
                plot = plot.rename(columns={metric: meta["label"]})
                # [고급] Altair mark_line → st.line_chart
                st.line_chart(plot)
                st.caption(meta["help"])

    with tabs[1]:
        region_monthly = panel[panel["시도"] == region].copy()
        region_charge = charge_annual[charge_annual["시도"] == region].copy()
        peak_rows = region_charge.dropna(subset=["평균초과율", "피크월"])

        if not peak_rows.empty:
            latest_peak = peak_rows.sort_values("연도").iloc[-1]
            peak_pct = float(latest_peak["평균초과율"])
            peak_month = int(latest_peak["피크월"])
            peak_year = int(latest_peak["연도"])
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
            month_line = region_monthly.set_index("date")[["충전량_kWh"]].rename(
                columns={"충전량_kWh": "충전량 (kWh)"}
            )
            st.line_chart(month_line)
            if not peak_rows.empty:
                peak_list = peak_rows[["연도", "피크월", "피크충전량", "평균초과율"]].rename(
                    columns={
                        "연도": "연도",
                        "피크월": "피크월",
                        "피크충전량": "피크 kWh",
                        "평균초과율": "평균 대비 초과(%)",
                    }
                )
                st.caption("연도별 피크월 (빨간 점 대신 표로 표시)")
                st.dataframe(peak_list, hide_index=True)

        with right, st.container(border=True):
            st.markdown("**연도별 피크월 · 평균 대비 초과율**")
            if peak_rows.empty:
                st.info("피크 집계가 없습니다.")
            else:
                peak_bar = peak_rows.set_index("연도")[["평균초과율"]].rename(
                    columns={"평균초과율": "월평균 대비 초과 (%)"}
                )
                st.plotly_chart(
                    category_bar_chart(peak_bar),
                    use_container_width=True,
                    config={"displayModeBar": False},
                )
                st.caption("막대=피크월 충전량이 월평균보다 얼마나 높은지")

        if not peak_rows.empty:
            avg_excess = float(peak_rows["평균초과율"].mean())
            common_month = int(peak_rows["피크월"].mode().iloc[0])
            insight_callout(
                "피크 조사 인사이트",
                f"{region}은 관측 기간 평균 피크 초과율이 약 **{avg_excess:.0f}%**이고, "
                f"자주 잡히는 피크월은 **{common_month}월**입니다. "
                "초과율이 크면 평소 용량보다 **성수기·이동 급속** 대비가 더 중요합니다.",
            )

    with tabs[2]:
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
