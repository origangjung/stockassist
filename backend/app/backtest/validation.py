from collections.abc import Callable
from dataclasses import asdict
from statistics import mean

import pandas as pd

from app.backtest.engine import BacktestEngine
from app.backtest.event_engine import EventDrivenBacktestEngine
from app.backtest.metrics import calculate_metrics
from app.backtest.models import BacktestConfig
from app.backtest.strategies import Strategy
from app.providers.contracts import Candle


VALIDATION_VERSION = "walk-forward-backtest-2026.2"


class _ActivationStrategy(Strategy):
    def __init__(self, delegate: Strategy, activation_index: int) -> None:
        self._delegate = delegate
        self._activation_index = activation_index
        self.name = delegate.name

    def signals(self, candles: pd.DataFrame) -> pd.Series:
        signals = self._delegate.signals(candles).copy()
        signals.iloc[: self._activation_index] = 0
        return signals


class WalkForwardBacktestValidator:
    """Chronological, non-overlapping out-of-sample strategy evaluation."""

    version = VALIDATION_VERSION
    status = "experimental"

    def run(
        self,
        candles: list[Candle],
        *,
        strategy_factory: Callable[[], Strategy],
        engine: BacktestEngine | EventDrivenBacktestEngine,
        config: BacktestConfig,
        n_splits: int = 3,
        warmup_candles: int = 60,
    ) -> dict:
        if not 2 <= n_splits <= 6:
            raise ValueError("n_splits must be between 2 and 6")
        if warmup_candles < 21:
            raise ValueError("warmup_candles must be at least 21")
        ordered = sorted(candles, key=lambda candle: candle.timestamp)
        available = len(ordered) - warmup_candles
        if available < n_splits * 10:
            raise ValueError("insufficient candles for walk-forward validation")

        fold_size = available // n_splits
        folds: list[dict] = []
        for fold_index in range(n_splits):
            test_start = warmup_candles + fold_index * fold_size
            test_end = (
                len(ordered)
                if fold_index == n_splits - 1
                else warmup_candles + (fold_index + 1) * fold_size
            )
            source_start = max(0, test_start - warmup_candles)
            activation_index = test_start - source_start
            fold_source = ordered[source_start:test_end]
            strategy = _ActivationStrategy(strategy_factory(), activation_index)
            result = engine.run(fold_source, strategy, config)

            test_timestamp = ordered[test_start].timestamp
            points = result.equity_curve[activation_index:]
            trades = [trade for trade in result.trades if trade.timestamp >= test_timestamp]
            events = [event for event in result.events if event.timestamp >= test_timestamp]
            equity = pd.Series([point.equity for point in points], dtype="float64")
            returns = pd.Series([point.daily_return for point in points], dtype="float64")
            metrics = calculate_metrics(equity, returns, trades, len(points), config)
            folds.append(
                {
                    "fold": fold_index + 1,
                    "test_started_at": test_timestamp,
                    "test_ended_at": ordered[test_end - 1].timestamp,
                    "test_candles": test_end - test_start,
                    "metrics": asdict(metrics),
                    "execution": {
                        "partial_fill_count": sum(
                            event.event_type == "partial_fill" for event in events
                        ),
                        "rejected_order_count": sum(
                            event.event_type == "rejected" for event in events
                        ),
                    },
                }
            )

        returns = [float(fold["metrics"]["total_return"]) for fold in folds]
        drawdowns = [float(fold["metrics"]["max_drawdown"]) for fold in folds]
        sharpes = [float(fold["metrics"]["sharpe_ratio"]) for fold in folds]
        profitable_folds = sum(value > 0 for value in returns)
        aggregate = {
            "mean_total_return": round(mean(returns), 8),
            "profitable_fold_ratio": round(profitable_folds / len(folds), 6),
            "worst_max_drawdown": round(min(drawdowns), 8),
            "mean_sharpe_ratio": round(mean(sharpes), 6),
            "total_trade_count": sum(int(fold["metrics"]["trade_count"]) for fold in folds),
            "total_partial_fill_count": sum(
                int(fold["execution"]["partial_fill_count"]) for fold in folds
            ),
            "total_rejected_order_count": sum(
                int(fold["execution"]["rejected_order_count"]) for fold in folds
            ),
            "stability": self._stability(returns),
        }
        return {
            "validation_version": self.version,
            "validation_status": self.status,
            "engine_version": engine.version,
            "strategy": strategy_factory().name,
            "n_splits": n_splits,
            "warmup_candles": warmup_candles,
            "execution_model": {
                "volume_limit_applied": isinstance(engine, EventDrivenBacktestEngine),
                "max_volume_participation": config.max_volume_participation,
                "force_close_bypasses_volume_limit": isinstance(
                    engine, EventDrivenBacktestEngine
                ),
            },
            "data_as_of": ordered[-1].timestamp,
            "aggregate": aggregate,
            "folds": folds,
        }

    @staticmethod
    def _stability(returns: list[float]) -> str:
        profitable_ratio = sum(value > 0 for value in returns) / len(returns)
        average = mean(returns)
        if profitable_ratio >= 2 / 3 and average > 0:
            return "consistent_positive"
        if profitable_ratio <= 1 / 3 and average < 0:
            return "consistent_negative"
        return "mixed"
