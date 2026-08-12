"""급·완속 설치 판단 (2순위)."""

import pandas as pd
import streamlit as st

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
        out["권역표시"] = out["권역"].map(chargeinfo_region_label)
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
            q_refs = sorted(chargeinfo_ev_wide["기준월"].unique(), reverse=True)
            q_ref = st.selectbox("사분면 기준월", q_refs, index=0, key="quadrant_ref")
            qdf = _with_region_label(
                chargeinfo_ev_wide[chargeinfo_ev_wide["기준월"] == q_ref]
            ).copy()
            med_fast = float(qdf["급속_대당"].median())
            med_slow = float(qdf["완속_대당"].median())

            def _hint(row):
                # 중앙값 기준으로 네 칸 중 어디에 있는지 글자로 붙임
                hi_fast = row["급속_대당"] >= med_fast
                hi_slow = row["완속_대당"] >= med_slow
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
                    "급속_대당": "급속(기/대)",
                    "완속_대당": "완속(기/대)",
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
                ["권역표시", "설치힌트", "급속_대당", "완속_대당"]
            ].copy()
            hint_table["한줄"] = hint_table["설치힌트"].map(HINT_SHORT)
            hint_table = hint_table.rename(
                columns={
                    "권역표시": "권역",
                    "급속_대당": "급속(기/대)",
                    "완속_대당": "완속(기/대)",
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
            refs = sorted(chargeinfo_ratio["기준월"].unique())
            selected_ref = st.selectbox(
                "비교 스냅샷",
                list(reversed(refs)),
                index=0,
                key="chargeinfo_share_ref",
            )
            prev_candidates = [r for r in refs if r < selected_ref]
            prev_ref = prev_candidates[-1] if prev_candidates else None

            cur = chargeinfo_ratio[
                (chargeinfo_ratio["기준월"] == selected_ref)
                & (chargeinfo_ratio["권역"] != "전국")
            ].copy()
            cur = _with_region_label(cur)
            if prev_ref:
                prev = chargeinfo_ratio[
                    (chargeinfo_ratio["기준월"] == prev_ref)
                    & (chargeinfo_ratio["권역"] != "전국")
                ][["권역", "급속비중", "완속급속비"]].rename(
                    columns={
                        "급속비중": "prev_fast_share",
                        "완속급속비": "prev_ratio",
                    }
                )
                cur = cur.merge(prev, on="권역", how="left")
                cur["fast_share_delta"] = cur["급속비중"] - cur["prev_fast_share"]
            else:
                cur["fast_share_delta"] = pd.NA

            left, right = st.columns(2)
            with left, st.container(border=True):
                st.markdown(f"**{selected_ref} 권역별 급속 비중**")
                share_bar = cur.set_index("권역표시")[["급속비중"]].rename(
                    columns={"급속비중": "급속 비중 (%)"}
                )
                st.bar_chart(share_bar)
            with right, st.container(border=True):
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
                    st.bar_chart(delta_bar)
                    st.caption("양수=급속 비중 상승, 음수=하락")
                else:
                    st.info("더 이른 스냅샷이 없어 변화량을 계산할 수 없습니다.")

            if has_chargeinfo_ev_ratio:
                st.markdown("#### 같은 달 EV 1대당 급속 (보급 강도)")
                snap = _with_region_label(
                    chargeinfo_ev_wide[chargeinfo_ev_wide["기준월"] == selected_ref]
                )
                if snap.empty:
                    nearest = max(
                        [r for r in chargeinfo_ev_wide["기준월"].unique() if r <= selected_ref],
                        default=None,
                    )
                    if nearest:
                        snap = _with_region_label(
                            chargeinfo_ev_wide[chargeinfo_ev_wide["기준월"] == nearest]
                        )
                        st.caption(f"보급률 표는 {nearest} 스냅샷을 사용합니다.")
                if not snap.empty:
                    intensity = snap.set_index("권역표시")[["급속_대당"]].rename(
                        columns={"급속_대당": "급속 (기/대)"}
                    )
                    st.bar_chart(intensity)

            show = cur[
                [
                    "권역표시",
                    "급속비중",
                    "fast_share_delta",
                    "급속",
                    "완속",
                    "완속급속비",
                ]
            ].rename(
                columns={
                    "급속비중": "급속 비중(%)",
                    "fast_share_delta": "직전 대비(%p)",
                    "급속": "급속 누적",
                    "완속": "완속 누적",
                    "완속급속비": "완속/급속",
                }
            )
            st.dataframe(show.sort_values("급속 비중(%)", ascending=False), hide_index=True)
            dataframe_download(show, f"fast_share_{selected_ref}.csv", "급속 비중 CSV")

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
        active_bar = active.set_index("시도")[["활성기당충전량"]].rename(
            columns={"활성기당충전량": "활성기당 kWh"}
        )
        st.bar_chart(active_bar)
        st.dataframe(active, hide_index=True)
        dataframe_download(active, f"public_fast_active_{year}.csv")

        if len(charge_annual):
            nat = (
                charge_annual.groupby("연도", as_index=False)[
                    ["충전량_kWh", "활성충전기수"]
                ].sum(min_count=1)
            )
            st.subheader("전국 공공급속 이용 추이")
            nat_line = nat.set_index("연도")[["충전량_kWh"]].rename(
                columns={"충전량_kWh": "충전량 (kWh)"}
            )
            st.line_chart(nat_line)
            st.caption(
                "EV는 늘어도 공공급속 충전량이 정체·감소한 구간이 있어, "
                "**일상 충전은 완속·거점으로 이동**했을 가능성을 함께 읽어야 합니다."
            )
