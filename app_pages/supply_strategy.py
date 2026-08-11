"""Priority 2: fast vs slow install guidance for charging service providers."""

import altair as alt
import pandas as pd
import streamlit as st

from charger_dashboard.data import (
    SIDO_ORDER,
    load_charge_annual,
    load_chargeinfo_ev_per_charger_avg,
    load_chargeinfo_ev_per_charger_wide,
    load_chargeinfo_region_stock,
    load_chargeinfo_region_stock_monthly,
    load_chargeinfo_region_yoy,
    load_chargeinfo_slow_fast_ratio_monthly,
    load_kepco_station_annual,
    load_master,
)
from charger_dashboard.ui import (
    dataframe_download,
    insight_callout,
    priority_banner,
    scope_notice,
)

priority_banner(
    2,
    "급속·완속 **충전 사업자·설치 담당**에게 어디에 어떤 속도를 깔지 판단하는 데이터 화면입니다.",
)

scope_notice()

try:
    chargeinfo_stock = load_chargeinfo_region_stock()
    chargeinfo_yoy = load_chargeinfo_region_yoy()
    has_chargeinfo = True
except FileNotFoundError:
    has_chargeinfo = False
    chargeinfo_stock = pd.DataFrame()
    chargeinfo_yoy = pd.DataFrame()

try:
    chargeinfo_monthly = load_chargeinfo_region_stock_monthly()
    chargeinfo_ratio = load_chargeinfo_slow_fast_ratio_monthly()
    has_chargeinfo_monthly = True
except FileNotFoundError:
    has_chargeinfo_monthly = False
    chargeinfo_monthly = pd.DataFrame()
    chargeinfo_ratio = pd.DataFrame()

try:
    chargeinfo_ev_wide = load_chargeinfo_ev_per_charger_wide()
    chargeinfo_ev_avg = load_chargeinfo_ev_per_charger_avg()
    has_chargeinfo_ev_ratio = True
except FileNotFoundError:
    has_chargeinfo_ev_ratio = False
    chargeinfo_ev_wide = pd.DataFrame()
    chargeinfo_ev_avg = pd.DataFrame()

if has_chargeinfo_ev_ratio:
    st.caption(
        "차지인포 **전기차 1대당 급속·완속·합계(기/대)** 월별 보급률 + "
        "급속·완속 **누적 대수**가 연동되어 있습니다."
    )
elif has_chargeinfo_monthly:
    st.caption(
        "차지인포 **급속·완속 분리 월별 누적(8권역)** 연동됨. "
        "연간 합계 표(2026 YTD 포함)는 별도 섹션입니다."
    )
elif has_chargeinfo:
    st.caption("차지인포 연간 누적만 있습니다. xls를 `data/raw/chargeinfo/`에 넣고 월별 전처리를 실행하세요.")
else:
    st.warning(
        "차지인포 데이터가 없습니다. "
        "`data/raw/chargeinfo/` 확인 후 전처리 스크립트를 실행하세요.",
        icon=":material/construction:",
    )

master = load_master()
charge_annual = load_charge_annual()
year = int(st.session_state.selected_year)

try:
    kepco_station = load_kepco_station_annual()
    has_kepco = True
except FileNotFoundError:
    has_kepco = False
    kepco_station = pd.DataFrame()

tabs = st.tabs(
    [
        "설치 힌트 사분면",
        "급속·완속 구조 (차지인포)",
        "공공급속 활성기",
        "한전 충전소 수",
    ]
)

