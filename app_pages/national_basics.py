"""전국 EV·충전소 기초 총량 (3순위)."""

import pandas as pd
import streamlit as st

from charger_dashboard.data import (
    available_years,
    load_chargeinfo_region_stock,
    load_ev_monthly,
    load_master,
    national_year,
    percent_change,
)
from charger_dashboard.ui import (
    dataframe_download,
    insight_callout,
    priority_banner,
    year_selector,
)


def render() -> None:
    priority_banner(
        3,
        "전국 전기차·공공급속 **기초 총량**을 먼저 확인하는 화면입니다.",
    )

    insight_callout(
        "이 탭의 역할",
        "숫자의 **규모와 기간 상태**를 확인하는 기초 레이어입니다. "
        "해석·설치 판단은 1순위(이용)·2순위(급·완속)에서 이어 보세요.",
    )

    try:
        chargeinfo_stock = load_chargeinfo_region_stock()
        has_chargeinfo = True
    except FileNotFoundError:
        has_chargeinfo = False
        chargeinfo_stock = pd.DataFrame()

    master = load_master()
    ev_monthly = load_ev_monthly()
    year = year_selector(available_years(), key="basics_year")

    national_rows = []
    for y in sorted(master["연도"].dropna().unique()):
        row = national_year(master, int(y))
        row["연도"] = int(y)
        national_rows.append(row)
    national = pd.DataFrame(national_rows)

    current = national[national["연도"] == year].iloc[0]
    prev_row = national[national["연도"] == year - 1]
    previous = prev_row.iloc[0] if not prev_row.empty else pd.Series()

    st.subheader("전국 핵심 총량")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(
        "전기차 등록대수",
        f"{int(current['전기차등록대수']):,}대",
        f"{percent_change(current['전기차등록대수'], previous.get('전기차등록대수')):+.1f}%"
        if not prev_row.empty and pd.notna(previous.get("전기차등록대수"))
        else None,
    )
    c2.metric(
        "활성 공공급속기",
        f"{int(current['활성충전기수']):,}기"
        if pd.notna(current.get("활성충전기수"))
        else "—",
        f"{percent_change(current['활성충전기수'], previous.get('활성충전기수')):+.1f}%"
        if not prev_row.empty
        and pd.notna(current.get("활성충전기수"))
        and pd.notna(previous.get("활성충전기수"))
        else None,
    )
    if pd.notna(current.get("전기차등록대수")) and pd.notna(current.get("활성충전기수")):
        ratio = current["활성충전기수"] * 1000 / current["전기차등록대수"]
        c3.metric("EV 1,000대당 활성 급속기", f"{ratio:.2f}기")
    else:
        c3.metric("EV 1,000대당 활성 급속기", "—")
    c4.metric(
        "공공급속 충전량",
        f"{current['충전량_kWh']:,.0f} kWh"
        if pd.notna(current.get("충전량_kWh"))
        else "—",
        help="부분연도는 관측 월만 합산",
    )

    tabs = st.tabs(["연도별 총량", "월별 EV", "시·도 한눈에", "데이터 기간 상태"])

    with tabs[0]:
        chart_df = national.dropna(subset=["전기차등록대수"]).set_index("연도")
        left, right = st.columns(2)
        with left, st.container(border=True):
            st.markdown("**전기차 등록대수 (연말·전국)**")
            st.line_chart(chart_df[["전기차등록대수"]].rename(columns={"전기차등록대수": "등록대수 (대)"}))
        with right, st.container(border=True):
            st.markdown("**활성 공공급속기 (연간·전국)**")
            active = chart_df.dropna(subset=["활성충전기수"])[
                ["활성충전기수"]
            ].rename(columns={"활성충전기수": "활성기 (기)"})
            st.line_chart(active)
        if has_chargeinfo:
            nat_ci = (
                chargeinfo_stock[chargeinfo_stock["권역"] == "전국"]
                .set_index("연도")[["누적충전기"]]
                .rename(columns={"누적충전기": "누적 (기)"})
            )
            st.markdown("**차지인포 전국 누적 충전기 (급속+완속 합계)**")
            st.line_chart(nat_ci)
            st.caption("2026년은 연중 누적(partial)일 수 있습니다. 상세는 2순위 탭.")

    with tabs[1]:
        nat_ev = (
            ev_monthly.groupby("기준월", as_index=False)["전기차등록대수"]
            .sum()
            .assign(date=lambda d: pd.to_datetime(d["기준월"], format="%Y-%m"))
            .set_index("date")[["전기차등록대수"]]
            .rename(columns={"전기차등록대수": "전국 EV (대)"})
        )
        st.line_chart(nat_ev)

    with tabs[2]:
        st.caption(
            f"{year}년 시·도 규모를 **막대 길이**로 비교합니다. "
            "전기차·활성기·이용량을 바로 읽도록 구성했습니다."
        )
        snapshot = master[master["연도"] == year][
            [
                "시도",
                "전기차등록대수",
                "활성충전기수",
                "EV천대당활성급속",
                "충전량_kWh",
            ]
        ].dropna(subset=["전기차등록대수"]).sort_values("전기차등록대수", ascending=False)

        c_left, c_right = st.columns(2)
        with c_left, st.container(border=True):
            st.markdown("**전기차 등록대수**")
            st.bar_chart(
                snapshot.set_index("시도")[["전기차등록대수"]].rename(
                    columns={"전기차등록대수": "대"}
                ),
                horizontal=True,
            )
        with c_right, st.container(border=True):
            st.markdown("**활성 공공급속기**")
            st.bar_chart(
                snapshot.dropna(subset=["활성충전기수"])
                .set_index("시도")[["활성충전기수"]]
                .rename(columns={"활성충전기수": "기"}),
                horizontal=True,
            )

        pretty = snapshot.rename(
            columns={
                "시도": "시·도",
                "전기차등록대수": "전기차 (대)",
                "활성충전기수": "활성 급속기 (기)",
                "EV천대당활성급속": "EV천대당 활성기",
                "충전량_kWh": "공공급속 충전량 (kWh)",
            }
        )
        st.dataframe(
            pretty,
            hide_index=True,
            column_config={
                "시·도": st.column_config.TextColumn("시·도", pinned=True),
                "전기차 (대)": st.column_config.NumberColumn(format="localized"),
                "활성 급속기 (기)": st.column_config.NumberColumn(format="localized"),
                "EV천대당 활성기": st.column_config.NumberColumn(format="%.2f"),
                "공공급속 충전량 (kWh)": st.column_config.NumberColumn(format="localized"),
            },
        )
        dataframe_download(pretty, f"national_snapshot_{year}.csv")

    with tabs[3]:
        st.markdown(
            """
            | 항목 | 기간·상태 |
            |---|---|
            | EV 등록 | 2019-01부터 2026-06까지 (연도는 연말, 없으면 최종월) |
            | 환경부 공공급속 충전량 | 2019-01부터 2025-08까지 · 2025는 **partial** |
            | 환경부 설치 재고 | 2022년까지 · 이후 `source_stale` |
            | 차지인포 누적 | 연간 표·월별 xls · 급·완속 분리 가능 |
            """
        )
        status_tbl = national[
            ["연도", "전기차등록대수", "충전량_kWh", "관측월수", "기간상태"]
        ].copy()
        status_tbl["충전량_표시"] = status_tbl.apply(
            lambda r: (
                "집계 없음 (None) — 환경부 공공급속 충전량 원천 없음"
                if int(r["연도"]) >= 2026 or pd.isna(r["충전량_kWh"])
                else f"{r['충전량_kWh']:,.0f}"
            ),
            axis=1,
        )
        status_tbl["관측월수_표시"] = status_tbl.apply(
            lambda r: (
                "집계 없음 (None) — 충전량 관측월 없음"
                if int(r["연도"]) >= 2026 or pd.isna(r["관측월수"])
                else f"{int(r['관측월수'])}개월"
            ),
            axis=1,
        )
        show = status_tbl[
            ["연도", "전기차등록대수", "충전량_표시", "관측월수_표시", "기간상태"]
        ].rename(
            columns={
                "연도": "연도",
                "전기차등록대수": "전기차 등록대수",
                "충전량_표시": "충전량_kWh",
                "관측월수_표시": "관측월수",
                "기간상태": "기간 상태",
            }
        )
        st.dataframe(show, hide_index=True, width="stretch")
        st.caption(
            "2026년 충전량_kWh·관측월수는 환경부 공공급속 이용 원천이 없어 **None(집계 없음)** 으로 표시합니다."
        )
