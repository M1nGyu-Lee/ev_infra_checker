"""발표·정책 브리핑 (1순위). 탐색 페이지와 분리된 스토리보드 화면."""

import pandas as pd
import streamlit as st

from charger_dashboard.data import (
    load_master,
    load_national_charge_ev_monthly,
    load_ytd_compare,
)
from charger_dashboard.ui import insight_callout, priority_banner, scope_notice


def _ytd_national(ytd: pd.DataFrame) -> dict:
    """시·도 YTD 표를 전국 합으로 요약."""
    kwh_2024 = float(ytd["charge_kwh_2024_ytd"].sum())
    kwh_2025 = float(ytd["charge_kwh_2025_ytd"].sum())
    ev_2024 = float(ytd["ev_count_2024_ytd_avg"].sum())
    ev_2025 = float(ytd["ev_count_2025_ytd_avg"].sum())
    active_2024 = float(ytd["active_charger_2024_ytd"].sum())
    active_2025 = float(ytd["active_charger_2025_ytd"].sum())
    return {
        "kwh_2024": kwh_2024,
        "kwh_2025": kwh_2025,
        "kwh_yoy": (kwh_2025 / kwh_2024 - 1) * 100 if kwh_2024 else float("nan"),
        "ev_2024": ev_2024,
        "ev_2025": ev_2025,
        "ev_yoy": (ev_2025 / ev_2024 - 1) * 100 if ev_2024 else float("nan"),
        "active_2024": active_2024,
        "active_2025": active_2025,
        "active_yoy": (active_2025 / active_2024 - 1) * 100 if active_2024 else float("nan"),
        "months": int(ytd["months_compared"].iloc[0]) if len(ytd) else 8,
    }


