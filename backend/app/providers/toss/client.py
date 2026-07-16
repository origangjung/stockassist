import time
from datetime import datetime, timezone
from time import perf_counter
from typing import Any, Callable

import httpx2
import structlog

from app.core.request_context import current_request_id
from app.providers.audit import ProviderAuditEvent, ProviderAuditSink
from app.providers.errors import (
    ProviderAuthenticationError,
    ProviderConflictError,
    ProviderError,
    ProviderForbiddenError,
    ProviderNotFoundError,
    ProviderRateLimitError,
    ProviderUnavailableError,
    ProviderValidationError,
)
from app.providers.toss.auth import TossTokenManager
from app.providers.toss.rate_limit import TossRateLimiter

logger = structlog.get_logger(__name__)


class TossApiClient:
    def __init__(
        self,
        http: httpx2.Client,
        tokens: TossTokenManager,
        limiter: TossRateLimiter,
        *,
        max_retries: int = 3,
        sleep: Callable[[float], None] = time.sleep,
        audit_sink: ProviderAuditSink | None = None,
    ) -> None:
        self._http = http
        self._tokens = tokens
        self._limiter = limiter
        self._max_retries = max_retries
        self._sleep = sleep
        self._audit_sink = audit_sink

    def get(
        self,
        path: str,
        *,
        group: str,
        params: dict[str, Any] | None = None,
        account_seq: int | None = None,
    ) -> dict[str, Any]:
        return self.request("GET", path, group=group, params=params, account_seq=account_seq)

    def request(
        self,
        method: str,
        path: str,
        *,
        group: str,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        account_seq: int | None = None,
    ) -> dict[str, Any]:
        started_at = perf_counter()
        occurred_at = datetime.now(timezone.utc)
        internal_request_id = current_request_id()
        auth_retried = False
        attempt = 0
        request_count = 0
        while True:
            self._limiter.acquire(group)
            token = self._tokens.get()
            headers = {"Authorization": f"Bearer {token}"}
            if account_seq is not None:
                headers["X-Tossinvest-Account"] = str(account_seq)
            try:
                request_count += 1
                response = self._http.request(
                    method, path, params=params, json=json, headers=headers
                )
            except httpx2.RequestError as exc:
                if attempt < self._max_retries:
                    self._sleep(float(2**attempt))
                    attempt += 1
                    continue
                self._record_audit(
                    method=method,
                    path=path,
                    group=group,
                    outcome="transport_error",
                    status_code=None,
                    error_code="provider-unavailable",
                    provider_request_id=None,
                    internal_request_id=internal_request_id,
                    attempt_count=request_count,
                    started_at=started_at,
                    occurred_at=occurred_at,
                )
                raise ProviderUnavailableError("Toss API is unavailable") from exc
            self._limiter.observe(group, response.headers)
            try:
                payload = _json_object(response)
            except ProviderError as exc:
                self._record_audit(
                    method=method,
                    path=path,
                    group=group,
                    outcome="error",
                    status_code=response.status_code,
                    error_code=exc.code,
                    provider_request_id=_extract_request_id({}, response.headers),
                    internal_request_id=internal_request_id,
                    attempt_count=request_count,
                    started_at=started_at,
                    occurred_at=occurred_at,
                )
                raise
            error = payload.get("error") if isinstance(payload.get("error"), dict) else {}
            code = str(error.get("code") or "")
            if response.status_code == 401 and code == "expired-token" and not auth_retried:
                self._tokens.invalidate(token)
                auth_retried = True
                continue
            if response.status_code == 429 and attempt < self._max_retries:
                delay = self._limiter.retry_delay(attempt, response.headers.get("Retry-After"))
                self._sleep(delay)
                attempt += 1
                continue
            if response.status_code >= 400:
                mapped = _map_error(response.status_code, payload, response.headers)
                self._record_audit(
                    method=method,
                    path=path,
                    group=group,
                    outcome="error",
                    status_code=response.status_code,
                    error_code=mapped.code,
                    provider_request_id=mapped.request_id,
                    internal_request_id=internal_request_id,
                    attempt_count=request_count,
                    started_at=started_at,
                    occurred_at=occurred_at,
                )
                raise mapped
            self._record_audit(
                method=method,
                path=path,
                group=group,
                outcome="success",
                status_code=response.status_code,
                error_code=None,
                provider_request_id=_extract_request_id(payload, response.headers),
                internal_request_id=internal_request_id,
                attempt_count=request_count,
                started_at=started_at,
                occurred_at=occurred_at,
            )
            return payload

    def _record_audit(
        self,
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
        if self._audit_sink is None:
            return
        event = ProviderAuditEvent(
            provider="toss",
            method=method.upper()[:8],
            endpoint=path.partition("?")[0][:255],
            api_group=group[:64],
            outcome=outcome,
            status_code=status_code,
            error_code=_bounded_text(error_code),
            provider_request_id=_bounded_text(provider_request_id),
            internal_request_id=_bounded_text(internal_request_id) or "unknown",
            attempt_count=max(attempt_count, 1),
            duration_ms=max(round((perf_counter() - started_at) * 1000, 3), 0),
            occurred_at=occurred_at,
        )
        try:
            self._audit_sink.save(event)
        except Exception:
            logger.exception(
                "provider_audit_save_failed",
                provider="toss",
                endpoint=event.endpoint,
                outcome=event.outcome,
                attempt_count=event.attempt_count,
            )

    def close(self) -> None:
        self._http.close()


def _json_object(response: httpx2.Response) -> dict[str, Any]:
    try:
        payload = response.json()
    except ValueError as exc:
        raise ProviderUnavailableError("Toss returned a non-JSON response") from exc
    if not isinstance(payload, dict):
        raise ProviderUnavailableError("Toss returned an invalid response envelope")
    return payload


def _map_error(status_code: int, payload: dict[str, Any], headers: httpx2.Headers) -> ProviderError:
    raw_error = payload.get("error")
    error = raw_error if isinstance(raw_error, dict) else {}
    code = str(error.get("code") or f"http-{status_code}")
    message = str(error.get("message") or "Toss API request failed")
    request_id = _extract_request_id(payload, headers)
    data = error.get("data") if isinstance(error.get("data"), dict) else None
    kwargs = {
        "code": code,
        "request_id": request_id,
        "data": data,
        "status_code": status_code,
    }
    if status_code == 401:
        return ProviderAuthenticationError(message, **kwargs)
    if status_code == 403:
        return ProviderForbiddenError(message, **kwargs)
    if status_code == 404:
        return ProviderNotFoundError(message, **kwargs)
    if status_code == 409:
        return ProviderConflictError(message, **kwargs)
    if status_code == 422:
        return ProviderValidationError(message, **kwargs)
    if status_code == 429:
        return ProviderRateLimitError(message, **kwargs)
    if status_code >= 500:
        return ProviderUnavailableError(message, **kwargs)
    return ProviderError(message, **kwargs)


def _extract_request_id(payload: dict[str, Any], headers: httpx2.Headers) -> str | None:
    raw_error = payload.get("error")
    error = raw_error if isinstance(raw_error, dict) else {}
    value = (
        error.get("requestId")
        or payload.get("requestId")
        or headers.get("X-Request-Id")
        or headers.get("x-amz-cf-id")
    )
    return _bounded_text(None if value is None else str(value))


def _bounded_text(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = "".join(character for character in str(value) if character.isprintable()).strip()
    return cleaned[:128] or None
