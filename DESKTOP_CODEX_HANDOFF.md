# StockPilot AI — Desktop Codex 인수인계

> 작성일: 2026-07-16 / 마지막 갱신: 2026-07-27
> 작업 경로: `C:\stock_assist`
> 기준 설계: StockPilot AI Master Project Blueprint v2.1

## 2026-07-27 노트북 최종 UI·Mock QA

- 검색 전 화면과 검색 후 결과 화면의 데스크톱·모바일 레이아웃을 재점검했다. 빠른 종목
  버튼을 전체 warm palette로 통일했고, 좁은 화면의 검색창은 입력과 실행 버튼을 두 행으로
  배치해 가로 폭을 넘지 않도록 보완했다.
- 종목 검색은 명시적 label, 키보드 후보 선택, 결과 영역 포커스 이동, 상태 알림과
  reduced-motion 처리를 유지한다. 관심 종목은 브라우저에만 저장하고, 저장소가 차단된 경우
  해당 탭 메모리로 안전하게 대체한다. 관심 종목 추가·제거에는 스크린리더 상태 알림을 준다.
- 별도 Mock FastAPI(`STOCK_PROVIDER=mock`, 영속화·스케줄러·실시간 비활성)에서 국내
  `005930`·미국 `AAPL` 현재가, 정제 캔들, 지표, AI 리포트가 모두 HTTP 200으로 응답하는지
  확인했다. AI 리포트의 `is_investment_advice=false`, `disclaimer`, `data_as_of`도 검증했다.
- Next.js의 읽기 전용 시장 BFF도 Mock 서버와 직접 연결해 정상 시세 요청은 200, 허용하지
  않은 query 조건은 400으로 차단되는 것을 확인했다. 자격증명은 이 검증에 사용하거나
  출력하지 않았다.
- 가벼운 최종 검증은 TypeScript typecheck, 웹 단위 테스트(9개), `git diff --check`로
  수행한다. 브라우저 자동 캡처는 이 노트북의 headless GPU 프로세스 제약으로 재실행할 수
  없으므로, 데스크톱에서 실제 브라우저 수동 확인을 한 번 더 수행한다.

## 2026-07-23 노트북 UI·품질 보완

- 첫 화면은 검색 전용으로 유지하고, 검색 후에만 멀티 에이전트 분석 화면이 위에서 아래로
  나타나는 흐름을 유지했다. `?symbol=005930` 주소로 삼성전자 결과를 바로 확인할 수 있다.
- 국내·미국 종목의 한글 별칭(예: `삼전`, `하이닉스`, `엔비디아`, `테슬라`) 검색과
  부분 일치 검색 후보를 추가했다. 최근 검색한 최대 5개 종목은 브라우저 `localStorage`에만
  저장하며, 저장소가 차단된 환경에서는 메모리 목록으로 안전하게 동작한다.
- 검색 후보는 화살표 키·Enter·Esc로도 선택할 수 있는 접근 가능한 combobox이며,
  선택 결과를 `?symbol=` 주소에 동기화한다. 결과 공유는 그 주소를 포함하므로 수신자가
  같은 종목의 검색 후 화면으로 바로 진입할 수 있다.
- 공유 주소는 기존 주소의 해시·추적·기타 query 값을 보존하지 않고 `symbol`만 허용하는
  표준 URL이다. Web Share가 실패하거나 미지원인 브라우저에서는 클립보드 복사로 안전하게
  대체하며, 최근 검색은 이 기기에서만 지울 수 있다.
- 분석 조직의 역할 버튼은 회의록의 해당 의견으로 포커스를 이동하고, 선택하지 않은 의견은
  시각적으로 낮춰 비교할 수 있다. reduced-motion 접근성 처리도 유지한다.
- 빈 캔들·네트워크·비정상 API 응답을 사용자용 제한 메시지로 처리하고, WebSocket 생성 실패는
  REST 현재가 경로를 방해하지 않도록 격리했다. 차트에는 기간·최신 종가·변동률의 접근 가능한
  요약을 추가했고, 리서치 탭은 방향키·Home/End·상태 알림을 지원한다.
