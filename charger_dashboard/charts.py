"""Chart helpers — Plotly 지도 + Streamlit 기본 차트용 데이터 준비."""

import copy

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from charger_dashboard.data import METRIC_META

# [고급 · 주석 처리] Altair 전체 (line_chart, burden_bubbles, burden_scatter 등)
# import altair as alt
# def line_chart(...): return alt.Chart(df).mark_line()...
# def burden_bubbles(...): return alt.Chart(df).mark_circle()...


def _sido_column(df):
    candidates = {"sido_short", "시도", "sido"}
    for name in df.columns:
        if name in candidates:
            return str(name)
    raise KeyError("시·도 컬럼(sido_short/시도)이 없습니다.")


def _geo_sido(props):
    candidates = {"sido_short", "시도", "sido"}
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


def _burden_band(rank, n):
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


def _with_burden_visuals(df):
    """순위 → 상대 부담 글자 + 점수(클수록 부담 큼)."""
    out = df.copy()
    n = len(out)
    out["burden_score"] = (n + 1) - out["rank"].astype(float)
    out["burden_band"] = out["rank"].map(lambda rank: _burden_band(rank, n))
    return out


def choropleth(geojson, metric_df, metric, year):
    """시·도 색칠 지도 (Plotly).

    흐름을 3단계로만 기억하면 됩니다.
    1) 표에서 시·도 이름 + 숫자(value) 꺼내기
    2) GeoJSON 도형에 같은 시·도 이름 붙이기 (조인 키)
    3) px.choropleth 로 locations=시·도, color=숫자 → 값이 클수록 진하게
    """
    meta = METRIC_META[metric]
    sido_col = _sido_column(metric_df)

    # --- 1) 데이터 표 준비: 시·도 / 값 / 순위 ---
    values = (
        metric_df[[sido_col, metric, "rank"]]
        .rename(columns={sido_col: "sido", metric: "value"})
        .dropna(subset=["value"])
        .copy()
    )
    values["sido"] = values["sido"].astype(str)
    values["value"] = values["value"].astype(float)
    values = _with_burden_visuals(values)

    # --- 2) 지도(GeoJSON) 쪽에도 같은 이름(sido)을 properties에 넣기 ---
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
        fig.update_layout(height=560, title=f"{year}년 {meta['label']}", margin=dict(l=0, r=0, t=48, b=0))
        return fig

    # --- 3) 색칠: color="value" → 숫자 클수록 Teal 색이 진해짐 ---
    fig = px.choropleth(
        values,
        geojson=geo,
        locations="sido",  # 표의 시·도 칼럼
        featureidkey="properties.sido",  # 지도 도형의 시·도 키 (같아야 붙음)
        color="value",  # 이 숫자로 색 강도 결정
        color_continuous_scale="Teal",
        hover_name="sido",
        hover_data={"value": ":,.2f", "burden_band": True, "sido": False, "rank": False, "burden_score": False},
        labels={"value": f"{meta['label']} ({meta['unit']})", "burden_band": "상대 부담"},
        title=f"{year}년 {meta['label']}",
    )
    # 배치: 한국이 화면에 맞게 들어오도록, 배경·여백만 정리
    fig.update_traces(marker_line_width=0.6, marker_line_color="#ffffff")
    fig.update_geos(fitbounds="locations", visible=False, projection_type="mercator", bgcolor="rgba(0,0,0,0)")
    fig.update_layout(
        height=560,
        margin=dict(l=0, r=0, t=48, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        coloraxis_colorbar=dict(title=f"{meta['label']}<br>({meta['unit']})", thickness=14, len=0.72),
    )
    return fig


def burden_bar_frame(df, metric):
    """버블 차트 대신: 시·도를 인덱스로 둔 막대용 표 (st.bar_chart에 넣기)."""
    # [고급 · 주석 처리] Altair mark_circle 버블 (크기=부담, 색=등급)
    # return alt.Chart(plot).mark_circle().encode(size=..., color=...)
    meta = METRIC_META[metric]
    sido_col = _sido_column(df)
    plot = _with_burden_visuals(df.rename(columns={sido_col: "sido", metric: "value"}))
    # 부담 큰 순(위→아래가 되게 bar_chart용으로 값 정렬)
    out = plot.sort_values("burden_score", ascending=True).set_index("sido")[["value"]]
    out = out.rename(columns={"value": meta["label"]})
    return out


def category_bar_chart(df, *, height=None):
    """세로 막대 차트 — x축 카테고리 이름을 가로(0도)로 표시.

    주의:
    - st.bar_chart / horizontal=True 쓰지 않음 (라벨이 y축으로 가거나 세로 회전됨)
    - 막대는 세로 유지, 바 폭은 category 슬롯의 ~0.72로 고정
    df 형식: 인덱스=카테고리(권역·시도·연도), 칼럼 1개=값.
    """
    plot_df = df.reset_index()
    x_col = plot_df.columns[0]
    y_col = plot_df.columns[1]
    xs = plot_df[x_col].astype(str).tolist()
    ys = pd.to_numeric(plot_df[y_col], errors="coerce").tolist()
    n = len(xs)
    if height is None:
        height = max(320, 90 + 22 * min(n, 14))
    # 카테고리 1칸 기준 바 폭 (horizontal 레이아웃으로 바꾸지 않음)
    bar_width = 0.72
    fig = go.Figure(
        data=[
            go.Bar(
                x=xs,
                y=ys,
                marker_color=COLORS["charge"],
                width=[bar_width] * n if n else None,
                hovertemplate="%{x}<br>%{y:,.2f}<extra></extra>",
            )
        ]
    )
    fig.update_layout(
        showlegend=False,
        height=height,
        margin=dict(l=48, r=16, t=12, b=80),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        # bargap은 width 지정 시 무시되는 편 — 레이아웃만 정리
        yaxis=dict(gridcolor="rgba(15,23,42,0.06)", zeroline=True, zerolinecolor="rgba(15,23,42,0.15)"),
        xaxis=dict(
            type="category",
            categoryorder="array",
            categoryarray=xs,
            tickmode="array",
            tickvals=xs,
            ticktext=xs,
            tickangle=0,
            tickfont=dict(size=11 if n <= 10 else 10),
            automargin=True,
            title=None,
        ),
    )
    return fig


def dual_axis_line(df, x_col, left_col, right_col, *, left_name, right_name, height=440):
    """전기차(왼쪽) + 충전량(오른쪽)을 한 장에. 가로로 넓게 쓰는 발표용."""
    plot = df.dropna(subset=[x_col]).copy()
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=plot[x_col],
            y=plot[left_col],
            name=left_name,
            mode="lines",
            line=dict(color=COLORS["ev"], width=2.5),
            hovertemplate="%{x|%Y-%m}<br>" + left_name + ": %{y:,.0f}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=plot[x_col],
            y=plot[right_col],
            name=right_name,
            mode="lines",
            line=dict(color=COLORS["charge"], width=2.5),
            yaxis="y2",
            hovertemplate="%{x|%Y-%m}<br>" + right_name + ": %{y:,.0f}<extra></extra>",
        )
    )
    fig.update_layout(
        height=height,
        margin=dict(l=56, r=64, t=28, b=48),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        xaxis=dict(showgrid=False),
        yaxis=dict(
            title=dict(text=left_name, font=dict(color=COLORS["ev"])),
            tickfont=dict(color=COLORS["ev"]),
            gridcolor="rgba(15,23,42,0.06)",
            zeroline=False,
        ),
        yaxis2=dict(
            title=dict(text=right_name, font=dict(color=COLORS["charge"])),
            tickfont=dict(color=COLORS["charge"]),
            overlaying="y",
            side="right",
            showgrid=False,
            zeroline=False,
        ),
    )
    return fig


