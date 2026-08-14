# EV Infra Checker

전국 17개 시·도 **공공급속 인프라**를 수요·이용·공급 구조로 나눠 보고,  
**어디에 공공급속을 우선 배치하는 것이 바람직한지**를 탐색하는 Streamlit 대시보드입니다.

| | |
|---|---|
| Repository | https://github.com/M1nGyu-Lee/ev_infra_checker |
| Live Demo | Streamlit Cloud에 이 리포를 연결해 배포 (Main file: `streamlit_app.py`) |
| Local | `uv run streamlit run streamlit_app.py` → `http://localhost:8501` |

---

## Table of Contents

1. [목적](#1-목적)
2. [획득·사용 데이터](#2-획득사용-데이터)
3. [도출 가능한 인사이트](#3-도출-가능한-인사이트)
4. [패키지가 하는 일](#4-패키지가-하는-일)
5. [대시보드 화면](#5-대시보드-화면)
6. [폴더 구조](#6-폴더-구조)
7. [Tech Stack](#7-tech-stack)
8. [Quick Start](#8-quick-start)
9. [Usage](#9-usage)
10. [한계](#10-한계)
11. [Contact](#11-contact)

---

## 1. 목적

전기차 등록은 늘고, “충전기가 많다 / 충전이 불편하다”는 말이 동시에 나온다.  
원인은 자료마다 **모집단과 지표 정의**가 다르기 때문이다.

이 프로젝트의 목적은 다음이다.

1. **수요(EV 등록)** · **이용(공공급속 실제 가동·충전량)** · **공급 구조(급·완속 구축)** 를 분리해 같은 기준으로 비교한다.
2. 시·도별 **이용 부담**(실제 가동 1기당 kWh)과 **충전 여력**(EV 1,000대당 실제 이용 충전기)을 본다.
3. 두 관점이 겹치는 지역을 **공공급속 배치 우선 방향**으로 제시한다.  
   (확충 % 처방 · 설치 확정이 아님)

핵심 질문:  
**전기차 수요 대비 공공급속 이용·여력이 어긋날 때, 어디에 배치를 우선할 것인가?**

---

## 2. 획득·사용 데이터

앱은 이미 가공된 `data/analysis`, `data/processed` CSV를 읽습니다.  
원천 → 전처리는 분석 저장소에서 수행하고, 이 리포는 **서빙용 산출물**을 포함합니다.

| 구분 | 출처 | 앱에서 쓰는 내용 |
|---|---|---|
| 수요 | 국토부 통계누리 · 연료별 자동차등록현황 | 시·도×월 EV 등록 |
| 이용 | 환경부 공공급속 연월별 충전량·횟수·시간 | 충전량(kWh) · **실제 가동 충전기** · 피크 |
| 공급 구조 | 환경부 급·완속 충전기 현황 API (시·도 코드 → CSV) | 급·완속 구축·비중 (배경) |
| 교차확인 | 한국전력 지역별 전기차 현황 | EV 교차 확인 |
| 지도 | `korea_sido_wgs84_light.geojson` | 시·도 choropleth |

주요 가공 테이블 (`data/analysis/`):

| 파일 | 역할 |
|---|---|
| `sido_year_master.csv` | 시·도×연도 마스터 (부담·여력 KPI) |
| `national_charge_ev_monthly.csv` | 전국 EV·충전 월별 |
| `charge_sido_ytd_compare.csv` | 동기간(같은 달끼리) 비교 |
| `charge_sido_monthly_panel.csv` | 시·도 월별 패널 |
| `ev_sido_monthly.csv` | 시·도 EV 월별 |

`data/processed/me_charger_status_*.csv` — 급·완속 현황·비중 (설치 판단·총량 화면).

용어:

| 용어 | 정의 |
|---|---|
| 실제 가동 충전기 | 해당 기간 충전 기록이 있는 환경부 공공급속 |
| 이용 부담 | 실제 가동 1기당 충전량 (kWh/기) |
| 충전 여력 | 전기차 1,000대당 실제 이용된 충전기 수 |
| 배치 우선 | 먼저 두는 **방향** (설치 확정 아님) |

---

## 3. 도출 가능한 인사이트

이 패키지로 확인할 수 있는 분석 관점입니다. (구체 수치는 앱 필터로 재현)

- **속도 괴리:** 같은 기간 기준 EV 증가 vs 실제 가동·충전량 증가가 어긋나는지
- **이용 부담:** 어느 시·도에서 가동 1기가 더 바쁜지 (kWh/기)
- **충전 여력:** 어느 시·도에서 차 수 대비 실제 이용 충전기가 적은지
- **겹침:** 부담·여력이 **둘 다** 나쁜 곳 vs 한쪽만 나쁜 곳 (처방을 나누어 봄)
- **시계열·피크:** 월별 추이, 피크월·평균 대비 초과
- **공급 배경:** 급·완속 비중·보급 강도 (결론 KPI가 아닌 참고)

결론 KPI는 **국토부 EV · 환경부 공공급속**. 설문·언론·급완속 총량은 배경입니다.

---

## 4. 패키지가 하는 일

| 기능 | 설명 |
|---|---|
| 발표 브리핑 | 전년 대비 → 종합(둘 다 / 부담만 / 여력만) 스토리 UI |
| 지도 | 이용 부담·충전 여력 choropleth + 순위 |
| 추이 | 전국·시·도 공공급속·EV 월별 시계열 |
| 지역 상세 | 시·도 KPI · 피크 |
| 급·완속 설치 판단 | 구축 비중·보급 강도 힌트 (참고) |
| EV·충전소 총량 | 전국 규모 맥락 |
| 데이터 안내 | 지표 정의·기간·한계 |

---

## 5. 대시보드 화면

| 구분 | 페이지 | 경로 |
|---|---|---|
| 본편 | 발표·정책 브리핑 | `pages/00_발표_브리핑.py` |
| 탐색 | 시·도 지도 | `pages/01_시도_지도.py` |
| 탐색 | 급속 이용 추이 | `pages/02_급속_이용_추이.py` |
| 탐색 | 지역 상세 | `pages/03_지역_상세.py` |
| 참고 | 급·완속 설치 판단 | `pages/04_급완속_설치_판단.py` |
| 참고 | EV·충전소 총량 | `pages/05_EV_충전소_총량.py` |
| 참고 | 데이터 안내 | `pages/06_데이터_안내.py` |

기본 진입: **발표·정책 브리핑**  
로컬 주소: **http://localhost:8501**

---

## 6. 폴더 구조

```text
ev_infra_checker/
├── streamlit_app.py          # 홈 (http://localhost:8501)
├── requirements.txt
├── pages/                    # Streamlit multipage 진입점
├── app_pages/                # 화면 본문 (briefing, map, trends, …)
├── charger_dashboard/        # 공통 모듈
│   ├── data.py               # CSV 로드 · KPI 헬퍼
│   ├── charts.py             # 차트
│   ├── ui.py / sidebar.py
│   └── assets/
├── data/
│   ├── analysis/             # 시·도 마스터 · YTD · 패널
│   ├── processed/            # me_charger_status_* 등
│   ├── forecast/             # 보조 예측·방법론 문서
│   └── geojson/              # 시·도 경계
└── docs/                     # 실행·화면 가이드
```

칼럼명은 **한글**(공유·열람용). 원본 분석 저장소 영문 스키마와 별도입니다.

---

## 7. Tech Stack

| 구분 | 기술 |
|---|---|
| Language | Python 3 |
| App | Streamlit (multipage) |
| Data | Pandas, CSV |
| Viz | Plotly |
| Map | GeoJSON |
| Deploy | Streamlit Cloud / 로컬 (`uv` 또는 pip) |

---

## 8. Quick Start

### 로컬

```powershell
uv venv
.\.venv\Scripts\activate
uv pip install -r requirements.txt
uv run streamlit run streamlit_app.py
```

브라우저: **http://localhost:8501**

### Streamlit Cloud

1. https://github.com/M1nGyu-Lee/ev_infra_checker 연결  
2. Main file: `streamlit_app.py`  
3. Dependencies: `requirements.txt`  
4. 배포 후 부여되는 `https://….streamlit.app` URL로 접속

---

## 9. Usage

1. 앱을 연 뒤 사이드바에서 **발표·정책 브리핑**으로 이동한다.
2. **전년 대비**에서 시·도·기간을 바꿔 EV·실제 가동·충전량 괴리를 본다.
3. **종합**에서 이용 부담·충전 여력 겹침(둘 다 / 한쪽만)을 본다.
4. 필요하면 지도·추이·지역 상세에서 같은 지표를 깊게 본다.
5. 지표 정의·한계는 **데이터 안내**를 참고한다.

---

## 10. 한계

- 시·도 단위 집계 (구·군·동 미제공 원천은 분석 불가)
- 이용 부담은 대기·체감이 아니라 **1기당 충전량**
- 연도·월 필터에 따라 부분연도(같은 달 비교)가 될 수 있음
- 급·완속 구축 총량만으로 공공급속 충분/부족을 단정하지 않음
- 확충 % · “이미 설치 확정” 주장은 하지 않음

---

## 11. Contact

- Author: 이민규 (4팀)  
- GitHub: https://github.com/M1nGyu-Lee/ev_infra_checker  
- Issues: https://github.com/M1nGyu-Lee/ev_infra_checker/issues
