"""PyPortfolioOpt를 프로젝트의 자금배분 계약에 연결한다."""

from decimal import Decimal

import pandas as pd

from app.fund_management.contracts import AllocationMandate, PortfolioOptimizationError


class PyPortfolioOptOptimizer:
    """검증된 오픈소스 엔진으로 최소변동성 또는 최대 샤프 비중을 계산한다."""

    name = "PyPortfolioOpt-1.6"

    def optimize(self, prices: pd.DataFrame, mandate: AllocationMandate) -> dict[str, Decimal]:
        """결측치를 제거한 가격으로 기대수익과 공분산을 계산해 비중을 최적화한다."""
        try:
            from pypfopt import EfficientFrontier, expected_returns, objective_functions, risk_models
        except ImportError as exc:
            raise PortfolioOptimizationError(
                "포트폴리오 최적화 선택 의존성이 설치되지 않았습니다. "
                "프로젝트의 portfolio 의존성 그룹을 설치해 주세요."
            ) from exc

        clean_prices = prices.sort_index().dropna(how="any")
        if len(clean_prices) < 60:
            raise PortfolioOptimizationError("공통 거래일 가격이 최소 60개 필요합니다.")
        if (clean_prices <= 0).any().any():
            raise PortfolioOptimizationError("가격 데이터에는 0 이하 값이 포함될 수 없습니다.")

        try:
            expected = expected_returns.mean_historical_return(clean_prices, frequency=252)
            covariance = risk_models.sample_cov(clean_prices, frequency=252)
            frontier = EfficientFrontier(
                expected,
                covariance,
                weight_bounds=(float(mandate.min_asset_weight), float(mandate.max_asset_weight)),
            )
            # 작은 L2 규제는 유사한 자산 하나에 해가 몰리는 현상을 완화한다.
            frontier.add_objective(objective_functions.L2_reg, gamma=0.1)
            if mandate.objective == "max_sharpe":
                frontier.max_sharpe(risk_free_rate=0.0)
            else:
                frontier.min_volatility()
            weights = frontier.clean_weights(cutoff=0.0001, rounding=8)
        except Exception as exc:
            raise PortfolioOptimizationError(f"포트폴리오 최적화에 실패했습니다: {exc}") from exc

        positive = {symbol: Decimal(str(weight)) for symbol, weight in weights.items() if weight > 0}
        total = sum(positive.values(), Decimal("0"))
        if not positive or total <= 0:
            raise PortfolioOptimizationError("최적화 결과에 투자 가능한 비중이 없습니다.")
        return {symbol: weight / total for symbol, weight in positive.items()}
