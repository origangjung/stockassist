from math import sqrt

import pandas as pd

from app.backtest.models import BacktestConfig, PerformanceMetrics, Trade


def calculate_metrics(
    equity: pd.Series,
    returns: pd.Series,
    trades: list[Trade],
    observation_count: int,
    config: BacktestConfig,
) -> PerformanceMetrics:
    final_equity = float(equity.iloc[-1])
    total_return = final_equity / config.initial_capital - 1
    years = max(
        (observation_count - 1) / config.annualization_days,
        1 / config.annualization_days,
    )
    cagr = (final_equity / config.initial_capital) ** (1 / years) - 1
    running_peak = equity.cummax().clip(lower=config.initial_capital)
    drawdown = equity / running_peak - 1
    volatility = float(returns.std(ddof=1)) if len(returns) > 1 else 0.0
    sharpe = (
        float(returns.mean()) / volatility * sqrt(config.annualization_days)
        if volatility > 0
        else 0.0
    )
    pairs = [
        (trades[index], trades[index + 1])
        for index in range(len(trades) - 1)
        if trades[index].side == "buy" and trades[index + 1].side == "sell"
    ]
    completed_returns = [
        (sell.execution_price * (1 - config.costs.commission_rate - config.costs.tax_rate))
        / (buy.execution_price * (1 + config.costs.commission_rate))
        - 1
        for buy, sell in pairs
    ]
    win_rate = (
        sum(value > 0 for value in completed_returns) / len(completed_returns)
        if completed_returns
        else 0.0
    )
    return PerformanceMetrics(
        total_return=round(total_return, 8),
        cagr=round(cagr, 8),
        max_drawdown=round(float(drawdown.min()), 8),
        sharpe_ratio=round(sharpe, 6),
        win_rate=round(win_rate, 6),
        trade_count=len(trades),
        final_equity=round(final_equity, 4),
    )
