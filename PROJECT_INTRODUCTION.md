# StockPilot AI

> 시장 데이터와 계산 엔진, 머신러닝, AI 설명을 한곳에 모은 투자 의사결정 지원 플랫폼

StockPilot AI는 국내·미국 주식의 시장 데이터를 분석하고, 기술지표·재무·뉴스·공시·수급·위험·머신러닝 결과를 종합해 사용자가 판단 근거를 한눈에 확인하도록 돕는 프로젝트입니다.

이 프로젝트의 AI는 투자 결정을 대신하지 않습니다. 계산된 데이터와 불확실성, 반대 근거를 함께 설명하며 모든 결과는 참고 정보로만 제공됩니다.

## 무엇을 확인할 수 있나요?

- 국내·미국 종목 검색, 현재가, 캔들, 호가와 체결 데이터
- 종목 코드 조회 후 현재가·차트·AI 분석이 함께 전환되는 동적 시장 화면
- TradingView Lightweight Charts 기반 반응형 캔들 차트
- 차트의 MA5·MA20·거래량 오버레이와 기술지표·패턴 스냅샷
- RSI, MACD, 이동평균, Bollinger Bands, ATR, ADX, MFI, VWAP, OBV, SuperTrend
- 도지·해머·장악형, 20봉 돌파, 확인된 이중 천장·이중 바닥 패턴
- DART 재무제표, 뉴스 감성, 공시 위험, 국내 외국인·기관 수급 분석
- 거래비용을 반영한 벡터·이벤트 기반 백테스트와 패턴 검증 전략
- 여러 비중복 시계열 구간의 안정성을 비교하는 Walk-Forward 백테스트 검증
- XGBoost 상승확률 추정과 Champion/Challenger Model Registry
- 6축 Score Engine과 실험 상태의 참고 시그널
- Technical, Financial, News, Disclosure, Prediction, Risk, Chart Pattern Agent를 종합한 AI 리포트
- Toss 계좌 기반 본인 보유종목 동기화와 포트폴리오 집중도·손실 노출 분석
- 관심종목, 가격 참고 알림, 관리자 화면
- 관리자 미리보기와 고정 허용목록을 사용하는 운영 데이터 보존·정리
- 자동 삭제 없이 오래된 월별 캔들 파티션을 식별하는 아카이브 미리보기
- 원본 캔들을 보존하는 기준시점 기업행동 revision과 보정 뷰
- Toss REST 폴링과 KIS WebSocket 기반 준실시간·실시간 시세 구조

## StockPilot AI의 차이점

### 계산과 설명을 분리합니다

지표, 점수, 패턴, 백테스트와 예측은 결정론적 엔진 또는 ML 모델이 계산합니다. LLM은 공급받은 정형 결과만 설명하며 숫자를 새로 계산하지 않습니다.

```text
Market Data
  → Data Quality Pipeline
  → Indicator / Pattern / Score / Prediction Engines
  → Bounded Analysis Agents
  → AI Explanation
  → Compliance Validator
  → Reference-only Report
```

### 데이터 공급자를 교체할 수 있습니다

서비스 로직은 특정 증권사에 직접 의존하지 않습니다. Capability 기반 Broker Adapter가 요청 기능에 맞는 Provider를 선택합니다.

- MockProvider: API 키 없이 재현 가능한 개발·테스트 데이터
- TossProvider: REST 시세, 종목, 투자유의, 본인 계좌 데이터
- KISProvider: 국내 수급과 WebSocket 실시간 보완

### 규정 준수를 코드로 강제합니다

모든 주요 분석 응답에는 다음 필드가 포함됩니다.

- `data_as_of`: 데이터 기준시점
- `disclaimer`: 투자 참고 정보 고지
- `is_investment_advice: false`
- `validation_status: experimental`: 정량 검증 전 기능 표시

AI 출력은 매수·매도 지시형 표현을 Compliance Validator에서 차단합니다. 주문 API와 타인 계좌 자동매매 기능은 제공하지 않습니다.

