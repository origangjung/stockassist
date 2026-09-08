# StockPilot AI 유지보수 가이드

이 문서는 코드를 처음 보는 사람이 **어디서 시작하고, 어떤 파일을 함께 수정해야 하며, 무엇을
검증해야 하는지** 빠르게 찾기 위한 지도다. 구현 세부 계약은 `docs/architecture`와 `docs/api`의
주제별 문서를 함께 참고한다.

각 클래스·메서드·함수·TypeScript 인터페이스의 한글 설명과 원본 위치는
[`code-reference-ko.md`](code-reference-ko.md)에서 찾는다.
선언을 추가하거나 이름을 바꾼 뒤에는 아래 명령으로 코드 사전을 갱신한다.

```powershell
.venv\Scripts\python.exe scripts\generate_korean_code_reference.py
```

## 1. 시스템 한눈에 보기

```text
Browser
  -> Next.js page/component
  -> Next.js BFF route (/api/market/*, /api/analysis/*, /api/admin/*)
  -> FastAPI route (/api/v1/*)
  -> application service
  -> provider adapter / repository / calculation engine
  -> external provider or PostgreSQL/Redis

AI report
  -> deterministic market facts
  -> five local specialist models
  -> rule-based diagnostic synthesis
  -> compliance validation
  -> browser presentation and office event sequence
```

핵심 원칙은 다음과 같다.

1. 브라우저에 API 키를 전달하지 않는다. 외부 요청은 FastAPI 또는 Next.js BFF에서 수행한다.
2. 계산 결과와 설명을 분리한다. 지표·확률·진단은 엔진이 계산하고 UI는 표시만 한다.
3. 외부 데이터 실패가 전체 분석을 깨뜨리지 않게 각 전문 AI는 `available`, `unavailable`,
   `quality_rejected` 상태를 명시한다.
4. 미래 데이터 유출을 막기 위해 학습 데이터는 당시 공개된 값만 사용하고 시간순으로 검증한다.
5. 후보 모델은 승격 기준을 통과하기 전까지 운영 artifact를 교체하지 않는다.

## 2. 최상위 파일

| 경로 | 역할 | 수정 시 확인할 것 |
| --- | --- | --- |
| `.env` | 로컬 비밀값과 실행 설정. Git에 포함하면 안 된다. | 키를 출력·로그·테스트 fixture에 넣지 않는다. |
| `.env.example` | 비밀값 없는 설정 설명서 | 새 설정을 추가하면 이름과 안전한 기본값을 추가한다. |
| `docker-compose.yml` | API, 웹, DB, Redis, 학습기, 모니터링 구성 | 포트는 기본적으로 `127.0.0.1`에만 바인딩한다. |
| `pyproject.toml`, `uv.lock` | Python 의존성과 도구 설정 | 의존성 변경 뒤 lock 파일과 테스트를 함께 갱신한다. |
| `package.json`, `pnpm-lock.yaml` | 웹 workspace와 Node 의존성 | 웹 의존성 변경 뒤 frozen-lockfile 빌드를 확인한다. |
| `README.md` | 실행 방법과 기능 개요 | 동작 방식이나 명령이 바뀌면 함께 갱신한다. |
| `REMAINING_WORK.md` | 미완료 작업과 모델 승격 상태 | 검증이 끝난 작업만 완료로 변경한다. |

`.next`, `node_modules`, `test-results`, `__pycache__`, `.pytest_cache`, `.ruff_cache`는 생성물이다.
기능을 이해하거나 수정할 때 읽을 대상이 아니다.

## 3. 프론트엔드: `frontend`

### 진입점과 데이터 흐름

| 경로 | 책임 |
| --- | --- |
| `app/layout.tsx` | 전역 HTML, 폰트, React Query provider를 연결한다. |
| `app/page.tsx` | 사용자 화면의 헤더, 검색 진입점, 면책 문구를 배치한다. |
| `app/admin/page.tsx` | 운영자 도구를 조합한다. 일반 사용자 기능을 넣지 않는다. |
| `app/globals.css` | 전역 토큰, 반응형 레이아웃, 분석 오피스와 결과 화면 스타일을 관리한다. |
| `app/api/**/route.ts` | 브라우저와 FastAPI 사이의 BFF다. 서버 비밀값과 허용 경로를 여기서 통제한다. |

### 사용자 분석 화면

