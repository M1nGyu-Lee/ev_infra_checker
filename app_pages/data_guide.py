"""Data scope, file hierarchy, and interpretation guide."""

import pandas as pd
import streamlit as st

from charger_dashboard.data import (
    load_forecast_manifest,
    load_forecast_methodology_text,
    load_kepco_forecast_manifest,
    load_kepco_forecast_methodology_text,
    load_master,
)
from charger_dashboard.ui import dataframe_download


def render() -> None:
    st.info(
        "이 페이지는 대시보드의 수치가 어느 파일에서 왔고 어디까지 해석 가능한지 설명합니다.",
        icon=":material/database:",
    )

    st.subheader("분석 표시 계층")
    layers = pd.DataFrame(
        [
            {
                "계층": "잠재 수요",
                "질문": "전기차가 얼마나 증가했는가?",
                "핵심 파일": "ev_sido_monthly.csv",
                "범위": "국토부 · 17개 시·도 · 2019-01부터 2026-06까지",
            },
            {
                "계층": "설치 공급",
                "질문": "환경부 공공급속기는 얼마나 설치됐는가?",
                "핵심 파일": "charger_public_fast_sido_annual.csv",
                "범위": "환경부 급속 · 17개 시·도 · 2022년까지",
            },
            {
                "계층": "실제 이용 공급",
                "질문": "실제로 이용 기록이 있는 급속기는 몇 개인가?",
                "핵심 파일": "charge_sido_annual.csv",
                "범위": "환경부 공공급속 · 2019년부터 2025-08까지",
            },
            {
                "계층": "한전 급속 보완",
                "질문": "한전망 급속 충전량 결측을 어떻게 채웠는가?",
                "핵심 파일": "kepco_charge_sido_monthly_trend.csv",
                "범위": "환경부+부하+충전소 현황 · 2019년부터 2025년까지 · 방법론 선행 명시",
            },
            {
                "계층": "수요–공급 부담",
                "질문": "EV 대비 공급과 활성기당 이용 부담은 어떤가?",
                "핵심 파일": "sido_year_master.csv",
                "범위": "시·도×연 통합",
            },
            {
                "계층": "최신 동기간 비교",
                "질문": "2025년 이용량은 전년 같은 기간보다 늘었는가?",
                "핵심 파일": "charge_sido_ytd_compare.csv",
                "범위": "2024년 1–8월 vs 2025년 1–8월",
            },
        ]
    )
    st.dataframe(layers, hide_index=True)

    tabs = st.tabs(["파일별 역할", "지표 정의", "발표·대시보드 구성", "환경부 예측 방법론", "한전 보완 방법론", "품질·한계"])

    with tabs[0]:
        files = pd.DataFrame(
            [
                ["ev_sido_monthly.csv", "시·도×월", "EV 월별 추이"],
                ["ev_sido_annual.csv", "시·도×연", "연말 EV와 부분연도 상태"],
                ["charger_public_fast_sido_annual.csv", "시·도×연", "2019–2022 설치 재고"],
                ["charge_sido_monthly.csv", "시·도×월", "충전량·활성기 월별 추이 (관측)"],
                ["charge_sido_monthly_trend.csv", "시·도×월", "관측+추정 통합 추이"],
                ["kepco_charge_sido_monthly_trend.csv", "시·도×월", "한전 급속 관측+보완 추이"],
                ["kepco_charge_sido_monthly_forecast.csv", "시·도×월", "한전 급속 보완(추정) 전용"],
                ["charge_sido_annual.csv", "시·도×연", "연간 합·피크·활성기"],
                ["charge_sido_monthly_panel.csv", "시·도×월", "동월 EV와 충전량 결합"],
                ["charge_sido_ytd_compare.csv", "시·도", "2024–2025년 1–8월 비교"],
                ["sido_year_master.csv", "시·도×연", "지도·순위·KPI 통합"],
            ],
            columns=["파일", "한 행의 단위", "주 분석"],
        )
        st.dataframe(files, hide_index=True)

    with tabs[1]:
        metrics = pd.DataFrame(
            [
                ["활성충전기수", "양수 실적이 있는 고유 충전기", "설치대수 아님"],
                ["EV천대당설치급속", "설치 재고×1,000/EV", "2022년까지만"],
                ["EV천대당활성급속", "활성기×1,000/EV", "2023년 이후 공급 보조"],
                ["활성기당충전량", "충전량/활성기", "이용 부담"],
                ["EV당충전량", "동월 충전량/동월 EV", "공공급속 의존 수준"],
                ["평균초과율", "피크월/월평균−1", "계절 집중도"],
                ["estimated_value", "예측 모형 산출값", "관측과 분리 표시"],
            ],
            columns=["컬럼", "정의", "해석"],
        )
        st.dataframe(metrics, hide_index=True)

    with tabs[2]:
        st.subheader("발표 우선순위별 대시보드 탭")
        deck = pd.DataFrame(
            [
                {
                    "순위": "1순위",
                    "대상": "대국민 홍보",
                    "탭": "시·도 지도 · 급속 이용 추이 · 지역 상세",
                    "데이터": "환경부 공공급속 (17시도, 지도·충전량·활성기)",
                },
                {
                    "순위": "2순위",
                    "대상": "급·완속 사업자",
                    "탭": "급·완속 설치 판단",
                    "데이터": "차지인포 급·완속(8권역) + 사분면 힌트 + 공공급속 활성기 + 한전 충전소 수",
                },
                {
                    "순위": "3순위",
                    "대상": "전국 기초",
                    "탭": "EV·충전소 총량",
                    "데이터": "국토부 EV + 공공급속 활성기 전국 총량",
                },
            ]
        )
        st.dataframe(deck, hide_index=True)

    with tabs[3]:
        st.caption("환경부 공공급속 — 2025년 9월부터 12월까지 결측 보완")
        try:
            manifest = load_forecast_manifest()
        except FileNotFoundError as exc:
            st.warning(str(exc))
            st.stop()

        weights = manifest["model_blend_weights"]
        trend = manifest["trend_analysis"]
        st.markdown(
            "예측 전에 **입력 데이터 → 추이 분석 → 기법·가중치** 순으로 명시합니다."
        )

        st.subheader("입력·제외 데이터")
        st.dataframe(pd.DataFrame(manifest["input_sources"]), hide_index=True)
        st.dataframe(pd.DataFrame(manifest["excluded_sources"]), hide_index=True)

        st.subheader("추이 분석")
        st.markdown(
            f"""
            - **YTD 비교:** {trend["ytd_comparison"]}
            - **성장률:** {trend["ytd_growth_method"]} (클리핑 {trend["growth_clip"]})
            - **전국 중앙 성장률:** {trend["national_growth_factor"]:.4f}
            - **계절성:** {trend["seasonality_reference"]}
            """
        )

        st.subheader("모형·가중치")
        st.dataframe(pd.DataFrame(manifest["models"]), hide_index=True)
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "채택 모형": manifest["chosen_model_id"],
                        "계절 성장률 가중치": weights["seasonal_growth"],
                        "계절 기준 가중치": weights["seasonal_naive"],
                        "선택 규칙": manifest["model_selection_rule"],
                    }
                ]
            ),
            hide_index=True,
        )
        with st.expander("전체 문서 (forecast_methodology.md)"):
            st.markdown(load_forecast_methodology_text())

    with tabs[4]:
        st.caption("한전 급속 충전량 — 환경부·부하·충전소 현황으로 결측 보완")
        try:
            kepco_manifest = load_kepco_forecast_manifest()
        except FileNotFoundError as exc:
            st.warning(str(exc))
            st.stop()

        blend = kepco_manifest["model_blend_weights"]
        st.markdown(
            """
            한전 원본은 2020년 상반기만 관측 가능합니다. 나머지는 아래 순서로 **보완·추정**합니다.

            1. **환경부 충전량 추이** → 시·도 스케일 (`MOE × ratio`)
            2. **시간대별 부하** → 전국 급속 부하 지수
            3. **충전소 현황** → 시·도 배분 비중
            4. **2020 H1 관측**으로 비율·가중치 교정 후 혼합
            """
        )

        st.subheader("사용 입력 데이터")
        st.dataframe(pd.DataFrame(kepco_manifest["input_sources"]), hide_index=True)

        st.subheader("추이 분석")
        ta = kepco_manifest["trend_analysis"]
        st.markdown(
            f"""
            - **교정 구간:** {kepco_manifest["calibration_period"][0]}부터 {kepco_manifest["calibration_period"][1]}까지
            - **환경부–한전 비율:** {ta["moe_kepco_ratio_calibration"]}
            - **부하 지수:** {ta["load_index_formula"]}
            - **충전소 배분:** {ta["station_share_formula"]}
            """
        )

        st.subheader("모형 구성요소·가중치")
        st.dataframe(pd.DataFrame(kepco_manifest["models"]), hide_index=True)
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "채택 모형": kepco_manifest["chosen_model_id"],
                        "환경부 연계 가중치 (w_moe)": blend["moe_scaled"],
                        "부하·충전소 배분 가중치 (w_load)": blend["load_station_share"],
                        "가중치 선택": kepco_manifest["weight_selection"],
                        "백테스트 WAPE(%)": kepco_manifest["backtest_wape_pct"],
                    }
                ]
            ),
            hide_index=True,
        )
        ratio_rows = [
            {"시도": s, "moe_kepco_ratio": v}
            for s, v in kepco_manifest["ratio_by_sido"].items()
        ]
        with st.expander("시·도별 환경부–한전 교정 비율"):
            st.dataframe(pd.DataFrame(ratio_rows), hide_index=True)
        with st.expander("전체 문서 (forecast_methodology_kepco.md)"):
            st.markdown(load_kepco_forecast_methodology_text())

    with tabs[5]:
        st.warning(
            "2023년 이후 환경부 공공급속 설치 재고는 원천 갱신 중단으로 비어 있습니다. "
            "신규 설치 0기로 해석하면 안 됩니다."
        )
        st.warning(
            "2025년 충전량은 1월부터 8월까지 자료입니다. 완전연도와 직접 비교하지 않고 YTD 표를 사용합니다."
        )
        st.warning(
            "2025년 9월부터 12월까지 **환경부** 충전량은 환경부 관측 시계열만으로 추정했습니다."
        )
        st.warning(
            "한전 급속 충전량은 원본이 2020년 상반기만 있어, "
            "**환경부·시간대별 부하·충전소 현황**으로 보완한 추정값입니다. 실제 한전 실적과 다릅니다."
        )
        st.markdown(
            """
            - 환경부 공공급속 충전량은 전국 모든 운영기관의 충전량이 아닙니다.
            - 활성 충전기는 설치대수나 실시간 정상운영 대수의 대체값이 아닙니다.
            - 지도 순위는 17개 시·도 내 상대평가이며 절대 부족 판정이 아닙니다.
            - 설비와 충전량은 충전기 행 단위로 직접 조인하지 않고 시·도×연 집계 후 결합합니다.
            - 예측치는 관측 파일과 분리 저장되며, 차트에서는 실선(관측)·점선(추정)으로 구분합니다.
            """
        )

    with st.expander("통합 마스터 원자료 미리보기"):
        master = load_master()
        st.dataframe(master, hide_index=True)
        dataframe_download(master, "sido_year_master.csv", "마스터 CSV 다운로드")
