from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Protocol

ACTION_TYPES = frozenset(
    {"split", "reverse_split", "cash_dividend", "stock_dividend", "rights_issue"}
)
ACTION_STATUSES = frozenset({"announced", "confirmed", "cancelled"})


class CorporateActionRevisionConflictError(ValueError):
    pass


@dataclass(frozen=True)
class CorporateActionRecord:
    symbol: str
    action_type: str
    event_id: str
    revision: int
    effective_at: datetime
    announced_at: datetime | None
    known_at: datetime
    price_factor: Decimal
    volume_factor: Decimal
    status: str
    source: str
    rule_version: str
    recorded_at: datetime | None = None


class CorporateActionRepository(Protocol):
    def save(self, action: CorporateActionRecord) -> None: ...

    def list_known(self, symbol: str, *, as_of: datetime) -> list[CorporateActionRecord]: ...

    def list_recent(
        self,
        *,
        limit: int,
        offset: int,
        symbol: str | None = None,
        as_of: datetime | None = None,
    ) -> tuple[list[CorporateActionRecord], int]: ...