| 경로 | 책임 | 함께 보는 파일 |
| --- | --- | --- |
| `components/market-dashboard.tsx` | 검색, 자동완성, 최근 검색, 관심 종목, URL 동기화, 시세 스트림, 결과 화면을 조율한다. | `lib/stock-search.ts`, `lib/market-api.ts` |
| `lib/stock-catalog.ts` | API 호출 전 즉시 보여줄 대표 종목·ETF와 한국어 별칭 목록이다. 증권 마스터가 아니다. | `lib/stock-search.ts` |
| `lib/stock-search.ts` | 검색어 정규화, 정확 일치, 부분 일치, 검색 순위를 계산하는 순수 함수다. | `lib/stock-search.test.mjs` |
| `components/stock-chart.tsx` | 정제된 캔들을 차트 라이브러리에 전달한다. 분석 계산을 넣지 않는다. | `lib/market-api.ts` |
| `components/technical-snapshot.tsx` | 기술 지표와 패턴을 요약한다. | FastAPI indicators/patterns API |
| `components/research-details.tsx` | 재무·밸류에이션·수급·뉴스·공시 탭을 필요할 때만 조회한다. | `lib/market-api.ts` |
| `components/analysis-result.tsx` | AI 리포트 조회, 결과 표시, 재시도, 최종 모달과 발표 순서를 조율한다. | `lib/analysis-sequence.ts` |
| `components/analysis-progress.tsx` | 픽셀 오피스, 캐릭터 상태, 이벤트 기록을 렌더링한다. | `features/office/*` |
| `components/final-verdict-modal.tsx` | 완료된 최종 의견을 접근 가능한 modal로 보여준다. | `analysis-result.tsx` |

### 오피스 이벤트

| 경로 | 책임 |
| --- | --- |
| `features/office/analysis-events.ts` | room/speech/verdict 이벤트 타입과 시간 기반 stream을 정의한다. |
| `features/office/office-store.ts` | 현재 방, 캐릭터, 발언, 최근 이벤트 24개를 보관한다. |
| `features/office/office-map.config.ts` | 캐릭터 위치와 방 좌표를 데이터로 관리한다. |
| `lib/analysis-sequence.ts` | 전문 AI 발표, 토론, 최종 판정의 시간표를 만든다. |

이벤트 시간을 바꿀 때는 CSS animation 시간만 바꾸지 말고 `analysis-sequence.ts`와 E2E의 완료
대기 시간도 확인한다. `prefers-reduced-motion`은 시각 움직임을 줄이지만 의미 있는 분석 이벤트를
삭제해서는 안 된다.

### 프론트 상태 규칙

- 서버 데이터는 TanStack Query로 관리한다. 서버 응답을 별도 `useState`에 복제하지 않는다.
- 검색처럼 연속 요청이 가능한 기능은 이전 `AbortController`를 취소하고 request id로 늦은 응답을
  무시한다.
- URL `?symbol=`은 공유 가능한 선택 상태다. 브라우저 뒤로가기는 `popstate`에서 복원한다.
- 최근 검색과 개인 관심 종목은 편의 기능이며 localStorage 실패가 핵심 분석을 막으면 안 된다.
- API 오류, 빈 데이터, loading, stale 상태를 서로 구분해 표시한다.

## 4. 백엔드: `backend/app`

### 진입점

| 경로 | 책임 |
| --- | --- |
| `main.py` | 설정을 읽고 provider, repository, service를 조립하는 composition root다. lifespan에서 scheduler와 resource를 시작·종료한다. |
| `api/routes.py` | `/api/v1` HTTP 계약과 FastAPI dependency를 정의한다. 계산이나 provider별 분기를 직접 넣지 않는다. |
| `websocket/routes.py` | 실시간 시세 WebSocket 계약을 제공한다. |
| `config/settings.py` | 환경변수 타입, 범위, 보안 기본값을 검증한다. |
| `core/` | 오류 envelope, 요청 ID, 접근 제어, rate limit, security headers 같은 횡단 관심사를 담당한다. |

### 계층별 책임

| 디렉터리 | 역할 | 넣지 말아야 할 것 |
| --- | --- | --- |
| `services/` | 한 사용자 요청의 use case를 조율한다. | HTTP response 생성, provider 전용 세부사항 |
| `providers/` | Toss/KIS/mock 등 외부 시장 데이터 구현체다. | UI 표현, 모델 학습 |
| `adapters/` | capability에 따라 provider를 선택하는 안정된 경계다. | 특정 provider를 가정한 서비스 로직 |
| `repositories/` | SQLAlchemy 영속화와 조회를 캡슐화한다. | 외부 HTTP 호출 |
| `models/` | ORM 테이블과 DB 관계를 정의한다. | 비즈니스 workflow |
| `pipeline/` | raw 데이터를 검증·정제하고 품질 로그를 만든다. | 화면용 문구 |
| `indicators/`, `patterns/`, `score/` | 결정론적 계산 엔진이다. | 네트워크·DB side effect |
| `prediction/` | 일반 예측 엔진과 artifact registry를 관리한다. | 로컬 전문 AI presentation |
| `ai_reports/` | 사실을 설명문으로 만들고 compliance를 검증한다. | 검증되지 않은 수치 계산 |
| `financials/`, `news/`, `disclosures/`, `investor_flow/` | 도메인별 provider 계약과 정규화를 담당한다. | 다른 도메인의 저장 규칙 |
| `realtime/` | 실시간 quote hub와 연결 상태를 관리한다. | 과거 데이터 학습 |
| `scheduler/` | 주기 수집과 유지보수 job을 예약한다. | endpoint 응답 로직 |
| `observability/` | 구조화 로그, metrics, health, Sentry 연결을 담당한다. | API 키나 원문 개인정보 로그 |