- 재분석 중에는 기존 회의록을 유지하고 최신 요청 실패 시에도 이전 결과가 사라지지 않게 했다.
- production preflight는 Settings와 맞춰 기업행동 승인·artifact 활성화 의존성과 활성
  Toss/DART/RSS/KIS/OpenAI URL의 HTTPS를 검사한다. 기본 노트북 테스트는 XGBoost 전용
  파일을 `ml` marker로 분리해 추가 ML 설치 없이 실행 가능하다.
- 가벼운 검증: `pytest -q -m "not ml"` 결과 `287 passed, 4 deselected`, 기존 설치된 ML
  의존성으로 실행한 `pytest -q -m ml` 결과 `4 passed`, 전체 `pytest -q` 결과 `291 passed`.
  Ruff, TypeScript, `git diff --check`도 통과했다. 대용량 빌드·Docker 재빌드·외부 API 호출은
  수행하지 않았다.

## 2026-07-21 노트북 최신 작업

<!-- current-alembic-head: 20260720_0021 -->

- 사용자 분석 화면을 참고 시그널 중심 결과 보드로 재구성하고 신호별 상태, 진행 단계,
  모바일 공유, 접근성 상태 알림과 reduced-motion 처리를 추가했다.
- `ALLOWED_HOSTS`를 FastAPI와 Next.js 관리자 경계에 적용했다. 운영 환경은 전역 `*`를
  거부하며 API와 웹 응답에 호환 가능한 CSP를 추가했다.
- 선택형 XGBoost artifact 런타임 활성화를 구현했다. 기본값은 비활성화이며 활성화 시
  모델 범위·크기·일반 파일·SHA-256을 검증하고 원자적 활성 포인터를 사용한다. 저장소
  수준의 이전 버전 롤백과 활성 artifact 재사용 테스트를 포함한다.
- 캔들 보정 기준 inventory에 그룹별 `evidence_required` 체크리스트를 추가했다. 기존
  `legacy_unknown` 행은 여전히 수정하거나 자동 재분류하지 않는다.
- 브라우저 시장 조회를 GET 전용 `/api/market/*` BFF로 전환했다. 고비용 분석 요청은
  선택형 `ANALYSIS_API_KEY`를 서버 사이드에서만 전달하며 운영 환경은 32자 이상을 요구한다.
- CI 권한 최소화, GitHub Action SHA 고정, Dependabot, 추적 파일 위생 검사를 추가했다.
- Toss·DART·KIS·OpenAI 활성화 시 자격증명을 설정 단계에서 fail-fast 검증하며, 설정
  오류에는 입력값을 표시하지 않아 시작 로그의 비밀값 조각 노출을 차단한다.
- `Settings`·Docker Compose·`.env.example` 환경변수 계약 검사를 CI에 추가했으며,
  민감한 템플릿 값은 빈 값 또는 `change-me`만 허용한다. 누락됐던 `INSTALL_ML`도 보완했다.
- 운영 배포 전에 명시한 env 파일만 읽고 값은 출력하지 않는 production preflight를 추가했다.
  PostgreSQL·Redis·HTTPS·Host/CORS·내부 관리 키·활성 Provider 자격증명 조합을 검사한다.
- Markdown 상대 링크와 문서의 현재 Alembic head를 실제 revision 그래프와 대조하는 CI 검사를
  추가하고, 오래된 `0018`·`0019` 현재-head 표기를 `20260720_0021`로 바로잡았다.
- CI에 격리 PostgreSQL 16의 `head → base → head` 마이그레이션 왕복 job을 추가했다. 로컬
  회귀 테스트는 임시 SQLite DB로 같은 전체 revision 체인을 검증하며 실제 DB는 건드리지 않는다.
- 최종 검증: 백엔드 283개 테스트, Ruff, 저장소 위생·환경 계약·문서 검사 통과. 직전 TypeScript,
  Alembic head, Compose 설정 검사도 통과 상태다.

데스크탑에서는 optional XGBoost 활성화를 켜기 전에 장기 Walk-Forward 학습으로 생성한
artifact를 검증하고, 별도 복사본으로 활성화·롤백 리허설을 수행한다. 실제 artifact와
학습 데이터는 Git에 올리지 않는다.

