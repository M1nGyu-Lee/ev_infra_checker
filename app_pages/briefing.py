"""발표용 정책 브리핑.

스토리: 전국 괴리 → 부담 지도 → 신호 겹침 → 우선 점검.
시연: 시·도·연도·기간을 바꾸면 같은 그래프가 따라간다.
"""

import pandas as pd
import streamlit as st

from charger_dashboard.charts import (
    COLORS,
    category_bar_chart,
    choropleth,
    dual_axis_line,
    paired_year_bars,
    sido_hbar,
)
from charger_dashboard.data import (
    METRIC_META,
    SIDO_ORDER,
    load_charge_panel,
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


def _ensure_date(df):
    out = df.copy()
    if "date" not in out.columns:
        ym = _col(out, "year_month", "기준월")
        out["date"] = pd.to_datetime(out[ym], format="%Y-%m")
    return out


def _period_compare(ytd, sido=None):
    """같은 달 구간(1–N월) 전년 대비. YTD라는 말은 화면에 쓰지 않음."""
    df = ytd
    if sido:
        sc = _sido_col(ytd)
        df = ytd[ytd[sc] == sido]
        if df.empty:
            return None
    kwh_2024 = float(df[_col(df, "charge_kwh_2024_ytd", "충전량_2024_YTD")].sum())
    kwh_2025 = float(df[_col(df, "charge_kwh_2025_ytd", "충전량_2025_YTD")].sum())
    ev_2024 = float(df[_col(df, "ev_count_2024_ytd_avg", "EV_2024_YTD평균")].sum())
    ev_2025 = float(df[_col(df, "ev_count_2025_ytd_avg", "EV_2025_YTD평균")].sum())
    active_2024 = float(df[_col(df, "active_charger_2024_ytd", "활성기_2024_YTD")].sum())
    active_2025 = float(df[_col(df, "active_charger_2025_ytd", "활성기_2025_YTD")].sum())
    months = int(df[_col(df, "months_compared", "비교월수")].iloc[0]) if len(df) else 8
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


def _monthly_series(nat, panel, sido, year_lo, year_hi):
    src = panel if sido else nat
    src = _ensure_date(src)
    if sido:
        src = src[src[_sido_col(src)] == sido]
    years = src["date"].dt.year
    return src[(years >= year_lo) & (years <= year_hi)].copy()


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


def _chart(fig):
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


def render():
    master = load_master()
    nat = _ensure_date(load_national_charge_ev_monthly())
    panel = _ensure_date(load_charge_panel())
    ytd = load_ytd_compare()
    fast_stock = _fast_stock_snapshot()

    c_date = "date"
    c_ev = _col(nat, "ev_count", "전기차등록대수")
    c_kwh = _col(nat, "charge_kwh_sum", "충전량_kWh")
    panel_ev = _col(panel, "ev_count", "전기차등록대수")
    panel_kwh = _col(panel, "charge_kwh_sum", "충전량_kWh")

    burden_metric = _pick_metric("kwh_per_active_charger", "활성기당충전량")
    volume_metric = _pick_metric("charge_kwh_sum", "충전량_kWh")
    supply_metric = _pick_metric("fast_per_1000_ev_active", "EV천대당활성급속")

    year_col = _year_col(master)
    sido_col_m = _sido_col(master)
    year_opts = sorted(
        int(y) for y in master[year_col].dropna().unique() if 2019 <= int(y) <= 2025
    )
    default_year = 2024 if 2024 in year_opts else year_opts[-1]

    with st.container(border=True):
        st.markdown("**화면 필터**")
        st.caption("시·도·연도·기간을 바꾸면 아래 그래프가 바로 바뀝니다.")
        f1, f2, f3 = st.columns([1.1, 0.9, 1.6])
        with f1:
            scope = st.selectbox("시·도", ["전국", *SIDO_ORDER], index=0, key="brief_sido")
        with f2:
            year = st.selectbox(
                "지도 연도", year_opts, index=year_opts.index(default_year), key="brief_year"
            )
        with f3:
            year_lo, year_hi = st.slider(
                "월별 추이 기간",
                min_value=2019,
                max_value=2025,
                value=(2022, 2025),
                key="brief_range",
            )
        metric_label = st.segmented_control(
            "지도·순위에 볼 것",
            ["이용 부담", "총 충전량", "급속 여력"],
            default="이용 부담",
            key="brief_metric",
            help="발표 본편은 이용 부담입니다. 급속 여력은 옅은 곳이 빠듯합니다.",
        )

    sido = None if scope == "전국" else scope
    place = "전국" if sido is None else sido
    cmp = _period_compare(ytd, sido)
    monthly = _monthly_series(nat, panel, sido, year_lo, year_hi)
    ev_col = c_ev if sido is None else panel_ev
    kwh_col = c_kwh if sido is None else panel_kwh

    if metric_label == "총 충전량":
        map_metric = volume_metric
        metric_help = "색이 진할수록 공공급속 총 충전량이 많습니다."
        high_is_priority = True
    elif metric_label == "급속 여력":
        map_metric = supply_metric
        metric_help = "색이 진할수록 EV 대비 실제 가동이 많습니다. 옅은 곳이 여력이 빠듯합니다."
        high_is_priority = False
    else:
        map_metric = burden_metric
        metric_help = "색이 진할수록 가동 1기당 충전량이 큽니다."
        high_is_priority = True
        metric_label = "이용 부담"

    # ------------------------------------------------------------------
    # 1) 괴리
    # ------------------------------------------------------------------
    st.markdown(f"### 1. {place} — EV와 공공급속")
    if cmp is None:
        st.warning(f"{place} 동기간 비교 데이터가 없습니다.")
    else:
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
            _chart(
                paired_year_bars(
                    cmp["ev_2024"],
                    cmp["ev_2025"],
                    yoy_pct=cmp["ev_yoy"],
                    unit="대",
                    months=cmp["months"],
                )
            )
        with b2, st.container(border=True):
            st.markdown("**실제 가동**")
            _chart(
                paired_year_bars(
                    cmp["active_2024"],
                    cmp["active_2025"],
                    yoy_pct=cmp["active_yoy"],
                    unit="기",
                    months=cmp["months"],
                )
            )
        with b3, st.container(border=True):
            st.markdown("**공공급속 충전량**")
            _chart(
                paired_year_bars(
                    cmp["kwh_2024"] / 1e6,
                    cmp["kwh_2025"] / 1e6,
                    yoy_pct=cmp["kwh_yoy"],
                    unit="GWh",
                    months=cmp["months"],
                )
            )

        st.info(
            f"**읽을 점:** {place} 전기차는 **{cmp['ev_yoy']:+.1f}%** 늘었는데 "
            f"실제 가동은 **{cmp['active_yoy']:+.1f}%**, 충전량은 **{cmp['kwh_yoy']:+.1f}%**입니다.",
            icon=":material/ev_station:",
        )

    with st.container(border=True):
        st.markdown(f"**월별 추이 · {place} · {year_lo}–{year_hi}년**")
        st.caption("왼쪽=전기차 등록, 오른쪽=공공급속 충전량.")
        if monthly.empty:
            st.warning("선택한 기간에 월별 데이터가 없습니다.")
        else:
            dual_df = monthly[[c_date, ev_col, kwh_col]].rename(
                columns={ev_col: "전기차", kwh_col: "충전량"}
            )
            _chart(
                dual_axis_line(
                    dual_df,
                    c_date,
                    "전기차",
                    "충전량",
                    left_name="전기차 (대)",
                    right_name="공공급속 충전량 (kWh)",
                    height=400,
                )
            )

    st.divider()

    # ------------------------------------------------------------------
    # 2) 지도
    # ------------------------------------------------------------------
    st.markdown("### 2. 시·도 이용 부담 지도")
    st.caption(f"{metric_help} Q4 = 17시·도 중 상위 약 25%.")
    if year == 2025:
        st.caption("2025년은 1–8월 관측입니다.")

    map_data = rank_for_map(master, year, map_metric)
    top_priority = []
    selected_rank = None
    selected_n = None
    if map_data.empty:
        st.warning(f"{year}년 지도 데이터가 없습니다.")
    else:
        geojson = load_geojson()
        map_col, bar_col = st.columns([1.25, 1])
        with map_col, st.container(border=True):
            st.markdown(f"**시·도 지도 · {year}년 · {metric_label}**")
            _chart(choropleth(geojson, map_data, map_metric, year))
        with bar_col, st.container(border=True):
            st.markdown("**같은 지표 순위**")
            sc = _sido_col(map_data)
            _chart(
                sido_hbar(
                    map_data[sc],
                    map_data[map_metric],
                    color=COLORS["charge"],
                    unit="",
                    height=520,
                    highlight=sido,
                )
            )

        sc = _sido_col(map_data)
        ranked = map_data.sort_values(map_metric, ascending=not high_is_priority)
        top_priority = ranked.head(5)[sc].tolist()
        selected_n = len(ranked)
        if sido:
            hit = ranked[ranked[sc] == sido]
            if not hit.empty:
                selected_rank = int(list(ranked[sc]).index(sido) + 1)

        if sido and selected_rank:
            st.info(
                f"**읽을 점:** {year}년 {metric_label}에서 **{sido}는 {selected_rank}위 / {selected_n}곳**입니다. "
                f"상위권은 {', '.join(top_priority)}입니다.",
                icon=":material/map:",
            )
        else:
            st.info(
                f"**읽을 점:** {year}년 {metric_label} 상위는 **{', '.join(top_priority)}**입니다.",
                icon=":material/map:",
            )

    # ------------------------------------------------------------------
    # 2b) 신호 겹침
    # ------------------------------------------------------------------
    q4 = _q4_signals(master, year, year_col, sido_col_m, burden_metric)
    if not q4.empty:
        st.markdown(f"### 신호가 겹치는가 — {year}년 부담 Q4")
        st.caption("기당 충전량 · EV/실제 가동 1기 · EV 3년 연평균 성장률. 선택한 시·도는 파란 막대.")
        names = q4[sido_col_m].astype(str).tolist()
        s1, s2, s3 = st.columns(3)
        with s1, st.container(border=True):
            st.markdown("**기당 충전량 (kWh)**")
            _chart(
                sido_hbar(
                    names,
                    q4[burden_metric],
                    color=COLORS["active"],
                    unit="kWh",
                    highlight=sido,
                )
            )
        with s2, st.container(border=True):
            st.markdown("**EV / 실제 가동 1기**")
            _chart(
                sido_hbar(
                    names,
                    q4["ev_per_active"],
                    color=COLORS["charge"],
                    unit="대/기",
                    highlight=sido,
                )
            )
        with s3, st.container(border=True):
            st.markdown("**EV 3년 CAGR**")
            cagr_pct = (q4["cagr"] * 100).where(q4["cagr"].notna(), 0)
            _chart(
                sido_hbar(names, cagr_pct, color=COLORS["ev"], unit="%", highlight=sido)
            )
        if sido:
            in_q4 = sido in names
            st.caption(
                f"{sido}는 {year}년 부담 Q4에 **{'들어갑니다' if in_q4 else '들어가지 않습니다'}**."
            )

    if fast_stock is not None:
        with st.expander("공급 배경 · 차지인포 급속 비중 (본편 결론 KPI 아님)"):
            st.caption(
                f"기준 {fast_stock['as_of']}. 공공+민간 전체 구축에서 급속 비율입니다."
            )
            r8 = (
                fast_stock["regions"]
                .set_index("권역")[["급속 비중(%)"]]
                .sort_values("급속 비중(%)")
            )
            _chart(category_bar_chart(r8))
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
    in_q4 = bool(sido) and sido in q4_names
    if cmp is None:
        st.success(
            f"**{where}**는 부담 Q4와 겹침 신호가 모이므로 공공급속 **우선 점검이 바람직합니다.**",
            icon=":material/flag:",
        )
    elif sido and selected_rank:
        line = (
            f"{sido}는 EV {cmp['ev_yoy']:+.1f}% · 실제 가동 {cmp['active_yoy']:+.1f}% · "
            f"충전량 {cmp['kwh_yoy']:+.1f}%입니다. {year}년 {metric_label} **{selected_rank}위**. "
            f"전국 Q4는 **{where}**입니다."
        )
        if in_q4:
            line += f" {sido}도 Q4에 들어가므로 공공급속 **우선 점검이 바람직합니다.**"
        st.success(line, icon=":material/flag:")
    else:
        st.success(
            f"수요(EV {cmp['ev_yoy']:+.1f}%)가 실제 가동({cmp['active_yoy']:+.1f}%)·"
            f"충전량({cmp['kwh_yoy']:+.1f}%)을 앞섭니다. "
            f"**{where}**는 부담 Q4와 겹침 신호가 모이므로 공공급속 **우선 점검이 바람직합니다.**",
            icon=":material/flag:",
        )
