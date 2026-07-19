# StockPilot AI — Desktop Codex 인수인계

> 작성일: 2026-07-16
> 작업 경로: `C:\stock_assist`
> 기준 설계: StockPilot AI Master Project Blueprint v2.1

## 2026-07-19 최신 인계 상태

노트북에서 Phase 16 운영 데이터 수명주기 기능을 구현했다. 데이터 품질 로그, 뉴스,
공시만 고정 허용목록으로 정리하며 관리자 미리보기, 수동 실행, 일일 스케줄러, 운영 상태,
관리자 UI와 `created_at` 인덱스 마이그레이션(`20260719_0017`)이 포함된다. 캔들, 거래,
백테스트, 예측, AI 리포트, 모델, 포트폴리오, 보유 종목, Provider 감사 로그는 이 작업의
자동 삭제 대상이 아니다.

데스크탑에서는 [검증 체크리스트](docs/operations/desktop-validation.md)와
[PostgreSQL 백업·복구 절차](docs/operations/postgresql-backup-restore.md)를 따라 Docker
재빌드와 격리 복구 리허설만 수행한다. 실제 정리 전 관리자 화면의 미리보기 결과와 조직의
보존정책을 확인하고 `DATA_LIFECYCLE_CLEANUP_ENABLED`는 승인 후 활성화한다.

## 작업 분담 원칙

- 노트북: 일반 코드 구현, 문서, 단위·통합 테스트, TypeScript 검사, 가벼운 로컬 검증
- 데스크탑: Docker 전체 재빌드, PostgreSQL 백업·복구 리허설, 장시간 soak/load 테스트,
  대형 ML 의존성 설치와 XGBoost 장기 학습
- 노트북 작업을 완료하고 테스트한 뒤 `main`에 push하면 데스크탑은 pull하여 무거운
  검증만 수행한다. 데스크탑 결과도 코드·문서·측정 보고서 형태로 commit/push한다.
- 두 환경에서 동시에 같은 파일을 수정하지 않는다. 작업을 넘기기 전 항상 push하고,
  이어받는 환경에서는 먼저 pull한다.

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

대략적인 상태는 기능 MVP 85~90%, 운영 가능한 베타 65~70%다.

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

- Toss 호출의 성공·실패 외부 `requestId`와 내부 요청 ID 감사 저장
- 상태 코드, API 그룹, 최종 결과, 재시도 횟수, 소요 시간 저장
- 토큰, 계좌번호, 쿼리·요청/응답 본문은 감사 이력에서 제외
- 관리자 전용 `GET /api/v1/admin/provider-audits` 추가
- 관리자 BFF `/api/admin/provider-audits` 및 운영 화면 추가
- Alembic revision `20260716_0016`이 현재 head
- Provider 감사 로그 기본 90일 보존, 일일 자동 정리, 관리자 수동 정리와 운영 상태 표시

주요 파일:

- `backend/app/providers/toss/client.py`
- `backend/app/providers/audit.py`
- `backend/app/models/provider_audit.py`
- `backend/app/repositories/provider_audit.py`
- `backend/app/services/provider_audit.py`
- `backend/alembic/versions/20260716_0016_provider_audit_logs.py`
- `apps/web/components/provider-audit-history.tsx`
- `apps/web/app/api/admin/provider-audits/route.ts`
- `apps/web/lib/admin-api.ts`

## 4. 현재 검증 상태

마지막으로 확인된 결과:

- 백엔드 전체 테스트: `170 passed`
- 최근 관리자·감사 집중 테스트: `15 passed`
- Ruff 검사: 통과
- 프론트 TypeScript 검사: 통과
- Alembic: `20260716_0016 (head)`
- 서버와 Docker Compose: 현재 꺼진 상태

검증 명령:

```powershell
.venv\Scripts\ruff.exe check backend
.venv\Scripts\pytest.exe -q
& 'C:\stock_assist\apps\web\node_modules\.bin\tsc.CMD' -p apps/web/tsconfig.json --noEmit --incremental false
.venv\Scripts\alembic.exe -c alembic.ini heads
```

주의할 점:

- Git 원격은 `https://github.com/origangjung/stockassist.git`, 기본 브랜치는 `main`이다.
  데스크탑 작업 전 `git pull --ff-only origin main`으로 노트북 완료분을 먼저 받는다.
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

### 다음 노트북 작업 — 운영 데이터 수명주기

- 뉴스, 공시, 시세 캐시, 데이터 품질 로그의 테이블별 보존 정책
- PostgreSQL 백업 및 실제 복구 리허설 문서
- 월 파티션 생성뿐 아니라 오래된 파티션 보관·아카이브 정책
- 감사 로그와 사용자 분석 이력의 보존 기간 분리

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

현재 Model Registry의 승격은 메타데이터 변경까지이며 실제 런타임 artifact 전환은
아직 수행하지 않는다. 원자적 활성화·롤백·artifact 검증을 설계한 뒤 구현해야 한다.

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
