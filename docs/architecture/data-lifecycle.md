# Operational data lifecycle

StockPilot AI separates operational retention from research and audit reproducibility. The
automatic lifecycle service can delete only three explicitly allowlisted datasets:

| Dataset | Default retention | Cutoff column |
| --- | ---: | --- |
| `data_quality_logs` | 180 days | `created_at` |
| `news` | 730 days | `created_at` |
| `disclosures` | 3650 days | `created_at` |

`created_at` is deliberately used as the storage-retention clock. Publication and filing dates
remain domain timestamps and do not unexpectedly shorten the time data is retained after it is
collected.

The repository contains a fixed model-and-column allowlist. It does not accept table or column
names from HTTP input. Candles, trades, backtest runs/results/events, predictions, AI reports,
model versions, portfolios, holdings and provider audit logs are outside this cleanup boundary.
Corporate-action revision history is also excluded because it is required for point-in-time
reconstruction.
Provider audit logs retain their separate policy and scheduler job.

## Safe operation

- `GET /api/v1/admin/data-lifecycle/preview` counts eligible rows and returns each cutoff without
  changing data. It remains available when automatic cleanup is disabled, provided persistence is
  available.
- `POST /api/v1/admin/data-lifecycle/cleanup` applies exactly the configured allowlist and cutoffs.
  It is a no-op unless `DATA_LIFECYCLE_CLEANUP_ENABLED=true`.
- All dataset deletes execute in one database transaction. A failure rolls the complete cleanup
  back instead of leaving a partially applied retention run.
- Responses and operations status contain exception types only; database exception messages are
  not returned to clients.
- Cleanup failures do not stop API startup, ingestion or market-data requests.

With persistence enabled, automatic cleanup runs daily at minute 30 of
`DATA_LIFECYCLE_CLEANUP_HOUR_KST` and once when the scheduler starts. It is disabled by default so
an operator must review the preview and retention requirements before enabling deletion.

The retention settings accept bounded values:

- `DATA_QUALITY_RETENTION_DAYS`: 30–3650
- `NEWS_RETENTION_DAYS`: 30–3650
- `DISCLOSURE_RETENTION_DAYS`: 365–7300

The `created_at` indexes introduced in migration `20260719_0017` support bounded scans and deletes
as these tables grow.
