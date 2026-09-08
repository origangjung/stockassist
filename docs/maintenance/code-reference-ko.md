# StockPilot AI 한글 코드 사전

> 이 문서는 `scripts/generate_korean_code_reference.py`가 생성합니다.
> 수동으로 수정하지 말고 소스의 한글 docstring/JSDoc을 고친 뒤 다시 생성하세요.

## 읽는 방법

- 클래스는 책임과 포함된 메서드를 함께 표시합니다.
- 메서드와 함수는 시그니처, 원본 줄 번호, 수행 기능을 표시합니다.
- TypeScript 인터페이스는 어느 계층의 계약인지와 주요 필드를 표시합니다.
- `_`로 시작하는 항목도 내부 동작 추적을 위해 포함합니다.

현재 수록 항목: Python 1665개, TypeScript 470개.

## Python 클래스·함수·메서드

### `backend/app/adapters/broker.py`

백엔드 도메인 기능을 구현합니다.

- **클래스 `CapabilityUnavailableError`** · broker.py:11
  - 기능: 해당 실패 조건을 호출 계층에 구분해 전달하는 예외입니다.
- **클래스 `ValidatedCandleBatch`** · broker.py:18
  - 기능: 한 번에 처리할 데이터 묶음과 처리 상태를 전달하는 값 객체입니다.
- **클래스 `BrokerAdapter`** · broker.py:26
  - 기능: 서로 다른 외부 제공자의 기능 차이를 공통 호출 방식으로 맞추는 어댑터입니다.
  - 메서드 `__init__(self, providers: list[StockProvider], *, candle_cache_ttl_seconds: float=15.0)` · broker.py:29
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `provider_for(self, capability: Capability)` · broker.py:41
    - 기능: `provider_for`은(는) 입력 조건을 지원하는 제공자나 처리 대상을 선택해 반환합니다.
  - 메서드 `candles(self, symbol: str, limit: int)` · broker.py:49
    - 기능: `candles`은(는) 이름에 해당하는 시장 또는 기업 데이터를 조회해 공통 형식으로 반환합니다.

### `backend/app/ai_reports/agents.py`

계산된 사실을 리포트로 조합하고 준법 규칙을 검증합니다.

- **클래스 `AgentFinding`** · agents.py:21
  - 기능: 전문 분석 과정에서 확인한 결과와 근거를 묶어 전달합니다.
  - 메서드 `to_dict(self)` · agents.py:30
    - 기능: `to_dict`은(는) 내부 값을 전송·표시 가능한 형식으로 변환합니다.
- **클래스 `AnalysisContext`** · agents.py:37
  - 기능: 여러 처리 단계가 함께 사용하는 실행 문맥과 입력 정보를 묶습니다.
- **클래스 `AnalysisAgent`** · agents.py:48
  - 기능: `AnalysisAgent` 구현체가 제공해야 하는 메서드 계약을 정의합니다.
  - 메서드 `analyze(self, context: AnalysisContext)` · agents.py:54
    - 기능: `analyze`은(는) 해당 작업의 전체 처리 흐름을 실행하고 결과를 반환합니다.
- **클래스 `ScoreAnalysisAgent`** · agents.py:58
  - 기능: `ScoreAnalysisAgent` 관련 상태와 동작을 하나의 객체로 묶습니다.
  - 메서드 `__init__(self, service: ScoreService, market: MarketDataService)` · agents.py:63
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `analyze(self, context: AnalysisContext)` · agents.py:69
    - 기능: `analyze`은(는) 해당 작업의 전체 처리 흐름을 실행하고 결과를 반환합니다.
- **클래스 `ScoreAxisAgent`** · agents.py:99
  - 기능: `ScoreAxisAgent` 관련 상태와 동작을 하나의 객체로 묶습니다.
  - 메서드 `__init__(self, axis: str)` · agents.py:102
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `analyze(self, context: AnalysisContext)` · agents.py:108
    - 기능: `analyze`은(는) 해당 작업의 전체 처리 흐름을 실행하고 결과를 반환합니다.
- **클래스 `PredictionAnalysisAgent`** · agents.py:141
  - 기능: `PredictionAnalysisAgent` 관련 상태와 동작을 하나의 객체로 묶습니다.
  - 메서드 `__init__(self, service: PredictionService)` · agents.py:146
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `analyze(self, context: AnalysisContext)` · agents.py:151
    - 기능: `analyze`은(는) 해당 작업의 전체 처리 흐름을 실행하고 결과를 반환합니다.
- **클래스 `RiskAnalysisAgent`** · agents.py:177
  - 기능: `RiskAnalysisAgent` 관련 상태와 동작을 하나의 객체로 묶습니다.
  - 메서드 `__init__(self, market: MarketDataService)` · agents.py:182
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `analyze(self, context: AnalysisContext)` · agents.py:187
    - 기능: `analyze`은(는) 해당 작업의 전체 처리 흐름을 실행하고 결과를 반환합니다.
- **클래스 `InvestorFlowAnalysisAgent`** · agents.py:206
  - 기능: `InvestorFlowAnalysisAgent` 관련 상태와 동작을 하나의 객체로 묶습니다.
  - 메서드 `__init__(self, service: InvestorFlowService)` · agents.py:211
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `analyze(self, context: AnalysisContext)` · agents.py:216
    - 기능: `analyze`은(는) 해당 작업의 전체 처리 흐름을 실행하고 결과를 반환합니다.
- **클래스 `ChartPatternAnalysisAgent`** · agents.py:240
  - 기능: `ChartPatternAnalysisAgent` 관련 상태와 동작을 하나의 객체로 묶습니다.
  - 메서드 `__init__(self, market: MarketDataService, engine: PatternEngine)` · agents.py:245
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `analyze(self, context: AnalysisContext)` · agents.py:251
    - 기능: `analyze`은(는) 해당 작업의 전체 처리 흐름을 실행하고 결과를 반환합니다.
- **클래스 `SupportResistanceAnalysisAgent`** · agents.py:276
  - 기능: `SupportResistanceAnalysisAgent` 관련 상태와 동작을 하나의 객체로 묶습니다.
  - 메서드 `__init__(self, market: MarketDataService)` · agents.py:281
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `analyze(self, context: AnalysisContext)` · agents.py:286
    - 기능: `analyze`은(는) 해당 작업의 전체 처리 흐름을 실행하고 결과를 반환합니다.
- **클래스 `MasterAnalysisOrchestrator`** · agents.py:316
  - 기능: `MasterAnalysisOrchestrator` 관련 상태와 동작을 하나의 객체로 묶습니다.
  - 메서드 `__init__(self, market: MarketDataService, score: ScoreService, prediction: PredictionService, investor_flow: InvestorFlowService)` · agents.py:321
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `collect(self, symbol: str, *, horizon_days: int, limit: int)` · agents.py:341
    - 기능: `collect`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `_run(agent: AnalysisAgent, context: AnalysisContext, findings: dict[str, dict[str, Any]])` · agents.py:368
    - 기능: `_run`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_mapping(value: Any)`** · agents.py:386
  - 기능: `_mapping`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_provider_name(value: Any)`** · agents.py:396
  - 기능: `_provider_name`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/ai_reports/compliance.py`

계산된 사실을 리포트로 조합하고 준법 규칙을 검증합니다.

- **클래스 `ComplianceValidator`** · compliance.py:21
  - 기능: `ComplianceValidator` 관련 상태와 동작을 하나의 객체로 묶습니다.
  - 메서드 `validate(self, report: dict[str, Any])` · compliance.py:32
    - 기능: `validate`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `_strings(self, value: Any)` · compliance.py:68
    - 기능: `_strings`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/ai_reports/contracts.py`

계산된 사실을 리포트로 조합하고 준법 규칙을 검증합니다.

- **클래스 `AIReportGenerator`** · contracts.py:6
  - 기능: `AIReportGenerator` 구현체가 제공해야 하는 메서드 계약을 정의합니다.
  - 메서드 `generate(self, facts: dict)` · contracts.py:13
    - 기능: `generate`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `close(self)` · contracts.py:15
    - 기능: `close`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/ai_reports/errors.py`

계산된 사실을 리포트로 조합하고 준법 규칙을 검증합니다.

- **클래스 `ReportComplianceError`** · errors.py:6
  - 기능: 해당 실패 조건을 호출 계층에 구분해 전달하는 예외입니다.
- **클래스 `ReportGenerationError`** · errors.py:10
  - 기능: 해당 실패 조건을 호출 계층에 구분해 전달하는 예외입니다.

### `backend/app/ai_reports/factory.py`

계산된 사실을 리포트로 조합하고 준법 규칙을 검증합니다.

- **함수 `build_ai_report_generator(settings: Settings)`** · factory.py:9
  - 기능: `build_ai_report_generator`은(는) 입력 값과 설정을 결합해 새 결과 객체를 생성합니다.

### `backend/app/ai_reports/mock.py`

계산된 사실을 리포트로 조합하고 준법 규칙을 검증합니다.

- **클래스 `MockAIReportGenerator`** · mock.py:6
  - 기능: `MockAIReportGenerator` 관련 상태와 동작을 하나의 객체로 묶습니다.
  - 메서드 `generate(self, facts: dict)` · mock.py:12
    - 기능: `generate`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/ai_reports/openai.py`

계산된 사실을 리포트로 조합하고 준법 규칙을 검증합니다.

- **클래스 `OpenAIReportGenerator`** · openai.py:25
  - 기능: `OpenAIReportGenerator` 관련 상태와 동작을 하나의 객체로 묶습니다.
  - 메서드 `__init__(self, *, api_key: str | None, base_url: str, model: str, timeout_seconds: float, transport: httpx2.BaseTransport | None=None)` · openai.py:30
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `generate(self, facts: dict)` · openai.py:50
    - 기능: `generate`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `close(self)` · openai.py:113
    - 기능: `close`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_output_text(payload: dict[str, Any])`** · openai.py:119
  - 기능: `_output_text`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/ai_reports/signals.py`

계산된 사실을 리포트로 조합하고 준법 규칙을 검증합니다.

- **클래스 `ReferenceSignalResult`** · signals.py:8
  - 기능: 계산 또는 처리 결과를 묶어 전달하는 값 객체입니다.
- **함수 `derive_reference_signal(score: dict | None, prediction: dict | None, warnings: list[dict])`** · signals.py:16
  - 기능: `derive_reference_signal`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_number(source: dict | None, key: str)`** · signals.py:62
  - 기능: `_number`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/alerts/models.py`

백엔드 도메인 기능을 구현합니다.

- **클래스 `WatchlistItem`** · models.py:13
  - 기능: 목록에서 사용하는 한 건의 구조화된 항목을 나타냅니다.
- **클래스 `PriceAlert`** · models.py:24
  - 기능: `PriceAlert` 관련 상태와 동작을 하나의 객체로 묶습니다.

### `backend/app/alerts/repository.py`

백엔드 도메인 기능을 구현합니다.

- **클래스 `AlertRepository`** · repository.py:15
  - 기능: `AlertRepository` 구현체가 제공해야 하는 메서드 계약을 정의합니다.
  - 메서드 `list_watchlist(self)` · repository.py:19
    - 기능: `list_watchlist`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `add_watchlist(self, stock: StockInfo)` · repository.py:22
    - 기능: `add_watchlist`은(는) 데이터를 저장하거나 기존 상태에 추가합니다.
  - 메서드 `remove_watchlist(self, symbol: str)` · repository.py:25
    - 기능: `remove_watchlist`은(는) 대상 데이터나 만료된 상태를 안전하게 제거합니다.
  - 메서드 `list_alerts(self, *, status: str | None=None)` · repository.py:28
    - 기능: `list_alerts`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `create_alert(self, symbol: str, condition: AlertCondition, target_price: Decimal)` · repository.py:31
    - 기능: `create_alert`은(는) 입력 값과 설정을 결합해 새 결과 객체를 생성합니다.
  - 메서드 `disable_alert(self, alert_id: str)` · repository.py:36
    - 기능: `disable_alert`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `record_evaluation(self, alert_id: str, *, price: Decimal, evaluated_at: datetime, triggered: bool)` · repository.py:39
    - 기능: `record_evaluation`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **클래스 `SqlAlchemyAlertRepository`** · repository.py:49
  - 기능: 도메인 객체의 저장·조회 방식을 캡슐화하는 저장소입니다.
  - 메서드 `__init__(self, sessions: sessionmaker[Session])` · repository.py:52
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `list_watchlist(self)` · repository.py:57
    - 기능: `list_watchlist`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `add_watchlist(self, stock: StockInfo)` · repository.py:64
    - 기능: `add_watchlist`은(는) 데이터를 저장하거나 기존 상태에 추가합니다.
  - 메서드 `remove_watchlist(self, symbol: str)` · repository.py:82
    - 기능: `remove_watchlist`은(는) 대상 데이터나 만료된 상태를 안전하게 제거합니다.
  - 메서드 `list_alerts(self, *, status: str | None=None)` · repository.py:89
    - 기능: `list_alerts`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `create_alert(self, symbol: str, condition: AlertCondition, target_price: Decimal)` · repository.py:99
    - 기능: `create_alert`은(는) 입력 값과 설정을 결합해 새 결과 객체를 생성합니다.
  - 메서드 `disable_alert(self, alert_id: str)` · repository.py:114
    - 기능: `disable_alert`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `record_evaluation(self, alert_id: str, *, price: Decimal, evaluated_at: datetime, triggered: bool)` · repository.py:126
    - 기능: `record_evaluation`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `_watchlist_item(model: WatchlistModel)` · repository.py:151
    - 기능: `_watchlist_item`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `_price_alert(model: PriceAlertModel)` · repository.py:163
    - 기능: `_price_alert`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `_utc(value: datetime | None)` · repository.py:179
    - 기능: `_utc`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **클래스 `InMemoryAlertRepository`** · repository.py:189
  - 기능: 도메인 객체의 저장·조회 방식을 캡슐화하는 저장소입니다.
  - 메서드 `__init__(self)` · repository.py:192
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `list_watchlist(self)` · repository.py:198
    - 기능: `list_watchlist`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `add_watchlist(self, stock: StockInfo)` · repository.py:203
    - 기능: `add_watchlist`은(는) 데이터를 저장하거나 기존 상태에 추가합니다.
  - 메서드 `remove_watchlist(self, symbol: str)` · repository.py:218
    - 기능: `remove_watchlist`은(는) 대상 데이터나 만료된 상태를 안전하게 제거합니다.
  - 메서드 `list_alerts(self, *, status: str | None=None)` · repository.py:223
    - 기능: `list_alerts`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `create_alert(self, symbol: str, condition: AlertCondition, target_price: Decimal)` · repository.py:231
    - 기능: `create_alert`은(는) 입력 값과 설정을 결합해 새 결과 객체를 생성합니다.
  - 메서드 `disable_alert(self, alert_id: str)` · repository.py:244
    - 기능: `disable_alert`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `record_evaluation(self, alert_id: str, *, price: Decimal, evaluated_at: datetime, triggered: bool)` · repository.py:253
    - 기능: `record_evaluation`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/api/admin.py`

HTTP 요청·응답 계약과 입력 검증을 담당합니다.

- **함수 `async require_admin_access(request: Request, x_admin_key: str | None=Header(default=None), settings: Settings=Depends(get_settings))`** · admin.py:18
  - 기능: `require_admin_access`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `reset_admin_rate_limiter()`** · admin.py:98
  - 기능: `reset_admin_rate_limiter`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/api/routes.py`

HTTP 요청·응답 계약과 입력 검증을 담당합니다.

- **함수 `get_market_service()`** · routes.py:96
  - 기능: `get_market_service`은(는) 필요한 데이터를 조회해 반환합니다.
- **함수 `get_toss_open_api_service()`** · routes.py:104
  - 기능: 현재 프로세스의 토스 확장 시장 데이터 서비스를 반환한다.
- **함수 `get_technical_service()`** · routes.py:111
  - 기능: `get_technical_service`은(는) 필요한 데이터를 조회해 반환합니다.
- **함수 `get_pattern_service()`** · routes.py:119
  - 기능: `get_pattern_service`은(는) 필요한 데이터를 조회해 반환합니다.
- **함수 `get_backtest_service()`** · routes.py:127
  - 기능: `get_backtest_service`은(는) 필요한 데이터를 조회해 반환합니다.
- **함수 `get_score_service()`** · routes.py:135
  - 기능: `get_score_service`은(는) 필요한 데이터를 조회해 반환합니다.
- **함수 `get_financial_service()`** · routes.py:143
  - 기능: `get_financial_service`은(는) 필요한 데이터를 조회해 반환합니다.
- **함수 `get_valuation_service()`** · routes.py:151
  - 기능: `get_valuation_service`은(는) 필요한 데이터를 조회해 반환합니다.
- **함수 `get_disclosure_service()`** · routes.py:159
  - 기능: `get_disclosure_service`은(는) 필요한 데이터를 조회해 반환합니다.
- **함수 `get_news_service()`** · routes.py:167
  - 기능: `get_news_service`은(는) 필요한 데이터를 조회해 반환합니다.
- **함수 `get_investor_flow_service()`** · routes.py:175
  - 기능: `get_investor_flow_service`은(는) 필요한 데이터를 조회해 반환합니다.
- **함수 `get_prediction_service()`** · routes.py:183
  - 기능: `get_prediction_service`은(는) 필요한 데이터를 조회해 반환합니다.
- **함수 `get_model_registry_service()`** · routes.py:191
  - 기능: `get_model_registry_service`은(는) 필요한 데이터를 조회해 반환합니다.
- **함수 `get_local_ai_readiness_service()`** · routes.py:199
  - 기능: 관리자용 직접 학습 AI 준비도 서비스를 반환한다.
- **함수 `get_ai_report_service()`** · routes.py:207
  - 기능: `get_ai_report_service`은(는) 필요한 데이터를 조회해 반환합니다.
- **함수 `get_portfolio_service()`** · routes.py:215
  - 기능: `get_portfolio_service`은(는) 필요한 데이터를 조회해 반환합니다.
- **함수 `get_paper_trading_service()`** · routes.py:223
  - 기능: 프로세스에서 공유하는 실제 주문과 격리된 모의투자 서비스를 반환한다.
- **함수 `get_reference_alert_service()`** · routes.py:230
  - 기능: `get_reference_alert_service`은(는) 필요한 데이터를 조회해 반환합니다.
- **함수 `get_operations_status_service()`** · routes.py:238
  - 기능: `get_operations_status_service`은(는) 필요한 데이터를 조회해 반환합니다.
- **함수 `get_data_quality_history_service()`** · routes.py:246
  - 기능: `get_data_quality_history_service`은(는) 필요한 데이터를 조회해 반환합니다.
- **함수 `get_candle_price_basis_inventory_service()`** · routes.py:254
  - 기능: `get_candle_price_basis_inventory_service`은(는) 필요한 데이터를 조회해 반환합니다.
- **함수 `get_provider_audit_history_service()`** · routes.py:262
  - 기능: `get_provider_audit_history_service`은(는) 필요한 데이터를 조회해 반환합니다.
- **함수 `get_provider_audit_maintenance_service()`** · routes.py:270
  - 기능: `get_provider_audit_maintenance_service`은(는) 필요한 데이터를 조회해 반환합니다.
- **함수 `get_data_lifecycle_maintenance_service()`** · routes.py:278
  - 기능: `get_data_lifecycle_maintenance_service`은(는) 필요한 데이터를 조회해 반환합니다.
- **함수 `get_corporate_action_service()`** · routes.py:286
  - 기능: `get_corporate_action_service`은(는) 필요한 데이터를 조회해 반환합니다.
- **함수 `get_corporate_action_ingestion_service()`** · routes.py:294
  - 기능: `get_corporate_action_ingestion_service`은(는) 필요한 데이터를 조회해 반환합니다.
- **함수 `get_corporate_action_candidate_service()`** · routes.py:302
  - 기능: `get_corporate_action_candidate_service`은(는) 필요한 데이터를 조회해 반환합니다.
- **함수 `get_corporate_action_approval_service()`** · routes.py:310
  - 기능: `get_corporate_action_approval_service`은(는) 필요한 데이터를 조회해 반환합니다.
- **함수 `get_ingestion_operations_service()`** · routes.py:318
  - 기능: `get_ingestion_operations_service`은(는) 필요한 데이터를 조회해 반환합니다.
- **함수 `get_realtime_hub()`** · routes.py:326
  - 기능: `get_realtime_hub`은(는) 필요한 데이터를 조회해 반환합니다.
- **함수 `envelope(data: dict)`** · routes.py:334
  - 기능: `envelope`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `search_stocks(q: str=Query(min_length=1, max_length=80), limit: int=Query(default=12, ge=1, le=30), service: TossOpenApiService=Depends(get_toss_open_api_service))`** · routes.py:341
  - 기능: 토스 전체 종목 원장에서 티커와 한글·영문 종목명을 검색한다.
- **함수 `get_market_overview(service: TossOpenApiService=Depends(get_toss_open_api_service))`** · routes.py:351
  - 기능: 시장 지표·환율·장 운영·거래대금 상위 종목을 한 번에 조회한다.
- **함수 `get_market_rankings(ranking_type: Literal['MARKET_TRADING_AMOUNT', 'MARKET_TRADING_VOLUME', 'TOP_GAINERS', 'TOP_LOSERS', 'TOSS_SECURITIES_TRADING_AMOUNT', 'TOSS_SECURITIES_TRADING_VOLUME']=Query(alias='type'), market_country: Literal['KR', 'US']=Query(default='KR'), duration: Literal['realtime', '1d', '1w', '1mo', '3mo', '6mo', '1y']=Query(default='1d'), count: int=Query(default=20, ge=1, le=100), service: TossOpenApiService=Depends(get_toss_open_api_service))`** · routes.py:359
  - 기능: 시장·토스 체결 기준의 거래대금·거래량·등락률 랭킹을 조회한다.
- **함수 `get_market_indicator_history(symbol: Literal['KOSPI', 'KOSDAQ', 'KR_BOND_2Y', 'KR_BOND_3Y', 'KR_BOND_5Y', 'KR_BOND_10Y', 'KR_BOND_20Y', 'KR_BOND_30Y'], interval: Literal['1m', '1d']=Query(default='1d'), count: int=Query(default=30, ge=1, le=200), service: TossOpenApiService=Depends(get_toss_open_api_service))`** · routes.py:386
  - 기능: 국내 지수·국채 시계열과 지수 투자자별 매매대금을 조회한다.
- **함수 `get_paper_portfolio(account_id: str=Path(pattern='^[0-9a-f-]{36}$'), service: PaperTradingService=Depends(get_paper_trading_service))`** · routes.py:410
  - 기능: 브라우저 UUID에 대응하는 모의 계좌 평가 결과를 조회한다.
- **함수 `create_paper_order(request: PaperOrderRequest, account_id: str=Path(pattern='^[0-9a-f-]{36}$'), service: PaperTradingService=Depends(get_paper_trading_service))`** · routes.py:419
  - 기능: 현재가 기반 모의 시장가 주문을 원장에 한 번만 체결한다.
- **함수 `reset_paper_portfolio(account_id: str=Path(pattern='^[0-9a-f-]{36}$'), service: PaperTradingService=Depends(get_paper_trading_service))`** · routes.py:440
  - 기능: 실제 계좌에는 영향 없이 해당 모의 계좌만 초기화한다.
- **함수 `get_quote(symbol: str, service: MarketDataService=Depends(get_market_service))`** · routes.py:449
  - 기능: `get_quote`은(는) 필요한 데이터를 조회해 반환합니다.
- **함수 `get_candles(symbol: str, limit: int=Query(default=30, ge=1, le=365), service: MarketDataService=Depends(get_market_service))`** · routes.py:460
  - 기능: `get_candles`은(는) 필요한 데이터를 조회해 반환합니다.
- **함수 `get_processed_candles(symbol: str, interval: CandleInterval=Query(default=CandleInterval.DAY), limit: int=Query(default=90, ge=1, le=365), service: MarketDataService=Depends(get_market_service))`** · routes.py:481
  - 기능: `get_processed_candles`은(는) 필요한 데이터를 조회해 반환합니다.
- **함수 `get_orderbook(symbol: str, service: MarketDataService=Depends(get_market_service))`** · routes.py:507
  - 기능: `get_orderbook`은(는) 필요한 데이터를 조회해 반환합니다.
- **함수 `get_trades(symbol: str, limit: int=Query(default=20, ge=1, le=100), service: MarketDataService=Depends(get_market_service))`** · routes.py:525
  - 기능: `get_trades`은(는) 필요한 데이터를 조회해 반환합니다.
- **함수 `get_stock_info(symbol: str, service: MarketDataService=Depends(get_market_service))`** · routes.py:542
  - 기능: `get_stock_info`은(는) 필요한 데이터를 조회해 반환합니다.
- **함수 `get_indicators(symbol: str, limit: int=Query(default=180, ge=30, le=365), service: TechnicalAnalysisService=Depends(get_technical_service))`** · routes.py:553
  - 기능: `get_indicators`은(는) 필요한 데이터를 조회해 반환합니다.
- **함수 `get_stock_warnings(symbol: str, service: MarketDataService=Depends(get_market_service))`** · routes.py:567
  - 기능: `get_stock_warnings`은(는) 필요한 데이터를 조회해 반환합니다.
- **함수 `get_stock_microstructure(symbol: str=Path(pattern='^[0-9A-Z.-]{1,16}$'), trade_limit: int=Query(default=20, ge=1, le=50), service: TossOpenApiService=Depends(get_toss_open_api_service))`** · routes.py:585
  - 기능: 호가·체결·가격 제한·투자 유의 정보를 한 화면용 응답으로 조립한다.
- **함수 `get_toss_stock_trends(symbol: str=Path(pattern='^[0-9]{6}$'), count: int=Query(default=20, ge=1, le=100), service: TossOpenApiService=Depends(get_toss_open_api_service))`** · routes.py:599
  - 기능: 국내 종목의 투자자·프로그램·공매도·신용·대차 흐름을 조회한다.
- **함수 `get_patterns(symbol: str, limit: int=Query(default=180, ge=21, le=365), service: PatternAnalysisService=Depends(get_pattern_service))`** · routes.py:609
  - 기능: `get_patterns`은(는) 필요한 데이터를 조회해 반환합니다.
- **함수 `get_financials(symbol: str, fiscal_year: int=Query(default=2025, ge=2015, le=2100), report_code: str=Query(default='11011', pattern='^1101[1-4]$'), service: FinancialAnalysisService=Depends(get_financial_service))`** · routes.py:623
  - 기능: `get_financials`은(는) 필요한 데이터를 조회해 반환합니다.
- **함수 `get_valuation(symbol: str, fiscal_year: int=Query(default=2025, ge=2015, le=2100), report_code: str=Query(default='11011', pattern='^1101[1-4]$'), service: ValuationAnalysisService=Depends(get_valuation_service))`** · routes.py:635
  - 기능: `get_valuation`은(는) 필요한 데이터를 조회해 반환합니다.
- **함수 `get_disclosures(symbol: str, days: int=Query(default=90, ge=1, le=365), limit: int=Query(default=20, ge=1, le=100), service: DisclosureAnalysisService=Depends(get_disclosure_service))`** · routes.py:647
  - 기능: `get_disclosures`은(는) 필요한 데이터를 조회해 반환합니다.
- **함수 `get_news(symbol: str, limit: int=Query(default=20, ge=1, le=100), service: NewsAnalysisService=Depends(get_news_service))`** · routes.py:659
  - 기능: `get_news`은(는) 필요한 데이터를 조회해 반환합니다.
- **함수 `get_investor_flow(symbol: str, service: InvestorFlowService=Depends(get_investor_flow_service))`** · routes.py:670
  - 기능: `get_investor_flow`은(는) 필요한 데이터를 조회해 반환합니다.
- **함수 `get_prediction(symbol: str, horizon_days: int=Query(default=5, ge=1, le=30), limit: int=Query(default=180, ge=80, le=365), service: PredictionService=Depends(get_prediction_service))`** · routes.py:680
  - 기능: `get_prediction`은(는) 필요한 데이터를 조회해 반환합니다.
- **함수 `get_ai_report(symbol: str, horizon_days: int=Query(default=5, ge=1, le=30), limit: int=Query(default=180, ge=80, le=365), service: AIReportService=Depends(get_ai_report_service))`** · routes.py:692
  - 기능: `get_ai_report`은(는) 필요한 데이터를 조회해 반환합니다.
- **함수 `get_broker_accounts(service: PortfolioService=Depends(get_portfolio_service))`** · routes.py:709
  - 기능: `get_broker_accounts`은(는) 필요한 데이터를 조회해 반환합니다.
- **함수 `get_realtime_status(hub=Depends(get_realtime_hub))`** · routes.py:716
  - 기능: `get_realtime_status`은(는) 필요한 데이터를 조회해 반환합니다.
- **함수 `sync_portfolio(account_seq: int, service: PortfolioService=Depends(get_portfolio_service))`** · routes.py:734
  - 기능: `sync_portfolio`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `get_toss_account_workspace(account_seq: int=Path(gt=0), symbol: str | None=Query(default=None, pattern='^[0-9A-Z.-]{1,16}$'), currency: str=Query(default='KRW', pattern='^(KRW|USD)$'), service: TossOpenApiService=Depends(get_toss_open_api_service))`** · routes.py:749
  - 기능: 보유 자산·주문 내역·주문 가능 정보가 포함된 읽기 전용 작업 공간을 반환한다.
- **함수 `get_toss_order_detail(account_seq: int=Path(gt=0), order_id: str=Path(pattern='^[a-zA-Z0-9_-]{1,128}$'), service: TossOpenApiService=Depends(get_toss_open_api_service))`** · routes.py:765
  - 기능: 실제 주문 상세와 부분 체결 상태를 읽기 전용으로 조회한다.
- **함수 `get_toss_conditional_order_detail(account_seq: int=Path(gt=0), conditional_order_id: str=Path(pattern='^[a-zA-Z0-9_-]{1,128}$'), service: TossOpenApiService=Depends(get_toss_open_api_service))`** · routes.py:780
  - 기능: 실제 조건주문의 감시·실행 상태를 읽기 전용으로 조회한다.
- **함수 `create_toss_order(request: TossOrderCreateRequest, account_seq: int=Path(gt=0), service: TossOpenApiService=Depends(get_toss_open_api_service))`** · routes.py:795
  - 기능: `create_toss_order`은(는) 입력 값과 설정을 결합해 새 결과 객체를 생성합니다.
- **함수 `modify_toss_order(request: TossOrderModifyRequest, account_seq: int=Path(gt=0), order_id: str=Path(pattern='^[a-zA-Z0-9_-]{1,128}$'), service: TossOpenApiService=Depends(get_toss_open_api_service))`** · routes.py:816
  - 기능: `modify_toss_order`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `cancel_toss_order(request: TossMutationConfirmation, account_seq: int=Path(gt=0), order_id: str=Path(pattern='^[a-zA-Z0-9_-]{1,128}$'), service: TossOpenApiService=Depends(get_toss_open_api_service))`** · routes.py:840
  - 기능: `cancel_toss_order`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `create_toss_conditional_order(request: TossConditionalOrderRequest, account_seq: int=Path(gt=0), service: TossOpenApiService=Depends(get_toss_open_api_service))`** · routes.py:859
  - 기능: `create_toss_conditional_order`은(는) 입력 값과 설정을 결합해 새 결과 객체를 생성합니다.
- **함수 `modify_toss_conditional_order(request: TossConditionalOrderRequest, account_seq: int=Path(gt=0), conditional_order_id: str=Path(pattern='^[a-zA-Z0-9_-]{1,128}$'), service: TossOpenApiService=Depends(get_toss_open_api_service))`** · routes.py:884
  - 기능: `modify_toss_conditional_order`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `cancel_toss_conditional_order(request: TossMutationConfirmation, account_seq: int=Path(gt=0), conditional_order_id: str=Path(pattern='^[a-zA-Z0-9_-]{1,128}$'), service: TossOpenApiService=Depends(get_toss_open_api_service))`** · routes.py:914
  - 기능: `cancel_toss_conditional_order`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `run_backtest(request: BacktestRequest, service: BacktestService=Depends(get_backtest_service))`** · routes.py:932
  - 기능: `run_backtest`은(는) 해당 작업의 전체 처리 흐름을 실행하고 결과를 반환합니다.
- **함수 `validate_backtest_walk_forward(request: BacktestValidationRequest, service: BacktestService=Depends(get_backtest_service))`** · routes.py:969
  - 기능: `validate_backtest_walk_forward`은(는) 입력 또는 현재 상태가 규칙을 만족하는지 검증합니다.
- **함수 `async get_operations_status(service: OperationsStatusService=Depends(get_operations_status_service))`** · routes.py:1010
  - 기능: `get_operations_status`은(는) 비동기로 필요한 데이터를 조회해 반환합니다.
- **함수 `get_data_quality_history(limit: int=Query(default=50, ge=1, le=200), offset: int=Query(default=0, ge=0), symbol: str | None=Query(default=None, pattern='^[0-9A-Z.-]{1,16}$'), severity: str | None=Query(default=None, pattern='^(error|warning)$'), service: DataQualityHistoryService=Depends(get_data_quality_history_service))`** · routes.py:1024
  - 기능: `get_data_quality_history`은(는) 필요한 데이터를 조회해 반환합니다.
- **함수 `get_candle_price_basis_inventory(symbol: str=Query(pattern='^[0-9A-Z.-]{1,16}$'), limit: int=Query(default=200, ge=1, le=500), service: CandlePriceBasisInventoryService=Depends(get_candle_price_basis_inventory_service))`** · routes.py:1049
  - 기능: `get_candle_price_basis_inventory`은(는) 필요한 데이터를 조회해 반환합니다.
- **함수 `get_ingestion_status(service: IngestionOperationsService=Depends(get_ingestion_operations_service))`** · routes.py:1065
  - 기능: `get_ingestion_status`은(는) 필요한 데이터를 조회해 반환합니다.
- **함수 `get_provider_audit_history(limit: int=Query(default=50, ge=1, le=200), offset: int=Query(default=0, ge=0), provider: str | None=Query(default=None, pattern='^[a-z0-9_-]{1,32}$'), outcome: str | None=Query(default=None, pattern='^(success|error|transport_error)$'), service: ProviderAuditHistoryService=Depends(get_provider_audit_history_service))`** · routes.py:1079
  - 기능: `get_provider_audit_history`은(는) 필요한 데이터를 조회해 반환합니다.
- **함수 `cleanup_provider_audit_history(service: ProviderAuditMaintenanceService=Depends(get_provider_audit_maintenance_service))`** · routes.py:1104
  - 기능: `cleanup_provider_audit_history`은(는) 대상 데이터나 만료된 상태를 안전하게 제거합니다.
- **함수 `preview_data_lifecycle_cleanup(service: DataLifecycleMaintenanceService=Depends(get_data_lifecycle_maintenance_service))`** · routes.py:1118
  - 기능: `preview_data_lifecycle_cleanup`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `cleanup_expired_operational_data(service: DataLifecycleMaintenanceService=Depends(get_data_lifecycle_maintenance_service))`** · routes.py:1132
  - 기능: `cleanup_expired_operational_data`은(는) 대상 데이터나 만료된 상태를 안전하게 제거합니다.
- **함수 `get_corporate_action_history(limit: int=Query(default=50, ge=1, le=200), offset: int=Query(default=0, ge=0), symbol: str | None=Query(default=None, pattern='^[0-9A-Z.-]{1,16}$'), as_of: datetime | None=Query(default=None), service: CorporateActionService=Depends(get_corporate_action_service))`** · routes.py:1146
  - 기능: `get_corporate_action_history`은(는) 필요한 데이터를 조회해 반환합니다.
- **함수 `get_corporate_action_ingestion_status(service: CorporateActionIngestionService=Depends(get_corporate_action_ingestion_service))`** · routes.py:1174
  - 기능: `get_corporate_action_ingestion_status`은(는) 필요한 데이터를 조회해 반환합니다.
- **함수 `get_corporate_action_candidate_status(service: CorporateActionCandidateService=Depends(get_corporate_action_candidate_service))`** · routes.py:1188
  - 기능: `get_corporate_action_candidate_status`은(는) 필요한 데이터를 조회해 반환합니다.
- **함수 `preview_corporate_action_candidates(source: str=Path(pattern='^[a-z0-9_-]{1,32}$'), symbol: str=Path(pattern='^[0-9A-Z.-]{1,16}$'), start: date=Query(), end: date=Query(), limit: int=Query(default=100, ge=1, le=200), service: CorporateActionCandidateService=Depends(get_corporate_action_candidate_service))`** · routes.py:1202
  - 기능: `preview_corporate_action_candidates`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `get_corporate_action_approval_status(service: CorporateActionApprovalService=Depends(get_corporate_action_approval_service))`** · routes.py:1234
  - 기능: `get_corporate_action_approval_status`은(는) 필요한 데이터를 조회해 반환합니다.
- **함수 `approve_corporate_action_candidate(request: CorporateActionApprovalRequest, source: str=Path(pattern='^[a-z0-9_-]{1,32}$'), symbol: str=Path(pattern='^[0-9A-Z.-]{1,16}$'), service: CorporateActionApprovalService=Depends(get_corporate_action_approval_service))`** · routes.py:1248
  - 기능: `approve_corporate_action_candidate`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `trigger_corporate_action_ingestion(source: str=Path(pattern='^[a-z0-9_-]{1,32}$'), symbol: str=Path(pattern='^[0-9A-Z.-]{1,16}$'), start: datetime=Query(), end: datetime=Query(), limit: int=Query(default=200, ge=1, le=500), service: CorporateActionIngestionService=Depends(get_corporate_action_ingestion_service))`** · routes.py:1286
  - 기능: `trigger_corporate_action_ingestion`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `trigger_candle_ingestion(symbol: str=Path(pattern='^[0-9A-Z.-]{1,16}$'), limit: int | None=Query(default=None, ge=30, le=365), service: IngestionOperationsService=Depends(get_ingestion_operations_service))`** · routes.py:1325
  - 기능: `trigger_candle_ingestion`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `get_backtest_history(limit: int=Query(default=25, ge=1, le=100), offset: int=Query(default=0, ge=0), symbol: str | None=Query(default=None, pattern='^[0-9A-Z]{1,16}$'), service: BacktestService=Depends(get_backtest_service))`** · routes.py:1346
  - 기능: `get_backtest_history`은(는) 필요한 데이터를 조회해 반환합니다.
- **함수 `compare_backtest_engines(request: BacktestComparisonRequest, service: BacktestService=Depends(get_backtest_service))`** · routes.py:1363
  - 기능: `compare_backtest_engines`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `compare_backtest_strategies(request: BacktestStrategyComparisonRequest, service: BacktestService=Depends(get_backtest_service))`** · routes.py:1401
  - 기능: `compare_backtest_strategies`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `get_backtest_history_detail(run_id: str, service: BacktestService=Depends(get_backtest_service))`** · routes.py:1439
  - 기능: `get_backtest_history_detail`은(는) 필요한 데이터를 조회해 반환합니다.
- **함수 `get_model_versions(limit: int=Query(default=25, ge=1, le=100), offset: int=Query(default=0, ge=0), symbol: str | None=Query(default=None, pattern='^[0-9A-Z.-]{1,16}$'), algorithm: str | None=Query(default=None, pattern='^[a-z0-9_-]{1,32}$'), horizon_days: int | None=Query(default=None, ge=1, le=30), service: ModelRegistryService=Depends(get_model_registry_service))`** · routes.py:1459
  - 기능: `get_model_versions`은(는) 필요한 데이터를 조회해 반환합니다.
- **함수 `promote_model_version(version: str=Path(pattern='^[a-z0-9-]{1,64}$'), service: ModelRegistryService=Depends(get_model_registry_service))`** · routes.py:1486
  - 기능: `promote_model_version`은(는) 기존 상태를 검증된 새 값으로 변경합니다.
- **함수 `get_local_ai_readiness(service: LocalAiReadinessService=Depends(get_local_ai_readiness_service))`** · routes.py:1508
  - 기능: 직접 학습 AI의 artifact 무결성과 품질 게이트 상태를 조회한다.
- **함수 `get_watchlist(service: ReferenceAlertService=Depends(get_reference_alert_service))`** · routes.py:1522
  - 기능: `get_watchlist`은(는) 필요한 데이터를 조회해 반환합니다.
- **함수 `add_watchlist_item(request: WatchlistCreateRequest, service: ReferenceAlertService=Depends(get_reference_alert_service))`** · routes.py:1536
  - 기능: `add_watchlist_item`은(는) 데이터를 저장하거나 기존 상태에 추가합니다.
- **함수 `remove_watchlist_item(symbol: str, service: ReferenceAlertService=Depends(get_reference_alert_service))`** · routes.py:1556
  - 기능: `remove_watchlist_item`은(는) 대상 데이터나 만료된 상태를 안전하게 제거합니다.
- **함수 `get_reference_alerts(status: str | None=Query(default=None, pattern='^(active|triggered|disabled)$'), service: ReferenceAlertService=Depends(get_reference_alert_service))`** · routes.py:1574
  - 기능: `get_reference_alerts`은(는) 필요한 데이터를 조회해 반환합니다.
- **함수 `create_reference_alert(request: PriceAlertCreateRequest, service: ReferenceAlertService=Depends(get_reference_alert_service))`** · routes.py:1589
  - 기능: `create_reference_alert`은(는) 입력 값과 설정을 결합해 새 결과 객체를 생성합니다.
- **함수 `evaluate_reference_alerts(service: ReferenceAlertService=Depends(get_reference_alert_service))`** · routes.py:1615
  - 기능: `evaluate_reference_alerts`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `disable_reference_alert(alert_id: str, service: ReferenceAlertService=Depends(get_reference_alert_service))`** · routes.py:1632
  - 기능: `disable_reference_alert`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `get_score(symbol: str, limit: int=Query(default=180, ge=30, le=365), service: ScoreService=Depends(get_score_service))`** · routes.py:1645
  - 기능: `get_score`은(는) 필요한 데이터를 조회해 반환합니다.

### `backend/app/api/schemas.py`

HTTP 요청·응답 계약과 입력 검증을 담당합니다.

- **클래스 `QuoteResponse`** · schemas.py:10
  - 기능: API 응답으로 전달하는 필드 계약을 정의합니다.
- **클래스 `CandleResponse`** · schemas.py:23
  - 기능: API 응답으로 전달하는 필드 계약을 정의합니다.
- **클래스 `OrderbookLevelResponse`** · schemas.py:34
  - 기능: API 응답으로 전달하는 필드 계약을 정의합니다.
- **클래스 `OrderbookResponse`** · schemas.py:41
  - 기능: API 응답으로 전달하는 필드 계약을 정의합니다.
- **클래스 `ApiEnvelope`** · schemas.py:50
  - 기능: `ApiEnvelope` 관련 상태와 동작을 하나의 객체로 묶습니다.
- **클래스 `CandleQuery`** · schemas.py:61
  - 기능: `CandleQuery` 관련 상태와 동작을 하나의 객체로 묶습니다.
- **클래스 `BacktestRequest`** · schemas.py:67
  - 기능: API 요청 본문의 필드와 검증 규칙을 정의합니다.
- **클래스 `BacktestValidationRequest`** · schemas.py:87
  - 기능: API 요청 본문의 필드와 검증 규칙을 정의합니다.
- **클래스 `BacktestComparisonRequest`** · schemas.py:94
  - 기능: API 요청 본문의 필드와 검증 규칙을 정의합니다.
- **클래스 `BacktestStrategyComparisonRequest`** · schemas.py:113
  - 기능: API 요청 본문의 필드와 검증 규칙을 정의합니다.
- **클래스 `WatchlistCreateRequest`** · schemas.py:129
  - 기능: API 요청 본문의 필드와 검증 규칙을 정의합니다.
- **클래스 `PaperOrderRequest`** · schemas.py:135
  - 기능: 모의 시장가 주문 입력값이며 실제 주문 옵션은 의도적으로 제공하지 않는다.
- **클래스 `PriceAlertCreateRequest`** · schemas.py:144
  - 기능: API 요청 본문의 필드와 검증 규칙을 정의합니다.
- **클래스 `CorporateActionApprovalRequest`** · schemas.py:152
  - 기능: API 요청 본문의 필드와 검증 규칙을 정의합니다.
- **클래스 `TossOrderCreateRequest`** · schemas.py:164
  - 기능: 토스 실제 주문 생성값과 사용자의 명시적 확인 문구다.
  - 메서드 `validate_order_shape(self)` · schemas.py:181
    - 기능: `validate_order_shape`은(는) 입력 또는 현재 상태가 규칙을 만족하는지 검증합니다.
- **클래스 `TossOrderModifyRequest`** · schemas.py:193
  - 기능: API 요청 본문의 필드와 검증 규칙을 정의합니다.
- **클래스 `TossMutationConfirmation`** · schemas.py:203
  - 기능: `TossMutationConfirmation` 관련 상태와 동작을 하나의 객체로 묶습니다.
- **클래스 `TossConditionRequest`** · schemas.py:209
  - 기능: API 요청 본문의 필드와 검증 규칙을 정의합니다.
- **클래스 `TossConditionalOrderRequest`** · schemas.py:219
  - 기능: API 요청 본문의 필드와 검증 규칙을 정의합니다.
  - 메서드 `validate_conditions(self)` · schemas.py:236
    - 기능: `validate_conditions`은(는) 입력 또는 현재 상태가 규칙을 만족하는지 검증합니다.

### `backend/app/backtest/engine.py`

전략 백테스트와 성과 평가를 담당합니다.

- **클래스 `BacktestEngine`** · engine.py:16
  - 기능: 입력 데이터로부터 결정론적 결과를 계산하는 엔진입니다.
  - 메서드 `run(self, candles: list[Candle], strategy: Strategy, config: BacktestConfig | None=None)` · engine.py:22
    - 기능: `run`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `_trades(frame: pd.DataFrame, position: pd.Series, previous_position: pd.Series, previous_equity: pd.Series, config: BacktestConfig)` · engine.py:102
    - 기능: `_trades`은(는) 이름에 해당하는 시장 또는 기업 데이터를 조회해 공통 형식으로 반환합니다.

### `backend/app/backtest/event_engine.py`

전략 백테스트와 성과 평가를 담당합니다.

- **클래스 `_PendingOrder`** · event_engine.py:24
  - 기능: `_PendingOrder` 관련 상태와 동작을 하나의 객체로 묶습니다.
- **클래스 `EventDrivenBacktestEngine`** · event_engine.py:32
  - 기능: 입력 데이터로부터 결정론적 결과를 계산하는 엔진입니다.
  - 메서드 `run(self, candles: list[Candle], strategy: Strategy, config: BacktestConfig | None=None)` · event_engine.py:38
    - 기능: `run`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `_execute(side: str, timestamp: datetime, market_price: float, market_volume: int | None, cash: float, quantity: int, config: BacktestConfig, trades: list[Trade], events: list[BacktestEvent], *, reason: str, bypass_volume_limit: bool=False)` · event_engine.py:198
    - 기능: `_execute`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `_bounded_quantity(requested_quantity: int, market_volume: int | None, max_volume_participation: float, bypass_volume_limit: bool)` · event_engine.py:352
    - 기능: `_bounded_quantity`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/backtest/metrics.py`

전략 백테스트와 성과 평가를 담당합니다.

- **함수 `calculate_metrics(equity: pd.Series, returns: pd.Series, trades: list[Trade], observation_count: int, config: BacktestConfig)`** · metrics.py:10
  - 기능: `calculate_metrics`은(는) 입력 데이터를 기준으로 모델 또는 규칙의 결과 값을 계산해 반환합니다.

### `backend/app/backtest/models.py`

전략 백테스트와 성과 평가를 담당합니다.

- **클래스 `CostModel`** · models.py:8
  - 기능: 데이터베이스에 저장되는 필드와 관계를 정의하는 ORM 모델입니다.
  - 메서드 `__post_init__(self)` · models.py:15
    - 기능: `__post_init__`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **클래스 `BacktestConfig`** · models.py:24
  - 기능: 실행 또는 계산에 필요한 설정 값을 묶는 객체입니다.
  - 메서드 `__post_init__(self)` · models.py:33
    - 기능: `__post_init__`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **클래스 `Trade`** · models.py:45
  - 기능: `Trade` 관련 상태와 동작을 하나의 객체로 묶습니다.
- **클래스 `BacktestEvent`** · models.py:58
  - 기능: `BacktestEvent` 관련 상태와 동작을 하나의 객체로 묶습니다.
- **클래스 `EquityPoint`** · models.py:67
  - 기능: 시계열 또는 차트에서 사용하는 한 시점의 값을 나타냅니다.
- **클래스 `PerformanceMetrics`** · models.py:77
  - 기능: `PerformanceMetrics` 관련 상태와 동작을 하나의 객체로 묶습니다.
- **클래스 `BacktestResult`** · models.py:90
  - 기능: 계산 또는 처리 결과를 묶어 전달하는 값 객체입니다.
- **클래스 `BacktestRunSummary`** · models.py:103
  - 기능: `BacktestRunSummary` 관련 상태와 동작을 하나의 객체로 묶습니다.
- **클래스 `BacktestRunDetail`** · models.py:118
  - 기능: `BacktestRunDetail` 관련 상태와 동작을 하나의 객체로 묶습니다.

### `backend/app/backtest/strategies.py`

전략 백테스트와 성과 평가를 담당합니다.

- **클래스 `Strategy`** · strategies.py:13
  - 기능: `Strategy` 구현체가 제공해야 하는 메서드 계약을 정의합니다.
  - 메서드 `signals(self, candles: pd.DataFrame)` · strategies.py:19
    - 기능: `signals`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **클래스 `BuyAndHoldStrategy`** · strategies.py:23
  - 기능: `BuyAndHoldStrategy` 관련 상태와 동작을 하나의 객체로 묶습니다.
  - 메서드 `signals(self, candles: pd.DataFrame)` · strategies.py:28
    - 기능: `signals`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **클래스 `MovingAverageCrossStrategy`** · strategies.py:34
  - 기능: `MovingAverageCrossStrategy` 관련 상태와 동작을 하나의 객체로 묶습니다.
  - 메서드 `__init__(self, fast_period: int=5, slow_period: int=20)` · strategies.py:37
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `signals(self, candles: pd.DataFrame)` · strategies.py:46
    - 기능: `signals`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **클래스 `PatternReferenceStrategy`** · strategies.py:54
  - 기능: `PatternReferenceStrategy` 관련 상태와 동작을 하나의 객체로 묶습니다.
  - 메서드 `__init__(self, minimum_confidence: float=0.68, window: int=60)` · strategies.py:59
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `signals(self, candles: pd.DataFrame)` · strategies.py:72
    - 기능: `signals`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `_signature(row: Any)` · strategies.py:104
    - 기능: `_signature`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `_to_candles(frame: pd.DataFrame)` · strategies.py:117
    - 기능: `_to_candles`은(는) 내부 값을 전송·표시 가능한 형식으로 변환합니다.

### `backend/app/backtest/validation.py`

전략 백테스트와 성과 평가를 담당합니다.

- **클래스 `_ActivationStrategy`** · validation.py:20
  - 기능: `_ActivationStrategy` 관련 상태와 동작을 하나의 객체로 묶습니다.
  - 메서드 `__init__(self, delegate: Strategy, activation_index: int)` · validation.py:23
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `signals(self, candles: pd.DataFrame)` · validation.py:30
    - 기능: `signals`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **클래스 `WalkForwardBacktestValidator`** · validation.py:38
  - 기능: `WalkForwardBacktestValidator` 관련 상태와 동작을 하나의 객체로 묶습니다.
  - 메서드 `run(self, candles: list[Candle], *, strategy_factory: Callable[[], Strategy], engine: BacktestEngine | EventDrivenBacktestEngine, config: BacktestConfig, n_splits: int=3, warmup_candles: int=60)` · validation.py:44
    - 기능: `run`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `_stability(returns: list[float])` · validation.py:143
    - 기능: `_stability`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/config/settings.py`

백엔드 도메인 기능을 구현합니다.

- **클래스 `Settings`** · settings.py:11
  - 기능: `Settings` 관련 상태와 동작을 하나의 객체로 묶습니다.
  - 메서드 `validate_feature_dependencies(self)` · settings.py:120
    - 기능: `validate_feature_dependencies`은(는) 입력 또는 현재 상태가 규칙을 만족하는지 검증합니다.
  - 메서드 `_active_http_provider_urls(self)` · settings.py:231
    - 기능: `_active_http_provider_urls`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `allowed_origins(self)` · settings.py:266
    - 기능: `allowed_origins`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `trusted_hosts(self)` · settings.py:274
    - 기능: `trusted_hosts`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `scheduled_symbols(self)` · settings.py:282
    - 기능: `scheduled_symbols`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `data_retention_days(self)` · settings.py:294
    - 기능: `data_retention_days`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `get_settings()`** · settings.py:305
  - 기능: `get_settings`은(는) 필요한 데이터를 조회해 반환합니다.

### `backend/app/core/analysis_access.py`

보안·오류·요청 문맥 같은 공통 기반 기능을 담당합니다.

- **클래스 `AnalysisAccessMiddleware`** · analysis_access.py:29
  - 기능: 요청과 응답 사이에서 공통 정책을 적용하는 미들웨어입니다.
  - 메서드 `__init__(self, app, *, api_key: str | None)` · analysis_access.py:32
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `async dispatch(self, request: Request, call_next)` · analysis_access.py:38
    - 기능: `dispatch`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `is_protected_analysis_request(request: Request)`** · analysis_access.py:68
  - 기능: `is_protected_analysis_request`은(는) 입력 또는 현재 상태가 규칙을 만족하는지 검증합니다.

### `backend/app/core/compliance.py`

보안·오류·요청 문맥 같은 공통 기반 기능을 담당합니다.

- **함수 `compliance_metadata()`** · compliance.py:13
  - 기능: `compliance_metadata`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/core/errors.py`

보안·오류·요청 문맥 같은 공통 기반 기능을 담당합니다.

- **함수 `_error_response(request: Request, status_code: int, code: str, message: str, data=None)`** · errors.py:23
  - 기능: `_error_response`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `async http_exception_handler(request: Request, exc: HTTPException)`** · errors.py:44
  - 기능: `http_exception_handler`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `async validation_exception_handler(request: Request, exc: RequestValidationError)`** · errors.py:62
  - 기능: `validation_exception_handler`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `async provider_exception_handler(request: Request, exc: ProviderError)`** · errors.py:76
  - 기능: `provider_exception_handler`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `async unhandled_exception_handler(request: Request, exc: Exception)`** · errors.py:102
  - 기능: `unhandled_exception_handler`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/core/rate_limit.py`

보안·오류·요청 문맥 같은 공통 기반 기능을 담당합니다.

- **함수 `client_ip_key(request: Request, *, trust_proxy_headers: bool)`** · rate_limit.py:33
  - 기능: `client_ip_key`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **클래스 `SlidingWindowLimiter`** · rate_limit.py:93
  - 기능: `SlidingWindowLimiter` 관련 상태와 동작을 하나의 객체로 묶습니다.
  - 메서드 `__init__(self, *, max_keys: int=10000, clock: Callable[[], float]=monotonic)` · rate_limit.py:96
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `consume(self, key: str, *, limit: int, window: int)` · rate_limit.py:112
    - 기능: `consume`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `is_limited(self, key: str, *, limit: int, window: int)` · rate_limit.py:138
    - 기능: `is_limited`은(는) 입력 또는 현재 상태가 규칙을 만족하는지 검증합니다.
  - 메서드 `clear(self, key: str | None=None)` · rate_limit.py:153
    - 기능: `clear`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `key_count(self)` · rate_limit.py:163
    - 기능: `key_count`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `_prune(requests: deque[float], cutoff: float)` · rate_limit.py:170
    - 기능: `_prune`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `_sweep(self, cutoff: float)` · rate_limit.py:176
    - 기능: `_sweep`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **클래스 `RedisSlidingWindowLimiter`** · rate_limit.py:185
  - 기능: `RedisSlidingWindowLimiter` 관련 상태와 동작을 하나의 객체로 묶습니다.
  - 메서드 `__init__(self, redis_url: str | None=None, *, client: Redis | None=None, clock: Callable[[], float]=time)` · rate_limit.py:188
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `async consume(self, key: str, *, limit: int, window: int)` · rate_limit.py:202
    - 기능: `consume`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `async is_limited(self, key: str, *, limit: int, window: int)` · rate_limit.py:219
    - 기능: `is_limited`은(는) 비동기로 입력 또는 현재 상태가 규칙을 만족하는지 검증합니다.
  - 메서드 `async clear(self, key: str)` · rate_limit.py:234
    - 기능: `clear`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `async aclose(self)` · rate_limit.py:239
    - 기능: `aclose`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `_key(key: str)` · rate_limit.py:245
    - 기능: `_key`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **클래스 `RateLimitMiddleware`** · rate_limit.py:252
  - 기능: 요청과 응답 사이에서 공통 정책을 적용하는 미들웨어입니다.
  - 메서드 `__init__(self, app, *, enabled: bool, window_seconds: int, request_limit: int, expensive_request_limit: int, trust_proxy_headers: bool, backend: str='memory', redis_url: str | None=None, distributed_limiter: RedisSlidingWindowLimiter | None=None)` · rate_limit.py:255
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `async dispatch(self, request: Request, call_next)` · rate_limit.py:287
    - 기능: `dispatch`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `_client_key(self, request: Request)` · rate_limit.py:334
    - 기능: `_client_key`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `_error_response(request: Request, *, status_code: int, code: str, message: str, headers: dict[str, str])` · rate_limit.py:340
    - 기능: `_error_response`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_is_expensive(request: Request)`** · rate_limit.py:365
  - 기능: `_is_expensive`은(는) 입력 또는 현재 상태가 규칙을 만족하는지 검증합니다.

### `backend/app/core/request_context.py`

보안·오류·요청 문맥 같은 공통 기반 기능을 담당합니다.

- **함수 `current_request_id()`** · request_context.py:18
  - 기능: `current_request_id`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **클래스 `RequestIdMiddleware`** · request_context.py:25
  - 기능: 요청과 응답 사이에서 공통 정책을 적용하는 미들웨어입니다.
  - 메서드 `async dispatch(self, request: Request, call_next)` · request_context.py:28
    - 기능: `dispatch`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/core/sanitization.py`

보안·오류·요청 문맥 같은 공통 기반 기능을 담당합니다.

- **함수 `public_provider_error_code(value: object, *, fallback: str='provider-error')`** · sanitization.py:21
  - 기능: `public_provider_error_code`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `sanitize_external_text(value: object, *, maximum: int=500)`** · sanitization.py:32
  - 기능: `sanitize_external_text`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `sanitize_external_data(value: Any, *, depth: int=0)`** · sanitization.py:40
  - 기능: `sanitize_external_data`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `public_provider_error_message(exc: Exception)`** · sanitization.py:71
  - 기능: `public_provider_error_message`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/core/security.py`

보안·오류·요청 문맥 같은 공통 기반 기능을 담당합니다.

- **클래스 `SecurityHeadersMiddleware`** · security.py:13
  - 기능: 요청과 응답 사이에서 공통 정책을 적용하는 미들웨어입니다.
  - 메서드 `async dispatch(self, request: Request, call_next)` · security.py:16
    - 기능: `dispatch`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/corporate_actions/approval_contracts.py`

백엔드 도메인 기능을 구현합니다.

- **클래스 `CorporateActionApprovalUnavailableError`** · approval_contracts.py:10
  - 기능: 해당 실패 조건을 호출 계층에 구분해 전달하는 예외입니다.
- **클래스 `CorporateActionApprovalConflictError`** · approval_contracts.py:16
  - 기능: 해당 실패 조건을 호출 계층에 구분해 전달하는 예외입니다.
- **클래스 `CorporateActionApprovalEvidence`** · approval_contracts.py:23
  - 기능: `CorporateActionApprovalEvidence` 관련 상태와 동작을 하나의 객체로 묶습니다.
- **클래스 `CorporateActionApprovalResult`** · approval_contracts.py:35
  - 기능: 계산 또는 처리 결과를 묶어 전달하는 값 객체입니다.
- **클래스 `CorporateActionApprovalRepository`** · approval_contracts.py:43
  - 기능: `CorporateActionApprovalRepository` 구현체가 제공해야 하는 메서드 계약을 정의합니다.
  - 메서드 `approve(self, action: CorporateActionRecord, evidence: CorporateActionApprovalEvidence)` · approval_contracts.py:46
    - 기능: `approve`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/corporate_actions/candidate_contracts.py`

백엔드 도메인 기능을 구현합니다.

- **클래스 `CorporateActionCandidate`** · candidate_contracts.py:12
  - 기능: `CorporateActionCandidate` 관련 상태와 동작을 하나의 객체로 묶습니다.
- **클래스 `CorporateActionCandidateFetchResult`** · candidate_contracts.py:35
  - 기능: 계산 또는 처리 결과를 묶어 전달하는 값 객체입니다.
- **클래스 `CorporateActionCandidateProvider`** · candidate_contracts.py:44
  - 기능: `CorporateActionCandidateProvider` 구현체가 제공해야 하는 메서드 계약을 정의합니다.
  - 메서드 `fetch_candidates(self, symbol: str, *, start: date, end: date, limit: int)` · candidate_contracts.py:49
    - 기능: `fetch_candidates`은(는) 필요한 데이터를 조회해 반환합니다.
  - 메서드 `close(self)` · candidate_contracts.py:58
    - 기능: `close`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/corporate_actions/contracts.py`

백엔드 도메인 기능을 구현합니다.

- **클래스 `CorporateActionRevisionConflictError`** · contracts.py:16
  - 기능: 해당 실패 조건을 호출 계층에 구분해 전달하는 예외입니다.
- **클래스 `CorporateActionIngestionUnavailableError`** · contracts.py:22
  - 기능: 해당 실패 조건을 호출 계층에 구분해 전달하는 예외입니다.
- **클래스 `CorporateActionAdjustmentUnavailableError`** · contracts.py:28
  - 기능: 해당 실패 조건을 호출 계층에 구분해 전달하는 예외입니다.
- **클래스 `CorporateActionSourceNotFoundError`** · contracts.py:34
  - 기능: 해당 실패 조건을 호출 계층에 구분해 전달하는 예외입니다.
- **클래스 `UntrustedCorporateActionSourceError`** · contracts.py:40
  - 기능: 해당 실패 조건을 호출 계층에 구분해 전달하는 예외입니다.
- **클래스 `CorporateActionRecord`** · contracts.py:47
  - 기능: 저장하거나 전송할 한 건의 구조화된 데이터를 나타냅니다.
- **클래스 `CorporateActionSourceMetadata`** · contracts.py:66
  - 기능: `CorporateActionSourceMetadata` 관련 상태와 동작을 하나의 객체로 묶습니다.
  - 메서드 `__post_init__(self)` · contracts.py:74
    - 기능: `__post_init__`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **클래스 `CorporateActionFetchResult`** · contracts.py:88
  - 기능: 계산 또는 처리 결과를 묶어 전달하는 값 객체입니다.
- **클래스 `CorporateActionProvider`** · contracts.py:97
  - 기능: `CorporateActionProvider` 구현체가 제공해야 하는 메서드 계약을 정의합니다.
  - 메서드 `fetch_actions(self, symbol: str, *, start: datetime, end: datetime, limit: int)` · contracts.py:102
    - 기능: `fetch_actions`은(는) 필요한 데이터를 조회해 반환합니다.
- **클래스 `CorporateActionRepository`** · contracts.py:112
  - 기능: `CorporateActionRepository` 구현체가 제공해야 하는 메서드 계약을 정의합니다.
  - 메서드 `save(self, action: CorporateActionRecord)` · contracts.py:115
    - 기능: `save`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `save_batch(self, actions: list[CorporateActionRecord])` · contracts.py:117
    - 기능: `save_batch`은(는) 데이터를 저장하거나 기존 상태에 추가합니다.
  - 메서드 `list_known(self, symbol: str, *, as_of: datetime)` · contracts.py:119
    - 기능: `list_known`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `list_recent(self, *, limit: int, offset: int, symbol: str | None=None, as_of: datetime | None=None)` · contracts.py:121
    - 기능: `list_recent`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/corporate_actions/dart_candidates.py`

백엔드 도메인 기능을 구현합니다.

- **클래스 `DartCorporateActionCandidateProvider`** · dart_candidates.py:18
  - 기능: 외부 또는 모의 데이터 원천을 동일한 계약으로 제공하는 구현체입니다.
  - 메서드 `__init__(self, dart: DartFinancialProvider)` · dart_candidates.py:23
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `create(cls, *, base_url: str, api_key: str, timeout_seconds: float=15, transport: httpx2.BaseTransport | None=None)` · dart_candidates.py:29
    - 기능: `create`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `fetch_candidates(self, symbol: str, *, start: date, end: date, limit: int)` · dart_candidates.py:48
    - 기능: `fetch_candidates`은(는) 필요한 데이터를 조회해 반환합니다.
  - 메서드 `_rows(self, path: str, params: dict[str, str], symbol: str, candidate_kind: str, disclosure_metadata: dict[str, tuple[str | None, str | None]])` · dart_candidates.py:94
    - 기능: `_rows`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `_candidate(symbol: str, row: dict[str, Any], candidate_kind: str, disclosure_metadata: tuple[str | None, str | None])` · dart_candidates.py:128
    - 기능: `_candidate`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `_disclosure_metadata(self, corp_code: str, start: date, end: date, limit: int)` · dart_candidates.py:199
    - 기능: `_disclosure_metadata`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `close(self)` · dart_candidates.py:255
    - 기능: `close`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_date(value: object, *, required: bool=False)`** · dart_candidates.py:261
  - 기능: `_date`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_decimal(value: object)`** · dart_candidates.py:276
  - 기능: `_decimal`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/corporate_actions/dart_mapping.py`

백엔드 도메인 기능을 구현합니다.

- **클래스 `DartCorporateActionMapper`** · dart_mapping.py:15
  - 기능: `DartCorporateActionMapper` 관련 상태와 동작을 하나의 객체로 묶습니다.
  - 메서드 `map_bonus_issue(self, row: Mapping[str, object], *, symbol: str, event_id: str, revision: int, known_at: datetime, effective_at: datetime, status: str='announced')` · dart_mapping.py:18
    - 기능: `map_bonus_issue`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `map_proportional_capital_reduction(self, row: Mapping[str, object], *, symbol: str, event_id: str, revision: int, known_at: datetime, effective_at: datetime, proportional_share_consolidation: bool, status: str='announced')` · dart_mapping.py:46
    - 기능: `map_proportional_capital_reduction`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `_record(*, symbol: str, event_id: str, revision: int, known_at: datetime, effective_at: datetime, announced_at: datetime | None, action_type: str, price_factor: Decimal, volume_factor: Decimal, status: str)` · dart_mapping.py:83
    - 기능: `_record`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `_positive_decimal(row: Mapping[str, object], field: str)` · dart_mapping.py:118
    - 기능: `_positive_decimal`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `_optional_date(value: object)` · dart_mapping.py:131
    - 기능: `_optional_date`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `_require_aware(value: datetime)` · dart_mapping.py:144
    - 기능: `_require_aware`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/corporate_actions/engine.py`

백엔드 도메인 기능을 구현합니다.

- **클래스 `AdjustmentResult`** · engine.py:14
  - 기능: 계산 또는 처리 결과를 묶어 전달하는 값 객체입니다.
- **클래스 `BacktestAdjustmentResult`** · engine.py:27
  - 기능: 계산 또는 처리 결과를 묶어 전달하는 값 객체입니다.
- **클래스 `CorporateActionAdjustmentEngine`** · engine.py:41
  - 기능: 입력 데이터로부터 결정론적 결과를 계산하는 엔진입니다.
  - 메서드 `adjust(self, candles: list[Candle], actions: list[CorporateActionRecord], *, as_of: datetime)` · engine.py:44
    - 기능: `adjust`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `_latest_effective_revisions(self, actions: list[CorporateActionRecord], as_of: datetime)` · engine.py:91
    - 기능: `_latest_effective_revisions`은(는) 필요한 데이터를 조회해 반환합니다.
  - 메서드 `_validate_action(self, action: CorporateActionRecord)` · engine.py:117
    - 기능: `_validate_action`은(는) 입력 또는 현재 상태가 규칙을 만족하는지 검증합니다.
  - 메서드 `_require_aware(value: datetime, field: str)` · engine.py:134
    - 기능: `_require_aware`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **클래스 `CorporateActionBacktestAdjustmentEngine`** · engine.py:141
  - 기능: 입력 데이터로부터 결정론적 결과를 계산하는 엔진입니다.
  - 메서드 `adjust(self, candles: list[Candle], actions: list[CorporateActionRecord], *, as_of: datetime)` · engine.py:144
    - 기능: `adjust`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/corporate_actions/exchange_verification.py`

백엔드 도메인 기능을 구현합니다.

- **함수 `_is_authoritative_https_url(value: str, *, expected_host: str | None=None)`** · exchange_verification.py:15
  - 기능: `_is_authoritative_https_url`은(는) 입력 또는 현재 상태가 규칙을 만족하는지 검증합니다.
- **클래스 `ExchangeVerificationSourceNotFoundError`** · exchange_verification.py:34
  - 기능: 해당 실패 조건을 호출 계층에 구분해 전달하는 예외입니다.
- **클래스 `ExchangeVerificationUnavailableError`** · exchange_verification.py:40
  - 기능: 해당 실패 조건을 호출 계층에 구분해 전달하는 예외입니다.
- **클래스 `ExchangeVerificationMetadata`** · exchange_verification.py:47
  - 기능: `ExchangeVerificationMetadata` 관련 상태와 동작을 하나의 객체로 묶습니다.
  - 메서드 `__post_init__(self)` · exchange_verification.py:62
    - 기능: `__post_init__`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **클래스 `ExchangeVerificationResult`** · exchange_verification.py:84
  - 기능: 계산 또는 처리 결과를 묶어 전달하는 값 객체입니다.
- **클래스 `ExchangeVerificationProvider`** · exchange_verification.py:98
  - 기능: `ExchangeVerificationProvider` 구현체가 제공해야 하는 메서드 계약을 정의합니다.
  - 메서드 `verify_effective_date(self, symbol: str, action_type: str, *, effective_at: datetime)` · exchange_verification.py:103
    - 기능: `verify_effective_date`은(는) 입력 또는 현재 상태가 규칙을 만족하는지 검증합니다.
- **클래스 `CorporateActionExchangeVerificationService`** · exchange_verification.py:206
  - 기능: 사용 사례의 처리 순서와 하위 의존성 호출을 조율하는 서비스입니다.
  - 메서드 `__init__(self, providers: list[ExchangeVerificationProvider] | None=None, candidates: tuple[ExchangeVerificationMetadata, ...]=EXCHANGE_VERIFICATION_CANDIDATES)` · exchange_verification.py:209
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `status(self)` · exchange_verification.py:224
    - 기능: `status`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `verify(self, source: str, symbol: str, action_type: str, *, effective_at: datetime)` · exchange_verification.py:248
    - 기능: `verify`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `_validate_result(cls, metadata: ExchangeVerificationMetadata, result: ExchangeVerificationResult, symbol: str, action_type: str, effective_at: datetime)` · exchange_verification.py:277
    - 기능: `_validate_result`은(는) 입력 또는 현재 상태가 규칙을 만족하는지 검증합니다.
  - 메서드 `_require_aware(value: datetime)` · exchange_verification.py:311
    - 기능: `_require_aware`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/corporate_actions/providers.py`

백엔드 도메인 기능을 구현합니다.

- **함수 `build_corporate_action_candidate_providers(settings: Settings)`** · providers.py:7
  - 기능: `build_corporate_action_candidate_providers`은(는) 입력 값과 설정을 결합해 새 결과 객체를 생성합니다.

### `backend/app/corporate_actions/reconciliation.py`

백엔드 도메인 기능을 구현합니다.

- **클래스 `CorporateActionRevisionGroup`** · reconciliation.py:12
  - 기능: `CorporateActionRevisionGroup` 관련 상태와 동작을 하나의 객체로 묶습니다.
- **클래스 `CorporateActionRevisionReconciler`** · reconciliation.py:28
  - 기능: `CorporateActionRevisionReconciler` 관련 상태와 동작을 하나의 객체로 묶습니다.
  - 메서드 `propose(self, candidates: tuple[CorporateActionCandidate, ...])` · reconciliation.py:31
    - 기능: `propose`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `_confidence(items: list[CorporateActionCandidate])` · reconciliation.py:75
    - 기능: `_confidence`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `_report_name(value: str | None)` · reconciliation.py:95
    - 기능: `_report_name`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/data_lifecycle/contracts.py`

백엔드 도메인 기능을 구현합니다.

- **클래스 `DataLifecycleRepository`** · contracts.py:7
  - 기능: `DataLifecycleRepository` 구현체가 제공해야 하는 메서드 계약을 정의합니다.
  - 메서드 `count_before(self, cutoffs: dict[str, datetime])` · contracts.py:10
    - 기능: `count_before`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `delete_before(self, cutoffs: dict[str, datetime])` · contracts.py:12
    - 기능: `delete_before`은(는) 대상 데이터나 만료된 상태를 안전하게 제거합니다.

### `backend/app/database/base.py`

백엔드 도메인 기능을 구현합니다.

- **클래스 `Base`** · base.py:6
  - 기능: `Base` 관련 상태와 동작을 하나의 객체로 묶습니다.

### `backend/app/database/partitions.py`

백엔드 도메인 기능을 구현합니다.

- **클래스 `PlannedPartition`** · partitions.py:18
  - 기능: `PlannedPartition` 관련 상태와 동작을 하나의 객체로 묶습니다.
- **클래스 `ArchiveCandidate`** · partitions.py:27
  - 기능: `ArchiveCandidate` 관련 상태와 동작을 하나의 객체로 묶습니다.
- **함수 `_shift_month(value: date, offset: int)`** · partitions.py:35
  - 기능: `_shift_month`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `plan_future_partitions(reference: date, lookahead_months: int)`** · partitions.py:42
  - 기능: `plan_future_partitions`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `plan_archive_candidates(partition_names: list[str], reference: date, archive_after_months: int)`** · partitions.py:57
  - 기능: `plan_archive_candidates`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **클래스 `CandlePartitionMaintenanceService`** · partitions.py:76
  - 기능: 사용 사례의 처리 순서와 하위 의존성 호출을 조율하는 서비스입니다.
  - 메서드 `__init__(self, sessions: sessionmaker[Session], lookahead_months: int, archive_after_months: int=120)` · partitions.py:79
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `supported(self)` · partitions.py:92
    - 기능: `supported`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `ensure_future(self, reference: date | None=None)` · partitions.py:98
    - 기능: `ensure_future`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `status(self)` · partitions.py:131
    - 기능: `status`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `_archive_plan(self, partition_names: list[str], reference: date, status: str)` · partitions.py:167
    - 기능: `_archive_plan`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/database/session.py`

백엔드 도메인 기능을 구현합니다.

- **함수 `create_session_factory(database_url: str)`** · session.py:7
  - 기능: `create_session_factory`은(는) 입력 값과 설정을 결합해 새 결과 객체를 생성합니다.

### `backend/app/disclosures/contracts.py`

백엔드 도메인 기능을 구현합니다.

- **클래스 `Disclosure`** · contracts.py:9
  - 기능: `Disclosure` 관련 상태와 동작을 하나의 객체로 묶습니다.
- **클래스 `DisclosureProvider`** · contracts.py:23
  - 기능: `DisclosureProvider` 구현체가 제공해야 하는 메서드 계약을 정의합니다.
  - 메서드 `list_disclosures(self, symbol: str, *, days: int, limit: int)` · contracts.py:29
    - 기능: `list_disclosures`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `close(self)` · contracts.py:31
    - 기능: `close`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/disclosures/dart.py`

백엔드 도메인 기능을 구현합니다.

- **클래스 `DartDisclosureProvider`** · dart.py:13
  - 기능: 외부 또는 모의 데이터 원천을 동일한 계약으로 제공하는 구현체입니다.
  - 메서드 `__init__(self, dart: DartFinancialProvider)` · dart.py:18
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `create(cls, *, base_url: str, api_key: str, timeout_seconds: float=15, transport: httpx2.BaseTransport | None=None)` · dart.py:24
    - 기능: `create`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `list_disclosures(self, symbol: str, *, days: int, limit: int)` · dart.py:43
    - 기능: `list_disclosures`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `close(self)` · dart.py:70
    - 기능: `close`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_disclosure_from_row(symbol: str, row: dict[str, Any])`** · dart.py:76
  - 기능: `_disclosure_from_row`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/disclosures/providers.py`

백엔드 도메인 기능을 구현합니다.

- **클래스 `MockDisclosureProvider`** · providers.py:10
  - 기능: 외부 또는 모의 데이터 원천을 동일한 계약으로 제공하는 구현체입니다.
  - 메서드 `list_disclosures(self, symbol: str, *, days: int, limit: int)` · providers.py:16
    - 기능: `list_disclosures`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `build_disclosure_provider(settings: Settings)`** · providers.py:54
  - 기능: `build_disclosure_provider`은(는) 입력 값과 설정을 결합해 새 결과 객체를 생성합니다.

### `backend/app/financials/contracts.py`

백엔드 도메인 기능을 구현합니다.

- **클래스 `FinancialSnapshot`** · contracts.py:10
  - 기능: 특정 시점에 관측된 데이터 상태를 변경 없이 전달하는 값 객체입니다.
- **클래스 `FinancialProvider`** · contracts.py:28
  - 기능: `FinancialProvider` 구현체가 제공해야 하는 메서드 계약을 정의합니다.
  - 메서드 `get_snapshot(self, symbol: str, fiscal_year: int, report_code: str='11011')` · contracts.py:34
    - 기능: `get_snapshot`은(는) 필요한 데이터를 조회해 반환합니다.
  - 메서드 `get_issued_shares(self, symbol: str, fiscal_year: int, report_code: str='11011')` · contracts.py:38
    - 기능: `get_issued_shares`은(는) 필요한 데이터를 조회해 반환합니다.
  - 메서드 `close(self)` · contracts.py:45
    - 기능: `close`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/financials/dart.py`

백엔드 도메인 기능을 구현합니다.

- **클래스 `DartFinancialProvider`** · dart.py:38
  - 기능: 외부 또는 모의 데이터 원천을 동일한 계약으로 제공하는 구현체입니다.
  - 메서드 `__init__(self, client: httpx2.Client, api_key: str)` · dart.py:43
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `create(cls, *, base_url: str, api_key: str, timeout_seconds: float=15, transport: httpx2.BaseTransport | None=None)` · dart.py:51
    - 기능: `create`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `get_snapshot(self, symbol: str, fiscal_year: int, report_code: str='11011')` · dart.py:70
    - 기능: `get_snapshot`은(는) 필요한 데이터를 조회해 반환합니다.
  - 메서드 `corp_code_for(self, symbol: str)` · dart.py:100
    - 기능: `corp_code_for`은(는) 입력 조건을 지원하는 제공자나 처리 대상을 선택해 반환합니다.
  - 메서드 `get_issued_shares(self, symbol: str, fiscal_year: int, report_code: str='11011')` · dart.py:104
    - 기능: `get_issued_shares`은(는) 필요한 데이터를 조회해 반환합니다.
  - 메서드 `get_json(self, path: str, params: dict[str, str])` · dart.py:132
    - 기능: `get_json`은(는) 필요한 데이터를 조회해 반환합니다.
  - 메서드 `_corp_code_for(self, symbol: str)` · dart.py:136
    - 기능: `_corp_code_for`은(는) 입력 조건을 지원하는 제공자나 처리 대상을 선택해 반환합니다.
  - 메서드 `_load_corp_codes(self)` · dart.py:148
    - 기능: `_load_corp_codes`은(는) 필요한 데이터를 조회해 반환합니다.
  - 메서드 `_statement_payload(self, corp_code: str, fiscal_year: int, report_code: str)` · dart.py:169
    - 기능: `_statement_payload`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `_json_get(self, path: str, params: dict[str, str])` · dart.py:193
    - 기능: `_json_get`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `close(self)` · dart.py:210
    - 기능: `close`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_extract_accounts(rows: list[Any])`** · dart.py:216
  - 기능: `_extract_accounts`은(는) 원시 입력을 해석하고 필요한 값을 정규화해 추출합니다.
- **함수 `_amount(value: Any)`** · dart.py:233
  - 기능: `_amount`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_first_currency(rows: list[Any])`** · dart.py:249
  - 기능: `_first_currency`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_raise_dart_error(payload: dict[str, Any])`** · dart.py:258
  - 기능: `_raise_dart_error`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/financials/providers.py`

백엔드 도메인 기능을 구현합니다.

- **클래스 `MockFinancialProvider`** · providers.py:10
  - 기능: 외부 또는 모의 데이터 원천을 동일한 계약으로 제공하는 구현체입니다.
  - 메서드 `get_snapshot(self, symbol: str, fiscal_year: int, report_code: str='11011')` · providers.py:49
    - 기능: `get_snapshot`은(는) 필요한 데이터를 조회해 반환합니다.
  - 메서드 `get_issued_shares(self, symbol: str, fiscal_year: int, report_code: str='11011')` · providers.py:79
    - 기능: `get_issued_shares`은(는) 필요한 데이터를 조회해 반환합니다.
- **함수 `build_financial_provider(settings: Settings)`** · providers.py:87
  - 기능: `build_financial_provider`은(는) 입력 값과 설정을 결합해 새 결과 객체를 생성합니다.

### `backend/app/financials/valuation.py`

백엔드 도메인 기능을 구현합니다.

- **클래스 `ValuationInputs`** · valuation.py:16
  - 기능: `ValuationInputs` 관련 상태와 동작을 하나의 객체로 묶습니다.
- **함수 `calculate_valuation_ratios(*, price: Decimal, inputs: ValuationInputs)`** · valuation.py:27
  - 기능: `calculate_valuation_ratios`은(는) 입력 데이터를 기준으로 모델 또는 규칙의 결과 값을 계산해 반환합니다.
- **클래스 `ValuationAnalysisService`** · valuation.py:43
  - 기능: 사용 사례의 처리 순서와 하위 의존성 호출을 조율하는 서비스입니다.
  - 메서드 `__init__(self, financial_provider: FinancialProvider, quote_loader: Callable[[str], tuple[Quote, str]], sec_client: SecCompanyFactsClient | None=None)` · valuation.py:46
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `analyze(self, symbol: str, fiscal_year: int, report_code: str='11011')` · valuation.py:58
    - 기능: `analyze`은(는) 해당 작업의 전체 처리 흐름을 실행하고 결과를 반환합니다.
- **함수 `_positive_denominator_ratio(numerator: Decimal | None, denominator: Decimal | None)`** · valuation.py:114
  - 기능: `_positive_denominator_ratio`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_decimal(value: object)`** · valuation.py:124
  - 기능: `_decimal`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/indicators/engine.py`

백엔드 도메인 기능을 구현합니다.

- **함수 `_wilder_smoothing(values: pd.Series, period: int)`** · engine.py:16
  - 기능: `_wilder_smoothing`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_safe_value(value: Any)`** · engine.py:35
  - 기능: `_safe_value`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **클래스 `IndicatorEngine`** · engine.py:48
  - 기능: 입력 데이터로부터 결정론적 결과를 계산하는 엔진입니다.
  - 메서드 `calculate(self, candles: list[Candle])` · engine.py:54
    - 기능: `calculate`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `_supertrend(high: pd.Series, low: pd.Series, close: pd.Series, period: int, multiplier: float)` · engine.py:160
    - 기능: `_supertrend`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/investor_flow/contracts.py`

백엔드 도메인 기능을 구현합니다.

- **클래스 `InvestorFlow`** · contracts.py:10
  - 기능: `InvestorFlow` 관련 상태와 동작을 하나의 객체로 묶습니다.
- **클래스 `InvestorFlowProvider`** · contracts.py:23
  - 기능: `InvestorFlowProvider` 구현체가 제공해야 하는 메서드 계약을 정의합니다.
  - 메서드 `get_flow(self, symbol: str)` · contracts.py:29
    - 기능: `get_flow`은(는) 필요한 데이터를 조회해 반환합니다.
  - 메서드 `close(self)` · contracts.py:31
    - 기능: `close`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/investor_flow/kis.py`

백엔드 도메인 기능을 구현합니다.

- **클래스 `KisInvestorFlowProvider`** · kis.py:18
  - 기능: 외부 또는 모의 데이터 원천을 동일한 계약으로 제공하는 구현체입니다.
  - 메서드 `__init__(self, client: httpx2.Client, app_key: str, app_secret: str)` · kis.py:30
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `create(cls, *, base_url: str, app_key: str, app_secret: str, timeout_seconds: float=15, transport: httpx2.BaseTransport | None=None)` · kis.py:40
    - 기능: `create`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `get_flow(self, symbol: str)` · kis.py:59
    - 기능: `get_flow`은(는) 필요한 데이터를 조회해 반환합니다.
  - 메서드 `get_daily_flows(self, symbol: str, *, end_date: date, max_pages: int=10)` · kis.py:108
    - 기능: 종목별 과거 투자자 수급을 KIS 연속조회 규칙에 맞춰 가져온다.
  - 메서드 `_daily_flow_page(self, symbol: str, *, end_date: date, continuation: str)` · kis.py:142
    - 기능: `_daily_flow_page`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `_access_token(self)` · kis.py:187
    - 기능: `_access_token`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `close(self)` · kis.py:217
    - 기능: `close`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_decimal(row: dict[str, Any], field: str)`** · kis.py:223
  - 기능: `_decimal`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_optional_decimal(row: dict[str, Any], field: str)`** · kis.py:232
  - 기능: `_optional_decimal`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **클래스 `DailyKisInvestorFlow`** · kis.py:247
  - 기능: KIS 종목별 일별 수급 중 학습에 필요한 시점 정보와 순매수 수량이다.
- **함수 `_daily_flow(row: Any, symbol: str)`** · kis.py:257
  - 기능: `_daily_flow`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/investor_flow/providers.py`

백엔드 도메인 기능을 구현합니다.

- **클래스 `MockInvestorFlowProvider`** · providers.py:11
  - 기능: 외부 또는 모의 데이터 원천을 동일한 계약으로 제공하는 구현체입니다.
  - 메서드 `get_flow(self, symbol: str)` · providers.py:21
    - 기능: `get_flow`은(는) 필요한 데이터를 조회해 반환합니다.
- **함수 `build_investor_flow_provider(settings: Settings)`** · providers.py:44
  - 기능: `build_investor_flow_provider`은(는) 입력 값과 설정을 결합해 새 결과 객체를 생성합니다.

### `backend/app/local_ai/advanced_market_features.py`

직접 학습 AI의 특성·모델·품질·실행을 담당합니다.

- **함수 `enrich_advanced_technical_rows(rows: list[dict[str, str]])`** · advanced_market_features.py:31
  - 기능: 기술 데이터 행에 누수 없는 시계열·횡단면 후보 피처를 덧붙인다.
- **함수 `_time_series_features(closes: np.ndarray, returns: np.ndarray, rolling_volatility: np.ndarray, index: int)`** · advanced_market_features.py:64
  - 기능: 한 종목의 현재 인덱스 이전 값만으로 후보 피처를 계산한다.
- **함수 `_rolling_volatility(returns: np.ndarray, *, window: int)`** · advanced_market_features.py:108
  - 기능: 각 종가 인덱스에서 확인 가능한 최근 수익률 변동성을 만든다.
- **함수 `_add_cross_section_features(rows: list[dict[str, object]])`** · advanced_market_features.py:116
  - 기능: 같은 시점에 존재하는 종목끼리만 상대순위와 시장 폭을 계산한다.
- **함수 `_percentile_ranks(values: np.ndarray)`** · advanced_market_features.py:144
  - 기능: 동률에 평균 순위를 부여하는 0~1 범위의 횡단면 순위를 반환한다.
- **함수 `_correlation(left: np.ndarray, right: np.ndarray)`** · advanced_market_features.py:160
  - 기능: 상수 구간에서는 중립값 0을 반환해 비유한 숫자를 방지한다.

### `backend/app/local_ai/context_features.py`

직접 학습 AI의 특성·모델·품질·실행을 담당합니다.

- **함수 `add_financial_trends(rows: list[dict])`** · context_features.py:21
  - 기능: `add_financial_trends`은(는) 데이터를 저장하거나 기존 상태에 추가합니다.
- **함수 `add_news_trends(rows: list[dict])`** · context_features.py:27
  - 기능: `add_news_trends`은(는) 데이터를 저장하거나 기존 상태에 추가합니다.
- **함수 `_add_grouped_trends(rows: list[dict], change_builder)`** · context_features.py:55
  - 기능: `_add_grouped_trends`은(는) 데이터를 저장하거나 기존 상태에 추가합니다.
- **함수 `_financial_changes(current: dict, previous: dict)`** · context_features.py:70
  - 기능: `_financial_changes`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_group_rows(rows: list[dict])`** · context_features.py:84
  - 기능: `_group_rows`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/local_ai/contracts.py`

직접 학습 AI의 특성·모델·품질·실행을 담당합니다.

- **클래스 `LocalAgentResult`** · contracts.py:22
  - 기능: 계산 또는 처리 결과를 묶어 전달하는 값 객체입니다.
  - 메서드 `to_dict(self)` · contracts.py:34
    - 기능: `to_dict`은(는) 내부 값을 전송·표시 가능한 형식으로 변환합니다.
- **클래스 `LocalSynthesisResult`** · contracts.py:41
  - 기능: 계산 또는 처리 결과를 묶어 전달하는 값 객체입니다.
  - 메서드 `to_dict(self)` · contracts.py:55
    - 기능: `to_dict`은(는) 내부 값을 전송·표시 가능한 형식으로 변환합니다.

### `backend/app/local_ai/diagnostic.py`

직접 학습 AI의 특성·모델·품질·실행을 담당합니다.

- **클래스 `DiagnosticCalculation`** · diagnostic.py:31
  - 기능: `DiagnosticCalculation` 관련 상태와 동작을 하나의 객체로 묶습니다.
- **클래스 `DiagnosticPolicy`** · diagnostic.py:42
  - 기능: `DiagnosticPolicy` 관련 상태와 동작을 하나의 객체로 묶습니다.
- **함수 `load_diagnostic_policy(path: Path)`** · diagnostic.py:50
  - 기능: `load_diagnostic_policy`은(는) 필요한 데이터를 조회해 반환합니다.
- **함수 `directional_signal(agent: AgentName, probability: float)`** · diagnostic.py:89
  - 기능: `directional_signal`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `calculate_diagnostic(results: dict[str, dict], specialist_names: tuple[AgentName, ...])`** · diagnostic.py:101
  - 기능: `calculate_diagnostic`은(는) 입력 데이터를 기준으로 모델 또는 규칙의 결과 값을 계산해 반환합니다.
- **함수 `diagnostic_disagreement(weighted: list[tuple[str, float, float]])`** · diagnostic.py:151
  - 기능: `diagnostic_disagreement`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/local_ai/etf.py`

직접 학습 AI의 특성·모델·품질·실행을 담당합니다.

- **함수 `is_etf(symbol: str, stock: dict | None=None)`** · etf.py:39
  - 기능: `is_etf`은(는) 입력 또는 현재 상태가 규칙을 만족하는지 검증합니다.
- **함수 `etf_asset_class(symbol: str)`** · etf.py:51
  - 기능: `etf_asset_class`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `etf_asset_class_features(symbol: str)`** · etf.py:65
  - 기능: `etf_asset_class_features`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/local_ai/features.py`

직접 학습 AI의 특성·모델·품질·실행을 담당합니다.

- **함수 `build_synthesis_features(results: dict[str, dict])`** · features.py:64
  - 기능: `build_synthesis_features`은(는) 입력 값과 설정을 결합해 새 결과 객체를 생성합니다.
- **함수 `build_etf_synthesis_features(results: dict[str, dict], macro_features: dict[str, float] | None)`** · features.py:77
  - 기능: `build_etf_synthesis_features`은(는) 입력 값과 설정을 결합해 새 결과 객체를 생성합니다.
- **함수 `extract_features(agent: AgentName, facts: dict[str, Any])`** · features.py:91
  - 기능: `extract_features`은(는) 원시 입력을 해석하고 필요한 값을 정규화해 추출합니다.
- **함수 `_select(names: tuple[str, ...], values: dict)`** · features.py:149
  - 기능: `_select`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_finding_score(findings: dict, name: str)`** · features.py:158
  - 기능: `_finding_score`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_range_width(support: Any, resistance: Any)`** · features.py:165
  - 기능: `_range_width`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_number(value: Any)`** · features.py:174
  - 기능: `_number`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/local_ai/financial_features.py`

직접 학습 AI의 특성·모델·품질·실행을 담당합니다.

- **클래스 `FinancialSnapshot`** · financial_features.py:41
  - 기능: 특정 시점에 관측된 데이터 상태를 변경 없이 전달하는 값 객체입니다.
- **클래스 `AnnualValuationSnapshot`** · financial_features.py:56
  - 기능: 특정 10-K가 처음 공개된 시점에 사용 가능했던 연간 재무 값이다.
- **함수 `latest_financial_features(companyfacts: dict)`** · financial_features.py:67
  - 기능: `latest_financial_features`은(는) 필요한 데이터를 조회해 반환합니다.
- **함수 `latest_annual_valuation_inputs(companyfacts: dict)`** · financial_features.py:74
  - 기능: `latest_annual_valuation_inputs`은(는) 필요한 데이터를 조회해 반환합니다.
- **함수 `extract_annual_valuation_snapshots(companyfacts: dict)`** · financial_features.py:93
  - 기능: 수정 공시의 미래 값 없이 최초 10-K별 밸류에이션 입력 이력을 복원한다.
- **함수 `build_financial_training_rows(companyfacts: dict)`** · financial_features.py:162
  - 기능: `build_financial_training_rows`은(는) 입력 값과 설정을 결합해 새 결과 객체를 생성합니다.
- **함수 `extract_financial_snapshots(companyfacts: dict)`** · financial_features.py:180
  - 기능: `extract_financial_snapshots`은(는) 원시 입력을 해석하고 필요한 값을 정규화해 추출합니다.
- **함수 `_feature_rows(snapshots: list[FinancialSnapshot])`** · financial_features.py:239
  - 기능: `_feature_rows`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_first_available_entries(facts: dict, candidates: tuple[str, ...])`** · financial_features.py:263
  - 기능: `_first_available_entries`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_first_available_unit_entries(facts: dict, candidates: tuple[str, ...], unit: str)`** · financial_features.py:269
  - 기능: `_first_available_unit_entries`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_is_quarter_duration(entry: dict)`** · financial_features.py:281
  - 기능: `_is_quarter_duration`은(는) 입력 또는 현재 상태가 규칙을 만족하는지 검증합니다.
- **함수 `_is_annual_duration(entry: dict)`** · financial_features.py:292
  - 기능: `_is_annual_duration`은(는) 입력 또는 현재 상태가 규칙을 만족하는지 검증합니다.
- **함수 `_quality(features: dict[str, float])`** · financial_features.py:303
  - 기능: `_quality`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_clip(value: float, low: float, high: float)`** · financial_features.py:315
  - 기능: `_clip`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_positive_number(value: object)`** · financial_features.py:321
  - 기능: `_positive_number`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/local_ai/finra.py`

직접 학습 AI의 특성·모델·품질·실행을 담당합니다.

- **클래스 `FinraShortVolumeClient`** · finra.py:17
  - 기능: 외부 서비스의 인증·요청·응답 검증을 캡슐화하는 client입니다.
  - 메서드 `__init__(self, *, base_url: str, token_url: str, client_id: str, client_secret: str, timeout_seconds: float=30.0, cache_seconds: float=900.0)` · finra.py:20
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `records(self, symbol: str)` · finra.py:41
    - 기능: `records`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `short_interest_records(self, symbol: str)` · finra.py:75
    - 기능: `short_interest_records`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `latest_features(self, symbol: str)` · finra.py:104
    - 기능: `latest_features`은(는) 필요한 데이터를 조회해 반환합니다.
  - 메서드 `close(self)` · finra.py:116
    - 기능: `close`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `_access_token(self)` · finra.py:121
    - 기능: `_access_token`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/local_ai/flow_features.py`

직접 학습 AI의 특성·모델·품질·실행을 담당합니다.

- **클래스 `DailyShortVolume`** · flow_features.py:31
  - 기능: `DailyShortVolume` 관련 상태와 동작을 하나의 객체로 묶습니다.
- **함수 `aggregate_short_volume(records: list[dict])`** · flow_features.py:40
  - 기능: `aggregate_short_volume`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `latest_flow_features(records: list[dict])`** · flow_features.py:60
  - 기능: `latest_flow_features`은(는) 필요한 데이터를 조회해 반환합니다.
- **함수 `short_interest_features_by_date(records: list[dict], target_dates: list[date])`** · flow_features.py:67
  - 기능: `short_interest_features_by_date`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `build_flow_training_rows(records: list[dict], candles: list[Candle], *, horizon_days: int=5, minimum_absolute_excess_return: float=0.0, benchmark_candles: list[Candle] | None=None)`** · flow_features.py:101
  - 기능: `build_flow_training_rows`은(는) 입력 값과 설정을 결합해 새 결과 객체를 생성합니다.
- **함수 `_features_at(daily: list[DailyShortVolume], index: int)`** · flow_features.py:159
  - 기능: `_features_at`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_nonnegative(value)`** · flow_features.py:180
  - 기능: `_nonnegative`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/local_ai/flow_market_features.py`

직접 학습 AI의 특성·모델·품질·실행을 담당합니다.

- **함수 `flow_market_features(market: dict[str, float])`** · flow_market_features.py:12
  - 기능: `flow_market_features`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/local_ai/fred.py`

직접 학습 AI의 특성·모델·품질·실행을 담당합니다.

- **클래스 `FredClient`** · fred.py:18
  - 기능: 외부 서비스의 인증·요청·응답 검증을 캡슐화하는 client입니다.
  - 메서드 `__init__(self, *, api_key: str, base_url: str='https://api.stlouisfed.org/fred', timeout_seconds: float=30.0)` · fred.py:21
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `latest_macro_features(self)` · fred.py:35
    - 기능: `latest_macro_features`은(는) 필요한 데이터를 조회해 반환합니다.
  - 메서드 `macro_observations(self, *, observation_start: date, observation_end: date)` · fred.py:50
    - 기능: `macro_observations`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `observations(self, series_id: str, *, observation_start: date, observation_end: date)` · fred.py:64
    - 기능: `observations`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `close(self)` · fred.py:99
    - 기능: `close`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/local_ai/http_security.py`

직접 학습 AI의 특성·모델·품질·실행을 담당합니다.

- **클래스 `DailyRequestBudget`** · http_security.py:16
  - 기능: `DailyRequestBudget` 관련 상태와 동작을 하나의 객체로 묶습니다.
  - 메서드 `__init__(self, maximum: int)` · http_security.py:19
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `consume(self, *, provider: str)` · http_security.py:29
    - 기능: `consume`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `validate_symbol(symbol: str)`** · http_security.py:42
  - 기능: `validate_symbol`은(는) 입력 또는 현재 상태가 규칙을 만족하는지 검증합니다.
- **함수 `validate_https_endpoint(value: str, *, name: str)`** · http_security.py:51
  - 기능: `validate_https_endpoint`은(는) 입력 또는 현재 상태가 규칙을 만족하는지 검증합니다.
- **함수 `bounded_json(response: Any, *, provider: str, maximum_bytes: int)`** · http_security.py:68
  - 기능: `bounded_json`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/local_ai/kis_flow_features.py`

직접 학습 AI의 특성·모델·품질·실행을 담당합니다.

- **함수 `build_kis_flow_training_rows(flows: list[DailyKisInvestorFlow], candles: list[Candle], *, benchmark_candles: list[Candle], horizon_days: int=5, minimum_absolute_excess_return: float=0.005)`** · kis_flow_features.py:37
  - 기능: 공개된 당일 수급만 사용해 이후 벤치마크 대비 하락 여부를 만든다.
- **함수 `_features_at(ratios: list[tuple[date, float, float, float]], index: int)`** · kis_flow_features.py:113
  - 기능: `_features_at`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_zscore(values: np.ndarray)`** · kis_flow_features.py:134
  - 기능: `_zscore`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/local_ai/macro_features.py`

직접 학습 AI의 특성·모델·품질·실행을 담당합니다.

- **함수 `build_macro_features(observations: dict[str, list[tuple[date, float]]])`** · macro_features.py:26
  - 기능: `build_macro_features`은(는) 입력 값과 설정을 결합해 새 결과 객체를 생성합니다.
- **함수 `macro_features_at(observations: dict[str, list[tuple[date, float]]], as_of: date)`** · macro_features.py:40
  - 기능: `macro_features_at`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_latest(values: list[tuple[date, float]], as_of: date)`** · macro_features.py:68
  - 기능: `_latest`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/local_ai/market_features.py`

직접 학습 AI의 특성·모델·품질·실행을 담당합니다.

- **클래스 `MarketTrainingRow`** · market_features.py:47
  - 기능: `MarketTrainingRow` 관련 상태와 동작을 하나의 객체로 묶습니다.
- **함수 `latest_market_features(candles: list[Candle], benchmark_candles: list[Candle] | None=None)`** · market_features.py:62
  - 기능: `latest_market_features`은(는) 필요한 데이터를 조회해 반환합니다.
- **함수 `build_market_training_rows(candles: list[Candle], *, horizon_days: int=5, risk_threshold: float=-0.03, benchmark_candles: list[Candle] | None=None, include_long_horizon_risk: bool=False)`** · market_features.py:79
  - 기능: `build_market_training_rows`은(는) 입력 값과 설정을 결합해 새 결과 객체를 생성합니다.
- **함수 `_features_by_date(candles: list[Candle])`** · market_features.py:147
  - 기능: `_features_by_date`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_add_benchmark_features(technical: dict[str, float], risk: dict[str, float], benchmark_technical: dict[str, float], benchmark_risk: dict[str, float])`** · market_features.py:159
  - 기능: `_add_benchmark_features`은(는) 데이터를 저장하거나 기존 상태에 추가합니다.
- **함수 `_features_at(candles: list[Candle], index: int)`** · market_features.py:186
  - 기능: `_features_at`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_long_horizon_risk_features(candles: list[Candle], index: int, risk: dict[str, float])`** · market_features.py:221
  - 기능: `_long_horizon_risk_features`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/local_ai/model.py`

직접 학습 AI의 특성·모델·품질·실행을 담당합니다.

- **클래스 `LocalModelArtifact`** · model.py:30
  - 기능: 학습 결과와 재현·검증 정보를 함께 저장하는 JSON 모델 계약이다.
- **클래스 `LocalLogisticModel`** · model.py:47
  - 기능: 표준화와 확률 보정을 포함하는 로컬 로지스틱 회귀 모델이다.
  - 메서드 `__init__(self, artifact: LocalModelArtifact)` · model.py:50
    - 기능: 검증된 모델 artifact를 메모리에 올려 추론 가능한 상태로 만든다.
  - 메서드 `train(cls, agent: ModelName, feature_names: tuple[str, ...], features: np.ndarray, labels: np.ndarray, *, iterations: int=1200, learning_rate: float=0.05, l2: float=0.001, validation_gap: int=0, validation_start: int | None=None)` · model.py:56
    - 기능: 시간순 학습·검증 구간으로 모델을 학습하고 검증 지표를 artifact에 기록한다.
  - 메서드 `train_sklearn(cls, agent: ModelName, feature_names: tuple[str, ...], features: np.ndarray, labels: np.ndarray, *, inverse_regularization: float=0.1, validation_gap: int=0, validation_start: int | None=None, class_weight_balanced: bool=False, positive_class_weight: float | None=None)` · model.py:134
    - 기능: scikit-learn으로 후보를 학습하되 동일한 안전한 JSON 계약으로 반환한다.
  - 메서드 `predict_probability(self, values: dict[str, float])` · model.py:221
    - 기능: 학습 당시 특성 순서와 표준화를 적용해 보정된 양성 확률을 계산한다.
  - 메서드 `save(self, path: str | Path)` · model.py:235
    - 기능: 체크섬을 포함한 실행 불가능 JSON 형식으로 모델을 원자적으로 저장한다.
  - 메서드 `load(cls, path: str | Path, *, expected_agent: ModelName)` · model.py:248
    - 기능: 크기·스키마·체크섬·AI 종류를 검증한 뒤 모델을 불러온다.
- **함수 `_payload_checksum(payload: dict[str, Any])`** · model.py:317
  - 기능: `_payload_checksum`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_signed_artifact(artifact: LocalModelArtifact)`** · model.py:327
  - 기능: `_signed_artifact`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_fit(x: np.ndarray, y: np.ndarray, *, iterations: int, learning_rate: float, l2: float)`** · model.py:335
  - 기능: `_fit`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_validate_training_data(x: np.ndarray, y: np.ndarray, feature_names: tuple[str, ...])`** · model.py:355
  - 기능: `_validate_training_data`은(는) 입력 또는 현재 상태가 규칙을 만족하는지 검증합니다.
- **함수 `_metrics(probabilities: np.ndarray, labels: np.ndarray)`** · model.py:370
  - 기능: `_metrics`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_expected_calibration_error(probabilities: np.ndarray, labels: np.ndarray, bins: int=10)`** · model.py:396
  - 기능: `_expected_calibration_error`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_roc_auc(probabilities: np.ndarray, labels: np.ndarray)`** · model.py:420
  - 기능: `_roc_auc`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_validation_split(rows: int, validation_start: int | None)`** · model.py:446
  - 기능: `_validation_split`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_sigmoid(value)`** · model.py:455
  - 기능: `_sigmoid`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/local_ai/news_api.py`

직접 학습 AI의 특성·모델·품질·실행을 담당합니다.

- **클래스 `NewsApiClient`** · news_api.py:41
  - 기능: 외부 서비스의 인증·요청·응답 검증을 캡슐화하는 client입니다.
  - 메서드 `__init__(self, *, api_key: str, base_url: str='https://newsapi.org/v2', timeout_seconds: float=30.0, cache_seconds: float=900.0, daily_request_limit: int=90)` · news_api.py:44
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `articles(self, symbol: str, *, start: date, end: date)` · news_api.py:63
    - 기능: `articles`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `latest_features(self, symbol: str)` · news_api.py:89
    - 기능: `latest_features`은(는) 필요한 데이터를 조회해 반환합니다.
  - 메서드 `close(self)` · news_api.py:103
    - 기능: `close`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/local_ai/news_features.py`

직접 학습 AI의 특성·모델·품질·실행을 담당합니다.

- **함수 `latest_news_features(articles: list[dict])`** · news_features.py:37
  - 기능: `latest_news_features`은(는) 필요한 데이터를 조회해 반환합니다.
- **함수 `build_news_training_rows(articles: list[dict], candles: list[Candle], *, horizon_days: int=3, minimum_articles: int=0, minimum_absolute_excess_return: float=0.0, benchmark_candles: list[Candle] | None=None)`** · news_features.py:43
  - 기능: `build_news_training_rows`은(는) 입력 값과 설정을 결합해 새 결과 객체를 생성합니다.
- **함수 `_benchmark_return(closes: dict[date, float], start: date, end: date)`** · news_features.py:115
  - 기능: `_benchmark_return`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_features_for_date(articles: list[dict], reference_date: date)`** · news_features.py:127
  - 기능: `_features_for_date`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_published_date(article: dict)`** · news_features.py:163
  - 기능: `_published_date`은(는) 연결 또는 메시지 전달 생명주기를 관리합니다.

### `backend/app/local_ai/quality.py`

직접 학습 AI의 특성·모델·품질·실행을 담당합니다.

- **클래스 `QualityAssessment`** · quality.py:22
  - 기능: `QualityAssessment` 관련 상태와 동작을 하나의 객체로 묶습니다.
- **함수 `assess_model_quality(model: ModelName, metrics: dict[str, float])`** · quality.py:29
  - 기능: `assess_model_quality`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `quality_evidence(metrics: dict[str, float], assessment: QualityAssessment)`** · quality.py:70
  - 기능: `quality_evidence`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/local_ai/runtime.py`

직접 학습 AI의 특성·모델·품질·실행을 담당합니다.

- **클래스 `LocalAnalysisRuntime`** · runtime.py:37
  - 기능: 외부 AI API 없이 직접 학습한 전문 모델을 실행하고 최종 진단을 조합한다.
  - 메서드 `__init__(self, artifact_dir: str | Path, flow_feature_loader: Callable[[str], dict[str, float] | None] | None=None, financial_feature_loader: Callable[[str], dict[str, float] | None] | None=None, news_feature_loader: Callable[[str], dict[str, float] | None] | None=None, macro_feature_loader: Callable[[], dict[str, float] | None] | None=None)` · runtime.py:40
    - 기능: 모델 경로와 전문 AI별 최신 특성 공급 함수를 등록한다.
  - 메서드 `analyze(self, facts: dict, *, symbol: str | None=None)` · runtime.py:56
    - 기능: 종목 facts를 전문 AI 5개에 전달하고 각 모델의 상태와 진단 결과를 반환한다.
  - 메서드 `synthesize(self, results: dict[str, dict], *, symbol: str | None=None, stock: dict | None=None, macro_features: dict[str, float] | None=None)` · runtime.py:93
    - 기능: 품질 승인된 전문 AI만 골라 신뢰도 가중 최종 진단을 생성한다.
  - 메서드 `_analyze_one(self, agent: AgentName, facts: dict, *, etf_scope: bool=False, symbol: str | None=None)` · runtime.py:201
    - 기능: 전문 AI 하나의 artifact·특성·품질을 검증하고 사용 가능 상태를 결정한다.
- **함수 `_excluded_evidence(results: dict[str, dict], specialist_names: tuple[AgentName, ...])`** · runtime.py:290
  - 기능: `_excluded_evidence`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/local_ai/sec.py`

직접 학습 AI의 특성·모델·품질·실행을 담당합니다.

- **클래스 `SecCompanyFactsClient`** · sec.py:19
  - 기능: 외부 서비스의 인증·요청·응답 검증을 캡슐화하는 client입니다.
  - 메서드 `__init__(self, *, user_agent: str, base_url: str='https://data.sec.gov', timeout_seconds: float=30.0, cache_seconds: float=3600.0)` · sec.py:22
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `companyfacts(self, symbol: str)` · sec.py:44
    - 기능: `companyfacts`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `cik(self, symbol: str)` · sec.py:60
    - 기능: `cik`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `latest_features(self, symbol: str)` · sec.py:78
    - 기능: `latest_features`은(는) 필요한 데이터를 조회해 반환합니다.
  - 메서드 `latest_annual_valuation_inputs(self, symbol: str)` · sec.py:83
    - 기능: `latest_annual_valuation_inputs`은(는) 필요한 데이터를 조회해 반환합니다.
  - 메서드 `submissions(self, symbol: str)` · sec.py:88
    - 기능: `submissions`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `release_cached_symbol(self, symbol: str)` · sec.py:104
    - 기능: 대량 배치에서 처리가 끝난 종목의 대용량 SEC 응답만 메모리에서 해제한다.
  - 메서드 `close(self)` · sec.py:114
    - 기능: `close`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/local_ai/sec_event_features.py`

직접 학습 AI의 특성·모델·품질·실행을 담당합니다.

- **함수 `extract_8k_events(submissions: dict)`** · sec_event_features.py:23
  - 기능: `extract_8k_events`은(는) 원시 입력을 해석하고 필요한 값을 정규화해 추출합니다.
- **함수 `_items(value: str)`** · sec_event_features.py:86
  - 기능: `_items`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_acceptance_datetime(value: str, filed: date)`** · sec_event_features.py:92
  - 기능: `_acceptance_datetime`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/local_ai/sector_features.py`

직접 학습 AI의 특성·모델·품질·실행을 담당합니다.

- **함수 `sector_etf(symbol: str)`** · sector_features.py:32
  - 기능: `sector_etf`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `latest_sector_features(stock_features: dict[str, float] | None, sector_candles: list[Candle])`** · sector_features.py:38
  - 기능: `latest_sector_features`은(는) 필요한 데이터를 조회해 반환합니다.
- **함수 `sector_features(stock: dict[str, float], sector: dict[str, float])`** · sector_features.py:54
  - 기능: `sector_features`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/main.py`

백엔드 도메인 기능을 구현합니다.

- **함수 `async lifespan(_: FastAPI)`** · main.py:350
  - 기능: `lifespan`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `health()`** · main.py:442
  - 기능: `health`은(는) 서비스와 핵심 의존성의 현재 동작 가능 상태를 반환합니다.
- **함수 `liveness()`** · main.py:449
  - 기능: `liveness`은(는) 서비스와 핵심 의존성의 현재 동작 가능 상태를 반환합니다.
- **함수 `async readiness()`** · main.py:456
  - 기능: `readiness`은(는) 서비스와 핵심 의존성의 현재 동작 가능 상태를 반환합니다.

### `backend/app/models/ai_report.py`

데이터베이스 ORM 모델을 정의합니다.

- **클래스 `AIReportModel`** · ai_report.py:11
  - 기능: 데이터베이스에 저장되는 필드와 관계를 정의하는 ORM 모델입니다.

### `backend/app/models/alerts.py`

데이터베이스 ORM 모델을 정의합니다.

- **클래스 `WatchlistModel`** · alerts.py:13
  - 기능: 데이터베이스에 저장되는 필드와 관계를 정의하는 ORM 모델입니다.
- **클래스 `PriceAlertModel`** · alerts.py:31
  - 기능: 데이터베이스에 저장되는 필드와 관계를 정의하는 ORM 모델입니다.

### `backend/app/models/backtest.py`

데이터베이스 ORM 모델을 정의합니다.

- **클래스 `BacktestRunModel`** · backtest.py:12
  - 기능: 데이터베이스에 저장되는 필드와 관계를 정의하는 ORM 모델입니다.
- **클래스 `BacktestResultModel`** · backtest.py:29
  - 기능: 데이터베이스에 저장되는 필드와 관계를 정의하는 ORM 모델입니다.

### `backend/app/models/content.py`

데이터베이스 ORM 모델을 정의합니다.

- **클래스 `DisclosureModel`** · content.py:11
  - 기능: 데이터베이스에 저장되는 필드와 관계를 정의하는 ORM 모델입니다.
- **클래스 `NewsArticleModel`** · content.py:36
  - 기능: 데이터베이스에 저장되는 필드와 관계를 정의하는 ORM 모델입니다.

### `backend/app/models/corporate_action.py`

데이터베이스 ORM 모델을 정의합니다.

- **클래스 `CorporateActionModel`** · corporate_action.py:23
  - 기능: 데이터베이스에 저장되는 필드와 관계를 정의하는 ORM 모델입니다.
- **클래스 `CorporateActionApprovalModel`** · corporate_action.py:71
  - 기능: 데이터베이스에 저장되는 필드와 관계를 정의하는 ORM 모델입니다.

### `backend/app/models/financial.py`

데이터베이스 ORM 모델을 정의합니다.

- **클래스 `CompanyModel`** · financial.py:12
  - 기능: 데이터베이스에 저장되는 필드와 관계를 정의하는 ORM 모델입니다.
- **클래스 `FinancialModel`** · financial.py:24
  - 기능: 데이터베이스에 저장되는 필드와 관계를 정의하는 ORM 모델입니다.

### `backend/app/models/investor_flow.py`

데이터베이스 ORM 모델을 정의합니다.

- **클래스 `InvestorFlowModel`** · investor_flow.py:12
  - 기능: 데이터베이스에 저장되는 필드와 관계를 정의하는 ORM 모델입니다.

### `backend/app/models/market.py`

데이터베이스 ORM 모델을 정의합니다.

- **클래스 `StockModel`** · market.py:22
  - 기능: 데이터베이스에 저장되는 필드와 관계를 정의하는 ORM 모델입니다.
- **클래스 `StockCandleModel`** · market.py:38
  - 기능: 데이터베이스에 저장되는 필드와 관계를 정의하는 ORM 모델입니다.
- **클래스 `DataQualityLogModel`** · market.py:90
  - 기능: 데이터베이스에 저장되는 필드와 관계를 정의하는 ORM 모델입니다.

### `backend/app/models/paper_trading.py`

데이터베이스 ORM 모델을 정의합니다.

- **클래스 `PaperAccountModel`** · paper_trading.py:12
  - 기능: 개인정보 대신 브라우저가 생성한 UUID로 구분되는 모의 계좌다.
- **클래스 `PaperPositionModel`** · paper_trading.py:26
  - 기능: 종목별 수량과 평균단가를 저장하는 모의 보유 종목이다.
- **클래스 `PaperOrderModel`** · paper_trading.py:50
  - 기능: 중복 요청 방지 키를 포함하는 변경 불가능한 모의 체결 원장이다.

### `backend/app/models/portfolio.py`

데이터베이스 ORM 모델을 정의합니다.

- **클래스 `BrokerAccountModel`** · portfolio.py:12
  - 기능: 데이터베이스에 저장되는 필드와 관계를 정의하는 ORM 모델입니다.
- **클래스 `HoldingModel`** · portfolio.py:32
  - 기능: 데이터베이스에 저장되는 필드와 관계를 정의하는 ORM 모델입니다.

### `backend/app/models/prediction.py`

데이터베이스 ORM 모델을 정의합니다.

- **클래스 `ModelVersionModel`** · prediction.py:12
  - 기능: 데이터베이스에 저장되는 필드와 관계를 정의하는 ORM 모델입니다.
- **클래스 `PredictionModel`** · prediction.py:42
  - 기능: 데이터베이스에 저장되는 필드와 관계를 정의하는 ORM 모델입니다.

### `backend/app/models/provider_audit.py`

데이터베이스 ORM 모델을 정의합니다.

- **클래스 `ProviderAuditLogModel`** · provider_audit.py:11
  - 기능: 데이터베이스에 저장되는 필드와 관계를 정의하는 ORM 모델입니다.

### `backend/app/models/score.py`

데이터베이스 ORM 모델을 정의합니다.

- **클래스 `ScoreWeightModel`** · score.py:11
  - 기능: 데이터베이스에 저장되는 필드와 관계를 정의하는 ORM 모델입니다.

### `backend/app/news/contracts.py`

백엔드 도메인 기능을 구현합니다.

- **클래스 `NewsArticle`** · contracts.py:9
  - 기능: `NewsArticle` 관련 상태와 동작을 하나의 객체로 묶습니다.
- **클래스 `NewsProvider`** · contracts.py:20
  - 기능: `NewsProvider` 구현체가 제공해야 하는 메서드 계약을 정의합니다.
  - 메서드 `latest(self, symbol: str, *, limit: int)` · contracts.py:26
    - 기능: `latest`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `close(self)` · contracts.py:28
    - 기능: `close`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/news/providers.py`

백엔드 도메인 기능을 구현합니다.

- **클래스 `MockNewsProvider`** · providers.py:15
  - 기능: 외부 또는 모의 데이터 원천을 동일한 계약으로 제공하는 구현체입니다.
  - 메서드 `latest(self, symbol: str, *, limit: int)` · providers.py:20
    - 기능: `latest`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **클래스 `RssNewsProvider`** · providers.py:45
  - 기능: 외부 또는 모의 데이터 원천을 동일한 계약으로 제공하는 구현체입니다.
  - 메서드 `__init__(self, client: httpx2.Client, search_url: str)` · providers.py:50
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `create(cls, *, search_url: str, timeout_seconds: float=10, transport: httpx2.BaseTransport | None=None)` · providers.py:57
    - 기능: `create`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `latest(self, symbol: str, *, limit: int)` · providers.py:68
    - 기능: `latest`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `close(self)` · providers.py:98
    - 기능: `close`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `build_news_provider(settings: Settings)`** · providers.py:104
  - 기능: `build_news_provider`은(는) 입력 값과 설정을 결합해 새 결과 객체를 생성합니다.
- **함수 `_text(item: ElementTree.Element, name: str)`** · providers.py:115
  - 기능: `_text`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_published_at(value: str)`** · providers.py:121
  - 기능: `_published_at`은(는) 연결 또는 메시지 전달 생명주기를 관리합니다.

### `backend/app/observability/health.py`

백엔드 도메인 기능을 구현합니다.

- **클래스 `DependencySpec`** · health.py:19
  - 기능: `DependencySpec` 관련 상태와 동작을 하나의 객체로 묶습니다.
- **클래스 `DependencyStatus`** · health.py:28
  - 기능: `DependencyStatus` 관련 상태와 동작을 하나의 객체로 묶습니다.
- **클래스 `HealthService`** · health.py:37
  - 기능: 사용 사례의 처리 순서와 하위 의존성 호출을 조율하는 서비스입니다.
  - 메서드 `__init__(self, dependencies: list[DependencySpec], timeout_seconds: float=2.0)` · health.py:40
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `async readiness(self)` · health.py:46
    - 기능: `readiness`은(는) 서비스와 핵심 의존성의 현재 동작 가능 상태를 반환합니다.
- **함수 `build_health_service(settings: Settings, sessions: sessionmaker[Session] | None)`** · health.py:87
  - 기능: `build_health_service`은(는) 입력 값과 설정을 결합해 새 결과 객체를 생성합니다.

### `backend/app/observability/logging.py`

백엔드 도메인 기능을 구현합니다.

- **함수 `configure_logging(level_name: str='INFO', output_format: Literal['json', 'console']='json')`** · logging.py:9
  - 기능: `configure_logging`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/observability/metrics.py`

백엔드 도메인 기능을 구현합니다.

- **함수 `metrics_app()`** · metrics.py:31
  - 기능: `metrics_app`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `record_dependency(name: str, ready: bool)`** · metrics.py:37
  - 기능: `record_dependency`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **클래스 `MetricsMiddleware`** · metrics.py:43
  - 기능: 요청과 응답 사이에서 공통 정책을 적용하는 미들웨어입니다.
  - 메서드 `async dispatch(self, request: Request, call_next)` · metrics.py:46
    - 기능: `dispatch`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/observability/sentry.py`

백엔드 도메인 기능을 구현합니다.

- **함수 `scrub_sensitive_data(event: dict[str, Any], _hint: dict[str, Any])`** · sentry.py:12
  - 기능: `scrub_sensitive_data`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `configure_sentry(settings: Settings)`** · sentry.py:28
  - 기능: `configure_sentry`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/paper_trading/contracts.py`

백엔드 도메인 기능을 구현합니다.

- **클래스 `PaperTradingError`** · contracts.py:8
  - 기능: 사용자에게 안전하게 전달할 수 있는 모의투자 도메인 오류다.
- **클래스 `InsufficientPaperCashError`** · contracts.py:12
  - 기능: 주문 금액과 수수료를 지불할 모의 현금이 부족할 때 발생한다.
- **클래스 `InsufficientPaperPositionError`** · contracts.py:16
  - 기능: 공매도를 막기 위해 보유 수량보다 큰 매도를 거절할 때 발생한다.
- **클래스 `PaperRiskLimitError`** · contracts.py:20
  - 기능: 모의 매수 후 계좌가 중앙 위험관리 한도를 넘을 때 발생한다.
- **클래스 `PaperAccount`** · contracts.py:25
  - 기능: 브라우저별 모의 계좌의 통화별 현금 상태다.
- **클래스 `PaperPosition`** · contracts.py:38
  - 기능: 평균 매입가와 누적 실현손익을 보존하는 모의 보유 종목이다.
- **클래스 `PaperOrder`** · contracts.py:53
  - 기능: 한 번 체결된 모의 시장가 주문의 변경 불가능한 기록이다.
- **클래스 `PaperFill`** · contracts.py:71
  - 기능: 시세 조회가 끝난 뒤 저장소가 원자적으로 적용할 체결 명령이다.

### `backend/app/paper_trading/risk.py`

백엔드 도메인 기능을 구현합니다.

- **클래스 `PaperRiskPolicy`** · risk.py:18
  - 기능: 과도한 단일 주문, 종목 집중, 현금 소진을 막는 모의투자 한도다.
- **함수 `validate_buy_risk(account: PaperAccount, positions: list[PaperPosition], fill: PaperFill, *, policy: PaperRiskPolicy=DEFAULT_PAPER_RISK_POLICY)`** · risk.py:31
  - 기능: 매수 체결 후 비중을 미리 계산해 중앙 위험한도를 초과하면 거절한다.
- **함수 `summarize_portfolio_risk(account: PaperAccount, positions: list[PaperPosition], currency: str, *, policy: PaperRiskPolicy=DEFAULT_PAPER_RISK_POLICY)`** · risk.py:74
  - 기능: 화면과 API가 함께 사용할 통화별 위험상태와 경고를 계산한다.
- **함수 `_position_values(positions: list[PaperPosition], currency: str)`** · risk.py:115
  - 기능: 최근 저장 가격을 기준으로 해당 통화 포지션의 평가금액을 반환한다.

### `backend/app/patterns/engine.py`

백엔드 도메인 기능을 구현합니다.

- **클래스 `PatternEngine`** · engine.py:13
  - 기능: 입력 데이터로부터 결정론적 결과를 계산하는 엔진입니다.
  - 메서드 `analyze(self, candles: list[Candle])` · engine.py:19
    - 기능: `analyze`은(는) 해당 작업의 전체 처리 흐름을 실행하고 결과를 반환합니다.
  - 메서드 `_validate(candles: list[Candle])` · engine.py:43
    - 기능: `_validate`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `_latest_candlestick_patterns(self, candles: list[Candle])` · engine.py:52
    - 기능: `_latest_candlestick_patterns`은(는) 필요한 데이터를 조회해 반환합니다.
  - 메서드 `_breakout_patterns(self, candles: list[Candle])` · engine.py:161
    - 기능: `_breakout_patterns`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `_reversal_patterns(self, candles: list[Candle])` · engine.py:200
    - 기능: `_reversal_patterns`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `_confirmed_double(self, candles: list[Candle], *, top: bool)` · engine.py:214
    - 기능: `_confirmed_double`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `_local_extrema(candles: list[Candle], *, top: bool)` · engine.py:263
    - 기능: `_local_extrema`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `_extreme_price(candle: Candle, *, top: bool)` · engine.py:277
    - 기능: `_extreme_price`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `_pattern(category: str, name: str, direction: str, confidence: float, first: Candle, last: Candle, evidence: list[str])` · engine.py:283
    - 기능: `_pattern`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/patterns/models.py`

백엔드 도메인 기능을 구현합니다.

- **클래스 `DetectedPattern`** · models.py:8
  - 기능: `DetectedPattern` 관련 상태와 동작을 하나의 객체로 묶습니다.
- **클래스 `PatternAnalysis`** · models.py:21
  - 기능: `PatternAnalysis` 관련 상태와 동작을 하나의 객체로 묶습니다.

### `backend/app/pipeline/candles.py`

원시 시장 데이터를 검증하고 정제합니다.

- **클래스 `CandleInterval`** · candles.py:11
  - 기능: `CandleInterval` 관련 상태와 동작을 하나의 객체로 묶습니다.
- **클래스 `QualitySeverity`** · candles.py:19
  - 기능: `QualitySeverity` 관련 상태와 동작을 하나의 객체로 묶습니다.
- **클래스 `DataQualityLog`** · candles.py:27
  - 기능: `DataQualityLog` 관련 상태와 동작을 하나의 객체로 묶습니다.
- **클래스 `DataQualityLogRecord`** · candles.py:37
  - 기능: 저장하거나 전송할 한 건의 구조화된 데이터를 나타냅니다.
- **클래스 `PipelineResult`** · candles.py:50
  - 기능: 계산 또는 처리 결과를 묶어 전달하는 값 객체입니다.
- **함수 `_business_days_between(start: date, end: date)`** · candles.py:62
  - 기능: `_business_days_between`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_detect_suspicious_daily_gaps(candles: list[Candle])`** · candles.py:74
  - 기능: `_detect_suspicious_daily_gaps`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `validate_candles(candles: list[Candle])`** · candles.py:97
  - 기능: `validate_candles`은(는) 입력 또는 현재 상태가 규칙을 만족하는지 검증합니다.
- **함수 `clean_candles(candles: list[Candle])`** · candles.py:155
  - 기능: `clean_candles`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `aggregate_candles(candles: list[Candle], interval: CandleInterval)`** · candles.py:171
  - 기능: `aggregate_candles`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **클래스 `CandlePipeline`** · candles.py:205
  - 기능: `CandlePipeline` 관련 상태와 동작을 하나의 객체로 묶습니다.
  - 메서드 `process(self, raw_candles: list[Candle], interval: CandleInterval=CandleInterval.DAY)` · candles.py:208
    - 기능: `process`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/portfolio/analysis.py`

백엔드 도메인 기능을 구현합니다.

- **함수 `analyze_portfolio(snapshot: HoldingsSnapshot)`** · analysis.py:10
  - 기능: `analyze_portfolio`은(는) 해당 작업의 전체 처리 흐름을 실행하고 결과를 반환합니다.
- **함수 `_currency_analysis(holdings: list[Holding])`** · analysis.py:38
  - 기능: `_currency_analysis`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/prediction/__init__.py`

예측 엔진과 모델 artifact를 관리합니다.

- **함수 `build_prediction_engine(name: str, artifact_store: ModelArtifactStore | None=None)`** · __init__.py:8
  - 기능: `build_prediction_engine`은(는) 입력 값과 설정을 결합해 새 결과 객체를 생성합니다.
- **함수 `__getattr__(name: str)`** · __init__.py:29
  - 기능: `__getattr__`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/prediction/artifacts.py`

예측 엔진과 모델 artifact를 관리합니다.

- **클래스 `ModelArtifactManifest`** · artifacts.py:22
  - 기능: `ModelArtifactManifest` 관련 상태와 동작을 하나의 객체로 묶습니다.
- **클래스 `ModelArtifactStore`** · artifacts.py:36
  - 기능: `ModelArtifactStore` 관련 상태와 동작을 하나의 객체로 묶습니다.
  - 메서드 `__init__(self, root: str | Path)` · artifacts.py:39
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `stage(self, *, version: str, symbol: str, algorithm: str, horizon_days: int, validation_status: str, validation_metrics: dict[str, float], write_artifact: Callable[[Path], None])` · artifacts.py:47
    - 기능: `stage`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `verify(self, version: str, *, symbol: str | None=None, algorithm: str | None=None, horizon_days: int | None=None)` · artifacts.py:105
    - 기능: `verify`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `activate(self, version: str, *, symbol: str, algorithm: str, horizon_days: int)` · artifacts.py:134
    - 기능: `activate`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `rollback(self, *, symbol: str, algorithm: str, horizon_days: int)` · artifacts.py:164
    - 기능: `rollback`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `current(self, *, symbol: str, algorithm: str, horizon_days: int)` · artifacts.py:201
    - 기능: `current`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `artifact_path(self, manifest: ModelArtifactManifest)` · artifacts.py:225
    - 기능: `artifact_path`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `_pointer_path(self, symbol: str, algorithm: str, horizon_days: int)` · artifacts.py:233
    - 기능: `_pointer_path`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `_assert_scope(manifest: ModelArtifactManifest, symbol: str, algorithm: str, horizon_days: int)` · artifacts.py:242
    - 기능: `_assert_scope`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `_safe_artifact_path(self, directory: Path, relative_name: str)` · artifacts.py:257
    - 기능: `_safe_artifact_path`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `_validate_artifact_file(path: Path)` · artifacts.py:272
    - 기능: `_validate_artifact_file`은(는) 입력 또는 현재 상태가 규칙을 만족하는지 검증합니다.
  - 메서드 `_sha256(path: Path)` · artifacts.py:282
    - 기능: `_sha256`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `_read_manifest(self, path: Path)` · artifacts.py:291
    - 기능: `_read_manifest`은(는) 필요한 데이터를 조회해 반환합니다.
  - 메서드 `_read_json(path: Path)` · artifacts.py:314
    - 기능: `_read_json`은(는) 필요한 데이터를 조회해 반환합니다.
  - 메서드 `_atomic_json_write(path: Path, payload: dict)` · artifacts.py:328
    - 기능: `_atomic_json_write`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `_validate_version(version: str)` · artifacts.py:343
    - 기능: `_validate_version`은(는) 입력 또는 현재 상태가 규칙을 만족하는지 검증합니다.
  - 메서드 `_validate_symbol(symbol: str)` · artifacts.py:351
    - 기능: `_validate_symbol`은(는) 입력 또는 현재 상태가 규칙을 만족하는지 검증합니다.
  - 메서드 `_validate_algorithm(algorithm: str)` · artifacts.py:360
    - 기능: `_validate_algorithm`은(는) 입력 또는 현재 상태가 규칙을 만족하는지 검증합니다.
- **클래스 `ModelArtifactValidationError`** · artifacts.py:369
  - 기능: 해당 실패 조건을 호출 계층에 구분해 전달하는 예외입니다.

### `backend/app/prediction/contracts.py`

예측 엔진과 모델 artifact를 관리합니다.

- **클래스 `PredictionResult`** · contracts.py:12
  - 기능: 계산 또는 처리 결과를 묶어 전달하는 값 객체입니다.
- **클래스 `PredictionEngine`** · contracts.py:26
  - 기능: `PredictionEngine` 구현체가 제공해야 하는 메서드 계약을 정의합니다.
  - 메서드 `predict(self, symbol: str, candles: list[Candle], *, horizon_days: int)` · contracts.py:31
    - 기능: `predict`은(는) 입력 데이터를 기준으로 모델 또는 규칙의 결과 값을 계산해 반환합니다.
- **클래스 `ModelVersionRecord`** · contracts.py:41
  - 기능: 저장하거나 전송할 한 건의 구조화된 데이터를 나타냅니다.

### `backend/app/prediction/engine.py`

예측 엔진과 모델 artifact를 관리합니다.

- **클래스 `XGBoostPredictionEngine`** · engine.py:18
  - 기능: 입력 데이터로부터 결정론적 결과를 계산하는 엔진입니다.
  - 메서드 `__init__(self, artifact_store: ModelArtifactStore | None=None)` · engine.py:23
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `predict(self, symbol: str, candles: list[Candle], *, horizon_days: int)` · engine.py:28
    - 기능: `predict`은(는) 입력 데이터를 기준으로 모델 또는 규칙의 결과 값을 계산해 반환합니다.
  - 메서드 `_new_model()` · engine.py:115
    - 기능: `_new_model`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_decimal(value: float)`** · engine.py:131
  - 기능: `_decimal`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/prediction/features.py`

예측 엔진과 모델 artifact를 관리합니다.

- **클래스 `FeatureDataset`** · features.py:12
  - 기능: `FeatureDataset` 관련 상태와 동작을 하나의 객체로 묶습니다.
- **함수 `build_feature_dataset(candles: list[Candle], horizon_days: int, lookback: int=20)`** · features.py:33
  - 기능: `build_feature_dataset`은(는) 입력 값과 설정을 결합해 새 결과 객체를 생성합니다.
- **함수 `_features_at(close: np.ndarray, volume: np.ndarray, index: int)`** · features.py:59
  - 기능: `_features_at`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/prediction/lightweight.py`

예측 엔진과 모델 artifact를 관리합니다.

- **클래스 `LightweightPredictionEngine`** · lightweight.py:14
  - 기능: 입력 데이터로부터 결정론적 결과를 계산하는 엔진입니다.
  - 메서드 `predict(self, symbol: str, candles: list[Candle], *, horizon_days: int)` · lightweight.py:19
    - 기능: `predict`은(는) 입력 데이터를 기준으로 모델 또는 규칙의 결과 값을 계산해 반환합니다.
- **함수 `_decimal(value: float)`** · lightweight.py:56
  - 기능: `_decimal`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/prediction/validation.py`

예측 엔진과 모델 artifact를 관리합니다.

- **클래스 `PurgedWalkForwardSplit`** · validation.py:8
  - 기능: `PurgedWalkForwardSplit` 관련 상태와 동작을 하나의 객체로 묶습니다.
  - 메서드 `__init__(self, *, horizon_days: int, min_train_size: int=60, n_splits: int=3)` · validation.py:11
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `split(self, sample_count: int)` · validation.py:18
    - 기능: `split`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/providers/__init__.py`

외부 시세 공급자 계약 또는 구현을 담당합니다.

- **함수 `build_providers(settings: Settings, audit_sink: ProviderAuditSink | None=None)`** · __init__.py:9
  - 기능: `build_providers`은(는) 입력 값과 설정을 결합해 새 결과 객체를 생성합니다.

### `backend/app/providers/audit.py`

외부 시세 공급자 계약 또는 구현을 담당합니다.

- **클래스 `ProviderAuditEvent`** · audit.py:9
  - 기능: `ProviderAuditEvent` 관련 상태와 동작을 하나의 객체로 묶습니다.
- **클래스 `ProviderAuditRecord`** · audit.py:27
  - 기능: 저장하거나 전송할 한 건의 구조화된 데이터를 나타냅니다.
- **클래스 `ProviderAuditSink`** · audit.py:45
  - 기능: `ProviderAuditSink` 구현체가 제공해야 하는 메서드 계약을 정의합니다.
  - 메서드 `save(self, event: ProviderAuditEvent)` · audit.py:48
    - 기능: `save`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **클래스 `ProviderAuditReadRepository`** · audit.py:51
  - 기능: `ProviderAuditReadRepository` 구현체가 제공해야 하는 메서드 계약을 정의합니다.
  - 메서드 `list_recent(self, *, limit: int, offset: int, provider: str | None=None, outcome: str | None=None)` · audit.py:54
    - 기능: `list_recent`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **클래스 `ProviderAuditMaintenanceRepository`** · audit.py:64
  - 기능: `ProviderAuditMaintenanceRepository` 구현체가 제공해야 하는 메서드 계약을 정의합니다.
  - 메서드 `delete_before(self, cutoff: datetime)` · audit.py:67
    - 기능: `delete_before`은(는) 대상 데이터나 만료된 상태를 안전하게 제거합니다.

### `backend/app/providers/contracts.py`

외부 시세 공급자 계약 또는 구현을 담당합니다.

- **클래스 `CandlePriceBasisPolicy`** · contracts.py:14
  - 기능: `CandlePriceBasisPolicy` 관련 상태와 동작을 하나의 객체로 묶습니다.
  - 메서드 `__post_init__(self)` · contracts.py:22
    - 기능: `__post_init__`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **클래스 `Capability`** · contracts.py:45
  - 기능: `Capability` 관련 상태와 동작을 하나의 객체로 묶습니다.
- **클래스 `ProviderCapabilities`** · contracts.py:61
  - 기능: `ProviderCapabilities` 관련 상태와 동작을 하나의 객체로 묶습니다.
  - 메서드 `supports(self, capability: Capability)` · contracts.py:75
    - 기능: `supports`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **클래스 `Quote`** · contracts.py:82
  - 기능: `Quote` 관련 상태와 동작을 하나의 객체로 묶습니다.
- **클래스 `Candle`** · contracts.py:96
  - 기능: `Candle` 관련 상태와 동작을 하나의 객체로 묶습니다.
  - 메서드 `__post_init__(self)` · contracts.py:107
    - 기능: `__post_init__`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **클래스 `OrderbookLevel`** · contracts.py:115
  - 기능: `OrderbookLevel` 관련 상태와 동작을 하나의 객체로 묶습니다.
- **클래스 `Trade`** · contracts.py:123
  - 기능: `Trade` 관련 상태와 동작을 하나의 객체로 묶습니다.
- **클래스 `StockInfo`** · contracts.py:134
  - 기능: `StockInfo` 관련 상태와 동작을 하나의 객체로 묶습니다.
- **클래스 `StockWarning`** · contracts.py:146
  - 기능: `StockWarning` 관련 상태와 동작을 하나의 객체로 묶습니다.
- **클래스 `BrokerAccount`** · contracts.py:156
  - 기능: `BrokerAccount` 관련 상태와 동작을 하나의 객체로 묶습니다.
- **클래스 `Holding`** · contracts.py:165
  - 기능: `Holding` 관련 상태와 동작을 하나의 객체로 묶습니다.
- **클래스 `HoldingsSnapshot`** · contracts.py:189
  - 기능: 특정 시점에 관측된 데이터 상태를 변경 없이 전달하는 값 객체입니다.
- **클래스 `StockProvider`** · contracts.py:206
  - 기능: `StockProvider` 구현체가 제공해야 하는 메서드 계약을 정의합니다.
  - 메서드 `get_quote(self, symbol: str)` · contracts.py:214
    - 기능: `get_quote`은(는) 필요한 데이터를 조회해 반환합니다.
  - 메서드 `get_candles(self, symbol: str, limit: int)` · contracts.py:217
    - 기능: `get_candles`은(는) 필요한 데이터를 조회해 반환합니다.
  - 메서드 `get_orderbook(self, symbol: str)` · contracts.py:220
    - 기능: `get_orderbook`은(는) 필요한 데이터를 조회해 반환합니다.
  - 메서드 `get_trades(self, symbol: str, limit: int)` · contracts.py:223
    - 기능: `get_trades`은(는) 필요한 데이터를 조회해 반환합니다.
  - 메서드 `get_stock_info(self, symbol: str)` · contracts.py:226
    - 기능: `get_stock_info`은(는) 필요한 데이터를 조회해 반환합니다.
  - 메서드 `get_warnings(self, symbol: str)` · contracts.py:229
    - 기능: `get_warnings`은(는) 필요한 데이터를 조회해 반환합니다.
  - 메서드 `get_accounts(self)` · contracts.py:231
    - 기능: `get_accounts`은(는) 필요한 데이터를 조회해 반환합니다.
  - 메서드 `get_holdings(self, account_seq: int)` · contracts.py:236
    - 기능: `get_holdings`은(는) 필요한 데이터를 조회해 반환합니다.
  - 메서드 `close(self)` · contracts.py:241
    - 기능: `close`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/providers/errors.py`

외부 시세 공급자 계약 또는 구현을 담당합니다.

- **클래스 `ProviderError`** · errors.py:6
  - 기능: 해당 실패 조건을 호출 계층에 구분해 전달하는 예외입니다.
  - 메서드 `__init__(self, message: str, *, code: str='provider-error', request_id: str | None=None, data: dict[str, Any] | None=None, status_code: int | None=None)` · errors.py:11
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
- **클래스 `ProviderAuthenticationError`** · errors.py:30
  - 기능: 해당 실패 조건을 호출 계층에 구분해 전달하는 예외입니다.
- **클래스 `ProviderForbiddenError`** · errors.py:36
  - 기능: 해당 실패 조건을 호출 계층에 구분해 전달하는 예외입니다.
- **클래스 `ProviderNotFoundError`** · errors.py:42
  - 기능: 해당 실패 조건을 호출 계층에 구분해 전달하는 예외입니다.
- **클래스 `ProviderConflictError`** · errors.py:48
  - 기능: 해당 실패 조건을 호출 계층에 구분해 전달하는 예외입니다.
- **클래스 `ProviderValidationError`** · errors.py:54
  - 기능: 해당 실패 조건을 호출 계층에 구분해 전달하는 예외입니다.
- **클래스 `ProviderRateLimitError`** · errors.py:60
  - 기능: 해당 실패 조건을 호출 계층에 구분해 전달하는 예외입니다.
- **클래스 `ProviderUnavailableError`** · errors.py:66
  - 기능: 해당 실패 조건을 호출 계층에 구분해 전달하는 예외입니다.

### `backend/app/providers/mock.py`

외부 시세 공급자 계약 또는 구현을 담당합니다.

- **클래스 `UnknownSymbolError`** · mock.py:70
  - 기능: 해당 실패 조건을 호출 계층에 구분해 전달하는 예외입니다.
- **클래스 `MockProvider`** · mock.py:74
  - 기능: 외부 또는 모의 데이터 원천을 동일한 계약으로 제공하는 구현체입니다.
  - 메서드 `_stock(self, symbol: str)` · mock.py:97
    - 기능: `_stock`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `_market_currency(symbol: str)` · mock.py:108
    - 기능: `_market_currency`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `get_quote(self, symbol: str)` · mock.py:115
    - 기능: `get_quote`은(는) 필요한 데이터를 조회해 반환합니다.
  - 메서드 `get_candles(self, symbol: str, limit: int=30)` · mock.py:132
    - 기능: `get_candles`은(는) 필요한 데이터를 조회해 반환합니다.
  - 메서드 `get_orderbook(self, symbol: str)` · mock.py:164
    - 기능: `get_orderbook`은(는) 필요한 데이터를 조회해 반환합니다.
  - 메서드 `get_trades(self, symbol: str, limit: int=20)` · mock.py:177
    - 기능: `get_trades`은(는) 필요한 데이터를 조회해 반환합니다.
  - 메서드 `get_stock_info(self, symbol: str)` · mock.py:199
    - 기능: `get_stock_info`은(는) 필요한 데이터를 조회해 반환합니다.
  - 메서드 `get_warnings(self, symbol: str)` · mock.py:213
    - 기능: `get_warnings`은(는) 필요한 데이터를 조회해 반환합니다.
  - 메서드 `get_accounts(self)` · mock.py:219
    - 기능: `get_accounts`은(는) 필요한 데이터를 조회해 반환합니다.
  - 메서드 `get_holdings(self, account_seq: int)` · mock.py:224
    - 기능: `get_holdings`은(는) 필요한 데이터를 조회해 반환합니다.
- **함수 `_mock_holding(quote: Quote, quantity: Decimal, average_price: Decimal, market_country: str)`** · mock.py:238
  - 기능: `_mock_holding`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_snapshot(account_seq: int, holdings: list[Holding])`** · mock.py:272
  - 기능: `_snapshot`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/providers/toss/audit.py`

외부 시세 공급자 계약 또는 구현을 담당합니다.

- **함수 `record_toss_audit(audit_sink: ProviderAuditSink | None, *, method: str, path: str, group: str, outcome: str, status_code: int | None, error_code: str | None, provider_request_id: str | None, internal_request_id: str, attempt_count: int, started_at: float, occurred_at: datetime)`** · audit.py:15
  - 기능: `record_toss_audit`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `extract_provider_request_id(payload: Mapping[str, Any], headers: Mapping[str, str])`** · audit.py:65
  - 기능: `extract_provider_request_id`은(는) 원시 입력을 해석하고 필요한 값을 정규화해 추출합니다.
- **함수 `bounded_text(value: str | None)`** · audit.py:81
  - 기능: `bounded_text`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/providers/toss/auth.py`

외부 시세 공급자 계약 또는 구현을 담당합니다.

- **클래스 `AccessToken`** · auth.py:23
  - 기능: `AccessToken` 관련 상태와 동작을 하나의 객체로 묶습니다.
- **클래스 `TokenCache`** · auth.py:30
  - 기능: `TokenCache` 구현체가 제공해야 하는 메서드 계약을 정의합니다.
  - 메서드 `get(self, key: str)` · auth.py:33
    - 기능: `get`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `set(self, key: str, token: AccessToken)` · auth.py:35
    - 기능: `set`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `delete(self, key: str, expected_value: str | None=None)` · auth.py:37
    - 기능: `delete`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `issue_lock(self, key: str)` · auth.py:39
    - 기능: `issue_lock`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **클래스 `InMemoryTokenCache`** · auth.py:42
  - 기능: `InMemoryTokenCache` 관련 상태와 동작을 하나의 객체로 묶습니다.
  - 메서드 `__init__(self)` · auth.py:45
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `get(self, key: str)` · auth.py:50
    - 기능: `get`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `set(self, key: str, token: AccessToken)` · auth.py:55
    - 기능: `set`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `delete(self, key: str, expected_value: str | None=None)` · auth.py:60
    - 기능: `delete`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `issue_lock(self, key: str)` · auth.py:68
    - 기능: `issue_lock`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **클래스 `RedisTokenCache`** · auth.py:75
  - 기능: `RedisTokenCache` 관련 상태와 동작을 하나의 객체로 묶습니다.
  - 메서드 `__init__(self, redis_url: str, *, clock=time.time)` · auth.py:78
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `get(self, key: str)` · auth.py:85
    - 기능: `get`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `set(self, key: str, token: AccessToken)` · auth.py:99
    - 기능: `set`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `delete(self, key: str, expected_value: str | None=None)` · auth.py:109
    - 기능: `delete`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `issue_lock(self, key: str)` · auth.py:128
    - 기능: `issue_lock`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **클래스 `TossTokenManager`** · auth.py:151
  - 기능: `TossTokenManager` 관련 상태와 동작을 하나의 객체로 묶습니다.
  - 메서드 `__init__(self, client: httpx2.Client, limiter: TossRateLimiter, *, client_id: str, client_secret: str, cache: TokenCache | None=None, clock=time.time, audit_sink: ProviderAuditSink | None=None)` · auth.py:154
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `get(self)` · auth.py:177
    - 기능: `get`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `invalidate(self, expected_token: str | None=None)` · auth.py:190
    - 기능: `invalidate`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `_usable(self, token: AccessToken | None)` · auth.py:195
    - 기능: `_usable`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `_issue(self)` · auth.py:200
    - 기능: `_issue`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `_record_audit(self, *, outcome: str, status_code: int | None, error_code: str | None, provider_request_id: str | None, internal_request_id: str, started_at: float, occurred_at: datetime)` · auth.py:299
    - 기능: `_record_audit`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_json_object(response: httpx2.Response)`** · auth.py:328
  - 기능: `_json_object`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/providers/toss/client.py`

외부 시세 공급자 계약 또는 구현을 담당합니다.

- **클래스 `TossApiClient`** · client.py:27
  - 기능: 외부 서비스의 인증·요청·응답 검증을 캡슐화하는 client입니다.
  - 메서드 `__init__(self, http: httpx2.Client, tokens: TossTokenManager, limiter: TossRateLimiter, *, max_retries: int=3, sleep: Callable[[float], None]=time.sleep, audit_sink: ProviderAuditSink | None=None)` · client.py:30
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `get(self, path: str, *, group: str, params: dict[str, Any] | None=None, account_seq: int | None=None)` · client.py:49
    - 기능: `get`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `access_token(self)` · client.py:61
    - 기능: 서버 내부 WebSocket 연결이 REST와 같은 OAuth 토큰을 재사용하게 한다.
  - 메서드 `request(self, method: str, path: str, *, group: str, params: dict[str, Any] | None=None, json: dict[str, Any] | None=None, account_seq: int | None=None)` · client.py:65
    - 기능: `request`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `_record_audit(self, *, method: str, path: str, group: str, outcome: str, status_code: int | None, error_code: str | None, provider_request_id: str | None, internal_request_id: str, attempt_count: int, started_at: float, occurred_at: datetime)` · client.py:171
    - 기능: `_record_audit`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `close(self)` · client.py:203
    - 기능: `close`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_json_object(response: httpx2.Response)`** · client.py:209
  - 기능: `_json_object`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_map_error(status_code: int, payload: dict[str, Any], headers: httpx2.Headers)`** · client.py:221
  - 기능: `_map_error`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_extract_request_id(payload: dict[str, Any], headers: httpx2.Headers)`** · client.py:256
  - 기능: `_extract_request_id`은(는) 원시 입력을 해석하고 필요한 값을 정규화해 추출합니다.

### `backend/app/providers/toss/provider.py`

외부 시세 공급자 계약 또는 구현을 담당합니다.

- **클래스 `TossProvider`** · provider.py:30
  - 기능: 외부 또는 모의 데이터 원천을 동일한 계약으로 제공하는 구현체입니다.
  - 메서드 `__init__(self, api: TossApiClient)` · provider.py:54
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `create(cls, *, base_url: str, client_id: str, client_secret: str, timeout_seconds: float=10, max_retries: int=3, token_cache: TokenCache | None=None, transport: httpx2.BaseTransport | None=None, audit_sink: ProviderAuditSink | None=None)` · provider.py:61
    - 기능: `create`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `get_quote(self, symbol: str)` · provider.py:100
    - 기능: `get_quote`은(는) 필요한 데이터를 조회해 반환합니다.
  - 메서드 `get_candles(self, symbol: str, limit: int=30)` · provider.py:120
    - 기능: `get_candles`은(는) 필요한 데이터를 조회해 반환합니다.
  - 메서드 `get_orderbook(self, symbol: str)` · provider.py:152
    - 기능: `get_orderbook`은(는) 필요한 데이터를 조회해 반환합니다.
  - 메서드 `get_trades(self, symbol: str, limit: int=20)` · provider.py:159
    - 기능: `get_trades`은(는) 필요한 데이터를 조회해 반환합니다.
  - 메서드 `get_stock_info(self, symbol: str)` · provider.py:180
    - 기능: `get_stock_info`은(는) 필요한 데이터를 조회해 반환합니다.
  - 메서드 `get_warnings(self, symbol: str)` · provider.py:204
    - 기능: `get_warnings`은(는) 필요한 데이터를 조회해 반환합니다.
  - 메서드 `get_accounts(self)` · provider.py:218
    - 기능: `get_accounts`은(는) 필요한 데이터를 조회해 반환합니다.
  - 메서드 `websocket_access_token(self)` · provider.py:224
    - 기능: 토큰 값을 브라우저에 노출하지 않고 서버 실시간 연결에만 제공한다.
  - 메서드 `get_holdings(self, account_seq: int)` · provider.py:228
    - 기능: `get_holdings`은(는) 필요한 데이터를 조회해 반환합니다.
  - 메서드 `list_stocks(self, market: str, *, status: str='ACTIVE', security_type: str | None=None, common_share: bool | None=None)` · provider.py:235
    - 기능: 전체 종목 원장에서 시장별 종목을 조회한다.
  - 메서드 `get_price_limit(self, symbol: str)` · provider.py:252
    - 기능: 당일 상·하한가와 가격 제한 여부를 조회한다.
  - 메서드 `get_exchange_rate(self, base_currency: str='USD', quote_currency: str='KRW')` · provider.py:261
    - 기능: 해외주식 원화 환산에 사용하는 참고 환율을 조회한다.
  - 메서드 `get_market_calendar(self, country: str, target_date: date | None=None)` · provider.py:274
    - 기능: 한국 또는 미국 시장의 장 운영 시간과 휴장 여부를 조회한다.
  - 메서드 `get_rankings(self, *, ranking_type: str, market_country: str, duration: str, count: int=10, exclude_investment_caution: bool=True)` · provider.py:287
    - 기능: 거래대금·거래량·상승·하락 종목 순위를 조회한다.
  - 메서드 `get_market_indicator_prices(self, symbols: list[str])` · provider.py:310
    - 기능: 코스피·코스닥과 한국 국채 금리의 현재 값을 조회한다.
  - 메서드 `get_market_indicator_candles(self, symbol: str, *, interval: str='1d', count: int=30)` · provider.py:319
    - 기능: 시장 지수 또는 국채 금리의 시계열을 조회한다.
  - 메서드 `get_market_indicator_investor_trading(self, symbol: str, *, interval: str='1d', count: int=10)` · provider.py:334
    - 기능: 코스피·코스닥의 투자자별 매매대금 흐름을 조회한다.
  - 메서드 `get_stock_trading_trend(self, symbol: str, trend: str, *, count: int=20)` · provider.py:349
    - 기능: 국내 종목의 수급·프로그램·공매도·신용·대차 추이를 조회한다.
  - 메서드 `get_buying_power(self, account_seq: int, currency: str)` · provider.py:373
    - 기능: 실제 주문 전에 현금 기반 매수 가능 금액을 조회한다.
  - 메서드 `get_sellable_quantity(self, account_seq: int, symbol: str)` · provider.py:383
    - 기능: 계좌에서 현재 매도 가능한 종목 수량을 조회한다.
  - 메서드 `get_commissions(self, account_seq: int)` · provider.py:393
    - 기능: 계좌에 적용되는 국내·미국 시장 수수료를 조회한다.
  - 메서드 `get_orders(self, account_seq: int, *, status: str, symbol: str | None=None, limit: int=20)` · provider.py:402
    - 기능: 진행 중이거나 종료된 실제 주문 목록을 조회한다.
  - 메서드 `get_order(self, account_seq: int, order_id: str)` · provider.py:422
    - 기능: 실제 주문 한 건의 상태와 부분 체결 내역을 조회한다.
  - 메서드 `create_order(self, account_seq: int, order: dict[str, Any])` · provider.py:431
    - 기능: 검증된 실제 주문 요청을 토스에 전달한다.
  - 메서드 `modify_order(self, account_seq: int, order_id: str, changes: dict[str, Any])` · provider.py:442
    - 기능: 미체결 실제 주문의 가격 또는 수량을 정정한다.
  - 메서드 `cancel_order(self, account_seq: int, order_id: str)` · provider.py:455
    - 기능: 미체결 실제 주문을 취소한다.
  - 메서드 `get_conditional_orders(self, account_seq: int, *, status: str, symbol: str | None=None, limit: int=20)` · provider.py:466
    - 기능: 진행 중이거나 종료된 조건주문 목록을 조회한다.
  - 메서드 `get_conditional_order(self, account_seq: int, conditional_order_id: str)` · provider.py:486
    - 기능: 조건주문 한 건의 감시·체결 상태를 조회한다.
  - 메서드 `create_conditional_order(self, account_seq: int, order: dict[str, Any])` · provider.py:497
    - 기능: 검증된 실제 조건주문을 등록한다.
  - 메서드 `modify_conditional_order(self, account_seq: int, conditional_order_id: str, changes: dict[str, Any])` · provider.py:510
    - 기능: 실제 조건주문의 감시 조건과 주문 조건을 수정한다.
  - 메서드 `cancel_conditional_order(self, account_seq: int, conditional_order_id: str)` · provider.py:526
    - 기능: 아직 종료되지 않은 실제 조건주문을 취소한다.
  - 메서드 `close(self)` · provider.py:538
    - 기능: `close`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_result_list(payload: dict[str, Any])`** · provider.py:544
  - 기능: `_result_list`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_result_object(payload: dict[str, Any])`** · provider.py:555
  - 기능: `_result_object`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_find_symbol(rows: list[dict[str, Any]], symbol: str)`** · provider.py:566
  - 기능: `_find_symbol`은(는) 필요한 데이터를 조회해 반환합니다.
- **함수 `_candle(row: dict[str, Any])`** · provider.py:575
  - 기능: `_candle`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_levels(result: dict[str, Any], key: str)`** · provider.py:589
  - 기능: `_levels`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_decimal(row: dict[str, Any], key: str)`** · provider.py:607
  - 기능: `_decimal`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_integer_decimal(row: dict[str, Any], key: str)`** · provider.py:619
  - 기능: `_integer_decimal`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_required_datetime(value: Any)`** · provider.py:631
  - 기능: `_required_datetime`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_optional_datetime(value: Any)`** · provider.py:642
  - 기능: `_optional_datetime`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_optional_date(value: Any)`** · provider.py:658
  - 기능: `_optional_date`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_optional_string(value: Any)`** · provider.py:671
  - 기능: `_optional_string`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_broker_account(row: dict[str, Any])`** · provider.py:677
  - 기능: `_broker_account`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_holdings_snapshot(result: dict[str, Any], account_seq: int)`** · provider.py:692
  - 기능: `_holdings_snapshot`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_holding(row: dict[str, Any])`** · provider.py:719
  - 기능: `_holding`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_required_object(row: dict[str, Any], key: str)`** · provider.py:753
  - 기능: `_required_object`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_currency_totals(row: dict[str, Any])`** · provider.py:765
  - 기능: `_currency_totals`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_optional_decimal(row: dict[str, Any], key: str)`** · provider.py:771
  - 기능: `_optional_decimal`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/providers/toss/rate_limit.py`

외부 시세 공급자 계약 또는 구현을 담당합니다.

- **클래스 `_Bucket`** · rate_limit.py:35
  - 기능: `_Bucket` 관련 상태와 동작을 하나의 객체로 묶습니다.
- **클래스 `TossRateLimiter`** · rate_limit.py:44
  - 기능: `TossRateLimiter` 관련 상태와 동작을 하나의 객체로 묶습니다.
  - 메서드 `__init__(self, limits: Mapping[str, float] | None=None, *, monotonic: Callable[[], float]=time.monotonic, sleep: Callable[[float], None]=time.sleep)` · rate_limit.py:47
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `acquire(self, group: str)` · rate_limit.py:65
    - 기능: `acquire`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `observe(self, group: str, headers: Mapping[str, str])` · rate_limit.py:86
    - 기능: `observe`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `effective_rate(self, group: str)` · rate_limit.py:107
    - 기능: `effective_rate`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `retry_delay(self, attempt: int, retry_after: str | None)` · rate_limit.py:120
    - 기능: `retry_delay`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `_bucket(self, group: str)` · rate_limit.py:131
    - 기능: `_bucket`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/realtime/bus.py`

실시간 시세 연결과 메시지 전달을 담당합니다.

- **클래스 `InMemoryQuoteBus`** · bus.py:14
  - 기능: `InMemoryQuoteBus` 관련 상태와 동작을 하나의 객체로 묶습니다.
  - 메서드 `__init__(self)` · bus.py:17
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `async publish(self, symbol: str, message: QuoteMessage)` · bus.py:24
    - 기능: `publish`은(는) 비동기로 연결 또는 메시지 전달 생명주기를 관리합니다.
  - 메서드 `async get_cached(self, symbol: str)` · bus.py:37
    - 기능: `get_cached`은(는) 비동기로 필요한 데이터를 조회해 반환합니다.
  - 메서드 `async listen(self, symbol: str)` · bus.py:43
    - 기능: `listen`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `async close(self)` · bus.py:59
    - 기능: `close`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **클래스 `RedisQuoteBus`** · bus.py:67
  - 기능: `RedisQuoteBus` 관련 상태와 동작을 하나의 객체로 묶습니다.
  - 메서드 `__init__(self, redis_url: str, cache_ttl_seconds: int=3)` · bus.py:70
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `_channel(symbol: str)` · bus.py:77
    - 기능: `_channel`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `_cache_key(cls, symbol: str)` · bus.py:83
    - 기능: `_cache_key`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `async publish(self, symbol: str, message: QuoteMessage)` · bus.py:88
    - 기능: `publish`은(는) 비동기로 연결 또는 메시지 전달 생명주기를 관리합니다.
  - 메서드 `async get_cached(self, symbol: str)` · bus.py:97
    - 기능: `get_cached`은(는) 비동기로 필요한 데이터를 조회해 반환합니다.
  - 메서드 `async listen(self, symbol: str)` · bus.py:106
    - 기능: `listen`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `async close(self)` · bus.py:124
    - 기능: `close`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/realtime/contracts.py`

실시간 시세 연결과 메시지 전달을 담당합니다.

- **클래스 `RealtimeQuoteSource`** · contracts.py:13
  - 기능: `RealtimeQuoteSource` 구현체가 제공해야 하는 메서드 계약을 정의합니다.
  - 메서드 `name(self)` · contracts.py:18
    - 기능: `name`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `async validate(self, symbol: str)` · contracts.py:21
    - 기능: `validate`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `async fetch(self, symbol: str)` · contracts.py:24
    - 기능: `fetch`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **클래스 `StreamingQuoteSource`** · contracts.py:27
  - 기능: `StreamingQuoteSource` 구현체가 제공해야 하는 메서드 계약을 정의합니다.
  - 메서드 `name(self)` · contracts.py:32
    - 기능: `name`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `async start(self, publish: QuotePublisher)` · contracts.py:35
    - 기능: `start`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `async subscribe(self, symbol: str)` · contracts.py:38
    - 기능: `subscribe`은(는) 비동기로 연결 또는 메시지 전달 생명주기를 관리합니다.
  - 메서드 `async unsubscribe(self, symbol: str)` · contracts.py:41
    - 기능: `unsubscribe`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `async stop(self)` · contracts.py:44
    - 기능: `stop`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **클래스 `QuoteBus`** · contracts.py:47
  - 기능: `QuoteBus` 구현체가 제공해야 하는 메서드 계약을 정의합니다.
  - 메서드 `async publish(self, symbol: str, message: QuoteMessage)` · contracts.py:51
    - 기능: `publish`은(는) 비동기로 연결 또는 메시지 전달 생명주기를 관리합니다.
  - 메서드 `async get_cached(self, symbol: str)` · contracts.py:54
    - 기능: `get_cached`은(는) 비동기로 필요한 데이터를 조회해 반환합니다.
  - 메서드 `listen(self, symbol: str)` · contracts.py:57
    - 기능: `listen`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `async close(self)` · contracts.py:60
    - 기능: `close`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **클래스 `RealtimeHub`** · contracts.py:63
  - 기능: `RealtimeHub` 구현체가 제공해야 하는 메서드 계약을 정의합니다.
  - 메서드 `enabled(self)` · contracts.py:67
    - 기능: `enabled`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `source_name(self)` · contracts.py:70
    - 기능: `source_name`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `transport(self)` · contracts.py:73
    - 기능: `transport`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `async start(self)` · contracts.py:75
    - 기능: `start`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `async stop(self)` · contracts.py:77
    - 기능: `stop`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `stream(self, symbol: str)` · contracts.py:79
    - 기능: `stream`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/realtime/factory.py`

실시간 시세 연결과 메시지 전달을 담당합니다.

- **함수 `build_realtime_quote_hub(settings: Settings, broker: BrokerAdapter)`** · factory.py:15
  - 기능: `build_realtime_quote_hub`은(는) 입력 값과 설정을 결합해 새 결과 객체를 생성합니다.

### `backend/app/realtime/hub.py`

실시간 시세 연결과 메시지 전달을 담당합니다.

- **클래스 `RealtimeDisabledError`** · hub.py:24
  - 기능: 해당 실패 조건을 호출 계층에 구분해 전달하는 예외입니다.
- **클래스 `RealtimeCapacityError`** · hub.py:30
  - 기능: 해당 실패 조건을 호출 계층에 구분해 전달하는 예외입니다.
- **클래스 `InvalidRealtimeSymbolError`** · hub.py:36
  - 기능: 해당 실패 조건을 호출 계층에 구분해 전달하는 예외입니다.
- **클래스 `RealtimeQuoteHub`** · hub.py:42
  - 기능: `RealtimeQuoteHub` 관련 상태와 동작을 하나의 객체로 묶습니다.
  - 메서드 `__init__(self, source: RealtimeQuoteSource, bus: QuoteBus, *, enabled: bool, poll_interval_seconds: float=2.0, max_symbols: int=20, max_connections: int=200)` · hub.py:45
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `enabled(self)` · hub.py:68
    - 기능: `enabled`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `source_name(self)` · hub.py:74
    - 기능: `source_name`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `transport(self)` · hub.py:80
    - 기능: `transport`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `async start(self)` · hub.py:85
    - 기능: `start`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `async stop(self)` · hub.py:91
    - 기능: `stop`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `async stream(self, symbol: str)` · hub.py:103
    - 기능: `stream`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `_normalize_symbol(symbol: str)` · hub.py:121
    - 기능: `_normalize_symbol`은(는) 원시 입력을 해석하고 필요한 값을 정규화해 추출합니다.
  - 메서드 `async _register(self, symbol: str)` · hub.py:129
    - 기능: `_register`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `async _unregister(self, symbol: str)` · hub.py:139
    - 기능: `_unregister`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `async _active_symbols(self)` · hub.py:149
    - 기능: `_active_symbols`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `async _poll_loop(self)` · hub.py:158
    - 기능: `_poll_loop`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `async _poll_symbol(self, symbol: str)` · hub.py:172
    - 기능: `_poll_symbol`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `async _publish(self, symbol: str, message: QuoteMessage)` · hub.py:209
    - 기능: `_publish`은(는) 비동기로 연결 또는 메시지 전달 생명주기를 관리합니다.
- **클래스 `StreamingRealtimeQuoteHub`** · hub.py:220
  - 기능: `StreamingRealtimeQuoteHub` 관련 상태와 동작을 하나의 객체로 묶습니다.
  - 메서드 `__init__(self, source: StreamingQuoteSource, bus: QuoteBus, *, enabled: bool, max_symbols: int=40, max_connections: int=200)` · hub.py:223
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `enabled(self)` · hub.py:243
    - 기능: `enabled`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `source_name(self)` · hub.py:249
    - 기능: `source_name`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `transport(self)` · hub.py:255
    - 기능: `transport`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `async start(self)` · hub.py:260
    - 기능: `start`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `async stop(self)` · hub.py:266
    - 기능: `stop`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `async stream(self, symbol: str)` · hub.py:272
    - 기능: `stream`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `async _register(self, symbol: str)` · hub.py:292
    - 기능: `_register`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `async _unregister(self, symbol: str)` · hub.py:304
    - 기능: `_unregister`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `async _on_quote(self, quote: Quote)` · hub.py:315
    - 기능: `_on_quote`은(는) 비동기로 발생한 이벤트 또는 요청 상태 변화를 처리합니다.

### `backend/app/realtime/kis.py`

실시간 시세 연결과 메시지 전달을 담당합니다.

- **클래스 `KISSubscription`** · kis.py:35
  - 기능: `KISSubscription` 관련 상태와 동작을 하나의 객체로 묶습니다.
- **함수 `resolve_subscription(stock: StockInfo)`** · kis.py:45
  - 기능: `resolve_subscription`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `subscription_message(approval_key: str, subscription: KISSubscription, action: str)`** · kis.py:75
  - 기능: `subscription_message`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `parse_realtime_quotes(raw: str, subscriptions: dict[tuple[str, str], KISSubscription])`** · kis.py:96
  - 기능: `parse_realtime_quotes`은(는) 원시 입력을 해석하고 필요한 값을 정규화해 추출합니다.
- **함수 `_find_subscription(tr_id: str, received_key: str, subscriptions: dict[tuple[str, str], KISSubscription])`** · kis.py:137
  - 기능: `_find_subscription`은(는) 필요한 데이터를 조회해 반환합니다.
- **함수 `_domestic_quote(values: list[str], subscription: KISSubscription)`** · kis.py:153
  - 기능: `_domestic_quote`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_overseas_quote(values: list[str], subscription: KISSubscription)`** · kis.py:168
  - 기능: `_overseas_quote`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_decimal(value: str)`** · kis.py:183
  - 기능: `_decimal`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_signed_decimal(value: str, sign_code: str)`** · kis.py:195
  - 기능: `_signed_decimal`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_integer(value: str)`** · kis.py:202
  - 기능: `_integer`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_timestamp(date_value: str, time_value: str, timezone: ZoneInfo)`** · kis.py:208
  - 기능: `_timestamp`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **클래스 `KISStreamingQuoteSource`** · kis.py:218
  - 기능: `KISStreamingQuoteSource` 관련 상태와 동작을 하나의 객체로 묶습니다.
  - 메서드 `__init__(self, *, base_url: str, websocket_url: str, app_key: str, app_secret: str, resolver: StockProvider, timeout_seconds: float=15.0, reconnect_max_seconds: float=30.0, transport: httpx2.AsyncBaseTransport | None=None, connector: Callable[..., Awaitable[ClientConnection]] | None=None)` · kis.py:223
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `diagnostics(self)` · kis.py:264
    - 기능: 키와 원문 응답을 제외한 운영 상태만 반환한다.
  - 메서드 `async start(self, publish: QuotePublisher)` · kis.py:276
    - 기능: `start`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `async subscribe(self, symbol: str)` · kis.py:283
    - 기능: `subscribe`은(는) 비동기로 연결 또는 메시지 전달 생명주기를 관리합니다.
  - 메서드 `async unsubscribe(self, symbol: str)` · kis.py:303
    - 기능: `unsubscribe`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `async stop(self)` · kis.py:317
    - 기능: `stop`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `async get_approval_key(self)` · kis.py:331
    - 기능: `get_approval_key`은(는) 비동기로 필요한 데이터를 조회해 반환합니다.
  - 메서드 `async _run(self)` · kis.py:368
    - 기능: `_run`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `async _send_actions(self, websocket: ClientConnection, approval_key: str)` · kis.py:413
    - 기능: `_send_actions`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `async _send(websocket: ClientConnection, approval_key: str, action: str, subscription: KISSubscription)` · kis.py:421
    - 기능: `_send`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `async _receive(self, websocket: ClientConnection)` · kis.py:432
    - 기능: `_receive`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `async _handle_system_message(websocket: ClientConnection, raw: str)` · kis.py:449
    - 기능: `_handle_system_message`은(는) 비동기로 발생한 이벤트 또는 요청 상태 변화를 처리합니다.
  - 메서드 `_drain_actions(self)` · kis.py:472
    - 기능: `_drain_actions`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/realtime/messages.py`

실시간 시세 연결과 메시지 전달을 담당합니다.

- **함수 `quote_message(quote: Quote, provider: str)`** · messages.py:9
  - 기능: `quote_message`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/realtime/source.py`

실시간 시세 연결과 메시지 전달을 담당합니다.

- **클래스 `PollingQuoteSource`** · source.py:10
  - 기능: `PollingQuoteSource` 관련 상태와 동작을 하나의 객체로 묶습니다.
  - 메서드 `__init__(self, broker: BrokerAdapter)` · source.py:13
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `name(self)` · source.py:19
    - 기능: `name`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `async validate(self, symbol: str)` · source.py:24
    - 기능: `validate`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `async fetch(self, symbol: str)` · source.py:29
    - 기능: `fetch`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/realtime/toss.py`

실시간 시세 연결과 메시지 전달을 담당합니다.

- **함수 `toss_trade_declaration(symbols: set[str], request_id: str='stockpilot-quotes')`** · toss.py:23
  - 기능: 현재 심볼 집합을 KR·US 토픽으로 묶은 full-replace 선언을 만든다.
- **함수 `parse_toss_trade_message(raw: str, names: dict[str, str])`** · toss.py:35
  - 기능: 체결 message 프레임만 Quote로 정규화하고 ack·pong은 무시한다.
- **클래스 `TossStreamingQuoteSource`** · toss.py:71
  - 기능: OAuth 토큰을 서버에만 보관하며 토스 체결 스트림을 자동 재연결한다.
  - 메서드 `__init__(self, provider: TossProvider, *, websocket_url: str, reconnect_max_seconds: float=30.0, connector: Callable[..., Awaitable[ClientConnection]] | None=None)` · toss.py:76
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `async start(self, publish: QuotePublisher)` · toss.py:99
    - 기능: `start`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `async subscribe(self, symbol: str)` · toss.py:106
    - 기능: `subscribe`은(는) 비동기로 연결 또는 메시지 전달 생명주기를 관리합니다.
  - 메서드 `async unsubscribe(self, symbol: str)` · toss.py:125
    - 기능: `unsubscribe`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `async stop(self)` · toss.py:136
    - 기능: `stop`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `async _run(self)` · toss.py:149
    - 기능: `_run`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `async _declare_changes(self, websocket: ClientConnection)` · toss.py:188
    - 기능: `_declare_changes`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `async _receive(self, websocket: ClientConnection)` · toss.py:198
    - 기능: `_receive`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `async _keepalive(websocket: ClientConnection)` · toss.py:223
    - 기능: `_keepalive`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/repositories/backtest.py`

데이터 저장과 조회 경계를 구현합니다.

- **함수 `_json_safe(value: Any)`** · backtest.py:20
  - 기능: `_json_safe`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **클래스 `SqlAlchemyBacktestRepository`** · backtest.py:32
  - 기능: 도메인 객체의 저장·조회 방식을 캡슐화하는 저장소입니다.
  - 메서드 `__init__(self, sessions: sessionmaker[Session])` · backtest.py:35
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `save(self, symbol: str, config: BacktestConfig, result: BacktestResult, *, metadata: dict[str, object] | None=None)` · backtest.py:40
    - 기능: `save`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `list_runs(self, *, limit: int, offset: int, symbol: str | None=None)` · backtest.py:80
    - 기능: `list_runs`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `get_run(self, run_id: str)` · backtest.py:106
    - 기능: `get_run`은(는) 필요한 데이터를 조회해 반환합니다.
  - 메서드 `_summary(run: BacktestRunModel, result: BacktestResultModel)` · backtest.py:128
    - 기능: `_summary`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/repositories/contracts.py`

데이터 저장과 조회 경계를 구현합니다.

- **클래스 `StockRepository`** · contracts.py:24
  - 기능: `StockRepository` 구현체가 제공해야 하는 메서드 계약을 정의합니다.
  - 메서드 `upsert(self, stock: StockInfo)` · contracts.py:28
    - 기능: `upsert`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **클래스 `CandlePriceBasisInventoryRow`** · contracts.py:32
  - 기능: `CandlePriceBasisInventoryRow` 관련 상태와 동작을 하나의 객체로 묶습니다.
- **클래스 `CandlePriceBasisInventory`** · contracts.py:47
  - 기능: `CandlePriceBasisInventory` 관련 상태와 동작을 하나의 객체로 묶습니다.
- **클래스 `CandleRepository`** · contracts.py:58
  - 기능: `CandleRepository` 구현체가 제공해야 하는 메서드 계약을 정의합니다.
  - 메서드 `save_many(self, symbol: str, candles: list[Candle], *, interval: str, stage: str, aggregation_version: str, source_provider: str, price_basis_rule_version: str)` · contracts.py:62
    - 기능: `save_many`은(는) 데이터를 저장하거나 기존 상태에 추가합니다.
  - 메서드 `find(self, symbol: str, *, interval: str, stage: str, limit: int)` · contracts.py:75
    - 기능: `find`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `price_basis_inventory(self, *, symbol: str, limit: int=200)` · contracts.py:78
    - 기능: `price_basis_inventory`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **클래스 `QualityLogRepository`** · contracts.py:86
  - 기능: `QualityLogRepository` 구현체가 제공해야 하는 메서드 계약을 정의합니다.
  - 메서드 `save_many(self, symbol: str, logs: list[DataQualityLog])` · contracts.py:90
    - 기능: `save_many`은(는) 데이터를 저장하거나 기존 상태에 추가합니다.
- **클래스 `CandleIngestionWrite`** · contracts.py:94
  - 기능: `CandleIngestionWrite` 관련 상태와 동작을 하나의 객체로 묶습니다.
- **클래스 `CandleIngestionRepository`** · contracts.py:107
  - 기능: `CandleIngestionRepository` 구현체가 제공해야 하는 메서드 계약을 정의합니다.
  - 메서드 `save(self, batch: CandleIngestionWrite)` · contracts.py:111
    - 기능: `save`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **클래스 `QualityLogReadRepository`** · contracts.py:114
  - 기능: `QualityLogReadRepository` 구현체가 제공해야 하는 메서드 계약을 정의합니다.
  - 메서드 `list_recent(self, *, limit: int, offset: int, symbol: str | None=None, severity: str | None=None)` · contracts.py:118
    - 기능: `list_recent`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **클래스 `BacktestRepository`** · contracts.py:128
  - 기능: `BacktestRepository` 구현체가 제공해야 하는 메서드 계약을 정의합니다.
  - 메서드 `save(self, symbol: str, config: BacktestConfig, result: BacktestResult, *, metadata: dict[str, object] | None=None)` · contracts.py:132
    - 기능: `save`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `list_runs(self, *, limit: int, offset: int, symbol: str | None=None)` · contracts.py:142
    - 기능: `list_runs`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `get_run(self, run_id: str)` · contracts.py:151
    - 기능: `get_run`은(는) 필요한 데이터를 조회해 반환합니다.
- **클래스 `ScoreWeightRepository`** · contracts.py:154
  - 기능: `ScoreWeightRepository` 구현체가 제공해야 하는 메서드 계약을 정의합니다.
  - 메서드 `get_active(self)` · contracts.py:158
    - 기능: `get_active`은(는) 필요한 데이터를 조회해 반환합니다.
  - 메서드 `save(self, weights: ScoreWeights, *, activate: bool=False)` · contracts.py:161
    - 기능: `save`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **클래스 `FinancialRepository`** · contracts.py:164
  - 기능: `FinancialRepository` 구현체가 제공해야 하는 메서드 계약을 정의합니다.
  - 메서드 `save(self, snapshot: FinancialSnapshot, *, source: str)` · contracts.py:168
    - 기능: `save`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **클래스 `DisclosureRepository`** · contracts.py:171
  - 기능: `DisclosureRepository` 구현체가 제공해야 하는 메서드 계약을 정의합니다.
  - 메서드 `save_many(self, disclosures: list[Disclosure], *, source: str)` · contracts.py:175
    - 기능: `save_many`은(는) 데이터를 저장하거나 기존 상태에 추가합니다.
- **클래스 `NewsRepository`** · contracts.py:178
  - 기능: `NewsRepository` 구현체가 제공해야 하는 메서드 계약을 정의합니다.
  - 메서드 `save_many(self, articles: list[NewsArticle], *, source: str)` · contracts.py:182
    - 기능: `save_many`은(는) 데이터를 저장하거나 기존 상태에 추가합니다.
- **클래스 `InvestorFlowRepository`** · contracts.py:185
  - 기능: `InvestorFlowRepository` 구현체가 제공해야 하는 메서드 계약을 정의합니다.
  - 메서드 `save(self, flow: InvestorFlow, *, source: str)` · contracts.py:189
    - 기능: `save`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **클래스 `PredictionRepository`** · contracts.py:192
  - 기능: `PredictionRepository` 구현체가 제공해야 하는 메서드 계약을 정의합니다.
  - 메서드 `save(self, prediction: PredictionResult, *, algorithm: str)` · contracts.py:196
    - 기능: `save`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `list_versions(self, *, limit: int, offset: int, symbol: str | None=None, algorithm: str | None=None, horizon_days: int | None=None)` · contracts.py:199
    - 기능: `list_versions`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `get_version(self, version: str)` · contracts.py:210
    - 기능: `get_version`은(는) 필요한 데이터를 조회해 반환합니다.
  - 메서드 `promote(self, version: str)` · contracts.py:213
    - 기능: `promote`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **클래스 `AIReportRepository`** · contracts.py:216
  - 기능: `AIReportRepository` 구현체가 제공해야 하는 메서드 계약을 정의합니다.
  - 메서드 `save(self, report: dict)` · contracts.py:220
    - 기능: `save`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **클래스 `PortfolioRepository`** · contracts.py:223
  - 기능: `PortfolioRepository` 구현체가 제공해야 하는 메서드 계약을 정의합니다.
  - 메서드 `save_snapshot(self, provider: str, account: BrokerAccount, snapshot: HoldingsSnapshot)` · contracts.py:227
    - 기능: `save_snapshot`은(는) 데이터를 저장하거나 기존 상태에 추가합니다.

### `backend/app/repositories/corporate_action.py`

데이터 저장과 조회 경계를 구현합니다.

- **클래스 `SqlAlchemyCorporateActionRepository`** · corporate_action.py:19
  - 기능: 도메인 객체의 저장·조회 방식을 캡슐화하는 저장소입니다.
  - 메서드 `__init__(self, sessions: sessionmaker[Session])` · corporate_action.py:22
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `save(self, action: CorporateActionRecord)` · corporate_action.py:27
    - 기능: `save`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `save_batch(self, actions: list[CorporateActionRecord])` · corporate_action.py:32
    - 기능: `save_batch`은(는) 데이터를 저장하거나 기존 상태에 추가합니다.
  - 메서드 `list_known(self, symbol: str, *, as_of: datetime)` · corporate_action.py:89
    - 기능: `list_known`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `list_recent(self, *, limit: int, offset: int, symbol: str | None=None, as_of: datetime | None=None)` · corporate_action.py:109
    - 기능: `list_recent`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `_record(model: CorporateActionModel)` · corporate_action.py:142
    - 기능: `_record`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `_same_revision(model: CorporateActionModel, action: CorporateActionRecord)` · corporate_action.py:166
    - 기능: `_same_revision`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `_same_record(left: CorporateActionRecord, right: CorporateActionRecord)` · corporate_action.py:188
    - 기능: `_same_record`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `_canonical(action: CorporateActionRecord)` · corporate_action.py:197
    - 기능: `_canonical`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `_validate(action: CorporateActionRecord)` · corporate_action.py:214
    - 기능: `_validate`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `_require_aware(value: datetime)` · corporate_action.py:227
    - 기능: `_require_aware`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `_aware(value: datetime)` · corporate_action.py:234
    - 기능: `_aware`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/repositories/corporate_action_approval.py`

데이터 저장과 조회 경계를 구현합니다.

- **클래스 `SqlAlchemyCorporateActionApprovalRepository`** · corporate_action_approval.py:25
  - 기능: 도메인 객체의 저장·조회 방식을 캡슐화하는 저장소입니다.
  - 메서드 `__init__(self, sessions: sessionmaker[Session])` · corporate_action_approval.py:28
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `approve(self, action: CorporateActionRecord, evidence: CorporateActionApprovalEvidence)` · corporate_action_approval.py:33
    - 기능: `approve`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `_evidence_hash(action: CorporateActionRecord, evidence: CorporateActionApprovalEvidence)` · corporate_action_approval.py:113
    - 기능: `_evidence_hash`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `_canonical(action: CorporateActionRecord)` · corporate_action_approval.py:139
    - 기능: `_canonical`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `_validate(action: CorporateActionRecord, evidence: CorporateActionApprovalEvidence)` · corporate_action_approval.py:156
    - 기능: `_validate`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/repositories/data_lifecycle.py`

데이터 저장과 조회 경계를 구현합니다.

- **클래스 `SqlAlchemyDataLifecycleRepository`** · data_lifecycle.py:18
  - 기능: 도메인 객체의 저장·조회 방식을 캡슐화하는 저장소입니다.
  - 메서드 `__init__(self, sessions: sessionmaker[Session])` · data_lifecycle.py:21
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `count_before(self, cutoffs: dict[str, datetime])` · data_lifecycle.py:26
    - 기능: `count_before`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `delete_before(self, cutoffs: dict[str, datetime])` · data_lifecycle.py:42
    - 기능: `delete_before`은(는) 대상 데이터나 만료된 상태를 안전하게 제거합니다.
  - 메서드 `_validate_datasets(cutoffs: dict[str, datetime])` · data_lifecycle.py:55
    - 기능: `_validate_datasets`은(는) 입력 또는 현재 상태가 규칙을 만족하는지 검증합니다.

### `backend/app/repositories/memory.py`

데이터 저장과 조회 경계를 구현합니다.

- **클래스 `InMemoryStockRepository`** · memory.py:29
  - 기능: 도메인 객체의 저장·조회 방식을 캡슐화하는 저장소입니다.
  - 메서드 `__init__(self)` · memory.py:32
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `upsert(self, stock: StockInfo)` · memory.py:37
    - 기능: `upsert`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **클래스 `InMemoryCandleRepository`** · memory.py:43
  - 기능: 도메인 객체의 저장·조회 방식을 캡슐화하는 저장소입니다.
  - 메서드 `__init__(self)` · memory.py:46
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `save_many(self, symbol: str, candles: list[Candle], *, interval: str, stage: str, aggregation_version: str, source_provider: str, price_basis_rule_version: str)` · memory.py:53
    - 기능: `save_many`은(는) 데이터를 저장하거나 기존 상태에 추가합니다.
  - 메서드 `find(self, symbol: str, *, interval: str, stage: str, limit: int)` · memory.py:79
    - 기능: `find`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `price_basis_inventory(self, *, symbol: str, limit: int=200)` · memory.py:88
    - 기능: `price_basis_inventory`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **클래스 `InMemoryQualityLogRepository`** · memory.py:142
  - 기능: 도메인 객체의 저장·조회 방식을 캡슐화하는 저장소입니다.
  - 메서드 `__init__(self)` · memory.py:145
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `save_many(self, symbol: str, logs: list[DataQualityLog])` · memory.py:150
    - 기능: `save_many`은(는) 데이터를 저장하거나 기존 상태에 추가합니다.
- **클래스 `InMemoryFinancialRepository`** · memory.py:156
  - 기능: 도메인 객체의 저장·조회 방식을 캡슐화하는 저장소입니다.
  - 메서드 `__init__(self)` · memory.py:159
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `save(self, snapshot: FinancialSnapshot, *, source: str)` · memory.py:164
    - 기능: `save`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **클래스 `InMemoryDisclosureRepository`** · memory.py:172
  - 기능: 도메인 객체의 저장·조회 방식을 캡슐화하는 저장소입니다.
  - 메서드 `__init__(self)` · memory.py:175
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `save_many(self, disclosures: list[Disclosure], *, source: str)` · memory.py:180
    - 기능: `save_many`은(는) 데이터를 저장하거나 기존 상태에 추가합니다.
- **클래스 `InMemoryNewsRepository`** · memory.py:188
  - 기능: 도메인 객체의 저장·조회 방식을 캡슐화하는 저장소입니다.
  - 메서드 `__init__(self)` · memory.py:191
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `save_many(self, articles: list[NewsArticle], *, source: str)` · memory.py:196
    - 기능: `save_many`은(는) 데이터를 저장하거나 기존 상태에 추가합니다.
- **클래스 `InMemoryInvestorFlowRepository`** · memory.py:204
  - 기능: 도메인 객체의 저장·조회 방식을 캡슐화하는 저장소입니다.
  - 메서드 `__init__(self)` · memory.py:207
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `save(self, flow: InvestorFlow, *, source: str)` · memory.py:212
    - 기능: `save`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **클래스 `InMemoryPredictionRepository`** · memory.py:219
  - 기능: 도메인 객체의 저장·조회 방식을 캡슐화하는 저장소입니다.
  - 메서드 `__init__(self)` · memory.py:222
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `save(self, prediction: PredictionResult, *, algorithm: str)` · memory.py:228
    - 기능: `save`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `list_versions(self, *, limit: int, offset: int, symbol: str | None=None, algorithm: str | None=None, horizon_days: int | None=None)` · memory.py:246
    - 기능: `list_versions`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `get_version(self, version: str)` · memory.py:267
    - 기능: `get_version`은(는) 필요한 데이터를 조회해 반환합니다.
  - 메서드 `promote(self, version: str)` · memory.py:272
    - 기능: `promote`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **클래스 `InMemoryAIReportRepository`** · memory.py:295
  - 기능: 도메인 객체의 저장·조회 방식을 캡슐화하는 저장소입니다.
  - 메서드 `__init__(self)` · memory.py:298
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `save(self, report: dict)` · memory.py:303
    - 기능: `save`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **클래스 `InMemoryPortfolioRepository`** · memory.py:309
  - 기능: 도메인 객체의 저장·조회 방식을 캡슐화하는 저장소입니다.
  - 메서드 `__init__(self)` · memory.py:312
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `save_snapshot(self, provider: str, account: BrokerAccount, snapshot: HoldingsSnapshot)` · memory.py:318
    - 기능: `save_snapshot`은(는) 데이터를 저장하거나 기존 상태에 추가합니다.

### `backend/app/repositories/paper_trading.py`

데이터 저장과 조회 경계를 구현합니다.

- **클래스 `PaperTradingRepository`** · paper_trading.py:31
  - 기능: 계좌 생성, 체결, 초기화를 원자적으로 수행하는 저장소 인터페이스다.
  - 메서드 `snapshot(self, account_id: str)` · paper_trading.py:37
    - 기능: `snapshot`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `execute(self, account_id: str, fill: PaperFill)` · paper_trading.py:40
    - 기능: `execute`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `reset(self, account_id: str)` · paper_trading.py:43
    - 기능: `reset`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_new_account(account_id: str, now: datetime)`** · paper_trading.py:46
  - 기능: `_new_account`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_apply_fill(account: PaperAccount, positions: list[PaperPosition], orders: list[PaperOrder], fill: PaperFill)`** · paper_trading.py:52
  - 기능: 수수료, 현금, 평균단가, 실현손익을 한 체결 규칙으로 계산한다.
- **클래스 `InMemoryPaperTradingRepository`** · paper_trading.py:117
  - 기능: 테스트와 비영속 개발 환경에서 스레드 안전하게 동작하는 저장소다.
  - 메서드 `__init__(self)` · paper_trading.py:120
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `snapshot(self, account_id: str)` · paper_trading.py:126
    - 기능: `snapshot`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `execute(self, account_id: str, fill: PaperFill)` · paper_trading.py:132
    - 기능: `execute`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `reset(self, account_id: str)` · paper_trading.py:140
    - 기능: `reset`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **클래스 `SqlAlchemyPaperTradingRepository`** · paper_trading.py:149
  - 기능: Docker/PostgreSQL 환경에서 행 잠금으로 중복·동시 체결을 막는 저장소다.
  - 메서드 `__init__(self, sessions: sessionmaker[Session])` · paper_trading.py:154
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `snapshot(self, account_id: str)` · paper_trading.py:159
    - 기능: `snapshot`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `execute(self, account_id: str, fill: PaperFill)` · paper_trading.py:166
    - 기능: `execute`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `reset(self, account_id: str)` · paper_trading.py:178
    - 기능: `reset`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `_get_or_create(self, session: Session, account_id: str, *, lock: bool=False)` · paper_trading.py:194
    - 기능: `_get_or_create`은(는) 필요한 데이터를 조회해 반환합니다.
  - 메서드 `_read(self, session: Session, model: PaperAccountModel)` · paper_trading.py:209
    - 기능: `_read`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `_write(self, session: Session, model: PaperAccountModel, state)` · paper_trading.py:222
    - 기능: `_write`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/repositories/provider_audit.py`

데이터 저장과 조회 경계를 구현합니다.

- **클래스 `SqlAlchemyProviderAuditRepository`** · provider_audit.py:14
  - 기능: 도메인 객체의 저장·조회 방식을 캡슐화하는 저장소입니다.
  - 메서드 `__init__(self, sessions: sessionmaker[Session])` · provider_audit.py:17
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `save(self, event: ProviderAuditEvent)` · provider_audit.py:22
    - 기능: `save`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `list_recent(self, *, limit: int, offset: int, provider: str | None=None, outcome: str | None=None)` · provider_audit.py:28
    - 기능: `list_recent`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `delete_before(self, cutoff: datetime)` · provider_audit.py:82
    - 기능: `delete_before`은(는) 대상 데이터나 만료된 상태를 안전하게 제거합니다.

### `backend/app/repositories/score.py`

데이터 저장과 조회 경계를 구현합니다.

- **클래스 `SqlAlchemyScoreWeightRepository`** · score.py:11
  - 기능: 도메인 객체의 저장·조회 방식을 캡슐화하는 저장소입니다.
  - 메서드 `__init__(self, sessions: sessionmaker[Session])` · score.py:14
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `get_active(self)` · score.py:19
    - 기능: `get_active`은(는) 필요한 데이터를 조회해 반환합니다.
  - 메서드 `save(self, weights: ScoreWeights, *, activate: bool=False)` · score.py:32
    - 기능: `save`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/repositories/sqlalchemy.py`

데이터 저장과 조회 경계를 구현합니다.

- **함수 `_validate_candle_provenance(source_provider: str, price_basis_rule_version: str)`** · sqlalchemy.py:43
  - 기능: `_validate_candle_provenance`은(는) 입력 또는 현재 상태가 규칙을 만족하는지 검증합니다.
- **함수 `_upsert_stock(session: Session, stock: StockInfo)`** · sqlalchemy.py:55
  - 기능: `_upsert_stock`은(는) 데이터를 저장하거나 기존 상태에 추가합니다.
- **함수 `_save_candles(session: Session, symbol: str, candles: list[Candle], *, interval: str, stage: str, aggregation_version: str, source_provider: str, price_basis_rule_version: str)`** · sqlalchemy.py:69
  - 기능: `_save_candles`은(는) 데이터를 저장하거나 기존 상태에 추가합니다.
- **함수 `_save_quality_logs(session: Session, symbol: str, logs: list[DataQualityLog])`** · sqlalchemy.py:118
  - 기능: `_save_quality_logs`은(는) 데이터를 저장하거나 기존 상태에 추가합니다.
- **클래스 `SqlAlchemyStockRepository`** · sqlalchemy.py:139
  - 기능: 도메인 객체의 저장·조회 방식을 캡슐화하는 저장소입니다.
  - 메서드 `__init__(self, sessions: sessionmaker[Session])` · sqlalchemy.py:142
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `upsert(self, stock: StockInfo)` · sqlalchemy.py:147
    - 기능: `upsert`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **클래스 `SqlAlchemyCandleRepository`** · sqlalchemy.py:154
  - 기능: 도메인 객체의 저장·조회 방식을 캡슐화하는 저장소입니다.
  - 메서드 `__init__(self, sessions: sessionmaker[Session])` · sqlalchemy.py:157
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `save_many(self, symbol: str, candles: list[Candle], *, interval: str, stage: str, aggregation_version: str, source_provider: str, price_basis_rule_version: str)` · sqlalchemy.py:162
    - 기능: `save_many`은(는) 데이터를 저장하거나 기존 상태에 추가합니다.
  - 메서드 `find(self, symbol: str, *, interval: str, stage: str, limit: int)` · sqlalchemy.py:188
    - 기능: `find`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `price_basis_inventory(self, *, symbol: str, limit: int=200)` · sqlalchemy.py:216
    - 기능: `price_basis_inventory`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **클래스 `SqlAlchemyCandleIngestionRepository`** · sqlalchemy.py:309
  - 기능: 도메인 객체의 저장·조회 방식을 캡슐화하는 저장소입니다.
  - 메서드 `__init__(self, sessions: sessionmaker[Session])` · sqlalchemy.py:312
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `save(self, batch: CandleIngestionWrite)` · sqlalchemy.py:317
    - 기능: `save`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `_validate_provenance(batch: CandleIngestionWrite)` · sqlalchemy.py:347
    - 기능: `_validate_provenance`은(는) 입력 또는 현재 상태가 규칙을 만족하는지 검증합니다.
  - 메서드 `_upsert_stock(session: Session, stock: StockInfo)` · sqlalchemy.py:356
    - 기능: `_upsert_stock`은(는) 데이터를 저장하거나 기존 상태에 추가합니다.
  - 메서드 `_save_candles(session: Session, symbol: str, candles: list[Candle], *, interval: str, stage: str, aggregation_version: str, source_provider: str, price_basis_rule_version: str)` · sqlalchemy.py:362
    - 기능: `_save_candles`은(는) 데이터를 저장하거나 기존 상태에 추가합니다.
  - 메서드 `_save_quality_logs(session: Session, symbol: str, logs: list[DataQualityLog])` · sqlalchemy.py:387
    - 기능: `_save_quality_logs`은(는) 데이터를 저장하거나 기존 상태에 추가합니다.
- **클래스 `SqlAlchemyQualityLogRepository`** · sqlalchemy.py:397
  - 기능: 도메인 객체의 저장·조회 방식을 캡슐화하는 저장소입니다.
  - 메서드 `__init__(self, sessions: sessionmaker[Session])` · sqlalchemy.py:400
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `save_many(self, symbol: str, logs: list[DataQualityLog])` · sqlalchemy.py:405
    - 기능: `save_many`은(는) 데이터를 저장하거나 기존 상태에 추가합니다.
  - 메서드 `list_recent(self, *, limit: int, offset: int, symbol: str | None=None, severity: str | None=None)` · sqlalchemy.py:411
    - 기능: `list_recent`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **클래스 `SqlAlchemyFinancialRepository`** · sqlalchemy.py:469
  - 기능: 도메인 객체의 저장·조회 방식을 캡슐화하는 저장소입니다.
  - 메서드 `__init__(self, sessions: sessionmaker[Session])` · sqlalchemy.py:472
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `save(self, snapshot: FinancialSnapshot, *, source: str)` · sqlalchemy.py:477
    - 기능: `save`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **클래스 `SqlAlchemyDisclosureRepository`** · sqlalchemy.py:520
  - 기능: 도메인 객체의 저장·조회 방식을 캡슐화하는 저장소입니다.
  - 메서드 `__init__(self, sessions: sessionmaker[Session])` · sqlalchemy.py:523
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `save_many(self, disclosures: list[Disclosure], *, source: str)` · sqlalchemy.py:528
    - 기능: `save_many`은(는) 데이터를 저장하거나 기존 상태에 추가합니다.
- **클래스 `SqlAlchemyNewsRepository`** · sqlalchemy.py:546
  - 기능: 도메인 객체의 저장·조회 방식을 캡슐화하는 저장소입니다.
  - 메서드 `__init__(self, sessions: sessionmaker[Session])` · sqlalchemy.py:549
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `save_many(self, articles: list[NewsArticle], *, source: str)` · sqlalchemy.py:554
    - 기능: `save_many`은(는) 데이터를 저장하거나 기존 상태에 추가합니다.
- **클래스 `SqlAlchemyInvestorFlowRepository`** · sqlalchemy.py:570
  - 기능: 도메인 객체의 저장·조회 방식을 캡슐화하는 저장소입니다.
  - 메서드 `__init__(self, sessions: sessionmaker[Session])` · sqlalchemy.py:573
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `save(self, flow: InvestorFlow, *, source: str)` · sqlalchemy.py:578
    - 기능: `save`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **클래스 `SqlAlchemyPredictionRepository`** · sqlalchemy.py:597
  - 기능: 도메인 객체의 저장·조회 방식을 캡슐화하는 저장소입니다.
  - 메서드 `__init__(self, sessions: sessionmaker[Session])` · sqlalchemy.py:600
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `save(self, prediction: PredictionResult, *, algorithm: str)` · sqlalchemy.py:605
    - 기능: `save`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `list_versions(self, *, limit: int, offset: int, symbol: str | None=None, algorithm: str | None=None, horizon_days: int | None=None)` · sqlalchemy.py:635
    - 기능: `list_versions`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `get_version(self, version: str)` · sqlalchemy.py:669
    - 기능: `get_version`은(는) 필요한 데이터를 조회해 반환합니다.
  - 메서드 `promote(self, version: str)` · sqlalchemy.py:676
    - 기능: `promote`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **클래스 `SqlAlchemyAIReportRepository`** · sqlalchemy.py:700
  - 기능: 도메인 객체의 저장·조회 방식을 캡슐화하는 저장소입니다.
  - 메서드 `__init__(self, sessions: sessionmaker[Session])` · sqlalchemy.py:703
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `save(self, report: dict)` · sqlalchemy.py:708
    - 기능: `save`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **클래스 `SqlAlchemyPortfolioRepository`** · sqlalchemy.py:730
  - 기능: 도메인 객체의 저장·조회 방식을 캡슐화하는 저장소입니다.
  - 메서드 `__init__(self, sessions: sessionmaker[Session])` · sqlalchemy.py:733
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `save_snapshot(self, provider: str, account: BrokerAccount, snapshot: HoldingsSnapshot)` · sqlalchemy.py:738
    - 기능: `save_snapshot`은(는) 데이터를 저장하거나 기존 상태에 추가합니다.
- **함수 `_mask_account_no(account_no: str)`** · sqlalchemy.py:781
  - 기능: `_mask_account_no`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_model_version_record(model: ModelVersionModel)`** · sqlalchemy.py:788
  - 기능: `_model_version_record`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/scheduler/jobs.py`

백엔드 도메인 기능을 구현합니다.

- **함수 `build_scheduler(settings: Settings, broker: BrokerAdapter, ingestion_service: CandleIngestionService | None=None, partition_service: CandlePartitionMaintenanceService | None=None, provider_audit_service: ProviderAuditMaintenanceService | None=None, data_lifecycle_service: DataLifecycleMaintenanceService | None=None)`** · jobs.py:30
  - 기능: `build_scheduler`은(는) 입력 값과 설정을 결합해 새 결과 객체를 생성합니다.

### `backend/app/score/axes.py`

백엔드 도메인 기능을 구현합니다.

- **함수 `financial_axis(snapshot: dict[str, Any])`** · axes.py:10
  - 기능: `financial_axis`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `news_axis(snapshot: dict[str, Any])`** · axes.py:36
  - 기능: `news_axis`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `disclosure_axis(snapshot: dict[str, Any])`** · axes.py:47
  - 기능: `disclosure_axis`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `investor_flow_axis(snapshot: dict[str, Any])`** · axes.py:59
  - 기능: `investor_flow_axis`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `market_risk_axis(warnings: list[Any])`** · axes.py:79
  - 기능: `market_risk_axis`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `unavailable_axis(message: str)`** · axes.py:96
  - 기능: `unavailable_axis`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_number(value: Any)`** · axes.py:102
  - 기능: `_number`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_average(components: list[float], evidence: list[str], missing: str)`** · axes.py:110
  - 기능: `_average`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_clamp(value: float, lower: float=0, upper: float=100)`** · axes.py:118
  - 기능: `_clamp`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/score/engine.py`

백엔드 도메인 기능을 구현합니다.

- **클래스 `ScoreWeights`** · engine.py:25
  - 기능: `ScoreWeights` 관련 상태와 동작을 하나의 객체로 묶습니다.
  - 메서드 `__post_init__(self)` · engine.py:31
    - 기능: `__post_init__`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_clamp(value: float, lower: float=0, upper: float=100)`** · engine.py:53
  - 기능: `_clamp`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **클래스 `TechnicalScoreCalculator`** · engine.py:59
  - 기능: `TechnicalScoreCalculator` 관련 상태와 동작을 하나의 객체로 묶습니다.
  - 메서드 `calculate(self, candle: Candle, indicators: dict[str, Any])` · engine.py:62
    - 기능: `calculate`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **클래스 `ScoreEngine`** · engine.py:126
  - 기능: 입력 데이터로부터 결정론적 결과를 계산하는 엔진입니다.
  - 메서드 `__init__(self, weights: ScoreWeights=DEFAULT_WEIGHTS)` · engine.py:132
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `aggregate(self, technical: AxisInput, additional_inputs: Mapping[str, AxisInput] | None=None)` · engine.py:137
    - 기능: `aggregate`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/score/models.py`

백엔드 도메인 기능을 구현합니다.

- **클래스 `AxisScore`** · models.py:10
  - 기능: `AxisScore` 관련 상태와 동작을 하나의 객체로 묶습니다.
- **클래스 `ScoreResult`** · models.py:22
  - 기능: 계산 또는 처리 결과를 묶어 전달하는 값 객체입니다.

### `backend/app/score/strategy.py`

백엔드 도메인 기능을 구현합니다.

- **클래스 `TechnicalScoreStrategy`** · strategy.py:14
  - 기능: `TechnicalScoreStrategy` 관련 상태와 동작을 하나의 객체로 묶습니다.
  - 메서드 `__init__(self, threshold: float=65)` · strategy.py:17
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `signals(self, frame: pd.DataFrame)` · strategy.py:28
    - 기능: `signals`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/services/ai_report.py`

애플리케이션 사용 사례와 도메인 호출 순서를 조율합니다.

- **클래스 `AIReportService`** · ai_report.py:22
  - 기능: 사용 사례의 처리 순서와 하위 의존성 호출을 조율하는 서비스입니다.
  - 메서드 `__init__(self, market: MarketDataService, score: ScoreService, prediction: PredictionService, investor_flow: InvestorFlowService, generator: AIReportGenerator, validator: ComplianceValidator, repository: AIReportRepository | None=None, local_ai: LocalAnalysisRuntime | None=None)` · ai_report.py:25
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `report(self, symbol: str, *, horizon_days: int, limit: int)` · ai_report.py:49
    - 기능: `report`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `_collect_facts(self, symbol: str, *, horizon_days: int, limit: int)` · ai_report.py:99
    - 기능: `_collect_facts`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_latest_as_of(facts: dict)`** · ai_report.py:118
  - 기능: `_latest_as_of`은(는) 필요한 데이터를 조회해 반환합니다.
- **함수 `_value(source: dict | None, name: str)`** · ai_report.py:129
  - 기능: `_value`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_confidence(prediction: dict | None)`** · ai_report.py:135
  - 기능: `_confidence`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_required_text(generated: dict, key: str)`** · ai_report.py:147
  - 기능: `_required_text`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_required_text_list(generated: dict, key: str)`** · ai_report.py:156
  - 기능: `_required_text_list`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/services/alerts.py`

애플리케이션 사용 사례와 도메인 호출 순서를 조율합니다.

- **클래스 `ReferenceAlertService`** · alerts.py:15
  - 기능: 사용 사례의 처리 순서와 하위 의존성 호출을 조율하는 서비스입니다.
  - 메서드 `__init__(self, broker: BrokerAdapter, repository: AlertRepository | None)` · alerts.py:18
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `watchlist(self)` · alerts.py:24
    - 기능: `watchlist`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `add_watchlist(self, symbol: str)` · alerts.py:34
    - 기능: `add_watchlist`은(는) 데이터를 저장하거나 기존 상태에 추가합니다.
  - 메서드 `remove_watchlist(self, symbol: str)` · alerts.py:45
    - 기능: `remove_watchlist`은(는) 대상 데이터나 만료된 상태를 안전하게 제거합니다.
  - 메서드 `alerts(self, status: str | None=None)` · alerts.py:51
    - 기능: `alerts`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `create_alert(self, symbol: str, condition: AlertCondition, target_price: Decimal)` · alerts.py:61
    - 기능: `create_alert`은(는) 입력 값과 설정을 결합해 새 결과 객체를 생성합니다.
  - 메서드 `disable_alert(self, alert_id: str)` · alerts.py:82
    - 기능: `disable_alert`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `evaluate_active(self)` · alerts.py:88
    - 기능: `evaluate_active`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `_required_repository(self)` · alerts.py:139
    - 기능: `_required_repository`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **클래스 `AlertPersistenceUnavailableError`** · alerts.py:147
  - 기능: 해당 실패 조건을 호출 계층에 구분해 전달하는 예외입니다.

### `backend/app/services/backtest.py`

애플리케이션 사용 사례와 도메인 호출 순서를 조율합니다.

- **클래스 `BacktestService`** · backtest.py:22
  - 기능: 사용 사례의 처리 순서와 하위 의존성 호출을 조율하는 서비스입니다.
  - 메서드 `__init__(self, broker: BrokerAdapter, engine: BacktestEngine, repository: BacktestRepository | None=None, event_engine: EventDrivenBacktestEngine | None=None, corporate_actions: CorporateActionService | None=None)` · backtest.py:25
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `run(self, *, symbol: str, strategy_name: str, limit: int, fast_period: int, slow_period: int, initial_capital: float, commission_rate: float, tax_rate: float, slippage_rate: float, engine_name: str='vectorized', max_volume_participation: float=1.0, corporate_action_mode: str='none')` · backtest.py:42
    - 기능: `run`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `validate_walk_forward(self, *, symbol: str, strategy_name: str, limit: int, fast_period: int, slow_period: int, initial_capital: float, commission_rate: float, tax_rate: float, slippage_rate: float, engine_name: str, n_splits: int, warmup_candles: int, max_volume_participation: float=1.0, corporate_action_mode: str='none')` · backtest.py:89
    - 기능: `validate_walk_forward`은(는) 입력 또는 현재 상태가 규칙을 만족하는지 검증합니다.
  - 메서드 `compare_engines(self, *, symbol: str, strategy_name: str, limit: int, fast_period: int, slow_period: int, initial_capital: float, commission_rate: float, tax_rate: float, slippage_rate: float, max_volume_participation: float=1.0, corporate_action_mode: str='none')` · backtest.py:136
    - 기능: `compare_engines`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `compare_strategies(self, *, symbol: str, engine_name: str, limit: int, fast_period: int, slow_period: int, initial_capital: float, commission_rate: float, tax_rate: float, slippage_rate: float, max_volume_participation: float=1.0, corporate_action_mode: str='none')` · backtest.py:236
    - 기능: `compare_strategies`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `_comparison_curve(points: list[EquityPoint], initial_capital: float, max_points: int=120)` · backtest.py:334
    - 기능: `_comparison_curve`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `_strategy(strategy_name: str, fast_period: int, slow_period: int)` · backtest.py:358
    - 기능: `_strategy`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `_engine_for(self, engine_name: str)` · backtest.py:369
    - 기능: `_engine_for`은(는) 입력 조건을 지원하는 제공자나 처리 대상을 선택해 반환합니다.
  - 메서드 `_load_candles(self, symbol: str, limit: int, corporate_action_mode: str)` · backtest.py:378
    - 기능: `_load_candles`은(는) 필요한 데이터를 조회해 반환합니다.
  - 메서드 `history(self, *, limit: int, offset: int, symbol: str | None=None)` · backtest.py:446
    - 기능: `history`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `history_detail(self, run_id: str)` · backtest.py:476
    - 기능: `history_detail`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **클래스 `BacktestHistoryUnavailableError`** · backtest.py:487
  - 기능: 해당 실패 조건을 호출 계층에 구분해 전달하는 예외입니다.
- **클래스 `BacktestRunNotFoundError`** · backtest.py:493
  - 기능: 해당 실패 조건을 호출 계층에 구분해 전달하는 예외입니다.

### `backend/app/services/candle_inventory.py`

애플리케이션 사용 사례와 도메인 호출 순서를 조율합니다.

- **클래스 `CandlePriceBasisInventoryService`** · candle_inventory.py:8
  - 기능: 사용 사례의 처리 순서와 하위 의존성 호출을 조율하는 서비스입니다.
  - 메서드 `__init__(self, repository: CandleRepository | None)` · candle_inventory.py:11
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `summarize(self, *, symbol: str, limit: int=200)` · candle_inventory.py:16
    - 기능: `summarize`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `_review_item(item: dict[str, object])` · candle_inventory.py:68
    - 기능: `_review_item`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/services/content.py`

애플리케이션 사용 사례와 도메인 호출 순서를 조율합니다.

- **클래스 `DisclosureAnalysisService`** · content.py:14
  - 기능: 사용 사례의 처리 순서와 하위 의존성 호출을 조율하는 서비스입니다.
  - 메서드 `__init__(self, provider: DisclosureProvider, repository: DisclosureRepository | None=None)` · content.py:17
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `latest(self, symbol: str, *, days: int, limit: int)` · content.py:25
    - 기능: `latest`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **클래스 `NewsAnalysisService`** · content.py:48
  - 기능: 사용 사례의 처리 순서와 하위 의존성 호출을 조율하는 서비스입니다.
  - 메서드 `__init__(self, provider: NewsProvider, repository: NewsRepository | None=None)` · content.py:51
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `latest(self, symbol: str, *, limit: int)` · content.py:57
    - 기능: `latest`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_news_score(article: NewsArticle)`** · content.py:83
  - 기능: `_news_score`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_disclosure_risk(disclosure: Disclosure)`** · content.py:93
  - 기능: `_disclosure_risk`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_contains(text: str, terms: Iterable[str])`** · content.py:99
  - 기능: `_contains`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/services/corporate_actions.py`

애플리케이션 사용 사례와 도메인 호출 순서를 조율합니다.

- **클래스 `CorporateActionService`** · corporate_actions.py:38
  - 기능: 사용 사례의 처리 순서와 하위 의존성 호출을 조율하는 서비스입니다.
  - 메서드 `__init__(self, repository: CorporateActionRepository | None, engine: CorporateActionAdjustmentEngine | None=None, backtest_engine: CorporateActionBacktestAdjustmentEngine | None=None)` · corporate_actions.py:41
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `recent(self, *, limit: int, offset: int, symbol: str | None=None, as_of: datetime | None=None)` · corporate_actions.py:53
    - 기능: `recent`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `adjusted_view(self, symbol: str, candles: list[Candle], *, as_of: datetime)` · corporate_actions.py:95
    - 기능: `adjusted_view`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `backtest_view(self, symbol: str, candles: list[Candle], *, as_of: datetime)` · corporate_actions.py:114
    - 기능: `backtest_view`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `_require_aware(value: datetime)` · corporate_actions.py:132
    - 기능: `_require_aware`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **클래스 `CorporateActionIngestionService`** · corporate_actions.py:139
  - 기능: 사용 사례의 처리 순서와 하위 의존성 호출을 조율하는 서비스입니다.
  - 메서드 `__init__(self, repository: CorporateActionRepository | None, providers: list[CorporateActionProvider] | None=None, source_candidates: tuple[CorporateActionSourceMetadata, ...]=SOURCE_CANDIDATES)` · corporate_actions.py:142
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `status(self)` · corporate_actions.py:159
    - 기능: `status`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `ingest(self, source: str, symbol: str, *, start: datetime, end: datetime, limit: int)` · corporate_actions.py:181
    - 기능: `ingest`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `_require_aware(value: datetime)` · corporate_actions.py:247
    - 기능: `_require_aware`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **클래스 `CorporateActionCandidateService`** · corporate_actions.py:254
  - 기능: 사용 사례의 처리 순서와 하위 의존성 호출을 조율하는 서비스입니다.
  - 메서드 `__init__(self, providers: list[CorporateActionCandidateProvider], reconciler: CorporateActionRevisionReconciler | None=None)` · corporate_actions.py:257
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `status(self)` · corporate_actions.py:272
    - 기능: `status`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `preview(self, source: str, symbol: str, *, start: date, end: date, limit: int)` · corporate_actions.py:290
    - 기능: `preview`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `close(self)` · corporate_actions.py:345
    - 기능: `close`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `_require_aware(value: datetime)` · corporate_actions.py:352
    - 기능: `_require_aware`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **클래스 `CorporateActionApprovalService`** · corporate_actions.py:359
  - 기능: 사용 사례의 처리 순서와 하위 의존성 호출을 조율하는 서비스입니다.
  - 메서드 `__init__(self, repository: CorporateActionApprovalRepository | None, candidate_service: CorporateActionCandidateService, *, enabled: bool=False, exchange_verification: CorporateActionExchangeVerificationService | None=None, clock=None)` · corporate_actions.py:365
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `status(self)` · corporate_actions.py:384
    - 기능: `status`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `approve(self, source: str, symbol: str, *, start: date, end: date, group_hint: str, receipt_no: str, effective_at: datetime, exchange_evidence_url: str, confirmation: str)` · corporate_actions.py:404
    - 기능: `approve`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `_require_aware(value: datetime)` · corporate_actions.py:503
    - 기능: `_require_aware`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `_validate_url(value: str, hosts: frozenset[str])` · corporate_actions.py:510
    - 기능: `_validate_url`은(는) 입력 또는 현재 상태가 규칙을 만족하는지 검증합니다.
  - 메서드 `_validate_filing_url(cls, value: str, receipt_no: str)` · corporate_actions.py:531
    - 기능: `_validate_filing_url`은(는) 입력 또는 현재 상태가 규칙을 만족하는지 검증합니다.

### `backend/app/services/data_lifecycle.py`

애플리케이션 사용 사례와 도메인 호출 순서를 조율합니다.

- **클래스 `DataLifecycleMaintenanceService`** · data_lifecycle.py:12
  - 기능: 사용 사례의 처리 순서와 하위 의존성 호출을 조율하는 서비스입니다.
  - 메서드 `__init__(self, repository: DataLifecycleRepository | None, *, enabled: bool, retention_days: dict[str, int], cleanup_hour_kst: int)` · data_lifecycle.py:15
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `preview(self, now: datetime | None=None)` · data_lifecycle.py:34
    - 기능: `preview`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `cleanup(self, now: datetime | None=None)` · data_lifecycle.py:60
    - 기능: `cleanup`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `status(self)` · data_lifecycle.py:83
    - 기능: `status`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `_cutoffs(self, now: datetime)` · data_lifecycle.py:109
    - 기능: `_cutoffs`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `_aware_now(now: datetime | None)` · data_lifecycle.py:118
    - 기능: `_aware_now`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/services/data_quality.py`

애플리케이션 사용 사례와 도메인 호출 순서를 조율합니다.

- **클래스 `DataQualityHistoryService`** · data_quality.py:8
  - 기능: 사용 사례의 처리 순서와 하위 의존성 호출을 조율하는 서비스입니다.
  - 메서드 `__init__(self, repository: QualityLogReadRepository | None)` · data_quality.py:11
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `recent(self, *, limit: int, offset: int, symbol: str | None=None, severity: str | None=None)` · data_quality.py:16
    - 기능: `recent`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/services/financial.py`

애플리케이션 사용 사례와 도메인 호출 순서를 조율합니다.

- **클래스 `FinancialAnalysisService`** · financial.py:7
  - 기능: 사용 사례의 처리 순서와 하위 의존성 호출을 조율하는 서비스입니다.
  - 메서드 `__init__(self, provider: FinancialProvider, repository: FinancialRepository | None=None)` · financial.py:10
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `snapshot(self, symbol: str, fiscal_year: int, report_code: str='11011')` · financial.py:18
    - 기능: `snapshot`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/services/ingestion.py`

애플리케이션 사용 사례와 도메인 호출 순서를 조율합니다.

- **클래스 `IngestionSummary`** · ingestion.py:20
  - 기능: `IngestionSummary` 관련 상태와 동작을 하나의 객체로 묶습니다.
- **클래스 `CandleIngestionService`** · ingestion.py:34
  - 기능: 사용 사례의 처리 순서와 하위 의존성 호출을 조율하는 서비스입니다.
  - 메서드 `__init__(self, broker: BrokerAdapter, stocks: StockRepository, candles: CandleRepository, quality_logs: QualityLogRepository, pipeline: CandlePipeline | None=None, atomic_repository: CandleIngestionRepository | None=None)` · ingestion.py:37
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `ingest_daily(self, symbol: str, limit: int=120)` · ingestion.py:55
    - 기능: `ingest_daily`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **클래스 `IngestionUnavailableError`** · ingestion.py:118
  - 기능: 해당 실패 조건을 호출 계층에 구분해 전달하는 예외입니다.
- **클래스 `IngestionOperationsService`** · ingestion.py:124
  - 기능: 사용 사례의 처리 순서와 하위 의존성 호출을 조율하는 서비스입니다.
  - 메서드 `__init__(self, settings: Settings, ingestion: CandleIngestionService | None)` · ingestion.py:127
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `status(self)` · ingestion.py:137
    - 기능: `status`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `ingest(self, symbol: str, *, limit: int | None=None)` · ingestion.py:149
    - 기능: `ingest`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/services/investor_flow.py`

애플리케이션 사용 사례와 도메인 호출 순서를 조율합니다.

- **클래스 `InvestorFlowService`** · investor_flow.py:7
  - 기능: 사용 사례의 처리 순서와 하위 의존성 호출을 조율하는 서비스입니다.
  - 메서드 `__init__(self, provider: InvestorFlowProvider, repository: InvestorFlowRepository | None=None)` · investor_flow.py:10
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `snapshot(self, symbol: str)` · investor_flow.py:18
    - 기능: `snapshot`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/services/local_ai_readiness.py`

애플리케이션 사용 사례와 도메인 호출 순서를 조율합니다.

- **클래스 `LocalAiReadinessService`** · local_ai_readiness.py:42
  - 기능: 로컬 AI 파일을 검증하고 관리자용 준비도 요약을 생성한다.
  - 메서드 `__init__(self, artifact_dir: str | Path, *, enabled: bool)` · local_ai_readiness.py:45
    - 기능: 허용된 artifact 루트와 런타임 활성화 상태를 저장한다.
  - 메서드 `summary(self)` · local_ai_readiness.py:51
    - 기능: 모델별 품질 상태와 전체 준비도 통계를 반환한다.
  - 메서드 `_inspect_model(self, model: ModelName, filename: str, label: str)` · local_ai_readiness.py:74
    - 기능: 고정 파일 하나를 체크섬과 품질 기준으로 검사한다.
  - 메서드 `_empty_item(model: ModelName, label: str, scope: str, status: str, reasons: tuple[str, ...])` · local_ai_readiness.py:122
    - 기능: 파일이 없거나 무효일 때 동일한 응답 계약을 만든다.

### `backend/app/services/market.py`

애플리케이션 사용 사례와 도메인 호출 순서를 조율합니다.

- **클래스 `MarketDataService`** · market.py:8
  - 기능: 사용 사례의 처리 순서와 하위 의존성 호출을 조율하는 서비스입니다.
  - 메서드 `__init__(self, broker: BrokerAdapter)` · market.py:11
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `quote(self, symbol: str)` · market.py:17
    - 기능: `quote`은(는) 이름에 해당하는 시장 또는 기업 데이터를 조회해 공통 형식으로 반환합니다.
  - 메서드 `candles(self, symbol: str, limit: int)` · market.py:23
    - 기능: `candles`은(는) 이름에 해당하는 시장 또는 기업 데이터를 조회해 공통 형식으로 반환합니다.
  - 메서드 `orderbook(self, symbol: str)` · market.py:29
    - 기능: `orderbook`은(는) 이름에 해당하는 시장 또는 기업 데이터를 조회해 공통 형식으로 반환합니다.
  - 메서드 `trades(self, symbol: str, limit: int)` · market.py:36
    - 기능: `trades`은(는) 이름에 해당하는 시장 또는 기업 데이터를 조회해 공통 형식으로 반환합니다.
  - 메서드 `stock_info(self, symbol: str)` · market.py:42
    - 기능: `stock_info`은(는) 이름에 해당하는 시장 또는 기업 데이터를 조회해 공통 형식으로 반환합니다.
  - 메서드 `warnings(self, symbol: str)` · market.py:48
    - 기능: `warnings`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `processed_candles(self, symbol: str, limit: int, interval: CandleInterval)` · market.py:54
    - 기능: `processed_candles`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/services/model_registry.py`

애플리케이션 사용 사례와 도메인 호출 순서를 조율합니다.

- **클래스 `ModelRegistryService`** · model_registry.py:9
  - 기능: 사용 사례의 처리 순서와 하위 의존성 호출을 조율하는 서비스입니다.
  - 메서드 `__init__(self, repository: PredictionRepository | None, artifact_store: ModelArtifactStore | None=None)` · model_registry.py:12
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `versions(self, *, limit: int, offset: int, symbol: str | None=None, algorithm: str | None=None, horizon_days: int | None=None)` · model_registry.py:22
    - 기능: `versions`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `promote(self, version: str)` · model_registry.py:58
    - 기능: `promote`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `_required_repository(self)` · model_registry.py:96
    - 기능: `_required_repository`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **클래스 `ModelRegistryUnavailableError`** · model_registry.py:104
  - 기능: 해당 실패 조건을 호출 계층에 구분해 전달하는 예외입니다.
- **클래스 `ModelVersionNotFoundError`** · model_registry.py:110
  - 기능: 해당 실패 조건을 호출 계층에 구분해 전달하는 예외입니다.

### `backend/app/services/operations.py`

애플리케이션 사용 사례와 도메인 호출 순서를 조율합니다.

- **클래스 `OperationsStatusService`** · operations.py:13
  - 기능: 사용 사례의 처리 순서와 하위 의존성 호출을 조율하는 서비스입니다.
  - 메서드 `__init__(self, settings: Settings, health: HealthService, partitions: CandlePartitionMaintenanceService | None=None, provider_audit: ProviderAuditMaintenanceService | None=None, data_lifecycle: DataLifecycleMaintenanceService | None=None)` · operations.py:16
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `async status(self)` · operations.py:32
    - 기능: `status`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/services/paper_trading.py`

애플리케이션 사용 사례와 도메인 호출 순서를 조율합니다.

- **클래스 `PaperTradingService`** · paper_trading.py:16
  - 기능: 검증된 현재가로만 모의 체결하고 통화별 자산을 계산한다.
  - 메서드 `__init__(self, market: MarketDataService, repository: PaperTradingRepository)` · paper_trading.py:19
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `snapshot(self, account_id: str)` · paper_trading.py:25
    - 기능: 보유 종목을 최신 시세로 평가하되 시세 장애 시 마지막 체결가를 사용한다.
  - 메서드 `execute(self, account_id: str, *, symbol: str, side: str, quantity: Decimal, idempotency_key: str)` · paper_trading.py:29
    - 기능: 공급자 종목 메타데이터와 현재가를 조회한 뒤 모의 원장에 한 번만 반영한다.
  - 메서드 `reset(self, account_id: str)` · paper_trading.py:58
    - 기능: 해당 모의 계좌의 보유 종목과 주문 원장만 초기 상태로 되돌린다.
  - 메서드 `_serialize(self, state)` · paper_trading.py:62
    - 기능: `_serialize`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/services/patterns.py`

애플리케이션 사용 사례와 도메인 호출 순서를 조율합니다.

- **클래스 `PatternAnalysisService`** · patterns.py:8
  - 기능: 사용 사례의 처리 순서와 하위 의존성 호출을 조율하는 서비스입니다.
  - 메서드 `__init__(self, broker: BrokerAdapter, engine: PatternEngine)` · patterns.py:11
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `patterns(self, symbol: str, limit: int)` · patterns.py:18
    - 기능: `patterns`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/services/portfolio.py`

애플리케이션 사용 사례와 도메인 호출 순서를 조율합니다.

- **클래스 `PortfolioService`** · portfolio.py:12
  - 기능: 사용 사례의 처리 순서와 하위 의존성 호출을 조율하는 서비스입니다.
  - 메서드 `__init__(self, broker: BrokerAdapter, *, sync_enabled: bool, repository: PortfolioRepository | None=None)` · portfolio.py:15
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `accounts(self)` · portfolio.py:28
    - 기능: `accounts`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `sync(self, account_seq: int)` · portfolio.py:38
    - 기능: `sync`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `_account(accounts: list[BrokerAccount], account_seq: int)` · portfolio.py:60
    - 기능: `_account`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `_require_enabled(self)` · portfolio.py:68
    - 기능: `_require_enabled`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `_account_data(account: BrokerAccount)` · portfolio.py:79
    - 기능: `_account_data`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `_summary(snapshot: HoldingsSnapshot)` · portfolio.py:89
    - 기능: `_summary`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `_holding_data(snapshot: HoldingsSnapshot)` · portfolio.py:105
    - 기능: `_holding_data`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_mask_account_no(account_no: str)`** · portfolio.py:117
  - 기능: `_mask_account_no`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/services/prediction.py`

애플리케이션 사용 사례와 도메인 호출 순서를 조율합니다.

- **클래스 `PredictionService`** · prediction.py:8
  - 기능: 사용 사례의 처리 순서와 하위 의존성 호출을 조율하는 서비스입니다.
  - 메서드 `__init__(self, broker: BrokerAdapter, engine: PredictionEngine, repository: PredictionRepository | None=None)` · prediction.py:11
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `predict(self, symbol: str, *, horizon_days: int, limit: int)` · prediction.py:23
    - 기능: `predict`은(는) 입력 데이터를 기준으로 모델 또는 규칙의 결과 값을 계산해 반환합니다.

### `backend/app/services/provider_audit.py`

애플리케이션 사용 사례와 도메인 호출 순서를 조율합니다.

- **클래스 `ProviderAuditHistoryService`** · provider_audit.py:13
  - 기능: 사용 사례의 처리 순서와 하위 의존성 호출을 조율하는 서비스입니다.
  - 메서드 `__init__(self, repository: ProviderAuditReadRepository | None)` · provider_audit.py:16
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `recent(self, *, limit: int, offset: int, provider: str | None=None, outcome: str | None=None)` · provider_audit.py:21
    - 기능: `recent`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **클래스 `ProviderAuditMaintenanceService`** · provider_audit.py:54
  - 기능: 사용 사례의 처리 순서와 하위 의존성 호출을 조율하는 서비스입니다.
  - 메서드 `__init__(self, repository: ProviderAuditMaintenanceRepository | None, *, enabled: bool, retention_days: int, cleanup_hour_kst: int)` · provider_audit.py:57
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `cleanup(self, now: datetime | None=None)` · provider_audit.py:77
    - 기능: `cleanup`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `status(self)` · provider_audit.py:111
    - 기능: `status`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/services/score.py`

애플리케이션 사용 사례와 도메인 호출 순서를 조율합니다.

- **클래스 `ScoreAnalysisBundle`** · score.py:32
  - 기능: `ScoreAnalysisBundle` 관련 상태와 동작을 하나의 객체로 묶습니다.
- **클래스 `ScoreService`** · score.py:41
  - 기능: 사용 사례의 처리 순서와 하위 의존성 호출을 조율하는 서비스입니다.
  - 메서드 `__init__(self, broker: BrokerAdapter, indicators: IndicatorEngine, technical: TechnicalScoreCalculator, score_engine: ScoreEngine, weights: ScoreWeightRepository | None=None, *, financial: FinancialAnalysisService | None=None, news: NewsAnalysisService | None=None, disclosure: DisclosureAnalysisService | None=None, investor_flow: InvestorFlowService | None=None)` · score.py:44
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `score(self, symbol: str, limit: int)` · score.py:70
    - 기능: `score`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `analysis_bundle(self, symbol: str, limit: int)` · score.py:75
    - 기능: `analysis_bundle`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `_load_source_axis(cls, name: str, loader: Callable[[], Any] | None, calculator: Callable[[Any], AxisInput], source_facts: dict[str, Any], source_status: dict[str, str])` · score.py:145
    - 기능: `_load_source_axis`은(는) 필요한 데이터를 조회해 반환합니다.
  - 메서드 `_load_axis(name: str, loader: Callable[[], AxisInput] | None)` · score.py:175
    - 기능: `_load_axis`은(는) 필요한 데이터를 조회해 반환합니다.

### `backend/app/services/technical.py`

애플리케이션 사용 사례와 도메인 호출 순서를 조율합니다.

- **클래스 `TechnicalAnalysisService`** · technical.py:8
  - 기능: 사용 사례의 처리 순서와 하위 의존성 호출을 조율하는 서비스입니다.
  - 메서드 `__init__(self, broker: BrokerAdapter, engine: IndicatorEngine)` · technical.py:11
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `indicators(self, symbol: str, limit: int)` · technical.py:18
    - 기능: `indicators`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `backend/app/services/toss_open_api.py`

애플리케이션 사용 사례와 도메인 호출 순서를 조율합니다.

- **클래스 `TossOpenApiService`** · toss_open_api.py:29
  - 기능: 공식 토스 Open API를 화면에서 사용하기 좋은 읽기 전용 계약으로 제공한다.
  - 메서드 `__init__(self, provider: TossProvider | None, *, account_access_enabled: bool=False, trading_enabled: bool=False, catalog_ttl_seconds: float=21600)` · toss_open_api.py:32
    - 기능: `__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다.
  - 메서드 `available(self)` · toss_open_api.py:51
    - 기능: `available`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `search_stocks(self, query: str, limit: int=12)` · toss_open_api.py:56
    - 기능: `search_stocks`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `market_overview(self)` · toss_open_api.py:87
    - 기능: `market_overview`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `rankings(self, ranking_type: str, market_country: str, duration: str, count: int)` · toss_open_api.py:128
    - 기능: 공식 랭킹의 지원 조합을 그대로 전달하는 읽기 전용 진입점이다.
  - 메서드 `market_indicator_history(self, symbol: str, *, interval: str, count: int)` · toss_open_api.py:150
    - 기능: 지수·국채 캔들과 지원되는 투자자 매매 흐름을 묶어 반환한다.
  - 메서드 `stock_microstructure(self, symbol: str, trade_limit: int=20)` · toss_open_api.py:180
    - 기능: `stock_microstructure`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `stock_trends(self, symbol: str, count: int=20)` · toss_open_api.py:214
    - 기능: `stock_trends`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `account_workspace(self, account_seq: int, *, symbol: str | None=None, currency: str='KRW')` · toss_open_api.py:237
    - 기능: 보유 자산과 실제 주문 전 확인 정보를 읽기 전용으로 묶는다.
  - 메서드 `order_detail(self, account_seq: int, order_id: str)` · toss_open_api.py:299
    - 기능: 부분 체결을 포함한 실제 주문 한 건을 읽기 전용으로 조회한다.
  - 메서드 `conditional_order_detail(self, account_seq: int, conditional_order_id: str)` · toss_open_api.py:304
    - 기능: 조건 감시 상태를 포함한 조건주문 한 건을 읽기 전용으로 조회한다.
  - 메서드 `submit_order(self, account_seq: int, order: dict[str, Any], *, confirmation: str)` · toss_open_api.py:311
    - 기능: `submit_order`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `modify_order(self, account_seq: int, order_id: str, changes: dict[str, Any], *, confirmation: str)` · toss_open_api.py:323
    - 기능: `modify_order`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `cancel_order(self, account_seq: int, order_id: str, *, confirmation: str)` · toss_open_api.py:336
    - 기능: `cancel_order`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `submit_conditional_order(self, account_seq: int, order: dict[str, Any], *, confirmation: str)` · toss_open_api.py:344
    - 기능: `submit_conditional_order`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `modify_conditional_order(self, account_seq: int, conditional_order_id: str, changes: dict[str, Any], *, confirmation: str)` · toss_open_api.py:356
    - 기능: `modify_conditional_order`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `cancel_conditional_order(self, account_seq: int, conditional_order_id: str, *, confirmation: str)` · toss_open_api.py:369
    - 기능: `cancel_conditional_order`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `_stock_catalog(self)` · toss_open_api.py:381
    - 기능: `_stock_catalog`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `_attempt(name: str, operation: Callable[[], Any], errors: dict[str, dict[str, Any]], fallback: Any)` · toss_open_api.py:418
    - 기능: 복합 화면에서 일부 공급자 오류를 비밀정보 없는 상태값으로 격리한다.
  - 메서드 `_require_provider(self)` · toss_open_api.py:431
    - 기능: `_require_provider`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `_require_account_access(self)` · toss_open_api.py:442
    - 기능: `_require_account_access`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
  - 메서드 `_require_trading(self, confirmation: str)` · toss_open_api.py:454
    - 기능: `_require_trading`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_normalize_search(value: str)`** · toss_open_api.py:473
  - 기능: `_normalize_search`은(는) 원시 입력을 해석하고 필요한 값을 정규화해 추출합니다.

### `backend/app/websocket/routes.py`

백엔드 도메인 기능을 구현합니다.

- **함수 `async _close_with_error(websocket: WebSocket, *, code: int, error_code: str, message: str)`** · routes.py:22
  - 기능: `_close_with_error`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `async quote_stream(websocket: WebSocket, symbol: str)`** · routes.py:44
  - 기능: `quote_stream`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `scripts/ai/data/build_diverse_local_ai_datasets.py`

AI 학습 데이터를 수집·결합·보강합니다.

- **함수 `parse_args()`** · build_diverse_local_ai_datasets.py:65
  - 기능: `parse_args`은(는) 원시 입력을 해석하고 필요한 값을 정규화해 추출합니다.
- **함수 `_read(path: Path)`** · build_diverse_local_ai_datasets.py:79
  - 기능: `_read`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_day(row: dict[str, str])`** · build_diverse_local_ai_datasets.py:89
  - 기능: `_day`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_index(rows: list[dict[str, str]])`** · build_diverse_local_ai_datasets.py:95
  - 기능: `_index`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_latest(index, symbol: str, target: date, *, maximum_age_days: int, strictly_before: bool=False)`** · build_diverse_local_ai_datasets.py:108
  - 기능: `_latest`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_select(row: dict[str, str] | None, fields: tuple[str, ...], prefix: str='')`** · build_diverse_local_ai_datasets.py:132
  - 기능: `_select`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_recent_events(event_index, symbol: str, target: date, days: int=7)`** · build_diverse_local_ai_datasets.py:140
  - 기능: `_recent_events`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_write(path: Path, rows: list[dict])`** · build_diverse_local_ai_datasets.py:164
  - 기능: `_write`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `main()`** · build_diverse_local_ai_datasets.py:181
  - 기능: `main`은(는) 명령행 인자를 해석하고 이 스크립트의 전체 작업 순서를 실행합니다.

### `scripts/ai/data/build_etf_synthesis_local_ai_dataset.py`

AI 학습 데이터를 수집·결합·보강합니다.

- **클래스 `WalkForwardModel`** · build_etf_synthesis_local_ai_dataset.py:28
  - 기능: 데이터베이스에 저장되는 필드와 관계를 정의하는 ORM 모델입니다.
- **함수 `parse_args()`** · build_etf_synthesis_local_ai_dataset.py:35
  - 기능: `parse_args`은(는) 원시 입력을 해석하고 필요한 값을 정규화해 추출합니다.
- **함수 `_read(path: Path)`** · build_etf_synthesis_local_ai_dataset.py:49
  - 기능: `_read`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_train(model_name: str, rows: list[dict], cutoff: date)`** · build_etf_synthesis_local_ai_dataset.py:60
  - 기능: `_train`은(는) 해당 작업의 전체 처리 흐름을 실행하고 결과를 반환합니다.
- **함수 `_summary(model: WalkForwardModel, row: dict, model_name: str)`** · build_etf_synthesis_local_ai_dataset.py:98
  - 기능: `_summary`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `main()`** · build_etf_synthesis_local_ai_dataset.py:114
  - 기능: `main`은(는) 명령행 인자를 해석하고 이 스크립트의 전체 작업 순서를 실행합니다.

### `scripts/ai/data/build_financial_local_ai_dataset.py`

AI 학습 데이터를 수집·결합·보강합니다.

- **함수 `parse_args()`** · build_financial_local_ai_dataset.py:23
  - 기능: `parse_args`은(는) 원시 입력을 해석하고 필요한 값을 정규화해 추출합니다.
- **함수 `merge_rows(existing: list[dict], incoming: list[dict])`** · build_financial_local_ai_dataset.py:35
  - 기능: `merge_rows`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_write_rows(path: Path, rows: list[dict])`** · build_financial_local_ai_dataset.py:45
  - 기능: `_write_rows`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `main()`** · build_financial_local_ai_dataset.py:65
  - 기능: `main`은(는) 명령행 인자를 해석하고 이 스크립트의 전체 작업 순서를 실행합니다.

### `scripts/ai/data/build_flow_local_ai_dataset.py`

AI 학습 데이터를 수집·결합·보강합니다.

- **함수 `parse_args()`** · build_flow_local_ai_dataset.py:28
  - 기능: `parse_args`은(는) 원시 입력을 해석하고 필요한 값을 정규화해 추출합니다.
- **함수 `_fieldnames(include_market_context: bool)`** · build_flow_local_ai_dataset.py:43
  - 기능: `_fieldnames`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_write_rows(path: Path, rows: list[dict], *, include_market_context: bool)`** · build_flow_local_ai_dataset.py:58
  - 기능: `_write_rows`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `main()`** · build_flow_local_ai_dataset.py:79
  - 기능: `main`은(는) 명령행 인자를 해석하고 이 스크립트의 전체 작업 순서를 실행합니다.

### `scripts/ai/data/build_kis_flow_local_ai_dataset.py`

AI 학습 데이터를 수집·결합·보강합니다.

- **함수 `parse_args()`** · build_kis_flow_local_ai_dataset.py:25
  - 기능: `parse_args`은(는) 원시 입력을 해석하고 필요한 값을 정규화해 추출합니다.
- **함수 `main()`** · build_kis_flow_local_ai_dataset.py:41
  - 기능: `main`은(는) 명령행 인자를 해석하고 이 스크립트의 전체 작업 순서를 실행합니다.
- **함수 `_collect_history(kis: KisInvestorFlowProvider, symbol: str, args: argparse.Namespace)`** · build_kis_flow_local_ai_dataset.py:95
  - 기능: `_collect_history`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_fieldnames()`** · build_kis_flow_local_ai_dataset.py:126
  - 기능: `_fieldnames`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_read_rows(path: Path)`** · build_kis_flow_local_ai_dataset.py:140
  - 기능: `_read_rows`은(는) 필요한 데이터를 조회해 반환합니다.
- **함수 `_write_rows(path: Path, rows: list[dict])`** · build_kis_flow_local_ai_dataset.py:155
  - 기능: `_write_rows`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `scripts/ai/data/build_market_local_ai_dataset.py`

AI 학습 데이터를 수집·결합·보강합니다.

- **함수 `parse_args()`** · build_market_local_ai_dataset.py:27
  - 기능: `parse_args`은(는) 원시 입력을 해석하고 필요한 값을 정규화해 추출합니다.
- **함수 `write_rows(path: Path, names: tuple[str, ...], rows: list[dict], *, extra_names: tuple[str, ...]=())`** · build_market_local_ai_dataset.py:44
  - 기능: `write_rows`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `main()`** · build_market_local_ai_dataset.py:63
  - 기능: `main`은(는) 명령행 인자를 해석하고 이 스크립트의 전체 작업 순서를 실행합니다.

### `scripts/ai/data/build_news_local_ai_dataset.py`

AI 학습 데이터를 수집·결합·보강합니다.

- **함수 `parse_args()`** · build_news_local_ai_dataset.py:23
  - 기능: `parse_args`은(는) 원시 입력을 해석하고 필요한 값을 정규화해 추출합니다.
- **함수 `main()`** · build_news_local_ai_dataset.py:39
  - 기능: `main`은(는) 명령행 인자를 해석하고 이 스크립트의 전체 작업 순서를 실행합니다.

### `scripts/ai/data/build_sec_event_local_ai_dataset.py`

AI 학습 데이터를 수집·결합·보강합니다.

- **함수 `parse_args()`** · build_sec_event_local_ai_dataset.py:33
  - 기능: `parse_args`은(는) 원시 입력을 해석하고 필요한 값을 정규화해 추출합니다.
- **함수 `_read_financial(path: Path)`** · build_sec_event_local_ai_dataset.py:46
  - 기능: `_read_financial`은(는) 필요한 데이터를 조회해 반환합니다.
- **함수 `_latest_financial(index: dict[str, tuple[list[date], list[dict]]], symbol: str, event_date: date, maximum_age_days: int)`** · build_sec_event_local_ai_dataset.py:64
  - 기능: `_latest_financial`은(는) 필요한 데이터를 조회해 반환합니다.
- **함수 `main()`** · build_sec_event_local_ai_dataset.py:82
  - 기능: `main`은(는) 명령행 인자를 해석하고 이 스크립트의 전체 작업 순서를 실행합니다.

### `scripts/ai/data/build_synthesis_local_ai_dataset.py`

AI 학습 데이터를 수집·결합·보강합니다.

- **함수 `parse_args()`** · build_synthesis_local_ai_dataset.py:37
  - 기능: `parse_args`은(는) 원시 입력을 해석하고 필요한 값을 정규화해 추출합니다.
- **함수 `_read(path: Path)`** · build_synthesis_local_ai_dataset.py:50
  - 기능: `_read`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_train_specialist(agent: str, rows: list[dict], cutoff: date, trainer: str)`** · build_synthesis_local_ai_dataset.py:61
  - 기능: `_train_specialist`은(는) 해당 작업의 전체 처리 흐름을 실행하고 결과를 반환합니다.
- **함수 `_indexes(rows_by_agent: dict[str, list[dict]])`** · build_synthesis_local_ai_dataset.py:85
  - 기능: `_indexes`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_latest_row(index, symbol: str, target_date: date, max_age_days: int)`** · build_synthesis_local_ai_dataset.py:100
  - 기능: `_latest_row`은(는) 필요한 데이터를 조회해 반환합니다.
- **함수 `_specialist_values(agent: str, model, row: dict | None)`** · build_synthesis_local_ai_dataset.py:113
  - 기능: `_specialist_values`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `main()`** · build_synthesis_local_ai_dataset.py:125
  - 기능: `main`은(는) 명령행 인자를 해석하고 이 스크립트의 전체 작업 순서를 실행합니다.

### `scripts/ai/data/collect_local_ai_incremental.py`

AI 학습 데이터를 수집·결합·보강합니다.

- **함수 `parse_args()`** · collect_local_ai_incremental.py:36
  - 기능: `parse_args`은(는) 원시 입력을 해석하고 필요한 값을 정규화해 추출합니다.
- **함수 `requested_symbols(values: list[str], csv_value: str)`** · collect_local_ai_incremental.py:81
  - 기능: 반복 인자와 쉼표 구분 인자를 합쳐 검증된 종목 목록으로 만든다.
- **함수 `normalized_symbols(values: list[str])`** · collect_local_ai_incremental.py:87
  - 기능: `normalized_symbols`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `rotating_news_symbols(symbols: list[str], today: date, *, windows: int, daily_request_limit: int)`** · collect_local_ai_incremental.py:100
  - 기능: 무료 요청 한도 안에서 종목을 순환하며 여러 과거 뉴스 구간을 수집한다.
- **함수 `safe_output_dir(value: Path)`** · collect_local_ai_incremental.py:118
  - 기능: `safe_output_dir`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `load_state(path: Path)`** · collect_local_ai_incremental.py:127
  - 기능: `load_state`은(는) 필요한 데이터를 조회해 반환합니다.
- **함수 `due_jobs(mode: str, state: dict[str, str | int], today: date, *, financial_interval_days: int, flow_interval_days: int=7, force: bool)`** · collect_local_ai_incremental.py:148
  - 기능: `due_jobs`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `command_for(job: str, symbols: list[str], output_dir: Path, *, news_window_days: int, news_windows: int, market_limit: int=500, financial_max_rows_per_symbol: int=40, flow_market_limit: int=2600)`** · collect_local_ai_incremental.py:181
  - 기능: `command_for`은(는) 입력 조건을 지원하는 제공자나 처리 대상을 선택해 반환합니다.
- **함수 `finalized_label_command(output_dir: Path)`** · collect_local_ai_incremental.py:269
  - 기능: 시장 결과가 확인된 뉴스·재무 행만 공통 5거래일 정답으로 확정한다.
- **함수 `news_enrichment_command(output_dir: Path)`** · collect_local_ai_incremental.py:291
  - 기능: `news_enrichment_command`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `dataset_audit_command(output_dir: Path)`** · collect_local_ai_incremental.py:306
  - 기능: 수집 결과의 무결성과 후보 재학습 준비도를 JSON으로 기록하는 명령을 만든다.
- **함수 `kis_dataset_audit_command(output_dir: Path)`** · collect_local_ai_incremental.py:320
  - 기능: KIS 후보 데이터가 존재할 때만 FINRA와 분리된 품질 보고서를 만든다.
- **함수 `run_collection_job(job: str, command: list[str])`** · collect_local_ai_incremental.py:339
  - 기능: 일반 작업은 즉시 실패시키고 KIS 장애만 다음 작업과 감사 단계에서 격리한다.
- **함수 `reserve_news_requests(state: dict[str, str | int], today: date, *, projected: int, limit: int)`** · collect_local_ai_incremental.py:351
  - 기능: `reserve_news_requests`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `save_state(path: Path, state: dict[str, str | int])`** · collect_local_ai_incremental.py:369
  - 기능: 호출 예산 상태를 배타적 임시 파일에 쓴 뒤 원자적으로 교체한다.
- **함수 `collection_lock(path: Path, *, now: datetime | None=None)`** · collect_local_ai_incremental.py:390
  - 기능: 동시에 실행된 수집기가 일일 호출 예산과 상태 파일을 중복 갱신하지 못하게 한다.
- **함수 `main()`** · collect_local_ai_incremental.py:415
  - 기능: `main`은(는) 명령행 인자를 해석하고 이 스크립트의 전체 작업 순서를 실행합니다.

### `scripts/ai/data/collect_toss_adjusted_history.py`

AI 학습 데이터를 수집·결합·보강합니다.

- **클래스 `RequiredRange`** · collect_toss_adjusted_history.py:33
  - 기능: `RequiredRange` 관련 상태와 동작을 하나의 객체로 묶습니다.
- **함수 `parse_args()`** · collect_toss_adjusted_history.py:40
  - 기능: `parse_args`은(는) 원시 입력을 해석하고 필요한 값을 정규화해 추출합니다.
- **함수 `required_ranges(rows: list[dict[str, str]])`** · collect_toss_adjusted_history.py:51
  - 기능: 재무 행마다 가격이 필요한 공시일 범위를 종목별로 계산한다.
- **함수 `validated_history(candles: list[Candle], required: RequiredRange)`** · collect_toss_adjusted_history.py:72
  - 기능: 중복이 없고 필요한 공시 범위를 덮는 검증된 조정 일봉만 반환한다.
- **함수 `_safe_output_dir(value: Path)`** · collect_toss_adjusted_history.py:91
  - 기능: `_safe_output_dir`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_read_financial(path: Path)`** · collect_toss_adjusted_history.py:100
  - 기능: `_read_financial`은(는) 필요한 데이터를 조회해 반환합니다.
- **함수 `_read_symbol(path: Path, symbol: str, required: RequiredRange)`** · collect_toss_adjusted_history.py:113
  - 기능: `_read_symbol`은(는) 필요한 데이터를 조회해 반환합니다.
- **함수 `_atomic_csv(path: Path, rows: list[dict[str, object]])`** · collect_toss_adjusted_history.py:140
  - 기능: `_atomic_csv`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_atomic_json(path: Path, payload: dict[str, object])`** · collect_toss_adjusted_history.py:161
  - 기능: `_atomic_json`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_collect_symbol(provider: StockProvider, symbol: str, required: RequiredRange, limit: int)`** · collect_toss_adjusted_history.py:181
  - 기능: `_collect_symbol`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_manifest(output_dir: Path, ranges: dict[str, RequiredRange])`** · collect_toss_adjusted_history.py:203
  - 기능: `_manifest`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `main()`** · collect_toss_adjusted_history.py:239
  - 기능: `main`은(는) 명령행 인자를 해석하고 이 스크립트의 전체 작업 순서를 실행합니다.

### `scripts/ai/data/enrich_advanced_market_features.py`

AI 학습 데이터를 수집·결합·보강합니다.

- **함수 `parse_args()`** · enrich_advanced_market_features.py:18
  - 기능: `parse_args`은(는) 원시 입력을 해석하고 필요한 값을 정규화해 추출합니다.
- **함수 `main()`** · enrich_advanced_market_features.py:27
  - 기능: `main`은(는) 명령행 인자를 해석하고 이 스크립트의 전체 작업 순서를 실행합니다.

### `scripts/ai/data/enrich_contextual_specialists.py`

AI 학습 데이터를 수집·결합·보강합니다.

- **함수 `parse_args()`** · enrich_contextual_specialists.py:24
  - 기능: `parse_args`은(는) 원시 입력을 해석하고 필요한 값을 정규화해 추출합니다.
- **함수 `_read(path: Path)`** · enrich_contextual_specialists.py:36
  - 기능: `_read`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_write(path: Path, rows: list[dict], extra_names: tuple[str, ...])`** · enrich_contextual_specialists.py:43
  - 기능: `_write`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `main()`** · enrich_contextual_specialists.py:58
  - 기능: `main`은(는) 명령행 인자를 해석하고 이 스크립트의 전체 작업 순서를 실행합니다.

### `scripts/ai/data/enrich_etf_asset_class.py`

AI 학습 데이터를 수집·결합·보강합니다.

- **함수 `parse_args()`** · enrich_etf_asset_class.py:21
  - 기능: `parse_args`은(는) 원시 입력을 해석하고 필요한 값을 정규화해 추출합니다.
- **함수 `main()`** · enrich_etf_asset_class.py:30
  - 기능: `main`은(는) 명령행 인자를 해석하고 이 스크립트의 전체 작업 순서를 실행합니다.

### `scripts/ai/data/enrich_financial_pit_valuation.py`

AI 학습 데이터를 수집·결합·보강합니다.

- **함수 `parse_args()`** · enrich_financial_pit_valuation.py:46
  - 기능: `parse_args`은(는) 원시 입력을 해석하고 필요한 값을 정규화해 추출합니다.
- **함수 `_safe_output_path(value: Path)`** · enrich_financial_pit_valuation.py:58
  - 기능: `_safe_output_path`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_read(path: Path)`** · enrich_financial_pit_valuation.py:67
  - 기능: `_read`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `build_price_index(rows: list[dict[str, str]])`** · enrich_financial_pit_valuation.py:82
  - 기능: 종목별 거래일 종가를 정렬하고 중복 날짜는 마지막 행으로 확정한다.
- **함수 `enrich_rows(rows: list[dict[str, str]], annuals_by_symbol: dict[str, list[AnnualValuationSnapshot]], price_index: dict[str, tuple[list[date], list[float]]])`** · enrich_financial_pit_valuation.py:105
  - 기능: 각 공시 시점보다 앞서 공개·확정된 연간 재무와 종가만 결합한다.
- **함수 `enrich_roe_rows(rows: list[dict[str, str]], annuals_by_symbol: dict[str, list[AnnualValuationSnapshot]])`** · enrich_financial_pit_valuation.py:185
  - 기능: 가격 이력 없이도 계산 가능한 최신 공개 연간 ROE만 시점 기준으로 결합한다.
- **함수 `_signed_log(value: float)`** · enrich_financial_pit_valuation.py:231
  - 기능: `_signed_log`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_write(path: Path, original_fields: list[str], rows: list[dict[str, str | float]], *, feature_fields: tuple[str, ...]=PIT_VALUATION_FEATURES, metadata_fields: tuple[str, ...]=PIT_VALUATION_METADATA)`** · enrich_financial_pit_valuation.py:237
  - 기능: `_write`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `main()`** · enrich_financial_pit_valuation.py:272
  - 기능: `main`은(는) 명령행 인자를 해석하고 이 스크립트의 전체 작업 순서를 실행합니다.

### `scripts/ai/data/enrich_flow_market_context.py`

AI 학습 데이터를 수집·결합·보강합니다.

- **함수 `parse_args()`** · enrich_flow_market_context.py:20
  - 기능: `parse_args`은(는) 원시 입력을 해석하고 필요한 값을 정규화해 추출합니다.
- **함수 `_key(row: dict[str, str])`** · enrich_flow_market_context.py:30
  - 기능: `_key`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `main()`** · enrich_flow_market_context.py:36
  - 기능: `main`은(는) 명령행 인자를 해석하고 이 스크립트의 전체 작업 순서를 실행합니다.

### `scripts/ai/data/enrich_flow_short_interest.py`

AI 학습 데이터를 수집·결합·보강합니다.

- **함수 `parse_args()`** · enrich_flow_short_interest.py:25
  - 기능: `parse_args`은(는) 원시 입력을 해석하고 필요한 값을 정규화해 추출합니다.
- **함수 `main()`** · enrich_flow_short_interest.py:33
  - 기능: `main`은(는) 명령행 인자를 해석하고 이 스크립트의 전체 작업 순서를 실행합니다.

### `scripts/ai/data/enrich_local_ai_macro.py`

AI 학습 데이터를 수집·결합·보강합니다.

- **함수 `parse_args()`** · enrich_local_ai_macro.py:21
  - 기능: `parse_args`은(는) 원시 입력을 해석하고 필요한 값을 정규화해 추출합니다.
- **함수 `_read(path: Path)`** · enrich_local_ai_macro.py:29
  - 기능: `_read`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_row_date(row: dict)`** · enrich_local_ai_macro.py:36
  - 기능: `_row_date`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `main()`** · enrich_local_ai_macro.py:42
  - 기능: `main`은(는) 명령행 인자를 해석하고 이 스크립트의 전체 작업 순서를 실행합니다.

### `scripts/ai/data/enrich_market_dataset_benchmark.py`

AI 학습 데이터를 수집·결합·보강합니다.

- **함수 `parse_args()`** · enrich_market_dataset_benchmark.py:21
  - 기능: `parse_args`은(는) 원시 입력을 해석하고 필요한 값을 정규화해 추출합니다.
- **함수 `_read(path: Path)`** · enrich_market_dataset_benchmark.py:31
  - 기능: `_read`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_write(path: Path, additions: tuple[str, ...], rows: list[dict])`** · enrich_market_dataset_benchmark.py:38
  - 기능: `_write`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `main()`** · enrich_market_dataset_benchmark.py:51
  - 기능: `main`은(는) 명령행 인자를 해석하고 이 스크립트의 전체 작업 순서를 실행합니다.

### `scripts/ai/data/enrich_technical_sector.py`

AI 학습 데이터를 수집·결합·보강합니다.

- **함수 `parse_args()`** · enrich_technical_sector.py:24
  - 기능: `parse_args`은(는) 원시 입력을 해석하고 필요한 값을 정규화해 추출합니다.
- **함수 `main()`** · enrich_technical_sector.py:35
  - 기능: `main`은(는) 명령행 인자를 해석하고 이 스크립트의 전체 작업 순서를 실행합니다.

### `scripts/ai/data/relabel_financial_sector_neutral.py`

AI 학습 데이터를 수집·결합·보강합니다.

- **함수 `parse_args()`** · relabel_financial_sector_neutral.py:38
  - 기능: `parse_args`은(는) 원시 입력을 해석하고 필요한 값을 정규화해 추출합니다.
- **함수 `_safe_output_path(value: Path)`** · relabel_financial_sector_neutral.py:50
  - 기능: `_safe_output_path`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_read(path: Path)`** · relabel_financial_sector_neutral.py:59
  - 기능: `_read`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_deduplicate(rows: list[dict[str, str]])`** · relabel_financial_sector_neutral.py:78
  - 기능: 같은 종목·결과 세션에는 결과 직전의 가장 최근 공시 특성만 남긴다.
- **함수 `relabel(rows: list[dict[str, str]], *, minimum_sector_peers: int, minimum_market_peers: int, minimum_absolute_return: float)`** · relabel_financial_sector_neutral.py:97
  - 기능: 동일 결과 날짜의 업종 중앙값을 우선 사용해 중립화된 이진 라벨을 계산한다.
- **함수 `write_rows(path: Path, rows: list[dict[str, str | float | int]])`** · relabel_financial_sector_neutral.py:184
  - 기능: 중립 라벨 데이터셋을 배타적 임시 파일에 쓴 뒤 원자 교체한다.
- **함수 `main()`** · relabel_financial_sector_neutral.py:208
  - 기능: `main`은(는) 명령행 인자를 해석하고 이 스크립트의 전체 작업 순서를 실행합니다.

### `scripts/ai/data/relabel_flow_local_ai_dataset.py`

AI 학습 데이터를 수집·결합·보강합니다.

- **함수 `parse_args()`** · relabel_flow_local_ai_dataset.py:9
  - 기능: `parse_args`은(는) 원시 입력을 해석하고 필요한 값을 정규화해 추출합니다.
- **함수 `main()`** · relabel_flow_local_ai_dataset.py:18
  - 기능: `main`은(는) 명령행 인자를 해석하고 이 스크립트의 전체 작업 순서를 실행합니다.

### `scripts/ai/data/relabel_news_local_ai_dataset.py`

AI 학습 데이터를 수집·결합·보강합니다.

- **함수 `parse_args()`** · relabel_news_local_ai_dataset.py:9
  - 기능: `parse_args`은(는) 원시 입력을 해석하고 필요한 값을 정규화해 추출합니다.
- **함수 `main()`** · relabel_news_local_ai_dataset.py:18
  - 기능: `main`은(는) 명령행 인자를 해석하고 이 스크립트의 전체 작업 순서를 실행합니다.

### `scripts/ai/data/relabel_specialists_with_market_outcomes.py`

AI 학습 데이터를 수집·결합·보강합니다.

- **함수 `parse_args()`** · relabel_specialists_with_market_outcomes.py:19
  - 기능: `parse_args`은(는) 원시 입력을 해석하고 필요한 값을 정규화해 추출합니다.
- **함수 `_key(row: dict[str, str])`** · relabel_specialists_with_market_outcomes.py:35
  - 기능: `_key`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_read(path: Path)`** · relabel_specialists_with_market_outcomes.py:41
  - 기능: `_read`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_outcomes(path: Path)`** · relabel_specialists_with_market_outcomes.py:49
  - 기능: `_outcomes`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_outcome_index(outcomes: dict[tuple[str, str], dict[str, str]])`** · relabel_specialists_with_market_outcomes.py:62
  - 기능: `_outcome_index`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_next_outcome(index: dict[str, tuple[list[date], list[dict[str, str]]]], row: dict[str, str])`** · relabel_specialists_with_market_outcomes.py:80
  - 기능: `_next_outcome`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `relabel(agent: str, source_path: Path, target_path: Path, outcomes: dict[tuple[str, str], dict[str, str]], outcome_index: dict[str, tuple[list[date], list[dict[str, str]]]])`** · relabel_specialists_with_market_outcomes.py:98
  - 기능: `relabel`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `main()`** · relabel_specialists_with_market_outcomes.py:159
  - 기능: `main`은(는) 명령행 인자를 해석하고 이 스크립트의 전체 작업 순서를 실행합니다.

### `scripts/ai/data/restore_market_close_prices.py`

AI 학습 데이터를 수집·결합·보강합니다.

- **함수 `parse_args()`** · restore_market_close_prices.py:24
  - 기능: `parse_args`은(는) 원시 입력을 해석하고 필요한 값을 정규화해 추출합니다.
- **함수 `restore_symbol_rows(rows: list[dict[str, str]], anchors: dict[date, float])`** · restore_market_close_prices.py:35
  - 기능: 겹치는 실제 종가 한 점을 기준으로 수익률 체인을 앞뒤로 복원한다.
- **함수 `restore_symbol_rows_with_diagnostics(rows: list[dict[str, str]], anchors: dict[date, float])`** · restore_market_close_prices.py:44
  - 기능: 복원 결과와 겹치는 실제 종가 대비 최대 상대 오차를 반환한다.
- **함수 `_safe_path(value: Path, *, output: bool)`** · restore_market_close_prices.py:82
  - 기능: `_safe_path`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_read(path: Path)`** · restore_market_close_prices.py:93
  - 기능: `_read`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_write(path: Path, fields: list[str], rows: list[dict[str, str | float]])`** · restore_market_close_prices.py:108
  - 기능: `_write`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `main()`** · restore_market_close_prices.py:134
  - 기능: `main`은(는) 명령행 인자를 해석하고 이 스크립트의 전체 작업 순서를 실행합니다.

### `scripts/ai/training/approve_local_ai_candidate.py`

로컬 AI 모델을 학습·검증하고 후보를 관리합니다.

- **함수 `parse_args()`** · approve_local_ai_candidate.py:19
  - 기능: `parse_args`은(는) 원시 입력을 해석하고 필요한 값을 정규화해 추출합니다.
- **함수 `safe_artifact_directory(path: Path)`** · approve_local_ai_candidate.py:30
  - 기능: `safe_artifact_directory`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `approve(candidate_dir: Path, operating_dir: Path, agent: ModelName, approved_version: str)`** · approve_local_ai_candidate.py:39
  - 기능: `approve`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `main()`** · approve_local_ai_candidate.py:76
  - 기능: `main`은(는) 명령행 인자를 해석하고 이 스크립트의 전체 작업 순서를 실행합니다.

### `scripts/ai/training/audit_local_ai_datasets.py`

로컬 AI 모델을 학습·검증하고 후보를 관리합니다.

- **함수 `parse_args()`** · audit_local_ai_datasets.py:59
  - 기능: `parse_args`은(는) 원시 입력을 해석하고 필요한 값을 정규화해 추출합니다.
- **함수 `_validation_start(timestamps: list[datetime])`** · audit_local_ai_datasets.py:74
  - 기능: 같은 시각 그룹이 학습과 검증 양쪽에 섞이지 않도록 80% 경계를 앞으로 맞춘다.
- **함수 `_training_readiness(*, structural_status: str, holdout_labels: list[int], holdout_timestamps: list[datetime], minimum_validation_samples: int)`** · audit_local_ai_datasets.py:86
  - 기능: 구조 검사를 통과한 데이터가 후보 재학습에 충분한지 보수적으로 판정한다.
- **함수 `audit(path: Path, features: tuple[str, ...], *, minimum_validation_samples: int=200)`** · audit_local_ai_datasets.py:111
  - 기능: 한 CSV의 무결성과 시간순 후보 재학습 준비도를 요약한다.
- **함수 `safe_report_path(data_dir: Path, output: Path)`** · audit_local_ai_datasets.py:203
  - 기능: 감사 보고서가 Git 제외 데이터 디렉터리 밖에 기록되지 않게 제한한다.
- **함수 `save_report(path: Path, report: dict[str, object])`** · audit_local_ai_datasets.py:213
  - 기능: 감사 보고서를 배타적 임시 파일에 쓴 뒤 원자적으로 교체한다.
- **함수 `main()`** · audit_local_ai_datasets.py:234
  - 기능: `main`은(는) 명령행 인자를 해석하고 이 스크립트의 전체 작업 순서를 실행합니다.

### `scripts/ai/training/benchmark_feature_groups.py`

로컬 AI 모델을 학습·검증하고 후보를 관리합니다.

- **함수 `parse_args()`** · benchmark_feature_groups.py:13
  - 기능: `parse_args`은(는) 원시 입력을 해석하고 필요한 값을 정규화해 추출합니다.
- **함수 `_names(value: str)`** · benchmark_feature_groups.py:25
  - 기능: `_names`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `main()`** · benchmark_feature_groups.py:31
  - 기능: `main`은(는) 명령행 인자를 해석하고 이 스크립트의 전체 작업 순서를 실행합니다.

### `scripts/ai/training/benchmark_gpu_xgboost_local_ai.py`

로컬 AI 모델을 학습·검증하고 후보를 관리합니다.

- **함수 `parse_args()`** · benchmark_gpu_xgboost_local_ai.py:25
  - 기능: `parse_args`은(는) 원시 입력을 해석하고 필요한 값을 정규화해 추출합니다.
- **함수 `main()`** · benchmark_gpu_xgboost_local_ai.py:50
  - 기능: `main`은(는) 명령행 인자를 해석하고 이 스크립트의 전체 작업 순서를 실행합니다.

### `scripts/ai/training/check_gpu_training.py`

로컬 AI 모델을 학습·검증하고 후보를 관리합니다.

- **함수 `main()`** · check_gpu_training.py:9
  - 기능: `main`은(는) 명령행 인자를 해석하고 이 스크립트의 전체 작업 순서를 실행합니다.

### `scripts/ai/training/diagnose_local_ai_retraining.py`

로컬 AI 모델을 학습·검증하고 후보를 관리합니다.

- **함수 `parse_args()`** · diagnose_local_ai_retraining.py:22
  - 기능: `parse_args`은(는) 원시 입력을 해석하고 필요한 값을 정규화해 추출합니다.
- **함수 `safe_auc(actual: np.ndarray, score: np.ndarray)`** · diagnose_local_ai_retraining.py:32
  - 기능: `safe_auc`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `load_rows(path: Path)`** · diagnose_local_ai_retraining.py:40
  - 기능: `load_rows`은(는) 필요한 데이터를 조회해 반환합니다.
- **함수 `compare_reference(rows: list[dict[str, str]], reference_path: Path)`** · diagnose_local_ai_retraining.py:47
  - 기능: `compare_reference`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `analyze(path: Path, agent: str, reference_path: Path | None=None)`** · diagnose_local_ai_retraining.py:68
  - 기능: `analyze`은(는) 해당 작업의 전체 처리 흐름을 실행하고 결과를 반환합니다.
- **함수 `main()`** · diagnose_local_ai_retraining.py:171
  - 기능: `main`은(는) 명령행 인자를 해석하고 이 스크립트의 전체 작업 순서를 실행합니다.

### `scripts/ai/training/evaluate_rule_diagnostic.py`

로컬 AI 모델을 학습·검증하고 후보를 관리합니다.

- **함수 `parse_args()`** · evaluate_rule_diagnostic.py:27
  - 기능: `parse_args`은(는) 원시 입력을 해석하고 필요한 값을 정규화해 추출합니다.
- **함수 `read_rows(path: Path)`** · evaluate_rule_diagnostic.py:40
  - 기능: `read_rows`은(는) 필요한 데이터를 조회해 반환합니다.
- **함수 `evaluate(rows: list[dict[str, str]], specialists: tuple[AgentName, ...], *, folds: int)`** · evaluate_rule_diagnostic.py:53
  - 기능: `evaluate`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_classification_metrics(rows: list[dict[str, int | str]])`** · evaluate_rule_diagnostic.py:127
  - 기능: `_classification_metrics`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `save_policy(path: Path, policy: dict[str, object])`** · evaluate_rule_diagnostic.py:152
  - 기능: `save_policy`은(는) 데이터를 저장하거나 기존 상태에 추가합니다.
- **함수 `main()`** · evaluate_rule_diagnostic.py:164
  - 기능: `main`은(는) 명령행 인자를 해석하고 이 스크립트의 전체 작업 순서를 실행합니다.

### `scripts/ai/training/nested_walk_forward_local_agent.py`

로컬 AI 모델을 학습·검증하고 후보를 관리합니다.

- **클래스 `CandidateSetting`** · nested_walk_forward_local_agent.py:36
  - 기능: `CandidateSetting` 관련 상태와 동작을 하나의 객체로 묶습니다.
  - 메서드 `key(self)` · nested_walk_forward_local_agent.py:43
    - 기능: `key`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **클래스 `SelectedCandidate`** · nested_walk_forward_local_agent.py:51
  - 기능: 내부 시간 검증에서 선택된 규제 설정과 피처 열 묶음이다.
- **함수 `parse_args()`** · nested_walk_forward_local_agent.py:60
  - 기능: `parse_args`은(는) 원시 입력을 해석하고 필요한 값을 정규화해 추출합니다.
- **함수 `candidate_settings(c_values: list[float])`** · nested_walk_forward_local_agent.py:83
  - 기능: 규제 강도마다 일반 가중치와 균형 가중치 후보를 만든다.
- **함수 `resolve_features(data_path: Path, agent: str, extra_features: list[str], *, use_all_safe_features: bool=False)`** · nested_walk_forward_local_agent.py:95
  - 기능: 운영 기본 피처에 CSV에 존재하는 안전한 후보 피처만 추가한다.
- **함수 `resolve_feature_sets(data_path: Path, agent: str, fixed_extra_features: list[str], candidate_extra_feature_sets: list[str], *, use_all_safe_features: bool=False)`** · nested_walk_forward_local_agent.py:117
  - 기능: 후보 피처 묶음을 검증하고 전체 행렬에서 사용할 열 인덱스로 변환한다.
- **함수 `load_sample_weights(path: Path, column: str)`** · nested_walk_forward_local_agent.py:153
  - 기능: CSV의 양수·유한 표본 가중치를 원본 행 순서대로 읽는다.
- **함수 `_calibration_error(actual: np.ndarray, probability: np.ndarray, sample_weights: np.ndarray)`** · nested_walk_forward_local_agent.py:169
  - 기능: `_calibration_error`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_metrics(actual: np.ndarray, probability: np.ndarray, sample_weights: np.ndarray | None=None, *, threshold: float=0.5, predictions: np.ndarray | None=None)`** · nested_walk_forward_local_agent.py:194
  - 기능: `_metrics`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_correct_balanced_probabilities(probability: np.ndarray, labels: np.ndarray, sample_weights: np.ndarray | None=None)`** · nested_walk_forward_local_agent.py:249
  - 기능: 균형 클래스 가중치로 왜곡된 사후확률을 실제 학습 발생률로 되돌린다.
- **함수 `_select_threshold(actual: np.ndarray, probability: np.ndarray, sample_weights: np.ndarray | None=None)`** · nested_walk_forward_local_agent.py:270
  - 기능: 내부 검증 결과에서 균형 정확도가 가장 안정적인 판정 임계값을 고른다.
- **함수 `_select_setting(x: np.ndarray, y: np.ndarray, timestamps: np.ndarray, settings: tuple[CandidateSetting, ...], *, inner_splits: int, purge: int, sample_weights: np.ndarray | None=None, feature_sets: dict[str, tuple[int, ...]] | None=None)`** · nested_walk_forward_local_agent.py:306
  - 기능: `_select_setting`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `nested_validate(agent: ModelName, x: np.ndarray, y: np.ndarray, timestamps: np.ndarray, settings: tuple[CandidateSetting, ...], *, outer_splits: int, inner_splits: int, purge: int, sample_weights: np.ndarray | None=None, feature_sets: dict[str, tuple[int, ...]] | None=None)`** · nested_walk_forward_local_agent.py:397
  - 기능: 각 바깥 학습 구간 안에서만 설정을 선택하고 다음 시점에서 평가한다.
- **함수 `safe_output_path(value: Path)`** · nested_walk_forward_local_agent.py:536
  - 기능: 검증 보고서가 Git 제외 artifact 디렉터리 밖에 기록되지 않게 제한한다.
- **함수 `save_report(path: Path, report: dict[str, object])`** · nested_walk_forward_local_agent.py:545
  - 기능: 중첩 검증 보고서를 배타적 임시 파일에 기록한 뒤 원자 교체한다.
- **함수 `main()`** · nested_walk_forward_local_agent.py:566
  - 기능: `main`은(는) 명령행 인자를 해석하고 이 스크립트의 전체 작업 순서를 실행합니다.

### `scripts/ai/training/report_local_ai_accuracy.py`

로컬 AI 모델을 학습·검증하고 후보를 관리합니다.

- **클래스 `QualityRow`** · report_local_ai_accuracy.py:35
  - 기능: `QualityRow` 관련 상태와 동작을 하나의 객체로 묶습니다.
- **함수 `parse_args()`** · report_local_ai_accuracy.py:54
  - 기능: `parse_args`은(는) 원시 입력을 해석하고 필요한 값을 정규화해 추출합니다.
- **함수 `selected_models(agent: ModelName | None, include_etf: bool)`** · report_local_ai_accuracy.py:67
  - 기능: 단일 후보 또는 기본 운영 모델군 중 보고할 범위를 선택한다.
- **함수 `wilson_interval(success_rate: float, samples: int)`** · report_local_ai_accuracy.py:75
  - 기능: `wilson_interval`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `quality_status(model: ModelName, metrics: dict[str, float])`** · report_local_ai_accuracy.py:94
  - 기능: `quality_status`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `read_quality(artifact_dir: Path, model: ModelName)`** · report_local_ai_accuracy.py:104
  - 기능: `read_quality`은(는) 필요한 데이터를 조회해 반환합니다.
- **함수 `main()`** · report_local_ai_accuracy.py:142
  - 기능: `main`은(는) 명령행 인자를 해석하고 이 스크립트의 전체 작업 순서를 실행합니다.

### `scripts/ai/training/train_local_agents.py`

로컬 AI 모델을 학습·검증하고 후보를 관리합니다.

- **함수 `parse_args()`** · train_local_agents.py:43
  - 기능: `parse_args`은(는) 원시 입력을 해석하고 필요한 값을 정규화해 추출합니다.
- **함수 `load_dataset(path: Path, feature_names: tuple[str, ...], *, min_absolute_return: float=0.0)`** · train_local_agents.py:63
  - 기능: `load_dataset`은(는) 필요한 데이터를 조회해 반환합니다.
- **함수 `_timestamp(raw: str)`** · train_local_agents.py:113
  - 기능: `_timestamp`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `train(agent: ModelName, data_dir: Path, output_dir: Path, validation_gap: int=0, *, iterations: int=1200, learning_rate: float=0.05, l2: float=0.001, trainer: str='custom', inverse_regularization: float=0.1, min_absolute_return: float=0.0, class_weight_balanced: bool=False, extra_features: tuple[str, ...]=(), positive_class_weight: float | None=None)`** · train_local_agents.py:120
  - 기능: `train`은(는) 해당 작업의 전체 처리 흐름을 실행하고 결과를 반환합니다.
- **함수 `main()`** · train_local_agents.py:188
  - 기능: `main`은(는) 명령행 인자를 해석하고 이 스크립트의 전체 작업 순서를 실행합니다.

### `scripts/ai/training/validate_local_ai_candidates.py`

로컬 AI 모델을 학습·검증하고 후보를 관리합니다.

- **함수 `parse_args()`** · validate_local_ai_candidates.py:23
  - 기능: `parse_args`은(는) 원시 입력을 해석하고 필요한 값을 정규화해 추출합니다.
- **함수 `safe_directory(path: Path, root: Path, *, must_exist: bool)`** · validate_local_ai_candidates.py:34
  - 기능: 데이터와 결과 경로가 각각 Git 제외 루트 안에만 머물도록 제한한다.
- **함수 `uses_custom_feature_schema(path: Path, agent: str)`** · validate_local_ai_candidates.py:45
  - 기능: 기본 운영 피처가 없는 지역 전용 데이터셋인지 판별한다.
- **함수 `audit_dataset(path: Path, agent: str)`** · validate_local_ai_candidates.py:52
  - 기능: 기본 운영 피처로 후보 데이터의 구조와 시간 검증 준비도를 확인한다.
- **함수 `validation_command(data_dir: Path, output_dir: Path, agent: str, *, custom_schema: bool=False)`** · validate_local_ai_candidates.py:62
  - 기능: 셸 문자열 결합 없이 중첩 시간 검증 명령 인자를 만든다.
- **함수 `selected_training_options(result: dict)`** · validate_local_ai_candidates.py:88
  - 기능: 중첩 검증에서 가장 자주 선택된 규제 설정을 최종 후보 학습에 사용한다.
- **함수 `candidate_training_command(data_dir: Path, output_dir: Path, agent: str, result: dict)`** · validate_local_ai_candidates.py:101
  - 기능: `candidate_training_command`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `save_json(path: Path, payload: object)`** · validate_local_ai_candidates.py:126
  - 기능: 부분 보고서가 남지 않도록 같은 디렉터리에서 원자적으로 교체한다.
- **함수 `main()`** · validate_local_ai_candidates.py:142
  - 기능: `main`은(는) 명령행 인자를 해석하고 이 스크립트의 전체 작업 순서를 실행합니다.

### `scripts/ai/training/walk_forward_local_agents.py`

로컬 AI 모델을 학습·검증하고 후보를 관리합니다.

- **함수 `parse_args()`** · walk_forward_local_agents.py:62
  - 기능: `parse_args`은(는) 원시 입력을 해석하고 필요한 값을 정규화해 추출합니다.
- **함수 `dataset_feature_names(path: Path)`** · walk_forward_local_agents.py:80
  - 기능: `dataset_feature_names`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `load_rows(path: Path, features: tuple[str, ...], *, min_absolute_outcome: float=0.0, outcome_column: str='future_excess_return', required_positive_features: tuple[str, ...]=())`** · walk_forward_local_agents.py:88
  - 기능: `load_rows`은(는) 필요한 데이터를 조회해 반환합니다.
- **함수 `timestamp_folds(timestamps: np.ndarray, *, splits: int, purge: int)`** · walk_forward_local_agents.py:128
  - 기능: `timestamp_folds`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `evaluate(x: np.ndarray, y: np.ndarray, folds: list[tuple[np.ndarray, np.ndarray]], *, inverse_regularization: float, balanced: bool, positive_weight: float | None=None)`** · walk_forward_local_agents.py:155
  - 기능: `evaluate`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_selective_metrics(probabilities: np.ndarray, actuals: np.ndarray, *, cutoff: float)`** · walk_forward_local_agents.py:248
  - 기능: `_selective_metrics`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `main()`** · walk_forward_local_agents.py:285
  - 기능: `main`은(는) 명령행 인자를 해석하고 이 스크립트의 전체 작업 순서를 실행합니다.

### `scripts/generate_korean_code_reference.py`

저장소 문서 자동화 작업을 수행합니다.

- **함수 `_relative(path: Path)`** · generate_korean_code_reference.py:38
  - 기능: `_relative`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_module_role(path: Path)`** · generate_korean_code_reference.py:44
  - 기능: 파일 경로를 이용해 유지보수자가 알아야 할 계층 책임을 설명한다.
- **함수 `_first_korean_doc(node: ast.AST)`** · generate_korean_code_reference.py:79
  - 기능: 기존 한글 docstring이 있으면 첫 문단을 재사용한다.
- **함수 `_class_description(node: ast.ClassDef)`** · generate_korean_code_reference.py:88
  - 기능: `_class_description`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_callable_description(name: str, *, async_function: bool=False)`** · generate_korean_code_reference.py:126
  - 기능: 함수 이름의 동사를 기준으로 부작용과 반환 목적을 한글로 설명한다.
- **함수 `_python_signature(node: ast.FunctionDef | ast.AsyncFunctionDef)`** · generate_korean_code_reference.py:165
  - 기능: `_python_signature`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_python_sections()`** · generate_korean_code_reference.py:176
  - 기능: `_python_sections`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_interface_fields(lines: list[str], start: int)`** · generate_korean_code_reference.py:236
  - 기능: `_interface_fields`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_preceding_korean_jsdoc(lines: list[str], start: int)`** · generate_korean_code_reference.py:253
  - 기능: 선언 바로 위의 한글 JSDoc 첫 문단을 찾아 코드 사전 설명으로 사용한다.
- **함수 `_interface_description(name: str, path: Path, fields: list[str])`** · generate_korean_code_reference.py:280
  - 기능: `_interface_description`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_typescript_sections()`** · generate_korean_code_reference.py:300
  - 기능: `_typescript_sections`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `main()`** · generate_korean_code_reference.py:369
  - 기능: 현재 소스 선언을 읽어 한글 코드 사전을 재생성한다.

### `scripts/operations/benchmark_redis_runtime.py`

개발·운영·보안 점검 작업을 수행합니다.

- **함수 `parse_args()`** · benchmark_redis_runtime.py:12
  - 기능: `parse_args`은(는) 원시 입력을 해석하고 필요한 값을 정규화해 추출합니다.
- **함수 `async receive_messages(bus: RedisQuoteBus, symbol: str, count: int)`** · benchmark_redis_runtime.py:23
  - 기능: `receive_messages`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `async benchmark(args: argparse.Namespace)`** · benchmark_redis_runtime.py:37
  - 기능: `benchmark`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `scripts/operations/check_docs.py`

개발·운영·보안 점검 작업을 수행합니다.

- **함수 `markdown_documents(root: Path=REPOSITORY_ROOT)`** · check_docs.py:22
  - 기능: `markdown_documents`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `broken_local_links(documents: list[Path], root: Path)`** · check_docs.py:36
  - 기능: `broken_local_links`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_assignment_value(tree: ast.Module, name: str)`** · check_docs.py:72
  - 기능: `_assignment_value`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `migration_heads(directory: Path=MIGRATION_DIRECTORY)`** · check_docs.py:83
  - 기능: `migration_heads`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `migration_head_reference_violations(documents: list[Path], expected_head: str, root: Path=REPOSITORY_ROOT)`** · check_docs.py:111
  - 기능: `migration_head_reference_violations`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `validate_repository_docs(root: Path=REPOSITORY_ROOT)`** · check_docs.py:137
  - 기능: `validate_repository_docs`은(는) 입력 또는 현재 상태가 규칙을 만족하는지 검증합니다.
- **함수 `main()`** · check_docs.py:150
  - 기능: `main`은(는) 명령행 인자를 해석하고 이 스크립트의 전체 작업 순서를 실행합니다.

### `scripts/operations/check_env_contract.py`

개발·운영·보안 점검 작업을 수행합니다.

- **함수 `parse_env_template(path: Path)`** · check_env_contract.py:28
  - 기능: `parse_env_template`은(는) 원시 입력을 해석하고 필요한 값을 정규화해 추출합니다.
- **함수 `settings_variables(path: Path)`** · check_env_contract.py:52
  - 기능: `settings_variables`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `compose_variables(path: Path)`** · check_env_contract.py:68
  - 기능: `compose_variables`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `secret_placeholder_violations(values: dict[str, str])`** · check_env_contract.py:74
  - 기능: `secret_placeholder_violations`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `validate_contract(template_path: Path=ENV_TEMPLATE, settings_path: Path=SETTINGS_MODULE, compose_path: Path=COMPOSE_FILE)`** · check_env_contract.py:90
  - 기능: `validate_contract`은(는) 입력 또는 현재 상태가 규칙을 만족하는지 검증합니다.
- **함수 `main()`** · check_env_contract.py:111
  - 기능: `main`은(는) 명령행 인자를 해석하고 이 스크립트의 전체 작업 순서를 실행합니다.

### `scripts/operations/check_production_env.py`

개발·운영·보안 점검 작업을 수행합니다.

- **함수 `_enabled(value: str | None)`** · check_production_env.py:20
  - 기능: `_enabled`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_usable_secret(value: str | None, *, minimum: int=1)`** · check_production_env.py:26
  - 기능: `_usable_secret`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_parsed_url(value: str | None)`** · check_production_env.py:33
  - 기능: `_parsed_url`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_choice(values: dict[str, str], name: str, allowed: set[str], *, default: str, violations: list[str])`** · check_production_env.py:42
  - 기능: `_choice`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_active_http_provider_urls(values: dict[str, str], *, stock_provider: str, financial_provider: str, disclosure_provider: str, news_provider: str, investor_flow_provider: str, ai_report_provider: str)`** · check_production_env.py:58
  - 기능: `_active_http_provider_urls`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `validate_production_environment(values: dict[str, str])`** · check_production_env.py:89
  - 기능: `validate_production_environment`은(는) 입력 또는 현재 상태가 규칙을 만족하는지 검증합니다.
- **함수 `main()`** · check_production_env.py:267
  - 기능: `main`은(는) 명령행 인자를 해석하고 이 스크립트의 전체 작업 순서를 실행합니다.

### `scripts/operations/check_repository_hygiene.py`

개발·운영·보안 점검 작업을 수행합니다.

- **함수 `tracked_paths()`** · check_repository_hygiene.py:43
  - 기능: `tracked_paths`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `path_violation(path: PurePosixPath)`** · check_repository_hygiene.py:59
  - 기능: `path_violation`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `main()`** · check_repository_hygiene.py:80
  - 기능: `main`은(는) 명령행 인자를 해석하고 이 스크립트의 전체 작업 순서를 실행합니다.

### `scripts/operations/ensure_declaration_docs.py`

개발·운영·보안 점검 작업을 수행합니다.

- **함수 `parse_args()`** · ensure_declaration_docs.py:31
  - 기능: 점검 또는 실제 보완 모드를 선택한다.
- **함수 `python_description(node: ast.AST)`** · ensure_declaration_docs.py:39
  - 기능: AST 선언 종류와 이름을 기반으로 호출자 관점의 설명을 만든다.
- **함수 `document_python(path: Path, *, apply: bool)`** · ensure_declaration_docs.py:52
  - 기능: 본문 첫 줄에 docstring이 없는 다중 행 Python 선언을 보완한다.
- **함수 `has_jsdoc(lines: list[str], index: int)`** · ensure_declaration_docs.py:91
  - 기능: 선언 바로 앞의 공백을 건너뛴 마지막 블록이 JSDoc인지 확인한다.
- **함수 `typescript_description(path: Path, match: re.Match[str])`** · ensure_declaration_docs.py:100
  - 기능: TypeScript 선언 종류에 맞는 외부 계약 설명을 만든다.
- **함수 `document_typescript(path: Path, *, apply: bool)`** · ensure_declaration_docs.py:111
  - 기능: 인터페이스·클래스·공개 함수 선언 바로 위에 JSDoc을 추가한다.
- **함수 `files(roots: tuple[Path, ...], patterns: tuple[str, ...])`** · ensure_declaration_docs.py:133
  - 기능: 생성물과 의존성 디렉터리를 제외한 소스 파일을 반환한다.
- **함수 `main()`** · ensure_declaration_docs.py:143
  - 기능: 선언 설명 누락 수를 보고하고 apply 모드에서는 소스를 보완한다.

### `scripts/operations/ensure_source_headers.py`

개발·운영·보안 점검 작업을 수행합니다.

- **함수 `parse_args()`** · ensure_source_headers.py:49
  - 기능: 점검 전용 또는 실제 보완 모드를 선택한다.
- **함수 `role(path: Path)`** · ensure_source_headers.py:57
  - 기능: 저장소 상대 경로를 가장 가까운 계층 책임으로 변환한다.
- **함수 `description(path: Path)`** · ensure_source_headers.py:64
  - 기능: 파일 이름과 계층을 결합해 한 줄짜리 책임 설명을 만든다.
- **함수 `document_python(path: Path, *, apply: bool)`** · ensure_source_headers.py:73
  - 기능: Python 모듈 docstring이 없을 때 파일 첫 부분에 한글 책임을 추가한다.
- **함수 `document_typescript(path: Path, *, apply: bool)`** · ensure_source_headers.py:88
  - 기능: TypeScript 파일의 첫 import 앞에 모듈 책임 JSDoc이 없으면 추가한다.
- **함수 `source_files(roots: tuple[Path, ...], patterns: tuple[str, ...])`** · ensure_source_headers.py:108
  - 기능: 지정한 소스 루트에서 생성 디렉터리를 제외한 파일을 순서대로 반환한다.
- **함수 `main()`** · ensure_source_headers.py:118
  - 기능: 누락 목록을 점검하고 apply 모드에서는 같은 목록을 원자적 파일 쓰기로 보완한다.

### `scripts/operations/rotate_local_docker_secrets.py`

개발·운영·보안 점검 작업을 수행합니다.

- **함수 `parse_args()`** · rotate_local_docker_secrets.py:19
  - 기능: `parse_args`은(는) 원시 입력을 해석하고 필요한 값을 정규화해 추출합니다.
- **함수 `_strong(value: str, minimum: int)`** · rotate_local_docker_secrets.py:28
  - 기능: `_strong`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_read_values(path: Path)`** · rotate_local_docker_secrets.py:38
  - 기능: `_read_values`은(는) 필요한 데이터를 조회해 반환합니다.
- **함수 `_database_url(current: str, password: str)`** · rotate_local_docker_secrets.py:53
  - 기능: `_database_url`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `rotate_env(path: Path, *, force: bool=False)`** · rotate_local_docker_secrets.py:67
  - 기능: `rotate_env`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `main()`** · rotate_local_docker_secrets.py:114
  - 기능: `main`은(는) 명령행 인자를 해석하고 이 스크립트의 전체 작업 순서를 실행합니다.

### `scripts/operations/smoke_local_ai_providers.py`

개발·운영·보안 점검 작업을 수행합니다.

- **함수 `parse_args()`** · smoke_local_ai_providers.py:21
  - 기능: `parse_args`은(는) 원시 입력을 해석하고 필요한 값을 정규화해 추출합니다.
- **함수 `_feature_count(values: dict[str, float] | None)`** · smoke_local_ai_providers.py:31
  - 기능: `_feature_count`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_check_sec(settings: Settings, symbol: str)`** · smoke_local_ai_providers.py:37
  - 기능: `_check_sec`은(는) 입력 또는 현재 상태가 규칙을 만족하는지 검증합니다.
- **함수 `_check_fred(settings: Settings, _symbol: str)`** · smoke_local_ai_providers.py:52
  - 기능: `_check_fred`은(는) 입력 또는 현재 상태가 규칙을 만족하는지 검증합니다.
- **함수 `_check_finra(settings: Settings, symbol: str)`** · smoke_local_ai_providers.py:67
  - 기능: `_check_finra`은(는) 입력 또는 현재 상태가 규칙을 만족하는지 검증합니다.
- **함수 `_check_news(settings: Settings, symbol: str)`** · smoke_local_ai_providers.py:84
  - 기능: `_check_news`은(는) 입력 또는 현재 상태가 규칙을 만족하는지 검증합니다.
- **함수 `_success(provider: str, features: int)`** · smoke_local_ai_providers.py:101
  - 기능: `_success`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `_missing(provider: str)`** · smoke_local_ai_providers.py:108
  - 기능: `_missing`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `main()`** · smoke_local_ai_providers.py:115
  - 기능: `main`은(는) 명령행 인자를 해석하고 이 스크립트의 전체 작업 순서를 실행합니다.

### `scripts/operations/smoke_toss_provider.py`

개발·운영·보안 점검 작업을 수행합니다.

- **함수 `parse_args()`** · smoke_toss_provider.py:15
  - 기능: `parse_args`은(는) 원시 입력을 해석하고 필요한 값을 정규화해 추출합니다.
- **함수 `main()`** · smoke_toss_provider.py:24
  - 기능: `main`은(는) 명령행 인자를 해석하고 이 스크립트의 전체 작업 순서를 실행합니다.

### `scripts/operations/soak_kis_realtime.py`

개발·운영·보안 점검 작업을 수행합니다.

- **함수 `parse_args()`** · soak_kis_realtime.py:28
  - 기능: `parse_args`은(는) 원시 입력을 해석하고 필요한 값을 정규화해 추출합니다.
- **함수 `safe_output_path(value: Path)`** · soak_kis_realtime.py:43
  - 기능: `safe_output_path`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `normalized_symbols(values: list[str])`** · soak_kis_realtime.py:52
  - 기능: `normalized_symbols`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수 `async run_soak(settings: Settings, symbols: list[str], duration_seconds: int)`** · soak_kis_realtime.py:61
  - 기능: `run_soak`은(는) 비동기로 해당 작업의 전체 처리 흐름을 실행하고 결과를 반환합니다.
- **함수 `save_report(path: Path, report: dict[str, object])`** · soak_kis_realtime.py:128
  - 기능: `save_report`은(는) 데이터를 저장하거나 기존 상태에 추가합니다.
- **함수 `main()`** · soak_kis_realtime.py:137
  - 기능: `main`은(는) 명령행 인자를 해석하고 이 스크립트의 전체 작업 순서를 실행합니다.

## TypeScript 인터페이스·타입·함수

### `frontend/app/admin/page.tsx`

Next.js 화면 진입점과 전역 오류·레이아웃을 담당합니다.

- **함수** · page.tsx:6 · `AdminPage`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `frontend/app/api/admin/alerts/[alertId]/route.ts`

브라우저와 FastAPI 사이의 서버 전용 BFF 경로입니다.

- **함수** · route.ts:6 · `DELETE`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `frontend/app/api/admin/alerts/evaluate/route.ts`

브라우저와 FastAPI 사이의 서버 전용 BFF 경로입니다.

- **함수** · route.ts:6 · `POST`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `frontend/app/api/admin/alerts/route.ts`

브라우저와 FastAPI 사이의 서버 전용 BFF 경로입니다.

- **함수** · route.ts:6 · `GET`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · route.ts:12 · `POST`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `frontend/app/api/admin/backtests/[runId]/route.ts`

브라우저와 FastAPI 사이의 서버 전용 BFF 경로입니다.

- **함수** · route.ts:6 · `GET`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `frontend/app/api/admin/backtests/compare/route.ts`

브라우저와 FastAPI 사이의 서버 전용 BFF 경로입니다.

- **함수** · route.ts:6 · `POST`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `frontend/app/api/admin/backtests/route.ts`

브라우저와 FastAPI 사이의 서버 전용 BFF 경로입니다.

- **함수** · route.ts:6 · `GET`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `frontend/app/api/admin/backtests/strategies/compare/route.ts`

브라우저와 FastAPI 사이의 서버 전용 BFF 경로입니다.

- **함수** · route.ts:6 · `POST`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `frontend/app/api/admin/backtests/walk-forward/route.ts`

브라우저와 FastAPI 사이의 서버 전용 BFF 경로입니다.

- **함수** · route.ts:6 · `POST`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `frontend/app/api/admin/broker-accounts/route.ts`

브라우저와 FastAPI 사이의 서버 전용 BFF 경로입니다.

- **함수** · route.ts:6 · `GET`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `frontend/app/api/admin/candles/price-basis-inventory/route.ts`

브라우저와 FastAPI 사이의 서버 전용 BFF 경로입니다.

- **함수** · route.ts:6 · `GET`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `frontend/app/api/admin/corporate-actions/approvals/[source]/[symbol]/route.ts`

브라우저와 FastAPI 사이의 서버 전용 BFF 경로입니다.

- **함수** · route.ts:6 · `POST`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `frontend/app/api/admin/corporate-actions/approvals/route.ts`

브라우저와 FastAPI 사이의 서버 전용 BFF 경로입니다.

- **함수** · route.ts:6 · `GET`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `frontend/app/api/admin/corporate-actions/candidates/[source]/[symbol]/route.ts`

브라우저와 FastAPI 사이의 서버 전용 BFF 경로입니다.

- **함수** · route.ts:6 · `GET`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `frontend/app/api/admin/corporate-actions/candidates/route.ts`

브라우저와 FastAPI 사이의 서버 전용 BFF 경로입니다.

- **함수** · route.ts:6 · `GET`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `frontend/app/api/admin/corporate-actions/ingestion/[source]/[symbol]/route.ts`

브라우저와 FastAPI 사이의 서버 전용 BFF 경로입니다.

- **함수** · route.ts:6 · `POST`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `frontend/app/api/admin/corporate-actions/ingestion/route.ts`

브라우저와 FastAPI 사이의 서버 전용 BFF 경로입니다.

- **함수** · route.ts:6 · `GET`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `frontend/app/api/admin/corporate-actions/route.ts`

브라우저와 FastAPI 사이의 서버 전용 BFF 경로입니다.

- **함수** · route.ts:6 · `GET`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `frontend/app/api/admin/data-lifecycle/cleanup/route.ts`

브라우저와 FastAPI 사이의 서버 전용 BFF 경로입니다.

- **함수** · route.ts:6 · `POST`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `frontend/app/api/admin/data-lifecycle/preview/route.ts`

브라우저와 FastAPI 사이의 서버 전용 BFF 경로입니다.

- **함수** · route.ts:6 · `GET`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `frontend/app/api/admin/data-quality/route.ts`

브라우저와 FastAPI 사이의 서버 전용 BFF 경로입니다.

- **함수** · route.ts:6 · `GET`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `frontend/app/api/admin/ingestion/[symbol]/route.ts`

브라우저와 FastAPI 사이의 서버 전용 BFF 경로입니다.

- **함수** · route.ts:6 · `POST`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `frontend/app/api/admin/ingestion/route.ts`

브라우저와 FastAPI 사이의 서버 전용 BFF 경로입니다.

- **함수** · route.ts:6 · `GET`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `frontend/app/api/admin/local-ai/readiness/route.ts`

브라우저와 FastAPI 사이의 서버 전용 BFF 경로입니다.

- **함수** · route.ts:6 · 관리자 세션을 유지한 채 AI 품질 요약을 조회한다.

### `frontend/app/api/admin/models/[version]/promote/route.ts`

브라우저와 FastAPI 사이의 서버 전용 BFF 경로입니다.

- **인터페이스** · route.ts:6 · `RouteContext` 인터페이스는 RouteContext 인터페이스는 브라우저와 FastAPI 사이의 서버 전용 BFF 경로입니다.에서 교환하는 필드 계약을 정의합니다. 주요 필드: `params`.
- **함수** · route.ts:11 · `POST`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `frontend/app/api/admin/models/route.ts`

브라우저와 FastAPI 사이의 서버 전용 BFF 경로입니다.

- **함수** · route.ts:6 · `GET`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `frontend/app/api/admin/operations/status/route.ts`

브라우저와 FastAPI 사이의 서버 전용 BFF 경로입니다.

- **함수** · route.ts:6 · `GET`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `frontend/app/api/admin/portfolios/[accountSeq]/sync/route.ts`

브라우저와 FastAPI 사이의 서버 전용 BFF 경로입니다.

- **함수** · route.ts:6 · `POST`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `frontend/app/api/admin/provider-audits/cleanup/route.ts`

브라우저와 FastAPI 사이의 서버 전용 BFF 경로입니다.

- **함수** · route.ts:6 · `POST`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `frontend/app/api/admin/provider-audits/route.ts`

브라우저와 FastAPI 사이의 서버 전용 BFF 경로입니다.

- **함수** · route.ts:6 · `GET`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `frontend/app/api/admin/toss/accounts/[accountSeq]/workspace/route.ts`

브라우저와 FastAPI 사이의 서버 전용 BFF 경로입니다.

- **함수** · route.ts:6 · `GET`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `frontend/app/api/admin/watchlist/[symbol]/route.ts`

브라우저와 FastAPI 사이의 서버 전용 BFF 경로입니다.

- **함수** · route.ts:6 · `DELETE`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `frontend/app/api/admin/watchlist/route.ts`

브라우저와 FastAPI 사이의 서버 전용 BFF 경로입니다.

- **함수** · route.ts:6 · `GET`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · route.ts:11 · `POST`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `frontend/app/api/analysis/[symbol]/route.ts`

브라우저와 FastAPI 사이의 서버 전용 BFF 경로입니다.

- **함수** · route.ts:10 · `GET`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `frontend/app/api/market/[...path]/route.ts`

브라우저와 FastAPI 사이의 서버 전용 BFF 경로입니다.

- **함수** · route.ts:6 · `GET`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `frontend/app/api/paper/[...path]/route.ts`

브라우저와 FastAPI 사이의 서버 전용 BFF 경로입니다.

- **함수** · route.ts:8 · `publicError`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · route.ts:16 · `upstreamPath`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · route.ts:26 · `proxy`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · route.ts:45 · `base`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `frontend/app/error.tsx`

Next.js 화면 진입점과 전역 오류·레이아웃을 담당합니다.

- **인터페이스** · error.tsx:5 · `PageErrorProps` 인터페이스는 error 파일은 Next.js 페이지와 레이아웃 기능을 담당한다. 주요 필드: `error`, `reset`.
- **함수** · error.tsx:11 · `Error`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `frontend/app/global-error.tsx`

Next.js 화면 진입점과 전역 오류·레이아웃을 담당합니다.

- **인터페이스** · global-error.tsx:5 · `GlobalErrorProps` 인터페이스는 global-error 파일은 Next.js 페이지와 레이아웃 기능을 담당한다. 주요 필드: `error`, `reset`.
- **함수** · global-error.tsx:49 · `GlobalError`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `frontend/app/layout.tsx`

Next.js 화면 진입점과 전역 오류·레이아웃을 담당합니다.

- **함수** · layout.tsx:14 · `RootLayout`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `frontend/app/loading.tsx`

Next.js 화면 진입점과 전역 오류·레이아웃을 담당합니다.

- **함수** · loading.tsx:3 · loading 파일은 Next.js 페이지와 레이아웃 기능을 담당한다.

### `frontend/app/market/page.tsx`

Next.js 화면 진입점과 전역 오류·레이아웃을 담당합니다.

- **함수** · page.tsx:7 · `MarketPage`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `frontend/app/not-found.tsx`

Next.js 화면 진입점과 전역 오류·레이아웃을 담당합니다.

- **함수** · not-found.tsx:3 · not-found 파일은 Next.js 페이지와 레이아웃 기능을 담당한다.

### `frontend/app/page.tsx`

Next.js 화면 진입점과 전역 오류·레이아웃을 담당합니다.

- **함수** · page.tsx:7 · `Dashboard`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `frontend/app/paper/page.tsx`

Next.js 화면 진입점과 전역 오류·레이아웃을 담당합니다.

- **함수** · page.tsx:13 · `PaperPortfolioPage`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `frontend/app/providers.tsx`

Next.js 화면 진입점과 전역 오류·레이아웃을 담당합니다.

- **함수** · providers.tsx:9 · `Providers`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `frontend/components/admin/admin-workspace.tsx`

관리자 운영 화면과 상태 조회 기능을 렌더링합니다.

- **타입** · admin-workspace.tsx:13 · `WorkspaceTab` 타입은 허용되는 값의 범위나 여러 데이터 형태의 조합을 제한합니다.
- **함수** · admin-workspace.tsx:15 · `loading`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · admin-workspace.tsx:101 · `tabFromHash`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · admin-workspace.tsx:107 · `AdminWorkspace`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · admin-workspace.tsx:113 · `syncFromUrl`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · admin-workspace.tsx:127 · `activateTab`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · admin-workspace.tsx:143 · `handleTabKeyDown`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `frontend/components/admin/backtest-history.tsx`

관리자 운영 화면과 상태 조회 기능을 렌더링합니다.

- **함수** · backtest-history.tsx:14 · `percent`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · backtest-history.tsx:17 · `number`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · backtest-history.tsx:20 · `time`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · backtest-history.tsx:24 · `BacktestHistoryPanel`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · backtest-history.tsx:46 · `submit`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · backtest-history.tsx:51 · `selectRun`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `frontend/components/admin/candle-price-basis-inventory.tsx`

관리자 운영 화면과 상태 조회 기능을 렌더링합니다.

- **함수** · candle-price-basis-inventory.tsx:37 · `formatDate`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · candle-price-basis-inventory.tsx:43 · `CandlePriceBasisInventoryPanel`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · candle-price-basis-inventory.tsx:55 · `submit`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `frontend/components/admin/corporate-action-history.tsx`

관리자 운영 화면과 상태 조회 기능을 렌더링합니다.

- **인터페이스** · corporate-action-history.tsx:28 · `ApprovalSelection` 인터페이스는 ApprovalSelection 인터페이스는 관리자 운영 화면과 상태 조회 기능을 렌더링합니다.에서 교환하는 필드 계약을 정의합니다. 주요 필드: `candidate`, `groupHint`.
- **함수** · corporate-action-history.tsx:34 · `formatDate`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · corporate-action-history.tsx:41 · `CorporateActionHistoryPanel`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · corporate-action-history.tsx:124 · `submit`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · corporate-action-history.tsx:130 · `previewCandidates`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · corporate-action-history.tsx:135 · `selectApproval`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `frontend/components/admin/data-lifecycle-maintenance.tsx`

관리자 운영 화면과 상태 조회 기능을 렌더링합니다.

- **함수** · data-lifecycle-maintenance.tsx:15 · `date`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · data-lifecycle-maintenance.tsx:21 · `DataLifecycleMaintenancePanel`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · data-lifecycle-maintenance.tsx:41 · `runCleanup`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `frontend/components/admin/data-quality-history.tsx`

관리자 운영 화면과 상태 조회 기능을 렌더링합니다.

- **함수** · data-quality-history.tsx:21 · `date`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · data-quality-history.tsx:28 · `DataQualityHistoryPanel`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · data-quality-history.tsx:41 · `submit`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · data-quality-history.tsx:47 · `changeSeverity`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `frontend/components/admin/engine-comparison.tsx`

관리자 운영 화면과 상태 조회 기능을 렌더링합니다.

- **함수** · engine-comparison.tsx:14 · `percent`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · engine-comparison.tsx:17 · `number`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · engine-comparison.tsx:22 · `currency`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · engine-comparison.tsx:30 · `EngineCard`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · engine-comparison.tsx:58 · `EngineComparisonPanel`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · engine-comparison.tsx:68 · `submit`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `frontend/components/admin/ingestion-control.tsx`

관리자 운영 화면과 상태 조회 기능을 렌더링합니다.

- **함수** · ingestion-control.tsx:10 · `IngestionControlPanel`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · ingestion-control.tsx:31 · `run`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · ingestion-control.tsx:35 · `submit`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `frontend/components/admin/local-ai-readiness.tsx`

관리자 운영 화면과 상태 조회 기능을 렌더링합니다.

- **함수** · local-ai-readiness.tsx:30 · 0~1 지표를 읽기 쉬운 백분율로 표시한다.
- **함수** · local-ai-readiness.tsx:35 · 품질 게이트의 기계 판정 사유를 한국어 운영 문구로 바꾼다.
- **함수** · local-ai-readiness.tsx:43 · 직접 학습 AI 모델들의 현재 검증 상태를 자동 갱신하는 패널이다.

### `frontend/components/admin/model-registry.tsx`

관리자 운영 화면과 상태 조회 기능을 렌더링합니다.

- **함수** · model-registry.tsx:13 · `ModelRegistryPanel`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · model-registry.tsx:35 · `submit`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · model-registry.tsx:40 · `promote`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `frontend/components/admin/operations-status.tsx`

관리자 운영 화면과 상태 조회 기능을 렌더링합니다.

- **함수** · operations-status.tsx:38 · `checkedAt`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · operations-status.tsx:44 · `OperationsStatusPanel`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `frontend/components/admin/portfolio-analysis.tsx`

관리자 운영 화면과 상태 조회 기능을 렌더링합니다.

- **함수** · portfolio-analysis.tsx:15 · `number`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · portfolio-analysis.tsx:17 · `percent`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · portfolio-analysis.tsx:19 · `findNumber`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · portfolio-analysis.tsx:33 · `findArrayCount`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · portfolio-analysis.tsx:44 · `PortfolioAnalysis`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · portfolio-analysis.tsx:59 · `synchronize`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `frontend/components/admin/provider-audit-history.tsx`

관리자 운영 화면과 상태 조회 기능을 렌더링합니다.

- **함수** · provider-audit-history.tsx:22 · `date`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · provider-audit-history.tsx:28 · `requestId`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · provider-audit-history.tsx:33 · `ProviderAuditHistoryPanel`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · provider-audit-history.tsx:55 · `changeProvider`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · provider-audit-history.tsx:60 · `changeOutcome`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · provider-audit-history.tsx:65 · `runCleanup`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `frontend/components/admin/strategy-comparison.tsx`

관리자 운영 화면과 상태 조회 기능을 렌더링합니다.

- **함수** · strategy-comparison.tsx:20 · `percent`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · strategy-comparison.tsx:23 · `signedPercent`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · strategy-comparison.tsx:26 · `number`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · strategy-comparison.tsx:31 · `currency`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · strategy-comparison.tsx:37 · `StrategyComparisonPanel`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · strategy-comparison.tsx:49 · `submit`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `frontend/components/admin/walk-forward-validation.tsx`

관리자 운영 화면과 상태 조회 기능을 렌더링합니다.

- **함수** · walk-forward-validation.tsx:13 · `percent`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · walk-forward-validation.tsx:16 · `number`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · walk-forward-validation.tsx:21 · `date`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · walk-forward-validation.tsx:31 · `WalkForwardValidationPanel`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · walk-forward-validation.tsx:43 · `submit`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `frontend/components/admin/watchlist-alerts.tsx`

관리자 운영 화면과 상태 조회 기능을 렌더링합니다.

- **함수** · watchlist-alerts.tsx:18 · `price`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · watchlist-alerts.tsx:22 · `WatchlistAlerts`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · watchlist-alerts.tsx:46 · `run`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · watchlist-alerts.tsx:61 · `submitWatchlist`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · watchlist-alerts.tsx:69 · `submitAlert`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · watchlist-alerts.tsx:81 · `evaluate`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `frontend/components/analysis/agent-meeting-stage.tsx`

AI 분석 진행과 결과 표현을 담당합니다.

- **타입** · agent-meeting-stage.tsx:13 · `MeetingAgentKey` 타입은 허용되는 값의 범위나 여러 데이터 형태의 조합을 제한합니다.
- **타입** · agent-meeting-stage.tsx:14 · `MeetingPhase` 타입은 허용되는 값의 범위나 여러 데이터 형태의 조합을 제한합니다.
- **인터페이스** · agent-meeting-stage.tsx:17 · `MeetingSceneAgent` 인터페이스는 MeetingSceneAgent 인터페이스는 AI 분석 진행과 결과 표현을 담당합니다.에서 교환하는 필드 계약을 정의합니다. 주요 필드: `agent`, `name`, `role`.
- **인터페이스** · agent-meeting-stage.tsx:24 · `ChefMenu` 인터페이스는 ChefMenu 인터페이스는 AI 분석 진행과 결과 표현을 담당합니다.에서 교환하는 필드 계약을 정의합니다. 주요 필드: `chefName`, `course`, `dish`, `ingredient`.
- **인터페이스** · agent-meeting-stage.tsx:66 · `AnalystAvatarProps` 인터페이스는 AnalystAvatarProps 인터페이스는 AI 분석 진행과 결과 표현을 담당합니다.에서 교환하는 필드 계약을 정의합니다. 주요 필드: `agent`, `size`.
- **인터페이스** · agent-meeting-stage.tsx:72 · `AgentMeetingStageProps` 인터페이스는 AgentMeetingStageProps 인터페이스는 AI 분석 진행과 결과 표현을 담당합니다.에서 교환하는 필드 계약을 정의합니다. 주요 필드: `agents`, `phase`, `revealedCount`, `complete`, `loading`, `cinematicDialog`, `initialFocusRef`, `restoreFocusRef`, `onCinematicEnter`, `onCinematicExit`, `onReplay`, `onSkip`.
- **함수** · agent-meeting-stage.tsx:96 · `AnalystAvatar`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · agent-meeting-stage.tsx:113 · `sceneMessage`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · agent-meeting-stage.tsx:175 · `AgentMeetingStage`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · agent-meeting-stage.tsx:262 · `handleDialogKeyDown`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `frontend/components/analysis/analysis-progress.tsx`

AI 분석 진행과 결과 표현을 담당합니다.

- **인터페이스** · analysis-progress.tsx:24 · `AnalysisProgressProps` 인터페이스는 AI 사무실의 진행 단계, 참여 가능한 전문가, 재생 제어를 전달하는 컴포넌트 계약입니다. 주요 필드: `agents`, `availableAgentKeys`, `complete`, `loading`, `onReplay`, `onSkip`, `phase`, `revealedCount`.
- **인터페이스** · analysis-progress.tsx:36 · `PixelAnalystProps` 인터페이스는 전문가 종류에 맞는 픽셀 캐릭터와 표시 크기를 선택하는 입력 계약입니다. 주요 필드: `agent`, `size`.
- **함수** · analysis-progress.tsx:49 · `roomForPhase`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · analysis-progress.tsx:58 · `phaseLabel`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · analysis-progress.tsx:68 · `agentState`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · analysis-progress.tsx:85 · `stateLabel`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · analysis-progress.tsx:94 · `PixelAnalyst`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · analysis-progress.tsx:112 · `TypingBubble`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · analysis-progress.tsx:138 · `AnalysisProgress`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · analysis-progress.tsx:164 · `closeOnEscape`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `frontend/components/analysis/analysis-result.tsx`

AI 분석 진행과 결과 표현을 담당합니다.

- **인터페이스** · analysis-result.tsx:39 · `AnalysisResultProps` 인터페이스는 종목 식별 정보와 현재 시세를 분석 결과 화면에 전달하는 컴포넌트 입력 계약입니다. 주요 필드: `autoRun`, `activeAgent`, `symbol`, `name`, `market`, `currency`, `currentPrice`, `changePercent`.
- **인터페이스** · analysis-result.tsx:94 · `MeetingPresentationState` 인터페이스는 분석 회의 애니메이션에서 현재 단계와 공개된 전문가 수를 관리하는 화면 상태입니다. 주요 필드: `announcement`, `complete`, `phase`, `revealedCount`.
- **인터페이스** · analysis-result.tsx:102 · `MeetingEntry` 인터페이스는 전문가 한 명의 화면 표시 정보에 데이터 가용성, 근거, 실험 모델 여부를 결합한 계약입니다. 주요 필드: `availability`, `dataAsOf`, `details`, `experimental`, `headline`.
- **함수** · analysis-result.tsx:113 · `fallbackMeetingContent`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · analysis-result.tsx:144 · `meetingFromReport`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · analysis-result.tsx:227 · `useMeetingPresentation`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · analysis-result.tsx:256 · `showAll`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · analysis-result.tsx:341 · `formatLevel`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · analysis-result.tsx:351 · `formatCurrentPrice`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · analysis-result.tsx:357 · `formatChangePercent`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · analysis-result.tsx:365 · `liveStageLabel`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · analysis-result.tsx:374 · `analysisFreshness`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · analysis-result.tsx:384 · `Report`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · analysis-result.tsx:445 · `copySharePayload`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · analysis-result.tsx:464 · `share`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · analysis-result.tsx:689 · `AnalysisResult`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · analysis-result.tsx:711 · `scrollToAgent`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `frontend/components/analysis/final-verdict-modal.tsx`

AI 분석 진행과 결과 표현을 담당합니다.

- **인터페이스** · final-verdict-modal.tsx:13 · `VerdictTranscript` 인터페이스는 VerdictTranscript 인터페이스는 AI 분석 진행과 결과 표현을 담당합니다.에서 교환하는 필드 계약을 정의합니다. 주요 필드: `agent`, `experimental`, `name`, `role`, `headline`.
- **인터페이스** · final-verdict-modal.tsx:22 · `FinalVerdictModalProps` 인터페이스는 FinalVerdictModalProps 인터페이스는 AI 분석 진행과 결과 표현을 담당합니다.에서 교환하는 필드 계약을 정의합니다. 주요 필드: `currency`, `currentPrice`, `inline`, `name`, `onClose`, `open`, `report`, `transcript`.
- **함수** · final-verdict-modal.tsx:58 · `validationSamples`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · final-verdict-modal.tsx:65 · `probabilityBand`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · final-verdict-modal.tsx:71 · `formatPrice`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · final-verdict-modal.tsx:80 · `FinalVerdictModal`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · final-verdict-modal.tsx:112 · `closeOnEscape`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · final-verdict-modal.tsx:142 · `verdict`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `frontend/components/analysis/research-details.tsx`

AI 분석 진행과 결과 표현을 담당합니다.

- **타입** · research-details.tsx:20 · `ResearchTab` 타입은 허용되는 값의 범위나 여러 데이터 형태의 조합을 제한합니다.
- **함수** · research-details.tsx:42 · `finite`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · research-details.tsx:49 · `formatAmount`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · research-details.tsx:60 · `formatQuantity`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · research-details.tsx:68 · `formatDate`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · research-details.tsx:74 · `safeExternalUrl`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · research-details.tsx:84 · `ResearchState`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · research-details.tsx:107 · `FinancialPanel`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · research-details.tsx:129 · `ValuationPanel`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · research-details.tsx:130 · `ratio`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · research-details.tsx:156 · `FlowPanel`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · research-details.tsx:177 · `NewsPanel`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · research-details.tsx:204 · `DisclosurePanel`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · research-details.tsx:228 · `ResearchFooter`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · research-details.tsx:233 · `ResearchDetails`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · research-details.tsx:285 · `tabId`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · research-details.tsx:287 · `activateTab`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · research-details.tsx:294 · `handleTabKeyDown`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `frontend/components/analysis/technical-snapshot.tsx`

AI 분석 진행과 결과 표현을 담당합니다.

- **함수** · technical-snapshot.tsx:32 · `number`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · technical-snapshot.tsx:39 · `price`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · technical-snapshot.tsx:48 · `latestValues`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · technical-snapshot.tsx:66 · `TechnicalSnapshot`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `frontend/components/market/market-dashboard.tsx`

종목 검색·차트·시장 데이터 화면을 담당합니다.

- **인터페이스** · market-dashboard.tsx:47 · `DashboardStock` 인터페이스는 DashboardStock 인터페이스는 종목 검색·차트·시장 데이터 화면을 담당합니다.에서 교환하는 필드 계약을 정의합니다. 주요 필드: `symbol`, `name`, `market`, `currency`, `aliases`.
- **타입** · market-dashboard.tsx:71 · `RealtimeStatus` 타입은 허용되는 값의 범위나 여러 데이터 형태의 조합을 제한합니다.
- **타입** · market-dashboard.tsx:72 · `AgentFocus` 타입은 허용되는 값의 범위나 여러 데이터 형태의 조합을 제한합니다.
- **타입** · market-dashboard.tsx:73 · `ServiceNoticeTone` 타입은 허용되는 값의 범위나 여러 데이터 형태의 조합을 제한합니다.
- **타입** · market-dashboard.tsx:95 · `HistoryMode` 타입은 허용되는 값의 범위나 여러 데이터 형태의 조합을 제한합니다.
- **함수** · market-dashboard.tsx:104 · `syncResultUrl`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · market-dashboard.tsx:115 · `clearResultUrl`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · market-dashboard.tsx:126 · `isDashboardStock`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · market-dashboard.tsx:141 · `useRealtimeQuote`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · market-dashboard.tsx:160 · `clearRetryTimer`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · market-dashboard.tsx:166 · `disconnectSocket`은(는) 연결 또는 메시지 전달 생명주기를 관리합니다.
- **함수** · market-dashboard.tsx:176 · `connect`은(는) 연결 또는 메시지 전달 생명주기를 관리합니다.
- **함수** · market-dashboard.tsx:230 · `handleOffline`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · market-dashboard.tsx:236 · `handleOnline`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · market-dashboard.tsx:267 · `formatPrice`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · market-dashboard.tsx:279 · `formatChange`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · market-dashboard.tsx:287 · `MarketDashboard`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · market-dashboard.tsx:363 · `handleOffline`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · market-dashboard.tsx:367 · `handleOnline`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · market-dashboard.tsx:452 · `rememberStock`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · market-dashboard.tsx:464 · `clearRecentStocks`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · market-dashboard.tsx:474 · `toggleWatchlist`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · market-dashboard.tsx:488 · `copyShareLink`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · market-dashboard.tsx:517 · `lookupStock`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · market-dashboard.tsx:600 · `search`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · market-dashboard.tsx:605 · `selectKnownStock`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · market-dashboard.tsx:612 · `resetSelection`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · market-dashboard.tsx:639 · `focusSearch`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · market-dashboard.tsx:651 · `handlePopState`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · market-dashboard.tsx:686 · `handleSearchKeyDown`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `frontend/components/market/market-microstructure.tsx`

종목 검색·차트·시장 데이터 화면을 담당합니다.

- **타입** · market-microstructure.tsx:10 · `MarketDetailTab` 타입은 허용되는 값의 범위나 여러 데이터 형태의 조합을 제한합니다.
- **인터페이스** · market-microstructure.tsx:13 · `MarketMicrostructureProps` 인터페이스는 MarketMicrostructureProps 인터페이스는 종목 검색·차트·시장 데이터 화면을 담당합니다.에서 교환하는 필드 계약을 정의합니다. 주요 필드: `currency`, `symbol`.
- **함수** · market-microstructure.tsx:19 · `formatNumber`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · market-microstructure.tsx:27 · `MarketMicrostructure`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `frontend/components/market/market-overview-dashboard.tsx`

종목 검색·차트·시장 데이터 화면을 담당합니다.

- **함수** · market-overview-dashboard.tsx:36 · `compactNumber`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · market-overview-dashboard.tsx:44 · `MarketOverviewDashboard`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `frontend/components/market/market-pulse.tsx`

종목 검색·차트·시장 데이터 화면을 담당합니다.

- **인터페이스** · market-pulse.tsx:10 · `MarketPulseProps` 인터페이스는 MarketPulseProps 인터페이스는 종목 검색·차트·시장 데이터 화면을 담당합니다.에서 교환하는 필드 계약을 정의합니다. 주요 필드: `onSelectSymbol`.
- **함수** · market-pulse.tsx:21 · `MarketPulse`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `frontend/components/market/stock-chart.tsx`

종목 검색·차트·시장 데이터 화면을 담당합니다.

- **함수** · stock-chart.tsx:20 · `movingAverage`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · stock-chart.tsx:38 · `chartDescription`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · stock-chart.tsx:57 · `StockChart`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `frontend/components/market/toss-stock-trends.tsx`

종목 검색·차트·시장 데이터 화면을 담당합니다.

- **타입** · toss-stock-trends.tsx:10 · `TrendKey` 타입은 허용되는 값의 범위나 여러 데이터 형태의 조합을 제한합니다.
- **함수** · toss-stock-trends.tsx:21 · `findRows`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · toss-stock-trends.tsx:29 · `visibleEntries`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · toss-stock-trends.tsx:36 · `TossStockTrendsPanel`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `frontend/components/paper/paper-portfolio-dashboard.tsx`

모의투자 주문과 자산 화면을 담당합니다.

- **타입** · paper-portfolio-dashboard.tsx:20 · `Currency` 타입은 허용되는 값의 범위나 여러 데이터 형태의 조합을 제한합니다.
- **함수** · paper-portfolio-dashboard.tsx:23 · `money`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · paper-portfolio-dashboard.tsx:32 · `percent`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · paper-portfolio-dashboard.tsx:38 · `dateTime`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · paper-portfolio-dashboard.tsx:48 · `PaperPortfolioDashboard`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `frontend/components/paper/paper-trading-panel.tsx`

모의투자 주문과 자산 화면을 담당합니다.

- **함수** · paper-trading-panel.tsx:15 · `money`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **인터페이스** · paper-trading-panel.tsx:24 · `Props` 인터페이스는 Props 인터페이스는 모의투자 주문과 자산 화면을 담당합니다.에서 교환하는 필드 계약을 정의합니다. 주요 필드: `symbol`, `name`, `currency`, `currentPrice`.
- **함수** · paper-trading-panel.tsx:32 · `PaperTradingPanel`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · paper-trading-panel.tsx:55 · `submit`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · paper-trading-panel.tsx:75 · `reset`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `frontend/components/shared/normalized-equity-chart.tsx`

공통 사용자 화면과 상호작용을 렌더링합니다.

- **인터페이스** · normalized-equity-chart.tsx:3 · `NormalizedEquityPoint` 인터페이스는 normalized-equity-chart 파일은 공유 화면 컴포넌트 기능을 담당한다. 주요 필드: `timestamp`, `normalized_equity`, `drawdown`.
- **인터페이스** · normalized-equity-chart.tsx:10 · `EquitySeries` 인터페이스는 EquitySeries 인터페이스는 공통 사용자 화면과 상호작용을 렌더링합니다.에서 교환하는 필드 계약을 정의합니다. 주요 필드: `name`, `color`, `points`.
- **인터페이스** · normalized-equity-chart.tsx:17 · `NormalizedEquityChartProps` 인터페이스는 NormalizedEquityChartProps 인터페이스는 공통 사용자 화면과 상호작용을 렌더링합니다.에서 교환하는 필드 계약을 정의합니다. 주요 필드: `title`, `ariaLabel`, `series`, `footerNote`.
- **함수** · normalized-equity-chart.tsx:25 · `NormalizedEquityChart`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · normalized-equity-chart.tsx:51 · `polyline`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `frontend/features/office/analysis-contract.ts`

화면 기능별 상태와 도메인 이벤트를 관리합니다.

- **인터페이스** · analysis-contract.ts:5 · `OfficeAnalysisAgent` 인터페이스는 전문 AI 한 명의 분석 결과를 사무실 UI가 공통 방식으로 소비하기 위한 계약입니다. 식별·배치 정보, 보정된 확률, 데이터 품질, 검증 성능, 주요 근거를 함께 전달합니다. 주요 필드: `id`, `name`, `role`, `room`, `probability`, `calibrated_band`, `data_available`, `experimental`, `experimental_reason`, `sample_size`, `validation_accuracy`, `baseline_accuracy`, `top_features`.
- **인터페이스** · analysis-contract.ts:25 · `OfficeAnalysisResponse` 인터페이스는 종목 분석 API와 사무실 UI 사이의 최상위 응답 계약입니다. 실제 시세, 최종 판정, 전문가별 결과, 회의 기록과 투자 유의 문구를 한 응답으로 묶습니다. 주요 필드: `analysis_id`, `symbol`, `name`, `market`, `price`, `change_pct`, `currency`, `verdict`, `signal`, `signal_label`, `confidence`, `summary`, `key_points`, `levels`, `entry_zone`, `stop_reference`, `target_reference`, `risk_reward`, `final_note`, `agents`.
- **함수** · analysis-contract.ts:68 · 백엔드 연결 없이 UI 계약만 점검할 때 사용하는 안전한 모의 응답을 만듭니다. 실제로 얻지 않은 가격이나 확률은 만들지 않고 모두 null 또는 데이터 부족으로 표시합니다.

### `frontend/features/office/analysis-events.ts`

화면 기능별 상태와 도메인 이벤트를 관리합니다.

- **타입** · analysis-events.ts:9 · `AgentId` 타입은 허용되는 값의 범위나 여러 데이터 형태의 조합을 제한합니다.
- **타입** · analysis-events.ts:21 · `AnalysisEvent` 타입은 허용되는 값의 범위나 여러 데이터 형태의 조합을 제한합니다.
- **인터페이스** · analysis-events.ts:27 · `AnalysisEventStream` 인터페이스는 시간표에서 발생한 분석 이벤트를 구독하고 해제하는 최소 stream 계약이다. 주요 필드: `subscribe`.
- **함수** · analysis-events.ts:61 · `createTimedAnalysisEventStream`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · analysis-events.ts:74 · `schedule`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `frontend/features/office/office-map.config.ts`

화면 기능별 상태와 도메인 이벤트를 관리합니다.

- **타입** · office-map.config.ts:5 · `OfficeRoomId` 타입은 허용되는 값의 범위나 여러 데이터 형태의 조합을 제한합니다.
- **타입** · office-map.config.ts:6 · `OfficeMotion` 타입은 허용되는 값의 범위나 여러 데이터 형태의 조합을 제한합니다.
- **인터페이스** · office-map.config.ts:9 · `OfficeRoom` 인터페이스는 사무실 구역의 식별자, 화면 라벨, CSS 배치 클래스를 연결하는 설정 계약입니다. 주요 필드: `id`, `label`, `className`.
- **인터페이스** · office-map.config.ts:20 · `OfficeCharacter` 인터페이스는 사무실 캐릭터의 소개 문구, 담당 AI, 동작 종류와 퍼센트 좌표를 정의합니다. agent가 없는 캐릭터는 보조 연출용이고, 있는 캐릭터는 실제 분석 이벤트와 연결됩니다. 주요 필드: `id`, `name`, `role`, `intro`, `motion`, `room`, `agent`, `x`, `y`.

### `frontend/features/office/office-store.ts`

화면 기능별 상태와 도메인 이벤트를 관리합니다.

- **인터페이스** · office-store.ts:7 · `OfficeActivity` 인터페이스는 OfficeActivity 인터페이스는 화면 기능별 상태와 도메인 이벤트를 관리합니다.에서 교환하는 필드 계약을 정의합니다. 주요 필드: `agent`, `id`, `kind`, `message`, `room`.
- **인터페이스** · office-store.ts:21 · `OfficeAnalysisState` 인터페이스는 오피스 화면 값과 그 값을 변경하는 action을 함께 정의하는 Zustand 상태 계약이다. 주요 필드: `activeMessage`, `activeRoom`, `activeSpeaker`, `analysisId`, `events`, `eventSequence`, `status`, `begin`, `complete`, `focusRoom`, `speak`, `reset`.
- **함수** · office-store.ts:47 · `appendEvent`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `frontend/lib/admin-api.ts`

프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.

- **인터페이스** · admin-api.ts:3 · `BacktestMetrics` 인터페이스는 admin-api 파일은 프론트 타입 계약과 API client 기능을 담당한다. 주요 필드: `total_return`, `cagr`, `max_drawdown`, `sharpe_ratio`, `win_rate`, `trade_count`, `final_equity`.
- **인터페이스** · admin-api.ts:14 · `BacktestRunSummary` 인터페이스는 BacktestRunSummary 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. 주요 필드: `run_id`, `symbol`, `strategy`, `status`, `engine`, `engine_version`, `started_at`, `finished_at`, `metrics`.
- **인터페이스** · admin-api.ts:27 · `BacktestHistory` 인터페이스는 BacktestHistory 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. 주요 필드: `persistence_status`, `items`, `total`, `limit`, `offset`.
- **인터페이스** · admin-api.ts:36 · `BacktestRunDetail` 인터페이스는 BacktestRunDetail 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. 주요 필드: `summary`, `config`, `equity_curve`, `trades`, `events`.
- **타입** · admin-api.ts:44 · `BacktestStrategy` 타입은 허용되는 값의 범위나 여러 데이터 형태의 조합을 제한합니다.
- **타입** · admin-api.ts:45 · `BacktestEngineName` 타입은 허용되는 값의 범위나 여러 데이터 형태의 조합을 제한합니다.
- **인터페이스** · admin-api.ts:48 · `BacktestComparisonRequest` 인터페이스는 BacktestComparisonRequest 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. 주요 필드: `symbol`, `strategy`, `limit`, `fast_period`, `slow_period`, `initial_capital`, `commission_rate`, `tax_rate`, `slippage_rate`, `max_volume_participation`.
- **인터페이스** · admin-api.ts:62 · `BacktestEngineComparisonSummary` 인터페이스는 BacktestEngineComparisonSummary 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. 주요 필드: `engine_version`, `metrics`, `equity_curve`, `timestamp`, `normalized_equity`, `drawdown`, `execution`, `fill_count`, `partial_fill_count`, `rejected_order_count`, `volume_limit_applied`.
- **인터페이스** · admin-api.ts:79 · `BacktestEngineComparison` 인터페이스는 BacktestEngineComparison 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. 주요 필드: `comparison_version`, `validation_status`, `symbol`, `provider`, `strategy`, `data_as_of`, `assumptions`, `candle_count`, `initial_capital`, `costs`, `commission_rate`, `tax_rate`, `slippage_rate`, `max_volume_participation`, `same_market_data_snapshot`, `force_close`, `vectorized`, `event_driven`, `deltas`, `total_return`.
- **인터페이스** · admin-api.ts:112 · `BacktestStrategyComparisonRequest` 인터페이스는 BacktestStrategyComparisonRequest 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. 주요 필드: `symbol`, `engine`, `limit`, `fast_period`, `slow_period`, `initial_capital`, `commission_rate`, `tax_rate`, `slippage_rate`, `max_volume_participation`.
- **인터페이스** · admin-api.ts:126 · `BacktestStrategyComparisonItem` 인터페이스는 BacktestStrategyComparisonItem 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. 주요 필드: `strategy`, `metrics`, `equity_curve`, `timestamp`, `normalized_equity`, `drawdown`, `execution`, `fill_count`, `partial_fill_count`, `rejected_order_count`, `deltas_vs_buy_and_hold`, `total_return`, `cagr`, `max_drawdown`, `sharpe_ratio`, `final_equity`, `trade_count`.
- **인터페이스** · admin-api.ts:150 · `BacktestStrategyComparison` 인터페이스는 BacktestStrategyComparison 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. 주요 필드: `comparison_version`, `validation_status`, `symbol`, `provider`, `engine`, `engine_version`, `data_as_of`, `benchmark`, `assumptions`, `candle_count`, `initial_capital`, `costs`, `commission_rate`, `tax_rate`, `slippage_rate`, `max_volume_participation`, `same_market_data_snapshot`, `force_close`, `fast_period`, `slow_period`.
- **인터페이스** · admin-api.ts:178 · `WalkForwardValidationRequest` 인터페이스는 WalkForwardValidationRequest 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. 주요 필드: `symbol`, `strategy`, `engine`, `limit`, `n_splits`, `warmup_candles`, `fast_period`, `slow_period`, `max_volume_participation`.
- **인터페이스** · admin-api.ts:191 · `WalkForwardFold` 인터페이스는 WalkForwardFold 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. 주요 필드: `fold`, `test_started_at`, `test_ended_at`, `test_candles`, `metrics`, `execution`, `partial_fill_count`, `rejected_order_count`.
- **인터페이스** · admin-api.ts:204 · `WalkForwardValidation` 인터페이스는 WalkForwardValidation 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. 주요 필드: `symbol`, `provider`, `engine`, `validation_version`, `validation_status`, `engine_version`, `strategy`, `n_splits`, `warmup_candles`, `data_as_of`, `aggregate`, `mean_total_return`, `profitable_fold_ratio`, `worst_max_drawdown`, `mean_sharpe_ratio`, `total_trade_count`, `total_partial_fill_count`, `total_rejected_order_count`, `stability`, `execution_model`.
- **인터페이스** · admin-api.ts:234 · `ModelVersion` 인터페이스는 ModelVersion 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. 주요 필드: `version`, `symbol`, `algorithm`, `horizon_days`, `validation_status`, `validation_metrics`, `registry_stage`, `data_as_of`, `promoted_at`, `created_at`.
- **인터페이스** · admin-api.ts:248 · `ModelRegistryData` 인터페이스는 ModelRegistryData 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. 주요 필드: `persistence_status`, `runtime_activation_enabled`, `items`, `total`, `limit`, `offset`.
- **인터페이스** · admin-api.ts:258 · `LocalAiReadinessItem` 인터페이스는 직접 학습 모델 하나의 검증 지표와 품질 게이트 결과다. 주요 필드: `agent`, `label`, `scope`, `status`, `model_version`, `trained_at`, `training_samples`, `validation_samples`, `required_validation_samples`, `remaining_validation_samples`, `metrics`, `reasons`.
- **인터페이스** · admin-api.ts:285 · `LocalAiReadinessData` 인터페이스는 직접 학습 AI 전체의 현재 운영 준비도 응답이다. 주요 필드: `enabled`, `generated_at`, `summary`, `total`, `available`, `quality_rejected`, `missing`, `artifact_invalid`, `core_ready`, `items`.
- **인터페이스** · admin-api.ts:300 · `ApiEnvelope` 인터페이스는 ApiEnvelope 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. 주요 필드: `success`, `data`, `error`.
- **인터페이스** · admin-api.ts:307 · `WatchlistItem` 인터페이스는 WatchlistItem 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. 주요 필드: `symbol`, `name`, `market`, `currency`, `created_at`.
- **인터페이스** · admin-api.ts:316 · `PriceAlert` 인터페이스는 PriceAlert 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. 주요 필드: `alert_id`, `symbol`, `condition`, `target_price`, `status`, `created_at`, `last_price`, `last_evaluated_at`, `triggered_at`.
- **인터페이스** · admin-api.ts:329 · `WatchlistData` 인터페이스는 WatchlistData 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. 주요 필드: `persistence_status`, `items`.
- **인터페이스** · admin-api.ts:335 · `PriceAlertData` 인터페이스는 PriceAlertData 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. 주요 필드: `persistence_status`, `items`.
- **인터페이스** · admin-api.ts:341 · `EvaluateResult` 인터페이스는 EvaluateResult 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. 주요 필드: `evaluated`, `triggered`, `failures`, `execution_enabled`.
- **인터페이스** · admin-api.ts:349 · `BrokerAccount` 인터페이스는 BrokerAccount 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. 주요 필드: `account_seq`, `account_no_masked`, `account_type`.
- **인터페이스** · admin-api.ts:356 · `PortfolioCurrencyAnalysis` 인터페이스는 PortfolioCurrencyAnalysis 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. 주요 필드: `holding_count`, `market_value`, `purchase_amount`, `profit_loss_after_cost`, `profit_rate_after_cost`, `profitable_count`, `loss_making_count`, `largest_symbol`, `largest_allocation`, `concentration_index`, `effective_holding_count`, `concentration_level`, `loss_exposure`, `risk_flags`.
- **인터페이스** · admin-api.ts:374 · `PortfolioSyncResult` 인터페이스는 PortfolioSyncResult 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. 주요 필드: `provider`, `account`, `holdings`, `symbol`, `name`, `currency`, `market_value`, `profit_loss_after_cost`, `allocation_within_currency`, `analysis`, `analysis_version`, `currency_separated`, `currencies`, `reference_signal`, `experimental`, `execution_enabled`, `data_as_of`, `is_read_only`, `persistence_status`.
- **인터페이스** · admin-api.ts:399 · `TossAccountWorkspace` 인터페이스는 TossAccountWorkspace 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. 주요 필드: `provider`, `holdings`, `buying_power`, `commissions`, `orders`, `open`, `closed`, `conditional_orders`, `trading_enabled`, `partial_errors`.
- **인터페이스** · admin-api.ts:417 · `DependencyStatus` 인터페이스는 DependencyStatus 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. 주요 필드: `status`, `required`, `latency_ms`, `error_type`.
- **인터페이스** · admin-api.ts:425 · `OperationsStatus` 인터페이스는 OperationsStatus 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. 주요 필드: `status`, `ready`, `service`, `release`, `environment`, `checked_at`, `readiness`, `checks`, `providers`, `features`, `realtime`, `source`, `max_symbols`, `max_connections`, `poll_interval_seconds`, `partitions`, `dialect`, `items`, `lookahead_months`, `archive_plan`.
- **인터페이스** · admin-api.ts:467 · `DataQualityLogItem` 인터페이스는 DataQualityLogItem 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. 주요 필드: `log_id`, `symbol`, `rule`, `severity`, `message`, `observed_at`, `created_at`.
- **인터페이스** · admin-api.ts:478 · `DataQualityHistory` 인터페이스는 DataQualityHistory 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. 주요 필드: `persistence_status`, `items`, `total`, `severity_counts`, `limit`, `offset`.
- **타입** · admin-api.ts:487 · `CandlePriceBasis` 타입은 허용되는 값의 범위나 여러 데이터 형태의 조합을 제한합니다.
- **인터페이스** · admin-api.ts:494 · `CandlePriceBasisInventoryItem` 인터페이스는 CandlePriceBasisInventoryItem 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. 주요 필드: `source_provider`, `price_basis`, `price_basis_rule_version`, `data_stage`, `interval`, `aggregation_version`, `candle_count`, `first_timestamp`, `last_timestamp`, `review_status`, `required_evidence`.
- **인터페이스** · admin-api.ts:509 · `CandlePriceBasisInventory` 인터페이스는 CandlePriceBasisInventory 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. 주요 필드: `persistence_status`, `symbol`, `items`, `total_candles`, `unknown_candles`, `legacy_unknown_candles`, `legacy_rule_candles`, `total_groups`, `review_ready_groups`, `blocked_review_groups`, `groups_truncated`, `classification_blockers`, `automatic_relabel`, `mutation_performed`.
- **타입** · admin-api.ts:527 · `ProviderAuditOutcome` 타입은 허용되는 값의 범위나 여러 데이터 형태의 조합을 제한합니다.
- **인터페이스** · admin-api.ts:530 · `ProviderAuditItem` 인터페이스는 ProviderAuditItem 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. 주요 필드: `audit_id`, `provider`, `method`, `endpoint`, `api_group`, `outcome`, `status_code`, `error_code`, `provider_request_id`, `internal_request_id`, `attempt_count`, `duration_ms`, `occurred_at`.
- **인터페이스** · admin-api.ts:547 · `ProviderAuditHistory` 인터페이스는 ProviderAuditHistory 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. 주요 필드: `persistence_status`, `items`, `total`, `limit`, `offset`.
- **인터페이스** · admin-api.ts:556 · `ProviderAuditMaintenanceStatus` 인터페이스는 ProviderAuditMaintenanceStatus 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. 주요 필드: `status`, `enabled`, `retention_days`, `cleanup_hour_kst`, `last_run_at`, `last_cutoff`, `last_deleted_count`, `last_error_type`.
- **인터페이스** · admin-api.ts:568 · `DataLifecycleStatus` 인터페이스는 DataLifecycleStatus 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. 주요 필드: `status`, `enabled`, `retention_days`, `cleanup_hour_kst`, `last_run_at`, `last_deleted_counts`, `last_error_type`.
- **인터페이스** · admin-api.ts:579 · `DataLifecyclePreview` 인터페이스는 DataLifecyclePreview 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. 주요 필드: `preview_status`, `eligible_counts`, `cutoffs`, `preview_error_type`.
- **인터페이스** · admin-api.ts:587 · `CorporateActionItem` 인터페이스는 CorporateActionItem 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. 주요 필드: `symbol`, `action_type`, `event_id`, `revision`, `effective_at`, `announced_at`, `known_at`, `price_factor`, `volume_factor`, `status`, `source`, `rule_version`, `recorded_at`.
- **인터페이스** · admin-api.ts:604 · `CorporateActionHistory` 인터페이스는 CorporateActionHistory 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. 주요 필드: `persistence_status`, `items`, `total`, `limit`, `offset`, `data_as_of`, `adjustment_version`, `application_mode`, `raw_candles_mutated`.
- **인터페이스** · admin-api.ts:617 · `CorporateActionSource` 인터페이스는 CorporateActionSource 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. 주요 필드: `name`, `markets`, `trust_status`, `revision_strategy`.
- **인터페이스** · admin-api.ts:625 · `CorporateActionIngestionStatus` 인터페이스는 CorporateActionIngestionStatus 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. 주요 필드: `persistence_status`, `ingestion_available`, `sources`, `source_candidates`, `verified_source_count`, `automatic_ingestion`, `consumer_adjustment_mode`, `max_batch_records`.
- **인터페이스** · admin-api.ts:637 · `CorporateActionIngestionResult` 인터페이스는 CorporateActionIngestionResult 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. 주요 필드: `source`, `symbol`, `requested_start`, `requested_end`, `data_as_of`, `fetched`, `created`, `unchanged`, `atomic_batch`, `consumer_adjustment_mode`.
- **인터페이스** · admin-api.ts:651 · `CorporateActionCandidateStatus` 인터페이스는 CorporateActionCandidateStatus 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. 주요 필드: `available`, `sources`, `read_only`, `automatic_confirmation`, `point_in_time_eligible`, `max_range_days`, `max_candidates`.
- **인터페이스** · admin-api.ts:662 · `CorporateActionCandidateItem` 인터페이스는 CorporateActionCandidateItem 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. 주요 필드: `source`, `symbol`, `event_id`, `receipt_no`, `action_type`, `filed_on`, `decision_date`, `record_date`, `proposed_price_factor`, `proposed_volume_factor`, `evidence_url`, `report_name`, `remarks`, `correction_hint`, `superseded_hint`, `warnings`, `confirmation_ready`.
- **인터페이스** · admin-api.ts:683 · `CorporateActionCandidatePreview` 인터페이스는 CorporateActionCandidatePreview 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. 주요 필드: `source`, `symbol`, `requested_start`, `requested_end`, `data_as_of`, `items`, `revision_groups`, `group_hint`, `action_type`, `anchor_date`, `receipt_nos`, `suggested_revisions`, `confidence`, `reasons`, `requires_manual_confirmation`, `persistence_allowed`, `count`, `read_only`, `write_performed`, `automatic_confirmation`.
- **인터페이스** · admin-api.ts:711 · `CorporateActionApprovalStatus` 인터페이스는 CorporateActionApprovalStatus 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. 주요 필드: `enabled`, `available`, `persistence_status`, `confirmation_phrase`, `candidate_refetch_required`, `supported_sources`, `exchange_evidence_required`, `allowed_exchange_evidence_hosts`, `known_at_policy`, `bulk_approval`, `automatic_execution`, `raw_candles_mutated`, `exchange_verification`.
- **인터페이스** · admin-api.ts:728 · `CorporateActionApprovalRequest` 인터페이스는 CorporateActionApprovalRequest 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. 주요 필드: `start`, `end`, `group_hint`, `receipt_no`, `effective_at`, `exchange_evidence_url`, `confirmation`.
- **인터페이스** · admin-api.ts:739 · `CorporateActionApprovalResult` 인터페이스는 CorporateActionApprovalResult 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. 주요 필드: `action`, `evidence_hash`, `created`, `candidate_refetched_at`, `known_at_policy`, `automatic_execution`, `raw_candles_mutated`.
- **인터페이스** · admin-api.ts:750 · `IngestionStatus` 인터페이스는 IngestionStatus 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. 주요 필드: `scheduler_enabled`, `persistence_enabled`, `manual_ingestion_available`, `interval_minutes`, `ingestion_limit`, `symbols`.
- **인터페이스** · admin-api.ts:760 · `IngestionResult` 인터페이스는 IngestionResult 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. 주요 필드: `summary`, `symbol`, `provider`, `raw_count`, `cleaned_count`, `quality_log_count`, `aggregation_version`, `price_basis`, `price_basis_rule_version`, `price_basis_verification_status`, `configured_symbol`, `triggered_at`.
- **함수** · admin-api.ts:777 · `request`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · admin-api.ts:796 · `fetchBacktestHistory`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · admin-api.ts:803 · `fetchBacktestRun`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · admin-api.ts:808 · `runWalkForwardValidation`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · admin-api.ts:819 · `compareBacktestEngines`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · admin-api.ts:830 · `compareBacktestStrategies`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · admin-api.ts:841 · `fetchModelVersions`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · admin-api.ts:848 · 체크섬을 통과한 직접 학습 모델의 품질 준비도를 조회한다.
- **함수** · admin-api.ts:853 · `promoteModelVersion`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · admin-api.ts:864 · `fetchWatchlist`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · admin-api.ts:869 · `addWatchlist`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · admin-api.ts:878 · `removeWatchlist`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · admin-api.ts:883 · `fetchPriceAlerts`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · admin-api.ts:888 · `createPriceAlert`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · admin-api.ts:901 · `disablePriceAlert`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · admin-api.ts:906 · `evaluatePriceAlerts`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · admin-api.ts:911 · `fetchBrokerAccounts`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · admin-api.ts:916 · `syncPortfolio`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · admin-api.ts:923 · `fetchTossAccountWorkspace`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · admin-api.ts:933 · `fetchOperationsStatus`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · admin-api.ts:938 · `fetchDataQualityHistory`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · admin-api.ts:951 · `fetchCandlePriceBasisInventory`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · admin-api.ts:962 · `fetchCorporateActionHistory`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · admin-api.ts:973 · `fetchCorporateActionIngestionStatus`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · admin-api.ts:978 · `triggerCorporateActionIngestion`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · admin-api.ts:993 · `fetchCorporateActionCandidateStatus`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · admin-api.ts:998 · `fetchCorporateActionApprovalStatus`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · admin-api.ts:1003 · `fetchCorporateActionCandidates`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · admin-api.ts:1017 · `approveCorporateActionCandidate`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · admin-api.ts:1033 · `fetchProviderAuditHistory`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · admin-api.ts:1046 · `cleanupProviderAuditHistory`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · admin-api.ts:1053 · `fetchDataLifecyclePreview`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · admin-api.ts:1058 · `cleanupDataLifecycle`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · admin-api.ts:1065 · `fetchIngestionStatus`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · admin-api.ts:1070 · `triggerIngestion`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `frontend/lib/admin-proxy.ts`

프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.

- **함수** · admin-proxy.ts:8 · `boundedInteger`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · admin-proxy.ts:21 · `errorResponse`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · admin-proxy.ts:35 · `boundedResponseBody`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **클래스** · admin-proxy.ts:60 · `AdminProxyResponseError` 클래스는 AdminProxyResponseError 클래스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.의 상태와 동작을 캡슐화합니다.
- **인터페이스** · admin-proxy.ts:63 · `AdminProxyOptions` 인터페이스는 AdminProxyOptions 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. 주요 필드: `method`, `body`.
- **함수** · admin-proxy.ts:69 · `proxyAdminRequest`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · admin-proxy.ts:81 · `backendUrl`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `frontend/lib/agent-labels.ts`

프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.

- **함수** · agent-labels.ts:13 · `agentDisplayName`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · agent-labels.ts:18 · `agentRoleName`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `frontend/lib/analysis-sequence.ts`

프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.

- **타입** · analysis-sequence.ts:10 · `AnalysisAgentKey` 타입은 허용되는 값의 범위나 여러 데이터 형태의 조합을 제한합니다.
- **타입** · analysis-sequence.ts:11 · `AnalysisSequencePhase` 타입은 허용되는 값의 범위나 여러 데이터 형태의 조합을 제한합니다.
- **인터페이스** · analysis-sequence.ts:19 · `AnalysisSequenceTiming` 인터페이스는 AnalysisSequenceTiming 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. 주요 필드: `briefingMs`, `courseMs`, `researchDebateMs`, `tradingReviewMs`, `finalServiceMs`.
- **인터페이스** · analysis-sequence.ts:33 · `AnalysisSequenceStep` 인터페이스는 발표 시간표에서 한 시점에 공개할 단계와 완료 상태를 나타내는 계약이다. 주요 필드: `announcement`, `atMs`, `complete`, `phase`, `revealedCount`.
- **함수** · analysis-sequence.ts:51 · `orderedAvailableAgents`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · analysis-sequence.ts:60 · `buildAnalysisSequence`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `frontend/lib/browser-watchlist.ts`

프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.

- **인터페이스** · browser-watchlist.ts:3 · `BrowserStorage` 인터페이스는 browser-watchlist 파일은 프론트 타입 계약과 API client 기능을 담당한다.
- **인터페이스** · browser-watchlist.ts:9 · `SymbolItem` 인터페이스는 SymbolItem 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. 주요 필드: `symbol`.
- **인터페이스** · browser-watchlist.ts:14 · `StoredItemsResult` 인터페이스는 StoredItemsResult 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. 주요 필드: `items`, `persisted`.
- **함수** · browser-watchlist.ts:20 · `readStoredItems`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · browser-watchlist.ts:36 · `writeStoredItems`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · browser-watchlist.ts:46 · `toggleStoredSymbol`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `frontend/lib/local-ai-presentation.ts`

프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.

- **타입** · local-ai-presentation.ts:1 · `LocalAgent` 타입은 허용되는 값의 범위나 여러 데이터 형태의 조합을 제한합니다.
- **함수** · local-ai-presentation.ts:67 · `signedPercent`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · local-ai-presentation.ts:74 · `localConfidenceLabel`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · local-ai-presentation.ts:81 · `localEvidenceLabel`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · local-ai-presentation.ts:102 · `isLocalQualityEvidence`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · local-ai-presentation.ts:107 · 백엔드 진단 문자열 중 알려진 원시 표현을 투자자가 읽는 문장으로 변환한다.

### `frontend/lib/market-api.ts`

프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.

- **타입** · market-api.ts:7 · `CandleInterval` 타입은 StockPilot Next.js BFF와 통신할 때 사용하는 브라우저 타입 계약이다. 화면 컴포넌트는 FastAPI나 외부 공급자를 직접 호출하지 않고 이 파일의 함수를 사용한다. API 키를 서버에만 보관하고 모든 화면에 같은 오류·응답 처리 규칙을 적용하기 위해서다.
- **인터페이스** · market-api.ts:10 · `MarketCandle` 인터페이스는 MarketCandle 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. 주요 필드: `timestamp`, `open`, `high`, `low`, `close`, `volume`.
- **인터페이스** · market-api.ts:20 · `ProcessedCandles` 인터페이스는 ProcessedCandles 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. 주요 필드: `symbol`, `provider`, `interval`, `raw_count`, `aggregation_version`, `candles`, `quality_logs`.
- **인터페이스** · market-api.ts:31 · `StockInfo` 인터페이스는 StockInfo 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. 주요 필드: `symbol`, `name`, `market`, `sector`, `listed_at`, `currency`, `provider`.
- **인터페이스** · market-api.ts:42 · `MarketQuote` 인터페이스는 MarketQuote 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. 주요 필드: `symbol`, `name`, `price`, `change`, `change_percent`, `volume`, `as_of`, `currency`, `provider`.
- **인터페이스** · market-api.ts:55 · `StockSnapshot` 인터페이스는 StockSnapshot 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. 주요 필드: `stock`, `quote`.
- **인터페이스** · market-api.ts:61 · `StockSearchResult` 인터페이스는 StockSearchResult 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. 주요 필드: `provider`, `catalog_size`, `items`, `symbol`, `name`, `englishName`, `market`, `securityType`, `status`, `currency`.
- **인터페이스** · market-api.ts:76 · `MarketOverview` 인터페이스는 MarketOverview 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. 주요 필드: `provider`, `indicators`, `exchange_rate`, `baseCurrency`, `quoteCurrency`, `rate`, `midRate`, `rateChangeType`, `validUntil`, `calendars`, `rankings`, `rankedAt`, `rank`, `symbol`, `currency`, `price`, `tradingVolume`, `tradingAmount`, `partial_errors`.
- **타입** · market-api.ts:105 · `TossRankingType` 타입은 허용되는 값의 범위나 여러 데이터 형태의 조합을 제한합니다.
- **인터페이스** · market-api.ts:114 · `MarketRankings` 인터페이스는 MarketRankings 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. 주요 필드: `provider`, `type`, `market_country`, `duration`, `rankedAt`, `rankings`.
- **인터페이스** · market-api.ts:124 · `MarketIndicatorHistory` 인터페이스는 MarketIndicatorHistory 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. 주요 필드: `provider`, `symbol`, `candles`, `timestamp`, `openPrice`, `highPrice`, `lowPrice`, `closePrice`, `volume`, `nextBefore`, `investor_trading`, `partial_errors`.
- **인터페이스** · market-api.ts:143 · `StockMicrostructure` 인터페이스는 StockMicrostructure 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. 주요 필드: `provider`, `price_limit`, `timestamp`, `upperLimitPrice`, `lowerLimitPrice`, `currency`, `orderbook`, `asks`, `bids`, `trades`, `symbol`, `price`, `quantity`, `side`, `executed_at`, `warnings`, `warning_type`, `exchange`, `start_date`, `end_date`.
- **인터페이스** · market-api.ts:171 · `TossStockTrends` 인터페이스는 TossStockTrends 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. 주요 필드: `provider`, `investor_trading`, `program_trades`, `short_selling`, `credit_trades`, `securities_lending`.
- **인터페이스** · market-api.ts:181 · `RealtimeQuote` 인터페이스는 RealtimeQuote 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. 주요 필드: `type`, `symbol`, `name`, `price`, `change`, `change_percent`, `volume`, `currency`, `data_as_of`, `provider`, `is_investment_advice`.
- **인터페이스** · market-api.ts:196 · `RealtimeError` 인터페이스는 RealtimeError 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. 주요 필드: `type`, `symbol`, `error`.
- **타입** · market-api.ts:202 · `ReferenceSignal` 타입은 허용되는 값의 범위나 여러 데이터 형태의 조합을 제한합니다.
- **인터페이스** · market-api.ts:210 · `DetectedPattern` 인터페이스는 DetectedPattern 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. 주요 필드: `category`, `name`, `direction`, `confidence`, `started_at`, `ended_at`, `evidence`.
- **인터페이스** · market-api.ts:221 · `IndicatorPoint` 인터페이스는 IndicatorPoint 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. 주요 필드: `timestamp`, `ma_5`, `ma_20`, `rsi_14`, `macd`, `macd_signal`, `macd_histogram`, `bb_middle`, `bb_upper`, `bb_lower`, `atr_14`, `plus_di_14`, `minus_di_14`, `adx_14`, `mfi_14`, `vwap`, `obv`, `supertrend_10_3`, `supertrend_direction`.
- **인터페이스** · market-api.ts:244 · `TechnicalAnalysis` 인터페이스는 TechnicalAnalysis 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. 주요 필드: `symbol`, `provider`, `engine_version`, `validation_status`, `indicators`.
- **인터페이스** · market-api.ts:253 · `PatternAnalysis` 인터페이스는 PatternAnalysis 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. 주요 필드: `symbol`, `provider`, `engine_version`, `validation_status`, `data_as_of`, `window_size`, `patterns`.
- **인터페이스** · market-api.ts:264 · `FinancialSnapshot` 인터페이스는 FinancialSnapshot 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. 주요 필드: `symbol`, `corp_code`, `fiscal_year`, `report_code`, `statement_type`, `currency`, `revenue`, `operating_income`, `net_income`, `total_assets`, `total_liabilities`, `total_equity`, `data_as_of`, `provider`, `persistence_status`.
- **인터페이스** · market-api.ts:283 · `ValuationAnalysis` 인터페이스는 ValuationAnalysis 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. 주요 필드: `symbol`, `currency`, `price`, `shares_outstanding`, `market_cap`, `per`, `pbr`, `psr`, `roe`, `financial_data_as_of`, `quote_data_as_of`, `financial_source`, `quote_provider`, `unavailable_metrics`, `methodology`, `experimental`.
- **인터페이스** · market-api.ts:303 · `NewsArticle` 인터페이스는 NewsArticle 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. 주요 필드: `symbol`, `title`, `url`, `publisher`, `published_at`, `summary`, `sentiment_score`.
- **인터페이스** · market-api.ts:314 · `NewsAnalysis` 인터페이스는 NewsAnalysis 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. 주요 필드: `symbol`, `provider`, `experimental`, `sentiment_score`, `sentiment_label`, `articles`, `persistence_status`.
- **인터페이스** · market-api.ts:325 · `DisclosureItem` 인터페이스는 DisclosureItem 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. 주요 필드: `symbol`, `corp_code`, `receipt_no`, `company_name`, `report_name`, `filed_at`, `filer_name`, `remarks`, `document_url`, `risk_level`.
- **인터페이스** · market-api.ts:339 · `DisclosureAnalysis` 인터페이스는 DisclosureAnalysis 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. 주요 필드: `symbol`, `provider`, `experimental`, `risk_flags`, `disclosures`, `persistence_status`.
- **인터페이스** · market-api.ts:349 · `InvestorFlow` 인터페이스는 InvestorFlow 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. 주요 필드: `symbol`, `as_of_date`, `foreign_net_quantity`, `institution_net_quantity`, `individual_net_quantity`, `foreign_holding_quantity`, `foreign_holding_rate`, `data_as_of`, `provider`, `experimental`, `foreign_institution_net_quantity`, `reference_signal`, `persistence_status`.
- **인터페이스** · market-api.ts:366 · `AIAnalysisReport` 인터페이스는 AIAnalysisReport 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. 주요 필드: `symbol`, `generator`, `llm_model`, `model_version`, `validation_status`, `overall_score`, `rise_probability`, `downside_risk`, `reference_signal`, `signal_strength`, `signal_basis`, `confidence`, `score_coverage`, `prediction_horizon_days`, `summary`, `key_points`, `risk_factors`, `counterpoints`, `chart_patterns`, `engine_version`.
- **인터페이스** · market-api.ts:453 · `ApiEnvelope` 인터페이스는 ApiEnvelope 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. 주요 필드: `success`, `request_id`, `data`, `error`.
- **함수** · market-api.ts:464 · `publicRequestError`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · market-api.ts:479 · `request`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · market-api.ts:487 · `abortFromCaller`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · market-api.ts:518 · `quoteWebSocketUrl`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · market-api.ts:532 · `fetchCandles`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · market-api.ts:546 · `fetchStockInfo`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · market-api.ts:555 · `fetchQuote`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · market-api.ts:564 · `fetchStockSnapshot`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · market-api.ts:573 · `searchStocks`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · market-api.ts:587 · `fetchMarketOverview`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · market-api.ts:596 · `fetchMarketRankings`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · market-api.ts:616 · `fetchMarketIndicatorHistory`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · market-api.ts:629 · `fetchStockMicrostructure`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · market-api.ts:642 · `fetchTossStockTrends`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · market-api.ts:655 · `fetchTechnicalAnalysis`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · market-api.ts:665 · `fetchPatternAnalysis`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · market-api.ts:675 · `fetchFinancials`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · market-api.ts:689 · `fetchValuation`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · market-api.ts:703 · `fetchNews`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · market-api.ts:713 · `fetchDisclosures`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · market-api.ts:723 · `fetchInvestorFlow`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · market-api.ts:732 · `fetchAnalysisReport`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `frontend/lib/market-proxy.ts`

프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.

- **함수** · market-proxy.ts:43 · `errorResponse`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · market-proxy.ts:57 · `boundedInteger`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · market-proxy.ts:70 · `allowedPath`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · market-proxy.ts:91 · `allowedQuery`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · market-proxy.ts:99 · `boundedBody`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **클래스** · market-proxy.ts:123 · `MarketProxyResponseError` 클래스는 MarketProxyResponseError 클래스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.의 상태와 동작을 캡슐화합니다.
- **함수** · market-proxy.ts:126 · `proxyMarketRequest`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · market-proxy.ts:147 · `backendUrl`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `frontend/lib/paper-api.ts`

프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.

- **인터페이스** · paper-api.ts:3 · `PaperPosition` 인터페이스는 모의투자 BFF와 통신하는 브라우저 전용 타입 및 함수다. 주요 필드: `symbol`, `name`, `market`, `currency`, `quantity`, `average_price`, `last_price`, `market_value`, `unrealized_pnl`, `realized_pnl`, `return_percent`, `price_status`.
- **인터페이스** · paper-api.ts:19 · `PaperOrder` 인터페이스는 PaperOrder 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. 주요 필드: `order_id`, `symbol`, `name`, `currency`, `side`, `quantity`, `fill_price`, `commission`, `executed_at`.
- **인터페이스** · paper-api.ts:32 · `PaperRiskSummary` 인터페이스는 PaperRiskSummary 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. 주요 필드: `status`, `invested_ratio`, `cash_ratio`, `largest_position_symbol`, `largest_position_ratio`, `warnings`, `limits`, `max_order_ratio`, `max_position_ratio`, `max_invested_ratio`.
- **인터페이스** · paper-api.ts:47 · `PaperPortfolio` 인터페이스는 PaperPortfolio 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. 주요 필드: `account`, `persistence_status`, `saved_at`, `totals`, `initial_cash`, `cash`, `market_value`, `unrealized_pnl`, `equity`, `total_pnl`, `return_percent`, `risk`, `positions`, `orders`, `commission_rate`, `execution_policy`, `is_real_order`.
- **함수** · paper-api.ts:71 · 개인정보 없이 브라우저에만 보관되는 모의투자 계정 식별자를 반환한다.
- **인터페이스** · paper-api.ts:87 · `Envelope` 인터페이스는 Envelope 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다.
- **함수** · paper-api.ts:90 · `request`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · paper-api.ts:100 · `fetchPaperPortfolio`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · paper-api.ts:105 · `createPaperOrder`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · paper-api.ts:117 · `resetPaperPortfolio`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `frontend/lib/share-url.ts`

프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.

- **함수** · share-url.ts:8 · `stockResultUrl`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

### `frontend/lib/stock-catalog.ts`

프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.

- **인터페이스** · stock-catalog.ts:2 · `CatalogStock` 인터페이스는 CatalogStock 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. 주요 필드: `aliases`, `currency`, `market`, `name`, `symbol`.

### `frontend/lib/stock-search.ts`

프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.

- **인터페이스** · stock-search.ts:3 · `StockSearchItem` 인터페이스는 stock-search 파일은 프론트 타입 계약과 API client 기능을 담당한다. 주요 필드: `aliases`, `name`, `symbol`.
- **타입** · stock-search.ts:9 · `StockSearchMatchKind` 타입은 허용되는 값의 범위나 여러 데이터 형태의 조합을 제한합니다.
- **인터페이스** · stock-search.ts:12 · `StockSearchMatch` 인터페이스는 StockSearchMatch 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. 주요 필드: `kind`, `stock`.
- **함수** · stock-search.ts:18 · `normalizeStockSearchText`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · stock-search.ts:23 · `editDistanceAtMostOne`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · stock-search.ts:51 · `isTolerantKoreanMatch`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · stock-search.ts:61 · `matchesSearchText`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · stock-search.ts:71 · `matchKind`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · stock-search.ts:84 · `matchRank`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · stock-search.ts:98 · `findStockByExactMatch`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · stock-search.ts:108 · `filterStocksBySearch`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.
- **함수** · stock-search.ts:121 · `findSimilarStockMatches`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다.

