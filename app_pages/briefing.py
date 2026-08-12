"""발표용 정책 브리핑.

스토리:
  1) EV·공공급속 이용이 어긋나는가 → 늘릴 필요는 있는가
  2) 이용은 많은데 급속 여력·비중이 낮은 곳은 어디인가
  3) 종합 결론
"""

import pandas as pd
import streamlit as st

from charger_dashboard.charts import (
    burden_bar_frame,
    category_bar_chart,
    choropleth,
    dual_axis_line,
)
from charger_dashboard.data import (
    METRIC_META,
    load_geojson,
    load_master,
    load_national_charge_ev_monthly,
    load_ytd_compare,
    rank_for_map,
)


def _col(df, *names):
    for name in names:
        if name in df.columns:
            return name
    raise KeyError(f"컬럼 없음: {names} / 실제={list(df.columns)}")


def _pick_metric(*candidates):
    for name in candidates:
        if name in METRIC_META:
            return name
    raise KeyError(f"METRIC_META에 없음: {candidates}")


def _period_compare(ytd):
    """같은 달 구간(1–N월) 전년 대비. YTD라는 말은 화면에 쓰지 않음."""
    kwh_2024 = float(ytd[_col(ytd, "charge_kwh_2024_ytd", "충전량_2024_YTD")].sum())
    kwh_2025 = float(ytd[_col(ytd, "charge_kwh_2025_ytd", "충전량_2025_YTD")].sum())
    ev_2024 = float(ytd[_col(ytd, "ev_count_2024_ytd_avg", "EV_2024_YTD평균")].sum())
    ev_2025 = float(ytd[_col(ytd, "ev_count_2025_ytd_avg", "EV_2025_YTD평균")].sum())
    active_2024 = float(ytd[_col(ytd, "active_charger_2024_ytd", "활성기_2024_YTD")].sum())
    active_2025 = float(ytd[_col(ytd, "active_charger_2025_ytd", "활성기_2025_YTD")].sum())
    months = int(ytd[_col(ytd, "months_compared", "비교월수")].iloc[0]) if len(ytd) else 8
    return {
        "months": months,
        "ev_yoy": (ev_2025 / ev_2024 - 1) * 100 if ev_2024 else float("nan"),
        "active_yoy": (active_2025 / active_2024 - 1) * 100 if active_2024 else float("nan"),
        "kwh_yoy": (kwh_2025 / kwh_2024 - 1) * 100 if kwh_2024 else float("nan"),
        "active_2025": active_2025,
        "kwh_2025": kwh_2025,
    }


def _fast_stock_snapshot():
    """차지인포: 완속 제외하고 급속이 전체에서 차지하는 비중."""
    try:
        from charger_dashboard.data import load_chargeinfo_slow_fast_ratio_monthly

        sf = load_chargeinfo_slow_fast_ratio_monthly()
    except Exception:
        return None

    ym = _col(sf, "ref_ym", "기준월")
    reg = _col(sf, "region_name", "권역")
    share = _col(sf, "fast_share_pct", "급속비중")
    fast = _col(sf, "fast", "급속")
    slow = _col(sf, "slow", "완속")
    ratio = _col(sf, "slow_fast_ratio", "완속급속비")

    latest = sf[ym].max()
    snap = sf[sf[ym] == latest].copy()
    nat = snap[snap[reg] == "전국"]
    regions = snap[snap[reg] != "전국"].copy()
    if nat.empty or regions.empty:
        return None

    row = nat.iloc[0]
    return {
        "as_of": str(latest),
        "fast_share": float(row[share]),
        "slow_fast": float(row[ratio]),
        "fast": float(row[fast]),
        "slow": float(row[slow]),
        "regions": regions.rename(
            columns={reg: "권역", share: "급속 비중(%)", fast: "급속(기)", slow: "완속(기)"}
        ),
    }


def _sido_col(df):
    for name in ("시도", "sido_short", "sido"):
        if name in df.columns:
            return name
    raise KeyError("시·도 컬럼이 없습니다.")


def _year_col(df):
    for name in ("연도", "year"):
        if name in df.columns:
            return name
    raise KeyError("연도 컬럼이 없습니다.")


