# Candle data-quality pipeline

Daily candles are stored in two stages. The provider response is preserved as `raw`, while only
records that pass deterministic OHLCV checks are written as `cleaned`. Validation never silently
changes source prices or volume.

## Rules

- `duplicate_timestamp` rejects a repeated timestamp.
- `invalid_ohlc` rejects prices outside the candle high/low boundary.
- `negative_volume` rejects negative volume.
- `out_of_order` records a provider ordering failure; cleaning still sorts valid records.
- `missing_daily_candles` warns about a suspicious long gap but does not remove either candle.

Gap detection sorts unique timestamps and counts weekdays strictly between adjacent candles. It
creates a warning only when at least five weekdays are absent. This conservative threshold avoids
marking ordinary weekends and short exchange holidays as missing data. It is not a replacement for
an exchange calendar: before production backfills, the warning should be reconciled against the
market-specific trading calendar and suspensions.

Pipeline/aggregation version `2026.2` introduces the long-gap rule. Quality logs are persisted for
the authenticated administrator history screen, where rule codes are paired with Korean operator
labels.
