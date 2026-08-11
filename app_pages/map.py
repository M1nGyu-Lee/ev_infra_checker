"""GeoJSON choropleth and ranked regional comparison."""

import streamlit as st

from charger_dashboard.charts import (
    _sido_column,
    _with_burden_visuals,
    burden_bubbles,
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

priority_banner(
    1,
    "시·도별 **환경부 공공급속** 부담을 지도로 비교하는 대국민용 화면입니다.",
)

master = load_master()
geojson = load_geojson()
year = year_selector(available_years(), key="map_year")
scope_notice()
data_status_notice(year)

# Keep only the two story metrics.
metric_options: list[str] = []
if year <= 2022:
    metric_options = ["활성기당충전량", "EV천대당설치급속"]
elif year <= 2025:
    metric_options = ["활성기당충전량", "EV천대당활성급속"]
else:
    st.info("2026년은 환경부 공공급속 이용 지표가 없어 지도를 표시하지 않습니다.")
    st.stop()

metric_options = [m for m in metric_options if m in METRIC_META]
default_metric = metric_options[0]

insight_callout(
    "이 지도를 이렇게 보세요",
    "**활성기당 충전량**이 높을수록 이용 부담, "
    "**EV천대당 활성(또는 설치) 급속기**가 낮을수록 공급이 빠듯한 방향입니다. "
    "오른쪽 원은 클수록 상대 부담이 큽니다. 17개 시·도 상대 비교이며 민간·완속은 제외합니다.",
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
        st.plotly_chart(
            choropleth(geojson, map_data, metric, year),
            use_container_width=True,
            config={"displayModeBar": False},
        )
        st.caption("지도 색 = 지표 값")
    with rank_col, st.container(border=True):
        st.caption("원 크기·색 = 상대 부담 (클수록·진할수록 부담이 큼)")
        st.altair_chart(burden_bubbles(map_data, metric), use_container_width=True)
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

summary_bits: list[str] = []
for _, row in rows.iterrows():
    sido = str(row[sido_col])
    value_txt = format_value(row[metric], metric)
    if show_burden:
        band = str(row["burden_band"])
        if metric == "활성기당충전량":
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
        summary_bits.append(
            f"<div style='padding:0.55rem 0;border-bottom:1px solid #e2e8f0;'>"
            f"<strong>{sido}</strong> · {meta['label']} {value_txt}"
            f" · <span style='color:#0f766e;font-weight:600;'>상대 부담 {band}</span>"
            f"<div style='color:#64748b;font-size:0.9rem;margin-top:0.15rem;'>{note}</div>"
            f"</div>"
        )
    else:
        summary_bits.append(
            f"<div style='padding:0.55rem 0;border-bottom:1px solid #e2e8f0;'>"
            f"<strong>{sido}</strong> · {meta['label']} {value_txt}</div>"
        )

st.markdown(
    "<div style='background:#fff;border:1px solid #e2e8f0;border-radius:14px;padding:0.4rem 1rem;'>"
    + "".join(summary_bits)
    + "</div>",
    unsafe_allow_html=True,
)

download_cols = [sido_col, metric] + (["burden_band"] if show_burden else [])
download = visual[download_cols].rename(
    columns={
        sido_col: "시·도",
        metric: meta["label"],
        **({"burden_band": "상대 부담"} if show_burden else {}),
    }
)
dataframe_download(download, f"sido_map_{year}_{metric}.csv", "분석 결과 CSV")
