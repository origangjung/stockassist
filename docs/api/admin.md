# Admin API and dashboard

The internal operations dashboard is available at `/admin`. It provides persisted backtest
history, reference price alerts, watchlists, own-account portfolio analysis and narrowly scoped
manual operations without exposing the administrator secret to browser JavaScript. Mutations are
separately feature-gated, bounded and disabled by default where they affect verified analysis data.

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
FastAPI and the browser administrator boundary also enforce the comma-separated `ALLOWED_HOSTS`
list before using origin or authentication metadata. Production deployments must list their exact
domains and cannot use the global wildcard.
The browser BFF additionally requires an exact same-origin `Origin` header for POST and DELETE
requests. Missing or cross-origin mutation requests return HTTP 403, while read-only GET requests
remain available after administrator authentication.

## Endpoints

- `GET /api/v1/admin/operations/status`
- `GET /api/v1/admin/data-quality?limit=50&offset=0&symbol=005930&severity=error`
- `GET /api/v1/admin/candles/price-basis-inventory?symbol=005930&limit=200`
- `GET /api/v1/admin/ingestion`
- `POST /api/v1/admin/ingestion/{symbol}?limit=120`
- `GET /api/v1/admin/provider-audits?limit=50&offset=0&provider=toss&outcome=error`
- `POST /api/v1/admin/provider-audits/cleanup`
- `GET /api/v1/admin/data-lifecycle/preview`
- `POST /api/v1/admin/data-lifecycle/cleanup`
- `GET /api/v1/admin/corporate-actions?symbol=005930&as_of=2026-01-12T00:00:00Z`
- `GET /api/v1/admin/corporate-actions/ingestion`
- `POST /api/v1/admin/corporate-actions/ingestion/{source}/{symbol}?start=2026-01-01T00:00:00Z&end=2026-12-31T23:59:59Z&limit=200`
- `GET /api/v1/admin/corporate-actions/candidates`
- `GET /api/v1/admin/corporate-actions/candidates/dart/{symbol}?start=2026-01-01&end=2026-12-31&limit=100`
- `GET /api/v1/admin/corporate-actions/approvals`
- `POST /api/v1/admin/corporate-actions/approvals/dart/{symbol}`
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

The operations response includes a non-mutating candle partition archive preview. It reports the
configured hot-storage window, cutoff month and valid monthly candidates while always returning
`automatic_action=false`. It never exposes archive paths and cannot detach or drop a partition.
See [Candle partition archive policy](../architecture/candle-partition-archive.md).

The candle price-basis inventory is read-only and groups stored candles by provider provenance,
price basis, classification rule version, stage, interval and aggregation version. Existing rows are deliberately reported as
`source_provider=legacy_unknown`; the migration does not infer a provider or modify their
`price_basis`. Pre-policy rows also retain `price_basis_rule_version=legacy_unknown`. Totals remain
accurate when the bounded group list is truncated. The endpoint always
returns `automatic_relabel=false` and `mutation_performed=false`; see
[Candle price-basis provenance and inventory](../architecture/candle-price-basis-inventory.md).
The internal `/admin` workspace exposes the same endpoint as a read-only summary and evidence table.
Successful manual candle ingestion invalidates the inventory query so newly recorded Provider and
rule-version metadata appear without reloading the page. No edit or relabel control is exposed.
Each group reports `review_status` and a bounded `required_evidence` checklist; these fields guide
manual review but do not authorize or perform historical relabeling.
The `symbol` parameter is mandatory and the UI waits for it before querying. This bounded access
pattern prevents an administrator page load from grouping the complete candle history.

Model promotion remains metadata-only by default. In an explicitly enabled XGBoost research
deployment, promotion additionally requires a staged checksum-verified artifact matching the
registry symbol, algorithm and horizon, then atomically changes the runtime pointer. Missing,
tampered or mismatched artifacts fail closed with HTTP 409.

The data-quality endpoint reads persisted pipeline validation logs in reverse chronological order.
It supports bounded pagination plus optional symbol and `error|warning` filters, and returns counts
for the active filter. When persistence is disabled it returns an explicit disabled state rather
than attempting an in-memory operational history.

The ingestion status endpoint reports the configured scheduler universe and bounded collection
settings. Manual ingestion is an explicit administrator action and accepts 30–365 candles for a
validated symbol. It persists raw and cleaned candles plus quality logs, but never calls account or
order capabilities. Automatic scheduling requires persistence and accepts at most 50 unique
symbols from `SCHEDULER_SYMBOLS`.

