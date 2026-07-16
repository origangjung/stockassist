from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Literal

AlertCondition = Literal["above", "below"]
AlertStatus = Literal["active", "triggered", "disabled"]


@dataclass(frozen=True)
class WatchlistItem:
    symbol: str
    name: str
    market: str
    currency: str
    created_at: datetime


@dataclass(frozen=True)
class PriceAlert:
    alert_id: str
    symbol: str
    condition: AlertCondition
    target_price: Decimal
    status: AlertStatus
    created_at: datetime
    last_price: Decimal | None = None
    last_evaluated_at: datetime | None = None
    triggered_at: datetime | None = None
