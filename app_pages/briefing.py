"""발표·정책 브리핑 (1순위).

타깃: 정책·예산 우선순위를 정하는 사람.
목표: 이 화면만으로 (1) 무슨 그래프인지 (2) 무엇이 어긋났는지 (3) 어디를 먼저 볼지 읽히게 한다.
차트: st.metric / st.bar_chart / st.line_chart 만 사용.
"""

import pandas as pd
import streamlit as st

from charger_dashboard.data import (
    load_master,
    load_national_charge_ev_monthly,
    load_ytd_compare,
)
from charger_dashboard.ui import priority_banner, scope_notice


def _col(df: pd.DataFrame, *names: str) -> str:
    for name in names:
        if name in df.columns:
            return name
    raise KeyError(f"컬럼 없음: {names} / 실제={list(df.columns)}")


def _ytd_national(ytd: pd.DataFrame) -> dict:
    kwh_2024 = float(ytd[_col(ytd, "charge_kwh_2024_ytd", "충전량_2024_YTD")].sum())
    kwh_2025 = float(ytd[_col(ytd, "charge_kwh_2025_ytd", "충전량_2025_YTD")].sum())
    ev_2024 = float(ytd[_col(ytd, "ev_count_2024_ytd_avg", "EV_2024_YTD평균")].sum())
    ev_2025 = float(ytd[_col(ytd, "ev_count_2025_ytd_avg", "EV_2025_YTD평균")].sum())
    active_2024 = float(ytd[_col(ytd, "active_charger_2024_ytd", "활성기_2024_YTD")].sum())
    active_2025 = float(ytd[_col(ytd, "active_charger_2025_ytd", "활성기_2025_YTD")].sum())
    months_col = _col(ytd, "months_compared", "비교월수")
    ev_yoy = (ev_2025 / ev_2024 - 1) * 100 if ev_2024 else float("nan")
    active_yoy = (active_2025 / active_2024 - 1) * 100 if active_2024 else float("nan")
    kwh_yoy = (kwh_2025 / kwh_2024 - 1) * 100 if kwh_2024 else float("nan")
    return {
        "ev_yoy": ev_yoy,
        "active_yoy": active_yoy,
        "kwh_yoy": kwh_yoy,
        "gap_ev_kwh": ev_yoy - kwh_yoy,
        "months": int(ytd[months_col].iloc[0]) if len(ytd) else 8,
    }


def _growth_index(nat: pd.DataFrame, ev_col: str, kwh_col: str, active_col: str | None) -> pd.DataFrame:
    """2019-01=100 지수. 세 지표 성장 속도를 한 차트에서 비교."""
    base = nat.iloc[0]
    out = pd.DataFrame({"date": nat["date"]})
    out["EV"] = nat[ev_col] / base[ev_col] * 100
    out["공공급속 충전량"] = nat[kwh_col] / base[kwh_col] * 100
    if active_col and active_col in nat.columns and pd.notna(base[active_col]) and base[active_col] > 0:
        out["활성 공공급속"] = nat[active_col] / base[active_col] * 100
    return out.set_index("date")


def _priority_table(master: pd.DataFrame, year: int) -> tuple[pd.DataFrame, list[str]]:
    c_year = _col(master, "year", "연도")
    c_sido = _col(master, "sido_short", "시도")
    c_status = _col(master, "data_status", "기간상태")
    c_burden = _col(master, "kwh_per_active_charger", "활성기당충전량")
    c_supply = _col(master, "fast_per_1000_ev_active", "EV천대당활성급속")
    c_ev = _col(master, "ev_count", "전기차등록대수")

    m = master[(master[c_year] == year) & (master[c_status] == "complete")].copy()
    m = m.dropna(subset=[c_burden, c_supply])
    if m.empty:
        return pd.DataFrame(), []

    burden_cut = m[c_burden].median()
    supply_cut = m[c_supply].median()

    rows = []
    for _, r in m.iterrows():
        high_burden = r[c_burden] >= burden_cut
        low_supply = r[c_supply] <= supply_cut
        if high_burden and low_supply:
            why = "이용 부담↑ · EV대비 활성기↓"
            priority = 1
        elif high_burden:
            why = "이용 부담이 중앙값 이상"
            priority = 2
        elif low_supply:
            why = "EV 대비 활성기가 중앙값 이하"
            priority = 3
        else:
            continue
        rows.append(
            {
                "우선": priority,
                "시·도": r[c_sido],
                "활성기당 충전량": r[c_burden],
                "EV천대당 활성기": r[c_supply],
                "EV 등록": r[c_ev],
                "점검 이유": why,
            }
        )

    table = pd.DataFrame(rows)
    if table.empty:
        return table, []
    table = table.sort_values(
        ["우선", "활성기당 충전량"], ascending=[True, False]
    ).head(7)
    overlap = table.loc[table["우선"] == 1, "시·도"].tolist()
    return table, overlap


