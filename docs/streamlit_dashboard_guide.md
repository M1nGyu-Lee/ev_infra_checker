# Streamlit 대시보드 구성 및 실행

## 실행

```powershell
pip install -r requirements-app.txt
python -m streamlit run streamlit_app.py
```

공유·Cloud용은 `share_package/`에서 동일 명령으로 실행한다.

## 발표 우선순위별 네비게이션

| 순위 | 대상 | 탭 | 한 화면 메시지 |
|---|---|---|---|
| 1순위 | 정책 결정 | **발표 브리핑** | 동기간 괴리 → 부담 지도 → Q4 겹침 → 배치 방향 |
| 탐색 | 정책·실무 | 지도 · 급속 추이 · 지역 상세 | 연도·지표 필터로 부담·피크 깊게 보기 |
| 2순위 | 사업자 | 급·완속 설치 판단 | 8권역 급속 비중·보급 강도 힌트 (설치 확정 아님) |
| 3순위 | 기초 | EV·충전소 총량 | 전국 EV·차지인포 구축 규모 |
| 참고 | 담당자 | 데이터 안내 | 파일·방법론·한계 |

기본 진입: **발표 브리핑** (`pages/00_발표_브리핑.py`)

## 화면 계층

| 페이지 | 표시 | 주 데이터 (analysis/processed) |
|---|---|---|
| 발표 브리핑 | 동기간 막대·월별 이중축 · 지도·연도/지표 · Q4 겹침 막대 | `national_charge_ev_monthly`, `charge_sido_ytd_compare`, `sido_year_master`, GeoJSON |
| 시·도 지도 | choropleth + 순위 막대 | `sido_year_master` + GeoJSON |
| 급속 이용 추이 | 전국·시·도 시계열 | `charge_sido_monthly_panel`, `national_charge_ev_monthly` |
| 지역 상세 | KPI + 피크 | master, panel, `charge_sido_annual` |
| 급·완속 설치 판단 | 급속 비중·보급 강도·활성기 | 차지인포 processed + master + annual |
| EV·충전소 총량 | 전국 KPI | master, `ev_sido_monthly`, chargeinfo annual |
| 데이터 안내 | 메타·forecast 문서 | `data/forecast/` |

## raw → 화면 경로 (요약)

| raw | 전처리 | 화면에서 쓰는 산출 |
|---|---|---|
| 국토부 xlsx | `ev_molit_monthly` | EV 추이·마스터 |
| 환경부 설비 CSV | `charger_facility` | 설치 재고(2022까지) → 마스터 |
| 환경부 공공급속 연월 CSV | `charge_public_fast_monthly` | 충전량·활성기·피크·동기간 비교 |
| `data/raw/chargeinfo/*` | chargeinfo_* | 급속 비중·8권역 구축 |
| GeoJSON light | (정적) | 지도 |

상세 기획·한계: `docs/기획서.md` / `docs/기획서.docx`

## 인터랙션

- 브리핑: 연도·지도 지표 선택. 차지인포는 펼침(참고). 결론 KPI는 국토부·환경부.
- 탐색 화면: 사이드바 기준연도·지역
- 부분연도(2025)·설비 stale(2022+) 안내 유지

## 지도 해석

- 이용 부담(활성기당 충전량)·총 충전량: 높을수록 이용이 몰린 방향
- EV천대당 활성기: 낮을수록 급속 여력이 빠듯한 방향
- 색 설명 문구는 브리핑에 고정 표시
