"""모의투자 전용 저장소 구현이다. 실제 증권 주문 저장소와 의도적으로 분리한다."""

from abc import ABC, abstractmethod
from dataclasses import replace
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from threading import RLock
from uuid import uuid4

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, sessionmaker

from app.models.paper_trading import PaperAccountModel, PaperOrderModel, PaperPositionModel
from app.paper_trading.contracts import (
    InsufficientPaperCashError,
    InsufficientPaperPositionError,
    PaperAccount,
    PaperFill,
    PaperOrder,
    PaperPosition,
    PaperTradingError,
)
from app.paper_trading.risk import validate_buy_risk

DEFAULT_KRW = Decimal("10000000")
DEFAULT_USD = Decimal("10000")
MONEY_UNIT = Decimal("0.01")
QUANTITY_UNIT = Decimal("0.000001")


class PaperTradingRepository(ABC):
    """계좌 생성, 체결, 초기화를 원자적으로 수행하는 저장소 인터페이스다."""

    persistence_status = "temporary"

    @abstractmethod
    def snapshot(self, account_id: str) -> tuple[PaperAccount, list[PaperPosition], list[PaperOrder]]: ...

    @abstractmethod
    def execute(self, account_id: str, fill: PaperFill) -> tuple[PaperAccount, list[PaperPosition], list[PaperOrder]]: ...

    @abstractmethod
    def reset(self, account_id: str) -> tuple[PaperAccount, list[PaperPosition], list[PaperOrder]]: ...


