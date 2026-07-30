# StockPilot AI — Desktop 작업 목록

> 마지막 정리: 2026-07-27
> 작업 경로: `C:\stock_assist`
> 상세 이력: [DESKTOP_CODEX_HANDOFF.md](DESKTOP_CODEX_HANDOFF.md)

## 현재 상태

- 기능 MVP: 약 **88~92%**
- 운영 준비도: 약 **70~75%**
- 노트북에서 가능한 코드·문서·가벼운 테스트는 대부분 진행했다.
- 데스크톱에서는 용량, 장시간 실행, 실제 증권사 연결이 필요한 검증을 우선한다.
- 주문·조건주문 자동 실행은 규제 검토 전까지 **구현·활성화 금지**다.

## 최근 사용자 화면 상태

- 검색 전에는 서비스 소개와 분석 데스크 안내가 보이고, 검색 후에만 분석 결과가 열린다.
- `삼성전자`, `005930`, `삼전`, `AAPL`, `애플`, `NVDA` 등의 종목명·티커·별칭을 검색할 수 있다.
- 입력 중에는 유사 종목 자동완성 드롭다운이 나타나며, 종목명·티커·별칭 중 일치한 근거를
  표시한다. `↑/↓`, `Enter`, `Esc`, `Ctrl/Cmd + K`를 지원한다.
- 최근 검색과 관심 종목은 브라우저에만 저장한다. 백엔드나 Git에 사용자 관심 종목을 저장하지 않는다.
- 프론트 TypeScript 검사와 웹 테스트 10개는 통과했다.

## 데스크톱 우선 작업

### 1. 실제 브라우저 UI/UX 최종 QA

노트북의 headless Chrome/Edge는 GPU 프로세스 제약으로 최신 화면 캡처를 재실행하지 못했다.
데스크톱에서는 실제 Chrome 또는 Edge로 다음을 확인한다.

- 데스크톱과 모바일 폭(360px, 390px, 768px, 1440px)에서 검색창과 자동완성 드롭다운이 잘리지 않는지
- 한글 별칭·영문 티커·부분 일치 검색 결과가 예상 순서로 표시되는지
- 키보드만으로 `Ctrl/Cmd + K → 화살표 → Enter → 결과 이동`이 가능한지
- 관심 종목 추가·삭제, 최근 검색 삭제, 공유 주소 `?symbol=005930`이 정상인지
- reduced-motion 환경에서 과도한 애니메이션이 없는지
- 실제 Mock 환경으로 우선 확인하고, UI 오류만 필요한 범위에서 수정한다.

완료 기준: 주요 화면의 스크린샷을 외부 비밀정보 없이 남기고, 모바일 가로 스크롤·포커스 누락·텍스트 잘림이 없어야 한다.

### 2. Docker·PostgreSQL·Redis 통합 검증

데스크톱의 Docker Desktop에서만 실행한다. 재빌드 전 디스크 여유 공간을 확인한다.

- `docker compose up --build`로 FastAPI·PostgreSQL·Redis·Next.js·Nginx 통합 기동
- Alembic 전체 revision의 `head → base → head` 왕복 검증
- PostgreSQL 백업과 **격리된 복구 리허설**
- Redis 재시작 중 rate limit, Pub/Sub, WebSocket 팬아웃의 안전한 실패·복구 확인
- 데이터 정리 기능은 미리보기만 먼저 확인하고, 승인 없이 `DATA_LIFECYCLE_CLEANUP_ENABLED`를 켜지 않는다.

참고 문서:

- `docs/operations/desktop-validation.md`
- `docs/operations/postgresql-backup-restore.md`
- `docs/operations/production-preflight.md`

### 3. 실제 Provider 장시간 검증

실제 키는 `.env` 또는 Secret Manager에서만 읽고, 터미널·로그·fixture·문서에 출력하지 않는다.

- Toss REST: 토큰 재발급, 허용 IP, 401/403/429/5xx, `Retry-After`, 그룹별 Rate Limit
- 장 운영 시간대 Toss 폴링: 관심·보유 종목 우선순위와 1~3초 준실시간 흐름
- KIS 국내·미국 WebSocket: 연결, 재연결, 구독 해제, 종목 제한, REST fallback
- Toss·KIS 장애 중 Mock fallback 및 사용자용 오류 메시지
- 실거래 주문은 호출하지 않는다. 계좌 동기화도 사용자 본인 계좌 범위와 읽기 전용으로 우선 검증한다.

### 4. 장기 백테스트와 ML 검증

대용량 데이터와 artifact는 Git에 커밋하지 않는다.

- 상장폐지 종목을 포함한 장기 유니버스 구축
- 수수료·세금·슬리피지 및 기업행동 기준시점 보정 확인
- 여러 시장 국면의 Walk-Forward 검증과 Champion/Challenger 비교
- XGBoost 장기 학습 artifact 생성, checksum 검증, 활성화·롤백 리허설
- Score·패턴·ML 결과를 성과 검증 전까지 계속 `experimental`로 유지

### 5. 운영 배포 준비

- 고정 Egress IP와 Toss 허용 IP 구성
- HTTPS 도메인, Secret Manager, CORS/ALLOWED_HOSTS/CSP 실배포 확인
- Prometheus·Grafana·Sentry 연결과 장애 알림 규칙 확인
- KRX 시세 재배포 계약, 개인정보·데이터 보존 정책 검토
- Nasdaq·NYSE·KRX 기업행동의 계약형 실제 Provider는 명세와 재배포 조건 확보 후 구현

## 보류 항목

- Toss SINGLE/OCO/OTO 조건주문, 자동 손절·익절, 타인 계좌 거래
- 투자일임업·자동매매 관련 규제 검토 전의 주문 실행 기능
- 계약·근거가 없는 기존 캔들의 일괄 `price_basis` 재분류

## 시작 전 안전 수칙

1. `.env`의 값, API 키, client secret, 계좌번호를 출력·커밋·문서화하지 않는다.
2. 작업 단위마다 자동 commit/push하지 않는다.
3. Docker 이미지 재빌드, 의존성 재설치, ML 패키지 설치 전 디스크 공간을 확인한다.
4. 실제 시장 데이터와 사용자 데이터는 테스트 fixture에 저장하지 않는다.
5. 관리자 쓰기 API와 데이터 정리·기업행동 승인은 명시적 운영 권한이 있을 때만 실행한다.

## 권장 검증 명령

```powershell
.venv\Scripts\ruff.exe check backend
.venv\Scripts\pytest.exe -q -m "not ml"
& 'C:\stock_assist\apps\web\node_modules\.bin\tsc.CMD' -p apps/web/tsconfig.json --noEmit --incremental false
npm.cmd --prefix apps\web test
.venv\Scripts\alembic.exe -c alembic.ini heads
```

무거운 Docker·실데이터·ML 작업 전에는 반드시 [DESKTOP_CODEX_HANDOFF.md](DESKTOP_CODEX_HANDOFF.md)를 끝까지 읽고, 현재 코드와 이 문서의 상태가 일치하는지 먼저 확인한다.
