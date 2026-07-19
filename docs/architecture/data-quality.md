# Candle data-quality pipeline

Daily candles are stored in two stages. The provider response is preserved as `raw`, while only
records that pass deterministic OHLCV checks are written as `cleaned`. Validation never silently
changes source prices or volume.

Candles also retain a price-basis provenance value. Mixing `unadjusted`, `provider_adjusted` or
legacy `unknown` bases produces a `mixed_price_basis` error, and higher-interval aggregation fails
closed rather than combining incompatible price series.

## Rules

- `duplicate_timestamp` rejects a repeated timestamp.
- `invalid_ohlc` rejects prices outside the candle high/low boundary.
- `negative_volume` rejects negative volume.
- `out_of_order` records a provider ordering failure; cleaning still sorts valid records.
- `missing_daily_candles` warns about a suspicious long gap but does not remove either candle.
- `mixed_price_basis` rejects aggregation across incompatible adjustment bases.

Gap detection sorts unique timestamps and counts weekdays strictly between adjacent candles. It
creates a warning only when at least five weekdays are absent. This conservative threshold avoids
marking ordinary weekends and short exchange holidays as missing data. It is not a replacement for
an exchange calendar: before production backfills, the warning should be reconciled against the
market-specific trading calendar and suspensions.

Pipeline/aggregation version `2026.2` introduces the long-gap rule. Quality logs are persisted for
the authenticated administrator history screen, where rule codes are paired with Korean operator
labels.