## 2026-07-19 최신 인계 상태

노트북에서 Phase 16 운영 데이터 수명주기와 캔들 파티션 아카이브 미리보기를 구현했다.
데이터 품질 로그, 뉴스, 공시만 고정 허용목록으로 정리하며 관리자 미리보기, 수동 실행,
일일 스케줄러, 운영 상태, 관리자 UI와 `created_at` 인덱스 마이그레이션
(`20260719_0017`)이 포함된다. 캔들, 거래, 백테스트, 예측, AI 리포트, 모델, 포트폴리오,
보유 종목, Provider 감사 로그는 이 작업의 자동 삭제 대상이 아니다.

오래된 `stock_candles_YYYY_MM` 파티션은 기본 120개월 hot-storage 기준으로 검토 후보만
표시한다. default·비정상 이름·최근 파티션은 제외하며 `automatic_action=false`라서 이동,
분리, 삭제를 실행하지 않는다.

기업행동 revision과 캔들 `price_basis` 메타데이터도 추가했다. Mock은 `unadjusted`, Toss
조정 캔들은 `provider_adjusted`, 보정 엔진 출력은 `point_in_time_adjusted`로 구분한다.
엔진은 기준시점 이후에 알려진 revision을 사용하지 않고 provider-adjusted·legacy unknown
캔들을 거부해 Look-ahead와 이중 보정을 차단한다. raw/cleaned DB 행은 수정하지 않는다.

데스크탑에서는 [검증 체크리스트](docs/operations/desktop-validation.md)와
[PostgreSQL 백업·복구 절차](docs/operations/postgresql-backup-restore.md)를 따라 Docker
재빌드와 격리 복구 리허설만 수행한다. 실제 정리 전 관리자 화면의 미리보기 결과와 조직의
보존정책을 확인하고 `DATA_LIFECYCLE_CLEANUP_ENABLED`는 승인 후 활성화한다.

## 작업 분담 원칙

- 노트북: 일반 코드 구현, 문서, 단위·통합 테스트, TypeScript 검사, 가벼운 로컬 검증
- 데스크탑: Docker 전체 재빌드, PostgreSQL 백업·복구 리허설, 장시간 soak/load 테스트,
  대형 ML 의존성 설치와 XGBoost 장기 학습
- 작업 단위마다 자동 commit/push하지 않는다. 환경을 바꾸기 직전에만 사용자가 요청한
  방식으로 변경 사항을 검토·전달하고, 데스크탑은 그 시점의 원격 저장소 또는 전달본을
  기준으로 무거운 검증을 수행한다.
- 두 환경에서 동시에 같은 파일을 수정하지 않는다. 환경을 넘기기 전 변경 목록과 검증
  결과를 먼저 확인한다.

## 1. 데스크탑 Codex에게 바로 전달할 요청

아래 내용을 새 Codex 대화의 첫 요청으로 전달한다.

```text
C:\stock_assist의 StockPilot AI 프로젝트 작업을 이어서 진행해줘.
먼저 DESKTOP_CODEX_HANDOFF.md를 끝까지 읽고, 현재 코드와 테스트 결과가 문서 내용과
일치하는지 읽기 전용으로 확인해. .env의 실제 비밀 값은 출력하거나 문서화하지 마.

이 프로젝트는 노트북에서 일반 개발을 진행하고 데스크탑에서는 용량이 큰 검증만 한다.
현재 요청받은 작업 범위가 Docker 전체 재빌드, PostgreSQL 복구 리허설, 장시간 부하·실데이터
테스트 또는 대형 ML 학습인지 먼저 확인해. 해당 범위가 아니면 코드 변경 없이 상태만 보고해.

작업 후 다음 명령으로 검증해:
- .venv\Scripts\ruff.exe check backend
- .venv\Scripts\pytest.exe -q
- & 'C:\stock_assist\apps\web\node_modules\.bin\tsc.CMD' -p apps/web/tsconfig.json --noEmit --incremental false

디스크 사용량을 최소화해야 하므로 요청 없이 전체 의존성 재설치, Docker 이미지 재빌드,
Next production build, 대형 ML 패키지 설치를 하지 마. 서버와 Docker도 필요할 때만 켜.
```

