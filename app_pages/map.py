"""GeoJSON choropleth and ranked regional comparison."""

import pandas as pd
import streamlit as st

from charger_dashboard.charts import (
    _with_burden_visuals,
    burden_bubbles,
    choropleth,
)
from charger_dashboard.data import (
    METRIC_META,
    SIDO_ORDER,
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
)

priority_banner(
    1,
    "시·도별 **환경부 공공급속** 부담을 지도로 비교하는 대국민용 화면입니다.",
)

master = load_master()
geojson = load_geojson()
year = int(st.session_state.selected_year)
selected_region = st.session_state.selected_sido

scope_notice()
data_status_notice(year)
insight_callout(
    "이 지도를 이렇게 보세요",
    "지도 색은 선택한 지표 값입니다. "
    "오른쪽 원은 **클수록 상대 부담이 큰 지역**입니다 "
    "(공급지표는 값이 낮을수록, 이용·수요지표는 값이 높을수록 부담이 커집니다). "
    "17개 시·도 상대 비교이며 민간·완속은 포함하지 않습니다.",
)

metric_options = ["전기차등록대수"]
if year <= 2022:
    metric_options.extend(["EV천대당설치급속", "활성충전기수"])
elif year <= 2025:
    metric_options.extend(
        [
            "활성충전기수",
            "EV천대당활성급속",
            "충전량_kWh",
            "활성기당충전량",
        ]
    )

metric = st.segmented_control(
    "지도 지표",
    metric_options,
    default=metric_options[1] if len(metric_options) > 1 else metric_options[0],
    format_func=lambda value: METRIC_META[value]["label"],
    key=f"map_metric_{year}",
)
meta = METRIC_META[metric]
map_data = rank_for_map(master, year, metric)

if map_data.empty:
    st.warning(f"{year}년 {meta['label']} 데이터가 없습니다.")
    st.stop()

visual = _with_burden_visuals(map_data)

map_col, rank_col = st.columns([1.25, 1])
with map_col, st.container(border=True):
    st.plotly_chart(
        choropleth(geojson, map_data, metric, year),
        use_container_width=True,
        config={"displayModeBar": False},
    )
    st.caption("지도 색 = 지표 값. 마우스를 올리면 시·도와 상대 부담을 볼 수 있습니다.")

with rank_col, st.container(border=True):
    st.caption("원 크기·색 = 상대 부담 (클수록·진할수록 부담이 큼)")
    st.altair_chart(burden_bubbles(map_data, metric), use_container_width=True)

st.caption(meta["help"])

st.subheader("선택 지역 확인")
region = st.selectbox(
    "시·도",
    SIDO_ORDER,
    index=SIDO_ORDER.index(selected_region) if selected_region in SIDO_ORDER else 0,
    key="map_detail_region",
)
sido_col = "시도" if "시도" in visual.columns else "시도"
row = visual[visual[sido_col] == region]
if not row.empty:
    row = row.iloc[0]
    band = str(row["burden_band"])
    with st.container(horizontal=True):
        st.metric(
            f"{region} · {meta['label']}",
            format_value(row[metric], metric),
            border=True,
        )
        st.metric(
            "상대 부담",
            band,
            help=(
                "17개 시·도 안에서 상대적으로 부담이 큰 편인지 보여 줍니다. "
                "공급지표는 값이 낮을수록, 이용·수요지표는 값이 높을수록 부담이 커집니다."
            ),
            border=True,
        )

download = visual[[sido_col, metric, "burden_band"]].rename(
    columns={
        sido_col: "시·도",
        metric: meta["label"],
        "burden_band": "상대 부담",
    }
)
dataframe_download(download, f"sido_map_{year}_{metric}.csv", "비교표 CSV 다운로드")

with st.expander("지도 해석 기준"):
    st.markdown(
        """
        - 원의 **크기·색**이 상대 부담입니다. 숫자가 아닌 감각으로 비교하세요.
        - `EV 1,000대당 설치/활성 급속기`: 값이 낮을수록 공급 부담이 커집니다.
        - `충전량`, `활성기당 충전량`, `EV 등록대수`: 값이 높을수록 이용·수요 부담이 커집니다.
        - 17개 시·도 상대 비교이며 법적·정책적 부족 판정이 아닙니다.
        """
    )
