"""alerts 파일은 애플리케이션 사용 사례 기능을 담당한다."""

import logging
from dataclasses import asdict
from datetime import datetime, timezone
from decimal import Decimal

from app.adapters.broker import BrokerAdapter
from app.alerts import AlertCondition, AlertRepository
from app.providers.contracts import Capability

logger = logging.getLogger(__name__)


class ReferenceAlertService:
    """사용 사례의 처리 순서와 하위 의존성 호출을 조율하는 서비스입니다."""

    def __init__(self, broker: BrokerAdapter, repository: AlertRepository | None):
        """`__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다."""

        self._broker = broker
        self._repository = repository

    def watchlist(self) -> dict:
        """`watchlist`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        if self._repository is None:
            return {"persistence_status": "disabled", "items": []}
        return {
            "persistence_status": "enabled",
            "items": [asdict(item) for item in self._repository.list_watchlist()],
        }

    def add_watchlist(self, symbol: str) -> dict:
        """`add_watchlist`은(는) 데이터를 저장하거나 기존 상태에 추가합니다."""

        repository = self._required_repository()
        provider = self._broker.provider_for(Capability.QUOTE)
        stock = provider.get_stock_info(symbol)
        return {
            "provider": provider.name,
            "item": asdict(repository.add_watchlist(stock)),
        }

    def remove_watchlist(self, symbol: str) -> dict:
        """`remove_watchlist`은(는) 대상 데이터나 만료된 상태를 안전하게 제거합니다."""

        repository = self._required_repository()
        return {"symbol": symbol, "removed": repository.remove_watchlist(symbol)}

    def alerts(self, status: str | None = None) -> dict:
        """`alerts`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

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
        """`create_alert`은(는) 입력 값과 설정을 결합해 새 결과 객체를 생성합니다."""

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
        """`disable_alert`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        repository = self._required_repository()
        return {"alert_id": alert_id, "disabled": repository.disable_alert(alert_id)}

    def evaluate_active(self) -> dict:
        """`evaluate_active`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

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
        """`_required_repository`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        if self._repository is None:
            raise AlertPersistenceUnavailableError("Alert persistence is disabled")
        return self._repository


class AlertPersistenceUnavailableError(RuntimeError):
    """해당 실패 조건을 호출 계층에 구분해 전달하는 예외입니다."""

    pass
