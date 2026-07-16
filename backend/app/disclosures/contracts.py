from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Disclosure:
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
    name: str

    @abstractmethod
    def list_disclosures(self, symbol: str, *, days: int, limit: int) -> list[Disclosure]: ...

    def close(self) -> None:
        """Release resources held by a provider when the application stops."""
