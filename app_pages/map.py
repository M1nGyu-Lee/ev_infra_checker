"""GeoJSON choropleth and ranked regional comparison."""

import pandas as pd
import streamlit as st

from charger_dashboard.charts import choropleth, ranked_bar
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
    "색이 진한 지역이 ‘무조건 부족’이 아닙니다. "
    "**활성기당 충전량·충전량**은 높을수록 이용 부담, "
    "**EV천대당 활성기**는 낮을수록 공급 여력이 빠듯한 방향입니다. "
    "17개 시·도 상대 비교이며, 민간·완속은 포함하지 않습니다.",
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

map_col, rank_col = st.columns([1.25, 1])
with map_col, st.container(border=True):
    st.altair_chart(choropleth(geojson, map_data, metric, year))
    st.caption("지도 위에 마우스를 올리면 시·도별 값과 부담 방향 순위를 볼 수 있습니다.")

with rank_col, st.container(border=True):
    st.altair_chart(ranked_bar(map_data, metric))

st.caption(meta["help"])

st.subheader("선택 지역 확인")
region = st.selectbox(
    "시·도",
    SIDO_ORDER,
    index=SIDO_ORDER.index(selected_region) if selected_region in SIDO_ORDER else 0,
    key="map_detail_region",
)
row = map_data[map_data["시도"] == region]
if not row.empty:
    row = row.iloc[0]
    with st.container(horizontal=True):
        st.metric(
            f"{region} · {meta['label']}",
            format_value(row[metric], metric),
            border=True,
        )
        st.metric(
            "부담 방향 순위",
            f"{int(row['rank'])}위 / {len(map_data)}개 시·도",
            help=(
                "공급지표는 값이 낮을수록, 이용부담·수요지표는 값이 높을수록 "
                "1위에 가까워집니다."
            ),
            border=True,
        )

table = map_data[["시도", metric, "rank", "기간상태", "설비상태"]]
st.dataframe(
    table,
    hide_index=True,
    column_config={
        "시도": st.column_config.TextColumn("시·도", pinned=True),
        metric: st.column_config.NumberColumn(
            f"{meta['label']} ({meta['unit']})",
            format=f"%.2f" if ".2" in meta["format"] else "localized",
        ),
        "rank": st.column_config.NumberColumn("부담 방향 순위", format="%d"),
        "기간상태": st.column_config.TextColumn("기간 상태"),
        "설비상태": st.column_config.TextColumn("설비 상태"),
    },
)
dataframe_download(table, f"sido_map_{year}_{metric}.csv")

with st.expander("지도 해석 기준"):
    st.markdown(
        """
        - `EV 1,000대당 설치/활성 급속기`: 값이 낮을수록 공급 부담 방향입니다.
        - `충전량`, `활성기당 충전량`, `EV 등록대수`: 값이 높을수록 수요·이용 부담 방향입니다.
        - 순위는 17개 시·도 내 상대 비교이며 법적·정책적 부족 판정이 아닙니다.
        - 2023년 이후 설치 재고는 원천 갱신 중단으로 지도에서 제외합니다.
        """
    )
