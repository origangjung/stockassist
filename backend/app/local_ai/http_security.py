"""http_security 파일은 직접 학습 AI 특성과 실행 기능을 담당한다."""

from __future__ import annotations

from datetime import date
import json
import re
from threading import Lock
from typing import Any
from urllib.parse import urlsplit


SYMBOL_PATTERN = re.compile(r"^[0-9A-Z.-]{1,16}$")


class DailyRequestBudget:
    """`DailyRequestBudget` 관련 상태와 동작을 하나의 객체로 묶습니다."""

    def __init__(self, maximum: int) -> None:
        """`__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다."""

        if maximum < 1:
            raise ValueError("daily request budget must be positive")
        self._maximum = maximum
        self._day = date.today()
        self._used = 0
        self._lock = Lock()

    def consume(self, *, provider: str) -> None:
        """`consume`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        with self._lock:
            today = date.today()
            if today != self._day:
                self._day = today
                self._used = 0
            if self._used >= self._maximum:
                raise ValueError(f"{provider} daily request budget exhausted")
            self._used += 1


def validate_symbol(symbol: str) -> str:
    """`validate_symbol`은(는) 입력 또는 현재 상태가 규칙을 만족하는지 검증합니다."""

    normalized = symbol.strip().upper()
    if not SYMBOL_PATTERN.fullmatch(normalized):
        raise ValueError("symbol contains unsupported characters")
    return normalized


def validate_https_endpoint(value: str, *, name: str) -> str:
    """`validate_https_endpoint`은(는) 입력 또는 현재 상태가 규칙을 만족하는지 검증합니다."""

    endpoint = value.strip().rstrip("/")
    parsed = urlsplit(endpoint)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError(f"{name} must be a credential-free HTTPS endpoint")
    return endpoint


def bounded_json(response: Any, *, provider: str, maximum_bytes: int) -> Any:
    """`bounded_json`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    status = int(response.status_code)
    if status < 200 or status >= 300:
        raise ValueError(f"{provider} request failed with HTTP {status}")
    declared = response.headers.get("content-length")
    if declared:
        try:
            if int(declared) > maximum_bytes:
                raise ValueError(f"{provider} response exceeds the size limit")
        except ValueError as exc:
            if "exceeds" in str(exc):
                raise
    content = bytes(response.content)
    if len(content) > maximum_bytes:
        raise ValueError(f"{provider} response exceeds the size limit")
    try:
        return json.loads(content)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"{provider} response is not valid JSON") from exc
