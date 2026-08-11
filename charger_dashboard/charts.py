"""Chart builders shared by dashboard pages."""

from __future__ import annotations

import copy

import altair as alt
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from charger_dashboard.data import METRIC_META


def _sido_column(df: pd.DataFrame) -> str:
    # Set form survives share-package rewrite (sido_short -> 시도) without duplicate branches.
    candidates = {"시도", "시도", "sido"}
    for name in df.columns:
        if name in candidates:
            return str(name)
    raise KeyError("시·도 컬럼(sido_short/시도)이 없습니다.")


def _geo_sido(props: dict) -> str | None:
    candidates = {"시도", "시도", "sido"}
    for key, value in props.items():
        if key in candidates and value is not None:
            return str(value)
    return None

COLORS = {
    "ev": "#2563EB",
    "charge": "#0F766E",
    "active": "#D97706",
    "muted": "#64748B",
    "danger": "#DC2626",
    "palette_slow": "#1D4ED8",
    "palette_fast": "#DC2626",
}


def line_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    color: str | None = None,
    x_title: str = "기간",
    y_title: str | None = None,
    height: int = 340,
) -> alt.Chart:
    tooltip = [
        alt.Tooltip(x, title=x_title),
        alt.Tooltip(y, title=y_title or y, format=",.2f"),
    ]
    encodings: dict = {
        "x": alt.X(x, title=x_title, axis=alt.Axis(labelAngle=0)),
        "y": alt.Y(y, title=y_title),
        "tooltip": tooltip,
    }
    if color:
        encodings["color"] = alt.Color(color, title="시·도")
        tooltip.append(alt.Tooltip(color, title="시·도"))
    return (
        alt.Chart(df)
        .mark_line(point=True, strokeWidth=2)
        .encode(**encodings)
        .properties(height=height)
        .interactive(bind_y=False)
    )


def paired_ytd_chart(df: pd.DataFrame, metric_prefix: str) -> alt.Chart:
    column_pairs = {
        "charge_kwh": ("충전량_2024_YTD", "충전량_2025_YTD"),
        "active_charger": ("활성기_2024_YTD", "활성기_2025_YTD"),
    }
    value_columns = list(column_pairs[metric_prefix])
    sido_col = _sido_column(df)
    chart_df = df[[sido_col, *value_columns]].rename(columns={sido_col: "sido"}).melt(
        id_vars="sido",
        var_name="period",
        value_name="value",
    )
    chart_df["period"] = chart_df["period"].map(
        {
            value_columns[0]: "2024년 1–8월",
            value_columns[1]: "2025년 1–8월",
        }
    )
    return (
        alt.Chart(chart_df)
        .mark_bar()
        .encode(
            x=alt.X("sido:N", title="시·도", sort="-y"),
            y=alt.Y("value:Q", title="동기간 값"),
            color=alt.Color(
                "period:N",
                title="비교기간",
                scale=alt.Scale(range=[COLORS["muted"], COLORS["charge"]]),
            ),
            xOffset="period:N",
            tooltip=[
                alt.Tooltip("sido:N", title="시·도"),
                alt.Tooltip("period:N", title="기간"),
                alt.Tooltip("value:Q", title="값", format=",.2f"),
            ],
        )
        .properties(height=380)
    )


def burden_scatter(df: pd.DataFrame) -> alt.Chart:
    sido_col = _sido_column(df)
    plot = df.dropna(subset=["EV천대당활성급속", "활성기당충전량"]).rename(
        columns={sido_col: "sido"}
    )
    return (
        alt.Chart(plot)
        .mark_circle(opacity=0.82)
        .encode(
            x=alt.X(
                "EV천대당활성급속:Q",
                title="EV 1,000대당 활성 급속기 (기)",
            ),
            y=alt.Y(
                "활성기당충전량:Q",
                title="활성기당 충전량 (kWh/기)",
            ),
            size=alt.Size(
                "전기차등록대수:Q",
                title="전기차 등록대수",
                scale=alt.Scale(range=[80, 900]),
            ),
            color=alt.Color(
                "충전량_kWh:Q",
                title="총 충전량",
                scale=alt.Scale(scheme="tealblues"),
            ),
            tooltip=[
                alt.Tooltip("sido:N", title="시·도"),
                alt.Tooltip("전기차등록대수:Q", title="EV", format=","),
                alt.Tooltip(
                    "EV천대당활성급속:Q",
                    title="EV 1,000대당 활성기",
                    format=",.2f",
                ),
                alt.Tooltip(
                    "활성기당충전량:Q",
                    title="활성기당 kWh",
                    format=",.2f",
                ),
            ],
        )
        .properties(height=420)
        .interactive()
    )


