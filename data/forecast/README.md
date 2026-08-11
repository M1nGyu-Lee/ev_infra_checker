# 예측·보완 산출물

## 환경부 공공급속 (2025-09~12)

| 파일 | 설명 |
|---|---|
| `forecast_methodology.md` | 방법론 (환경부 관측만 사용) |
| `charge_sido_monthly_forecast.csv` | 추정값 |
| `../analysis/charge_sido_monthly_trend.csv` | 관측+추정 통합 |

생성: `python scripts/build_charge_forecast.py`

## 한전 급속 충전량 (2019~2025 보완)

| 파일 | 설명 |
|---|---|
| `forecast_methodology_kepco.md` | 방법론 (환경부+부하+충전소 현황) |
| `kepco_forecast_run_manifest.json` | 가중치·비율·백테스트 메타 |
| `kepco_charge_sido_monthly_forecast.csv` | 추정 구간만 |
| `../analysis/kepco_charge_sido_monthly_trend.csv` | 관측+보완 통합 |

전처리: `python scripts/preprocess_kepco_aux.py`  
생성: `python scripts/build_kepco_charge_fill.py`

**수치보다 방법론 문서를 먼저 확인하세요.**
