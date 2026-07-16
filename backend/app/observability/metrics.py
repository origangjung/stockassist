from time import perf_counter

from prometheus_client import Counter, Gauge, Histogram, make_asgi_app
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

HTTP_REQUESTS = Counter(
    "stockpilot_http_requests_total",
    "Total HTTP requests processed by the API.",
    ("method", "route", "status"),
)
HTTP_DURATION = Histogram(
    "stockpilot_http_request_duration_seconds",
    "HTTP request latency in seconds.",
    ("method", "route"),
)
HTTP_IN_PROGRESS = Gauge(
    "stockpilot_http_requests_in_progress",
    "HTTP requests currently being processed.",
    ("method",),
)
DEPENDENCY_READY = Gauge(
    "stockpilot_dependency_ready",
    "Whether a configured dependency passed its latest readiness check.",
    ("dependency",),
)


def metrics_app():
    return make_asgi_app()


def record_dependency(name: str, ready: bool) -> None:
    DEPENDENCY_READY.labels(dependency=name).set(1 if ready else 0)


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        method = request.method
        started_at = perf_counter()
        status_code = 500
        HTTP_IN_PROGRESS.labels(method=method).inc()
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            route_object = request.scope.get("route")
            route = getattr(route_object, "path", "unmatched")
            elapsed = perf_counter() - started_at
            HTTP_IN_PROGRESS.labels(method=method).dec()
            HTTP_REQUESTS.labels(
                method=method,
                route=route,
                status=str(status_code),
            ).inc()
            HTTP_DURATION.labels(method=method, route=route).observe(elapsed)