def render():
    # ----- 헤더: 누구 · 무엇을 -----
    priority_banner(
        1,
        "**정책·예산 우선순위 점검**용 메인 화면 · 환경부 공공급속 기준",
    )
    st.markdown("#### 전기차는 늘었는데, 공공급속 정책도 같은 속도로 따라갔을까?")
    st.caption(
        f"범위: 국토부 EV · 환경부 공공급속(민간·완속 제외) · "
        "금액 편성이 아니라 **어디를 먼저 볼지**를 같은 정의로 보여 줍니다."
    )
    scope_notice()

    master = load_master()
    nat = load_national_charge_ev_monthly()
    ytd = load_ytd_compare()
    y = _ytd_national(ytd)

    c_nat_ev = _col(nat, "ev_count", "전기차등록대수")
    c_nat_kwh = _col(nat, "charge_kwh_sum", "충전량_kWh")
    c_nat_active = _col(nat, "active_charger_count", "활성충전기수")
    c_ytd_sido = _col(ytd, "sido_short", "시도")
    c_ytd_yoy = _col(ytd, "charge_kwh_ytd_yoy_pct", "충전량_YTD증감률")

    # ----- A. 결론 = KPI 3개 (서두 에세이 제거) -----
    st.markdown("### A. 최근 신호 — 증가율이 어긋남")
    st.caption(
        f"읽는 법: **2024년 1–{y['months']}월 vs 2025년 1–{y['months']}월** "
        "같은 기간끼리 비교한 전국 합산 증감률입니다."
    )

    k1, k2, k3, k4 = st.columns(4)
    k1.metric(
        "EV 등록",
        f"{y['ev_yoy']:+.1f}%",
        help="잠재 수요(국토부 등록) 증가율",
        border=True,
    )
    k2.metric(
        "활성 공공급속",
        f"{y['active_yoy']:+.1f}%",
        help="충전 실적이 있는 환경부 공공급속기 수 증가율",
        border=True,
    )
    k3.metric(
        "공공급속 충전량",
        f"{y['kwh_yoy']:+.1f}%",
        help="환경부 공공급속망 이용량(kWh) 증가율",
        border=True,
    )
    k4.metric(
        "수요−이용 격차",
        f"{y['gap_ev_kwh']:+.1f}%p",
        delta="EV 증가 − 충전량 증가",
        delta_color="inverse",
        help="클수록 수요 증가 대비 공공급속 이용 증가가 못 따라간 것",
        border=True,
    )

    left, right = st.columns([1.05, 1])
    with left:
        st.markdown("**그래프 1 · 세 지표 증가율 비교**")
        st.caption("막대가 길수록 전년 동기간 대비 더 크게 늘었다는 뜻입니다.")
        st.bar_chart(
            pd.DataFrame(
                {"증감률 (%)": [y["ev_yoy"], y["active_yoy"], y["kwh_yoy"]]},
                index=["① EV 등록", "② 활성 공공급속", "③ 공공급속 충전량"],
            )
        )
        st.info(
            f"**인사이트:** EV(+{y['ev_yoy']:.1f}%)는 크게 늘었지만 "
            f"공공급속 활성(+{y['active_yoy']:.1f}%)·충전량(+{y['kwh_yoy']:.1f}%)은 "
            f"약 +4%대입니다. → 총량 일률 확대만으로는 **체감·이용**이 안 따라갈 수 있습니다.",
            icon=":material/lightbulb:",
        )
    with right:
        st.markdown("**그래프 2 · 장기 성장 속도 (2019-01=100)**")
        st.caption("같은 출발점에서 보면 EV 선이 공공급속 이용·활성보다 가파릅니다.")
        idx = _growth_index(nat, c_nat_ev, c_nat_kwh, c_nat_active)
        st.line_chart(idx)
        st.caption("단위: 지수(100=2019년 1월). 2025년 충전량은 8월까지.")

    st.divider()

    # ----- B. 어디에 먼저 -----
    st.markdown("### B. 어디에 먼저 볼까 — 2024년 시·도 점검 후보")
    st.caption(
        "지표: **활성기당 충전량**(높을수록 기기당 이용 부담↑) · "
        "**EV천대당 활성기**(낮을수록 EV 대비 여력↓). "
        "중앙값 기준으로 ‘부담↑·여력↓’가 겹치면 1순위 후보입니다. 설치 확정이 아닙니다."
    )

    table, overlap = _priority_table(master, 2024)
    if table.empty:
        st.warning("2024년 완전연도 부담 지표가 없습니다.")
    else:
        chart_df = table.set_index("시·도")[["활성기당 충전량"]]
        col_chart, col_table = st.columns([1, 1.15])
        with col_chart:
            st.markdown("**그래프 3 · 점검 후보의 이용 부담**")
            st.caption("막대 = 활성기 1기당 연간 공공급속 충전량(kWh).")
            st.bar_chart(chart_df)
        with col_table:
            st.markdown("**점검 후보 표**")
            show = table.copy()
            show["우선"] = show["우선"].map({1: "● 1순위", 2: "○ 부담", 3: "○ 여력"})
            st.dataframe(
                show,
                hide_index=True,
                width="stretch",
                column_config={
                    "활성기당 충전량": st.column_config.NumberColumn(format="%.0f"),
                    "EV천대당 활성기": st.column_config.NumberColumn(format="%.1f"),
                    "EV 등록": st.column_config.NumberColumn(format="localized"),
                },
            )

        if overlap:
            st.warning(
                f"**인사이트:** 부담↑·여력↓가 겹치는 곳 → **{', '.join(overlap)}**. "
                "공공급속 확충·입지·가동을 **우선 점검**할 후보입니다 "
                "(민간·완속은 이 숫자에 없음).",
                icon=":material/priority_high:",
            )
        else:
            st.info(
                "**인사이트:** 전국 일률보다 시·도별 이용 부담을 보고 현장 점검 후보를 고르세요.",
                icon=":material/lightbulb:",
            )

    # 지역 비대칭 (한 줄 + 작은 차트)
    with st.expander("참고 · 공공급속 충전량 YTD가 늘/준 시·도", expanded=False):
        st.caption("전국 +4% 안에도 지역은 반대 방향일 수 있습니다 → 차등 검토 근거.")
        ytd_sorted = ytd.sort_values(c_ytd_yoy, ascending=False)
        u, d = st.columns(2)
        with u:
            st.markdown("증가 상위 3")
            up = ytd_sorted.head(3)[[c_ytd_sido, c_ytd_yoy]]
            st.bar_chart(up.set_index(c_ytd_sido).rename(columns={c_ytd_yoy: "%"}))
        with d:
            st.markdown("감소·하위 3")
            down = ytd_sorted.tail(3)[[c_ytd_sido, c_ytd_yoy]]
            st.bar_chart(down.set_index(c_ytd_sido).rename(columns={c_ytd_yoy: "%"}))

    st.divider()

    # ----- C. 그래서 무엇을 -----
    st.markdown("### C. 정책에 쓸 때 — 이 대시보드가 말하는 것")
    a, b, c = st.columns(3)
    with a, st.container(border=True):
        st.markdown("**1. 무엇을 봤나**")
        st.markdown(
            "수요(EV) 증가와 공공급속 **이용·활성** 증가가 어긋납니다."
        )
    with b, st.container(border=True):
        st.markdown("**2. 어디에 쓰나**")
        st.markdown(
            "총량 일률이 아니라 **부담·여력 기준 지역 차등 점검**에 쓰세요."
        )
    with c, st.container(border=True):
        st.markdown("**3. 무엇은 아닌가**")
        st.markdown(
            "예산 **금액** 산출·전국 충전 전체·설치 확정 권고가 아닙니다."
        )

    with st.expander("데이터 정의 · 한계 (필요할 때만)", expanded=False):
        st.markdown(
            """
| 지표 | 정의 | 주의 |
|---|---|---|
| EV 등록 | 국토부 전기차 등록대수 | 잠재 수요 |
| 공공급속 충전량 | 환경부 공공 **급속** kWh | 전국 모든 충전기 이용량 아님 |
| 활성 충전기 | 기간 중 충전 실적 있는 기기 | 설치 대수와 다름 |
| 활성기당 충전량 | 충전량 ÷ 활성기 | 17시·도 **상대** 비교 |
| YTD | 2024·2025 동일 1–N월 | 2025는 부분연도 |
"""
        )
        st.caption("2023년 이후 설비 설치 재고 원천은 갱신 제한 → 활성기 지표를 사용합니다.")

    st.caption("더 깊게 보려면 탐색 화면으로 이동하세요.")
    l1, l2, l3 = st.columns(3)
    with l1:
        try:
            st.page_link("pages/01_시도_지도.py", label="지도로 부담 보기", icon=":material/map:")
        except Exception:
            st.caption("시·도 지도")
    with l2:
        try:
            st.page_link(
                "pages/02_급속_이용_추이.py", label="월별 추이 탐색", icon=":material/timeline:"
            )
        except Exception:
            st.caption("급속 이용 추이")
    with l3:
        try:
            st.page_link("pages/03_지역_상세.py", label="한 지역 자세히", icon=":material/location_on:")
        except Exception:
            st.caption("지역 상세")