def render():
    master = load_master()
    nat = load_national_charge_ev_monthly().copy()
    cmp = _period_compare(load_ytd_compare())
    fast_stock = _fast_stock_snapshot()

    if "date" not in nat.columns:
        ym = _col(nat, "year_month", "기준월")
        nat["date"] = pd.to_datetime(nat[ym], format="%Y-%m")
    c_date = "date"
    c_ev = _col(nat, "ev_count", "전기차등록대수")
    c_kwh = _col(nat, "charge_kwh_sum", "충전량_kWh")

    burden_metric = _pick_metric("kwh_per_active_charger", "활성기당충전량")
    volume_metric = _pick_metric("charge_kwh_sum", "충전량_kWh")
    supply_metric = _pick_metric("fast_per_1000_ev_active", "EV천대당활성급속")

    # ------------------------------------------------------------------
    # 1) 전국 신호
    # ------------------------------------------------------------------
    st.markdown("### 1. 늘려야 하나 — EV와 공공급속 이용")
    st.caption(
        f"비교 구간: 2024년 1–{cmp['months']}월 vs 2025년 1–{cmp['months']}월. "
        "급속 = 환경부 공공급속 활성기(충전 실적 있는 기기)."
    )

    m1, m2, m3 = st.columns(3)
    m1.metric("전기차 등록", f"{cmp['ev_yoy']:+.1f}%", border=True)
    m2.metric("공공급속 활성기", f"{cmp['active_yoy']:+.1f}%", border=True)
    m3.metric(
        "공공급속 충전량",
        f"{cmp['kwh_yoy']:+.1f}%",
        help=f"같은 기간 합계 약 {cmp['kwh_2025'] / 1e6:,.1f} GWh",
        border=True,
    )

    with st.container(border=True):
        st.markdown("**전기차 등록 · 공공급속 충전량 (월별)**")
        st.caption("왼쪽=전기차 등록대수, 오른쪽=환경부 공공급속 충전량(kWh). 간격이 벌어질수록 수요가 이용·공급을 앞선 신호입니다.")
        dual_df = nat[[c_date, c_ev, c_kwh]].rename(
            columns={c_ev: "전기차", c_kwh: "충전량"}
        )
        st.plotly_chart(
            dual_axis_line(
                dual_df,
                c_date,
                "전기차",
                "충전량",
                left_name="전기차 (대)",
                right_name="공공급속 충전량 (kWh)",
                height=460,
            ),
            use_container_width=True,
            config={"displayModeBar": False},
        )

    if fast_stock is not None:
        f1, f2, f3 = st.columns(3)
        f1.metric(
            "전국 급속 비중",
            f"{fast_stock['fast_share']:.1f}%",
            help="차지인포 전체 구축(공공+민간)에서 급속 비율",
            border=True,
        )
        f2.metric("완속 : 급속", f"{fast_stock['slow_fast']:.1f} : 1", border=True)
        f3.metric(
            "급속 누적",
            f"{fast_stock['fast']:,.0f}기",
            help=f"기준 {fast_stock['as_of']} · 완속 제외 판단용",
            border=True,
        )
        st.caption(
            f"차지인포 기준(공공+민간) 급속은 전체의 약 **{fast_stock['fast_share']:.0f}%**뿐입니다. "
            "완속은 판단에서 빼고, **급속 비중**으로 보면 급속 확충 논의가 더 분명해집니다."
        )

    st.info(
        f"**인사이트:** 전기차는 **{cmp['ev_yoy']:+.1f}%** 늘었는데 "
        f"공공급속 활성기는 **{cmp['active_yoy']:+.1f}%**, 충전량은 **{cmp['kwh_yoy']:+.1f}%**입니다. "
        "수요가 이용·공급을 앞서므로 **공공급속을 더 늘릴 필요**가 있습니다.",
        icon=":material/ev_station:",
    )

    st.divider()

    # ------------------------------------------------------------------
    # 2) 어디에 먼저
    # ------------------------------------------------------------------
    st.markdown("### 2. 어디에 먼저 — 이용 부담과 급속 비중")

    year_col = _year_col(master)
    year_opts = sorted(
        int(y) for y in master[year_col].dropna().unique() if 2019 <= int(y) <= 2025
    )
    default_year = 2024 if 2024 in year_opts else year_opts[-1]

    ctrl1, ctrl2 = st.columns([1, 2])
    with ctrl1:
        year = st.selectbox("지도 연도", year_opts, index=year_opts.index(default_year))
    with ctrl2:
        metric_label = st.radio(
            "지도·순위 지표",
            [
                "이용 부담 (활성기당 충전량)",
                "총 충전량",
                "급속 여력 (EV천대당 활성기)",
            ],
            horizontal=True,
            help="이용이 큰데 여력이 낮은 곳이 우선 점검 후보입니다.",
        )

    if metric_label.startswith("이용 부담"):
        map_metric = burden_metric
        metric_help = (
            "색이 진할수록 **활성기당 충전량**이 커서, 기기당 이용 부담이 큰 편입니다 "
            "→ 급속 확충·분산을 우선 점검할 후보."
        )
        high_is_priority = True
    elif metric_label.startswith("총 충전량"):
        map_metric = volume_metric
        metric_help = (
            "색이 진할수록 **공공급속 총 충전량**이 많습니다. "
            "이용이 몰리는 시·도부터 용량을 볼 때 씁니다."
        )
        high_is_priority = True
    else:
        map_metric = supply_metric
        metric_help = (
            "색이 진할수록 EV 대비 활성기가 **많습니다(여력↑)**. "
            "반대로 **옅은 곳**이 급속 여력이 빠듯한 후보입니다."
        )
        high_is_priority = False

    st.caption(metric_help)
    if year == 2025:
        st.caption("2025년은 1–8월 관측입니다. 완전연도와 직접 비교하지 마세요.")

    map_data = rank_for_map(master, year, map_metric)
    if map_data.empty:
        st.warning(f"{year}년 지도 데이터가 없습니다.")
        top_priority = []
        bottom_ref = []
    else:
        geojson = load_geojson()
        map_col, bar_col = st.columns([1.25, 1])
        with map_col, st.container(border=True):
            st.markdown("**시·도 지도**")
            st.plotly_chart(
                choropleth(geojson, map_data, map_metric, year),
                use_container_width=True,
                config={"displayModeBar": False},
            )
        with bar_col, st.container(border=True):
            st.markdown("**같은 지표 순위**")
            st.bar_chart(burden_bar_frame(map_data, map_metric), horizontal=True)

        sido = _sido_col(map_data)
        if high_is_priority:
            ranked = map_data.sort_values(map_metric, ascending=False)
            top_priority = ranked.head(3)[sido].tolist()
            bottom_ref = ranked.tail(3)[sido].tolist()
        else:
            ranked = map_data.sort_values(map_metric, ascending=True)
            top_priority = ranked.head(3)[sido].tolist()
            bottom_ref = ranked.tail(3)[sido].tolist()

        # 교차: 이용 부담 상위 ∩ 급속 여력 하위
        burden_data = rank_for_map(master, year, burden_metric)
        supply_data = rank_for_map(master, year, supply_metric)
        overlap = []
        if not burden_data.empty and not supply_data.empty:
            b_col = _sido_col(burden_data)
            s_col = _sido_col(supply_data)
            high_use = set(burden_data.nlargest(5, burden_metric)[b_col])
            low_supply = set(supply_data.nsmallest(5, supply_metric)[s_col])
            overlap = [s for s in high_use if s in low_supply]

        insight2 = (
            f"**인사이트:** 선택 지표 기준 우선 후보는 **{', '.join(top_priority)}** 쪽입니다. "
        )
        if overlap:
            insight2 += (
                f"이용 부담은 큰데 EV 대비 활성기가 적은 곳(**{', '.join(overlap)}**)은 "
                f"**사용량은 많고 급속 여력은 상대적으로 낮은** 패턴이라 먼저 볼 만합니다. "
            )
        insight2 += f"상대적으로 여유 있는 편은 **{', '.join(bottom_ref)}**입니다."
        st.info(insight2, icon=":material/map:")

    # 급속 비중 — expander 없이 바로 노출
    if fast_stock is not None:
        st.markdown("**급속 비중 (완속 제외 판단)**")
        st.caption(
            "차지인포 전체 구축에서 **급속만** 본 비중입니다. "
            "비중이 낮을수록 같은 규모 대비 급속이 얇습니다. (공공급속 지도와 모집단이 다름)"
        )
        r8 = (
            fast_stock["regions"]
            .set_index("권역")[["급속 비중(%)"]]
            .sort_values("급속 비중(%)")
        )
        left, right = st.columns([1.4, 1])
        with left, st.container(border=True):
            st.plotly_chart(
                category_bar_chart(r8),
                use_container_width=True,
                config={"displayModeBar": False},
            )
        with right, st.container(border=True):
            low3 = fast_stock["regions"].nsmallest(3, "급속 비중(%)")["권역"].tolist()
            st.markdown(
                f"급속 비중이 낮은 권역: **{', '.join(low3)}**\n\n"
                f"전국 급속 비중 **{fast_stock['fast_share']:.1f}%** "
                f"(완속:급속 ≈ {fast_stock['slow_fast']:.1f}:1).\n\n"
                "완속을 빼고 급속 비중으로 보면, "
                "**비중이 낮은 권역에 급속을 먼저 보강**하는 판단이 설득력을 갖습니다."
            )

    st.divider()

    # ------------------------------------------------------------------
    # 3) 종합 결론 (카드/링크/한줄정리 제거)
    # ------------------------------------------------------------------
    st.markdown("### 3. 종합")
    where = ", ".join(top_priority) if top_priority else "이용 부담이 큰 시·도"
    share_txt = (
        f"차지인포 급속 비중(전국 약 {fast_stock['fast_share']:.0f}%)"
        if fast_stock is not None
        else "차지인포 급속 비중"
    )
    st.success(
        f"**국토부 전기차 증가(+{cmp['ev_yoy']:.1f}%), "
        f"환경부 공공급속 이용·활성기(+{cmp['kwh_yoy']:.1f}% / +{cmp['active_yoy']:.1f}%), "
        f"{share_txt}**을 종합하면, "
        f"수요 대비 급속 확충이 필요하고 "
        f"**이용은 많은데 급속 여력·비중이 상대적으로 낮은 곳({where})부터** "
        f"먼저 설치·보강하는 것이 바람직하다고 봅니다.",
        icon=":material/flag:",
    )
