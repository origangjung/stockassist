"""contracts 파일은 백엔드 도메인 기능을 담당한다."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal


@dataclass(frozen=True)
class InvestorFlow:
    """`InvestorFlow` 관련 상태와 동작을 하나의 객체로 묶습니다."""

    symbol: str
    as_of_date: date
    foreign_net_quantity: Decimal
    institution_net_quantity: Decimal
    individual_net_quantity: Decimal
    foreign_holding_quantity: Decimal | None
    foreign_holding_rate: Decimal | None
    data_as_of: datetime


class InvestorFlowProvider(ABC):
    """`InvestorFlowProvider` 구현체가 제공해야 하는 메서드 계약을 정의합니다."""

    name: str

    @abstractmethod
    def get_flow(self, symbol: str) -> InvestorFlow: ...

    def close(self) -> None:
        """Release resources held by a provider when the application stops."""