## 2. 프로젝트 목적과 절대 원칙

StockPilot AI는 국내·미국 주식의 시장 데이터, 기술·재무·뉴스·공시·수급 분석,
백테스트, ML 예측과 AI 설명을 통합하는 투자 의사결정 지원 시스템이다.

- AI는 주문이나 투자 결정을 대신하지 않는다.
- 시스템 용어는 `추천` 대신 `참고 시그널(Reference Signal)`을 사용한다.
- AI 출력은 `data_as_of`, `disclaimer`, `is_investment_advice: false`를 포함한다.
- Score, ML, Signal은 장기 백테스트 전까지 `experimental`이다.
- 시점 T의 판단에 미래 데이터를 사용하는 Look-ahead Bias를 허용하지 않는다.
- LLM은 계산하지 않고 계산 엔진의 정형 결과를 설명한다.
- Phase 17 주문·조건주문은 규제 검토 전까지 구현하거나 활성화하지 않는다.
- `.env`, API 토큰, client secret, 계좌번호를 로그·응답·문서에 노출하지 않는다.

## 3. 현재 구현 상태

대략적인 상태는 기능 MVP 88~92%, 운영 가능한 베타 70~75%다.

### 완료 또는 MVP 완료

- Phase 0~2: 모노레포, FastAPI/Next.js, PostgreSQL/Redis, MockProvider, Provider Capability
- Phase 3: raw/cleaned 캔들 수집, 정합성 검사, 집계, 스케줄러, 파티션 관리
- Phase 4~5: Lightweight Charts, 기술지표와 차트·캔들 패턴
- Phase 6: Vectorized 및 Event-driven 백테스트, 비용·부분 체결·유동성 제약
- Phase 7: 6축 Score Engine과 외부화된 가중치
- Phase 8: Toss OAuth, 토큰 캐시, 그룹별 Rate Limit, 오류 매핑, 국내·미국 종목
- Phase 9~11: DART 재무, 뉴스·공시, KIS 수급
- Phase 12: Lightweight/XGBoost 예측, Walk-Forward, Champion/Challenger 메타데이터
- Phase 13: 제한된 Multi-Agent 분석, AI 리포트, Compliance Validator
- Phase 14: Toss 본인 계좌·보유 종목 동기화와 포트폴리오 분석
- Phase 15: Toss 폴링 및 KIS 국내·미국 WebSocket 실시간 구조
- Phase 16 일부: 관리자 화면, 이벤트 백테스트 비교, 데이터 품질, 수동 수집,
  운영 상태, 보안 강화, Provider 감사 이력

### 가장 최근 완료 작업

- 기업행동 source/event/revision 불변 이력과 `known_at` 기준시점 저장
- 분할·병합·현금/주식배당·유상증자 가격/거래량 계수 모델
- confirmed·cancelled 정정 이력을 재현하는 point-in-time 보정 엔진
- `stock_candles.price_basis` provenance와 혼합 기준 정제 차단
- Toss `adjusted=true` 캔들의 이중 보정 차단
- 관리자 전용 기업행동 조회 API, BFF와 읽기 전용 이력 화면
- Alembic revision `20260720_0021`가 현재 head
- 기업행동 이력을 운영 데이터 자동 정리 대상에서 제외
- 기업행동 공급자 trust metadata와 검증 공급자 전용 수집 계약
- 최대 500건 원자적·멱등 수동 수집 API 및 관리자 공급자 상태 표시
- 실제 공급자 미등록 시 fail-closed, 분석 소비자 자동 연결은 계속 비활성화
- DART 무상증자·비례감자 검토 매퍼와 SEC 공시후보 전용 정책
- DART corpCode + `fricDecsn`/`crDecsn` 실제 후보 수집 어댑터와 관리자 조회 UI
- 후보 조회는 최대 366일·200건이며 DB 저장·자동확정·분석 반영을 모두 금지
- DART `list.json(last_reprt_at=N)` 기반 정정 표시·제목 보강과 revision 그룹 제안
- 그룹 제안은 수동확인 필수·저장 불가이며 durable source event ID로 사용하지 않음
- 기본 비활성화된 DART 후보 수동 승인 API와 KRX 근거 URL 검증
- 후보 재조회 후 확정 revision과 불변 승인 근거를 한 트랜잭션으로 저장
- 승인 시각을 `known_at`으로 강제하고 동일 근거 재요청을 멱등 처리