### API 요청을 추가하는 순서

1. 도메인 contract 또는 Pydantic schema를 정의한다.
2. provider/repository 경계를 구현한다.
3. `services/`에 use case를 구현한다.
4. `main.py`에서 dependency를 한 번 조립한다.
5. `api/routes.py`에는 입력 검증과 service 호출만 추가한다.
6. Next.js BFF allowlist와 `market-api.ts` 타입을 추가한다.
7. backend contract test와 frontend loading/error test를 추가한다.

## 5. 직접 학습 AI: `backend/app/local_ai`

### 모델별 역할

| 모델 | 주요 입력 | 출력 의미 |
| --- | --- | --- |
| `technical` | 가격·거래량·추세·변동성·벤치마크/섹터 상대 특성 | 기술적 방향 진단 |
| `financial` | point-in-time SEC/DART 재무와 변화율·밸류에이션 입력 | 재무 상태 진단 |
| `news` | 허용된 뉴스 metadata, 공시 사건, 거시 문맥 | 뉴스 사건 영향 진단 |
| `investor_flow` | FINRA short volume/interest와 시장 문맥 | 수급·공매도 압력 진단 |
| `risk` | 가격 하락 위험, VIX·금리·달러 등 거시 특성 | downside event 위험 |
| `synthesis` | 전문 AI 결과와 availability/confidence | 현재는 승인된 규칙 기반 종합 진단을 우선 사용 |

### 핵심 파일

| 경로 | 책임 |
| --- | --- |
| `contracts.py` | 전문 AI 이름과 runtime 결과 schema다. 상태 의미를 변경하면 API/UI도 함께 수정한다. |
| `features.py` | 운영 facts를 모델별 고정 feature vector로 바꾼다. 학습 CSV 열과 순서가 일치해야 한다. |
| `model.py` | 표준화, 로지스틱 학습, calibration, metric, JSON artifact 서명·검증을 담당한다. 임의 코드를 deserialize하지 않는다. |
| `runtime.py` | artifact와 최신 feature를 불러 전문 AI 5개를 실행하고 품질 기준을 적용한다. |
| `diagnostic.py` | 승인된 전문 AI만 신뢰도 가중해 최종 진단을 만든다. |
| `quality.py` | sample 수, AUC, balanced accuracy, Brier, calibration 기준으로 사용 가능 여부를 판정한다. |
| `market_features.py` | 기술·위험 학습용 시계열과 미래 market outcome label을 만든다. |
| `financial_features.py` | SEC companyfacts를 공개 시점 기준 snapshot으로 변환한다. |
| `news_features.py`, `sec_event_features.py` | 뉴스·8-K 사건을 날짜별 feature/label로 만든다. |
| `flow_features.py`, `flow_market_features.py` | FINRA 수급 records와 시장 문맥을 결합한다. |
| `macro_features.py`, `sector_features.py`, `etf.py` | 거시·섹터·ETF 공통 문맥을 만든다. |
| `http_security.py` | HTTPS endpoint, symbol, 응답 크기, 일일 요청 예산을 강제한다. |
| `sec.py`, `fred.py`, `finra.py`, `news_api.py` | 외부 데이터 client다. timeout/rate limit/출처 시각을 보존한다. |

### 학습과 승격 흐름

```text
public point-in-time data
  -> scripts/ai/data/build_*_dataset.py
  -> datasets/local-ai*/{agent}.csv
  -> scripts/ai/training/train_local_agents.py
  -> candidate JSON artifacts
  -> scripts/ai/training/walk_forward_local_agents.py
  -> quality/promotion gates
  -> artifacts/local-ai/*.json
  -> LocalAnalysisRuntime
```

행 수가 늘었다고 정확도가 높아지는 것은 아니다. 같은 날짜의 여러 종목은 독립 표본이 아니며,
target·기간·벤치마크가 달라지면 이전 metric과 직접 비교할 수 없다. 관련 진단은
`docs/operations/local-ai-retraining-diagnosis-20260814.md`를 참고한다.

## 6. 학습·운영 스크립트: `scripts`

파일 이름의 동사가 책임을 나타낸다.

