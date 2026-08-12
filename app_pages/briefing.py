"""정책 우선순위 브리핑 (1순위 메인).

스토리:
  1) EV·급속기·충전량 → “충전기(급속)를 더 늘려야 한다” 신호
  2) 그럼 어디에 먼저? → 17시·도 지도(전체) + 8권역 보조
  3) 마치며 → 종합 인사이트
"""

import pandas as pd
import streamlit as st

from charger_dashboard.charts import burden_bar_frame, category_bar_chart, choropleth
from charger_dashboard.data import (
    METRIC_META,
    load_geojson,
    load_master,
    load_national_charge_ev_monthly,
    load_ytd_compare,
    rank_for_map,
)
from charger_dashboard.ui import priority_banner


def _col(df: pd.DataFrame, *names: str) -> str:
    for name in names:
        if name in df.columns:
            return name
    raise KeyError(f"컬럼 없음: {names} / 실제={list(df.columns)}")


def _pick_metric(*candidates: str) -> str:
    for name in candidates:
        if name in METRIC_META:
            return name
    raise KeyError(f"METRIC_META에 없음: {candidates}")


def _ytd_national(ytd: pd.DataFrame) -> dict:
    kwh_2024 = float(ytd[_col(ytd, "charge_kwh_2024_ytd", "충전량_2024_YTD")].sum())
    kwh_2025 = float(ytd[_col(ytd, "charge_kwh_2025_ytd", "충전량_2025_YTD")].sum())
    ev_2024 = float(ytd[_col(ytd, "ev_count_2024_ytd_avg", "EV_2024_YTD평균")].sum())
    ev_2025 = float(ytd[_col(ytd, "ev_count_2025_ytd_avg", "EV_2025_YTD평균")].sum())
    active_2024 = float(ytd[_col(ytd, "active_charger_2024_ytd", "활성기_2024_YTD")].sum())
    active_2025 = float(ytd[_col(ytd, "active_charger_2025_ytd", "활성기_2025_YTD")].sum())
    months = int(ytd[_col(ytd, "months_compared", "비교월수")].iloc[0]) if len(ytd) else 8
    ev_yoy = (ev_2025 / ev_2024 - 1) * 100 if ev_2024 else float("nan")
    active_yoy = (active_2025 / active_2024 - 1) * 100 if active_2024 else float("nan")
    kwh_yoy = (kwh_2025 / kwh_2024 - 1) * 100 if kwh_2024 else float("nan")
    return {
        "months": months,
        "ev_yoy": ev_yoy,
        "active_yoy": active_yoy,
        "kwh_yoy": kwh_yoy,
        "active_2025": active_2025,
        "kwh_2025": kwh_2025,
        "ev_2025": ev_2025,
    }


def _load_region8_latest():
    """차지인포 8권역 최신 급속 관련 스냅샷 (없으면 None)."""
    try:
        from charger_dashboard.data import (
            load_chargeinfo_ev_per_charger_wide,
            load_chargeinfo_slow_fast_ratio_monthly,
        )

        wide = load_chargeinfo_ev_per_charger_wide()
        slow_fast = load_chargeinfo_slow_fast_ratio_monthly()
    except Exception:
        return None

    # 컬럼 별칭
    ym_w = _col(wide, "ref_ym", "기준월")
    reg_w = _col(wide, "region_name", "권역")
    fast_per = _col(wide, "fast_per_ev", "급속_대당")

    ym_s = _col(slow_fast, "ref_ym", "기준월")
    reg_s = _col(slow_fast, "region_name", "권역")
    fast_n = _col(slow_fast, "fast", "급속")

    latest_w = wide[ym_w].max()
    latest_s = slow_fast[ym_s].max()
    w = wide[wide[ym_w] == latest_w].copy()
    s = slow_fast[slow_fast[ym_s] == latest_s].copy()
    w = w[w[reg_w] != "전국"]
    s = s[s[reg_s] != "전국"]

    merged = w[[reg_w, fast_per]].merge(
        s[[reg_s, fast_n]], left_on=reg_w, right_on=reg_s, how="inner"
    )
    merged = merged.rename(
        columns={reg_w: "권역", fast_per: "EV당 급속", fast_n: "급속 누적(기)"}
    )
    if "권역_y" in merged.columns:
        merged = merged.drop(columns=["권역_y"], errors="ignore")
    if reg_s in merged.columns and reg_s != "권역":
        merged = merged.drop(columns=[reg_s], errors="ignore")
    return merged, str(latest_w)


