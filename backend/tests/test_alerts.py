from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError

from app.adapters.broker import BrokerAdapter
from app.alerts import InMemoryAlertRepository, SqlAlchemyAlertRepository
from app.config import Settings
from app.database import Base, create_session_factory
from app.providers.mock import MockProvider
from app.services.alerts import (
    AlertPersistenceUnavailableError,
    ReferenceAlertService,
)
from app.scheduler import build_scheduler


def test_watchlist_and_one_shot_reference_alerts():
    provider = MockProvider()
    repository = InMemoryAlertRepository()
    service = ReferenceAlertService(BrokerAdapter([provider]), repository)

    first = service.add_watchlist("005930")["item"]
    duplicate = service.add_watchlist("005930")["item"]
    assert first["symbol"] == "005930"
    assert duplicate == first
    assert len(service.watchlist()["items"]) == 1

    quote = provider.get_quote("005930")
    reached = service.create_alert("005930", "above", quote.price)
    pending = service.create_alert("005930", "below", quote.price - Decimal("1"))
    assert reached["execution_enabled"] is False
    assert pending["is_investment_advice"] is False

    result = service.evaluate_active()
    assert result["evaluated"] == 2
    assert len(result["triggered"]) == 1
    assert result["triggered"][0]["alert_id"] == reached["alert"]["alert_id"]
    assert result["execution_enabled"] is False

    second_result = service.evaluate_active()
    assert second_result["evaluated"] == 1
    assert second_result["triggered"] == []
    assert service.disable_alert(pending["alert"]["alert_id"])["disabled"] is True
    assert service.remove_watchlist("005930")["removed"] is True


def test_alert_persistence_disabled_and_settings_dependency():
    service = ReferenceAlertService(BrokerAdapter([MockProvider()]), None)
    assert service.watchlist() == {"persistence_status": "disabled", "items": []}
    with pytest.raises(AlertPersistenceUnavailableError):
        service.create_alert("005930", "above", Decimal("75000"))
    with pytest.raises(ValueError, match="PERSISTENCE_ENABLED"):
        Settings(
            _env_file=None,
            persistence_enabled=False,
            reference_alerts_enabled=True,
        )


def test_sqlalchemy_alert_repository_round_trip(tmp_path):
    sessions = create_session_factory(f"sqlite:///{tmp_path / 'alerts.db'}")
    Base.metadata.create_all(sessions.kw["bind"])
    provider = MockProvider()
    repository = SqlAlchemyAlertRepository(sessions)

    item = repository.add_watchlist(provider.get_stock_info("AAPL"))
    assert item.currency == "USD"
    assert repository.add_watchlist(provider.get_stock_info("AAPL")) == item
    assert len(repository.list_watchlist()) == 1

    alert = repository.create_alert("AAPL", "above", Decimal("220.00"))
    assert alert.status == "active"
    assert repository.disable_alert(alert.alert_id) is True
    assert repository.disable_alert(alert.alert_id) is False
    assert repository.list_alerts(status="disabled")[0].alert_id == alert.alert_id
    with pytest.raises(IntegrityError):
        repository.create_alert("AAPL", "above", Decimal("-1"))


def test_reference_alert_scheduler_can_run_without_candle_jobs(tmp_path):
    settings = Settings(
        _env_file=None,
        database_url=f"sqlite:///{tmp_path / 'scheduler.db'}",
        persistence_enabled=True,
        scheduler_enabled=False,
        reference_alerts_enabled=True,
        reference_alert_interval_seconds=15,
    )
    scheduler = build_scheduler(settings, BrokerAdapter([MockProvider()]))

    assert [job.id for job in scheduler.get_jobs()] == ["reference-price-alerts"]
    assert scheduler.get_job("reference-price-alerts").trigger.interval.total_seconds() == 15
