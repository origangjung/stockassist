"""models 파일은 백엔드 도메인 기능을 담당한다."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Literal

AlertCondition = Literal["above", "below"]
AlertStatus = Literal["active", "triggered", "disabled"]


@dataclass(frozen=True)
class WatchlistItem:
    """목록에서 사용하는 한 건의 구조화된 항목을 나타냅니다."""

    symbol: str
    name: str
    market: str
    currency: str
    created_at: datetime


@dataclass(frozen=True)
class PriceAlert:
    """`PriceAlert` 관련 상태와 동작을 하나의 객체로 묶습니다."""

    alert_id: str
    symbol: str
    condition: AlertCondition
    target_price: Decimal
    status: AlertStatus
    created_at: datetime
    last_price: Decimal | None = None
    last_evaluated_at: datetime | None = None
    triggered_at: datetime | None = None
