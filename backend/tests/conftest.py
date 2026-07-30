"""Keep the test suite deterministic and independent from developer secrets."""

import os

import pytest

from app.api.admin import reset_admin_rate_limiter


os.environ.update(
    {
        "PERSISTENCE_ENABLED": "false",
        "REFERENCE_ALERTS_ENABLED": "false",
        "STOCK_PROVIDER": "mock",
        "FINANCIAL_PROVIDER": "mock",
        "DISCLOSURE_PROVIDER": "mock",
        "NEWS_PROVIDER": "mock",
        "INVESTOR_FLOW_PROVIDER": "mock",
        "PREDICTION_ENGINE": "lightweight",
        "AI_REPORT_PROVIDER": "mock",
        "ACCOUNT_SYNC_ENABLED": "true",
        "REALTIME_ENABLED": "false",
        "SCHEDULER_ENABLED": "false",
        "ADMIN_API_KEY": "test-admin-secret",
    }
)


@pytest.fixture(autouse=True)
def _reset_admin_attempts():
    reset_admin_rate_limiter()
    yield
    reset_admin_rate_limiter()
