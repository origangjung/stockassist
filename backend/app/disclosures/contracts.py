"""contracts 파일은 백엔드 도메인 기능을 담당한다."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Disclosure:
    """`Disclosure` 관련 상태와 동작을 하나의 객체로 묶습니다."""

    symbol: str
    corp_code: str
    receipt_no: str
    company_name: str
    report_name: str
    filed_at: datetime
    filer_name: str
    remarks: str | None
    document_url: str


class DisclosureProvider(ABC):
    """`DisclosureProvider` 구현체가 제공해야 하는 메서드 계약을 정의합니다."""

    name: str

    @abstractmethod
    def list_disclosures(self, symbol: str, *, days: int, limit: int) -> list[Disclosure]: ...

    def close(self) -> None:
        """Release resources held by a provider when the application stops."""
