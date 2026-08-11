"""Priority 3: national EV vs charger stock basics."""

import altair as alt
import pandas as pd
import streamlit as st

from charger_dashboard.data import (
    load_chargeinfo_region_stock,
    load_ev_monthly,
    load_master,
    national_year,
    percent_change,
)
from charger_dashboard.ui import dataframe_download, insight_callout, priority_banner

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
year = int(st.session_state.selected_year)

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

tabs = st.tabs(["연도별 총량", "월별 EV", "시·도 스냅샷", "데이터 기간 상태"])

with tabs[0]:
    chart_df = national.dropna(subset=["전기차등록대수"])
    left, right = st.columns(2)
    with left, st.container(border=True):
        st.markdown("**전기차 등록대수 (연말·전국)**")
        st.altair_chart(
            alt.Chart(chart_df)
            .mark_line(point=True, color="#2563EB")
            .encode(
                x=alt.X("연도:O", title="연도"),
                y=alt.Y("전기차등록대수:Q", title="등록대수 (대)"),
            )
            .properties(height=320)
        )
    with right, st.container(border=True):
        st.markdown("**활성 공공급속기 (연간·전국)**")
        st.altair_chart(
            alt.Chart(chart_df.dropna(subset=["활성충전기수"]))
            .mark_line(point=True, color="#D97706")
            .encode(
                x=alt.X("연도:O", title="연도"),
                y=alt.Y("활성충전기수:Q", title="활성기 (기)"),
            )
            .properties(height=320)
        )
    if has_chargeinfo:
        nat_ci = chargeinfo_stock[chargeinfo_stock["권역"] == "전국"]
        st.markdown("**차지인포 전국 누적 충전기 (급속+완속 합계)**")
        st.altair_chart(
            alt.Chart(nat_ci)
            .mark_line(point=True, color="#4F46E5")
            .encode(
                x=alt.X("연도:O", title="연도"),
                y=alt.Y("누적충전기:Q", title="누적 (기)"),
                tooltip=["연도:O", "누적충전기:Q", "기간상태:N"],
            )
            .properties(height=260)
        )
        st.caption("2026년은 연중 누적(partial)일 수 있습니다. 상세는 2순위 탭.")
    st.dataframe(
        national[
            [
                "연도",
                "전기차등록대수",
                "활성충전기수",
                "충전량_kWh",
                "관측월수",
                "기간상태",
            ]
        ],
        hide_index=True,
    )

with tabs[1]:
    nat_ev = (
        ev_monthly.groupby("기준월", as_index=False)["전기차등록대수"]
        .sum()
        .assign(date=lambda d: pd.to_datetime(d["기준월"], format="%Y-%m"))
    )
    st.altair_chart(
        alt.Chart(nat_ev)
        .mark_line(color="#2563EB")
        .encode(x="date:T", y=alt.Y("전기차등록대수:Q", title="전국 EV (대)"))
        .properties(height=360, title="월별 전국 전기차 등록대수")
    )

with tabs[2]:
    snapshot = master[master["연도"] == year][
        [
            "시도",
            "전기차등록대수",
            "활성충전기수",
            "EV천대당활성급속",
            "충전량_kWh",
            "기간상태",
        ]
    ].sort_values("전기차등록대수", ascending=False)
    st.dataframe(snapshot, hide_index=True)
    dataframe_download(snapshot, f"national_snapshot_{year}.csv")

with tabs[3]:
    st.markdown(
        """
        | 항목 | 기간·상태 |
        |---|---|
        | EV 등록 | 2019-01 ~ 2026-06 (연도는 연말, 없으면 최종월) |
        | 환경부 공공급속 충전량 | 2019-01 ~ 2025-08 · 2025는 **partial** |
        | 환경부 설치 재고 | ~2022 · 이후 `source_stale` |
        | 차지인포 누적 | 연간 표·월별 xls · 급·완속 분리 가능 |
        """
    )
    status_tbl = national[
        ["연도", "전기차등록대수", "충전량_kWh", "관측월수", "기간상태"]
    ].copy()
    st.dataframe(status_tbl, hide_index=True, width="stretch")
