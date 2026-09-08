"""contracts 파일은 백엔드 도메인 기능을 담당한다."""

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
    """해당 실패 조건을 호출 계층에 구분해 전달하는 예외입니다."""

    pass


class CorporateActionIngestionUnavailableError(RuntimeError):
    """해당 실패 조건을 호출 계층에 구분해 전달하는 예외입니다."""

    pass


class CorporateActionAdjustmentUnavailableError(RuntimeError):
    """해당 실패 조건을 호출 계층에 구분해 전달하는 예외입니다."""

    pass


class CorporateActionSourceNotFoundError(LookupError):
    """해당 실패 조건을 호출 계층에 구분해 전달하는 예외입니다."""

    pass


class UntrustedCorporateActionSourceError(PermissionError):
    """해당 실패 조건을 호출 계층에 구분해 전달하는 예외입니다."""

    pass


@dataclass(frozen=True)
class CorporateActionRecord:
    """저장하거나 전송할 한 건의 구조화된 데이터를 나타냅니다."""

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
    """`CorporateActionSourceMetadata` 관련 상태와 동작을 하나의 객체로 묶습니다."""

    name: str
    markets: tuple[str, ...]
    trust_status: str
    revision_strategy: str

    def __post_init__(self) -> None:
        """`__post_init__`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

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
    """계산 또는 처리 결과를 묶어 전달하는 값 객체입니다."""

    source: str
    symbol: str
    fetched_at: datetime
    actions: tuple[CorporateActionRecord, ...]


class CorporateActionProvider(Protocol):
    """`CorporateActionProvider` 구현체가 제공해야 하는 메서드 계약을 정의합니다."""

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
    """`CorporateActionRepository` 구현체가 제공해야 하는 메서드 계약을 정의합니다."""

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
