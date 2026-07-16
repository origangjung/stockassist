import re
from collections.abc import Mapping, Sequence
from typing import Any

_SENSITIVE_KEY = re.compile(
    r"(?:authorization|cookie|credential|password|secret|token|api[_-]?key|"
    r"client[_-]?id|account|resident|ssn)",
    re.IGNORECASE,
)
_BEARER_VALUE = re.compile(r"(?i)\bbearer\s+[a-z0-9._~+/-]+=*")
_ASSIGNED_SECRET = re.compile(
    r"(?i)\b(token|secret|password|api[_-]?key|client[_-]?id)\s*[:=]\s*[^\s,;&]+"
)

REDACTED = "[REDACTED]"


def sanitize_external_text(value: object, *, maximum: int = 500) -> str:
    """Return bounded external text with common credential forms removed."""

    text = _BEARER_VALUE.sub(f"Bearer {REDACTED}", str(value))
    text = _ASSIGNED_SECRET.sub(lambda match: f"{match.group(1)}={REDACTED}", text)
    return text if len(text) <= maximum else f"{text[:maximum]}…"


def sanitize_external_data(value: Any, *, depth: int = 0) -> Any:
    """Recursively sanitize untrusted provider error metadata for API responses."""

    if depth >= 5:
        return "[TRUNCATED]"
    if isinstance(value, Mapping):
        sanitized: dict[str, Any] = {}
        for index, (raw_key, item) in enumerate(value.items()):
            if index >= 30:
                sanitized["_truncated"] = True
                break
            key = sanitize_external_text(raw_key, maximum=100)
            sanitized[key] = (
                REDACTED
                if _SENSITIVE_KEY.search(key)
                else sanitize_external_data(item, depth=depth + 1)
            )
        return sanitized
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        items = list(value)
        sanitized_items = [sanitize_external_data(item, depth=depth + 1) for item in items[:20]]
        if len(items) > 20:
            sanitized_items.append("[TRUNCATED]")
        return sanitized_items
    if isinstance(value, str):
        return sanitize_external_text(value)
    if value is None or isinstance(value, (bool, int, float)):
        return value
    return sanitize_external_text(value)


def public_provider_error_message(exc: Exception) -> str:
    """Build a client-safe message for HTTP and realtime provider failures."""

    from app.providers.errors import ProviderAuthenticationError, ProviderForbiddenError

    if isinstance(exc, ProviderAuthenticationError):
        return "외부 데이터 제공자의 인증에 실패했습니다."
    if isinstance(exc, ProviderForbiddenError):
        return "외부 데이터 제공자가 요청을 거부했습니다."
    return sanitize_external_text(exc)
