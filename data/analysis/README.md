# 분석용 테이블 (시·도 × 연/월)

재생성:

```powershell
python scripts/preprocess_all.py
python scripts/build_analysis_tables.py
pytest tests/test_analysis_tables.py -q
```

컬럼 설명: `docs/analysis_columns.md`  
조인·품질 검증: `join_validation_report.txt`

## 파일

| 파일 | grain | 용도 |
|---|---|---|
| `ev_sido_monthly.csv` | 시·도×월 | EV 시계열 |
| `ev_sido_annual.csv` | 시·도×연 | 연말 EV + `data_status` |
| `ev_kepco_annual.csv` | 시·도×연 | EV 검증용 (연·시도 유일) |
| `charger_public_fast_sido_annual.csv` | 시·도×연 | 공공 급속 설치 (2022년까지 관측) |
| `charge_sido_monthly.csv` | 시·도×월 | 월별 충전·활성 충전기 |
| `charge_sido_annual.csv` | 시·도×연 | 연간 충전·피크·`data_status` |
| `charge_sido_monthly_panel.csv` | 시·도×월 | EV + 충전량 결합 (`kwh_per_ev` 등) |
| `charge_sido_ytd_compare.csv` | 시·도 | 2024 vs 2025 1~8월 동기간 비교 |
| `sido_year_master.csv` | 시·도×연 | **조인·파생지표 마스터** |

## 마스터 해석

- `charger_stock_end`, `charger_new_install`: 2022년까지만 관측. 2023년 이후는 `NA` + `charger_stock_status=source_stale`
- `fast_per_1000_ev_stock`, `kwh_per_fast_stock`: 2023년 이후 계산하지 않음
- `fast_per_1000_ev_active`, `kwh_per_active_charger`: 활성 충전기 기준 (2023년 이후 참고)
- 2025년 충전량: 8개월 (`data_status=partial`)
- 2026년 EV: 6월 스냅샷, 충전량 없음
