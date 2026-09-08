"""client 파일은 외부 데이터 공급자 연동 기능을 담당한다."""

import time
from datetime import datetime, timezone
from time import perf_counter
from typing import Any, Callable

import httpx2

from app.core.request_context import current_request_id
from app.providers.audit import ProviderAuditSink
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
from app.providers.toss.audit import extract_provider_request_id, record_toss_audit
from app.providers.toss.auth import TossTokenManager
from app.providers.toss.rate_limit import TossRateLimiter


class TossApiClient:
    """외부 서비스의 인증·요청·응답 검증을 캡슐화하는 client입니다."""

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
        """`__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다."""

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
        """`get`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        return self.request("GET", path, group=group, params=params, account_seq=account_seq)

    def access_token(self) -> str:
        """서버 내부 WebSocket 연결이 REST와 같은 OAuth 토큰을 재사용하게 한다."""
        return self._tokens.get()

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
        """`request`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

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
            if response.status_code == 401 and not auth_retried:
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
        """`_record_audit`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        record_toss_audit(
            self._audit_sink,
            method=method,
            path=path,
            group=group,
            outcome=outcome,
            status_code=status_code,
            error_code=error_code,
            provider_request_id=provider_request_id,
            internal_request_id=internal_request_id,
            attempt_count=attempt_count,
            started_at=started_at,
            occurred_at=occurred_at,
        )

    def close(self) -> None:
        """`close`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        self._http.close()


def _json_object(response: httpx2.Response) -> dict[str, Any]:
    """`_json_object`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    try:
        payload = response.json()
    except ValueError as exc:
        raise ProviderUnavailableError("Toss returned a non-JSON response") from exc
    if not isinstance(payload, dict):
        raise ProviderUnavailableError("Toss returned an invalid response envelope")
    return payload


def _map_error(status_code: int, payload: dict[str, Any], headers: httpx2.Headers) -> ProviderError:
    """`_map_error`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    raw_error = payload.get("error")
    error = raw_error if isinstance(raw_error, dict) else {}
    # Upstream error codes are untrusted metadata.  Keep them out of public
    # responses, logs, and audit records; the HTTP status is sufficient for a
    # stable, provider-owned error category.
    code = f"toss-http-{status_code}"
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
    """`_extract_request_id`은(는) 원시 입력을 해석하고 필요한 값을 정규화해 추출합니다."""

    return extract_provider_request_id(payload, headers)
