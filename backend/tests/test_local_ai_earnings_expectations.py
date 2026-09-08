from datetime import date

import httpx2
import pytest

from app.local_ai.earnings_expectations import AlphaVantageEarningsClient


def test_earnings_client_parses_point_in_time_quarters_and_filters_future_rows():
    requests = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        requests.append(request)
        return httpx2.Response(
            200,
            json={
                "quarterlyEarnings": [
                    {
                        "fiscalDateEnding": "2026-03-31",
                        "reportedDate": "2026-04-24",
                        "reportedEPS": "1.20",
                        "estimatedEPS": "1.00",
                        "surprise": "0.20",
                        "surprisePercentage": "20.0",
                        "reportTime": "post-market",
                    },
                    {
                        "fiscalDateEnding": "2026-06-30",
                        "reportedDate": "2026-07-22",
                        "reportedEPS": "1.30",
                        "estimatedEPS": "1.10",
                        "surprise": "0.20",
                        "surprisePercentage": "18.18",
                        "reportTime": "pre-market",
                    },
                ]
            },
        )

    client = AlphaVantageEarningsClient(
        api_key="test-key",
        transport=httpx2.MockTransport(handler),
    )
    try:
        rows = client.quarterly("aapl", as_of=date(2026, 4, 27))
    finally:
        client.close()

    assert len(requests) == 1
    assert requests[0].url.params["apikey"] == "test-key"
    assert requests[0].url.params["symbol"] == "AAPL"
    assert len(rows) == 1
    assert rows[0].available_date == date(2026, 4, 27)
    assert rows[0].surprise_percentage == 20.0


def test_earnings_client_rejects_provider_limit_messages():
    client = AlphaVantageEarningsClient(
        api_key="test-key",
        transport=httpx2.MockTransport(
            lambda _request: httpx2.Response(200, json={"Note": "limit reached"})
        ),
    )
    try:
        with pytest.raises(ValueError, match="limit or entitlement"):
            client.quarterly("AAPL")
    finally:
        client.close()


def test_earnings_client_rejects_unapproved_hosts_and_empty_keys():
    with pytest.raises(ValueError, match="API key"):
        AlphaVantageEarningsClient(api_key="")
    with pytest.raises(ValueError, match="allowlisted"):
        AlphaVantageEarningsClient(
            api_key="test-key",
            base_url="https://example.com/query",
        )
