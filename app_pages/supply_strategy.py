"""급·완속 설치 판단 (2순위)."""

import pandas as pd
import streamlit as st

from charger_dashboard.charts import category_bar_chart
from charger_dashboard.data import (
    available_years,
    load_charge_annual,
    load_chargeinfo_ev_per_charger_avg,
    load_chargeinfo_ev_per_charger_wide,
    load_chargeinfo_region_stock_monthly,
    load_chargeinfo_slow_fast_ratio_monthly,
    load_master,
)
from charger_dashboard.ui import (
    chargeinfo_region_label,
    dataframe_download,
    insight_callout,
    priority_banner,
    scope_notice,
    year_selector,
)


def _fast_share_insight(cur, selected_ref, prev_ref):
    """급속 비중 표 직전에 보여 줄 자동 요약."""
    ranked = cur.dropna(subset=["fast_share_pct"]).sort_values("fast_share_pct", ascending=False)
    if ranked.empty:
        return "이 스냅샷에 표시할 급속 비중 데이터가 없습니다."

    top = ranked.iloc[0]
    bottom = ranked.iloc[-1]
    parts = [
        f"**{selected_ref}** 기준 급속 비중 최고는 **{top['권역표시']}** "
        f"({top['fast_share_pct']:.1f}%), 최저는 **{bottom['권역표시']}** "
        f"({bottom['fast_share_pct']:.1f}%)입니다."
    ]

    if prev_ref and cur["fast_share_delta"].notna().any():
        delta = cur.dropna(subset=["fast_share_delta"]).sort_values(
            "fast_share_delta", ascending=False
        )
        up = delta.iloc[0]
        down = delta.iloc[-1]
        parts.append(
            f"직전 **{prev_ref}** 대비 증가 폭이 가장 큰 권역은 **{up['권역표시']}** "
            f"({up['fast_share_delta']:+.1f}%p), 감소 폭이 가장 큰 권역은 **{down['권역표시']}** "
            f"({down['fast_share_delta']:+.1f}%p)입니다."
        )
    else:
        parts.append("직전 스냅샷이 없어 비중 변화는 아래 표의 절대 비중만 참고하세요.")

    parts.append(
        "차지인포 **8권역 누적 설치 대수** 비중이며, 충전 이용·환경부 공공급속과는 별도입니다."
    )
    return " ".join(parts)


