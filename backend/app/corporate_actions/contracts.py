import re
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Protocol

ACTION_TYPES = frozenset(
    {"split", "reverse_split", "cash_dividend", "stock_dividend", "rights_issue"}
)
ACTION_STATUSES = frozenset({"announced", "confirmed", "cancelled"})
SOURCE_TRUST_STATUSES = frozenset({"experimental", "verified", "disabled"})


class CorporateActionRevisionConflictError(ValueError):
    pass


class CorporateActionIngestionUnavailableError(RuntimeError):
    pass


class CorporateActionAdjustmentUnavailableError(RuntimeError):
    pass


class CorporateActionSourceNotFoundError(LookupError):
    pass


class UntrustedCorporateActionSourceError(PermissionError):
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


@dataclass(frozen=True)
class CorporateActionSourceMetadata:
    name: str
    markets: tuple[str, ...]
    trust_status: str
    revision_strategy: str

    def __post_init__(self) -> None:
        if (
            not re.fullmatch(r"[a-z0-9_-]{1,32}", self.name)
            or not self.markets
            or any(not re.fullmatch(r"[A-Z]{2,8}", market) for market in self.markets)
            or self.trust_status not in SOURCE_TRUST_STATUSES
            or not self.revision_strategy.strip()
        ):
            raise ValueError("Invalid corporate action source metadata")


@dataclass(frozen=True)
class CorporateActionFetchResult:
    source: str
    symbol: str
    fetched_at: datetime
    actions: tuple[CorporateActionRecord, ...]


class CorporateActionProvider(Protocol):
    metadata: CorporateActionSourceMetadata

    def fetch_actions(
        self,
        symbol: str,
        *,
        start: datetime,
        end: datetime,
        limit: int,
    ) -> CorporateActionFetchResult: ...


class CorporateActionRepository(Protocol):
    def save(self, action: CorporateActionRecord) -> None: ...

    def save_batch(self, actions: list[CorporateActionRecord]) -> tuple[int, int]: ...

    def list_known(self, symbol: str, *, as_of: datetime) -> list[CorporateActionRecord]: ...

    def list_recent(
        self,
        *,
        limit: int,
        offset: int,
        symbol: str | None = None,
        as_of: datetime | None = None,
    ) -> tuple[list[CorporateActionRecord], int]: ...