def render():
    priority_banner(
        1,
        "**정책·예산 우선순위** · 환경부 공공급속 기준으로 “늘려야 하나 / 어디에 먼저”를 봅니다.",
    )

    master = load_master()
    nat = load_national_charge_ev_monthly()
    ytd = load_ytd_compare()
    y = _ytd_national(ytd)

    c_nat_kwh = _col(nat, "charge_kwh_sum", "충전량_kWh")
    burden_metric = _pick_metric("kwh_per_active_charger", "활성기당충전량")
    supply_metric = _pick_metric("fast_per_1000_ev_active", "EV천대당활성급속")

    # =====================================================================
    # 1) 위: EV↑ · 급속기↑ · 실제 충전량 → 늘려야 한다
    # =====================================================================
    st.markdown("### 1. 전국 신호 — EV는 늘고, 급속은 따라가나?")
    st.caption(
        f"비교: **2024년 1–{y['months']}월 vs 2025년 1–{y['months']}월** (같은 기간). "
        "급속 충전기 대수 = 환경부 공공급속 **활성기**(그 기간 충전 실적이 있는 기기)."
    )

    m1, m2, m3 = st.columns(3)
    m1.metric(
        "EV 등록 증가율",
        f"{y['ev_yoy']:+.1f}%",
        help="국토부 전기차 등록(잠재 수요)",
        border=True,
    )
    m2.metric(
        "급속 충전기(활성) 증가율",
        f"{y['active_yoy']:+.1f}%",
        help="환경부 공공급속 활성기 수 증가율",
        border=True,
    )
    m3.metric(
        "공공급속 충전량(YTD)",
        f"{y['kwh_2025'] / 1e6:,.1f} GWh",
        delta=f"{y['kwh_yoy']:+.1f}%",
        help="환경부 공공급속망 실제 이용량",
        border=True,
    )

    g1, g2 = st.columns(2)
    with g1:
        st.markdown("**그래프 · 증가율 비교**")
        st.caption("막대 = 전년 동기간 대비 증감률(%). EV만 크게 솟으면 공급·이용이 못 따라간 신호입니다.")
        st.plotly_chart(
            category_bar_chart(
                pd.DataFrame(
                    {
                        "증감률(%)": [y["ev_yoy"], y["active_yoy"], y["kwh_yoy"]],
                    },
                    index=["EV 등록", "급속 활성기", "공공급속 충전량"],
                )
            ),
            use_container_width=True,
            config={"displayModeBar": False},
        )
    with g2:
        st.markdown("**그래프 · 실제 급속 충전량 추이**")
        st.caption("선 = 전국 환경부 공공급속 월별 충전량(kWh). 이용이 실제로 얼마나 나갔는지 봅니다.")
        nat_plot = nat.set_index("date")[[c_nat_kwh]].rename(columns={c_nat_kwh: "충전량 (kWh)"})
        st.line_chart(nat_plot)
        st.caption("참고: 2025년은 1–8월까지 관측.")

    st.warning(
        f"**인사이트 (위):** EV는 **{y['ev_yoy']:+.1f}%** 늘었는데 "
        f"공공급속 활성기는 **{y['active_yoy']:+.1f}%**, 충전량은 **{y['kwh_yoy']:+.1f}%**입니다. "
        f"수요 대비 급속 **용량·가동**이 부족해질 수 있어, "
        f"**공공급속 확충(대수·입지·가동)** 을 검토할 근거가 됩니다. "
        f"(현재 YTD 활성기 약 {y['active_2025']:,.0f}기 · 민간·완속 제외)",
        icon=":material/ev_station:",
    )

    st.divider()

    # =====================================================================
    # 2) 중간: 어디에 먼저? — 17시·도 전체 지도
    # =====================================================================
    st.markdown("### 2. 어디에 먼저 둘까 — 시·도 전체 지도")
    year = 2024
    st.caption(
        f"**{year}년 전체 17개 시·도**를 한눈에 봅니다. "
        "색이 진할수록 **활성기당 충전량**이 커서, 기기당 이용 부담이 큰 편입니다 "
        "→ 급속 확충·분산을 **우선 점검**할 후보. (설치 확정 아님)"
    )

    map_data = rank_for_map(master, year, burden_metric)
    if map_data.empty:
        st.warning(f"{year}년 지도 데이터가 없습니다.")
    else:
        geojson = load_geojson()
        map_col, bar_col = st.columns([1.2, 1])
        with map_col, st.container(border=True):
            st.markdown("**지도 · 활성기당 충전량 (17시·도 전체)**")
            st.plotly_chart(
                choropleth(geojson, map_data, burden_metric, year),
                use_container_width=True,
                config={"displayModeBar": False},
            )
            st.caption("진한 색 = 부담 큼. 모든 시·도가 포함됩니다.")
        with bar_col, st.container(border=True):
            st.markdown("**막대 · 같은 지표 전체 순위**")
            st.caption("막대가 길수록 활성기당 이용 부담이 큽니다.")
            st.bar_chart(burden_bar_frame(map_data, burden_metric), horizontal=True)

        # 상위·하위 인사이트 (전체 중)
        sido_col = "시도" if "시도" in map_data.columns else "sido_short"
        ranked = map_data.sort_values(burden_metric, ascending=False)
        top3 = ranked.head(3)[sido_col].tolist()
        bottom3 = ranked.tail(3)[sido_col].tolist()

        # 여력(활성기/EV)도 낮은 곳
        supply_data = rank_for_map(master, year, supply_metric)
        if not supply_data.empty:
            # supply: 낮을수록 빠듯 → ascending rank already
            s_col = "시도" if "시도" in supply_data.columns else "sido_short"
            tight = supply_data.nsmallest(5, supply_metric)[s_col].tolist()
            overlap = [s for s in top3 if s in tight]
        else:
            tight, overlap = [], []

        insight = (
            f"**인사이트 (중간):** 이용 부담이 큰 편인 시·도는 "
            f"**{', '.join(top3)}** 등입니다. "
        )
        if overlap:
            insight += (
                f"그중 EV 대비 활성기도 낮은 편인 곳(**{', '.join(overlap)}**)은 "
                f"급속 **우선 확충 점검** 후보로 볼 수 있습니다. "
            )
        insight += (
            f"상대적으로 부담이 작은 편은 **{', '.join(bottom3)}** 쪽입니다. "
            "전국을 같은 강도로 늘리기보다 **진한 지역부터** 보는 것이 효율적입니다."
        )
        st.info(insight, icon=":material/map:")

    # 8권역 보조 (차지인포 전체 급속 구축)
    region8 = _load_region8_latest()
    if region8 is not None:
        r8, as_of = region8
        with st.expander(f"보조 · 차지인포 8권역 급속 밀도 (기준 {as_of})", expanded=False):
            st.caption(
                "공공급속(위 지도)과 **다른 모집단**입니다. "
                "공공+민간 포함 전체 급속 구축의 EV당 급속기입니다. "
                "막대가 짧을수록 EV 대비 급속이 적은 권역입니다."
            )
            r8_plot = r8.set_index("권역")[["EV당 급속"]].sort_values("EV당 급속")
            st.plotly_chart(
                category_bar_chart(r8_plot),
                use_container_width=True,
                config={"displayModeBar": False},
            )
            low = r8.nsmallest(3, "EV당 급속")["권역"].tolist()
            st.caption(f"EV당 급속이 낮은 권역 예: {', '.join(low)}")

    st.divider()

    # =====================================================================
    # 3) 마치며 — 종합
    # =====================================================================
    st.markdown("### 3. 마치며 — 종합 인사이트")
    c1, c2, c3 = st.columns(3)
    with c1, st.container(border=True):
        st.markdown("**무엇을 봤나**")
        st.markdown(
            f"EV 증가({y['ev_yoy']:+.1f}%)가 "
            f"공공급속 활성({y['active_yoy']:+.1f}%)·이용({y['kwh_yoy']:+.1f}%)을 "
            "크게 앞섭니다."
        )
    with c2, st.container(border=True):
        st.markdown("**그래서**")
        st.markdown(
            "공공급속 **확충이 필요**한 신호입니다. "
            "다만 전국 일률이 아니라 **부담이 큰 시·도부터**."
        )
    with c3, st.container(border=True):
        st.markdown("**주의**")
        st.markdown(
            "이 화면은 **우선 점검 후보**입니다. "
            "예산 금액·민간·완속 전체 이용량은 포함하지 않습니다."
        )

    st.success(
        "**한 줄 정리:** 전기차 수요 증가에 맞춰 공공급속을 더 늘릴 필요는 있어 보이며, "
        "그 위치는 **활성기당 이용 부담이 큰 시·도(지도 진한 곳)** 부터 점검하는 것이 맞습니다.",
        icon=":material/flag:",
    )

    with st.expander("데이터 정의 · 한계", expanded=False):
        st.markdown(
            """
- **EV**: 국토부 등록대수  
- **급속 활성기**: 환경부 공공급속 중 충전 실적이 있는 기기 (설치 재고 ≠ 활성)  
- **충전량**: 환경부 공공급속 kWh (전국 모든 급속 이용량 아님)  
- **지도**: 2024년 시·도 전체, 활성기당 충전량  
- **8권역**: 차지인포 전체 급·완속(공공+민간) — 위 지도와 모집단이 다름  
- 2025 충전량은 1–8월(부분연도)
"""
        )

    st.caption("세부 필터·피크는 탐색 화면에서 이어 보세요.")
    l1, l2, l3 = st.columns(3)
    with l1:
        try:
            st.page_link("pages/01_시도_지도.py", label="지도 탐색", icon=":material/map:")
        except Exception:
            pass
    with l2:
        try:
            st.page_link("pages/02_급속_이용_추이.py", label="추이 탐색", icon=":material/timeline:")
        except Exception:
            pass
    with l3:
        try:
            st.page_link("pages/03_지역_상세.py", label="지역 상세", icon=":material/location_on:")
        except Exception:
            pass