주요 파일:

- `backend/app/corporate_actions/engine.py`
- `backend/app/models/corporate_action.py`
- `backend/app/repositories/corporate_action.py`
- `backend/app/repositories/corporate_action_approval.py`
- `backend/app/services/corporate_actions.py`
- `backend/alembic/versions/20260719_0018_corporate_actions.py`
- `backend/alembic/versions/20260720_0019_corporate_action_approvals.py`
- `backend/alembic/versions/20260720_0020_candle_source_provider.py`
- `backend/alembic/versions/20260720_0021_candle_price_basis_policy.py`
- `backend/app/services/candle_inventory.py`
- `apps/web/components/corporate-action-history.tsx`
- `docs/architecture/corporate-action-adjustments.md`
- `apps/web/lib/admin-api.ts`

## 4. 이전 검증 스냅샷

아래는 기업행동 작업 직후의 이전 검증 결과이며, 최신 노트북 검증 결과는 문서 첫 부분의
2026-07-23 항목을 기준으로 한다.

- 백엔드 전체 테스트: `246 passed`
- 최근 기업행동 승인·정정·후보·source·수집·보안 집중 테스트: `38 passed`
- Ruff 검사: 통과
- 프론트 TypeScript 검사: 통과
- Alembic: `20260720_0021 (head)`
- 캔들 수집: 종목, raw/cleaned 캔들, 품질 로그를 단일 DB 트랜잭션으로 저장하며 최종 단계 실패 시 전체 롤백
- 가격 기준 inventory: `symbol` 필수, 종목 선두 복합 인덱스로 전체 이력 무제한 집계 차단
- 기업행위 승인 증빙 URL: HTTPS 허용 호스트 외에 비표준 포트와 fragment도 차단
- 구조화 거래소 검증 결과: 등록된 공식 source metadata와 다른 evidence 호스트 차단
- 관리자 기업행위 승인 UI/BFF: 후보 재조회, 직접 입력한 적용 시각·KRX URL·확인 문구를 요구하며 기본 비활성화 유지
- 관리자 BFF CSRF 방어: POST/DELETE는 Basic 인증 후 동일한 `Origin`만 허용
- 당시 검증 시점의 서버와 Docker Compose: 꺼진 상태

검증 명령:

```powershell
.venv\Scripts\ruff.exe check backend
.venv\Scripts\pytest.exe -q -m "not ml"
& 'C:\stock_assist\apps\web\node_modules\.bin\tsc.CMD' -p apps/web/tsconfig.json --noEmit --incremental false
.venv\Scripts\alembic.exe -c alembic.ini heads
```

주의할 점:

- Git 원격은 `https://github.com/origangjung/stockassist.git`, 기본 브랜치는 `main`이다.
  사용자가 변경을 Git으로 전달한 경우에만 데스크탑에서 `git pull --ff-only origin main`을
  실행한다. 자동 commit/push로 전달하지 않으며, 원격이 아닌 전달본을 받았다면 해당 worktree
  또는 archive가 검증된 버전인지 먼저 확인한다.
- `ruff format --check backend`는 이번 작업과 무관한 기존 파일 일부도 포맷 대상으로
  표시한다. 전역 자동 포맷으로 사용자 변경을 넓게 수정하지 않는다.
- PowerShell 출력에서 UTF-8 한국어가 깨져 보일 수 있다. 실제 파일 인코딩을 임의로
  변환하지 말고 UTF-8을 유지한다.

## 5. 다음 작업 우선순위

### 완료 — Provider 감사 로그 보존과 자동 정리

다음 항목이 구현되었다.

