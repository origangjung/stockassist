from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal


@dataclass(frozen=True)
class InvestorFlow:
    symbol: str
    as_of_date: date
    foreign_net_quantity: Decimal
    institution_net_quantity: Decimal
    individual_net_quantity: Decimal
    foreign_holding_quantity: Decimal | None
    foreign_holding_rate: Decimal | None
    data_as_of: datetime


class InvestorFlowProvider(ABC):
    name: str

    @abstractmethod
    def get_flow(self, symbol: str) -> InvestorFlow: ...

    def close(self) -> None:
        """Release resources held by a provider when the application stops."""
