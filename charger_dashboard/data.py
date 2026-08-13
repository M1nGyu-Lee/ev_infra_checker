"""Cached data access and analysis helpers for Streamlit pages."""

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

# Chargeinfo packs multiple provinces into 8 mixed regions (city + province groups).
CHARGEINFO_REGION_LABEL = {
    "서울": "서울",
    "인천": "인천",
    "제주": "제주",
    "경기": "경기권",
    "강원": "강원권",
    "충청": "충청권",
    "전라": "전라권",
    "경상": "경상권",
}

# Map metrics where "상대 부담" is meaningful (not raw stock counts).
BURDEN_METRICS = {
    "fast_per_1000_ev_stock",
    "fast_per_1000_ev_active",
    "kwh_per_active_charger",
    "charge_kwh_sum",
}

METRIC_META = {
    "ev_count": {
        "label": "전기차 등록대수",
        "unit": "대",
        "format": ",.0f",
        "help": "해당 연도 12월 등록대수이며, 12월이 없으면 최종 관측월입니다.",
    },
    "charge_kwh_sum": {
        "label": "환경부 공공급속 충전량",
        "unit": "kWh",
        "format": ",.0f",
        "help": "환경부 공공급속 충전망에서 발생한 충전량입니다.",
    },
    "active_charger_count": {
        "label": "실제 가동 충전기",
        "unit": "기",
        "format": ",.0f",
        "help": "해당 기간에 양수 충전량 또는 충전횟수가 기록된 고유 충전기 수입니다.",
    },
    "fast_per_1000_ev_stock": {
        "label": "EV 1,000대당 설치 급속기",
        "unit": "기",
        "format": ",.2f",
        "help": "환경부 공공급속 설비 재고 기준이며 2022년까지만 사용합니다.",
    },
    "fast_per_1000_ev_active": {
        "label": "EV 1,000대당 실제 가동 충전기",
        "unit": "기",
        "format": ",.2f",
        "help": "실제 가동 충전기 기준 보조 공급지표입니다.",
    },
    "kwh_per_active_charger": {
        "label": "실제 가동 1기당 충전량",
        "unit": "kWh/기",
        "format": ",.0f",
        "help": "환경부 공공급속 충전량을 실제 가동 충전기 수로 나눈 이용부담 지표입니다.",
    },
    "kwh_per_ev": {
        "label": "EV당 월 충전량",
        "unit": "kWh/대",
        "format": ",.2f",
        "help": "동일 월의 환경부 공공급속 충전량을 등록 EV로 나눈 값입니다.",
    },
}