## 빠르게 실행하기

### Docker Compose

Docker Desktop과 가상화/WSL2가 준비된 환경에서 실행합니다.

```powershell
Copy-Item .env.example .env
docker compose up --build
```

실행 후 접속 주소:

- 웹 애플리케이션: `http://localhost:8080`
- FastAPI 문서: `http://localhost:8080/docs`

처음에는 `.env`의 `STOCK_PROVIDER=mock`을 유지하면 외부 API 키 없이 사용할 수 있습니다. 실제 Provider를 사용할 때만 해당 자격증명을 서버 환경변수에 설정합니다. `.env` 파일과 API 키는 저장소에 커밋하면 안 됩니다.

### 로컬 개발

```powershell
python -m pip install uv==0.11.28
uv sync --locked --extra dev
uv run alembic upgrade head
uv run python -m uvicorn app.main:app --app-dir backend --reload
```

기본 설치는 경량 예측 기준선을 사용한다. XGBoost 연구 환경이 필요한 경우에만
`uv sync --locked --extra dev --extra ml`을 실행하고 `PREDICTION_ENGINE=xgboost`를 설정한다.

프론트엔드는 별도 터미널에서 실행합니다.

```powershell
corepack enable
pnpm install --frozen-lockfile
pnpm --filter @stockpilot/web dev
```

## 대표 API

| API | 용도 |
| --- | --- |
| `GET /api/v1/stocks/{symbol}/quote` | 현재가 |
| `GET /api/v1/stocks/{symbol}/candles/processed` | 검증·집계 캔들 |
| `GET /api/v1/stocks/{symbol}/indicators` | 기술지표 |
| `GET /api/v1/stocks/{symbol}/patterns` | 차트·캔들 패턴 |
| `GET /api/v1/stocks/{symbol}/score` | 6축 종합 점수 |
| `GET /api/v1/stocks/{symbol}/prediction` | 실험 ML 확률 |
| `GET /api/v1/stocks/{symbol}/ai-report` | Multi-Agent 종합 리포트 |
| `POST /api/v1/backtests/walk-forward` | 전략의 구간별 Walk-Forward 검증 |
| `WS /ws/v1/quotes/{symbol}` | 실시간 시세 팬아웃 |

Mock 데이터에서 사용할 수 있는 예시 종목은 `005930`, `000660`, `035420`, `AAPL`, `MSFT`, `TSLA`입니다.

관리자 화면에서는 Walk-Forward 검증을 직접 실행하고 평균 구간 수익률, 수익 구간 비율,
최악 MDD, 평균 Sharpe 및 fold별 결과를 확인할 수 있습니다. 관리자 API 키는 Next.js의
서버 BFF에서만 전달되며 브라우저 응답이나 클라이언트 번들에는 포함되지 않습니다.

## 기술 구성

- Frontend: Next.js App Router, React, TypeScript, TanStack Query, Lightweight Charts
- Backend: Python 3.12+, FastAPI, SQLAlchemy, Alembic, APScheduler
- Data: PostgreSQL 16, Redis
- Analysis/ML: Pandas, NumPy, scikit-learn, XGBoost
- Infrastructure: Docker Compose, Nginx, Prometheus, Grafana, Sentry, GitHub Actions

## 현재 개발 상태

기능 로드맵 진행률은 약 **85%**, 실제 외부 Provider와 장시간 장애 시험까지 포함한 운영
준비도는 약 **65%**입니다.

| 단계 | 상태 | 현재 범위 |
| --- | --- | --- |
| Phase 0~2 | 완료 | 모노레포·인프라·Stock Data Layer·MockProvider |
| Phase 3~7 | MVP 완료 | 파이프라인·차트·지표·백테스트·Score Engine |
| Phase 8~11 | MVP 완료 | Toss·DART·뉴스/공시·국내 수급 Provider |
| Phase 12~15 | MVP 완료 | ML·Multi-Agent·포트폴리오·폴링/KIS 실시간 구조 |
| Phase 16 | 진행 중 | 이벤트 백테스트·관리자·관측성·데이터 품질·파티션 운영 |
| Phase 17 | 보류 | 조건주문은 계약·규제 검토 통과 후 진행 |

