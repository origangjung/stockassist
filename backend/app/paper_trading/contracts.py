"""모의투자 계좌와 체결 원장이 공유하는 도메인 계약이다."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


class PaperTradingError(ValueError):
    """사용자에게 안전하게 전달할 수 있는 모의투자 도메인 오류다."""


class InsufficientPaperCashError(PaperTradingError):
    """주문 금액과 수수료를 지불할 모의 현금이 부족할 때 발생한다."""


class InsufficientPaperPositionError(PaperTradingError):
    """공매도를 막기 위해 보유 수량보다 큰 매도를 거절할 때 발생한다."""


class PaperRiskLimitError(PaperTradingError):
    """모의 매수 후 계좌가 중앙 위험관리 한도를 넘을 때 발생한다."""


@dataclass(frozen=True)
class PaperAccount:
    """브라우저별 모의 계좌의 통화별 현금 상태다."""

    account_id: str
    initial_cash_krw: Decimal
    initial_cash_usd: Decimal
    cash_krw: Decimal
    cash_usd: Decimal
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class PaperPosition:
    """평균 매입가와 누적 실현손익을 보존하는 모의 보유 종목이다."""

    symbol: str
    name: str
    market: str
    currency: str
    quantity: Decimal
    average_price: Decimal
    last_price: Decimal
    realized_pnl: Decimal
    updated_at: datetime


@dataclass(frozen=True)
class PaperOrder:
    """한 번 체결된 모의 시장가 주문의 변경 불가능한 기록이다."""

    order_id: str
    idempotency_key: str
    symbol: str
    name: str
    market: str
    currency: str
    side: str
    quantity: Decimal
    fill_price: Decimal
    notional: Decimal
    commission: Decimal
    executed_at: datetime


@dataclass(frozen=True)
class PaperFill:
    """시세 조회가 끝난 뒤 저장소가 원자적으로 적용할 체결 명령이다."""

    idempotency_key: str
    symbol: str
    name: str
    market: str
    currency: str
    side: str
    quantity: Decimal
    fill_price: Decimal
    commission_rate: Decimal
    executed_at: datetime
