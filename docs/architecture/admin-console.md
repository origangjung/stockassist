# Administrator Console

The administrator page is divided into four workspaces: operations, research and validation,
model management, and accounts and alerts. Only the selected workspace is mounted. Each panel is
also loaded through a separate Next.js dynamic import.

This boundary is operational, not only visual. Panels such as readiness status, data quality,
backtest history, model registry, watchlists, and broker accounts issue requests when mounted.
Keeping inactive workspaces unmounted prevents their polling and initial fetches from running in
the background. Switching tabs intentionally discards local form results and stops the previous
workspace's polling lifecycle.

The operations workspace is the initial tab because it provides the lowest-risk readiness view.
Administrator credentials remain inside the server-side BFF and are never included in browser
JavaScript or API responses. The tab interface uses `tablist`, `tab`, and `tabpanel` semantics and
supports responsive layouts without adding a UI dependency.

## BFF failure boundary

Administrator BFF requests abort after `ADMIN_PROXY_TIMEOUT_MS` (15 seconds by default). Request
bodies are limited to 64 KiB and upstream responses are streamed through a bounded reader controlled
by `ADMIN_PROXY_MAX_RESPONSE_BYTES` (2 MB by default). Non-JSON, malformed JSON, oversized, timeout,
and connection failures are converted to small same-origin JSON errors without reflecting the
upstream body.

The BFF forwards only operationally useful response headers: request ID, retry delay, and rate-limit
limit and remaining values. It does not forward cookies, authentication headers, or arbitrary
provider headers. Both proxy limits are explicitly passed into the Docker web container.