def choropleth(
    geojson: dict,
    metric_df: pd.DataFrame,
    metric: str,
    year: int,
) -> go.Figure:
    """Sido choropleth via Plotly.

    Streamlit's ``st.altair_chart`` strips inline GeoJSON geometry, which yields a
    blank map with a NaN legend. Plotly ``px.choropleth`` keeps local WGS84
    polygons (lon ~124–132, lat ~33–39) and is the reliable Cloud path.
    """
    meta = METRIC_META[metric]
    sido_col = _sido_column(metric_df)
    values = (
        metric_df[[sido_col, metric, "rank"]]
        .rename(columns={sido_col: "sido", metric: "value"})
        .dropna(subset=["value"])
        .copy()
    )
    values["sido"] = values["sido"].astype(str)
    values["value"] = values["value"].astype(float)
    values = _with_burden_visuals(values)

    geo = copy.deepcopy(geojson)
    matched = 0
    for feat in geo.get("features", []):
        props = feat.setdefault("properties", {})
        sido = _geo_sido(props)
        if sido is None:
            continue
        props["sido"] = sido
        if sido in set(values["sido"]):
            matched += 1

    if values.empty or matched == 0:
        fig = go.Figure()
        fig.add_annotation(
            text="지도 데이터 조인 실패 (시·도 키 또는 좌표 확인)",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
        )
        fig.update_layout(
            height=560,
            title=f"{year}년 {meta['label']}",
            margin=dict(l=0, r=0, t=48, b=0),
        )
        return fig

    fig = px.choropleth(
        values,
        geojson=geo,
        locations="sido",
        featureidkey="properties.sido",
        color="value",
        color_continuous_scale="Teal",
        hover_name="sido",
        hover_data={
            "value": ":,.2f",
            "burden_band": True,
            "sido": False,
            "rank": False,
            "burden_score": False,
        },
        labels={
            "value": f"{meta['label']} ({meta['unit']})",
            "burden_band": "상대 부담",
        },
        title=f"{year}년 {meta['label']}",
    )
    fig.update_traces(marker_line_width=0.6, marker_line_color="#ffffff")
    fig.update_geos(
        fitbounds="locations",
        visible=False,
        projection_type="mercator",
        bgcolor="rgba(0,0,0,0)",
    )
    fig.update_layout(
        height=560,
        margin=dict(l=0, r=0, t=48, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        coloraxis_colorbar=dict(
            title=f"{meta['label']}<br>({meta['unit']})",
            thickness=14,
            len=0.72,
        ),
    )
    return fig


def _burden_band(rank: float | int, n: int) -> str:
    if n <= 0 or pd.isna(rank):
        return "자료 없음"
    share = float(rank) / n
    if share <= 0.25:
        return "높음"
    if share <= 0.50:
        return "다소 높음"
    if share <= 0.75:
        return "보통"
    return "낮음"


def _with_burden_visuals(df: pd.DataFrame) -> pd.DataFrame:
    """Attach qualitative burden band + size score (bigger = more relative burden)."""
    out = df.copy()
    n = len(out)
    out["burden_score"] = (n + 1) - out["rank"].astype(float)
    out["burden_band"] = out["rank"].map(lambda rank: _burden_band(rank, n))
    return out


def burden_bubbles(df: pd.DataFrame, metric: str) -> alt.Chart:
    """Circle size = relative burden; color = burden band. Avoids redundant rank numbers."""
    meta = METRIC_META[metric]
    sido_col = _sido_column(df)
    plot = df.rename(columns={sido_col: "sido", metric: "value"})
    plot = _with_burden_visuals(plot)
    band_order = ["높음", "다소 높음", "보통", "낮음"]
    return (
        alt.Chart(plot)
        .mark_circle(opacity=0.9, stroke="#0f172a", strokeWidth=0.4)
        .encode(
            y=alt.Y(
                "sido:N",
                title="시·도",
                sort=alt.EncodingSortField(field="burden_score", order="descending"),
            ),
            x=alt.X(
                "value:Q",
                title=f"{meta['label']} ({meta['unit']})",
            ),
            size=alt.Size(
                "burden_score:Q",
                title="상대 부담",
                scale=alt.Scale(range=[80, 1200]),
                legend=None,
            ),
            color=alt.Color(
                "burden_band:N",
                title="상대 부담",
                scale=alt.Scale(
                    domain=band_order,
                    range=["#0f766e", "#14b8a6", "#99f6e4", "#cbd5e1"],
                ),
                sort=band_order,
            ),
            tooltip=[
                alt.Tooltip("sido:N", title="시·도"),
                alt.Tooltip("value:Q", title=meta["label"], format=meta["format"]),
                alt.Tooltip("burden_band:N", title="상대 부담"),
            ],
        )
        .properties(height=560)
    )