# share_package(한글 CSV) ↔ 로컬(영문 CSV) 호환. 로드 직후 영문 키로 통일한다.
COLUMN_ALIASES = {
    "연도": "year",
    "월": "month",
    "기준월": "year_month",
    "시도": "sido_short",
    "권역": "region_name",
    "기간상태": "data_status",
    "전기차등록대수": "ev_count",
    "사용기준월": "ref_month_used",
    "설치누적": "charger_stock_end",
    "신규설치": "charger_new_install",
    "설비상태": "charger_stock_status",
    "충전량_kWh": "charge_kwh_sum",
    "충전횟수": "charge_count_sum",
    "충전시간_h": "charge_hours_sum",
    "활성충전기수": "active_charger_count",
    "관측월수": "month_count",
    "월평균충전량": "avg_monthly_kwh",
    "피크월": "peak_month",
    "피크충전량": "peak_kwh",
    "평균초과율": "peak_above_avg_pct",
    "EV천대당설치급속": "fast_per_1000_ev_stock",
    "EV천대당활성급속": "fast_per_1000_ev_active",
    "설치급속당충전량": "kwh_per_fast_stock",
    "활성기당충전량": "kwh_per_active_charger",
    "EV당충전량": "kwh_per_ev",
    "EV당충전횟수": "count_per_ev",
    "충전량_2024_YTD": "charge_kwh_2024_ytd",
    "충전량_2025_YTD": "charge_kwh_2025_ytd",
    "충전량_YTD증감률": "charge_kwh_ytd_yoy_pct",
    "충전횟수_2024_YTD": "charge_count_2024_ytd",
    "충전횟수_2025_YTD": "charge_count_2025_ytd",
    "활성기_2024_YTD": "active_charger_2024_ytd",
    "활성기_2025_YTD": "active_charger_2025_ytd",
    "EV_2024_YTD평균": "ev_count_2024_ytd_avg",
    "EV_2025_YTD평균": "ev_count_2025_ytd_avg",
    "EV당충전량_2024_YTD": "kwh_per_ev_2024_ytd",
    "EV당충전량_2025_YTD": "kwh_per_ev_2025_ytd",
    "비교월수": "months_compared",
    "급속": "fast",
    "완속": "slow",
    "합계누적": "total_stock",
    "완속급속비": "slow_fast_ratio",
    "급속비중": "fast_share_pct",
    "완속비중": "slow_share_pct",
    "합계비중": "total_share_pct",
    "누적충전기": "charger_stock",
    "전국대비비중": "share_pct",
    "전년대비증감률": "yoy_pct",
    "급속_대당": "fast_per_ev",
    "완속_대당": "slow_per_ev",
    "합계_대당": "total_per_ev",
    "완속급속강도비": "slow_fast_intensity_ratio",
    "평균_대당충전기": "avg_per_ev",
    "대당충전기": "per_ev",
    "권역구성비": "region_share_pct",
    "평균여부": "is_avg",
    "지리단위": "geo_level",
    "출처ID": "source_id",
    "지표코드": "metric_code",
    "지표명": "metric_name_kr",
    "충전속도코드": "speed_code",
    "충전속도": "speed_label",
    "충전소수": "station_count",
    "예측값": "forecast",
    "관측값": "observed_value",
    "하한_80": "lower_80",
    "상한_80": "upper_80",
    "모형ID": "model_id",
    "잔차": "residual",
}


# 캐시 무효화 · Cloud 재배포 시 구버전 한글 컬럼 DF가 남지 않게 함
DATA_SCHEMA_VERSION = 3


def col(df: pd.DataFrame, *names: str) -> str:
    """영문/한글 후보 중 실제 존재하는 컬럼명 반환."""
    for name in names:
        if name in df.columns:
            return name
    raise KeyError(f"컬럼 없음: {names} / 실제={list(df.columns)}")


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """한글(share_package) 컬럼명을 영문 분석 키로 통일."""
    out = df.copy()
    out.columns = [str(c).replace("\ufeff", "").strip() for c in out.columns]
    rename = {c: COLUMN_ALIASES[c] for c in out.columns if c in COLUMN_ALIASES}
    out = out.rename(columns=rename)
    # 동일 영문키로 중복되면 첫 컬럼만 유지
    if out.columns.duplicated().any():
        out = out.loc[:, ~out.columns.duplicated()].copy()
    # ref_ym 별칭: 일부 차지인포/월 표는 year_month 를 ref_ym 로도 씀
    if "year_month" in out.columns and "ref_ym" not in out.columns:
        out["ref_ym"] = out["year_month"]
    if "ref_ym" in out.columns and "year_month" not in out.columns:
        out["year_month"] = out["ref_ym"]
    return out