시장 데이터부터 AI 참고 리포트까지 이어지는 핵심 MVP 파이프라인과 관리자용 전략
구간 검증 화면이 구현되어 있습니다. 자동 주문 없이 분석·검증·계좌 조회·참고 알림에
집중하고 있습니다. 관리자 화면에서는 PostgreSQL·Redis 준비 상태, 활성 Provider,
기능 플래그와 실시간 처리 한도를 30초 주기로 확인할 수 있습니다. 또한 종목·심각도별
데이터 품질 이력을 조회해 수집 과정의 결측·중복·비정상 OHLCV 문제를 추적할 수 있습니다.
운영 데이터 정리는 데이터 품질 로그·뉴스·공시만 대상으로 하며 삭제 전 대상 건수와
기준 시각을 관리자 화면에서 확인할 수 있습니다. 연구 재현에 필요한 캔들·백테스트·예측·
AI 리포트·포트폴리오는 이 자동 정리 범위에서 제외됩니다.
장기 캔들 데이터도 자동 삭제하지 않으며, 관리자는 설정된 hot-storage 기간보다 오래된
완결 월 파티션을 아카이브 검토 대상으로만 확인할 수 있습니다.
설정된 국내·미국 수집 유니버스를 확인하고 관리자 인증 아래 특정 종목의 캔들 수집을
명시적으로 실행할 수도 있습니다. 이 동작은 시세 저장만 수행하며 주문을 실행하지 않습니다.
중복·OHLC·거래량·시간 순서 외에도 연속 5영업일 이상의 캔들 공백을 보수적으로 감지해
일반 주말이나 짧은 휴장 기간의 오탐을 줄입니다.
이벤트 백테스트는 캔들 거래량 참여율에 따라 부분 체결과 유동성 거절을 기록하며,
Walk-Forward 화면에서 fold별 체결 제약 발생 횟수를 함께 확인할 수 있습니다.

추가 개발 및 운영 검증이 필요한 영역:

- 이벤트 기반 백테스트 고도화
- 패턴·Score·ML의 장기간 Walk-Forward 성능 검증
- 실거래 시간대 Toss/KIS 장시간 장애·재연결 시험
- 관리자 운영 도구와 모니터링 고도화
- 시세 재배포 및 조건주문 관련 계약·규제 검토

## 반드시 확인해 주세요

StockPilot AI가 제공하는 점수, 확률, 패턴, 지지·저항과 참고 시그널은 투자 권유나 수익 보장이 아닙니다. 실제 투자 판단과 손실 책임은 사용자에게 있으며, 실데이터를 제3자에게 제공하거나 상용화할 때는 거래소·데이터 공급자 계약과 관련 법규를 별도로 검토해야 합니다.

StockPilot AI는 “무엇을 사야 하는가”보다 “어떤 데이터와 위험을 확인하고 판단해야 하는가”를 더 명확하게 보여주는 것을 목표로 합니다.

## 사용자 리서치 화면

종목 상세 화면에서 재무, 투자자 수급, 뉴스, 공시를 탭으로 확인할 수 있습니다. 각 탭은 사용자가 열었을 때만 데이터를 요청하며, 이미 조회한 결과는 짧게 캐시해 불필요한 네트워크 요청과 메모리 사용을 줄입니다.

- 재무: 최근 연간 매출, 영업이익, 순이익, 자산·부채·자본
- 수급: 국내 종목의 외국인·기관·개인 순매매와 합산 흐름
- 뉴스: 최근 기사와 실험 상태의 규칙 기반 감성 요약
- 공시: 최근 90일 공시와 위험 키워드 표시

수급 방향과 뉴스 감성은 매수·매도 지시가 아닌 참고 정보이며, 원문 링크는 안전한 HTTP(S) 주소만 새 창으로 제공합니다.
