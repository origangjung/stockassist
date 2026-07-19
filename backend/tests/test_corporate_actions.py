from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.api.routes import get_corporate_action_service
from app.config import Settings, get_settings
from app.corporate_actions import (
    CorporateActionAdjustmentEngine,
    CorporateActionRecord,
    CorporateActionRevisionConflictError,
)
from app.database import Base, create_session_factory
from app.main import app
from app.models.market import StockModel
from app.providers.contracts import Candle
from app.repositories.corporate_action import SqlAlchemyCorporateActionRepository
from app.services.corporate_actions import CorporateActionService


def _action(
    *,
    revision: int = 1,
    known_at: datetime = datetime(2026, 1, 5, tzinfo=UTC),
    status: str = "confirmed",
    price_factor: str = "0.5",
) -> CorporateActionRecord:
    return CorporateActionRecord(
        symbol="005930",
        action_type="split",
        event_id="split-2026-01",
        revision=revision,
        effective_at=datetime(2026, 1, 10, tzinfo=UTC),
        announced_at=datetime(2026, 1, 4, tzinfo=UTC),
        known_at=known_at,
        price_factor=Decimal(price_factor),
        volume_factor=Decimal("2"),
        status=status,
        source="test",
        rule_version="corp-action-2026.1",
    )


def _candles() -> list[Candle]:
    return [
        Candle(
            datetime(2026, 1, 2, tzinfo=UTC),
            Decimal("100"),
            Decimal("120"),
            Decimal("90"),
            Decimal("110"),
            1000,
            "unadjusted",
        ),
        Candle(
            datetime(2026, 1, 12, tzinfo=UTC),
            Decimal("55"),
            Decimal("60"),
            Decimal("50"),
            Decimal("58"),
            2200,
            "unadjusted",
        ),
    ]


def test_adjustment_engine_creates_view_without_mutating_raw_candles():
    source = _candles()
    original = list(source)

    result = CorporateActionAdjustmentEngine().adjust(
        source,
        [_action()],
        as_of=datetime(2026, 1, 12, tzinfo=UTC),
    )

    assert source == original
    assert result.raw_candles_mutated is False
    assert result.adjustment_version == "2026.1"
    assert result.candles[0].open == Decimal("50.0")
    assert result.candles[0].close == Decimal("55.0")
    assert result.candles[0].volume == 2000
    assert result.candles[1] == replace(source[1], price_basis="point_in_time_adjusted")
    assert [(item.event_id, item.revision) for item in result.applied_actions] == [
        ("split-2026-01", 1)
    ]


def test_adjustment_engine_uses_latest_revision_known_at_the_requested_time():
    confirmed = _action()
    cancelled = _action(
        revision=2,
        known_at=datetime(2026, 1, 15, tzinfo=UTC),
        status="cancelled",
    )
    future_correction = _action(
        revision=3,
        known_at=datetime(2026, 1, 20, tzinfo=UTC),
        status="confirmed",
        price_factor="0.4",
    )
    engine = CorporateActionAdjustmentEngine()

    before_cancel = engine.adjust(
        _candles(),
        [confirmed, cancelled, future_correction],
        as_of=datetime(2026, 1, 12, tzinfo=UTC),
    )
    after_cancel = engine.adjust(
        _candles(),
        [confirmed, cancelled, future_correction],
        as_of=datetime(2026, 1, 16, tzinfo=UTC),
    )

    assert before_cancel.candles[0].open == Decimal("50.0")
    assert after_cancel.candles == [
        replace(candle, price_basis="point_in_time_adjusted") for candle in _candles()
    ]
    assert after_cancel.applied_actions == []


def test_adjustment_engine_rejects_naive_timestamps_and_invalid_factors():
    with pytest.raises(ValueError, match="timezone-aware"):
        CorporateActionAdjustmentEngine().adjust(
            _candles(),
            [_action()],
            as_of=datetime(2026, 1, 12),
        )
    with pytest.raises(ValueError, match="factors must be positive"):
        CorporateActionAdjustmentEngine().adjust(
            _candles(),
            [replace(_action(), price_factor=Decimal("0"))],
            as_of=datetime(2026, 1, 12, tzinfo=UTC),
        )


def test_adjustment_engine_rejects_provider_adjusted_candles():
    with pytest.raises(ValueError, match="explicitly unadjusted"):
        CorporateActionAdjustmentEngine().adjust(
            [replace(candle, price_basis="provider_adjusted") for candle in _candles()],
            [_action()],
            as_of=datetime(2026, 1, 12, tzinfo=UTC),
        )


def test_candle_rejects_unknown_price_basis_classification():
    with pytest.raises(ValueError, match="Unsupported candle price basis"):
        replace(_candles()[0], price_basis="ambiguous")


def test_repository_preserves_immutable_revisions_and_point_in_time_queries(tmp_path):
    sessions = create_session_factory(f"sqlite:///{tmp_path / 'actions.db'}")
    Base.metadata.create_all(sessions.kw["bind"])
    with sessions.begin() as session:
        session.add(StockModel(symbol="005930", name="Samsung", market="KOSPI"))
    repository = SqlAlchemyCorporateActionRepository(sessions)
    action = _action()

    repository.save(action)
    repository.save(action)

    assert repository.list_known(
        "005930", as_of=datetime(2026, 1, 4, tzinfo=UTC)
    ) == []
    known = repository.list_known(
        "005930", as_of=datetime(2026, 1, 6, tzinfo=UTC)
    )
    assert len(known) == 1
    assert known[0].recorded_at is not None
    items, total = repository.list_recent(limit=10, offset=0, symbol="005930")
    assert total == len(items) == 1

    with pytest.raises(CorporateActionRevisionConflictError):
        repository.save(replace(action, price_factor=Decimal("0.4")))


def test_service_reports_disabled_storage_and_requires_aware_as_of():
    service = CorporateActionService(None)
    result = service.recent(limit=25, offset=0)

    assert result["persistence_status"] == "disabled"
    assert result["application_mode"] == "preview_only"
    assert result["raw_candles_mutated"] is False
    with pytest.raises(ValueError, match="timezone-aware"):
        service.recent(limit=25, offset=0, as_of=datetime(2026, 1, 1))


class _StubCorporateActionService:
    def recent(self, **_: object) -> dict[str, object]:
        return {
            "persistence_status": "enabled",
            "items": [],
            "total": 0,
            "application_mode": "preview_only",
            "raw_candles_mutated": False,
        }


def test_corporate_action_endpoint_requires_admin_access():
    settings = Settings(_env_file=None, admin_api_key="test-admin-secret")
    service = _StubCorporateActionService()
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_corporate_action_service] = lambda: service
    client = TestClient(app)
    try:
        unauthorized = client.get("/api/v1/admin/corporate-actions")
        accepted = client.get(
            "/api/v1/admin/corporate-actions?symbol=005930",
            headers={"X-Admin-Key": "test-admin-secret"},
        )

        assert unauthorized.status_code == 401
        assert accepted.status_code == 200
        assert accepted.json()["data"]["raw_candles_mutated"] is False
    finally:
        app.dependency_overrides.pop(get_settings, None)
        app.dependency_overrides.pop(get_corporate_action_service, None)