def _parse_month_col(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col_name in ("year_month", "ref_ym", "기준월"):
        if col_name in out.columns:
            out["date"] = pd.to_datetime(out[col_name], format="%Y-%m", errors="coerce")
            break
    return out


def _read_csv(name):
    path = ANALYSIS / name
    if not path.exists():
        raise FileNotFoundError(
            f"분석 파일이 없습니다: {path}. "
            "python scripts/build_analysis_tables.py를 먼저 실행하세요."
        )
    return normalize_columns(pd.read_csv(path, encoding="utf-8-sig"))


def _read_forecast_csv(name):
    path = FORECAST / name
    if not path.exists():
        raise FileNotFoundError(
            f"예측 파일이 없습니다: {path}. "
            "python scripts/build_charge_forecast.py를 먼저 실행하세요."
        )
    return normalize_columns(pd.read_csv(path, encoding="utf-8-sig"))


def _read_processed_csv(path: Path, missing_msg: str):
    if not path.exists():
        raise FileNotFoundError(missing_msg)
    return normalize_columns(pd.read_csv(path, encoding="utf-8-sig"))


# @st.cache_data: CSV를 한 번 읽고 메모리에 보관 → 페이지 다시 그릴 때 파일 재읽기 생략
# (개념만 배웠다면: 함수 위에 붙이는 "기억해 두기" 스티커라고 보면 됨)
@st.cache_data(show_spinner=False)
def load_master():
    _ = DATA_SCHEMA_VERSION
    return _read_csv("sido_year_master.csv")


@st.cache_data(show_spinner=False)
def load_ev_monthly():
    _ = DATA_SCHEMA_VERSION
    df = _read_csv("ev_sido_monthly.csv")
    return _parse_month_col(df)


@st.cache_data(show_spinner=False)
def load_charge_monthly():
    df = _read_csv("charge_sido_monthly.csv")
    return _parse_month_col(df)


@st.cache_data(show_spinner=False)
def load_charge_panel():
    _ = DATA_SCHEMA_VERSION
    df = _read_csv("charge_sido_monthly_panel.csv")
    return _parse_month_col(df)


@st.cache_data(show_spinner=False)
def load_national_charge_ev_monthly():
    """Pre-aggregated national EV + public-fast charge series (fast path for trends)."""
    _ = DATA_SCHEMA_VERSION
    path = ANALYSIS / "national_charge_ev_monthly.csv"
    if not path.exists():
        panel = load_charge_panel()
        df = (
            panel.groupby("year_month", as_index=False)[
                ["ev_count", "charge_kwh_sum", "active_charger_count"]
            ]
            .sum(min_count=1)
        )
    else:
        df = normalize_columns(pd.read_csv(path, encoding="utf-8-sig"))
    return _parse_month_col(df)


@st.cache_data(show_spinner=False)
def load_charge_annual():
    _ = DATA_SCHEMA_VERSION
    return _read_csv("charge_sido_annual.csv")


@st.cache_data(show_spinner=False)
def load_charger_annual():
    return _read_csv("charger_public_fast_sido_annual.csv")


@st.cache_data(show_spinner=False)
def load_ytd_compare():
    return _read_csv("charge_sido_ytd_compare.csv")


@st.cache_data(show_spinner=False)
def load_charge_trend():
    df = _read_csv("charge_sido_monthly_trend.csv")
    return _parse_month_col(df)


@st.cache_data(show_spinner=False)
def load_charge_forecast():
    return _read_forecast_csv("charge_sido_monthly_forecast.csv")


@st.cache_data(show_spinner=False)
def load_forecast_manifest():
    path = FORECAST / "forecast_run_manifest.json"
    if not path.exists():
        raise FileNotFoundError(
            f"예측 메타가 없습니다: {path}. "
            "python scripts/build_charge_forecast.py를 먼저 실행하세요."
        )
    with path.open(encoding="utf-8") as file:
        return json.load(file)


@st.cache_data(show_spinner=False)
def load_forecast_methodology_text():
    path = FORECAST / "forecast_methodology.md"
    if not path.exists():
        raise FileNotFoundError(
            f"예측 방법론 문서가 없습니다: {path}. "
            "python scripts/build_charge_forecast.py를 먼저 실행하세요."
        )
    return path.read_text(encoding="utf-8")


@st.cache_data(show_spinner=False)
def load_chargeinfo_region_stock():
    _ = DATA_SCHEMA_VERSION
    path = PROCESSED / "chargeinfo_region_stock_annual.csv"
    return _read_processed_csv(
        path,
        f"차지인포 누적 데이터 없음: {path}. "
        "python scripts/preprocess_chargeinfo_stock.py를 실행하세요.",
    )


@st.cache_data(show_spinner=False)
def load_chargeinfo_region_yoy():
    path = PROCESSED / "chargeinfo_region_stock_yoy.csv"
    return _read_processed_csv(
        path,
        f"차지인포 YoY 없음: {path}. "
        "python scripts/preprocess_chargeinfo_stock.py를 실행하세요.",
    )


@st.cache_data(show_spinner=False)
def load_chargeinfo_region_stock_monthly():
    _ = DATA_SCHEMA_VERSION
    path = PROCESSED / "chargeinfo_region_stock_monthly.csv"
    return _read_processed_csv(
        path,
        f"차지인포 월별 누적 없음: {path}. "
        "python scripts/preprocess_chargeinfo_monthly.py를 실행하세요.",
    )


@st.cache_data(show_spinner=False)
def load_chargeinfo_slow_fast_ratio_monthly():
    _ = DATA_SCHEMA_VERSION
    path = PROCESSED / "chargeinfo_region_slow_fast_ratio_monthly.csv"
    return _read_processed_csv(
        path,
        f"차지인포 완속/급속 비율 없음: {path}. "
        "python scripts/preprocess_chargeinfo_monthly.py를 실행하세요.",
    )


@st.cache_data(show_spinner=False)
def load_chargeinfo_ev_per_charger_wide():
    _ = DATA_SCHEMA_VERSION
    path = PROCESSED / "chargeinfo_ev_per_charger_ratio_wide.csv"
    return _read_processed_csv(
        path,
        f"차지인포 EV 1대당 보급률 없음: {path}. "
        "python scripts/preprocess_chargeinfo_ev_ratio.py를 실행하세요.",
    )


@st.cache_data(show_spinner=False)
def load_chargeinfo_ev_per_charger_avg():
    _ = DATA_SCHEMA_VERSION
    path = PROCESSED / "chargeinfo_ev_per_charger_ratio_avg.csv"
    return _read_processed_csv(
        path,
        f"차지인포 EV 1대당 평균 없음: {path}. "
        "python scripts/preprocess_chargeinfo_ev_ratio.py를 실행하세요.",
    )


@st.cache_data(show_spinner=False)
def load_kepco_station_annual():
    path = PROCESSED / "kepco_station_sido_annual.csv"
    return _read_processed_csv(
        path,
        f"한전 충전소 현황이 없습니다: {path}. "
        "python scripts/preprocess_kepco_aux.py를 먼저 실행하세요.",
    )


@st.cache_data(show_spinner=False)
def load_kepco_charge_trend():
    df = _read_csv("kepco_charge_sido_monthly_trend.csv")
    return _parse_month_col(df)


@st.cache_data(show_spinner=False)
def load_kepco_forecast():
    return _read_forecast_csv("kepco_charge_sido_monthly_forecast.csv")


@st.cache_data(show_spinner=False)
def load_kepco_forecast_manifest():
    path = FORECAST / "kepco_forecast_run_manifest.json"
    if not path.exists():
        raise FileNotFoundError(
            f"한전 보완 메타가 없습니다: {path}. "
            "python scripts/build_kepco_charge_fill.py를 먼저 실행하세요."
        )
    with path.open(encoding="utf-8") as file:
        return json.load(file)


@st.cache_data(show_spinner=False)
def load_kepco_forecast_methodology_text():
    path = FORECAST / "forecast_methodology_kepco.md"
    if not path.exists():
        raise FileNotFoundError(
            f"한전 방법론 문서가 없습니다: {path}. "
            "python scripts/build_kepco_charge_fill.py를 먼저 실행하세요."
        )
    return path.read_text(encoding="utf-8")


@st.cache_data(show_spinner=False)
def load_geojson():
    with GEOJSON_PATH.open(encoding="utf-8") as file:
        return json.load(file)


def available_years():
    master = load_master()
    year_col = col(master, "year", "연도")
    return sorted(master[year_col].dropna().astype(int).unique().tolist())


def latest_complete_charge_year():
    annual = load_charge_annual()
    status_col = col(annual, "data_status", "기간상태")
    year_col = col(annual, "year", "연도")
    complete = annual.loc[annual[status_col] == "complete", year_col]
    return int(complete.max())


def national_year(master, year):
    year_col = col(master, "year", "연도")
    subset = master[master[year_col] == year]
    additive = [
        ("ev_count", "전기차등록대수"),
        ("charger_stock_end", "설치누적"),
        ("charger_new_install", "신규설치"),
        ("charge_kwh_sum", "충전량_kWh"),
        ("charge_count_sum", "충전횟수"),
        ("charge_hours_sum", "충전시간_h"),
        ("active_charger_count", "활성충전기수"),
    ]
    values = {}
    for en, kr in additive:
        key = en if en in subset.columns else (kr if kr in subset.columns else None)
        values[en] = subset[key].sum(min_count=1) if key else pd.NA
    mc = col(subset, "month_count", "관측월수") if any(
        c in subset.columns for c in ("month_count", "관측월수")
    ) else None
    values["month_count"] = subset[mc].max() if mc else pd.NA
    rm = next((c for c in ("ref_month_used", "사용기준월") if c in subset.columns), None)
    values["ref_month_used"] = subset[rm].max() if rm else pd.NA
    ds = next((c for c in ("data_status", "기간상태") if c in subset.columns), None)
    values["data_status"] = (
        "partial" if ds and (subset[ds] == "partial").any() else "complete"
    )
    if values["ev_count"] and pd.notna(values["active_charger_count"]):
        values["fast_per_1000_ev_active"] = (
            values["active_charger_count"] * 1000 / values["ev_count"]
        )
    else:
        values["fast_per_1000_ev_active"] = pd.NA
    if values["active_charger_count"] and pd.notna(values["charge_kwh_sum"]):
        values["kwh_per_active_charger"] = (
            values["charge_kwh_sum"] / values["active_charger_count"]
        )
    else:
        values["kwh_per_active_charger"] = pd.NA
    return pd.Series(values)


def percent_change(current, previous):
    if pd.isna(current) or pd.isna(previous) or previous == 0:
        return None
    return (current / previous - 1) * 100


def filter_regions(df, regions):
    sido = col(df, "sido_short", "시도")
    return df[df[sido].isin(regions)].copy()


def rank_for_map(master, year, metric):
    year_col = col(master, "year", "연도")
    sido_col = col(master, "sido_short", "시도")
    metric_col = col(master, metric, *[
        k for k, v in COLUMN_ALIASES.items() if v == metric
    ])
    extras = []
    for en, kr in (("data_status", "기간상태"), ("charger_stock_status", "설비상태")):
        if en in master.columns:
            extras.append(en)
        elif kr in master.columns:
            extras.append(kr)
    columns = [sido_col, metric_col, *extras]
    out = master.loc[master[year_col] == year, columns].dropna(subset=[metric_col]).copy()
    if out.empty:
        return out
    # 표준 영문 키로 맞춤 (차트·페이지 공통)
    out = out.rename(
        columns={
            sido_col: "sido_short",
            metric_col: metric,
            **{
                c: ("data_status" if c in ("data_status", "기간상태") else "charger_stock_status")
                for c in extras
            },
        }
    )
    ascending = metric in {"fast_per_1000_ev_stock", "fast_per_1000_ev_active"}
    out["rank"] = out[metric].rank(method="min", ascending=ascending).astype("Int64")
    out["percentile"] = out[metric].rank(pct=True) * 100
    return out
