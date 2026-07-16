import logging
from dataclasses import asdict
from datetime import datetime, timezone
from decimal import Decimal

from app.adapters.broker import BrokerAdapter
from app.alerts import AlertCondition, AlertRepository
from app.providers.contracts import Capability

logger = logging.getLogger(__name__)


class ReferenceAlertService:
    def __init__(self, broker: BrokerAdapter, repository: AlertRepository | None):
        self._broker = broker
        self._repository = repository

    def watchlist(self) -> dict:
        if self._repository is None:
            return {"persistence_status": "disabled", "items": []}
        return {
            "persistence_status": "enabled",
            "items": [asdict(item) for item in self._repository.list_watchlist()],
        }

    def add_watchlist(self, symbol: str) -> dict:
        repository = self._required_repository()
        provider = self._broker.provider_for(Capability.QUOTE)
        stock = provider.get_stock_info(symbol)
        return {
            "provider": provider.name,
            "item": asdict(repository.add_watchlist(stock)),
        }

    def remove_watchlist(self, symbol: str) -> dict:
        repository = self._required_repository()
        return {"symbol": symbol, "removed": repository.remove_watchlist(symbol)}

    def alerts(self, status: str | None = None) -> dict:
        if self._repository is None:
            return {"persistence_status": "disabled", "items": []}
        return {
            "persistence_status": "enabled",
            "items": [asdict(item) for item in self._repository.list_alerts(status=status)],
        }

    def create_alert(
        self,
        symbol: str,
        condition: AlertCondition,
        target_price: Decimal,
    ) -> dict:
        if target_price <= 0:
            raise ValueError("target_price must be positive")
        repository = self._required_repository()
        provider = self._broker.provider_for(Capability.QUOTE)
        provider.get_stock_info(symbol)
        alert = repository.create_alert(symbol, condition, target_price)
        return {
            "provider": provider.name,
            "alert": asdict(alert),
            "is_investment_advice": False,
            "execution_enabled": False,
        }

    def disable_alert(self, alert_id: str) -> dict:
        repository = self._required_repository()
        return {"alert_id": alert_id, "disabled": repository.disable_alert(alert_id)}

    def evaluate_active(self) -> dict:
        repository = self._required_repository()
        active = repository.list_alerts(status="active")
        provider = self._broker.provider_for(Capability.QUOTE)
        quotes = {}
        failures: list[dict[str, str]] = []
        for symbol in dict.fromkeys(alert.symbol for alert in active):
            try:
                quotes[symbol] = provider.get_quote(symbol)
            except Exception as exc:
                logger.warning(
                    "Reference alert quote failed symbol=%s error_type=%s",
                    symbol,
                    type(exc).__name__,
                )
                failures.append({"symbol": symbol, "error_type": type(exc).__name__})

        evaluated = 0
        triggered = []
        now = datetime.now(timezone.utc)
        for alert in active:
            quote = quotes.get(alert.symbol)
            if quote is None:
                continue
            is_triggered = (
                quote.price >= alert.target_price
                if alert.condition == "above"
                else quote.price <= alert.target_price
            )
            updated = repository.record_evaluation(
                alert.alert_id,
                price=quote.price,
                evaluated_at=quote.as_of or now,
                triggered=is_triggered,
            )
            if updated is None:
                continue
            evaluated += 1
            if is_triggered:
                triggered.append(asdict(updated))
        return {
            "provider": provider.name,
            "evaluated": evaluated,
            "triggered": triggered,
            "failures": failures,
            "execution_enabled": False,
            "is_investment_advice": False,
        }

    def _required_repository(self) -> AlertRepository:
        if self._repository is None:
            raise AlertPersistenceUnavailableError("Alert persistence is disabled")
        return self._repository


class AlertPersistenceUnavailableError(RuntimeError):
    pass
