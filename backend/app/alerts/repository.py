"""repository 파일은 백엔드 도메인 기능을 담당한다."""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, sessionmaker

from app.alerts.models import AlertCondition, PriceAlert, WatchlistItem
from app.models.alerts import PriceAlertModel, WatchlistModel
from app.providers.contracts import StockInfo


class AlertRepository(ABC):
    """`AlertRepository` 구현체가 제공해야 하는 메서드 계약을 정의합니다."""

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
    """도메인 객체의 저장·조회 방식을 캡슐화하는 저장소입니다."""

    def __init__(self, sessions: sessionmaker[Session]):
        """`__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다."""

        self._sessions = sessions

    def list_watchlist(self) -> list[WatchlistItem]:
        """`list_watchlist`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        query = select(WatchlistModel).order_by(WatchlistModel.created_at, WatchlistModel.symbol)
        with self._sessions() as session:
            return [self._watchlist_item(model) for model in session.scalars(query).all()]

    def add_watchlist(self, stock: StockInfo) -> WatchlistItem:
        """`add_watchlist`은(는) 데이터를 저장하거나 기존 상태에 추가합니다."""

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
        """`remove_watchlist`은(는) 대상 데이터나 만료된 상태를 안전하게 제거합니다."""

        with self._sessions.begin() as session:
            result = session.execute(delete(WatchlistModel).where(WatchlistModel.symbol == symbol))
            return bool(result.rowcount)

    def list_alerts(self, *, status: str | None = None) -> list[PriceAlert]:
        """`list_alerts`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        query = select(PriceAlertModel)
        if status:
            query = query.where(PriceAlertModel.status == status)
        query = query.order_by(PriceAlertModel.created_at.desc(), PriceAlertModel.id.desc())
        with self._sessions() as session:
            return [self._price_alert(model) for model in session.scalars(query).all()]

    def create_alert(
        self, symbol: str, condition: AlertCondition, target_price: Decimal
    ) -> PriceAlert:
        """`create_alert`은(는) 입력 값과 설정을 결합해 새 결과 객체를 생성합니다."""

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
        """`disable_alert`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

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
        """`record_evaluation`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

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
        """`_watchlist_item`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        return WatchlistItem(
            symbol=model.symbol,
            name=model.name,
            market=model.market,
            currency=model.currency,
            created_at=SqlAlchemyAlertRepository._utc(model.created_at),
        )

    @staticmethod
    def _price_alert(model: PriceAlertModel) -> PriceAlert:
        """`_price_alert`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

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
        """`_utc`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


class InMemoryAlertRepository(AlertRepository):
    """도메인 객체의 저장·조회 방식을 캡슐화하는 저장소입니다."""

    def __init__(self) -> None:
        """`__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다."""

        self.watchlist: dict[str, WatchlistItem] = {}
        self.alerts: dict[str, PriceAlert] = {}

    def list_watchlist(self) -> list[WatchlistItem]:
        """`list_watchlist`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        return sorted(self.watchlist.values(), key=lambda item: (item.created_at, item.symbol))

    def add_watchlist(self, stock: StockInfo) -> WatchlistItem:
        """`add_watchlist`은(는) 데이터를 저장하거나 기존 상태에 추가합니다."""

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
        """`remove_watchlist`은(는) 대상 데이터나 만료된 상태를 안전하게 제거합니다."""

        return self.watchlist.pop(symbol, None) is not None

    def list_alerts(self, *, status: str | None = None) -> list[PriceAlert]:
        """`list_alerts`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        items = self.alerts.values()
        if status:
            items = (item for item in items if item.status == status)
        return sorted(items, key=lambda item: item.created_at, reverse=True)

    def create_alert(
        self, symbol: str, condition: AlertCondition, target_price: Decimal
    ) -> PriceAlert:
        """`create_alert`은(는) 입력 값과 설정을 결합해 새 결과 객체를 생성합니다."""

        from uuid import uuid4

        item = PriceAlert(
            str(uuid4()), symbol, condition, target_price, "active", datetime.now(timezone.utc)
        )
        self.alerts[item.alert_id] = item
        return item

    def disable_alert(self, alert_id: str) -> bool:
        """`disable_alert`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

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
        """`record_evaluation`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

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
