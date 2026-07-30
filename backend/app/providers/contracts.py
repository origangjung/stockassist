from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import Enum

PRICE_BASES = frozenset({"unknown", "unadjusted", "provider_adjusted", "point_in_time_adjusted"})
CANDLE_PRICE_BASIS_VERIFICATION_STATUSES = frozenset({"unverified", "verified", "synthetic"})


@dataclass(frozen=True)
class CandlePriceBasisPolicy:
    expected_basis: str
    verification_status: str
    rule_version: str
    evidence: str

    def __post_init__(self) -> None:
        if self.expected_basis not in PRICE_BASES:
            raise ValueError("Unsupported Provider candle price basis")
        if self.verification_status not in CANDLE_PRICE_BASIS_VERIFICATION_STATUSES:
            raise ValueError("Unsupported candle price-basis verification status")
        if self.verification_status == "unverified" and self.expected_basis != "unknown":
            raise ValueError("Unverified Provider policies must use the unknown price basis")
        if not self.rule_version or len(self.rule_version) > 32:
            raise ValueError("Candle price-basis rule version must contain 1 to 32 characters")
        if not self.evidence:
            raise ValueError("Candle price-basis policy evidence is required")


UNKNOWN_CANDLE_PRICE_BASIS_POLICY = CandlePriceBasisPolicy(
    expected_basis="unknown",
    verification_status="unverified",
    rule_version="provider-contract-v1",
    evidence="Provider has not declared verified candle adjustment semantics",
)


class Capability(str, Enum):
    QUOTE = "quote"
    ORDERBOOK = "orderbook"
    TRADES = "trades"
    CANDLES = "candles"
    STREAMING = "streaming"
    ORDERS = "orders"
    CONDITIONAL_ORDERS = "conditional_orders"
    INVESTOR_FLOW = "investor_flow"
    ACCOUNT_SYNC = "account_sync"
    WARNINGS = "warnings"


@dataclass(frozen=True)
class ProviderCapabilities:
    supports_quote: bool = False
    supports_orderbook: bool = False
    supports_trades: bool = False
    supports_candles: bool = False
    supports_streaming: bool = False
    supports_orders: bool = False
    supports_conditional_orders: bool = False
    supports_investor_flow: bool = False
    supports_account_sync: bool = False
    supports_warnings: bool = False

    def supports(self, capability: Capability) -> bool:
        return bool(getattr(self, f"supports_{capability.value}"))


@dataclass(frozen=True)
class Quote:
    symbol: str
    name: str | None
    price: Decimal
    change: Decimal | None
    change_percent: Decimal | None
    volume: int | None
    as_of: datetime | None
    currency: str | None = None


@dataclass(frozen=True)
class Candle:
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int
    price_basis: str = "unknown"

    def __post_init__(self) -> None:
        if self.price_basis not in PRICE_BASES:
            raise ValueError("Unsupported candle price basis")


@dataclass(frozen=True)
class OrderbookLevel:
    price: Decimal
    quantity: Decimal


@dataclass(frozen=True)
class Trade:
    symbol: str
    price: Decimal
    quantity: Decimal
    side: str | None
    executed_at: datetime


@dataclass(frozen=True)
class StockInfo:
    symbol: str
    name: str
    market: str
    sector: str | None
    listed_at: datetime | None
    currency: str = "KRW"


@dataclass(frozen=True)
class StockWarning:
    warning_type: str
    exchange: str | None
    start_date: date | None
    end_date: date | None


@dataclass(frozen=True)
class BrokerAccount:
    account_seq: int
    account_no: str
    account_type: str


@dataclass(frozen=True)
class Holding:
    symbol: str
    name: str
    market_country: str
    currency: str
    quantity: Decimal
    last_price: Decimal
    average_purchase_price: Decimal
    purchase_amount: Decimal
    market_value: Decimal
    market_value_after_cost: Decimal
    profit_loss: Decimal
    profit_loss_after_cost: Decimal
    profit_rate: Decimal
    profit_rate_after_cost: Decimal
    daily_profit_loss: Decimal
    daily_profit_rate: Decimal
    commission: Decimal | None
    tax: Decimal | None


@dataclass(frozen=True)
class HoldingsSnapshot:
    account_seq: int
    total_purchase_amount: dict[str, Decimal | None]
    market_value: dict[str, Decimal | None]
    market_value_after_cost: dict[str, Decimal | None]
    profit_loss: dict[str, Decimal | None]
    profit_loss_after_cost: dict[str, Decimal | None]
    profit_rate: Decimal
    profit_rate_after_cost: Decimal
    daily_profit_loss: dict[str, Decimal | None]
    daily_profit_rate: Decimal
    holdings: list[Holding]
    fetched_at: datetime


class StockProvider(ABC):
    name: str
    capabilities: ProviderCapabilities
    candle_price_basis_policy = UNKNOWN_CANDLE_PRICE_BASIS_POLICY

    @abstractmethod
    def get_quote(self, symbol: str) -> Quote: ...

    @abstractmethod
    def get_candles(self, symbol: str, limit: int) -> list[Candle]: ...

    @abstractmethod
    def get_orderbook(self, symbol: str) -> tuple[list[OrderbookLevel], list[OrderbookLevel]]: ...

    @abstractmethod
    def get_trades(self, symbol: str, limit: int) -> list[Trade]: ...

    @abstractmethod
    def get_stock_info(self, symbol: str) -> StockInfo: ...

    @abstractmethod
    def get_warnings(self, symbol: str) -> list[StockWarning]: ...

    def get_accounts(self) -> list[BrokerAccount]:
        raise NotImplementedError("This provider does not support account synchronization")

    def get_holdings(self, account_seq: int) -> HoldingsSnapshot:
        raise NotImplementedError("This provider does not support account synchronization")

    def close(self) -> None:
        """Release provider resources when the application shuts down."""
