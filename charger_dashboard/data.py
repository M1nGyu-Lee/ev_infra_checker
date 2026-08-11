"""Cached data access and analysis helpers for Streamlit pages."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "data" / "analysis"
FORECAST = ROOT / "data" / "forecast"
PROCESSED = ROOT / "data" / "processed"
GEOJSON_PATH = ROOT / "data" / "geojson" / "korea_sido_wgs84_light.geojson"
if not GEOJSON_PATH.exists():
    GEOJSON_PATH = ROOT / "data" / "geojson" / "korea_sido_wgs84.geojson"

SIDO_ORDER = [
    "서울", "부산", "대구", "인천", "광주", "대전", "울산", "세종",
    "경기", "강원", "충북", "충남", "전북", "전남", "경북", "경남", "제주",
]

METRIC_META = {
    "전기차등록대수": {
        "label": "전기차 등록대수",
        "unit": "대",
        "format": ",.0f",
        "help": "해당 연도 12월 등록대수이며, 12월이 없으면 최종 관측월입니다.",
    },
    "충전량_kWh": {
        "label": "환경부 공공급속 충전량",
        "unit": "kWh",
        "format": ",.0f",
        "help": "환경부 공공급속 충전망에서 발생한 충전량입니다.",
    },
    "활성충전기수": {
        "label": "활성 급속충전기",
        "unit": "기",
        "format": ",.0f",
        "help": "해당 기간에 양수 충전량 또는 충전횟수가 기록된 고유 충전기 수입니다.",
    },
    "EV천대당설치급속": {
        "label": "EV 1,000대당 설치 급속기",
        "unit": "기",
        "format": ",.2f",
        "help": "환경부 공공급속 설비 재고 기준이며 2022년까지만 사용합니다.",
    },
    "EV천대당활성급속": {
        "label": "EV 1,000대당 활성 급속기",
        "unit": "기",
        "format": ",.2f",
        "help": "활성 충전기 기준 보조 공급지표입니다.",
    },
    "활성기당충전량": {
        "label": "활성기당 충전량",
        "unit": "kWh/기",
        "format": ",.0f",
        "help": "환경부 공공급속 충전량을 활성 충전기 수로 나눈 이용부담 지표입니다.",
    },
    "EV당충전량": {
        "label": "EV당 월 충전량",
        "unit": "kWh/대",
        "format": ",.2f",
        "help": "동일 월의 환경부 공공급속 충전량을 등록 EV로 나눈 값입니다.",
    },
}


def _read_csv(name: str) -> pd.DataFrame:
    path = ANALYSIS / name
    if not path.exists():
        raise FileNotFoundError(
            f"분석 파일이 없습니다: {path}. "
            "python scripts/build_analysis_tables.py를 먼저 실행하세요."
        )
    return pd.read_csv(path, encoding="utf-8-sig")


def _read_forecast_csv(name: str) -> pd.DataFrame:
    path = FORECAST / name
    if not path.exists():
        raise FileNotFoundError(
            f"예측 파일이 없습니다: {path}. "
            "python scripts/build_charge_forecast.py를 먼저 실행하세요."
        )
    return pd.read_csv(path, encoding="utf-8-sig")


@st.cache_data(show_spinner=False)
def load_master() -> pd.DataFrame:
    return _read_csv("sido_year_master.csv")


@st.cache_data(show_spinner=False)
def load_ev_monthly() -> pd.DataFrame:
    df = _read_csv("ev_sido_monthly.csv")
    df["date"] = pd.to_datetime(df["기준월"], format="%Y-%m")
    return df


@st.cache_data(show_spinner=False)
def load_charge_monthly() -> pd.DataFrame:
    df = _read_csv("charge_sido_monthly.csv")
    df["date"] = pd.to_datetime(df["기준월"], format="%Y-%m")
    return df


@st.cache_data(show_spinner=False)
def load_charge_panel() -> pd.DataFrame:
    df = _read_csv("charge_sido_monthly_panel.csv")
    df["date"] = pd.to_datetime(df["기준월"], format="%Y-%m")
    return df


@st.cache_data(show_spinner=False)
def load_national_charge_ev_monthly() -> pd.DataFrame:
    """Pre-aggregated national EV + public-fast charge series (fast path for trends)."""
    path = ANALYSIS / "national_charge_ev_monthly.csv"
    if not path.exists():
        panel = load_charge_panel()
        df = (
            panel.groupby("기준월", as_index=False)[
                ["전기차등록대수", "충전량_kWh", "활성충전기수"]
            ]
            .sum(min_count=1)
        )
    else:
        df = pd.read_csv(path, encoding="utf-8-sig")
    df["date"] = pd.to_datetime(df["기준월"], format="%Y-%m")
    return df


@st.cache_data(show_spinner=False)
def load_charge_annual() -> pd.DataFrame:
    return _read_csv("charge_sido_annual.csv")


@st.cache_data(show_spinner=False)
def load_charger_annual() -> pd.DataFrame:
    return _read_csv("charger_public_fast_sido_annual.csv")


@st.cache_data(show_spinner=False)
def load_ytd_compare() -> pd.DataFrame:
    return _read_csv("charge_sido_ytd_compare.csv")


@st.cache_data(show_spinner=False)
def load_charge_trend() -> pd.DataFrame:
    df = _read_csv("charge_sido_monthly_trend.csv")
    df["date"] = pd.to_datetime(df["기준월"], format="%Y-%m")
    return df


@st.cache_data(show_spinner=False)
def load_charge_forecast() -> pd.DataFrame:
    return _read_forecast_csv("charge_sido_monthly_forecast.csv")


@st.cache_data(show_spinner=False)
def load_forecast_manifest() -> dict:
    path = FORECAST / "forecast_run_manifest.json"
    if not path.exists():
        raise FileNotFoundError(
            f"예측 메타가 없습니다: {path}. "
            "python scripts/build_charge_forecast.py를 먼저 실행하세요."
        )
    with path.open(encoding="utf-8") as file:
        return json.load(file)


@st.cache_data(show_spinner=False)
def load_forecast_methodology_text() -> str:
    path = FORECAST / "forecast_methodology.md"
    if not path.exists():
        raise FileNotFoundError(
            f"예측 방법론 문서가 없습니다: {path}. "
            "python scripts/build_charge_forecast.py를 먼저 실행하세요."
        )
    return path.read_text(encoding="utf-8")


@st.cache_data(show_spinner=False)
def load_chargeinfo_region_stock() -> pd.DataFrame:
    path = PROCESSED / "chargeinfo_region_stock_annual.csv"
    if not path.exists():
        raise FileNotFoundError(
            f"차지인포 누적 데이터 없음: {path}. "
            "python scripts/preprocess_chargeinfo_stock.py를 실행하세요."
        )
    return pd.read_csv(path, encoding="utf-8-sig")


@st.cache_data(show_spinner=False)
def load_chargeinfo_region_yoy() -> pd.DataFrame:
    path = PROCESSED / "chargeinfo_region_stock_yoy.csv"
    if not path.exists():
        raise FileNotFoundError(
            f"차지인포 YoY 없음: {path}. "
            "python scripts/preprocess_chargeinfo_stock.py를 실행하세요."
        )
    return pd.read_csv(path, encoding="utf-8-sig")


@st.cache_data(show_spinner=False)
def load_chargeinfo_region_stock_monthly() -> pd.DataFrame:
    path = PROCESSED / "chargeinfo_region_stock_monthly.csv"
    if not path.exists():
        raise FileNotFoundError(
            f"차지인포 월별 누적 없음: {path}. "
            "python scripts/preprocess_chargeinfo_monthly.py를 실행하세요."
        )
    return pd.read_csv(path, encoding="utf-8-sig")


@st.cache_data(show_spinner=False)
def load_chargeinfo_slow_fast_ratio_monthly() -> pd.DataFrame:
    path = PROCESSED / "chargeinfo_region_slow_fast_ratio_monthly.csv"
    if not path.exists():
        raise FileNotFoundError(
            f"차지인포 완속/급속 비율 없음: {path}. "
            "python scripts/preprocess_chargeinfo_monthly.py를 실행하세요."
        )
    return pd.read_csv(path, encoding="utf-8-sig")


@st.cache_data(show_spinner=False)
def load_chargeinfo_ev_per_charger_wide() -> pd.DataFrame:
    path = PROCESSED / "chargeinfo_ev_per_charger_ratio_wide.csv"
    if not path.exists():
        raise FileNotFoundError(
            f"차지인포 EV 1대당 보급률 없음: {path}. "
            "python scripts/preprocess_chargeinfo_ev_ratio.py를 실행하세요."
        )
    return pd.read_csv(path, encoding="utf-8-sig")


@st.cache_data(show_spinner=False)
def load_chargeinfo_ev_per_charger_avg() -> pd.DataFrame:
    path = PROCESSED / "chargeinfo_ev_per_charger_ratio_avg.csv"
    if not path.exists():
        raise FileNotFoundError(
            f"차지인포 EV 1대당 평균 없음: {path}. "
            "python scripts/preprocess_chargeinfo_ev_ratio.py를 실행하세요."
        )
    return pd.read_csv(path, encoding="utf-8-sig")


@st.cache_data(show_spinner=False)
def load_kepco_station_annual() -> pd.DataFrame:
    path = PROCESSED / "kepco_station_sido_annual.csv"
    if not path.exists():
        raise FileNotFoundError(
            f"한전 충전소 현황이 없습니다: {path}. "
            "python scripts/preprocess_kepco_aux.py를 먼저 실행하세요."
        )
    return pd.read_csv(path, encoding="utf-8-sig")


@st.cache_data(show_spinner=False)
def load_kepco_charge_trend() -> pd.DataFrame:
    df = _read_csv("kepco_charge_sido_monthly_trend.csv")
    df["date"] = pd.to_datetime(df["기준월"], format="%Y-%m")
    return df


@st.cache_data(show_spinner=False)
def load_kepco_forecast() -> pd.DataFrame:
    return _read_forecast_csv("kepco_charge_sido_monthly_forecast.csv")


@st.cache_data(show_spinner=False)
def load_kepco_forecast_manifest() -> dict:
    path = FORECAST / "kepco_forecast_run_manifest.json"
    if not path.exists():
        raise FileNotFoundError(
            f"한전 보완 메타가 없습니다: {path}. "
            "python scripts/build_kepco_charge_fill.py를 먼저 실행하세요."
        )
    with path.open(encoding="utf-8") as file:
        return json.load(file)


@st.cache_data(show_spinner=False)
def load_kepco_forecast_methodology_text() -> str:
    path = FORECAST / "forecast_methodology_kepco.md"
    if not path.exists():
        raise FileNotFoundError(
            f"한전 방법론 문서가 없습니다: {path}. "
            "python scripts/build_kepco_charge_fill.py를 먼저 실행하세요."
        )
    return path.read_text(encoding="utf-8")


@st.cache_data(show_spinner=False)
def load_geojson() -> dict:
    with GEOJSON_PATH.open(encoding="utf-8") as file:
        return json.load(file)


def available_years() -> list[int]:
    return sorted(load_master()["연도"].dropna().astype(int).unique().tolist())


def latest_complete_charge_year() -> int:
    annual = load_charge_annual()
    complete = annual.loc[annual["기간상태"] == "complete", "연도"]
    return int(complete.max())


def national_year(master: pd.DataFrame, year: int) -> pd.Series:
    subset = master[master["연도"] == year]
    additive = [
        "전기차등록대수",
        "설치누적",
        "신규설치",
        "충전량_kWh",
        "충전횟수",
        "충전시간_h",
        "활성충전기수",
    ]
    values = {column: subset[column].sum(min_count=1) for column in additive}
    values["관측월수"] = subset["관측월수"].max()
    values["사용기준월"] = subset["사용기준월"].max()
    values["기간상태"] = (
        "partial" if (subset["기간상태"] == "partial").any() else "complete"
    )
    if values["전기차등록대수"] and pd.notna(values["활성충전기수"]):
        values["EV천대당활성급속"] = (
            values["활성충전기수"] * 1000 / values["전기차등록대수"]
        )
    else:
        values["EV천대당활성급속"] = pd.NA
    if values["활성충전기수"] and pd.notna(values["충전량_kWh"]):
        values["활성기당충전량"] = (
            values["충전량_kWh"] / values["활성충전기수"]
        )
    else:
        values["활성기당충전량"] = pd.NA
    return pd.Series(values)


def percent_change(current: float | int, previous: float | int) -> float | None:
    if pd.isna(current) or pd.isna(previous) or previous == 0:
        return None
    return (current / previous - 1) * 100


def filter_regions(df: pd.DataFrame, regions: list[str]) -> pd.DataFrame:
    return df[df["시도"].isin(regions)].copy()


def rank_for_map(master: pd.DataFrame, year: int, metric: str) -> pd.DataFrame:
    columns = ["시도", metric, "기간상태", "설비상태"]
    out = master.loc[master["연도"] == year, columns].dropna(subset=[metric]).copy()
    if out.empty:
        return out
    ascending = metric in {"EV천대당설치급속", "EV천대당활성급속"}
    out["rank"] = out[metric].rank(method="min", ascending=ascending).astype("Int64")
    out["percentile"] = out[metric].rank(pct=True) * 100
    return out
