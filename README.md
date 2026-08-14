# EV Infra Checker

전기차·환경부 공공급속·환경부 급·완속 현황(API) Streamlit 대시보드 배포본입니다.

- GitHub: https://github.com/M1nGyu-Lee/ev_infra_checker
- 칼럼명은 **한글** (공유·열람용). 원본 분석 저장소 영문 스키마와 별도입니다.

## 로컬 실행 (uv 권장)

```powershell
uv venv
.\.venv\Scripts\activate
uv pip install -r requirements.txt
uv run streamlit run streamlit_app.py
```

## Streamlit Cloud

1. 이 리포 연결
2. Main file: `streamlit_app.py`
3. Dependencies: `requirements.txt`

## 화면 우선순위

1. 정책: 발표·정책 브리핑 (스토리 본편)
2. 탐색: 지도 · 급속 추이 · 지역 상세
3. 사업자: 설치 힌트 사분면 · 환경부 급·완속 현황 · 공공급속 활성기 · 한전
4. 기초: 전국 EV·활성기 총량 · 기간 상태
