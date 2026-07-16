# StockPilot AI

AI 기반 투자 의사결정 지원 플랫폼입니다. Blueprint v2.1에 따라 시장 데이터, 분석·백테스트, AI 참고 리포트, 본인 계좌 포트폴리오, 참고 알림, 준실시간·KIS 스트리밍 골격을 단계적으로 구현하고 있습니다.

다른 사용자에게 공유할 수 있는 기능 소개와 빠른 시작 안내는 [프로젝트 소개](PROJECT_INTRODUCTION.md)에서 확인할 수 있습니다.

## 실행

```powershell
python -m pip install uv==0.11.28
uv sync --locked --extra dev
uv run python -m uvicorn app.main:app --app-dir backend --reload
```

기본 개발 구성은 디스크 사용량을 줄이기 위해 `PREDICTION_ENGINE=lightweight`를 사용한다.
XGBoost 모델 개발과 관련 테스트가 필요할 때만 `uv sync --locked --extra dev --extra ml`로
ML 의존성을 추가하고 `PREDICTION_ENGINE=xgboost`를 설정한다. Docker에서도 같은 경우에만
`INSTALL_ML=true`로 빌드한다.

API 문서: `http://127.0.0.1:8000/docs`

Docker Compose 전체 스택은 Nginx를 통해 `http://localhost:8080`에서 접근한다.
서비스 포트는 기본적으로 로컬 호스트에만 바인딩되고, 웹 컨테이너는 Next.js 프로덕션 빌드로 실행된다. 외부 배포 시 `PUBLIC_API_URL`, HTTPS, 강력한 비밀번호와 시크릿 매니저를 별도로 설정해야 한다. 보안 기준은 [보안 설계](docs/architecture/security.md)를 참고한다.

## 데이터베이스와 스케줄러

```powershell
uv run alembic upgrade head
$env:SCHEDULER_ENABLED="true"
uv run python -m uvicorn app.main:app --app-dir backend --reload
```

스케줄러는 기본적으로 비활성화되어 있다. 활성화하면 `SCHEDULER_SYMBOLS`의 국내·미국
종목 일봉을 raw/cleaned 단계로 주기적으로 적재한다. 기본값은
`005930,000660,035420,AAPL,MSFT`이며 최대 50종목까지 허용한다. 종목당 조회 개수는
`SCHEDULER_INGESTION_LIMIT`으로 30~365 범위에서 설정한다.

Docker PostgreSQL 구성은 `PARTITION_MAINTENANCE_ENABLED=true`를 기본으로 사용해 다음
3개월의 `stock_candles` 월별 파티션을 서버 시작 시점과 매월 20일에 미리 생성한다. 로컬
SQLite에서는 이 작업을 실행하지 않는다.

`PERSISTENCE_ENABLED=true`이면 백테스트 결과와 활성 Score 가중치를 DB에 연결한다. 이 옵션을 켜기 전에 `alembic upgrade head`를 실행해야 한다. Docker Compose에서는 마이그레이션 후 자동으로 활성화된다.

관리자 화면 `/admin`에서는 백테스트 이력, 데이터 품질 로그, 캔들 수집, 관심 종목,
가격 참고 알림을 관리할 수 있다. 수동 수집은 선택한 종목의 raw/cleaned 캔들과 품질 로그만
DB에 저장하며 주문이나 계좌 변경을 실행하지 않는다. `ADMIN_UI_USERNAME`과
`ADMIN_UI_PASSWORD`를 설정하면 관리자 화면과 BFF가 HTTP Basic 인증으로 보호된다.
운영 환경에서는 두 값이 필수이며 반드시 HTTPS 뒤에서 사용해야 한다. 자동 가격 평가는
`REFERENCE_ALERTS_ENABLED=true`로 켜며 DB 저장이 필수다. 참고 알림은 조건 도달만 기록하고
주문은 실행하지 않는다. 자세한 내용은 [참고 알림 설계](docs/architecture/reference-alerts.md)를 확인한다.

`ACCOUNT_SYNC_ENABLED=true`이면 `/admin`에서 마스킹된 본인 계좌를 수동 동기화하고 통화별 포트폴리오 집중도와 손실 노출을 확인할 수 있다. 계좌 API는 관리자 키로 보호되며 주문 기능은 없다.

## 현재 범위

- Provider Capability 선언 및 기능 기반 Broker Adapter 라우팅
- 시드 기반 Mock 시세·호가·캔들 데이터
- 표준 API 응답 envelope 및 request ID
- 투자 자문이 아님을 명시하는 compliance 메타데이터

`STOCK_PROVIDER=toss`와 Toss OAuth 자격증명을 설정하면 현재가·일봉·호가·체결·종목 정보·투자유의 데이터를 Toss Open API에서 조회합니다. 본인 계좌 동기화는 명시적으로 `ACCOUNT_SYNC_ENABLED=true`일 때만 열리며, 주문 API는 제공하지 않습니다. KIS 자격증명과 `REALTIME_SOURCE=kis`를 설정하면 KIS WebSocket 스트리밍을 사용할 수 있습니다.
