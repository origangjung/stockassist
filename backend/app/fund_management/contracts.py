"""자금운용 제안 계층에서 공유하는 값 객체와 인터페이스다."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol

import pandas as pd


class FundManagementError(ValueError):
    """사용자에게 전달할 수 있는 자금운용 제안 오류다."""


class PortfolioOptimizationError(FundManagementError):
    """입력 데이터로 안정적인 최적화 결과를 만들 수 없을 때 발생한다."""


@dataclass(frozen=True)
class AllocationMandate:
    """최적화기가 반드시 지켜야 하는 목적과 자산배분 한도다."""

    objective: str
    invest_ratio: Decimal
    min_asset_weight: Decimal
    max_asset_weight: Decimal
    lookback_days: int


class PortfolioOptimizer(Protocol):
    """외부 포트폴리오 최적화 프레임워크를 교체할 수 있게 하는 인터페이스다."""

    name: str

    def optimize(self, prices: pd.DataFrame, mandate: AllocationMandate) -> dict[str, Decimal]:
        """가격 행렬과 운용 한도를 받아 투자자산 내부의 목표 비중을 반환한다."""
        ...
