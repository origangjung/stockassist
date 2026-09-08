"""models 파일은 전략 검증과 성과 계산 기능을 담당한다."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class CostModel:
    """데이터베이스에 저장되는 필드와 관계를 정의하는 ORM 모델입니다."""

    commission_rate: float = 0.00015
    tax_rate: float = 0.0018
    slippage_rate: float = 0.0005

    def __post_init__(self) -> None:
        """`__post_init__`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        for name, value in self.__dict__.items():
            if not 0 <= value < 1:
                raise ValueError(f"{name} must be between 0 and 1")


@dataclass(frozen=True)
class BacktestConfig:
    """실행 또는 계산에 필요한 설정 값을 묶는 객체입니다."""

    initial_capital: float = 10_000_000
    annualization_days: int = 252
    force_close: bool = True
    costs: CostModel = CostModel()
    max_volume_participation: float = 1.0

    def __post_init__(self) -> None:
        """`__post_init__`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        if self.initial_capital <= 0:
            raise ValueError("initial_capital must be positive")
        if self.annualization_days <= 0:
            raise ValueError("annualization_days must be positive")
        if not 0 < self.max_volume_participation <= 1:
            raise ValueError("max_volume_participation must be greater than 0 and at most 1")


@dataclass(frozen=True)
class Trade:
    """`Trade` 관련 상태와 동작을 하나의 객체로 묶습니다."""

    timestamp: datetime
    side: str
    execution_price: float
    cost: float
    position_after: int
    quantity: int | None = None
    cash_after: float | None = None


@dataclass(frozen=True)
class BacktestEvent:
    """`BacktestEvent` 관련 상태와 동작을 하나의 객체로 묶습니다."""

    timestamp: datetime
    event_type: str
    details: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class EquityPoint:
    """시계열 또는 차트에서 사용하는 한 시점의 값을 나타냅니다."""

    timestamp: datetime
    equity: float
    daily_return: float
    position: int


@dataclass(frozen=True)
class PerformanceMetrics:
    """`PerformanceMetrics` 관련 상태와 동작을 하나의 객체로 묶습니다."""

    total_return: float
    cagr: float
    max_drawdown: float
    sharpe_ratio: float
    win_rate: float
    trade_count: int
    final_equity: float


@dataclass(frozen=True)
class BacktestResult:
    """계산 또는 처리 결과를 묶어 전달하는 값 객체입니다."""

    engine_version: str
    validation_status: str
    strategy: str
    metrics: PerformanceMetrics
    equity_curve: list[EquityPoint]
    trades: list[Trade]
    events: list[BacktestEvent] = field(default_factory=list)


@dataclass(frozen=True)
class BacktestRunSummary:
    """`BacktestRunSummary` 관련 상태와 동작을 하나의 객체로 묶습니다."""

    run_id: str
    symbol: str
    strategy: str
    status: str
    engine: str
    engine_version: str
    started_at: datetime
    finished_at: datetime | None
    metrics: dict[str, object]


@dataclass(frozen=True)
class BacktestRunDetail:
    """`BacktestRunDetail` 관련 상태와 동작을 하나의 객체로 묶습니다."""

    summary: BacktestRunSummary
    config: dict[str, object]
    equity_curve: list[dict[str, object]]
    trades: list[dict[str, object]]
    events: list[dict[str, object]]
