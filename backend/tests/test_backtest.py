from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
import pandas as pd

from app.backtest import (
    BacktestConfig,
    BacktestEngine,
    BuyAndHoldStrategy,
    CostModel,
    EventDrivenBacktestEngine,
    PatternReferenceStrategy,
    WalkForwardBacktestValidator,
)
from app.patterns import PatternEngine
from app.backtest.strategies import Strategy
from app.providers.contracts import Candle


def candles(prices: list[tuple[int, int]]) -> list[Candle]:
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    return [
        Candle(
            timestamp=start + timedelta(days=index),
            open=Decimal(open_price),
            high=Decimal(max(open_price, close_price)),
            low=Decimal(min(open_price, close_price)),
            close=Decimal(close_price),
            volume=100,
        )
        for index, (open_price, close_price) in enumerate(prices)
    ]


def zero_cost_config(**kwargs) -> BacktestConfig:
    return BacktestConfig(
        initial_capital=1_000, force_close=False, costs=CostModel(0, 0, 0), **kwargs
    )


def test_buy_and_hold_known_return_regression():
    result = BacktestEngine().run(
        candles([(100, 100), (100, 110), (110, 121)]),
        BuyAndHoldStrategy(),
        zero_cost_config(),
    )
    assert result.metrics.final_equity == pytest.approx(1_210)
    assert result.metrics.total_return == pytest.approx(0.21)


def test_close_signal_cannot_capture_same_bar_jump():
    result = BacktestEngine().run(
        candles([(50, 100), (100, 100), (100, 100)]),
        BuyAndHoldStrategy(),
        zero_cost_config(),
    )
    assert result.metrics.total_return == 0
    assert result.equity_curve[0].position == 0
    assert result.equity_curve[1].position == 1


def test_costs_reduce_returns_and_drawdown_is_negative():
    source = candles([(100, 100), (100, 80), (80, 100)])
    without_costs = BacktestEngine().run(source, BuyAndHoldStrategy(), zero_cost_config())
    with_costs = BacktestEngine().run(
        source,
        BuyAndHoldStrategy(),
        BacktestConfig(initial_capital=1_000, costs=CostModel(0.001, 0.002, 0.001)),
    )
    assert without_costs.metrics.max_drawdown == pytest.approx(-0.2)
    assert with_costs.metrics.final_equity < without_costs.metrics.final_equity
    assert with_costs.metrics.trade_count == 2


def test_event_engine_executes_close_signal_at_next_open():
    result = EventDrivenBacktestEngine().run(
        candles([(100, 100), (100, 110), (110, 121)]),
        BuyAndHoldStrategy(),
        zero_cost_config(),
    )
    assert result.trades[0].timestamp == result.equity_curve[1].timestamp
    assert result.trades[0].side == "buy"
    assert result.trades[0].quantity == 10
    assert result.metrics.final_equity == pytest.approx(1_210)
    assert [event.event_type for event in result.events].count("fill") == 1


def test_event_engine_only_exposes_history_available_at_each_close():
    class FutureLeakingStrategy(Strategy):
        name = "future_leak_probe"

        def signals(self, source: pd.DataFrame) -> pd.Series:
            return (source["close"] < source["close"].iloc[-1]).astype("int64")

    result = EventDrivenBacktestEngine().run(
        candles([(100, 100), (100, 110), (110, 120)]),
        FutureLeakingStrategy(),
        zero_cost_config(),
    )
    assert result.trades == []
    assert result.metrics.total_return == 0


def test_event_engine_force_close_records_order_and_fill_costs():
    result = EventDrivenBacktestEngine().run(
        candles([(100, 100), (100, 110), (110, 120)]),
        BuyAndHoldStrategy(),
        BacktestConfig(
            initial_capital=1_000,
            force_close=True,
            costs=CostModel(commission_rate=0.001, tax_rate=0.002, slippage_rate=0),
        ),
    )
    assert [trade.side for trade in result.trades] == ["buy", "sell"]
    assert result.trades[-1].position_after == 0
    assert result.trades[-1].cost > 0
    assert any(
        event.event_type == "fill" and event.details.get("reason") == "force_close"
        for event in result.events
    )


def test_event_engine_limits_signal_fill_to_candle_volume_participation():
    result = EventDrivenBacktestEngine().run(
        candles([(100, 100), (100, 100), (100, 100)]),
        BuyAndHoldStrategy(),
        BacktestConfig(
            initial_capital=1_000,
            force_close=False,
            costs=CostModel(0, 0, 0),
            max_volume_participation=0.05,
        ),
    )

    assert result.trades[0].quantity == 5
    partial = next(event for event in result.events if event.event_type == "partial_fill")
    assert partial.details["requested_quantity"] == 10
    assert partial.details["unfilled_quantity"] == 5
    assert result.engine_version == "event-backtest-2026.2"


def test_event_engine_rejects_signal_order_when_candle_has_no_liquidity():
    source = candles([(100, 100), (100, 100), (100, 100)])
    source[1] = replace(source[1], volume=0)
    source[2] = replace(source[2], volume=0)
    result = EventDrivenBacktestEngine().run(
        source,
        BuyAndHoldStrategy(),
        BacktestConfig(
            initial_capital=1_000,
            force_close=False,
            costs=CostModel(0, 0, 0),
            max_volume_participation=0.1,
        ),
    )

    assert result.trades == []
    assert any(
        event.event_type == "rejected"
        and event.details.get("reason") == "insufficient_liquidity"
        for event in result.events
    )


