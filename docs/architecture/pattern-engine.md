# Chart and candlestick pattern engine

`PatternEngine` is a deterministic calculation component. It consumes cleaned OHLCV
candles and never fetches market data, generates prose, or issues trading instructions.

## Supported patterns

| Category | Pattern |
| --- | --- |
| Candlestick | doji, hammer, shooting star |
| Two-candle | bullish engulfing, bearish engulfing |
| Chart | prior 20-candle range breakout up/down |
| Chart | confirmed double top/bottom |

Every result includes its category, directional bias, confidence, detection window,
evidence, `data_as_of`, engine version, and `validation_status: experimental`.
Confidence is rule strength, not a calibrated probability of future returns.

The double-top and double-bottom rules require two local extrema within a 3% price
tolerance, a separation of 5–35 candles, and a latest-close neckline confirmation.
Unconfirmed shapes are not returned. Breakouts compare the latest close only with the
preceding 20 completed candles.

## Look-ahead protection

The engine sorts only the supplied candles and treats the last candle as the analysis
timestamp. It cannot access later candles. The application passes the same cleaned candle
bundle used by the Score Engine into the Chart Pattern Agent, avoiding both a second
provider request and inconsistent timestamps.

## API and AI report integration

- `GET /api/v1/stocks/{symbol}/patterns?limit=180` exposes standalone structured results.
- `ChartPatternAnalysisAgent` adds the same result to `chart_patterns` and
  `agent_findings.chart_pattern` in an AI report.
- The LLM receives only the calculated result and may explain it, but it does not detect
  or score patterns itself.

Pattern rules remain experimental until their precision, forward returns, transaction
cost sensitivity, and market-regime stability pass backtest validation.

The `pattern_reference` backtest strategy is the first validation harness for these rules. It can
run through either the vectorized or event-driven engine with the same commission, tax, slippage,
T+1 execution, metrics, persistence, and audit-event contracts as other strategies.

Walk-forward validation can then run the strategy over non-overlapping chronological folds. A
positive aggregate does not change the engine's `experimental` status; promotion criteria require
separate versioned thresholds and broader market-regime evidence.
