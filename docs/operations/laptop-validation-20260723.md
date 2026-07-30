# Laptop validation record — 2026-07-23

## Scope

This is a non-production validation record for the isolated Docker Compose project
`stockpilot-validate`. It used a dedicated PostgreSQL database and volumes, Mock providers by
default, and no order, account-sync, scheduler, polling, or automatic cleanup features.

No credential values, prices, account identifiers, raw provider payloads, or provider request IDs
are recorded here.

## Completed validation

- Built the production API and web images with `INSTALL_ML=false`.
- Started PostgreSQL, Redis, API, web, and Nginx; all required services became healthy.
- Confirmed Alembic revision `20260720_0021` in PostgreSQL.
- Confirmed API readiness and Nginx health endpoints.
- Fixed Nginx health proxy forwarding so the backend receives the validated request host.
- Fixed the web market BFF allowlist so documented public read endpoints, including raw candles,
  orderbook, trades, and warnings, are forwarded explicitly.
- Fixed AI report persistence: `Decimal` values are converted to JSON-safe strings only at the
  SQLAlchemy JSON persistence boundary; the live API result retains its native values.
- Confirmed the UI path through Nginx → Next.js BFF → FastAPI for quote, candles, and AI report.
  The report includes its disclaimer, `is_investment_advice=false`, and persisted successfully.
- Created a custom-format PostgreSQL backup, restored it only into
  `stockpilot_validate_restore_check`, and verified matching Alembic revision and critical-table
  row counts. The backup runbook was corrected to use the actual `broker_accounts` table rather
  than a nonexistent `portfolios` table.
- Ran a real Toss single-symbol smoke test for `005930`: quote, daily candles, orderbook, trades,
  and warnings all returned successful responses through the application provider path.
- Verified six successful Toss provider audit records with both internal and provider request IDs,
  without logging request bodies, query strings, credentials, account data, or raw responses.
- Stopped and restarted only Redis. During the interruption, `/health/live` stayed `200`,
  `/health/ready` and market access failed closed with `503` / `RATE_LIMIT_UNAVAILABLE`; after
  Redis restart, readiness and quote access recovered to `200` without restarting the API.
- Ran the largest currently supported Mock workload serially: one 365-candle event-driven
  backtest, six-fold walk-forward validation, engine comparison, strategy comparison, and a
  lightweight prediction. All outputs remained marked `experimental`.
- Applied and tested a proxy-aware admin lockout key: only trusted, valid, bounded `X-Real-IP`
  values are used; otherwise the request peer address is used. This prevents an Nginx proxy IP
  from locking every administrator together and rejects spoofed or malformed forwarded addresses.

## Validation commands and results

| Check | Result |
| --- | --- |
| Full backend test suite | `295 passed` |
| ML-marked local tests | `4 passed, 291 deselected` |
| Ruff (`backend`, `scripts`) | passed |
| TypeScript (`apps/web`) | passed |
| Docker API readiness | `ready` |
| Nginx health | `ok` |
| PostgreSQL restore revision | `20260720_0021` matches source |

At the end of the workload, the API container used approximately `131 MiB` of memory. Docker
reported approximately `1.624 GB` of images and `2.637 GB` of build cache, of which about
`1.864 GB` was reclaimable. These measurements are snapshots, not capacity guarantees.

## Intentionally retained local validation state

- `backups/stockpilot-validate-20260723.dump` is Git-ignored and retained locally.
- `stockpilot_validate_restore_check` is retained as a restore-verification database.
- Only temporary dump files inside the PostgreSQL container were removed.

Do not use `docker compose down -v`, delete the backup, or drop the restore database without an
explicit operator decision.

## Deferred to the desktop or additional credentials

- KIS REST/WebSocket validation: `KIS_APP_KEY` and `KIS_APP_SECRET` are not configured.
- ML Docker image with `INSTALL_ML=true`, XGBoost dependency installation, artifact staging, and
  long training. The current laptop image deliberately keeps ML dependencies out of Docker.
- Multi-symbol or multi-year backfills, production-volume partition measurements, and long
  walk-forward workloads. Current public APIs cap a request at 365 candles and no batch runner is
  implemented yet.
- Real-provider soak tests and naturally occurring 401/403/429/5xx handling. Do not deliberately
  cause provider errors with production credentials.
- Monitoring profile capacity/retention validation and deployment production preflight. The local
  `.env` is a development configuration and is not a production-preflight candidate.
- Production-side OAuth credential validation remains deferred, but the Toss token issuance path now
  has MockTransport contract coverage for one privacy-minimized `AUTH` audit event per real network
  issuance (including HTTP authentication, invalid-envelope, and transport failures). Cache hits,
  request bodies, client credentials, access tokens, account identifiers, and raw responses are not
  recorded.
