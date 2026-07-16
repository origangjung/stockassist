# Security baseline

## Network boundary

Docker Compose binds API, web, PostgreSQL, Redis, Nginx, Prometheus, Alertmanager, and Grafana ports to `127.0.0.1`. They are not exposed to the local network by default. Production deployment still requires an HTTPS reverse proxy, firewall rules, secret manager, fixed egress IP, and non-default database and Grafana passwords.

The Next.js container runs an optimized production build with `next start`. Set `PUBLIC_API_URL` before building when the browser-facing API origin is not `http://localhost:8080`.

## HTTP and WebSocket controls

- FastAPI, Next.js, and Nginx add `nosniff`, frame-denial, referrer, and permissions-policy headers.
- Administrator, account, portfolio, watchlist, and alert responses use `Cache-Control: no-store, private`.
- `CORS_ORIGINS` is an explicit comma-separated allowlist.
- Browser WebSocket requests with an untrusted `Origin` are rejected with code `4403`.
- Realtime hubs cap both distinct symbols and total concurrent connections; Provider errors use the same redacted public messages as HTTP responses.
- Nginx limits request bodies to 1 MiB.

## Abuse controls

Public API requests use an in-process sliding-window limit. Expensive AI report, prediction, score, financial, content, investor-flow, and backtest requests have a lower independent limit. Limiter keys use a bounded LRU store with periodic stale-entry cleanup, so arbitrary client identifiers cannot grow process memory without bound. Docker trusts `X-Real-IP` only because the API port is loopback-bound and Nginx overwrites that header.

Public API limiting uses the bounded in-memory backend by default for dependency-free local
development. Set `RATE_LIMIT_BACKEND=redis` to use one atomic Redis sorted-set window across API
replicas. Client keys are SHA-256 hashed before storage, keys expire after the configured window,
and a Redis failure returns a generic fail-closed `503` response. The Docker Compose API defaults
to the Redis backend when the variable is not explicitly set.

Administrator API-key authentication has a separate failed-attempt lockout and returns
`Retry-After` on HTTP 429. With the Redis backend it shares the same distributed limiter across API
replicas, clears the caller's failure history after valid authentication, and fails closed when the
limiter is unavailable. Browser-facing Basic authentication is enforced by Next.js middleware and
remains process-local; a horizontally scaled external deployment still needs a distributed,
identity-aware login limiter or gateway.

The administrator BFF enforces a bounded upstream timeout and response size, validates JSON before
returning it to the browser, and replaces malformed or non-JSON upstream responses with a generic
same-origin error. Only request ID and rate-limit metadata are forwarded from the internal API.

Nginx routes `/api/admin/*` to the Next.js administrator BFF before the general `/api/*` FastAPI rule, limits administrator requests per client, and limits concurrent WebSocket connections per client. The Next.js middleware protects both `/admin/*` and `/api/admin/*` with HTTP Basic authentication when `ADMIN_UI_USERNAME` and `ADMIN_UI_PASSWORD` are configured. Production fails closed when either value is missing or the UI password is shorter than 16 characters.

## Administrator and account boundary

`ADMIN_API_KEY` is server-side only. After browser-level Basic authentication, the browser calls a same-origin Next.js BFF and never receives the backend key. Production account synchronization or automatic reference-alert evaluation requires an administrator key of at least 32 characters. This is an interim internal boundary; external multi-user deployment still requires JWT/OAuth, RBAC, user-scoped watchlists, ownership checks, and a distributed login-attempt limiter.

In production, any configured administrator key must contain at least 32 characters, persistence must use PostgreSQL, and active HTTP data providers must use HTTPS. Provider error metadata is treated as untrusted input: credential- and account-like fields are recursively redacted, collections and strings are bounded, and authentication errors use generic public messages.

No broker credential or full account number is stored in the database. Account synchronization is read-only and no order endpoint is exposed.

## Dependency and build integrity

- Python resolution is committed in `uv.lock`; Docker and CI use `uv sync --locked`.
- pnpm uses a frozen lockfile in CI. Dependency install scripts are denied by default, with only Next.js image optimization dependency `sharp` explicitly allowed.
- Next.js is pinned to 15.5.18 and React/React DOM to the 19.1.7 security backport. These versions address the official React Server Components advisory and the Next.js 15 security fixes, including the WebSocket-upgrade SSRF advisory.
- `postcss` is overridden to 8.5.10 or newer within the lockfile to address GHSA-qx2v-qp2m-jg93.
- Run `pnpm audit --prod` and `uv tool run pip-audit --path .venv/Lib/site-packages --skip-editable` during dependency-update reviews.