- `collect_*`: 외부 원천을 증분 수집한다. 요청 예산과 마지막 성공 지점을 보존해야 한다.
- `build_*_dataset.py`: raw 입력을 시간순 학습 CSV로 변환한다. 미래 값을 feature에 넣지 않는다.
- `enrich_*`: 기존 행에 point-in-time 문맥 feature를 추가한다.
- `relabel_*`: target 정의를 변경한다. 기존 성능과 비교할 때 target 버전을 반드시 기록한다.
- `train_*`: artifact 후보를 만든다. 운영 artifact를 무조건 덮어쓰지 않는다.
- `walk_forward_*`, `benchmark_*`, `report_*`, `diagnose_*`: 평가 전용이며 학습 데이터에 결과를
  역으로 반영하지 않는다.
- `smoke_*`: 실제 credential과 provider 연결을 최소 호출로 확인한다. 응답이나 키를 출력하지 않는다.
- `backup_*`, `rotate_*`: 운영 데이터와 secret 유지보수다. 실행 전 대상 경로와 환경을 확인한다.

새 스크립트에는 module docstring, 입력/출력 경로, 재실행 안전성, 외부 비용 가능성, 비밀값 처리,
종료 코드 의미를 적는다.

## 7. 데이터와 artifact

- `datasets/`: 재생성 가능한 학습 데이터다. source, 수집 시각, 공개 시각, target version을 보존한다.
- `artifacts/`: 모델 JSON과 checksum을 저장한다. 검증 없이 신뢰하지 않는다.
- `backups/`: DB/Redis backup과 manifest다. 복원 검증 전에는 유효한 backup으로 간주하지 않는다.
- `.runtime/`: 로컬 실행 중 생성되는 임시 상태다.

모델 JSON은 feature 이름·순서, scaler, coefficient, metric, target, version, checksum을 함께
가져야 한다. pickle처럼 로드 시 코드를 실행할 수 있는 형식은 사용하지 않는다.

## 8. Docker와 네트워크

| 서비스 | 역할 | 기본 로컬 포트 |
| --- | --- | --- |
| `nginx` | 외부 단일 진입점과 reverse proxy | `127.0.0.1:8080` |
| `web` | Next.js production server | `127.0.0.1:3000` |
| `api` | FastAPI | `127.0.0.1:8000` |
| `postgres` | 영속 데이터 | `127.0.0.1:5432` |
| `redis` | rate limit, cache, pub/sub | `127.0.0.1:6379` |
| `trainer` | 명시적으로 실행하는 학습 profile | 외부 포트 없음 |
| `prometheus`, `alertmanager`, `grafana` | 선택적 monitoring profile | 9090, 9093, 3001 |

일반 기능 변경은 `docker compose up -d --build web api`로 반영한다. 학습기는 항상 실행되는
서비스가 아니며 필요할 때 profile/명령으로 실행한다.

## 9. 테스트 위치와 최소 검증

| 변경 | 최소 검증 |
| --- | --- |
| 검색 순위·별칭 | `stock-search.test.mjs`, Playwright autocomplete test |
| 사용자 분석 화면 | TypeScript, frontend unit tests, desktop/mobile Playwright |
| API contract/service | 관련 `backend/tests/test_*.py`, Ruff |
| DB model/repository | migration, repository tests, PostgreSQL integration test |
| feature/label | feature unit test, leakage check, time split/walk-forward report |
| 모델 runtime/artifact | local AI tests, checksum/security tests, promotion report |
| Docker/env | image build, health check, `/health`, 실제 BFF smoke test |

대표 명령:

```powershell
corepack pnpm --filter @stockpilot/web exec tsc --noEmit
corepack pnpm --filter @stockpilot/web test
corepack pnpm --filter @stockpilot/web test:e2e
.venv\Scripts\ruff.exe check backend scripts
.venv\Scripts\pytest.exe -q -m "not ml"
docker compose up -d --build web api
docker compose ps
```

## 10. 주석 작성 기준

좋은 주석은 코드가 **무엇을 하는지 되풀이하지 않고 왜 그렇게 해야 하는지** 설명한다.

주석을 추가해야 하는 경우:

- look-ahead bias를 막는 날짜 경계
- 오래된 비동기 응답을 버리는 request id와 취소 규칙
- provider fallback, retry, rate limit, circuit breaker 조건
- 보안 검증과 fail-closed 선택
- 모델 승격·품질 제외 기준
- 금융 도메인에서 부호나 target 의미가 직관과 반대인 경우

주석을 피해야 하는 경우:

- `count += 1`에 “count를 1 증가”처럼 코드를 번역하는 문장
- 현재 구현과 쉽게 어긋나는 숫자·성능·진행률
- 함수 이름과 타입으로 이미 명확한 내용
- 폐기된 구현을 주석 처리해 남기는 것

공개 함수나 복잡한 class에는 docstring/JSDoc으로 입력, 출력, side effect, 실패 방식을 적는다.
구현 변경 시 관련 주석과 이 가이드가 여전히 맞는지 같은 변경에서 확인한다.