def test_event_engine_force_close_explicitly_bypasses_volume_limit():
    source = candles([(100, 100), (100, 100), (100, 100)])
    source[-1] = replace(source[-1], volume=0)
    result = EventDrivenBacktestEngine().run(
        source,
        BuyAndHoldStrategy(),
        BacktestConfig(
            initial_capital=1_000,
            force_close=True,
            costs=CostModel(0, 0, 0),
            max_volume_participation=0.01,
        ),
    )

    force_fill = next(
        event
        for event in result.events
        if event.event_type == "fill" and event.details.get("reason") == "force_close"
    )
    assert force_fill.details["volume_limit_bypassed"] is True
    assert result.trades[-1].side == "sell"
    assert result.trades[-1].position_after == 0


def test_backtest_config_rejects_invalid_volume_participation():
    with pytest.raises(ValueError, match="max_volume_participation"):
        BacktestConfig(max_volume_participation=0)
    with pytest.raises(ValueError, match="max_volume_participation"):
        BacktestConfig(max_volume_participation=1.01)


def test_pattern_reference_strategy_executes_breakout_on_next_open():
    source = candles([(100, 100)] * 20 + [(101, 105), (106, 108)])
    source[20] = Candle(
        timestamp=source[20].timestamp,
        open=Decimal(101),
        high=Decimal(106),
        low=Decimal(100),
        close=Decimal(105),
        volume=100,
    )

    vectorized = BacktestEngine().run(
        source,
        PatternReferenceStrategy(),
        zero_cost_config(),
    )
    event_driven = EventDrivenBacktestEngine().run(
        source,
        PatternReferenceStrategy(),
        zero_cost_config(),
    )

    assert vectorized.trades[0].timestamp == source[21].timestamp
    assert event_driven.trades[0].timestamp == source[21].timestamp
    assert vectorized.equity_curve[20].position == 0
    assert event_driven.equity_curve[20].position == 0


def test_pattern_reference_strategy_rejects_invalid_configuration():
    with pytest.raises(ValueError, match="minimum_confidence"):
        PatternReferenceStrategy(minimum_confidence=1.1)
    with pytest.raises(ValueError, match="at least 21"):
        PatternReferenceStrategy(window=20)


def test_pattern_reference_strategy_caches_incremental_event_history():
    class CountingPatternEngine(PatternEngine):
        def __init__(self):
            self.calls = 0

        def analyze(self, source):
            self.calls += 1
            return super().analyze(source)

    strategy = PatternReferenceStrategy()
    counting = CountingPatternEngine()
    strategy._engine = counting
    source = candles([(100, 100)] * 24)

    EventDrivenBacktestEngine().run(source, strategy, zero_cost_config())

    assert counting.calls == len(source)


def test_walk_forward_validator_uses_non_overlapping_test_folds():
    source = candles([(100 + index, 100 + index) for index in range(180)])
    result = WalkForwardBacktestValidator().run(
        source,
        strategy_factory=BuyAndHoldStrategy,
        engine=BacktestEngine(),
        config=BacktestConfig(
            initial_capital=1_000,
            costs=CostModel(0, 0, 0),
        ),
        n_splits=3,
        warmup_candles=60,
    )

    assert result["validation_status"] == "experimental"
    assert result["n_splits"] == 3
    assert result["aggregate"]["profitable_fold_ratio"] == 1
    assert result["aggregate"]["stability"] == "consistent_positive"
    assert result["folds"][0]["test_ended_at"] < result["folds"][1]["test_started_at"]
    assert result["folds"][1]["test_ended_at"] < result["folds"][2]["test_started_at"]
    assert result["aggregate"]["total_partial_fill_count"] == 0
    assert result["execution_model"]["volume_limit_applied"] is False


def test_walk_forward_event_validation_reports_partial_execution_counts():
    source = candles([(100, 100) for _ in range(100)])
    result = WalkForwardBacktestValidator().run(
        source,
        strategy_factory=BuyAndHoldStrategy,
        engine=EventDrivenBacktestEngine(),
        config=BacktestConfig(
            initial_capital=1_000,
            costs=CostModel(0, 0, 0),
            max_volume_participation=0.01,
        ),
        n_splits=2,
        warmup_candles=60,
    )

    assert result["execution_model"]["volume_limit_applied"] is True
    assert result["execution_model"]["max_volume_participation"] == 0.01
    assert result["aggregate"]["total_partial_fill_count"] >= 1
    assert any(fold["execution"]["partial_fill_count"] >= 1 for fold in result["folds"])


def test_walk_forward_validator_requires_enough_out_of_sample_candles():
    with pytest.raises(ValueError, match="insufficient candles"):
        WalkForwardBacktestValidator().run(
            candles([(100, 100)] * 70),
            strategy_factory=BuyAndHoldStrategy,
            engine=BacktestEngine(),
            config=zero_cost_config(),
            n_splits=3,
            warmup_candles=60,
        )