with tabs[0]:
    st.subheader("권역별 급속·완속 보급 강도 사분면")
    insight_callout(
        "읽는 방법",
        "가로=EV 1대당 **급속**, 세로=EV 1대당 **완속**(차지인포 8권역). "
        "중앙선은 해당 월 **중앙값**입니다. "
        "**설치 확정이 아니라** 상대 위치 힌트이며, 환경부 공공급속(17시도)과 합산하지 않습니다.",
        tone="warning",
    )
    if not has_chargeinfo_ev_ratio:
        st.info("차지인포 EV 1대당 보급률 데이터가 없습니다.")
    else:
        q_refs = sorted(chargeinfo_ev_wide["기준월"].unique(), reverse=True)
        q_ref = st.selectbox("사분면 기준월", q_refs, index=0, key="quadrant_ref")
        qdf = chargeinfo_ev_wide[chargeinfo_ev_wide["기준월"] == q_ref].copy()
        med_fast = float(qdf["급속_대당"].median())
        med_slow = float(qdf["완속_대당"].median())

        def _hint(row: pd.Series) -> str:
            hi_fast = row["급속_대당"] >= med_fast
            hi_slow = row["완속_대당"] >= med_slow
            if hi_fast and hi_완속:
                return "급·완속 모두 상대적 여유 → 유지·관망"
            if (not hi_fast) and hi_완속:
                return "완속 상대 여유·급속 상대 부족 → 급속/핫스팟 검토"
            if hi_fast and (not hi_slow):
                return "급속 상대 여유·완속 상대 부족 → 완속·거점 검토"
            return "급·완속 모두 상대적 낮음 → 수요·입지 추가 확인"

        qdf["설치힌트"] = qdf.apply(_hint, axis=1)
        scatter = (
            alt.Chart(qdf)
            .mark_circle(size=160)
            .encode(
                x=alt.X("급속_대당:Q", title="급속 (기/대)"),
                y=alt.Y("완속_대당:Q", title="완속 (기/대)"),
                color=alt.Color("설치힌트:N", title="힌트"),
                tooltip=[
                    "권역:N",
                    "급속_대당:Q",
                    "완속_대당:Q",
                    "완속급속강도비:Q",
                    "설치힌트:N",
                ],
            )
        )
        vline = (
            alt.Chart(pd.DataFrame({"급속_대당": [med_fast]}))
            .mark_rule(color="#94A3B8", strokeDash=[4, 4])
            .encode(x="급속_대당:Q")
        )
        hline = (
            alt.Chart(pd.DataFrame({"완속_대당": [med_slow]}))
            .mark_rule(color="#94A3B8", strokeDash=[4, 4])
            .encode(y="완속_대당:Q")
        )
        labels = (
            alt.Chart(qdf)
            .mark_text(align="left", dx=7, fontSize=11)
            .encode(x="급속_대당:Q", y="완속_대당:Q", text="권역:N")
        )
        st.altair_chart((scatter + vline + hline + labels).properties(height=420))
        st.dataframe(
            qdf[
                [
                    "권역",
                    "급속_대당",
                    "완속_대당",
                    "완속급속강도비",
                    "설치힌트",
                ]
            ].sort_values("권역"),
            hide_index=True,
            width="stretch",
        )
        st.caption(
            f"중앙값 — 급속 {med_급속:.2f} · 완속 {med_완속:.2f} 기/대. "
            "체크리스트는 아래 공공급속·한전 탭과 함께 보세요."
        )

