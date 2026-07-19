# Observability and health checks

## Health endpoints

- `GET /health` keeps the original compatibility response.
- `GET /health/live` reports that the API process can serve requests.
- `GET /health/ready` checks only dependencies required by enabled features.

PostgreSQL is required when `PERSISTENCE_ENABLED=true`; Redis is required when
`REALTIME_ENABLED=true` or `RATE_LIMIT_BACKEND=redis`. Disabled dependencies are reported as
`disabled` and do not make the API unready. Each required probe has a bounded timeout. Responses
expose only the exception type, not connection strings or provider secrets.

The authenticated `GET /api/v1/admin/operations/status` endpoint reuses these probes and adds a
safe runtime summary for the operations dashboard. It reports active provider names, enabled
features and realtime capacity without returning credentials or endpoint URLs. The feature list
also indicates whether distributed Redis request limiting is active.

When distributed limiting is active, the same Redis dependency protects both public request limits
and administrator API-key failure lockouts. A Redis outage therefore makes readiness fail and
returns bounded `503` responses instead of silently falling back to per-process counters.

The API container uses readiness for its Docker health check. The web container waits for the API
to become healthy before starting.

## Prometheus metrics

The API mounts the official Prometheus Python ASGI exporter at `/metrics/` when
`METRICS_ENABLED=true`. It records request count, request duration, in-progress requests and the
latest dependency readiness state. Route templates are used as labels to avoid symbol or run-ID
cardinality growth.

The Nginx public gateway does not proxy `/metrics`; Prometheus scrapes it over the internal Compose
network.

## Structured logs and Sentry

`LOG_FORMAT=json` configures structlog and standard-library logs to use one JSON format. Completed
request logs include the request ID, route template, method, status and duration. Request bodies,
query values, authorization credentials and administrator keys are not logged.

Sentry is disabled when `SENTRY_DSN` is empty. When enabled, the integration keeps
`send_default_pii=false`, never sends request bodies or local variables, and filters authorization,
cookie and administrator-key headers. `SENTRY_TRACES_SAMPLE_RATE` defaults to zero so performance
tracing must be explicitly enabled.

Prometheus loads `alert_rules.yml`, which detects an unavailable API, a required dependency outage,
a five-minute 5xx ratio above 5%, and sustained p95 latency above two seconds. Notification routing
still requires an Alertmanager destination appropriate for the deployment environment.

## Alertmanager routing

The monitoring profile includes Alertmanager on port 9093. Prometheus forwards firing and resolved
alerts over the internal Compose network. The default `stockpilot-local` receiver has no outbound
integration, so alerts remain visible in the Alertmanager UI without sending messages.

Alertmanager groups alerts by service, name and severity. Critical alerts repeat hourly, other
alerts repeat every four hours, and an API-unavailable critical alert suppresses secondary latency
and 5xx warnings for the same service.

To enable Slack without committing a webhook:

1. Copy `alertmanager.slack.example.yml` to the ignored `alertmanager.local.yml` file.
2. Create an ignored `infrastructure/monitoring/secrets/slack_webhook_url` file containing only the
   webhook URL.
3. Set `ALERTMANAGER_CONFIG_PATH=./infrastructure/monitoring/alertmanager.local.yml` and
   `ALERTMANAGER_SECRETS_PATH=./infrastructure/monitoring/secrets`.
4. Update the Slack channel in the local configuration and restart the monitoring profile.

No external notification is sent until those explicit local settings are provided. Production
deployments should store the webhook in their platform secret manager rather than a filesystem.

## Local monitoring stack

Start the optional monitoring profile with:

```powershell
docker compose --profile monitoring up --build
```

Prometheus is available on port 9090, Alertmanager on port 9093 and Grafana on port 3001. Grafana provisions the Prometheus
data source and the `StockPilot API Operations` dashboard automatically. Set a strong
`GRAFANA_ADMIN_PASSWORD` before starting the profile outside an isolated local machine.

## Provider audit retention

External provider audit rows have an independent lifecycle. Set
`PROVIDER_AUDIT_CLEANUP_ENABLED=true` with persistence enabled to delete rows older than
`PROVIDER_AUDIT_RETENTION_DAYS` once per day. The default retention is 90 days, the accepted range
is 7–3650 days, and `PROVIDER_AUDIT_CLEANUP_HOUR_KST` selects the KST hour; the job runs at minute
15. It also runs once when the scheduler starts so an overdue backlog does not wait until the next
daily window.

The maintenance service records only its last run, cutoff, deleted count and exception type for
the authenticated operations status response. Database exception messages are not returned. A
cleanup failure is logged and reported as `failed`, but does not stop API startup, scheduled market
data ingestion or provider requests. Both automatic and manual cleanup are bounded to the
`provider_audit_logs` table and the configured retention cutoff.
