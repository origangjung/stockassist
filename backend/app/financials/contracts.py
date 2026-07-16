from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True)
class FinancialSnapshot:
    symbol: str
    corp_code: str
    fiscal_year: int
    report_code: str
    statement_type: str
    currency: str
    revenue: Decimal | None
    operating_income: Decimal | None
    net_income: Decimal | None
    total_assets: Decimal | None
    total_liabilities: Decimal | None
    total_equity: Decimal | None
    data_as_of: datetime


class FinancialProvider(ABC):
    name: str

    @abstractmethod
    def get_snapshot(
        self, symbol: str, fiscal_year: int, report_code: str = "11011"
    ) -> FinancialSnapshot: ...

    def close(self) -> None:
        """Release provider-owned connections."""
