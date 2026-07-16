from dataclasses import asdict, dataclass
from datetime import datetime

import pandas as pd

from app.backtest.metrics import calculate_metrics
from app.backtest.models import (
    BacktestConfig,
    BacktestEvent,
    BacktestResult,
    EquityPoint,
    Trade,
)
from app.backtest.strategies import Strategy
from app.providers.contracts import Candle


EVENT_ENGINE_VERSION = "event-backtest-2026.2"


@dataclass(frozen=True)
class _PendingOrder:
    side: str
    created_at: datetime
    execute_at: datetime


class EventDrivenBacktestEngine:
    """Sequential long-only engine with close-to-next-open order execution."""

    version = EVENT_ENGINE_VERSION
    status = "experimental"

    def run(
        self,
        candles: list[Candle],
        strategy: Strategy,
        config: BacktestConfig | None = None,
    ) -> BacktestResult:
        config = config or BacktestConfig()
        if len(candles) < 2:
            raise ValueError("at least two candles are required")

        frame = pd.DataFrame([asdict(candle) for candle in candles])
        frame = frame.sort_values("timestamp").reset_index(drop=True)
        for column in ("open", "high", "low", "close"):
            frame[column] = frame[column].astype(float)
        if (frame[["open", "high", "low", "close"]] <= 0).any().any():
            raise ValueError("candle prices must be positive")
        if frame["timestamp"].duplicated().any():
            raise ValueError("candle timestamps must be unique")

        cash = float(config.initial_capital)
        quantity = 0
        pending: _PendingOrder | None = None
        previous_equity = float(config.initial_capital)
        equity_values: list[float] = []
        return_values: list[float] = []
        points: list[EquityPoint] = []
        trades: list[Trade] = []
        events: list[BacktestEvent] = []

        for index, row in frame.iterrows():
            timestamp = row["timestamp"]
            events.append(
                BacktestEvent(
                    timestamp,
                    "market",
                    {
                        "open": float(row["open"]),
                        "high": float(row["high"]),
                        "low": float(row["low"]),
                        "close": float(row["close"]),
                        "volume": int(row["volume"]),
                    },
                )
            )

            if pending is not None:
                cash, quantity = self._execute(
                    pending.side,
                    timestamp,
                    float(row["open"]),
                    int(row["volume"]),
                    cash,
                    quantity,
                    config,
                    trades,
                    events,
                    reason="signal",
                )
                pending = None

            # Only the history available at this close is passed to the strategy.
            history = frame.iloc[: index + 1].copy()
            observed = strategy.signals(history).reindex(history.index).fillna(0)
            desired_position = int(observed.clip(0, 1).astype(int).iloc[-1])
            current_position = int(quantity > 0)
            events.append(
                BacktestEvent(
                    timestamp,
                    "signal",
                    {
                        "strategy": strategy.name,
                        "desired_position": desired_position,
                        "position_before": current_position,
                    },
                )
            )

            if desired_position != current_position and index + 1 < len(frame):
                side = "buy" if desired_position == 1 else "sell"
                execute_at = frame["timestamp"].iloc[index + 1]
                pending = _PendingOrder(side, timestamp, execute_at)
                events.append(
                    BacktestEvent(
                        timestamp,
                        "order",
                        {
                            "side": side,
                            "execute_at": execute_at.isoformat(),
                            "quantity_policy": "all_available",
                            "max_volume_participation": config.max_volume_participation,
                            "reason": "signal",
                        },
                    )
                )

            is_last = index == len(frame) - 1
            if is_last and config.force_close and quantity > 0:
                events.append(
                    BacktestEvent(
                        timestamp,
                        "order",
                        {
                            "side": "sell",
                            "execute_at": timestamp.isoformat(),
                            "quantity": quantity,
                            "reason": "force_close",
                            "volume_limit_bypassed": True,
                        },
                    )
                )
                cash, quantity = self._execute(
                    "sell",
                    timestamp,
                    float(row["close"]),
                    None,
                    cash,
                    quantity,
                    config,
                    trades,
                    events,
                    reason="force_close",
                    bypass_volume_limit=True,
                )

            equity = cash + quantity * float(row["close"])
            daily_return = equity / previous_equity - 1 if previous_equity else 0.0
            equity_values.append(equity)
            return_values.append(daily_return)
            points.append(
                EquityPoint(
                    timestamp=timestamp,
                    equity=round(equity, 4),
                    daily_return=round(daily_return, 8),
                    position=int(quantity > 0),
                )
            )
            previous_equity = equity

        equity_series = pd.Series(equity_values, dtype="float64")
        return_series = pd.Series(return_values, dtype="float64")
        metrics = calculate_metrics(
            equity_series,
            return_series,
            trades,
            len(frame),
            config,
        )
        return BacktestResult(
            self.version,
            self.status,
            strategy.name,
            metrics,
            points,
            trades,
            events,
        )

    @staticmethod
    def _execute(
        side: str,
        timestamp: datetime,
        market_price: float,
        market_volume: int | None,
        cash: float,
        quantity: int,
        config: BacktestConfig,
        trades: list[Trade],
        events: list[BacktestEvent],
        *,
        reason: str,
        bypass_volume_limit: bool = False,
    ) -> tuple[float, int]:
        if side == "buy":
            execution_price = market_price * (1 + config.costs.slippage_rate)
            requested_quantity = int(
                cash // (execution_price * (1 + config.costs.commission_rate))
            )
            if requested_quantity <= 0:
                events.append(
                    BacktestEvent(
                        timestamp,
                        "rejected",
                        {
                            "side": side,
                            "reason": "insufficient_cash",
                        },
                    )
                )
                return cash, quantity
            filled_quantity = EventDrivenBacktestEngine._bounded_quantity(
                requested_quantity,
                market_volume,
                config.max_volume_participation,
                bypass_volume_limit,
            )
            if filled_quantity <= 0:
                events.append(
                    BacktestEvent(
                        timestamp,
                        "rejected",
                        {
                            "side": side,
                            "reason": "insufficient_liquidity",
                            "requested_quantity": requested_quantity,
                            "market_volume": market_volume or 0,
                            "max_volume_participation": config.max_volume_participation,
                        },
                    )
                )
                return cash, quantity
            notional = execution_price * filled_quantity
            commission = notional * config.costs.commission_rate
            cash -= notional + commission
            quantity += filled_quantity
            tax = 0.0
        elif side == "sell":
            if quantity <= 0:
                events.append(
                    BacktestEvent(
                        timestamp,
                        "rejected",
                        {
                            "side": side,
                            "reason": "no_position",
                        },
                    )
                )
                return cash, quantity
            execution_price = market_price * (1 - config.costs.slippage_rate)
            requested_quantity = quantity
            filled_quantity = EventDrivenBacktestEngine._bounded_quantity(
                requested_quantity,
                market_volume,
                config.max_volume_participation,
                bypass_volume_limit,
            )
            if filled_quantity <= 0:
                events.append(
                    BacktestEvent(
                        timestamp,
                        "rejected",
                        {
                            "side": side,
                            "reason": "insufficient_liquidity",
                            "requested_quantity": requested_quantity,
                            "market_volume": market_volume or 0,
                            "max_volume_participation": config.max_volume_participation,
                        },
                    )
                )
                return cash, quantity
            notional = execution_price * filled_quantity
            commission = notional * config.costs.commission_rate
            tax = notional * config.costs.tax_rate
            cash += notional - commission - tax
            quantity -= filled_quantity
        else:
            raise ValueError(f"unsupported order side: {side}")

        unfilled_quantity = requested_quantity - filled_quantity
        if unfilled_quantity > 0:
            events.append(
                BacktestEvent(
                    timestamp,
                    "partial_fill",
                    {
                        "side": side,
                        "requested_quantity": requested_quantity,
                        "filled_quantity": filled_quantity,
                        "unfilled_quantity": unfilled_quantity,
                        "market_volume": market_volume,
                        "max_volume_participation": config.max_volume_participation,
                        "reason": reason,
                    },
                )
            )
        fees = commission + tax
        trades.append(
            Trade(
                timestamp=timestamp,
                side=side,
                execution_price=execution_price,
                cost=fees,
                position_after=int(quantity > 0),
                quantity=filled_quantity,
                cash_after=round(cash, 4),
            )
        )
        events.append(
            BacktestEvent(
                timestamp,
                "fill",
                {
                    "side": side,
                    "requested_quantity": requested_quantity,
                    "quantity": filled_quantity,
                    "unfilled_quantity": unfilled_quantity,
                    "market_price": market_price,
                    "execution_price": execution_price,
                    "commission": commission,
                    "tax": tax,
                    "cash_after": round(cash, 4),
                    "reason": reason,
                    "volume_limit_bypassed": bypass_volume_limit,
                },
            )
        )
        return cash, quantity

    @staticmethod
    def _bounded_quantity(
        requested_quantity: int,
        market_volume: int | None,
        max_volume_participation: float,
        bypass_volume_limit: bool,
    ) -> int:
        if bypass_volume_limit or market_volume is None:
            return requested_quantity
        return min(requested_quantity, int(max(0, market_volume) * max_volume_participation))