def _new_account(account_id: str, now: datetime) -> PaperAccount:
    """`_new_account`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    return PaperAccount(account_id, DEFAULT_KRW, DEFAULT_USD, DEFAULT_KRW, DEFAULT_USD, now, now)


def _apply_fill(
    account: PaperAccount,
    positions: list[PaperPosition],
    orders: list[PaperOrder],
    fill: PaperFill,
) -> tuple[PaperAccount, list[PaperPosition], list[PaperOrder]]:
    """수수료, 현금, 평균단가, 실현손익을 한 체결 규칙으로 계산한다."""
    duplicate = next((order for order in orders if order.idempotency_key == fill.idempotency_key), None)
    if duplicate is not None:
        if (
            duplicate.symbol != fill.symbol
            or duplicate.side != fill.side
            or duplicate.quantity != fill.quantity
        ):
            raise PaperTradingError("같은 중복 방지 키로 다른 주문을 요청할 수 없습니다.")
        return account, positions, orders

    notional = (fill.fill_price * fill.quantity).quantize(MONEY_UNIT, ROUND_HALF_UP)
    commission = (notional * fill.commission_rate).quantize(MONEY_UNIT, ROUND_HALF_UP)
    cash_field = "cash_usd" if fill.currency == "USD" else "cash_krw"
    cash = getattr(account, cash_field)
    current = next((item for item in positions if item.symbol == fill.symbol), None)

    if fill.side == "buy":
        validate_buy_risk(account, positions, fill)
        required = notional + commission
        if cash < required:
            raise InsufficientPaperCashError("모의 현금이 부족합니다.")
        old_quantity = current.quantity if current else Decimal("0")
        old_cost = (current.average_price * old_quantity) if current else Decimal("0")
        new_quantity = (old_quantity + fill.quantity).quantize(QUANTITY_UNIT)
        average_price = ((old_cost + notional) / new_quantity).quantize(QUANTITY_UNIT)
        position = PaperPosition(
            fill.symbol, fill.name, fill.market, fill.currency, new_quantity,
            average_price, fill.fill_price, current.realized_pnl if current else Decimal("0"),
            fill.executed_at,
        )
        next_cash = cash - required
    else:
        if current is None or current.quantity < fill.quantity:
            raise InsufficientPaperPositionError("보유 수량보다 많이 매도할 수 없습니다.")
        next_quantity = (current.quantity - fill.quantity).quantize(QUANTITY_UNIT)
        realized = current.realized_pnl + (fill.fill_price - current.average_price) * fill.quantity - commission
        position = replace(
            current,
            quantity=next_quantity,
            last_price=fill.fill_price,
            realized_pnl=realized.quantize(MONEY_UNIT, ROUND_HALF_UP),
            updated_at=fill.executed_at,
        )
        next_cash = cash + notional - commission

    next_positions = [item for item in positions if item.symbol != fill.symbol]
    if position.quantity > 0:
        next_positions.append(position)
    next_positions.sort(key=lambda item: item.symbol)
    account = replace(account, **{cash_field: next_cash.quantize(MONEY_UNIT)}, updated_at=fill.executed_at)
    order = PaperOrder(
        str(uuid4()), fill.idempotency_key, fill.symbol, fill.name, fill.market,
        fill.currency, fill.side, fill.quantity, fill.fill_price, notional,
        commission, fill.executed_at,
    )
    return account, next_positions, [order, *orders][:100]


class InMemoryPaperTradingRepository(PaperTradingRepository):
    """테스트와 비영속 개발 환경에서 스레드 안전하게 동작하는 저장소다."""

    def __init__(self) -> None:
        """`__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다."""

        self._states: dict[str, tuple[PaperAccount, list[PaperPosition], list[PaperOrder]]] = {}
        self._lock = RLock()

    def snapshot(self, account_id: str):
        """`snapshot`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        with self._lock:
            return self._states.setdefault(account_id, (_new_account(account_id, datetime.now(timezone.utc)), [], []))

    def execute(self, account_id: str, fill: PaperFill):
        """`execute`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        with self._lock:
            state = _apply_fill(*self.snapshot(account_id), fill)
            self._states[account_id] = state
            return state

    def reset(self, account_id: str):
        """`reset`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        with self._lock:
            state = (_new_account(account_id, datetime.now(timezone.utc)), [], [])
            self._states[account_id] = state
            return state


class SqlAlchemyPaperTradingRepository(PaperTradingRepository):
    """Docker/PostgreSQL 환경에서 행 잠금으로 중복·동시 체결을 막는 저장소다."""

    persistence_status = "saved"

    def __init__(self, sessions: sessionmaker[Session]):
        """`__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다."""

        self._sessions = sessions

    def snapshot(self, account_id: str):
        """`snapshot`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        with self._sessions.begin() as session:
            account = self._get_or_create(session, account_id)
            return self._read(session, account)

    def execute(self, account_id: str, fill: PaperFill):
        """`execute`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        with self._sessions.begin() as session:
            account_model = self._get_or_create(session, account_id, lock=True)
            state = self._read(session, account_model)
            next_state = _apply_fill(*state, fill)
            if next_state == state:
                return state
            self._write(session, account_model, next_state)
            return next_state

    def reset(self, account_id: str):
        """`reset`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        with self._sessions.begin() as session:
            account_model = self._get_or_create(session, account_id, lock=True)
            session.execute(delete(PaperPositionModel).where(PaperPositionModel.account_id == account_id))
            session.execute(delete(PaperOrderModel).where(PaperOrderModel.account_id == account_id))
            now = datetime.now(timezone.utc)
            account_model.initial_cash_krw = DEFAULT_KRW
            account_model.initial_cash_usd = DEFAULT_USD
            account_model.cash_krw = DEFAULT_KRW
            account_model.cash_usd = DEFAULT_USD
            account_model.updated_at = now
            session.flush()
            return self._read(session, account_model)

    def _get_or_create(self, session: Session, account_id: str, *, lock: bool = False) -> PaperAccountModel:
        """`_get_or_create`은(는) 필요한 데이터를 조회해 반환합니다."""

        query = select(PaperAccountModel).where(PaperAccountModel.id == account_id)
        model = session.scalar(query.with_for_update() if lock else query)
        if model is None:
            now = datetime.now(timezone.utc)
            model = PaperAccountModel(
                id=account_id, initial_cash_krw=DEFAULT_KRW, initial_cash_usd=DEFAULT_USD,
                cash_krw=DEFAULT_KRW, cash_usd=DEFAULT_USD, created_at=now, updated_at=now,
            )
            session.add(model)
            session.flush()
        return model

    def _read(self, session: Session, model: PaperAccountModel):
        """`_read`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        positions = session.scalars(
            select(PaperPositionModel).where(PaperPositionModel.account_id == model.id).order_by(PaperPositionModel.symbol)
        ).all()
        orders = session.scalars(
            select(PaperOrderModel).where(PaperOrderModel.account_id == model.id)
            .order_by(PaperOrderModel.executed_at.desc()).limit(100)
        ).all()
        account = PaperAccount(model.id, model.initial_cash_krw, model.initial_cash_usd, model.cash_krw, model.cash_usd, model.created_at, model.updated_at)
        return account, [PaperPosition(p.symbol, p.name, p.market, p.currency, p.quantity, p.average_price, p.last_price, p.realized_pnl, p.updated_at) for p in positions], [PaperOrder(o.id, o.idempotency_key, o.symbol, o.name, o.market, o.currency, o.side, o.quantity, o.fill_price, o.notional, o.commission, o.executed_at) for o in orders]

    def _write(self, session: Session, model: PaperAccountModel, state) -> None:
        """`_write`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        account, positions, orders = state
        model.cash_krw, model.cash_usd, model.updated_at = account.cash_krw, account.cash_usd, account.updated_at
        session.execute(delete(PaperPositionModel).where(PaperPositionModel.account_id == model.id))
        session.add_all(PaperPositionModel(account_id=model.id, **position.__dict__) for position in positions)
        newest = orders[0]
        session.add(PaperOrderModel(id=newest.order_id, account_id=model.id, **{key: value for key, value in newest.__dict__.items() if key != "order_id"}))
