from dataclasses import asdict

import pandas as pd

from app.backtest.metrics import calculate_metrics
from app.backtest.models import BacktestConfig, BacktestResult, EquityPoint, Trade
from app.backtest.strategies import Strategy
from app.providers.contracts import Candle


ENGINE_VERSION = "backtest-2026.1"


class BacktestEngine:
    """Long-only core where a close signal at T becomes executable at T+1 open."""

    version = ENGINE_VERSION
    status = "experimental"

    def run(
        self, candles: list[Candle], strategy: Strategy, config: BacktestConfig | None = None
    ) -> BacktestResult:
        config = config or BacktestConfig()
        if len(candles) < 2:
            raise ValueError("at least two candles are required")
        frame = (
            pd.DataFrame([asdict(candle) for candle in candles])
            .sort_values("timestamp")
            .reset_index(drop=True)
        )
        for column in ("open", "high", "low", "close"):
            frame[column] = frame[column].astype(float)

        observed_signal = (
            strategy.signals(frame).reindex(frame.index).fillna(0).clip(0, 1).astype(int)
        )
        # A signal is only known after bar T closes; shift enforces execution at T+1 open.
        position = observed_signal.shift(1, fill_value=0).astype(int)
        previous_position = position.shift(1, fill_value=0).astype(int)
        previous_close = frame["close"].shift(1)

        overnight_return = previous_position * (frame["open"] / previous_close - 1).fillna(0)
        intraday_return = position * (frame["close"] / frame["open"] - 1)
        gross_return = (1 + overnight_return) * (1 + intraday_return) - 1

        buys = (position - previous_position).clip(lower=0)
        sells = (previous_position - position).clip(lower=0)
        buy_cost_rate = config.costs.commission_rate + config.costs.slippage_rate
        sell_cost_rate = (
            config.costs.commission_rate + config.costs.tax_rate + config.costs.slippage_rate
        )
        net_return = gross_return - buys * buy_cost_rate - sells * sell_cost_rate

        if config.force_close and position.iloc[-1] == 1:
            net_return.iloc[-1] -= sell_cost_rate

        equity = config.initial_capital * (1 + net_return).cumprod()
        trades = self._trades(
            frame,
            position,
            previous_position,
            equity.shift(1).fillna(config.initial_capital),
            config,
        )
        if config.force_close and position.iloc[-1] == 1:
            base_equity = float(equity.iloc[-2]) if len(equity) > 1 else config.initial_capital
            trades.append(
                Trade(
                    timestamp=frame["timestamp"].iloc[-1],
                    side="sell",
                    execution_price=float(frame["close"].iloc[-1])
                    * (1 - config.costs.slippage_rate),
                    cost=base_equity * (config.costs.commission_rate + config.costs.tax_rate),
                    position_after=0,
                )
            )

        points = [
            EquityPoint(
                row.timestamp,
                round(float(row.equity), 4),
                round(float(row.daily_return), 8),
                int(row.position),
            )
            for row in pd.DataFrame(
                {
                    "timestamp": frame["timestamp"],
                    "equity": equity,
                    "daily_return": net_return,
                    "position": position,
                }
            ).itertuples(index=False)
        ]
        metrics = calculate_metrics(equity, net_return, trades, len(frame), config)
        return BacktestResult(self.version, self.status, strategy.name, metrics, points, trades)

    @staticmethod
    def _trades(
        frame: pd.DataFrame,
        position: pd.Series,
        previous_position: pd.Series,
        previous_equity: pd.Series,
        config: BacktestConfig,
    ) -> list[Trade]:
        trades: list[Trade] = []
        for index in frame.index:
            change = int(position.iloc[index] - previous_position.iloc[index])
            if change == 1:
                trades.append(
                    Trade(
                        frame["timestamp"].iloc[index],
                        "buy",
                        float(frame["open"].iloc[index]) * (1 + config.costs.slippage_rate),
                        float(previous_equity.iloc[index]) * config.costs.commission_rate,
                        1,
                    )
                )
            elif change == -1:
                trades.append(
                    Trade(
                        frame["timestamp"].iloc[index],
                        "sell",
                        float(frame["open"].iloc[index]) * (1 - config.costs.slippage_rate),
                        float(previous_equity.iloc[index])
                        * (config.costs.commission_rate + config.costs.tax_rate),
                        0,
                    )
                )
        return trades
