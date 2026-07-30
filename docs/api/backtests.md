# Backtest API

## Run a backtest

`POST /api/v1/backtests`

```json
{
  "symbol": "005930",
  "strategy": "ma_cross",
  "engine": "event_driven",
  "limit": 240,
  "fast_period": 5,
  "slow_period": 20,
  "initial_capital": 10000000,
  "commission_rate": 0.00015,
  "tax_rate": 0.0018,
  "slippage_rate": 0.0005,
  "max_volume_participation": 0.1,
  "corporate_action_mode": "none"
}
```

`engine` accepts `vectorized` (default) or `event_driven`. Supported strategies are
`ma_cross`, `buy_and_hold`, and `pattern_reference`.

`pattern_reference` evaluates only the candle history available at each close, retains the prior
desired position when no directional pattern is present, and executes changes at the following
open. It remains experimental until walk-forward results are stable across markets and regimes.

The response includes the engine name and version, `experimental` validation status, performance
metrics, equity curve, trades and—when the event-driven engine is selected—the chronological event
audit log. The standard compliance envelope always sets `is_investment_advice` to `false`.

Event-driven fills use the next candle open after a close signal. This means the last candle cannot
create a new executable position. An existing final position is closed at the last close when
`force_close` is enabled by the server-side configuration.

`max_volume_participation` accepts values greater than zero and at most one. It limits signal-order
fills to that fraction of the execution candle's volume in the event-driven engine. A smaller fill
creates a `partial_fill` event; zero available liquidity creates a `rejected` event. Final
`force_close` bypasses the limit to preserve the configured close-out contract and records that
bypass in the order and fill audit events. The vectorized engine does not apply this limit.

`corporate_action_mode` defaults to `none`. The explicit `forward_point_in_time` mode is available
only when corporate-action persistence is enabled. It accepts only candles whose price basis is
`unadjusted`, uses revisions known no later than the candle snapshot, and forward-normalizes
post-event candles rather than rewriting pre-event history. This prevents a later split from
changing a strategy signal that was calculated before the split was known.

The conservative first version rejects an event when its confirmed knowledge time is after its
effective time or when multiple correction/cancellation revisions are present by the end of the
snapshot. It also rejects provider-adjusted and legacy-unknown candles. Responses contain
`corporate_action_adjustment` with the mode, direction, price bases, version and exact source event
IDs/revisions used. Persisted runs store the same metadata in their config. No source candle is
mutated.
The same metadata records the validated input Provider, expected basis, verification status and
price-basis rule version. A persisted run therefore identifies both the corporate-action operation
and the Provider policy that classified its source candles.

## Walk-forward validation

`POST /api/v1/backtests/walk-forward`

```json
{
  "symbol": "005930",
  "strategy": "pattern_reference",
  "engine": "event_driven",
  "limit": 180,
  "n_splits": 3,
  "warmup_candles": 60,
  "initial_capital": 10000000,
  "commission_rate": 0.00015,
  "tax_rate": 0.0018,
  "slippage_rate": 0.0005,
  "max_volume_participation": 0.1,
  "corporate_action_mode": "none"
}
```

`n_splits` accepts 2–6 and `warmup_candles` accepts 21–120. At least ten test candles per fold are
required after the warm-up window. Fold windows are chronological and never overlap.
Event-driven responses include partial-fill and rejected-order counts per fold and in aggregate.

## Compare execution engines

`POST /api/v1/admin/backtests/compare` requires `X-Admin-Key` and accepts the common backtest
fields without an `engine` field. It fetches one candle snapshot, constructs independent strategy
instances, and runs both engines without persisting duplicate history rows.

```json
{
  "symbol": "005930",
  "strategy": "pattern_reference",
  "limit": 240,
  "initial_capital": 10000000,
  "commission_rate": 0.00015,
  "tax_rate": 0.0018,
  "slippage_rate": 0.0005,
  "max_volume_participation": 0.1,
  "corporate_action_mode": "none"
}
```

The response contains each engine's metrics and execution counts plus `event_driven - vectorized`
deltas for return, CAGR, MDD, Sharpe ratio, final equity, and trade count. Only the event-driven
engine applies candle-volume participation. This comparison remains `experimental`; a positive
delta is not a reference signal or investment recommendation.

Each engine also returns a normalized equity curve (`initial_capital = 100`). Curves are bounded to
at most 120 evenly spaced observations while always retaining the first and last timestamp. The
drawdown attached to each retained point is calculated against the full unsampled curve, so payload
reduction does not change its high-water-mark basis.

## Compare strategies

`POST /api/v1/admin/backtests/strategies/compare` requires `X-Admin-Key`. It runs
`buy_and_hold`, `ma_cross`, and `pattern_reference` using one candle snapshot and one selected
execution engine. Comparison runs are not written to normal backtest history.

```json
{
  "symbol": "005930",
  "engine": "event_driven",
  "limit": 240,
  "fast_period": 5,
  "slow_period": 20,
  "initial_capital": 10000000,
  "commission_rate": 0.00015,
  "tax_rate": 0.0018,
  "slippage_rate": 0.0005,
  "max_volume_participation": 0.1,
  "corporate_action_mode": "none"
}
```

The response preserves a fixed strategy order and reports metrics, execution counts, and signed
`strategy - buy_and_hold` deltas. `buy_and_hold` is only a neutral historical benchmark; the API
does not rank strategies or convert an observed delta into a reference signal.

Every strategy includes the same bounded normalized-equity representation used by the engine
comparison endpoint. At most 120 points are returned per strategy, with full-series drawdown
calculation occurring before sampling.
