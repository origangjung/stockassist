"""contracts 파일은 백엔드 도메인 기능을 담당한다."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True)
class FinancialSnapshot:
    """특정 시점에 관측된 데이터 상태를 변경 없이 전달하는 값 객체입니다."""

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
    """`FinancialProvider` 구현체가 제공해야 하는 메서드 계약을 정의합니다."""

    name: str

    @abstractmethod
    def get_snapshot(
        self, symbol: str, fiscal_year: int, report_code: str = "11011"
    ) -> FinancialSnapshot: ...

    def get_issued_shares(
        self, symbol: str, fiscal_year: int, report_code: str = "11011"
    ) -> Decimal | None:
        """`get_issued_shares`은(는) 필요한 데이터를 조회해 반환합니다."""

        return None

    def close(self) -> None:
        """Release provider-owned connections."""
