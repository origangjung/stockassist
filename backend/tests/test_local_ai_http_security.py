import json

import pytest

from app.local_ai.http_security import (
    DailyRequestBudget,
    bounded_json,
    validate_https_endpoint,
    validate_symbol,
)


class _Response:
    def __init__(self, payload, *, status=200, declared_length=None):
        self.status_code = status
        self.content = json.dumps(payload).encode()
        self.headers = {}
        if declared_length is not None:
            self.headers["content-length"] = str(declared_length)


def test_local_ai_external_inputs_are_bounded_and_validated():
    assert validate_symbol(" aapl ") == "AAPL"
    assert validate_https_endpoint("https://api.example.com/", name="API") == (
        "https://api.example.com"
    )
    assert bounded_json(_Response({"ok": True}), provider="test", maximum_bytes=100)[
        "ok"
    ]

    with pytest.raises(ValueError):
        validate_symbol("AAPL?token=secret")
    with pytest.raises(ValueError, match="HTTPS"):
        validate_https_endpoint("http://api.example.com", name="API")
    with pytest.raises(ValueError, match="size limit"):
        bounded_json(
            _Response({"ok": True}, declared_length=1000),
            provider="test",
            maximum_bytes=100,
        )
    with pytest.raises(ValueError, match="HTTP 401"):
        bounded_json(_Response({}, status=401), provider="test", maximum_bytes=100)


def test_daily_request_budget_fails_closed_at_the_configured_limit():
    budget = DailyRequestBudget(2)

    budget.consume(provider="NewsAPI")
    budget.consume(provider="NewsAPI")

    with pytest.raises(ValueError, match="daily request budget exhausted"):
        budget.consume(provider="NewsAPI")
