"""Single-region drilldown: yearly burden + monthly peak investigation."""

import altair as alt
import pandas as pd
import streamlit as st

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
    colors = ["#0F766E", "#D97706", "#2563EB"]
    cols = st.columns(3)
    for col, metric, color in zip(cols, annual_metrics, colors, strict=True):
        meta = METRIC_META[metric]
        with col, st.container(border=True):
            st.markdown(f"**{meta['label']}**")
            plot = region_year.dropna(subset=[metric])
            st.altair_chart(
                alt.Chart(plot)
                .mark_line(point=True, color=color)
                .encode(
                    x=alt.X("연도:O", title="연도"),
                    y=alt.Y(
                        f"{metric}:Q",
                        title=f"{meta['unit']}",
                    ),
                    tooltip=[
                        alt.Tooltip("연도:O", title="연도"),
                        alt.Tooltip(
                            f"{metric}:Q",
                            title=meta["label"],
                            format=meta["format"],
                        ),
                    ],
                )
                .properties(height=320),
                use_container_width=True,
            )
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
            tone="info",
        )

    # Mark annual peak months on the monthly series when possible.
    peak_marks = []
    if not peak_rows.empty and not region_monthly.empty:
        for _, prow in peak_rows.iterrows():
            ym = f"{int(prow['연도'])}-{int(prow['피크월']):02d}"
            hit = region_monthly[region_monthly["기준월"] == ym]
            if not hit.empty:
                peak_marks.append(
                    {
                        "date": hit.iloc[0]["date"],
                        "충전량_kWh": hit.iloc[0]["충전량_kWh"],
                        "label": f"{int(prow['피크월'])}월 피크",
                    }
                )
    peak_mark_df = pd.DataFrame(peak_marks)

    left, right = st.columns(2)
    with left, st.container(border=True):
        st.markdown("**월별 공공급속 충전량**")
        line = (
            alt.Chart(region_monthly)
            .mark_line(color="#2563EB")
            .encode(
                x=alt.X("date:T", title="기준월"),
                y=alt.Y("충전량_kWh:Q", title="충전량 (kWh)"),
                tooltip=[
                    alt.Tooltip("기준월:N", title="기준월"),
                    alt.Tooltip("충전량_kWh:Q", title="충전량", format=",.0f"),
                    alt.Tooltip("활성충전기수:Q", title="활성기", format=","),
                ],
            )
        )
        chart = line
        if not peak_mark_df.empty:
            points = (
                alt.Chart(peak_mark_df)
                .mark_point(size=90, color="#DC2626", filled=True)
                .encode(
                    x="date:T",
                    y="충전량_kWh:Q",
                    tooltip=[
                        alt.Tooltip("label:N", title="구분"),
                        alt.Tooltip("충전량_kWh:Q", title="충전량", format=",.0f"),
                    ],
                )
            )
            labels = (
                alt.Chart(peak_mark_df)
                .mark_text(dy=-12, fontSize=11, color="#B91C1C")
                .encode(x="date:T", y="충전량_kWh:Q", text="label:N")
            )
            chart = line + points + labels
        st.altair_chart(
            chart.properties(height=380).interactive(bind_y=False),
            use_container_width=True,
        )
        st.caption("빨간 점은 해당 연도의 피크월입니다.")

    with right, st.container(border=True):
        st.markdown("**연도별 피크월 · 평균 대비 초과율**")
        if peak_rows.empty:
            st.info("피크 집계가 없습니다.")
        else:
            peak_plot = peak_rows.copy()
            peak_plot["피크월라벨"] = peak_plot["피크월"].map(lambda m: f"{int(m)}월")
            bars = (
                alt.Chart(peak_plot)
                .mark_bar(cornerRadiusEnd=4, color="#0F766E")
                .encode(
                    x=alt.X("연도:O", title="연도"),
                    y=alt.Y("평균초과율:Q", title="월평균 대비 초과 (%)"),
                    tooltip=[
                        alt.Tooltip("연도:O", title="연도"),
                        alt.Tooltip("피크월라벨:N", title="피크월"),
                        alt.Tooltip(
                            "평균초과율:Q",
                            title="초과율",
                            format=".1f",
                        ),
                        alt.Tooltip("피크충전량:Q", title="피크 kWh", format=",.0f"),
                    ],
                )
            )
            text = (
                alt.Chart(peak_plot)
                .mark_text(dy=-8, fontSize=11, color="#134E4A")
                .encode(
                    x="연도:O",
                    y="평균초과율:Q",
                    text="피크월라벨:N",
                )
            )
            st.altair_chart(
                (bars + text).properties(height=380),
                use_container_width=True,
            )
            st.caption(
                "막대=피크월 충전량이 월평균보다 얼마나 높은지, "
                "막대 위 숫자=그해 피크월입니다."
            )

    if not peak_rows.empty:
        avg_excess = float(peak_rows["평균초과율"].mean())
        common_month = int(
            peak_rows["피크월"].mode().iloc[0]
        )
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
