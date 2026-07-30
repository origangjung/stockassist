from datetime import datetime
from time import perf_counter
from typing import Any, Mapping

import structlog

from app.providers.audit import ProviderAuditEvent, ProviderAuditSink


logger = structlog.get_logger(__name__)


def record_toss_audit(
    audit_sink: ProviderAuditSink | None,
    *,
    method: str,
    path: str,
    group: str,
    outcome: str,
    status_code: int | None,
    error_code: str | None,
    provider_request_id: str | None,
    internal_request_id: str,
    attempt_count: int,
    started_at: float,
    occurred_at: datetime,
) -> None:
    """Save metadata-only telemetry without allowing audit storage to block a provider call.

    Callers must pass an endpoint path, not a full URL, and never supply a request body,
    query string, credential, token, account identifier, or response payload.
    """
    if audit_sink is None:
        return
    event = ProviderAuditEvent(
        provider="toss",
        method=method.upper()[:8],
        endpoint=path.partition("?")[0][:255],
        api_group=group[:64],
        outcome=outcome,
        status_code=status_code,
        error_code=bounded_text(error_code),
        provider_request_id=bounded_text(provider_request_id),
        internal_request_id=bounded_text(internal_request_id) or "unknown",
        attempt_count=max(attempt_count, 1),
        duration_ms=max(round((perf_counter() - started_at) * 1000, 3), 0),
        occurred_at=occurred_at,
    )
    try:
        audit_sink.save(event)
    except Exception as exc:
        # Avoid serializing a storage exception: driver messages can include connection details.
        logger.warning(
            "provider_audit_save_failed",
            provider="toss",
            endpoint=event.endpoint,
            outcome=event.outcome,
            attempt_count=event.attempt_count,
            error_type=type(exc).__name__,
        )


def extract_provider_request_id(
    payload: Mapping[str, Any], headers: Mapping[str, str]
) -> str | None:
    raw_error = payload.get("error")
    error = raw_error if isinstance(raw_error, Mapping) else {}
    value = (
        error.get("requestId")
        or payload.get("requestId")
        or headers.get("X-Request-Id")
        or headers.get("x-amz-cf-id")
    )
    return bounded_text(None if value is None else str(value))


def bounded_text(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = "".join(character for character in str(value) if character.isprintable()).strip()
    return cleaned[:128] or None
