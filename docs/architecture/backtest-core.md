# Backtest Core

StockPilot exposes two long-only backtest engines. Every result remains `experimental` until its
strategy has passed quantitative validation.

## Vectorized engine

`BacktestEngine` is the fast research engine. A signal observed after candle T closes is shifted
and executed at candle T+1 open. This prevents a close-derived signal from capturing a price move
that already happened inside the same candle.

## Event-driven engine

Set `engine` to `event_driven` in `POST /api/v1/backtests`. The engine processes one candle at a
time and passes only history through the current close to the strategy. The event stream records:

- `market`: OHLCV data visible at the current step
- `signal`: desired position observed after the close
- `order`: an order scheduled for the next candle open
- `fill`: quantity, execution price, fees, taxes and cash after execution
- `partial_fill`: requested, filled and unfilled quantities after the candle-volume cap
- `rejected`: orders rejected because cash or a position is unavailable

Signal orders execute at the next candle open. When `force_close` is enabled, the final position
is closed at the last candle close and recorded with `reason=force_close`.

## Costs and sizing

Both engines apply commission, sell tax and slippage. The event engine first calculates the largest
whole-share quantity affordable by cash, then caps signal fills at
`candle volume × max_volume_participation`. Residual quantities are cancelled and recorded as
partial fills. A partially filled sell can be requested again after the next close signal. The
final forced close bypasses the volume cap and records that exception. Its equity curve is marked
to each candle close.

Default costs are commission 0.015%, sell tax 0.18%, and slippage 0.05%. Results include total
return, CAGR, maximum drawdown, Sharpe ratio, completed-trade win rate, trade count, equity curve,
trades and the event audit log.

## Corporate-action-safe opt-in

Backtests default to the provider candle basis with `corporate_action_mode=none`. An operator may
explicitly select `forward_point_in_time` only when immutable corporate-action persistence exists.
The backtest adapter refuses `provider_adjusted`, `unknown`, mixed-basis and already-adjusted input.

The general chart view uses backward adjustment to display a current point-in-time price history;
that representation is not passed to a strategy because it would let an event learned later alter
earlier signals. The backtest-specific engine instead leaves every pre-event candle untouched and
applies inverse factors from the effective candle forward. For a 2-for-1 split, post-event prices
are multiplied by two and post-event volume is divided by two, preserving the earlier unit basis
without knowledge leaking into earlier observations.

Version `2026.1` accepts only a single confirmed revision whose `known_at` is no later than its
effective time. A later correction or cancellation makes the entire opt-in request fail instead of
silently choosing a hindsight revision. Every run reports and, when enabled, persists its mode,
input/output basis, source, event ID, revision, effective time, known time and rule version.

## Pattern reference strategy

`pattern_reference` converts the deterministic Pattern Engine output into a long-only research
position. The highest-confidence non-neutral pattern available at each close is used: an upward
pattern requests a long position and a downward pattern requests a flat position. When no new
directional pattern is present, the previous desired position is retained.

The detector receives at most the trailing 60 candles ending at the current bar. Both backtest
engines then execute a changed desired position at the next candle open, so the strategy cannot
capture the move inside the candle that formed the pattern. Its 0.68 rule-strength threshold is
fixed in version `patterns-2026.1` and is not a calibrated return probability.

## Walk-forward strategy validation

`POST /api/v1/backtests/walk-forward` evaluates a strategy over 2–6 chronological,
non-overlapping future folds. Each fold receives a configurable historical warm-up window, while
cash, position and performance accounting restart from the configured initial capital at the test
boundary.

The response includes each fold's return, CAGR, MDD, Sharpe ratio, win rate and trade count plus:

- mean out-of-sample total return
- profitable-fold ratio
- worst fold MDD
- mean fold Sharpe ratio
- total trade count
- total partial-fill count and rejected-order count for the event engine
- descriptive stability: `consistent_positive`, `mixed`, or `consistent_negative`

Stability is only a compact description of the observed folds. It does not promote a strategy,
remove `experimental` status, estimate future probability, or constitute investment advice.

The admin dashboard exposes the same validation through an authenticated Next.js BFF. Operators
can select the symbol, strategy, engine, volume participation, fold count, warm-up length and candle
count, then inspect aggregate and per-fold metrics. `ADMIN_API_KEY` remains server-side and is never returned to the
browser. Backtest execution and validation POST routes use the stricter expensive-request
rate-limit group.

## Same-snapshot engine comparison

The protected administrator endpoint `POST /api/v1/admin/backtests/compare` is an engine-parity
diagnostic. Market candles are requested once and reused by both engines, while each engine gets a
fresh strategy instance so stateful incremental detectors cannot contaminate the other run. The
comparison is intentionally not persisted as two normal runs.

The result reports common assumptions, engine versions, performance metrics, execution counts,
and signed deltas calculated as event-driven minus vectorized. Its purpose is to expose the impact
of whole-share cash accounting and liquidity constraints, not to rank strategies. The endpoint and
its Next.js BFF are administrator-only and use the expensive-request rate-limit group.

The administrator UI overlays both normalized equity curves. To keep browser and API memory bounded,
the comparison serializer reduces each curve to at most 120 evenly spaced points and preserves both
endpoints. Drawdown is computed before sampling against every original equity point.

## Same-snapshot strategy comparison

The protected `POST /api/v1/admin/backtests/strategies/compare` diagnostic runs every supported
strategy with the same candle objects, costs, capital, execution engine, and close-out rules. Each
strategy receives a fresh instance. Results are returned in a stable order with `buy_and_hold` as a
historical benchmark and are not persisted as ordinary runs.

The administrator table shows absolute metrics, execution constraints, and signed deltas from the
benchmark. No automatic winner, promotion, recommendation, or future-return inference is produced.
The route is administrator-only and belongs to the expensive-request rate-limit group.

The strategy and engine comparison panels share one `NormalizedEquityChart` component. It accepts
an arbitrary list of named series, derives one common vertical scale including the initial-capital
baseline, and renders compact SVG polylines without adding a charting dependency.
