from datetime import UTC, datetime
from decimal import Decimal

from fastapi.testclient import TestClient

from app.api.routes import get_candle_price_basis_inventory_service
from app.config import Settings, get_settings
from app.main import app
from app.providers.contracts import Candle
from app.repositories.memory import InMemoryCandleRepository
from app.services.candle_inventory import CandlePriceBasisInventoryService


def _candle(day: int, price_basis: str) -> Candle:
    value = Decimal(100 + day)
    return Candle(
        datetime(2026, 7, day, tzinfo=UTC),
        value,
        value,
        value,
        value,
        1000,
        price_basis,
    )


def _settings() -> Settings:
    return Settings(
        _env_file=None,
        admin_api_key="test-admin-secret",
        persistence_enabled=False,
        realtime_enabled=False,
        stock_provider="mock",
        financial_provider="mock",
        disclosure_provider="mock",
        news_provider="mock",
        investor_flow_provider="mock",
        ai_report_provider="mock",
    )


def test_inventory_reports_unknown_and_legacy_provenance_without_mutation():
    repository = InMemoryCandleRepository()
    repository.save_many(
        "005930",
        [_candle(1, "unknown"), _candle(2, "unknown")],
        interval="1d",
        stage="raw",
        aggregation_version="raw",
        source_provider="legacy_unknown",
        price_basis_rule_version="legacy_unknown",
    )
    repository.save_many(
        "AAPL",
        [_candle(3, "provider_adjusted")],
        interval="1d",
        stage="raw",
        aggregation_version="raw",
        source_provider="toss",
        price_basis_rule_version="toss-adjusted-v1",
    )

    result = CandlePriceBasisInventoryService(repository).summarize(
        symbol="005930", limit=10
    )

    assert result["symbol"] == "005930"
    assert result["total_candles"] == 2
    assert result["unknown_candles"] == 2
    assert result["legacy_unknown_candles"] == 2
    assert result["legacy_rule_candles"] == 2
    assert result["review_ready_groups"] == 0
    assert result["blocked_review_groups"] == 1
    assert result["items"][0]["review_status"] == "evidence_required"
    assert result["items"][0]["required_evidence"] == [
        "original_provider_identifier",
        "provider_response_or_contract_reference",
        "endpoint_adjustment_semantics",
        "provider_contract_test",
        "versioned_price_basis_rule",
    ]
    assert result["classification_blockers"] == [
        "unknown_price_basis_requires_source_specific_evidence",
        "legacy_rows_lack_provider_provenance",
        "legacy_rows_lack_price_basis_rule_version",
    ]
    assert result["automatic_relabel"] is False
    assert result["mutation_performed"] is False
    assert len(repository.find("005930", interval="1d", stage="raw", limit=10)) == 2


def test_inventory_symbol_filter_and_disabled_state():
    repository = InMemoryCandleRepository()
    repository.save_many(
        "AAPL",
        [_candle(3, "provider_adjusted")],
        interval="1d",
        stage="cleaned",
        aggregation_version="candle-pipeline-v1",
        source_provider="toss",
        price_basis_rule_version="toss-adjusted-v1",
    )

    filtered = CandlePriceBasisInventoryService(repository).summarize(symbol="AAPL", limit=10)
    disabled = CandlePriceBasisInventoryService(None).summarize(symbol="AAPL", limit=10)

    assert filtered["unknown_candles"] == 0
    assert filtered["classification_blockers"] == []
    assert filtered["items"][0]["source_provider"] == "toss"
    assert filtered["items"][0]["review_status"] == "evidence_recorded"
    assert filtered["items"][0]["required_evidence"] == []
    assert disabled["persistence_status"] == "disabled"
    assert disabled["mutation_performed"] is False


def test_candle_repository_rejects_missing_source_provenance():
    repository = InMemoryCandleRepository()

    try:
        repository.save_many(
            "AAPL",
            [_candle(3, "provider_adjusted")],
            interval="1d",
            stage="raw",
            aggregation_version="raw",
            source_provider="",
            price_basis_rule_version="toss-adjusted-v1",
        )
    except ValueError as exc:
        assert str(exc) == "Candle source provider must contain 1 to 32 characters"
    else:
        raise AssertionError("Missing source provenance must be rejected")


class _StubInventoryService:
    def summarize(self, **_: object) -> dict[str, object]:
        return {
            "persistence_status": "enabled",
            "symbol": "AAPL",
            "items": [],
            "total_candles": 0,
            "unknown_candles": 0,
            "legacy_unknown_candles": 0,
            "legacy_rule_candles": 0,
            "total_groups": 0,
            "review_ready_groups": 0,
            "blocked_review_groups": 0,
            "groups_truncated": False,
            "classification_blockers": [],
            "automatic_relabel": False,
            "mutation_performed": False,
        }


def test_inventory_endpoint_is_admin_only_and_validates_bounds():
    app.dependency_overrides[get_settings] = _settings
    app.dependency_overrides[get_candle_price_basis_inventory_service] = _StubInventoryService
    client = TestClient(app)
    headers = {"X-Admin-Key": "test-admin-secret"}
    try:
        unauthorized = client.get("/api/v1/admin/candles/price-basis-inventory")
        accepted = client.get(
            "/api/v1/admin/candles/price-basis-inventory?symbol=AAPL&limit=50",
            headers=headers,
        )
        invalid = client.get(
            "/api/v1/admin/candles/price-basis-inventory?limit=501",
            headers=headers,
        )
        missing_symbol = client.get(
            "/api/v1/admin/candles/price-basis-inventory?limit=50",
            headers=headers,
        )

        assert unauthorized.status_code == 401
        assert accepted.status_code == 200
        assert accepted.json()["data"]["automatic_relabel"] is False
        assert invalid.status_code == 422
        assert missing_symbol.status_code == 422
    finally:
        app.dependency_overrides.pop(get_settings, None)
        app.dependency_overrides.pop(get_candle_price_basis_inventory_service, None)
