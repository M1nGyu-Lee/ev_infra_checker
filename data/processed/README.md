# Processed CSV (UTF-8 BOM)

원본은 `전기차 현황 csv데이터/`, `전기차 충전소 현황 데이터/`에 그대로 유지합니다.

재생성:

```powershell
python scripts/preprocess_all.py
python scripts/build_analysis_tables.py
```

## 분석용 컬럼만 유지

| 파일 | grain | 컬럼 |
|---|---|---|
| `ev_molit_monthly.csv` | 시·도×월 | `ref_year`, `ref_month`, `ref_ym`, `sido_short`, `ev_count` |
| `ev_kepco_monthly.csv` | 시·도×기준일 | `ref_date`, `ref_year`, `ref_month`, `ref_ym`, `sido_short`, `ev_count` |
| `charger_facility.csv` | 충전기 | `install_year`, `sido_short`, `charger_class_lcl`, `operator_lcl` |
| `charge_public_fast_monthly.csv` | 충전기×연월 | `sido_short`, `year`, `month`, `year_month`, `station_id`, `charger_id`, `charge_kwh`, `charge_count`, `charge_hours` |
| `chargeinfo_region_stock_annual.csv` | 권역×연도 | `year`, `region_name`, `charger_stock`, `share_pct`, `data_status` |
| `chargeinfo_region_stock_yoy.csv` | 권역×연도 | `year`, `region_name`, `charger_stock`, `yoy_pct`, `data_status` |
| `chargeinfo_region_stock_monthly.csv` | 권역×월×속도 | `ref_ym`, `year`, `month`, `region_name`, `charger_class_lcl`, `charger_stock`, `share_pct` |
| `chargeinfo_region_slow_fast_ratio_monthly.csv` | 권역×월 | `ref_ym`, `region_name`, `fast`, `slow`, `slow_fast_ratio`, `fast_share_pct` |
| `chargeinfo_ev_per_charger_ratio_monthly.csv` | 권역×월×지표 | `metric`, `ref_ym`, `region_name`, `chargers_per_ev`, `region_share_pct` |
| `chargeinfo_ev_per_charger_ratio_wide.csv` | 권역×월 | `fast_per_ev`, `slow_per_ev`, `total_per_ev`, `slow_fast_intensity_ratio` |
| `chargeinfo_ev_per_charger_ratio_avg.csv` | 지표×월 | `metric`, `ref_ym`, `avg_chargers_per_ev` |

조인 키: `sido_short` (+ `year` / `ref_ym` / `year_month`). 차지인포는 **8권역**이라 시·도 마스터와 직접 조인하지 않습니다.

차지인포 재생성:

```powershell
python scripts/preprocess_chargeinfo_stock.py
python scripts/preprocess_chargeinfo_monthly.py
python scripts/preprocess_chargeinfo_ev_ratio.py
```