with tabs[1]:
    st.subheader("차지인포 — 급속·완속 구축·보급 (8권역)")

    if has_chargeinfo_ev_ratio:
        st.markdown("#### 전기차 1대당 충전기 수 (기/대)")
        st.info(
            "숫자 = **전기차 1대당 충전기 대수**. "
            "괄호(%) = 8권역 비율값 합 대비 비중(산술구성비). "
            "**평균** = 8권역 산술평균(전국 EV 가중평균 아님). "
            "누적 대수와 단위가 다릅니다.",
            icon=":material/info:",
        )
        ratio_refs = sorted(chargeinfo_ev_wide["기준월"].unique(), reverse=True)
        selected_ratio_ref = st.selectbox(
            "보급률 스냅샷",
            ratio_refs,
            index=0,
            key="chargeinfo_ev_ratio_ref",
        )

        avg_plot = chargeinfo_ev_avg.copy()
        avg_plot["ref_date"] = pd.to_datetime(avg_plot["기준월"], format="%Y-%m")
        avg_plot["metric_ko"] = avg_plot["지표코드"].map(
            {
                "급속_대당": "급속",
                "완속_대당": "완속",
                "합계_대당": "합계",
            }
        )
        st.altair_chart(
            alt.Chart(avg_plot)
            .mark_line(point=True)
            .encode(
                x=alt.X("ref_date:T", title="기준월"),
                y=alt.Y("평균_대당충전기:Q", title="8권역 평균 (기/대)"),
                color=alt.Color(
                    "metric_ko:N",
                    title="구분",
                    scale=alt.Scale(
                        domain=["급속", "완속", "합계"],
                        range=["#DC2626", "#2563EB", "#64748B"],
                    ),
                ),
                tooltip=["기준월:N", "metric_ko:N", "평균_대당충전기:Q"],
            )
            .properties(height=300, title="8권역 산술평균 — EV 1대당 충전기")
        )

        snap = chargeinfo_ev_wide[
            chargeinfo_ev_wide["기준월"] == selected_ratio_ref
        ].sort_values("합계_대당", ascending=False)
        melt = snap.melt(
            id_vars=["권역"],
            value_vars=["급속_대당", "완속_대당"],
            var_name="지표코드",
            value_name="대당충전기",
        )
        melt["metric_ko"] = melt["지표코드"].map(
            {"급속_대당": "급속", "완속_대당": "완속"}
        )
        st.altair_chart(
            alt.Chart(melt)
            .mark_bar()
            .encode(
                x=alt.X("권역:N", sort="-y", title="권역"),
                y=alt.Y("대당충전기:Q", title="기/대"),
                color=alt.Color(
                    "metric_ko:N",
                    scale=alt.Scale(domain=["급속", "완속"], range=["#DC2626", "#2563EB"]),
                ),
                xOffset="metric_ko:N",
                tooltip=["권역:N", "metric_ko:N", "대당충전기:Q"],
            )
            .properties(height=340, title=f"{selected_ratio_ref} 권역별 EV 1대당 급속·완속")
        )

        latest_avg_fast = float(
            chargeinfo_ev_avg[
                (chargeinfo_ev_avg["기준월"] == selected_ratio_ref)
                & (chargeinfo_ev_avg["지표코드"] == "급속_대당")
            ]["평균_대당충전기"].iloc[0]
        )
        latest_avg_slow = float(
            chargeinfo_ev_avg[
                (chargeinfo_ev_avg["기준월"] == selected_ratio_ref)
                & (chargeinfo_ev_avg["지표코드"] == "완속_대당")
            ]["평균_대당충전기"].iloc[0]
        )
        intensity = latest_avg_slow / latest_avg_fast if latest_avg_fast else float("nan")
        st.caption(
            f"{selected_ratio_ref} 8권역 평균: 급속 **{latest_avg_급속:.2f}** · "
            f"완속 **{latest_avg_완속:.2f}** 기/대 "
            f"(완속/급속 강도 ≈ **{intensity:.1f}배**). "
            "제주·인천은 상대적으로 낮고, 강원은 급속 강도가 높습니다."
        )
        show_cols = [
            "권역",
            "급속_대당",
            "완속_대당",
            "합계_대당",
            "완속급속강도비",
            "급속비중",
            "완속비중",
        ]
        st.dataframe(snap[show_cols], hide_index=True, width="stretch")
        dataframe_download(
            chargeinfo_ev_wide,
            "chargeinfo_ev_per_charger_ratio_wide.csv",
            "EV 1대당 보급률 CSV",
        )
        st.markdown("---")

    if has_chargeinfo_monthly:
        ref_options = sorted(chargeinfo_monthly["기준월"].unique(), reverse=True)
        selected_ref = st.selectbox(
            "누적 대수 스냅샷",
            ref_options,
            index=0,
            key="chargeinfo_stock_ref",
        )

        nat_monthly = chargeinfo_monthly[
            (chargeinfo_monthly["권역"] == "전국")
        ].copy()
        nat_monthly["ref_date"] = pd.to_datetime(nat_monthly["기준월"], format="%Y-%m")

        st.markdown("#### 전국 급속·완속 누적 대수")
        st.altair_chart(
            alt.Chart(nat_monthly)
            .mark_line(point=True)
            .encode(
                x=alt.X("ref_date:T", title="기준월"),
                y=alt.Y("누적충전기:Q", title="누적 충전기 (기)", stack=None),
                color=alt.Color(
                    "충전속도:N",
                    title="충전속도",
                    scale=alt.Scale(domain=["급속", "완속"], range=["#DC2626", "#2563EB"]),
                ),
                tooltip=["기준월:N", "충전속도:N", "누적충전기:Q"],
            )
            .properties(height=320)
        )

        nat_ratio = chargeinfo_ratio[chargeinfo_ratio["권역"] == "전국"].copy()
        nat_ratio["ref_date"] = pd.to_datetime(nat_ratio["기준월"], format="%Y-%m")
        latest_nat_ratio = float(
            nat_ratio.sort_values("기준월")["완속급속비"].iloc[-1]
        )
        st.caption(
            f"최신 스냅샷({nat_ratio['기준월'].max()}) 전국 **완속/급속 누적 비율 ≈ {latest_nat_ratio:.1f}배** "
            "(완속 누적 ÷ 급속 누적)."
        )
        st.altair_chart(
            alt.Chart(nat_ratio)
            .mark_line(point=True, color="#7C3AED")
            .encode(
                x=alt.X("ref_date:T", title="기준월"),
                y=alt.Y("완속급속비:Q", title="완속/급속 (배)"),
                tooltip=["기준월:N", "완속급속비:Q", "급속비중:Q"],
            )
            .properties(height=240, title="전국 완속/급속 누적 비율")
        )

        st.markdown(f"#### {selected_ref} 권역별 누적 구조")
        snap_ratio = chargeinfo_ratio[
            (chargeinfo_ratio["기준월"] == selected_ref)
            & (chargeinfo_ratio["권역"] != "전국")
        ].sort_values("완속급속비", ascending=False)
        st.altair_chart(
            alt.Chart(snap_ratio)
            .mark_bar()
            .encode(
                x=alt.X("권역:N", sort="-y", title="권역"),
                y=alt.Y("완속급속비:Q", title="완속/급속 (배)"),
                color=alt.Color("급속비중:Q", title="급속 비중 %"),
                tooltip=[
                    "권역:N",
                    "완속:Q",
                    "급속:Q",
                    "완속급속비:Q",
                    "급속비중:Q",
                ],
            )
            .properties(height=340)
        )

        snap_stock = chargeinfo_monthly[
            (chargeinfo_monthly["기준월"] == selected_ref)
            & (chargeinfo_monthly["권역"] != "전국")
        ]
        st.altair_chart(
            alt.Chart(snap_stock)
            .mark_bar()
            .encode(
                x=alt.X("권역:N", sort="-y"),
                y=alt.Y("누적충전기:Q", title="누적 (기)"),
                color=alt.Color(
                    "충전속도:N",
                    scale=alt.Scale(domain=["급속", "완속"], range=["#DC2626", "#2563EB"]),
                ),
                xOffset="충전속도:N",
                tooltip=["권역:N", "충전속도:N", "누적충전기:Q"],
            )
            .properties(height=360, title="권역별 급속·완속 누적")
        )
        dataframe_download(
            chargeinfo_monthly,
            "chargeinfo_region_stock_monthly.csv",
            "차지인포 월별 누적 CSV",
        )

    elif not has_chargeinfo and not has_chargeinfo_ev_ratio:
        st.info(
            "`data/raw/chargeinfo/`에 원본을 넣고 전처리 스크립트를 실행하세요."
        )

    if has_chargeinfo:
        st.markdown("---")
        st.markdown("#### 연도별 누적 합계 (급속+완속, 연간 표)")
        st.warning(
            "2026년 연간 표는 **8월 11일까지** 누적입니다. 월별 xls(2025-12까지)와 기준 시점이 다릅니다.",
            icon=":material/event:",
        )
        national = chargeinfo_stock[chargeinfo_stock["권역"] == "전국"].copy()
        st.altair_chart(
            alt.Chart(national)
            .mark_line(point=True, color="#4F46E5")
            .encode(
                x=alt.X("연도:O", title="연도"),
                y=alt.Y("누적충전기:Q", title="누적 충전기 (기)"),
                tooltip=[
                    alt.Tooltip("연도:O", title="연도"),
                    alt.Tooltip("누적충전기:Q", title="누적(기)", format=","),
                    alt.Tooltip("기간상태:N", title="상태"),
                ],
            )
            .properties(height=280, title="전국 누적 (연간 합계 테이블)")
        )

        regions = chargeinfo_stock[chargeinfo_stock["권역"] != "전국"]
        latest = regions[regions["연도"] == regions["연도"].max()].sort_values(
            "누적충전기", ascending=False
        )
        st.altair_chart(
            alt.Chart(latest)
            .mark_bar()
            .encode(
                x=alt.X("권역:N", sort="-y", title="권역"),
                y=alt.Y("누적충전기:Q", title="누적 충전기 (기)"),
                color=alt.Color("전국대비비중:Q", title="전국 대비 %"),
            )
            .properties(height=300)
        )

        yoy_nat = chargeinfo_yoy[chargeinfo_yoy["권역"] == "전국"]
        st.altair_chart(
            alt.Chart(yoy_nat)
            .mark_bar(color="#0D9488")
            .encode(
                x=alt.X("연도:O", title="연도"),
                y=alt.Y("전년대비증감률:Q", title="YoY (%)"),
                tooltip=["연도:O", "전년대비증감률:Q", "기간상태:N"],
            )
            .properties(height=240)
        )

        pivot = chargeinfo_stock.pivot_table(
            index="권역",
            columns="연도",
            values="누적충전기",
            aggfunc="first",
        )
        st.dataframe(pivot, width="stretch")
        dataframe_download(
            chargeinfo_stock,
            "chargeinfo_region_stock_annual.csv",
            "차지인포 권역 연간 누적 CSV",
        )

    st.markdown(
        """
        **해석 메모**
        - **EV 1대당(기/대)**: 보급 강도. `(%)`는 8권역 비율합 대비 구성비, `평균`은 산술평균.
        - **누적 대수**: 급속·완속 **기 수**. 보급률과 단위·해석이 다릅니다.
        - 환경부 **공공급속 활성기**(17시도)와 권역·모집단이 다르므로 직접 비교·합산하지 않습니다.
        """
    )

