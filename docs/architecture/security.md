# Security baseline

## Network boundary

Docker Compose binds API, web, PostgreSQL, Redis, Nginx, Prometheus, Alertmanager, and Grafana ports to `127.0.0.1`. They are not exposed to the local network by default. Production deployment still requires an HTTPS reverse proxy, firewall rules, secret manager, fixed egress IP, and non-default database and Grafana passwords.

The Next.js container runs an optimized production build with `next start`. Set `PUBLIC_API_URL` before building when the browser-facing API origin is not `http://localhost:8080`.

## HTTP and WebSocket controls

- FastAPI, Next.js, and Nginx add `nosniff`, frame-denial, referrer, and permissions-policy headers.
- Administrator, account, portfolio, watchlist, and alert responses use `Cache-Control: no-store, private`.
- `CORS_ORIGINS` is an explicit comma-separated allowlist.
- `ALLOWED_HOSTS` is a separate Host-header allowlist used by FastAPI and the Next.js administrator boundary. Production rejects the global `*` wildcard; deployment domains must be listed explicitly without schemes or ports.
- Compose also includes the internal `api` service name because the Next.js BFF and Prometheus call
  FastAPI over the private Docker network. External deployments must retain required private service
  names alongside their public domains.
- API responses use a deny-by-default CSP. The web application CSP blocks plugins, hostile base URLs, framing, and cross-origin form submission without weakening Next.js hydration requirements.
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

The browser calls market data through a same-origin, GET-only Next.js BFF. Its allowlist contains
only stock information, processed candles, quote, indicator, pattern and documented analysis paths;
it cannot reach arbitrary upstream URLs, administrator, account, portfolio or order endpoints.
Query names, response size, response type and upstream duration are bounded. When
`ANALYSIS_API_KEY` is configured, the BFF adds it server-side to costly report, prediction, score,
financial, news, disclosure, investor-flow and public backtest requests. The backend compares it in
constant time and returns a generic 401 without logging or echoing the secret. Production requires
at least 32 characters. Lower-cost quote/chart requests remain rate-limited without requiring the
key. This is an interim service-abuse boundary, not a user identity or authorization system.

Administrator API-key authentication has a separate failed-attempt lockout and returns
`Retry-After` on HTTP 429. With the Redis backend it shares the same distributed limiter across API
replicas, clears the caller's failure history after valid authentication, and fails closed when the
limiter is unavailable. Browser-facing Basic authentication is enforced by Next.js middleware and
remains process-local; a horizontally scaled external deployment still needs a distributed,
identity-aware login limiter or gateway.

The administrator BFF enforces a bounded upstream timeout and response size, validates JSON before
returning it to the browser, and replaces malformed or non-JSON upstream responses with a generic
same-origin error. Only request ID and rate-limit metadata are forwarded from the internal API.
All state-changing `/api/admin/*` requests must also carry an `Origin` exactly matching the
administrator application's origin. Missing or cross-origin values fail with HTTP 403, preventing
browser credential reuse from becoming a CSRF path. The rule remains active in local development
even when Basic authentication is intentionally unset. Server automation should call the backend
administrator API directly rather than bypass this browser-only BFF rule. Nginx preserves the
original Host port for web and BFF routes so origin comparison also works through local port 8080.

Nginx routes `/api/admin/*` to the Next.js administrator BFF before the general `/api/*` FastAPI rule, limits administrator requests per client, and limits concurrent WebSocket connections per client. The Next.js middleware protects both `/admin/*` and `/api/admin/*` with HTTP Basic authentication when `ADMIN_UI_USERNAME` and `ADMIN_UI_PASSWORD` are configured. Production fails closed when either value is missing or the UI password is shorter than 16 characters.

## Administrator and account boundary

`ADMIN_API_KEY` is server-side only. After browser-level Basic authentication, the browser calls a same-origin Next.js BFF and never receives the backend key. Production account synchronization or automatic reference-alert evaluation requires an administrator key of at least 32 characters. This is an interim internal boundary; external multi-user deployment still requires JWT/OAuth, RBAC, user-scoped watchlists, ownership checks, and a distributed login-attempt limiter.

In production, any configured administrator key must contain at least 32 characters, persistence must use PostgreSQL, and active HTTP data providers must use HTTPS. Provider error metadata is treated as untrusted input: credential- and account-like fields are recursively redacted, collections and strings are bounded, and authentication errors use generic public messages.

Selecting Toss, DART, KIS, or OpenAI now validates its required credentials while settings are
loaded, before any provider client is constructed. Whitespace-only secrets are rejected. KIS
streaming credentials are required only when the realtime feature is enabled, so an inactive source
selection remains safe for local configuration. Settings validation errors hide all input values to
prevent Pydantic exception output from disclosing secret fragments in startup logs. Production
persistence accepts only a PostgreSQL SQLAlchemy URL.

No broker credential or full account number is stored in the database. Account synchronization is read-only and no order endpoint is exposed.

## Dependency and build integrity

- Python resolution is committed in `uv.lock`; Docker and CI use `uv sync --locked`.
- The CI workflow has read-only repository permissions, disables persisted checkout credentials,
  cancels superseded runs, and pins every third-party GitHub Action to an immutable full commit SHA.
- CI rejects tracked environment files, credential-like files, database dumps, generated build
  directories, model artifacts, and files larger than 10 MiB without reading their contents.
- The backend and Next.js runtime images execute as dedicated non-root users. The optional model
  artifact directory is the only backend runtime write location and uses a dedicated Compose volume.
- pnpm uses a frozen lockfile in CI. Dependency install scripts are denied by default, with only Next.js image optimization dependency `sharp` explicitly allowed.
- CI runs a high-severity production pnpm audit. Dependabot checks GitHub Actions and pnpm workspace
  dependencies weekly; immutable Action SHAs must remain in place when accepting its updates.
- Next.js is pinned to 15.5.18 and React/React DOM to the 19.1.7 security backport. These versions address the official React Server Components advisory and the Next.js 15 security fixes, including the WebSocket-upgrade SSRF advisory.
- `postcss` is overridden to 8.5.10 or newer within the lockfile to address GHSA-qx2v-qp2m-jg93.
- Run `pnpm audit --prod` and `uv tool run pip-audit --path .venv/Lib/site-packages --skip-editable` during dependency-update reviews.

Run the lightweight repository admission check locally with:

```powershell
python scripts/check_repository_hygiene.py
git diff --check
```

The admission check is intentionally path-based. It complements GitHub secret scanning and a
deployment secret manager; it is not a content-based secret detector.

CI also treats `Settings`, Docker Compose interpolation variables, and `.env.example` as one
environment contract. It rejects missing, duplicate, stale, or malformed template entries and
requires credential-like template values to stay empty or use the literal `change-me` placeholder.
The check reads `.env.example` only and never opens the developer's local `.env` file. Run it with:

```powershell
python scripts/check_env_contract.py
```
