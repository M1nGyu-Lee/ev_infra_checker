"""발표용 정책 브리핑.

그래프는 위 페이지 버튼으로 바꾸고, 필터는 각 그래프 안에만 둔다.
2020–2024는 연간 전체, 2025는 1–8월을 전년 같은 달과 비교한다.
"""

import pandas as pd
import streamlit as st

from charger_dashboard.charts import (
    COLORS,
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


def _yoy(curr, prev):
    if prev is None or pd.isna(prev) or prev == 0 or curr is None or pd.isna(curr):
        return float("nan")
    return (float(curr) / float(prev) - 1) * 100


def _delta_text(curr, prev, unit, pct, *, decimals=0):
    if pd.isna(pct):
        return None
    diff = float(curr) - float(prev)
    if decimals == 0:
        return f"{diff:+,.0f}{unit}  ·  {pct:+.1f}%"
    return f"{diff:+,.{decimals}f}{unit}  ·  {pct:+.1f}%"


def _agg_year(master, year, sido=None):
    yc = _year_col(master)
    sc = _sido_col(master)
    df = master[master[yc] == year]
    if sido:
        df = df[df[sc] == sido]
    if df.empty:
        return None
    ev_c = _col(df, "ev_count", "전기차등록대수")
    ac_c = _col(df, "active_charger_count", "활성충전기수")
    kwh_c = _col(df, "charge_kwh_sum", "충전량_kWh")
    st_c = _col(df, "data_status", "기간상태")
    mo_c = _col(df, "month_count", "관측월수")
    months = int(df[mo_c].max()) if df[mo_c].notna().any() else 12
    status = "partial" if (df[st_c] == "partial").any() else "complete"
    return {
        "ev": float(df[ev_c].sum()),
        "active": float(df[ac_c].sum()),
        "kwh": float(df[kwh_c].sum()),
        "months": months,
        "status": status,
    }


def _from_ytd(ytd, sido=None):
    """2025 부분연도: 2024·2025 같은 달(1–N월) 합."""
    df = ytd
    if sido:
        sc = _sido_col(ytd)
        df = ytd[ytd[sc] == sido]
        if df.empty:
            return None
    kwh_prev = float(df[_col(df, "charge_kwh_2024_ytd", "충전량_2024_YTD")].sum())
    kwh_curr = float(df[_col(df, "charge_kwh_2025_ytd", "충전량_2025_YTD")].sum())
    ev_prev = float(df[_col(df, "ev_count_2024_ytd_avg", "EV_2024_YTD평균")].sum())
    ev_curr = float(df[_col(df, "ev_count_2025_ytd_avg", "EV_2025_YTD평균")].sum())
    active_prev = float(df[_col(df, "active_charger_2024_ytd", "활성기_2024_YTD")].sum())
    active_curr = float(df[_col(df, "active_charger_2025_ytd", "활성기_2025_YTD")].sum())
    months = int(df[_col(df, "months_compared", "비교월수")].iloc[0]) if len(df) else 8
    return {
        "mode": "same_months",
        "year": 2025,
        "prev_year": 2024,
        "months": months,
        "label_prev": f"2024년 1–{months}월",
        "label_curr": f"2025년 1–{months}월",
        "ev_prev": ev_prev,
        "ev_curr": ev_curr,
        "active_prev": active_prev,
        "active_curr": active_curr,
        "kwh_prev": kwh_prev,
        "kwh_curr": kwh_curr,
        "ev_yoy": _yoy(ev_curr, ev_prev),
        "active_yoy": _yoy(active_curr, active_prev),
        "kwh_yoy": _yoy(kwh_curr, kwh_prev),
    }


def _year_compare(master, ytd, year, sido=None):
    """선택 연도 vs 바로 전 해.

    연간이 꽉 찬 해(2020–2024)는 1–12월끼리.
    2025처럼 달이 비면 전년 같은 달끼리(YTD 표).
    """
    cur = _agg_year(master, year, sido)
    if cur is None:
        return None
    if cur["status"] == "partial" or cur["months"] < 12:
        if year == 2025:
            return _from_ytd(ytd, sido)
        return None
    prev = _agg_year(master, year - 1, sido)
    if prev is None:
        return None
    return {
        "mode": "full_year",
        "year": year,
        "prev_year": year - 1,
        "months": 12,
        "label_prev": f"{year - 1}년",
        "label_curr": f"{year}년",
        "ev_prev": prev["ev"],
        "ev_curr": cur["ev"],
        "active_prev": prev["active"],
        "active_curr": cur["active"],
        "kwh_prev": prev["kwh"],
        "kwh_curr": cur["kwh"],
        "ev_yoy": _yoy(cur["ev"], prev["ev"]),
        "active_yoy": _yoy(cur["active"], prev["active"]),
        "kwh_yoy": _yoy(cur["kwh"], prev["kwh"]),
    }


def _monthly_series(nat, panel, sido, year_lo, year_hi):
    src = panel if sido else nat
    src = _ensure_date(src)
    if sido:
        src = src[src[_sido_col(src)] == sido]
    years = src["date"].dt.year
    return src[(years >= year_lo) & (years <= year_hi)].copy()


def _q4_names(df, value_col, sido_col, *, higher_is_worse):
    """17시·도를 5-4-4-4로 나눌 때 Q4(1–5위). PPT 부담·여력 등급과 같다."""
    n = int(df[value_col].notna().sum())
    n_q4 = n - 3 * (n // 4)
    rank = df[value_col].rank(ascending=not higher_is_worse, method="min")
    hit = df.loc[rank <= n_q4].sort_values(value_col, ascending=not higher_is_worse)
    return hit[sido_col].astype(str).tolist()


def _priority_groups(master, year):
    yc = _year_col(master)
    sc = _sido_col(master)
    burden_c = _col(master, "kwh_per_active_charger", "활성기당충전량")
    supply_c = _col(master, "fast_per_1000_ev_active", "EV천대당활성급속")
    df = master[master[yc] == year].dropna(subset=[burden_c, supply_c, sc]).copy()
    if df.empty:
        return [], [], []
    busy = _q4_names(df, burden_c, sc, higher_is_worse=True)
    tight = _q4_names(df, supply_c, sc, higher_is_worse=False)
    both = [s for s in busy if s in tight]
    burden_only = [s for s in busy if s not in tight]
    supply_only = [s for s in tight if s not in busy]
    return both, burden_only, supply_only


def _chart(fig):
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


def _year_label(year):
    if year >= 2025:
        return f"{year}년 · 1–8월을 전년 같은 달과 비교"
    return f"{year}년 · 1–12월 전체"


def _filters(key_prefix, *, sido=True, year=True, year_opts=None, default_year=None, range_years=False):
    """이 그래프 전용 필터. 다른 화면 값과 섞이지 않게 key를 나눈다."""
    out = {}
    cols = st.columns((1.2, 1.6, 1.6)[: (1 if sido else 0) + (1 if year else 0) + (1 if range_years else 0)] or [1])
    i = 0
    if sido:
        with cols[i]:
            out["scope"] = st.selectbox(
                "시·도",
                ["전국", *SIDO_ORDER],
                index=0,
                key=f"{key_prefix}_sido",
            )
        i += 1
    if year and year_opts:
        idx = year_opts.index(default_year) if default_year in year_opts else len(year_opts) - 1
        with cols[i]:
            out["year"] = st.selectbox(
                "연도",
                year_opts,
                index=idx,
                format_func=_year_label,
                key=f"{key_prefix}_year",
            )
        i += 1
    if range_years and year_opts:
        with cols[i]:
            lo, hi = year_opts[0], year_opts[-1]
            out["year_lo"], out["year_hi"] = st.slider(
                "기간",
                min_value=lo,
                max_value=hi,
                value=(max(lo, 2020), hi),
                key=f"{key_prefix}_range",
            )
    return out


def _map_panel(master, year, metric, sido, *, high_is_priority, caption):
    map_data = rank_for_map(master, year, metric)
    if map_data.empty:
        st.warning(f"{year}년 지도 데이터가 없습니다.")
        return
    if year >= 2025:
        st.caption("2025년은 1–8월 관측입니다.")
    st.caption(caption)
    geojson = load_geojson()
    map_col, bar_col = st.columns([1.25, 1])
    with map_col, st.container(border=True):
        st.markdown(f"**시·도 지도 · {year}년**")
        _chart(choropleth(geojson, map_data, metric, year))
    with bar_col, st.container(border=True):
        st.markdown("**같은 숫자 순위**")
        sc = _sido_col(map_data)
        _chart(
            sido_hbar(
                map_data[sc],
                map_data[metric],
                color=COLORS["charge"],
                unit=METRIC_META[metric]["unit"],
                height=520,
                highlight=sido,
                higher_on_top=high_is_priority,
            )
        )
    sc = _sido_col(map_data)
    ranked = map_data.sort_values(metric, ascending=not high_is_priority)
    top = ranked.head(5)[sc].astype(str).tolist()
    if sido:
        names = list(ranked[sc].astype(str))
        if sido in names:
            rank = names.index(sido) + 1
            st.info(
                f"**읽을 점:** {year}년 {sido}는 **{rank}위 / {len(names)}곳**입니다. "
                f"{'부담이 큰' if high_is_priority else '충전기가 부족한'} 쪽은 {', '.join(top)}입니다.",
                icon=":material/map:",
            )
            return
    st.info(
        f"**읽을 점:** {year}년 {'부담이 큰' if high_is_priority else '전기차 대비 충전기가 부족한'} "
        f"시·도는 **{', '.join(top)}**입니다.",
        icon=":material/map:",
    )


BRIEF_PAGES = [
    "전년 대비",
    "월별 추이",
    "이용 부담",
    "전기차 대비 충전기",
    "종합",
]


def render():
    master = load_master()
    nat = _ensure_date(load_national_charge_ev_monthly())
    panel = _ensure_date(load_charge_panel())
    ytd = load_ytd_compare()

    c_date = "date"
    c_ev = _col(nat, "ev_count", "전기차등록대수")
    c_kwh = _col(nat, "charge_kwh_sum", "충전량_kWh")
    panel_ev = _col(panel, "ev_count", "전기차등록대수")
    panel_kwh = _col(panel, "charge_kwh_sum", "충전량_kWh")

    burden_metric = _pick_metric("kwh_per_active_charger", "활성기당충전량")
    supply_metric = _pick_metric("fast_per_1000_ev_active", "EV천대당활성급속")

    year_col = _year_col(master)
    year_opts = sorted(
        int(y) for y in master[year_col].dropna().unique() if 2020 <= int(y) <= 2025
    )
    yoy_years = [y for y in year_opts if (y - 1) in set(
        int(v) for v in master[year_col].dropna().unique()
    )]
    default_map_year = 2024 if 2024 in year_opts else year_opts[-1]
    default_yoy_year = 2024 if 2024 in yoy_years else yoy_years[-1]

    page = st.segmented_control(
        "이 화면에서 볼 그래프",
        BRIEF_PAGES,
        default=BRIEF_PAGES[0],
        key="brief_page",
    )
    if page is None:
        page = BRIEF_PAGES[0]
    st.caption("위를 누르면 그래프가 바뀝니다. 시·도·연도 필터는 각 그래프 안에 있습니다.")

    if page == "전년 대비":
        st.markdown("### 전기차는 늘었는데, 충전기·충전량은 따라갔을까?")
        with st.container(border=True):
            st.markdown("**이 그래프 필터**")
            f = _filters(
                "yoy",
                year_opts=yoy_years,
                default_year=default_yoy_year,
            )
        sido = None if f["scope"] == "전국" else f["scope"]
        place = f["scope"]
        year = f["year"]
        cmp = _year_compare(master, ytd, year, sido)
        if cmp is None:
            st.warning(f"{place} {year}년 전년 대비 데이터가 없습니다.")
        else:
            if cmp["mode"] == "same_months":
                st.caption(
                    f"{place} · {cmp['label_curr']}을 {cmp['label_prev']}과 같은 달끼리 비교합니다. "
                    "2020–2024년을 고르면 1–12월 전체끼리 비교합니다."
                )
            else:
                st.caption(
                    f"{place} · {cmp['label_curr']} 전체를 {cmp['label_prev']} 전체와 비교합니다. "
                    "실제 이용된 충전기 = 그해 충전 실적이 있는 충전기."
                )
            m1, m2, m3 = st.columns(3)
            m1.metric(
                "전기차 등록",
                f"{cmp['ev_curr']:,.0f}대",
                delta=_delta_text(cmp["ev_curr"], cmp["ev_prev"], "대", cmp["ev_yoy"]),
                border=True,
            )
            m2.metric(
                "실제 이용된 충전기",
                f"{cmp['active_curr']:,.0f}기",
                delta=_delta_text(
                    cmp["active_curr"], cmp["active_prev"], "기", cmp["active_yoy"]
                ),
                border=True,
            )
            m3.metric(
                "충전량",
                f"{cmp['kwh_curr'] / 1e6:,.1f} GWh",
                delta=_delta_text(
                    cmp["kwh_curr"] / 1e6,
                    cmp["kwh_prev"] / 1e6,
                    " GWh",
                    cmp["kwh_yoy"],
                    decimals=1,
                ),
                border=True,
            )
            b1, b2, b3 = st.columns(3)
            with b1, st.container(border=True):
                st.markdown("**전기차 등록**")
                _chart(
                    paired_year_bars(
                        cmp["ev_prev"],
                        cmp["ev_curr"],
                        yoy_pct=cmp["ev_yoy"],
                        unit="대",
                        label_prev=cmp["label_prev"],
                        label_curr=cmp["label_curr"],
                    )
                )
            with b2, st.container(border=True):
                st.markdown("**실제 이용된 충전기 수**")
                _chart(
                    paired_year_bars(
                        cmp["active_prev"],
                        cmp["active_curr"],
                        yoy_pct=cmp["active_yoy"],
                        unit="기",
                        label_prev=cmp["label_prev"],
                        label_curr=cmp["label_curr"],
                    )
                )
            with b3, st.container(border=True):
                st.markdown("**충전량**")
                _chart(
                    paired_year_bars(
                        cmp["kwh_prev"] / 1e6,
                        cmp["kwh_curr"] / 1e6,
                        yoy_pct=cmp["kwh_yoy"],
                        unit="GWh",
                        label_prev=cmp["label_prev"],
                        label_curr=cmp["label_curr"],
                    )
                )
            st.info(
                f"**읽을 점:** {place} 전기차는 **{cmp['ev_yoy']:+.1f}%** "
                f"({cmp['ev_curr'] - cmp['ev_prev']:+,.0f}대)인데, "
                f"실제 이용된 충전기는 **{cmp['active_yoy']:+.1f}%** "
                f"({cmp['active_curr'] - cmp['active_prev']:+,.0f}기), "
                f"충전량은 **{cmp['kwh_yoy']:+.1f}%**입니다.",
                icon=":material/ev_station:",
            )

    elif page == "월별 추이":
        st.markdown("### 월별로 보면 전기차와 충전량은 어떻게 움직이나?")
        with st.container(border=True):
            st.markdown("**이 그래프 필터**")
            f = _filters(
                "trend",
                year=False,
                range_years=True,
                year_opts=year_opts,
            )
        sido = None if f["scope"] == "전국" else f["scope"]
        place = f["scope"]
        year_lo, year_hi = f["year_lo"], f["year_hi"]
        monthly = _monthly_series(nat, panel, sido, year_lo, year_hi)
        ev_col = c_ev if sido is None else panel_ev
        kwh_col = c_kwh if sido is None else panel_kwh
        st.caption(
            f"{place} · {year_lo}–{year_hi}년. 왼쪽은 전기차 등록, 오른쪽은 충전량입니다."
        )
        with st.container(border=True):
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
                        right_name="충전량 (kWh)",
                        height=420,
                    )
                )

    elif page == "이용 부담":
        st.markdown("### 어디에 이용 부담이 큰가?")
        st.caption("이용 부담 = 실제 이용된 충전기 1기당 충전량. 숫자가 클수록 한 대가 바쁩니다.")
        with st.container(border=True):
            st.markdown("**이 그래프 필터**")
            f = _filters(
                "burden",
                year_opts=year_opts,
                default_year=default_map_year,
            )
        sido = None if f["scope"] == "전국" else f["scope"]
        _map_panel(
            master,
            f["year"],
            burden_metric,
            sido,
            high_is_priority=True,
            caption="색이 진할수록 충전기 한 대가 더 많이 쓰입니다. 상위 약 25%가 부담이 큰 시·도입니다.",
        )

    elif page == "전기차 대비 충전기":
        st.markdown("### 전기차 수에 비해 실제 이용된 충전기가 어디가 부족한가?")
        st.caption(
            "전기차 1,000대당 실제 이용된 충전기 수입니다. 숫자가 낮을수록 충전기가 부족합니다."
        )
        with st.container(border=True):
            st.markdown("**이 그래프 필터**")
            f = _filters(
                "supply",
                year_opts=year_opts,
                default_year=default_map_year,
            )
        sido = None if f["scope"] == "전국" else f["scope"]
        _map_panel(
            master,
            f["year"],
            supply_metric,
            sido,
            high_is_priority=False,
            caption="색이 옅을수록 전기차 수에 비해 실제 이용된 충전기가 적습니다.",
        )

    elif page == "종합":
        st.markdown("### 어디에 배치를 우선하는 것이 바람직한가?")
        with st.container(border=True):
            st.markdown("**이 그래프 필터**")
            f = _filters(
                "sum",
                year_opts=year_opts,
                default_year=default_map_year,
            )
        year = f["year"]
        sido = None if f["scope"] == "전국" else f["scope"]
        both, burden_only, supply_only = _priority_groups(master, year)
        st.caption(
            f"{year}년 기준. 이용 부담이 큰 곳과, 전기차 대비 실제 이용된 충전기가 부족한 곳을 겹쳐 봅니다."
        )
        g1, g2, g3 = st.columns(3)
        with g1, st.container(border=True):
            st.markdown("**둘 다**")
            st.write(" · ".join(both) if both else "해당 없음")
        with g2, st.container(border=True):
            st.markdown("**이용 부담만 크다**")
            st.write(" · ".join(burden_only) if burden_only else "해당 없음")
        with g3, st.container(border=True):
            st.markdown("**전기차 대비 충전기만 부족하다**")
            st.write(" · ".join(supply_only) if supply_only else "해당 없음")
        where = ", ".join(both) if both else "이용 부담과 충전기 부족이 겹치는 시·도"
        if sido:
            bits = []
            if sido in both:
                bits.append("둘 다에 들어갑니다")
            elif sido in burden_only:
                bits.append("이용 부담만 큽니다")
            elif sido in supply_only:
                bits.append("전기차 대비 충전기만 부족합니다")
            else:
                bits.append("두 상위 목록에는 없습니다")
            st.success(
                f"{year}년 **{sido}**는 {bits[0]}. "
                f"둘 다인 곳은 **{where}**이므로, 여기서부터 배치를 우선하는 것이 바람직합니다.",
                icon=":material/flag:",
            )
        else:
            extra = []
            if burden_only:
                extra.append(f"이용 부담만 큰 곳은 {', '.join(burden_only)}")
            if supply_only:
                extra.append(f"전기차 대비 충전기만 부족한 곳은 {', '.join(supply_only)}")
            tail = " ".join(extra)
            st.success(
                f"{year}년 둘 다 부족한 곳은 **{where}**입니다. {tail} "
                "둘 다인 곳부터 배치를 우선하는 것이 바람직합니다.",
                icon=":material/flag:",
            )