For SQL persistence, stock metadata, raw candles, cleaned candles and quality logs are committed as
one ingestion transaction. A failure in any write rolls back the complete batch, preventing a raw-
only or cleaned-without-quality-log state.

Provider audit history stores only bounded operational metadata: provider, method, endpoint path,
API group, outcome, status, attempt count, duration and internal/external request IDs. It never
stores credentials, account numbers, query parameters, request bodies or response bodies.
`PROVIDER_AUDIT_CLEANUP_ENABLED=true` schedules a daily cleanup at minute 15 of the configured
`PROVIDER_AUDIT_CLEANUP_HOUR_KST`; the default retention is 90 days and the accepted range is
7–3650 days. The manual cleanup endpoint applies only this configured cutoff and can delete only
rows from `provider_audit_logs`. Cleanup failures are reported in operations status without
interrupting market-data requests or API startup.

Operational lifecycle cleanup has a separate, explicit allowlist for `data_quality_logs`, `news`
and `disclosures`. Preview returns eligible counts and storage-time cutoffs without deleting data.
Cleanup is disabled unless `DATA_LIFECYCLE_CLEANUP_ENABLED=true`, and all deletes commit or roll
back together. Research, account, AI and market-history tables are not part of this endpoint. See
[Operational data lifecycle](../architecture/data-lifecycle.md).

Corporate-action history is revisioned and point-in-time bounded. The endpoint is read-only and
returns action factors, effective time, `known_at`, source, revision and rule version. It never
changes candles and reports `application_mode=preview_only` plus `raw_candles_mutated=false`.
Naive `as_of` timestamps are rejected. See
[Point-in-time corporate action adjustments](../architecture/corporate-action-adjustments.md).

Corporate-action ingestion is disabled until persistence and at least one `verified` source are
available. Experimental or disabled sources cannot write. Each manual request is limited to 500
records, validates source/symbol/time provenance, and commits the batch atomically. It only stores
immutable action metadata; it does not rewrite candles or automatically enable adjusted data in
Indicator, Score, ML or Backtest consumers.

The status response separates `sources` (registered implementations) from `source_candidates`
(evaluated but non-ingestible candidates). DART, SEC EDGAR, Nasdaq Daily List, NYSE Market Event
Feed and DTCC Asset Servicing currently appear only as experimental candidates, so the default
`verified_source_count` is zero. SEC is a filing crosscheck; the Nasdaq/NYSE/DTCC candidates require
contract and schema validation before implementation.

When `DART_API_KEY` is configured, the candidate status endpoint reports `dart` as an available
read-only collector. Candidate preview accepts at most 366 days and 200 rows and uses the expensive
rate-limit group. It queries the official structured bonus-issue and capital-reduction endpoints,
returns bounded normalized evidence and DART document links, and always reports
`write_performed=false`, `automatic_confirmation=false` and `point_in_time_eligible=false`.
The preview also returns `revision_groups`. These contain ordered receipt suggestions and evidence
reasons, but always set `requires_manual_confirmation=true` and `persistence_allowed=false`; they
cannot be submitted to the ingestion endpoint as confirmed revisions.

Manual approval is a separate, fail-closed path and is disabled by default. Enabling
`CORPORATE_ACTION_APPROVAL_ENABLED=true` also requires persistence, `ADMIN_API_KEY`, and
`DART_API_KEY`. The POST body must repeat the candidate date range, group hint and receipt number,
provide a timezone-aware exchange effective time, include an HTTPS evidence URL hosted by KRX,
and use the exact confirmation phrase returned by the approval status endpoint. The server
re-fetches the candidate and rejects changed groups or incomplete factors. It derives factors from
the re-fetched filing rather than accepting them from the client. The confirmed revision and its
evidence audit record commit atomically, identical retries are idempotent, and `known_at` is always
the actual approval time. Approval never executes an order or rewrites stored candles.
The administrator UI exposes the same guarded workflow only after a candidate is selected. It does
not prefill the effective timestamp, exchange evidence URL or confirmation phrase. The browser
calls the same-origin BFF, while `X-Admin-Key` remains server-side.
The approval status also reports the exchange-verification source catalog. The public KRX OPEN API
is marked unavailable for corporate-action effective dates, while the KRX EOD market-event feed is
marked contract-required with an unverified schema. Neither state enables automated verification.
Registered structured verification providers must return evidence on the same authoritative host
as their source metadata; credential-bearing URLs, non-standard ports and fragments fail closed.

The broker account endpoints use the same `X-Admin-Key` boundary even though their paths are not
under `/admin`. Account numbers are masked, synchronization is read-only, and portfolio results
always return `execution_enabled=false`.
