from typing import Any

import sentry_sdk

from app.config import Settings

_SENSITIVE_HEADERS = {"authorization", "cookie", "set-cookie", "x-admin-key"}


def scrub_sensitive_data(event: dict[str, Any], _hint: dict[str, Any]) -> dict[str, Any]:
    request = event.get("request")
    if not isinstance(request, dict):
        return event
    headers = request.get("headers")
    if isinstance(headers, dict):
        request["headers"] = {
            key: "[Filtered]" if str(key).lower() in _SENSITIVE_HEADERS else value
            for key, value in headers.items()
        }
    request.pop("data", None)
    return event


def configure_sentry(settings: Settings) -> bool:
    configured = settings.sentry_dsn
    dsn = configured.get_secret_value() if configured else ""
    if not dsn:
        return False
    sentry_sdk.init(
        dsn=dsn,
        environment=settings.app_environment,
        release=settings.app_release,
        traces_sample_rate=settings.sentry_traces_sample_rate,
        send_default_pii=False,
        include_local_variables=False,
        max_request_body_size="never",
        before_send=scrub_sensitive_data,
    )
    return True
