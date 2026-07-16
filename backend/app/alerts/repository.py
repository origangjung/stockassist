from abc import ABC, abstractmethod
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, sessionmaker

from app.alerts.models import AlertCondition, PriceAlert, WatchlistItem
from app.models.alerts import PriceAlertModel, WatchlistModel
from app.providers.contracts import StockInfo


class AlertRepository(ABC):
    @abstractmethod
    def list_watchlist(self) -> list[WatchlistItem]: ...

    @abstractmethod
    def add_watchlist(self, stock: StockInfo) -> WatchlistItem: ...

    @abstractmethod
    def remove_watchlist(self, symbol: str) -> bool: ...

    @abstractmethod
    def list_alerts(self, *, status: str | None = None) -> list[PriceAlert]: ...

    @abstractmethod
    def create_alert(
        self, symbol: str, condition: AlertCondition, target_price: Decimal
    ) -> PriceAlert: ...

    @abstractmethod
    def disable_alert(self, alert_id: str) -> bool: ...

    @abstractmethod
    def record_evaluation(
        self,
        alert_id: str,
        *,
        price: Decimal,
        evaluated_at: datetime,
        triggered: bool,
    ) -> PriceAlert | None: ...


class SqlAlchemyAlertRepository(AlertRepository):
    def __init__(self, sessions: sessionmaker[Session]):
        self._sessions = sessions

    def list_watchlist(self) -> list[WatchlistItem]:
        query = select(WatchlistModel).order_by(WatchlistModel.created_at, WatchlistModel.symbol)
        with self._sessions() as session:
            return [self._watchlist_item(model) for model in session.scalars(query).all()]

    def add_watchlist(self, stock: StockInfo) -> WatchlistItem:
        with self._sessions.begin() as session:
            model = session.scalar(
                select(WatchlistModel).where(WatchlistModel.symbol == stock.symbol)
            )
            if model is None:
                model = WatchlistModel(
                    symbol=stock.symbol,
                    name=stock.name,
                    market=stock.market,
                    currency=stock.currency,
                )
                session.add(model)
                session.flush()
            return self._watchlist_item(model)

    def remove_watchlist(self, symbol: str) -> bool:
        with self._sessions.begin() as session:
            result = session.execute(delete(WatchlistModel).where(WatchlistModel.symbol == symbol))
            return bool(result.rowcount)

    def list_alerts(self, *, status: str | None = None) -> list[PriceAlert]:
        query = select(PriceAlertModel)
        if status:
            query = query.where(PriceAlertModel.status == status)
        query = query.order_by(PriceAlertModel.created_at.desc(), PriceAlertModel.id.desc())
        with self._sessions() as session:
            return [self._price_alert(model) for model in session.scalars(query).all()]

    def create_alert(
        self, symbol: str, condition: AlertCondition, target_price: Decimal
    ) -> PriceAlert:
        model = PriceAlertModel(
            symbol=symbol,
            condition=condition,
            target_price=target_price,
        )
        with self._sessions.begin() as session:
            session.add(model)
            session.flush()
            return self._price_alert(model)

    def disable_alert(self, alert_id: str) -> bool:
        with self._sessions.begin() as session:
            model = session.scalar(
                select(PriceAlertModel).where(PriceAlertModel.id == alert_id).with_for_update()
            )
            if model is None or model.status != "active":
                return False
            model.status = "disabled"
            return True

    def record_evaluation(
        self,
        alert_id: str,
        *,
        price: Decimal,
        evaluated_at: datetime,
        triggered: bool,
    ) -> PriceAlert | None:
        with self._sessions.begin() as session:
            model = session.scalar(
                select(PriceAlertModel).where(PriceAlertModel.id == alert_id).with_for_update()
            )
            if model is None or model.status != "active":
                return None
            model.last_price = price
            model.last_evaluated_at = evaluated_at
            if triggered:
                model.status = "triggered"
                model.triggered_at = evaluated_at
            session.flush()
            return self._price_alert(model)

    @staticmethod
    def _watchlist_item(model: WatchlistModel) -> WatchlistItem:
        return WatchlistItem(
            symbol=model.symbol,
            name=model.name,
            market=model.market,
            currency=model.currency,
            created_at=SqlAlchemyAlertRepository._utc(model.created_at),
        )

    @staticmethod
    def _price_alert(model: PriceAlertModel) -> PriceAlert:
        return PriceAlert(
            alert_id=model.id,
            symbol=model.symbol,
            condition=model.condition,
            target_price=model.target_price,
            status=model.status,
            created_at=SqlAlchemyAlertRepository._utc(model.created_at),
            last_price=model.last_price,
            last_evaluated_at=SqlAlchemyAlertRepository._utc(model.last_evaluated_at),
            triggered_at=SqlAlchemyAlertRepository._utc(model.triggered_at),
        )

    @staticmethod
    def _utc(value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


class InMemoryAlertRepository(AlertRepository):
    def __init__(self) -> None:
        self.watchlist: dict[str, WatchlistItem] = {}
        self.alerts: dict[str, PriceAlert] = {}

    def list_watchlist(self) -> list[WatchlistItem]:
        return sorted(self.watchlist.values(), key=lambda item: (item.created_at, item.symbol))

    def add_watchlist(self, stock: StockInfo) -> WatchlistItem:
        item = self.watchlist.get(stock.symbol)
        if item is None:
            item = WatchlistItem(
                stock.symbol,
                stock.name,
                stock.market,
                stock.currency,
                datetime.now(timezone.utc),
            )
            self.watchlist[stock.symbol] = item
        return item

    def remove_watchlist(self, symbol: str) -> bool:
        return self.watchlist.pop(symbol, None) is not None

    def list_alerts(self, *, status: str | None = None) -> list[PriceAlert]:
        items = self.alerts.values()
        if status:
            items = (item for item in items if item.status == status)
        return sorted(items, key=lambda item: item.created_at, reverse=True)

    def create_alert(
        self, symbol: str, condition: AlertCondition, target_price: Decimal
    ) -> PriceAlert:
        from uuid import uuid4

        item = PriceAlert(
            str(uuid4()), symbol, condition, target_price, "active", datetime.now(timezone.utc)
        )
        self.alerts[item.alert_id] = item
        return item

    def disable_alert(self, alert_id: str) -> bool:
        item = self.alerts.get(alert_id)
        if item is None or item.status != "active":
            return False
        self.alerts[alert_id] = PriceAlert(**{**item.__dict__, "status": "disabled"})
        return True

    def record_evaluation(
        self,
        alert_id: str,
        *,
        price: Decimal,
        evaluated_at: datetime,
        triggered: bool,
    ) -> PriceAlert | None:
        item = self.alerts.get(alert_id)
        if item is None or item.status != "active":
            return None
        updated = PriceAlert(
            **{
                **item.__dict__,
                "status": "triggered" if triggered else "active",
                "last_price": price,
                "last_evaluated_at": evaluated_at,
                "triggered_at": evaluated_at if triggered else None,
            }
        )
        self.alerts[alert_id] = updated
        return updated
