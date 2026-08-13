"""발표용 정책 브리핑.

스토리: 전국 괴리 → 부담 지도 → 신호 겹침 → 우선 점검.
시연: 연도·지표를 바꿔 발표와 같은 그래프를 다시 본다.
"""

import pandas as pd
import streamlit as st

from charger_dashboard.charts import (
    COLORS,
    burden_bar_frame,
    category_bar_chart,
    choropleth,
    dual_axis_line,
    paired_year_bars,
    sido_hbar,
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
        "ev_2024": ev_2024,
        "ev_2025": ev_2025,
        "active_2024": active_2024,
        "active_2025": active_2025,
        "kwh_2024": kwh_2024,
        "kwh_2025": kwh_2025,
        "ev_yoy": (ev_2025 / ev_2024 - 1) * 100 if ev_2024 else float("nan"),
        "active_yoy": (active_2025 / active_2024 - 1) * 100 if active_2024 else float("nan"),
        "kwh_yoy": (kwh_2025 / kwh_2024 - 1) * 100 if kwh_2024 else float("nan"),
    }


def _fast_stock_snapshot():
    """차지인포: 완속 제외하고 급속이 전체에서 차지하는 비중. 본편 결론 KPI가 아님."""
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


def _q4_signals(master, year, year_col, sido_col, burden_col):
    """선택 연도 부담 상위 ~25%(Q4)의 기당 kWh · EV/기 · 3년 CAGR."""
    year_df = master[master[year_col] == year].dropna(subset=[burden_col, sido_col]).copy()
    if year_df.empty:
        return pd.DataFrame()
    year_df["ev_per_active"] = year_df["ev_count"] / year_df["active_charger_count"]
    n = len(year_df)
    year_df["burden_rank"] = year_df[burden_col].rank(ascending=False, method="min")
    q4 = year_df[year_df["burden_rank"] <= max(1, round(n * 0.25))].copy()

    prev = master[master[year_col] == year - 3][[sido_col, "ev_count"]].rename(
        columns={"ev_count": "ev_then"}
    )
    q4 = q4.merge(prev, on=sido_col, how="left")
    q4["cagr"] = (q4["ev_count"] / q4["ev_then"]) ** (1 / 3) - 1
    return q4.sort_values(burden_col, ascending=False)


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

    st.caption(
        "발표 뒤 시연: 아래 연도·지표를 바꾸면 같은 정의로 지도와 순위를 다시 볼 수 있습니다. "
        "실제 가동 충전기 = 충전 기록이 있는 공공급속."
    )

    # ------------------------------------------------------------------
    # 1) 전국 괴리 (발표 차트와 같은 읽기)
    # ------------------------------------------------------------------
    st.markdown("### 1. 전국 괴리 — EV와 공공급속")
    st.caption(
        f"비교 구간: 2024년 1–{cmp['months']}월 vs 2025년 1–{cmp['months']}월. "
        "실제 가동 = 환경부 공공급속 중 충전 실적이 있는 기기."
    )

    m1, m2, m3 = st.columns(3)
    m1.metric("전기차 등록", f"{cmp['ev_yoy']:+.1f}%", border=True)
    m2.metric("실제 가동", f"{cmp['active_yoy']:+.1f}%", border=True)
    m3.metric(
        "공공급속 충전량",
        f"{cmp['kwh_yoy']:+.1f}%",
        help=f"같은 기간 합계 약 {cmp['kwh_2025'] / 1e6:,.1f} GWh",
        border=True,
    )

    b1, b2, b3 = st.columns(3)
    with b1, st.container(border=True):
        st.markdown("**전기차 등록**")
        st.plotly_chart(
            paired_year_bars(cmp["ev_2024"], cmp["ev_2025"], yoy_pct=cmp["ev_yoy"], unit="대"),
            use_container_width=True,
            config={"displayModeBar": False},
        )
    with b2, st.container(border=True):
        st.markdown("**실제 가동**")
        st.plotly_chart(
            paired_year_bars(
                cmp["active_2024"], cmp["active_2025"], yoy_pct=cmp["active_yoy"], unit="기"
            ),
            use_container_width=True,
            config={"displayModeBar": False},
        )
    with b3, st.container(border=True):
        st.markdown("**공공급속 충전량**")
        st.plotly_chart(
            paired_year_bars(
                cmp["kwh_2024"] / 1e6,
                cmp["kwh_2025"] / 1e6,
                yoy_pct=cmp["kwh_yoy"],
                unit="GWh",
            ),
            use_container_width=True,
            config={"displayModeBar": False},
        )

    with st.container(border=True):
        st.markdown("**월별 추이 (연도·월을 따라가며 보기)**")
        st.caption("왼쪽=전기차 등록, 오른쪽=공공급속 충전량. 간격이 벌어질수록 수요가 이용을 앞선 신호입니다.")
        dual_df = nat[[c_date, c_ev, c_kwh]].rename(columns={c_ev: "전기차", c_kwh: "충전량"})
        st.plotly_chart(
            dual_axis_line(
                dual_df,
                c_date,
                "전기차",
                "충전량",
                left_name="전기차 (대)",
                right_name="공공급속 충전량 (kWh)",
                height=420,
            ),
            use_container_width=True,
            config={"displayModeBar": False},
        )

    st.info(
        f"**읽을 점:** 전기차는 **{cmp['ev_yoy']:+.1f}%** 늘었는데 "
        f"실제 가동은 **{cmp['active_yoy']:+.1f}%**, 충전량은 **{cmp['kwh_yoy']:+.1f}%**입니다. "
        "총량만으로 충분을 단정하기 어렵습니다.",
        icon=":material/ev_station:",
    )

    st.divider()

    # ------------------------------------------------------------------
    # 2) 어디에 먼저 — 지도 (시연 핵심)
    # ------------------------------------------------------------------
    st.markdown("### 2. 어디에 먼저 — 이용 부담 지도")
    st.caption("이용 부담 = 실제 가동 1기당 충전량. Q4 = 17시·도 중 상위 약 25%.")

    year_col = _year_col(master)
    sido_col_m = _sido_col(master)
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
                "이용 부담 (가동 1기당 충전량)",
                "총 충전량",
                "급속 여력 (EV천대당 실제 가동)",
            ],
            horizontal=True,
            help="발표 본편은 이용 부담입니다. 여력은 반대로 옅은 곳이 빠듯합니다.",
        )

    if metric_label.startswith("이용 부담"):
        map_metric = burden_metric
        metric_help = "색이 진할수록 가동 1기당 충전량이 큽니다 → 우선 점검 후보."
        high_is_priority = True
    elif metric_label.startswith("총 충전량"):
        map_metric = volume_metric
        metric_help = "색이 진할수록 공공급속 총 충전량이 많습니다."
        high_is_priority = True
    else:
        map_metric = supply_metric
        metric_help = "색이 진할수록 EV 대비 실제 가동이 많습니다. **옅은 곳**이 여력이 빠듯합니다."
        high_is_priority = False

    st.caption(metric_help)
    if year == 2025:
        st.caption("2025년은 1–8월 관측입니다. 완전연도와 직접 비교하지 마세요.")

    map_data = rank_for_map(master, year, map_metric)
    top_priority = []
    bottom_ref = []
    if map_data.empty:
        st.warning(f"{year}년 지도 데이터가 없습니다.")
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
        ranked = map_data.sort_values(map_metric, ascending=not high_is_priority)
        top_priority = ranked.head(5)[sido].tolist()
        bottom_ref = ranked.tail(3)[sido].tolist()

        st.info(
            f"**읽을 점:** {year}년 선택 지표 상위는 **{', '.join(top_priority)}**입니다. "
            f"상대적으로 낮은 편은 **{', '.join(bottom_ref)}**입니다.",
            icon=":material/map:",
        )

    # ------------------------------------------------------------------
    # 2b) 신호 겹침 — 발표 evidence 차트와 같은 세 막대
    # ------------------------------------------------------------------
    q4 = _q4_signals(master, year, year_col, sido_col_m, burden_metric)
    if not q4.empty:
        st.markdown(f"### 신호가 겹치는가 — {year}년 부담 Q4")
        st.caption(
            "한 지표만 보지 않습니다. 기당 충전량 · EV/실제 가동 1기 · EV 3년 연평균 성장률."
        )
        names = q4[sido_col_m].astype(str).tolist()
        s1, s2, s3 = st.columns(3)
        with s1, st.container(border=True):
            st.markdown("**기당 충전량 (kWh)**")
            st.plotly_chart(
                sido_hbar(names, q4[burden_metric], color=COLORS["active"], unit="kWh"),
                use_container_width=True,
                config={"displayModeBar": False},
            )
        with s2, st.container(border=True):
            st.markdown("**EV / 실제 가동 1기**")
            st.plotly_chart(
                sido_hbar(names, q4["ev_per_active"], color=COLORS["charge"], unit="대/기"),
                use_container_width=True,
                config={"displayModeBar": False},
            )
        with s3, st.container(border=True):
            st.markdown("**EV 3년 CAGR**")
            cagr_pct = (q4["cagr"] * 100).where(q4["cagr"].notna(), 0)
            st.plotly_chart(
                sido_hbar(names, cagr_pct, color=COLORS["ev"], unit="%"),
                use_container_width=True,
                config={"displayModeBar": False},
            )
        st.caption("CAGR은 해당 연도 대비 3년 전 등록이 있을 때만 계산합니다.")

    if fast_stock is not None:
        with st.expander("공급 배경 · 차지인포 급속 비중 (본편 결론 KPI 아님)"):
            st.caption(
                f"기준 {fast_stock['as_of']}. 공공+민간 전체 구축에서 급속 비율입니다. "
                "공공급속 지도와 모집단이 다릅니다."
            )
            r8 = (
                fast_stock["regions"]
                .set_index("권역")[["급속 비중(%)"]]
                .sort_values("급속 비중(%)")
            )
            st.plotly_chart(
                category_bar_chart(r8),
                use_container_width=True,
                config={"displayModeBar": False},
            )
            st.caption(
                f"전국 급속 비중 {fast_stock['fast_share']:.1f}% "
                f"(완속:급속 ≈ {fast_stock['slow_fast']:.1f}:1)."
            )

    st.divider()

    # ------------------------------------------------------------------
    # 3) 종합
    # ------------------------------------------------------------------
    st.markdown("### 3. 종합")
    q4_names = q4[sido_col_m].astype(str).tolist() if not q4.empty else top_priority
    where = ", ".join(q4_names) if q4_names else "이용 부담이 큰 시·도"
    st.success(
        f"수요(EV {cmp['ev_yoy']:+.1f}%)가 실제 가동({cmp['active_yoy']:+.1f}%)·충전량({cmp['kwh_yoy']:+.1f}%)을 앞섭니다. "
        f"**{where}**는 부담 Q4와 겹침 신호가 모이므로 공공급속 **우선 점검이 바람직합니다.** "
        "확충 비율을 여기서 처방하지 않습니다.",
        icon=":material/flag:",
    )
