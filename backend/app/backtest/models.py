from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class CostModel:
    commission_rate: float = 0.00015
    tax_rate: float = 0.0018
    slippage_rate: float = 0.0005

    def __post_init__(self) -> None:
        for name, value in self.__dict__.items():
            if not 0 <= value < 1:
                raise ValueError(f"{name} must be between 0 and 1")


@dataclass(frozen=True)
class BacktestConfig:
    initial_capital: float = 10_000_000
    annualization_days: int = 252
    force_close: bool = True
    costs: CostModel = CostModel()
    max_volume_participation: float = 1.0

    def __post_init__(self) -> None:
        if self.initial_capital <= 0:
            raise ValueError("initial_capital must be positive")
        if self.annualization_days <= 0:
            raise ValueError("annualization_days must be positive")
        if not 0 < self.max_volume_participation <= 1:
            raise ValueError("max_volume_participation must be greater than 0 and at most 1")


@dataclass(frozen=True)
class Trade:
    timestamp: datetime
    side: str
    execution_price: float
    cost: float
    position_after: int
    quantity: int | None = None
    cash_after: float | None = None


@dataclass(frozen=True)
class BacktestEvent:
    timestamp: datetime
    event_type: str
    details: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class EquityPoint:
    timestamp: datetime
    equity: float
    daily_return: float
    position: int


@dataclass(frozen=True)
class PerformanceMetrics:
    total_return: float
    cagr: float
    max_drawdown: float
    sharpe_ratio: float
    win_rate: float
    trade_count: int
    final_equity: float


@dataclass(frozen=True)
class BacktestResult:
    engine_version: str
    validation_status: str
    strategy: str
    metrics: PerformanceMetrics
    equity_curve: list[EquityPoint]
    trades: list[Trade]
    events: list[BacktestEvent] = field(default_factory=list)


@dataclass(frozen=True)
class BacktestRunSummary:
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
    summary: BacktestRunSummary
    config: dict[str, object]
    equity_curve: list[dict[str, object]]
    trades: list[dict[str, object]]
    events: list[dict[str, object]]
