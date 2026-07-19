# Admin API and dashboard

The read-only operations dashboard is available at `/admin`. It provides persisted backtest
history, reference price alerts, watchlists, and own-account portfolio analysis without exposing
the administrator secret to browser JavaScript.

## Security boundary

Set the same high-entropy `ADMIN_API_KEY` for the FastAPI and Next.js server processes. The browser
calls the Next.js same-origin proxy, and the proxy adds `X-Admin-Key` only on the server side. It
must also authenticate to the administrator page and BFF with `ADMIN_UI_USERNAME` and
`ADMIN_UI_PASSWORD`. In production both are required and the password must contain at least 16
characters. HTTP Basic authentication is an internal deployment boundary and must only be exposed
behind HTTPS.

If the key is missing, the proxy and backend endpoints fail closed with HTTP 503. An invalid key
returns HTTP 401. This shared-key gate is an interim internal-operations boundary; user accounts,
roles and externally exposed administration still require JWT/OAuth-based RBAC before production.
Repeated invalid credentials are temporarily blocked with HTTP 429 and a `Retry-After` header.
Sensitive responses are marked `Cache-Control: no-store, private`.

## Endpoints

- `GET /api/v1/admin/operations/status`
- `GET /api/v1/admin/data-quality?limit=50&offset=0&symbol=005930&severity=error`
- `GET /api/v1/admin/ingestion`
- `POST /api/v1/admin/ingestion/{symbol}?limit=120`
- `GET /api/v1/admin/provider-audits?limit=50&offset=0&provider=toss&outcome=error`
- `POST /api/v1/admin/provider-audits/cleanup`
- `GET /api/v1/admin/backtests?limit=25&offset=0&symbol=005930`
- `GET /api/v1/admin/backtests/{run_id}`
- `GET /api/v1/admin/models?symbol=005930&algorithm=xgboost&horizon_days=5`
- `POST /api/v1/admin/models/{version}/promote`
- `GET|POST /api/v1/admin/watchlist`
- `DELETE /api/v1/admin/watchlist/{symbol}`
- `GET|POST /api/v1/admin/alerts`
- `POST /api/v1/admin/alerts/evaluate`
- `DELETE /api/v1/admin/alerts/{alert_id}`
- `GET /api/v1/broker-accounts`
- `POST /api/v1/portfolios/{account_seq}/sync`

The list endpoint returns an empty result with `persistence_status=disabled` when database
persistence is off. Detail requests return HTTP 503 in that state.

The operations status endpoint combines bounded PostgreSQL and Redis readiness probes with a
secret-free view of active providers, feature flags and realtime limits. The admin dashboard
refreshes it every 30 seconds. It exposes only provider names and boolean configuration state;
credentials, URLs and DSNs are never returned.

The data-quality endpoint reads persisted pipeline validation logs in reverse chronological order.
It supports bounded pagination plus optional symbol and `error|warning` filters, and returns counts
for the active filter. When persistence is disabled it returns an explicit disabled state rather
than attempting an in-memory operational history.

The ingestion status endpoint reports the configured scheduler universe and bounded collection
settings. Manual ingestion is an explicit administrator action and accepts 30–365 candles for a
validated symbol. It persists raw and cleaned candles plus quality logs, but never calls account or
order capabilities. Automatic scheduling requires persistence and accepts at most 50 unique
symbols from `SCHEDULER_SYMBOLS`.

Provider audit history stores only bounded operational metadata: provider, method, endpoint path,
API group, outcome, status, attempt count, duration and internal/external request IDs. It never
stores credentials, account numbers, query parameters, request bodies or response bodies.
`PROVIDER_AUDIT_CLEANUP_ENABLED=true` schedules a daily cleanup at minute 15 of the configured
`PROVIDER_AUDIT_CLEANUP_HOUR_KST`; the default retention is 90 days and the accepted range is
7–3650 days. The manual cleanup endpoint applies only this configured cutoff and can delete only
rows from `provider_audit_logs`. Cleanup failures are reported in operations status without
interrupting market-data requests or API startup.

The broker account endpoints use the same `X-Admin-Key` boundary even though their paths are not
under `/admin`. Account numbers are masked, synchronization is read-only, and portfolio results
always return `execution_enabled=false`.