def render():
    priority_banner(
        2,
        "급속·완속 **충전 사업자·설치 담당**에게 어디에 어떤 속도를 깔지 판단하는 데이터 화면입니다.",
    )
    scope_notice()

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
        _ = load_chargeinfo_ev_per_charger_avg()
        has_chargeinfo_ev_ratio = True
    except FileNotFoundError:
        has_chargeinfo_ev_ratio = False
        chargeinfo_ev_wide = pd.DataFrame()

    if not has_chargeinfo_ev_ratio and not has_chargeinfo_monthly:
        st.warning(
            "차지인포 데이터가 없습니다. `data/raw/chargeinfo/` 확인 후 전처리를 실행하세요.",
            icon=":material/construction:",
        )

    master = load_master()
    charge_annual = load_charge_annual()
    year = year_selector(available_years(), key="supply_year")

    HINT_SHORT = {
        "유지·관망": "급·완속 모두 상대적 여유",
        "급속/핫스팟 검토": "완속은 여유, 급속이 상대 부족",
        "완속·거점 검토": "급속은 여유, 완속이 상대 부족",
        "수요·입지 추가 확인": "급·완속 모두 상대적으로 낮음",
    }

    def _with_region_label(df):
        out = df.copy()
        out["권역표시"] = out["region_name"].map(chargeinfo_region_label)
        return out

    tabs = st.tabs(
        [
            "설치 힌트 사분면",
            "급속 비중·변화",
            "공공급속 활성기",
        ]
    )

    with tabs[0]:
        st.subheader("권역별 급속·완속 보급 강도 사분면")
        insight_callout(
            "읽는 방법",
            "가로=EV 1대당 **급속**, 세로=EV 1대당 **완속**. "
            "중앙값보다 큰지/작은지로 네 칸(사분면)을 나눕니다. "
            "차지인포 **8권역** 기준이며 환경부 17시·도와 합산하지 않습니다.",
            tone="warning",
        )
        if not has_chargeinfo_ev_ratio:
            st.info("차지인포 EV 1대당 보급률 데이터가 없습니다.")
        else:
            q_refs = sorted(chargeinfo_ev_wide["ref_ym"].unique(), reverse=True)
            q_ref = st.selectbox("사분면 기준월", q_refs, index=0, key="quadrant_ref")
            qdf = _with_region_label(
                chargeinfo_ev_wide[chargeinfo_ev_wide["ref_ym"] == q_ref]
            ).copy()
            med_fast = float(qdf["fast_per_ev"].median())
            med_slow = float(qdf["slow_per_ev"].median())

            def _hint(row):
                # 중앙값 기준으로 네 칸 중 어디에 있는지 글자로 붙임
                hi_fast = row["fast_per_ev"] >= med_fast
                hi_slow = row["slow_per_ev"] >= med_slow
                if hi_fast and hi_slow:
                    return "유지·관망"
                if (not hi_fast) and hi_slow:
                    return "급속/핫스팟 검토"
                if hi_fast and (not hi_slow):
                    return "완속·거점 검토"
                return "수요·입지 추가 확인"

            qdf["설치힌트"] = qdf.apply(_hint, axis=1)

            # [고급] Altair mark_rect 배경색 + mark_rule 중앙선 + mark_circle
            # → 흩어진 점(scatter) + 표로 힌트 표시
            scatter_df = qdf.rename(
                columns={
                    "fast_per_ev": "급속(기/대)",
                    "slow_per_ev": "완속(기/대)",
                }
            )
            st.scatter_chart(
                scatter_df,
                x="급속(기/대)",
                y="완속(기/대)",
                color="설치힌트",
            )
            st.caption(
                f"사분면 중심(중앙값) — 급속 {med_fast:.3f} · 완속 {med_slow:.3f} 기/대. "
                "점의 위치가 중앙값보다 오른쪽/위쪽이면 그 축은 '여유' 쪽입니다."
            )

            st.markdown("#### 권역별 설치 힌트")
            hint_table = qdf.sort_values("설치힌트")[
                ["권역표시", "설치힌트", "fast_per_ev", "slow_per_ev"]
            ].copy()
            hint_table["한줄"] = hint_table["설치힌트"].map(HINT_SHORT)
            hint_table = hint_table.rename(
                columns={
                    "권역표시": "권역",
                    "fast_per_ev": "급속(기/대)",
                    "slow_per_ev": "완속(기/대)",
                }
            )
            st.dataframe(hint_table, hide_index=True, width="stretch")

    with tabs[1]:
        st.subheader("급속 비중·스냅샷 변화")
        insight_callout(
            "이 탭의 초점",
            "완속이 많다는 사실보다 **급속 비중(%)**과 **직전 스냅샷 대비 변화**를 봅니다. "
            "스냅샷을 바꾸면 아래 막대·증감이 함께 바뀝니다.",
        )
        if not has_chargeinfo_monthly:
            st.info("차지인포 월별 누적 데이터가 없습니다.")
        else:
            refs = sorted(chargeinfo_ratio["ref_ym"].unique())
            selected_ref = st.selectbox(
                "비교 스냅샷",
                list(reversed(refs)),
                index=0,
                key="chargeinfo_share_ref",
            )
            prev_candidates = [r for r in refs if r < selected_ref]
            prev_ref = prev_candidates[-1] if prev_candidates else None

            cur = chargeinfo_ratio[
                (chargeinfo_ratio["ref_ym"] == selected_ref)
                & (chargeinfo_ratio["region_name"] != "전국")
            ].copy()
            cur = _with_region_label(cur)
            if prev_ref:
                prev = chargeinfo_ratio[
                    (chargeinfo_ratio["ref_ym"] == prev_ref)
                    & (chargeinfo_ratio["region_name"] != "전국")
                ][["region_name", "fast_share_pct", "slow_fast_ratio"]].rename(
                    columns={
                        "fast_share_pct": "prev_fast_share",
                        "slow_fast_ratio": "prev_ratio",
                    }
                )
                cur = cur.merge(prev, on="region_name", how="left")
                cur["fast_share_delta"] = cur["fast_share_pct"] - cur["prev_fast_share"]
            else:
                cur["fast_share_delta"] = pd.NA

            with st.container(border=True):
                st.markdown(f"**{selected_ref} 권역별 급속 비중**")
                share_bar = cur.set_index("권역표시")[["fast_share_pct"]].rename(
                    columns={"fast_share_pct": "급속 비중 (%)"}
                )
                st.plotly_chart(
                    category_bar_chart(share_bar),
                    use_container_width=True,
                    config={"displayModeBar": False},
                )

            with st.container(border=True):
                title = (
                    f"**직전 스냅샷({prev_ref}) 대비 급속 비중 변화**"
                    if prev_ref
                    else "**직전 스냅샷 없음**"
                )
                st.markdown(title)
                if prev_ref:
                    delta_bar = (
                        cur.dropna(subset=["fast_share_delta"])
                        .set_index("권역표시")[["fast_share_delta"]]
                        .rename(columns={"fast_share_delta": "변화 (%p)"})
                    )
                    st.plotly_chart(
                        category_bar_chart(delta_bar),
                        use_container_width=True,
                        config={"displayModeBar": False},
                    )
                    st.caption("양수=급속 비중 상승, 음수=하락")
                else:
                    st.info("더 이른 스냅샷이 없어 변화량을 계산할 수 없습니다.")

            if has_chargeinfo_ev_ratio:
                st.markdown("#### 같은 달 EV 1대당 급속 (보급 강도)")
                snap = _with_region_label(
                    chargeinfo_ev_wide[chargeinfo_ev_wide["ref_ym"] == selected_ref]
                )
                if snap.empty:
                    nearest = max(
                        [r for r in chargeinfo_ev_wide["ref_ym"].unique() if r <= selected_ref],
                        default=None,
                    )
                    if nearest:
                        snap = _with_region_label(
                            chargeinfo_ev_wide[chargeinfo_ev_wide["ref_ym"] == nearest]
                        )
                        st.caption(f"보급률 표는 {nearest} 스냅샷을 사용합니다.")
                if not snap.empty:
                    intensity = snap.set_index("권역표시")[["fast_per_ev"]].rename(
                        columns={"fast_per_ev": "급속 (기/대)"}
                    )
                    st.plotly_chart(
                        category_bar_chart(intensity),
                        use_container_width=True,
                        config={"displayModeBar": False},
                    )
                    insight_callout(
                        "급속 비중 한줄 요약",
                        _fast_share_insight(cur, selected_ref, prev_ref),
                    )

            show = cur[
                [
                    "권역표시",
                    "fast_share_pct",
                    "fast_share_delta",
                    "fast",
                    "slow",
                    "slow_fast_ratio",
                ]
            ].rename(
                columns={
                    "fast_share_pct": "급속 비중(%)",
                    "fast_share_delta": "직전 대비(%p)",
                    "fast": "급속 누적",
                    "slow": "완속 누적",
                    "slow_fast_ratio": "완속/급속",
                }
            )
            st.dataframe(show.sort_values("급속 비중(%)", ascending=False), hide_index=True)
            dataframe_download(show, f"fast_share_{selected_ref}.csv", "급속 비중 CSV")

    with tabs[2]:
        st.subheader(f"{year}년 시·도별 공공급속 활성기·이용")
        active = master[master["year"] == year][
            [
                "sido_short",
                "ev_count",
                "active_charger_count",
                "fast_per_1000_ev_active",
                "kwh_per_active_charger",
                "charge_kwh_sum",
            ]
        ].dropna(subset=["active_charger_count"])
        active = active.sort_values("kwh_per_active_charger", ascending=False)
        st.caption(
            "활성기당 충전량이 높은 지역은 **급속 이용 부담**이 큰 편입니다. "
            "EV 대비 활성기가 낮으면 급속 추가를 검토할 수 있습니다."
        )
        active_bar = active.set_index("sido_short")[["kwh_per_active_charger"]].rename(
            columns={"kwh_per_active_charger": "활성기당 kWh"}
        )
        st.plotly_chart(
            category_bar_chart(active_bar, height=520),
            use_container_width=True,
            config={"displayModeBar": False},
        )
        st.dataframe(active, hide_index=True)
        dataframe_download(active, f"public_fast_active_{year}.csv")

        if len(charge_annual):
            nat = (
                charge_annual.groupby("year", as_index=False)[
                    ["charge_kwh_sum", "active_charger_count"]
                ].sum(min_count=1)
            )
            st.subheader("전국 공공급속 이용 추이")
            nat_line = nat.set_index("year")[["charge_kwh_sum"]].rename(
                columns={"charge_kwh_sum": "충전량 (kWh)"}
            )
            st.line_chart(nat_line)
            st.caption(
                "EV는 늘어도 공공급속 충전량이 정체·감소한 구간이 있어, "
                "**일상 충전은 완속·거점으로 이동**했을 가능성을 함께 읽어야 합니다."
            )
