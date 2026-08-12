"""시·도 지도 + 상대 부담 비교 (1순위)."""

import streamlit as st

from charger_dashboard.charts import (
    _sido_column,
    _with_burden_visuals,
    burden_bar_frame,
    choropleth,
)
from charger_dashboard.data import (
    BURDEN_METRICS,
    METRIC_META,
    available_years,
    load_geojson,
    load_master,
    rank_for_map,
)
from charger_dashboard.ui import (
    data_status_notice,
    dataframe_download,
    format_value,
    insight_callout,
    priority_banner,
    scope_notice,
    year_selector,
)


def render():
    priority_banner(
        1,
        "시·도별 **환경부 공공급속** 부담을 지도로 비교하는 **탐색** 화면입니다. "
        "발표 본편은 **발표·정책 브리핑**을 먼저 보세요.",
    )

    master = load_master()
    geojson = load_geojson()
    year = year_selector(available_years(), key="map_year")
    scope_notice()
    data_status_notice(year)

    if year <= 2022:
        metric_options = ["kwh_per_active_charger", "fast_per_1000_ev_stock"]
    elif year <= 2025:
        metric_options = ["kwh_per_active_charger", "fast_per_1000_ev_active"]
    else:
        st.info("2026년은 환경부 공공급속 이용 지표가 없어 지도를 표시하지 않습니다.")
        st.stop()

    metric_options = [m for m in metric_options if m in METRIC_META]
    default_metric = metric_options[0]

    insight_callout(
        "이 지도를 이렇게 보세요",
        "**활성기당 충전량**이 높을수록 이용 부담, "
        "**EV천대당 활성(또는 설치) 급속기**가 낮을수록 공급이 빠듯한 방향입니다. "
        "오른쪽 막대가 길수록 상대 부담이 큽니다. 17개 시·도 상대 비교이며 민간·완속은 제외합니다.",
    )

    metric = st.segmented_control(
        "지도 지표",
        metric_options,
        default=default_metric,
        format_func=lambda value: METRIC_META[value]["label"],
        key=f"map_metric_{year}",
    )
    if metric is None:
        metric = default_metric
    meta = METRIC_META[metric]
    map_data = rank_for_map(master, year, metric)
    show_burden = metric in BURDEN_METRICS

    if map_data.empty:
        st.warning(f"{year}년 {meta['label']} 데이터가 없습니다.")
        st.stop()

    visual = _with_burden_visuals(map_data) if show_burden else map_data.copy()
    sido_col = _sido_column(visual)

    if show_burden:
        map_col, rank_col = st.columns([1.25, 1])
        with map_col, st.container(border=True):
            # 지도: 표(시·도+값) + GeoJSON 이름을 맞춰 color="value"로 색칠
            st.plotly_chart(
                choropleth(geojson, map_data, metric, year),
                use_container_width=True,
                config={"displayModeBar": False},
            )
            st.caption("지도 색 = 지표 값 (진할수록 큼)")
        with rank_col, st.container(border=True):
            st.caption("막대 길이 = 지표 값 (길수록 상대 부담이 큰 쪽에 가깝게 정렬)")
            # [고급] st.altair_chart(burden_bubbles(...))  → 기본 막대
            st.bar_chart(burden_bar_frame(map_data, metric), horizontal=True)
    else:
        with st.container(border=True):
            st.plotly_chart(
                choropleth(geojson, map_data, metric, year),
                use_container_width=True,
                config={"displayModeBar": False},
            )

    st.caption(meta["help"])

    st.subheader("시·도별 분석 결과")
    st.caption("상대 부담이 큰 순서로 정리했습니다. 숫자는 17개 시·도 안에서의 비교입니다.")

    rows = visual.sort_values(
        "burden_score" if show_burden and "burden_score" in visual.columns else metric,
        ascending=False,
    )

    # HTML 목록 대신 표로 보여 주기
    notes = []
    for _, row in rows.iterrows():
        sido = str(row[sido_col])
        value_txt = format_value(row[metric], metric)
        if show_burden:
            band = str(row["burden_band"])
            if metric == "kwh_per_active_charger":
                note = {
                    "높음": "활성기 대비 이용이 몰리는 편",
                    "다소 높음": "이용 부담이 평균보다 큰 편",
                    "보통": "이용 부담이 중간대",
                    "낮음": "활성기 대비 이용이 여유 있는 편",
                }.get(band, "")
            else:
                note = {
                    "높음": "EV 대비 급속 공급이 빠듯한 편",
                    "다소 높음": "공급 여력이 평균보다 타이트",
                    "보통": "공급 여력이 중간대",
                    "낮음": "EV 대비 급속 공급이 여유 있는 편",
                }.get(band, "")
            notes.append(
                {
                    "시·도": sido,
                    meta["label"]: value_txt,
                    "상대 부담": band,
                    "한줄 해석": note,
                }
            )
        else:
            notes.append({"시·도": sido, meta["label"]: value_txt})

    st.dataframe(notes, hide_index=True, width="stretch")

    download_cols = [sido_col, metric] + (["burden_band"] if show_burden else [])
    download = visual[download_cols].rename(
        columns={
            sido_col: "시·도",
            metric: meta["label"],
            **({"burden_band": "상대 부담"} if show_burden else {}),
        }
    )
    dataframe_download(download, f"sido_map_{year}_{metric}.csv", "분석 결과 CSV")
