"""Vectorized backtesting primitives."""

from app.backtest.engine import BacktestEngine
from app.backtest.event_engine import EventDrivenBacktestEngine
from app.backtest.models import BacktestConfig, BacktestEvent, BacktestResult, CostModel
from app.backtest.strategies import (
    BuyAndHoldStrategy,
    MovingAverageCrossStrategy,
    PatternReferenceStrategy,
)
from app.backtest.validation import WalkForwardBacktestValidator

__all__ = [
    "BacktestEngine",
    "EventDrivenBacktestEngine",
    "BacktestConfig",
    "BacktestEvent",
    "BacktestResult",
    "CostModel",
    "BuyAndHoldStrategy",
    "MovingAverageCrossStrategy",
    "PatternReferenceStrategy",
    "WalkForwardBacktestValidator",
]
