# Candle partition archive policy

`stock_candles` is monthly partitioned because market history grows continuously and is required
for indicator, score, ML and backtest reproducibility. Old candle partitions therefore follow a
review-and-archive policy rather than automatic deletion.

## Preview rules

- `PARTITION_ARCHIVE_AFTER_MONTHS` controls the hot-storage window. The default is 120 months and
  the accepted range is 12–600 months.
- The cutoff is the first day of the current UTC month shifted backward by that window.
- A monthly partition is a candidate only when its exclusive end boundary is on or before the
  cutoff. The currently open month can never be selected.
- Only names matching `stock_candles_YYYY_MM` with a valid month are classified.
  `stock_candles_default`, malformed names and unrelated child tables are ignored.
- The operations API and admin screen expose this as `preview_only` with
  `automatic_action=false`.

The preview does not detach, export, move, truncate or drop a partition. It also does not alter
backtest or model metadata.

## Operator-controlled archive workflow

An actual archive is a desktop/operations task and requires a separately approved maintenance
window:

1. Create and restore-test a complete PostgreSQL backup.
2. Confirm no ingestion or backfill job writes into the candidate month.
3. Export the candidate partition to encrypted, access-controlled storage.
4. Record row count, minimum/maximum candle timestamp, file size, checksum, schema/Alembic revision
   and storage location in an archive manifest.
5. Restore the exported data into an isolated database and run representative candle and backtest
   reads.
6. Only after approval, detach the production partition. Do not immediately drop it; retain a
   rollback window defined by the organization's data policy.
7. Verify API readiness, ingestion and historical-query behavior after the maintenance window.

No detach or drop command is kept in application code because a storage incident, corporate-action
backfill or model reproduction request can make old candles immediately necessary. Production
archive automation should be introduced only after backup encryption, manifest storage, restore
tests, monitoring and rollback ownership are established.
