from dataclasses import asdict

from app.adapters.broker import BrokerAdapter
from app.backtest import (
    BacktestConfig,
    BacktestEngine,
    BuyAndHoldStrategy,
    CostModel,
    EventDrivenBacktestEngine,
    MovingAverageCrossStrategy,
    PatternReferenceStrategy,
    WalkForwardBacktestValidator,
)
from app.backtest.models import EquityPoint
from app.providers.contracts import Capability
from app.repositories.contracts import BacktestRepository


class BacktestService:
    def __init__(
        self,
        broker: BrokerAdapter,
        engine: BacktestEngine,
        repository: BacktestRepository | None = None,
        event_engine: EventDrivenBacktestEngine | None = None,
    ):
        self._broker = broker
        self._engine = engine
        self._event_engine = event_engine or EventDrivenBacktestEngine()
        self._validator = WalkForwardBacktestValidator()
        self._repository = repository

    def run(
        self,
        *,
        symbol: str,
        strategy_name: str,
        limit: int,
        fast_period: int,
        slow_period: int,
        initial_capital: float,
        commission_rate: float,
        tax_rate: float,
        slippage_rate: float,
        engine_name: str = "vectorized",
        max_volume_participation: float = 1.0,
    ) -> dict:
        strategy = self._strategy(strategy_name, fast_period, slow_period)
        provider = self._broker.provider_for(Capability.CANDLES)
        candles = provider.get_candles(symbol, limit)
        config = BacktestConfig(
            initial_capital=initial_capital,
            costs=CostModel(commission_rate, tax_rate, slippage_rate),
            max_volume_participation=max_volume_participation,
        )
        engine = self._engine_for(engine_name)
        result = engine.run(candles, strategy, config)
        run_id = (
            self._repository.save(symbol, config, result) if self._repository is not None else None
        )
        return {
            "run_id": run_id,
            "persistence_status": "persisted" if run_id else "disabled",
            "symbol": symbol,
            "provider": provider.name,
            "engine": engine_name,
            **asdict(result),
        }

    def validate_walk_forward(
        self,
        *,
        symbol: str,
        strategy_name: str,
        limit: int,
        fast_period: int,
        slow_period: int,
        initial_capital: float,
        commission_rate: float,
        tax_rate: float,
        slippage_rate: float,
        engine_name: str,
        n_splits: int,
        warmup_candles: int,
        max_volume_participation: float = 1.0,
    ) -> dict:
        provider = self._broker.provider_for(Capability.CANDLES)
        candles = provider.get_candles(symbol, limit)
        config = BacktestConfig(
            initial_capital=initial_capital,
            costs=CostModel(commission_rate, tax_rate, slippage_rate),
            max_volume_participation=max_volume_participation,
        )
        engine = self._engine_for(engine_name)
        result = self._validator.run(
            candles,
            strategy_factory=lambda: self._strategy(
                strategy_name,
                fast_period,
                slow_period,
            ),
            engine=engine,
            config=config,
            n_splits=n_splits,
            warmup_candles=warmup_candles,
        )
        return {
            "symbol": symbol,
            "provider": provider.name,
            "engine": engine_name,
            **result,
        }

    def compare_engines(
        self,
        *,
        symbol: str,
        strategy_name: str,
        limit: int,
        fast_period: int,
        slow_period: int,
        initial_capital: float,
        commission_rate: float,
        tax_rate: float,
        slippage_rate: float,
        max_volume_participation: float = 1.0,
    ) -> dict:
        """Run both engines against one immutable market-data snapshot."""
        provider = self._broker.provider_for(Capability.CANDLES)
        candles = provider.get_candles(symbol, limit)
        config = BacktestConfig(
            initial_capital=initial_capital,
            costs=CostModel(commission_rate, tax_rate, slippage_rate),
            max_volume_participation=max_volume_participation,
        )
        vectorized = self._engine.run(
            candles,
            self._strategy(strategy_name, fast_period, slow_period),
            config,
        )
        event_driven = self._event_engine.run(
            candles,
            self._strategy(strategy_name, fast_period, slow_period),
            config,
        )

        event_counts = {
            event_type: sum(event.event_type == event_type for event in event_driven.events)
            for event_type in ("fill", "partial_fill", "rejected")
        }
        vector_metrics = asdict(vectorized.metrics)
        event_metrics = asdict(event_driven.metrics)
        return {
            "comparison_version": "engine-comparison-2026.1",
            "validation_status": "experimental",
            "symbol": symbol,
            "provider": provider.name,
            "strategy": vectorized.strategy,
            "data_as_of": candles[-1].timestamp,
            "assumptions": {
                "candle_count": len(candles),
                "initial_capital": initial_capital,
                "costs": asdict(config.costs),
                "max_volume_participation": max_volume_participation,
                "same_market_data_snapshot": True,
                "force_close": config.force_close,
            },
            "vectorized": {
                "engine_version": vectorized.engine_version,
                "metrics": vector_metrics,
                "equity_curve": self._comparison_curve(
                    vectorized.equity_curve,
                    initial_capital,
                ),
                "execution": {
                    "fill_count": len(vectorized.trades),
                    "partial_fill_count": 0,
                    "rejected_order_count": 0,
                    "volume_limit_applied": False,
                },
            },
            "event_driven": {
                "engine_version": event_driven.engine_version,
                "metrics": event_metrics,
                "equity_curve": self._comparison_curve(
                    event_driven.equity_curve,
                    initial_capital,
                ),
                "execution": {
                    "fill_count": event_counts["fill"],
                    "partial_fill_count": event_counts["partial_fill"],
                    "rejected_order_count": event_counts["rejected"],
                    "volume_limit_applied": max_volume_participation < 1,
                },
            },
            "deltas": {
                key: round(event_metrics[key] - vector_metrics[key], 8)
                for key in (
                    "total_return",
                    "cagr",
                    "max_drawdown",
                    "sharpe_ratio",
                    "final_equity",
                    "trade_count",
                )
            },
            "interpretation": (
                "event_driven minus vectorized; event-driven results include order-level "
                "cash, quantity, and liquidity constraints"
            ),
        }

    def compare_strategies(
        self,
        *,
        symbol: str,
        engine_name: str,
        limit: int,
        fast_period: int,
        slow_period: int,
        initial_capital: float,
        commission_rate: float,
        tax_rate: float,
        slippage_rate: float,
        max_volume_participation: float = 1.0,
    ) -> dict:
        """Compare every supported strategy on one market-data snapshot."""
        provider = self._broker.provider_for(Capability.CANDLES)
        candles = provider.get_candles(symbol, limit)
        config = BacktestConfig(
            initial_capital=initial_capital,
            costs=CostModel(commission_rate, tax_rate, slippage_rate),
            max_volume_participation=max_volume_participation,
        )
        engine = self._engine_for(engine_name)
        strategy_names = ("buy_and_hold", "ma_cross", "pattern_reference")
        results = {
            name: engine.run(
                candles,
                self._strategy(name, fast_period, slow_period),
                config,
            )
            for name in strategy_names
        }
        benchmark_metrics = asdict(results["buy_and_hold"].metrics)
        metric_keys = (
            "total_return",
            "cagr",
            "max_drawdown",
            "sharpe_ratio",
            "final_equity",
            "trade_count",
        )
        strategies = []
        for name in strategy_names:
            result = results[name]
            metrics = asdict(result.metrics)
            event_counts = {
                event_type: sum(event.event_type == event_type for event in result.events)
                for event_type in ("fill", "partial_fill", "rejected")
            }
            strategies.append(
                {
                    "strategy": name,
                    "metrics": metrics,
                    "equity_curve": self._comparison_curve(
                        result.equity_curve,
                        initial_capital,
                    ),
                    "execution": {
                        "fill_count": event_counts["fill"]
                        if engine_name == "event_driven"
                        else len(result.trades),
                        "partial_fill_count": event_counts["partial_fill"],
                        "rejected_order_count": event_counts["rejected"],
                    },
                    "deltas_vs_buy_and_hold": {
                        key: round(metrics[key] - benchmark_metrics[key], 8)
                        for key in metric_keys
                    },
                }
            )

        return {
            "comparison_version": "strategy-comparison-2026.1",
            "validation_status": "experimental",
            "symbol": symbol,
            "provider": provider.name,
            "engine": engine_name,
            "engine_version": engine.version,
            "data_as_of": candles[-1].timestamp,
            "benchmark": "buy_and_hold",
            "assumptions": {
                "candle_count": len(candles),
                "initial_capital": initial_capital,
                "costs": asdict(config.costs),
                "max_volume_participation": max_volume_participation,
                "same_market_data_snapshot": True,
                "force_close": config.force_close,
                "fast_period": fast_period,
                "slow_period": slow_period,
            },
            "strategies": strategies,
            "interpretation": (
                "deltas are strategy minus buy_and_hold under identical historical assumptions; "
                "they are not a future-return estimate or investment recommendation"
            ),
        }

    @staticmethod
    def _comparison_curve(
        points: list[EquityPoint],
        initial_capital: float,
        max_points: int = 120,
    ) -> list[dict]:
        """Return a bounded, normalized curve while preserving both endpoints."""
        peak = initial_capital
        curve: list[dict] = []
        for point in points:
            peak = max(peak, point.equity)
            curve.append(
                {
                    "timestamp": point.timestamp,
                    "normalized_equity": round(point.equity / initial_capital * 100, 6),
                    "drawdown": round(point.equity / peak - 1, 8),
                }
            )
        if len(curve) <= max_points:
            return curve
        last = len(curve) - 1
        indices = {round(index * last / (max_points - 1)) for index in range(max_points)}
        return [curve[index] for index in sorted(indices)]

    @staticmethod
    def _strategy(strategy_name: str, fast_period: int, slow_period: int):
        if strategy_name == "ma_cross":
            return MovingAverageCrossStrategy(fast_period, slow_period)
        if strategy_name == "buy_and_hold":
            return BuyAndHoldStrategy()
        if strategy_name == "pattern_reference":
            return PatternReferenceStrategy()
        raise ValueError(f"unsupported strategy: {strategy_name}")

    def _engine_for(self, engine_name: str):
        if engine_name == "vectorized":
            return self._engine
        if engine_name == "event_driven":
            return self._event_engine
        raise ValueError(f"unsupported backtest engine: {engine_name}")

    def history(
        self,
        *,
        limit: int,
        offset: int,
        symbol: str | None = None,
    ) -> dict:
        if self._repository is None:
            return {
                "persistence_status": "disabled",
                "items": [],
                "total": 0,
                "limit": limit,
                "offset": offset,
            }
        items, total = self._repository.list_runs(
            limit=limit,
            offset=offset,
            symbol=symbol,
        )
        return {
            "persistence_status": "enabled",
            "items": [asdict(item) for item in items],
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    def history_detail(self, run_id: str) -> dict:
        if self._repository is None:
            raise BacktestHistoryUnavailableError("Backtest persistence is disabled")
        detail = self._repository.get_run(run_id)
        if detail is None:
            raise BacktestRunNotFoundError(f"Backtest run not found: {run_id}")
        return asdict(detail)


class BacktestHistoryUnavailableError(RuntimeError):
    pass


class BacktestRunNotFoundError(LookupError):
    pass