with tabs[2]:
    st.subheader(f"{year}년 시·도별 공공급속 활성기·이용")
    active = master[master["연도"] == year][
        [
            "시도",
            "전기차등록대수",
            "활성충전기수",
            "EV천대당활성급속",
            "활성기당충전량",
            "충전량_kWh",
        ]
    ].dropna(subset=["활성충전기수"])
    active = active.sort_values("활성기당충전량", ascending=False)
    st.caption(
        "활성기당 충전량이 높은 지역은 **급속 이용 부담**이 큰 편입니다. "
        "EV 대비 활성기가 낮으면 급속 추가를 검토할 수 있습니다."
    )
    st.altair_chart(
        alt.Chart(active)
        .mark_bar()
        .encode(
            x=alt.X("시도:N", sort="-y", title="시·도"),
            y=alt.Y("활성기당충전량:Q", title="활성기당 kWh"),
            color=alt.Color("EV천대당활성급속:Q", title="EV천대당 활성기"),
        )
        .properties(height=380)
    )
    st.dataframe(active, hide_index=True)
    dataframe_download(active, f"public_fast_active_{year}.csv")

    if len(charge_annual):
        nat = charge_annual.groupby("연도", as_index=False).agg(
            charge_kwh_sum=("충전량_kWh", "sum"),
            active_charger_count=("활성충전기수", "sum"),
        )
        st.subheader("전국 공공급속 이용 추이")
        st.altair_chart(
            alt.Chart(nat)
            .mark_line(point=True)
            .encode(
                x=alt.X("연도:O", title="연도"),
                y=alt.Y("충전량_kWh:Q", title="충전량 (kWh)"),
                color=alt.value("#0F766E"),
            )
            .properties(height=300)
        )
        st.caption(
            "EV는 늘어도 공공급속 충전량이 정체·감소한 구간이 있어, "
            "**일상 충전은 완속·거점으로 이동**했을 가능성을 함께 읽어야 합니다."
        )

with tabs[3]:
    if not has_kepco:
        st.info("한전 충전소 현황 파일이 없습니다. `preprocess_kepco_aux.py`를 실행하세요.")
    else:
        st.subheader("한전 지역별 충전소 수 (연도별)")
        st.caption("한전망 충전소 **개소 수**입니다. 급속기 대수와 1:1은 아닙니다.")
        pivot = kepco_station.pivot_table(
            index="시도",
            columns="연도",
            values="충전소수",
            aggfunc="first",
        )
        pivot = pivot.reindex(SIDO_ORDER).dropna(how="all")
        st.dataframe(pivot, width="stretch")
        latest_year = int(kepco_station["연도"].max())
        latest = kepco_station[kepco_station["연도"] == latest_year].sort_values(
            "충전소수", ascending=False
        )
        st.altair_chart(
            alt.Chart(latest)
            .mark_bar(color="#64748B")
            .encode(
                x=alt.X("시도:N", sort="-y"),
                y=alt.Y("충전소수:Q", title=f"{latest_year}년 충전소 수"),
            )
            .properties(height=360)
        )
