# GeoJSON (정적 행정구역 경계)

SGIS API 기반 [statgarten/maps](https://github.com/statgarten/maps) 원본(UTM-K)을 **WGS84** 로 변환한 정적 파일입니다.

| 파일 | 단위 | 주요 조인 키 |
|---|---|---|
| `korea_sido_wgs84.geojson` | 시·도 | `properties.sido_short` (한국전력), `sido_cd` |
| `korea_sigungu_wgs84.geojson` | 시·군·구 | `properties.sigungu_cd` (5자리), `sigungu_nm` |
| `sigungu_lookup.csv` | 코드·명칭表 | CSV/환경부 데이터 조인용 |

## 생성 이력

현재 파일은 SGIS 기반 UTM-K(EPSG:5179) 경계를 WGS84(EPSG:4326)로 변환해 생성한 **정적 산출물**입니다. 일회성 생성 스크립트와 전용 의존성 파일은 사용 완료 후 삭제했습니다.

재생성이 필요할 때의 입력·출력·필수 속성 명세는
`docs/analysis_dashboard_implementation_plan.md`의 **코드베이스 생명주기 관리 > 삭제 계층 이력**을 기준으로 새로 구현합니다.

## 참고

- 원본 경계 기준: statgarten/maps (SGIS, 2020년대 초 경계)
- 발급받은 SGIS `hadmarea.geojson` API는 현재 키에서 `-201` 오류 → 추후 SGIS에서 **행정구역경계 API** 권한 추가 시 교체 가능
- SGIS `addr/stage.json` (`pg_yn=1`)은 경량 경계(WKT) 제공 — geocode·코드表용으로 별도 활용

## 좌표계

- 저장 좌표: **WGS84 (EPSG:4326)** — Streamlit `st.map`, PyDeck, Folium 호환
