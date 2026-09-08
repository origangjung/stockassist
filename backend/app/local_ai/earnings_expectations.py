"""분기별 실제 EPS와 당시 예상 EPS를 제한적으로 조회하고 시점을 검증한다."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
import math
from urllib.parse import urlsplit

import httpx2

from app.local_ai.http_security import (
    DailyRequestBudget,
    bounded_json,
    validate_https_endpoint,
    validate_symbol,
)


MAX_EARNINGS_RESPONSE_BYTES = 2 * 1024 * 1024
ALLOWED_ALPHA_VANTAGE_HOSTS = frozenset({"www.alphavantage.co"})


@dataclass(frozen=True)
class EarningsExpectation:
    """발표 당시 실제 EPS와 애널리스트 예상 EPS의 구조화된 기록이다."""

    fiscal_date: date
    reported_date: date
    available_date: date
    reported_eps: float
    estimated_eps: float
    surprise: float
    surprise_percentage: float
    report_time: str


class AlphaVantageEarningsClient:
    """Alpha Vantage 무료 EARNINGS 응답을 일일 한도 안에서 조회한다."""

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str = "https://www.alphavantage.co/query",
        timeout_seconds: float = 30.0,
        daily_request_limit: int = 25,
        transport: httpx2.BaseTransport | None = None,
    ) -> None:
        if not api_key.strip():
            raise ValueError("Alpha Vantage API key is required")
        endpoint = validate_https_endpoint(base_url, name="ALPHA_VANTAGE_BASE_URL")
        if (urlsplit(endpoint).hostname or "").casefold() not in ALLOWED_ALPHA_VANTAGE_HOSTS:
            raise ValueError("Alpha Vantage host is not allowlisted")
        self._base_url = endpoint
        self._api_key = api_key.strip()
        self._http = httpx2.Client(timeout=timeout_seconds, transport=transport)
        self._budget = DailyRequestBudget(min(daily_request_limit, 25))

    def quarterly(
        self,
        symbol: str,
        *,
        as_of: date | None = None,
    ) -> list[EarningsExpectation]:
        """기준일에 이용 가능했던 분기 실적 예상치 기록만 반환한다."""

        normalized = validate_symbol(symbol)
        self._budget.consume(provider="AlphaVantage")
        response = self._http.get(
            self._base_url,
            params={
                "function": "EARNINGS",
                "symbol": normalized,
                "apikey": self._api_key,
            },
        )
        payload = bounded_json(
            response,
            provider="AlphaVantage",
            maximum_bytes=MAX_EARNINGS_RESPONSE_BYTES,
        )
        if not isinstance(payload, dict):
            raise ValueError("Alpha Vantage earnings response is not an object")
        if payload.get("Note") or payload.get("Information"):
            raise ValueError("Alpha Vantage limit or entitlement rejected the request")
        rows = payload.get("quarterlyEarnings")
        if not isinstance(rows, list):
            raise ValueError("Alpha Vantage response has no quarterly earnings")
        cutoff = as_of or date.today()
        parsed = [_parse_expectation(row) for row in rows if isinstance(row, dict)]
        return sorted(
            (item for item in parsed if item is not None and item.available_date <= cutoff),
            key=lambda item: (item.available_date, item.fiscal_date),
        )

    def close(self) -> None:
        """HTTP 연결 자원을 반환한다."""

        self._http.close()


def _parse_expectation(row: dict) -> EarningsExpectation | None:
    """불완전하거나 비유한 분기 기록을 제외하고 공개 가능일을 계산한다."""

    try:
        fiscal_date = date.fromisoformat(str(row["fiscalDateEnding"]))
        reported_date = date.fromisoformat(str(row["reportedDate"]))
        reported_eps = float(row["reportedEPS"])
        estimated_eps = float(row["estimatedEPS"])
        surprise = float(row["surprise"])
        surprise_percentage = float(row["surprisePercentage"])
    except (KeyError, TypeError, ValueError):
        return None
    values = (reported_eps, estimated_eps, surprise, surprise_percentage)
    if not all(math.isfinite(value) for value in values):
        return None
    report_time = str(row.get("reportTime") or "unknown").strip().casefold()
    available_date = (
        reported_date
        if report_time == "pre-market"
        else _next_business_day(reported_date)
    )
    return EarningsExpectation(
        fiscal_date=fiscal_date,
        reported_date=reported_date,
        available_date=available_date,
        reported_eps=reported_eps,
        estimated_eps=estimated_eps,
        surprise=surprise,
        surprise_percentage=surprise_percentage,
        report_time=report_time,
    )


def _next_business_day(value: date) -> date:
    """장 마감 후 발표를 다음 평일 전에는 사용할 수 없게 한다."""

    candidate = value + timedelta(days=1)
    while candidate.weekday() >= 5:
        candidate += timedelta(days=1)
    return candidate