1. `PROVIDER_AUDIT_RETENTION_DAYS` 설정 추가
2. 운영 기본값과 최소·최대 범위 검증
3. Repository에 기준 시각 이전 로그 삭제 기능 추가
4. APScheduler를 이용한 하루 1회 정리 작업
5. 삭제 건수, 마지막 성공 시각, 마지막 오류를 운영 상태에 표시
6. 정리 실패는 로깅하되 시장 데이터 요청과 서버 시작을 막지 않도록 격리
7. 관리자 전용 수동 정리 API에 명시적 보존 범위 제한 적용
8. SQLite/PostgreSQL 호환 테스트, 설정 테스트, 관리자 인증 테스트 추가
9. `.env.example`, 보안·운영·Toss Provider 문서 갱신

삭제 대상은 반드시 `provider_audit_logs`로 제한하고 다른 감사·AI 리포트·백테스트
이력을 함께 삭제하지 않는다.

### 완료 — 운영 데이터 수명주기와 파티션 아카이브 계획

- 뉴스, 공시, 데이터 품질 로그의 테이블별 보존 정책과 정리 미리보기
- PostgreSQL 백업 및 격리 복구 리허설 문서
- 오래된 월 파티션의 비파괴 아카이브 후보 미리보기
- 감사 로그, 운영 데이터, 사용자 분석 이력의 보존 범위 분리
- 캔들·백테스트·예측·AI 리포트·포트폴리오 자동 삭제 금지

### 완료 — 분석 데이터 보정 메타데이터

- 액면분할·배당락 등 기업행동 보정 규칙의 revision·기준시점 스키마
- raw/cleaned 캔들을 보존하는 별도 point-in-time 보정 뷰
- 시점 T 이후에 알려진 정정·취소를 사용하지 않는 검증
- 공급자 조정 캔들과 legacy unknown 데이터의 이중 보정 차단

### 진행 중 — 기업행동 수집과 소비자 opt-in 설계

- 완료: 국내·미국 기업행동 source용 Provider 신뢰·revision 계약 정의
- 완료: source event를 원자적 불변 revision으로 적재하는 idempotent 수집 서비스
- 완료: 관리자 상태/수동 수집 API와 expensive-operation rate limit
- 완료: DART·SEC 공식 API 범위 검토와 experimental 후보 정책
- 완료: DART 무상증자·비례감자 필드 매핑 및 오입력 계약 테스트
- 완료: DART 구조화 API 기반 read-only 실제 후보 수집 어댑터
- 완료: DART 정정 공시의 보수적 revision 그룹 제안과 충돌 방지
- 완료: 원문·거래소 근거를 기록하는 수동 승인 DTO와 confirmed 승격 워크플로
- 완료: 후보 재조회, KRX URL 검증, 승인 시각 `known_at`, 원자적 승인 감사 이력
- 완료: KRX 공개 API와 계약형 EOD 참조정보를 구분하는 거래소 검증 Provider 계약
- 완료: 검증되지 않은 효력일 source·타임스탬프·provenance를 차단하는 fail-closed 게이트
- 완료: 미국 Nasdaq Daily List·NYSE Market Event Feed·DTCC·SEC 역할 및 커버리지 정책
- 완료: 백테스트 전용 `forward_point_in_time` 기업행동 opt-in과 재현 메타데이터 저장
- 완료: 공급자 보정·unknown·늦게 알려진 사건·정정 이력의 보수적 차단
- 남음: KRX 계약형 종목이벤트 명세 확보 후 효력일 필드 검증·실제 Provider 구현
- 남음: Nasdaq·NYSE 계약/재배포 조건 확인 후 미국 실제 factor Provider 구현
- 완료: 신규 캔들의 Provider provenance 저장과 기존 `legacy_unknown`/`unknown` 현황을
  변경 없이 집계하는 관리자 inventory API
- 완료: 관리자 운영 탭의 캔들 보정 기준 inventory 패널, 종목 필터, 차단 사유 표시,
  수동 수집 후 자동 캐시 갱신(BFF 읽기 전용 경계 유지)
- 완료: Mock/Toss의 버전화된 `price_basis` 정책 선언, Broker Adapter 중앙 계약 검증,
  캔들별 정책 버전 저장 및 계약 테스트
- 남음: 실제 운영 inventory를 검토해 기존 행의 개별 근거를 마련하는 절차
  (자동·일괄 relabel은 계속 금지)
