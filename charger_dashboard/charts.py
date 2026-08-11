"""Altair chart builders shared by dashboard pages."""

from __future__ import annotations

import altair as alt
import pandas as pd

from charger_dashboard.data import METRIC_META

COLORS = {
    "ev": "#2563EB",
    "charge": "#0F766E",
    "active": "#D97706",
    "muted": "#64748B",
    "danger": "#DC2626",
    "완속": "#1D4ED8",
    "급속": "#DC2626",
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
    chart_df = df[["시도", *value_columns]].melt(
        id_vars="시도",
        var_name="period",
        value_name="value",
    )
    chart_df["period"] = chart_df["period"].map(
        {
            value_columns[0]: "2024년 1~8월",
            value_columns[1]: "2025년 1~8월",
        }
    )
    return (
        alt.Chart(chart_df)
        .mark_bar()
        .encode(
            x=alt.X("시도:N", title="시·도", sort="-y"),
            y=alt.Y("value:Q", title="동기간 값"),
            color=alt.Color(
                "period:N",
                title="비교기간",
                scale=alt.Scale(range=[COLORS["muted"], COLORS["charge"]]),
            ),
            xOffset="period:N",
            tooltip=[
                alt.Tooltip("시도:N", title="시·도"),
                alt.Tooltip("period:N", title="기간"),
                alt.Tooltip("value:Q", title="값", format=",.2f"),
            ],
        )
        .properties(height=380)
    )


def burden_scatter(df: pd.DataFrame) -> alt.Chart:
    return (
        alt.Chart(df.dropna(subset=["EV천대당활성급속", "활성기당충전량"]))
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
                alt.Tooltip("시도:N", title="시·도"),
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
) -> alt.Chart:
    """Sido choropleth with ASCII top-level join key (Altair-safe) and Korea-centered mercator."""
    meta = METRIC_META[metric]
    values = metric_df.copy()
    if "시도" in values.columns:
        values = values.rename(columns={"시도": "sido"})
    elif "시도" in values.columns:
        values = values.rename(columns={"시도": "sido"})
    values = values[["sido", metric, "rank"]].copy()

    features: list[dict] = []
    for feat in geojson.get("features", []):
        props = feat.get("properties") or {}
        sido = props.get("시도") or props.get("시도") or props.get("sido")
        features.append(
            {
                "type": "Feature",
                "geometry": feat["geometry"],
                "sido": sido,
            }
        )

    return (
        alt.Chart(alt.Data(values=features))
        .mark_geoshape(stroke="#FFFFFF", strokeWidth=1.0)
        .transform_lookup(
            lookup="sido",
            from_=alt.LookupData(values, "sido", [metric, "rank"]),
        )
        .encode(
            color=alt.Color(
                f"{metric}:Q",
                title=f"{meta['label']} ({meta['unit']})",
                scale=alt.Scale(scheme="tealblues"),
            ),
            tooltip=[
                alt.Tooltip("sido:N", title="시·도"),
                alt.Tooltip(
                    f"{metric}:Q",
                    title=meta["label"],
                    format=meta["format"],
                ),
                alt.Tooltip("rank:Q", title="부담 방향 순위"),
            ],
        )
        .project(type="mercator", scale=5500, center=[127.7, 35.9])
        .properties(
            height=560,
            title=f"{year}년 {meta['label']}",
        )
    )


def ranked_bar(df: pd.DataFrame, metric: str) -> alt.Chart:
    meta = METRIC_META[metric]
    return (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X(f"{metric}:Q", title=f"{meta['label']} ({meta['unit']})"),
            y=alt.Y(
                "시도:N",
                title="시·도",
                sort=alt.EncodingSortField(field=metric, order="descending"),
            ),
            color=alt.Color(
                f"{metric}:Q",
                title=meta["label"],
                scale=alt.Scale(scheme="tealblues"),
            ),
            tooltip=[
                alt.Tooltip("시도:N", title="시·도"),
                alt.Tooltip(f"{metric}:Q", title=meta["label"], format=meta["format"]),
                alt.Tooltip("rank:Q", title="순위"),
            ],
        )
        .properties(height=560)
    )
