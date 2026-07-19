# Point-in-time corporate action adjustments

Corporate actions can make historical prices discontinuous, but rewriting source candles would
destroy auditability and make past model or backtest results impossible to reproduce. StockPilot
therefore stores action revisions separately and creates adjusted candle views in memory.

## Immutable source and price basis

Every candle carries a `price_basis`:

- `unadjusted`: eligible for the StockPilot corporate-action engine.
- `provider_adjusted`: already adjusted by the external provider and rejected by this engine to
  prevent double adjustment. Toss daily candles currently use this value because the request sets
  `adjusted=true`.
- `unknown`: migrated legacy data; it cannot be adjusted until its provenance is verified.
- `point_in_time_adjusted`: an in-memory output view produced by adjustment version `2026.1`.

Raw and cleaned database rows are not overwritten by the adjustment engine. Weekly and monthly
aggregation preserves a single price basis and refuses mixed-basis input.

## Event revision model

Migration `20260719_0018` adds `corporate_actions` and the candle `price_basis` column. Each action
revision records:

- symbol, source and source event ID;
- immutable positive revision number;
- split, reverse split, cash dividend, stock dividend or rights issue classification;
- announcement time, effective time and `known_at` time;
- positive price and volume factors;
- announced, confirmed or cancelled status;
- deterministic adjustment-rule version and database recording time.

`(source, symbol, event_id, revision)` is unique. Replaying an identical revision is idempotent,
while a different payload for an existing revision is rejected. Corrections must create a new revision so
the old knowledge state remains reproducible.

## Look-ahead protection

For an analysis timestamp `T`, the engine:

1. ignores revisions whose `known_at` is after `T`;
2. ignores events whose effective time is after `T`;
3. chooses the latest known revision for each source event;
4. applies only the latest revision when its status is `confirmed`;
5. adjusts only candles strictly before the event's effective timestamp.

A cancellation or correction therefore changes results only after that revision became known. All
timestamps must be timezone-aware. Price and volume factors must be positive.

## Current integration boundary

`GET /api/v1/admin/corporate-actions` provides authenticated, read-only revision history with an
optional symbol and point-in-time filter. The admin UI exposes the same history and explicitly
reports `preview_only` and `raw_candles_mutated=false`.

The engine is not yet automatically inserted into indicators, Score, ML or backtests. This is
intentional: a trusted corporate-action collection source and historical price-basis verification
must exist first. Consumers must opt in with candles explicitly marked `unadjusted`; provider-
adjusted or legacy-unknown candles fail closed.