def paired_year_bars(v2024, v2025, *, yoy_pct, unit, height=260):
    """동기간 2024 vs 2025 막대 하나. 발표 YoY 차트와 같은 읽기."""
    fig = go.Figure(
        data=[
            go.Bar(
                x=["2024 1–8월", "2025 1–8월"],
                y=[v2024, v2025],
                marker_color=[COLORS["ev"], COLORS["charge"]],
                width=0.55,
                text=[f"{v2024:,.0f}", f"{v2025:,.0f}"],
                textposition="outside",
                hovertemplate="%{x}<br>%{y:,.0f} " + unit + "<extra></extra>",
            )
        ]
    )
    fig.update_layout(
        showlegend=False,
        height=height,
        margin=dict(l=40, r=16, t=36, b=40),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        yaxis=dict(gridcolor="rgba(15,23,42,0.06)", zeroline=False, title=unit),
        xaxis=dict(title=None),
        annotations=[
            dict(
                x=1,
                y=v2025,
                text=f"{yoy_pct:+.1f}%",
                showarrow=False,
                yshift=18,
                font=dict(size=13, color=COLORS["active"]),
            )
        ],
    )
    return fig


def sido_hbar(names, values, *, color=None, unit="", height=320):
    """시·도 가로 막대. 값이 큰 시·도가 위에 오도록 정렬."""
    plot = pd.DataFrame({"sido": list(names), "value": list(values)})
    plot = plot.sort_values("value", ascending=True)
    fig = go.Figure(
        data=[
            go.Bar(
                x=plot["value"],
                y=plot["sido"],
                orientation="h",
                marker_color=color or COLORS["charge"],
                hovertemplate="%{y}<br>%{x:,.1f} " + unit + "<extra></extra>",
            )
        ]
    )
    fig.update_layout(
        showlegend=False,
        height=height,
        margin=dict(l=56, r=24, t=8, b=24),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(gridcolor="rgba(15,23,42,0.06)", zeroline=False, title=unit),
        yaxis=dict(title=None),
    )
    return fig