def render():
    priority_banner(
        1,
        "정책 결정·예산 우선순위 **점검용 발표 화면**입니다. "
        "설치 확정이나 예산 금액 산출이 아니라, **어디에 먼저 볼지**를 같은 정의로 보여 줍니다.",
    )
    scope_notice()

    master = load_master()
    nat = load_national_charge_ev_monthly()
    ytd = load_ytd_compare()
    ytd_nat = _ytd_national(ytd)

    # ----- 1. 한 줄 결론 -----
    st.markdown("### 1. 한 줄 결론")
    insight_callout(
        "정책 메시지",
        "전기차는 빠르게 늘었지만 **환경부 공공급속**의 이용·활성 증가는 그에 못 미치고, "
        "부담은 **시·도마다 다릅니다.** "
        "공공급속 정책은 총량 일률 확대보다 **지역·이용 부담 기준의 우선 점검**이 필요합니다. "
        "(환경부 공공급속 범위 · 상대 비교)",
        tone="success",
    )

    # ----- 2. 이 숫자가 무엇인가 -----
    st.markdown("### 2. 이 숫자가 무엇인가")
    st.caption("발표에서 쓰는 지표는 아래 네 개뿐입니다. 범위를 섞지 마세요.")
    d1, d2, d3, d4 = st.columns(4)
    with d1, st.container(border=True):
        st.markdown("**전기차 등록**")
        st.caption("국토부 · 잠재 수요")
        st.markdown("등록된 전기차 대수")
    with d2, st.container(border=True):
        st.markdown("**공공급속 충전량**")
        st.caption("환경부 · 이용량")
        st.markdown("공공 **급속**망 kWh")
        st.caption("전국 모든 충전기 이용량 아님")
    with d3, st.container(border=True):
        st.markdown("**활성 충전기**")
        st.caption("환경부 · 가동")
        st.markdown("충전 실적이 있는 기기 수")
        st.caption("설치 대수와 다름")
    with d4, st.container(border=True):
        st.markdown("**활성기당 충전량**")
        st.caption("이용 ÷ 활성기")
        st.markdown("높을수록 기기당 부담↑")
        st.caption("17개 시·도 상대 비교")

    st.divider()

    # ----- 3. 전국 신호 -----
    st.markdown("### 3. 전국 신호 — 수요와 공공급속 이용이 어긋나는가?")
    st.caption(
        f"비교 구간: 2024년 1–{ytd_nat['months']}월 vs 2025년 1–{ytd_nat['months']}월 "
        "(같은 기간끼리만 비교)"
    )

    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric(
            "EV 평균등록 (YTD)",
            f"{ytd_nat['ev_2025']:,.0f}대",
            delta=f"{ytd_nat['ev_yoy']:+.1f}%",
            help="시·도 YTD 평균 등록대수의 전국 합",
            border=True,
        )
    with m2:
        st.metric(
            "활성 공공급속 (YTD)",
            f"{ytd_nat['active_2025']:,.0f}기",
            delta=f"{ytd_nat['active_yoy']:+.1f}%",
            help="시·도 YTD 활성기 수의 전국 합",
            border=True,
        )
    with m3:
        st.metric(
            "공공급속 충전량 (YTD)",
            f"{ytd_nat['kwh_2025'] / 1e6:,.1f} GWh",
            delta=f"{ytd_nat['kwh_yoy']:+.1f}%",
            help="시·도 YTD 충전량 합",
            border=True,
        )

    # 증감률 막대 (배운 st.bar_chart만 사용)
    yoy_frame = pd.DataFrame(
        {
            "증감률(%)": [
                ytd_nat["ev_yoy"],
                ytd_nat["active_yoy"],
                ytd_nat["kwh_yoy"],
            ]
        },
        index=["EV 등록", "활성 공공급속", "공공급속 충전량"],
    )
    st.markdown("**전년 동기간 대비 증감률**")
    st.bar_chart(yoy_frame)
    insight_callout(
        "정책 함의",
        f"같은 1–{ytd_nat['months']}월 기준으로 EV는 약 **{ytd_nat['ev_yoy']:+.1f}%** 늘었지만, "
        f"활성 공공급속은 **{ytd_nat['active_yoy']:+.1f}%**, 충전량은 **{ytd_nat['kwh_yoy']:+.1f}%**입니다. "
        "총량 확대만으로는 공공급속 **체감·이용**이 따라가지 않을 수 있어, "
        "**입지·가동(활성)·지역 차등**을 함께 볼 필요가 있습니다.",
    )

    st.markdown("**월별 추이 (전국)**")
    st.caption("축 단위가 달라 차트를 두 개로 나눴습니다.")
    nat_plot = nat.set_index("date")
    left, right = st.columns(2)
    with left:
        st.caption("전기차 등록대수")
        st.line_chart(nat_plot[["ev_count"]].rename(columns={"ev_count": "전기차 (대)"}))
    with right:
        st.caption("환경부 공공급속 충전량")
        st.line_chart(
            nat_plot[["charge_kwh_sum"]].rename(columns={"charge_kwh_sum": "충전량 (kWh)"})
        )
    st.caption("2025년 충전량은 1–8월까지만 있습니다.")

    st.divider()

    # ----- 4. 지역 우선 점검 후보 -----
    st.markdown("### 4. 지역 우선 점검 후보 — 부담이 전국 균등한가?")
    year = 2024
    m24 = master[(master["year"] == year) & (master["data_status"] == "complete")].copy()
    m24 = m24.dropna(subset=["kwh_per_active_charger", "fast_per_1000_ev_active"])

    st.caption(
        f"{year}년(완전연도) 기준. "
        "**활성기당 충전량**이 높을수록 기기당 이용 부담이 큰 편입니다. "
        "설치 확정이 아니라 **우선 점검 후보**입니다."
    )

    top = m24.nlargest(5, "kwh_per_active_charger")[
        ["sido_short", "kwh_per_active_charger", "fast_per_1000_ev_active", "ev_count"]
    ].copy()
    top = top.rename(
        columns={
            "sido_short": "시·도",
            "kwh_per_active_charger": "활성기당 충전량",
            "fast_per_1000_ev_active": "EV천대당 활성기",
            "ev_count": "EV 등록",
        }
    )

    bar = top.set_index("시·도")[["활성기당 충전량"]]
    st.markdown("**활성기당 충전량 상위 5개 시·도**")
    st.bar_chart(bar)

    st.dataframe(
        top,
        hide_index=True,
        width="stretch",
        column_config={
            "활성기당 충전량": st.column_config.NumberColumn(format="%.0f"),
            "EV천대당 활성기": st.column_config.NumberColumn(format="%.2f"),
            "EV 등록": st.column_config.NumberColumn(format="localized"),
        },
    )

    # 여력도 낮은 곳이 겹치면 강조
    low_supply = set(
        m24.nsmallest(5, "fast_per_1000_ev_active")["sido_short"].tolist()
    )
    high_burden = set(top["시·도"].tolist())
    overlap = sorted(high_burden & low_supply)
    if overlap:
        insight_callout(
            "정책 함의",
            f"이용 부담(활성기당 kWh) 상위와 EV 대비 활성기 하위가 겹치는 곳: "
            f"**{', '.join(overlap)}**. "
            "공공급속 **확충·입지·가동률**을 우선 점검할 후보로 읽을 수 있습니다. "
            "민간·완속 보완은 이 지표에 포함되지 않습니다.",
            tone="warning",
        )
    else:
        insight_callout(
            "정책 함의",
            "전국 일률 지원보다 **시·도별 이용 부담**을 보고 "
            "현장 점검·차등 검토 후보를 고르는 편이 안전합니다.",
        )

    # 충전량 YTD 증감 양극 (짧게)
    ytd_sorted = ytd.sort_values("charge_kwh_ytd_yoy_pct", ascending=False)
    up = ytd_sorted.head(3)[["sido_short", "charge_kwh_ytd_yoy_pct"]]
    down = ytd_sorted.tail(3)[["sido_short", "charge_kwh_ytd_yoy_pct"]]
    c_up, c_down = st.columns(2)
    with c_up:
        st.markdown("**공공급속 충전량 YTD 증가 상위**")
        st.bar_chart(up.set_index("sido_short").rename(columns={"charge_kwh_ytd_yoy_pct": "%"}))
    with c_down:
        st.markdown("**공공급속 충전량 YTD 감소·하위**")
        st.bar_chart(down.set_index("sido_short").rename(columns={"charge_kwh_ytd_yoy_pct": "%"}))
    st.caption("전국 평균(+수 %)만 보면 지역 체감이 가려질 수 있습니다 → 차등 검토 근거.")

    st.divider()

    # ----- 5. 의사결정 주의 -----
    st.markdown("### 5. 의사결정에 쓸 때 주의")
    st.warning(
        "- **공공급속 ≠ 전국 충전** (민간·완속·다른 운영사 미포함)\n"
        "- **예산 금액을 산출하는 화면이 아님** (우선 점검·수단 선택 힌트)\n"
        "- 2025년 충전량은 **1–8월(부분연도)** → 연간 합처럼 비교하지 말 것\n"
        "- 2023년 이후 설비 설치 재고 원천은 갱신 제한 → **활성기 지표** 사용\n"
        "- “부족/충분” 단정 대신 **상대적으로 빠듯/여유**로 표현",
        icon=":material/policy:",
    )

    # ----- 6. 더 보려면 (탐색) -----
    st.markdown("### 6. 더 보려면 (탐색 화면)")
    st.caption("아래는 필터·표가 많은 **탐색용**입니다. 발표 본편은 이 페이지까지로 충분합니다.")
    l1, l2, l3, l4 = st.columns(4)
    with l1:
        try:
            st.page_link("pages/01_시도_지도.py", label="시·도 지도", icon=":material/map:")
        except Exception:
            st.caption("시·도 지도")
    with l2:
        try:
            st.page_link(
                "pages/02_급속_이용_추이.py", label="급속 이용 추이", icon=":material/timeline:"
            )
        except Exception:
            st.caption("급속 이용 추이")
    with l3:
        try:
            st.page_link("pages/03_지역_상세.py", label="지역 상세", icon=":material/location_on:")
        except Exception:
            st.caption("지역 상세")
    with l4:
        try:
            st.page_link(
                "pages/04_급완속_설치_판단.py",
                label="급·완속 설치(사이드)",
                icon=":material/electrical_services:",
            )
        except Exception:
            st.caption("급·완속 설치 판단")