- Indicator·Score·ML에는 자동 보정을 연결하지 않고 Backtest도 명시적 opt-in만 허용
- 실제 대량 backfill과 장기 성능 측정은 데스크탑 검증으로 분리

### 다음 데스크탑 작업 — 실데이터 장시간 검증

- 장 운영 시간대 Toss REST 폴링 soak test
- Toss 401/403/429/5xx와 `Retry-After` 실제 동작 확인
- KIS 국내·미국 WebSocket 재연결, 구독 해제, 40종목 제한 검증
- Redis 장애·재시작 중 Pub/Sub 및 분산 Rate Limit 동작 확인
- 민감한 실제 응답은 테스트 fixture나 로그에 저장하지 않는다.

### 우선순위 4 — 분석 신뢰도 고도화

- 상장폐지 종목을 포함한 장기 백테스트 유니버스
- 액면분할·배당락·거래정지 보정 강화
- 실제 수수료·세금·슬리피지 보정
- 여러 시장 구간의 Walk-Forward 결과 비교
- Champion 승격 후 런타임 모델 artifact 활성화

Model Registry의 checksum 검증·원자적 활성 포인터·이전 버전 롤백 구현은 완료됐지만 기본값은
비활성이다. 데스크톱에서는 장기 Walk-Forward로 생성한 실제 artifact를 검증하고, 별도
복사본에서 활성화·롤백 리허설을 수행한 뒤에만 운영 활성화를 검토한다.

### 우선순위 5 — 배포 및 운영 검증

- HTTPS 운영 도메인
- 고정 Egress IP와 Toss 허용 IP
- 배포용 Secret Manager
- Prometheus/Grafana 경보 규칙과 Sentry 확인
- PostgreSQL/Redis 부하 및 장애 복구 테스트
- KRX 시세 재배포 계약과 개인정보·보존 정책 검토

### 보류 — Phase 17 조건주문

Toss SINGLE/OCO/OTO, 손절·익절 자동 집행, 고액 주문 재확인과 주문 멱등성은
투자일임업 및 자동매매 규제 검토가 끝나기 전까지 구현·활성화하지 않는다.

## 6. 환경과 비밀정보

- `.env`에는 사용자가 직접 입력한 Toss 자격증명이 있다.
- 실제 값을 읽어서 응답하거나 테스트 출력에 포함하지 않는다.
- `.env.example`에는 키 이름과 안전한 예시만 유지한다.
- 운영 환경에서는 `.env` 대신 Secret Manager 사용이 목표다.
- Toss는 허용 IP 등록이 필요하며 운영 배포에는 고정 Egress IP가 필요하다.
- KIS 자격증명 설정 여부는 실제 값을 출력하지 않고 존재 여부만 확인한다.

## 7. 디스크 사용량 최소화 원칙

사용자는 프로젝트 디스크 사용량 최소화를 요청했다.

- 요청 없이 `pnpm install`, `uv sync`, Docker 전체 재빌드를 반복하지 않는다.
- 기본 예측 엔진은 경량 구현을 유지한다.
- XGBoost 관련 `--extra ml`은 실제 ML 검증 시에만 설치한다.
- Next.js production build는 필요할 때만 수행한다.
- `.next`, Docker 이미지, Python 캐시는 임의 삭제하지 말고 삭제 전 사용자 승인을 받는다.
- 테스트는 먼저 관련 파일만 실행하고 마지막에 전체 회귀 테스트를 실행한다.

## 8. 완료 판단 기준

각 작업은 다음 조건을 모두 만족해야 완료다.

1. 설정과 실패 모드가 명시되어 있다.
2. API Router에 비즈니스 로직을 넣지 않는다.
3. Provider 교체가 Service 수정으로 이어지지 않는다.
4. 관리자 기능은 BFF와 관리자 인증을 통과한다.
5. 민감정보가 로그·DB·프론트 응답에 포함되지 않는다.
6. 단위·통합 테스트와 타입 검사가 통과한다.
7. 관련 `.env.example`과 설계 문서가 함께 갱신된다.
8. 서버나 Docker를 켰다면 작업 후 상태를 사용자에게 명확히 알린다.
