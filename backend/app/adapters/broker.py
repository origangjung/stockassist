from dataclasses import dataclass

from app.providers.contracts import Candle, CandlePriceBasisPolicy, Capability, StockProvider
from app.providers.errors import ProviderValidationError


class CapabilityUnavailableError(LookupError):
    pass


@dataclass(frozen=True)
class ValidatedCandleBatch:
    candles: list[Candle]
    provider: StockProvider
    policy: CandlePriceBasisPolicy


class BrokerAdapter:
    """Selects an active provider without exposing provider choice to services."""

    def __init__(self, providers: list[StockProvider]):
        self._providers = providers

    def provider_for(self, capability: Capability) -> StockProvider:
        for provider in self._providers:
            if provider.capabilities.supports(capability):
                return provider
        raise CapabilityUnavailableError(f"활성 Provider에 {capability.value} 기능이 없습니다.")

    def candles(self, symbol: str, limit: int) -> ValidatedCandleBatch:
        provider = self.provider_for(Capability.CANDLES)
        candles = provider.get_candles(symbol, limit)
        policy = provider.candle_price_basis_policy
        observed = sorted({candle.price_basis for candle in candles})
        if observed and observed != [policy.expected_basis]:
            raise ProviderValidationError(
                "Provider candle price basis does not match its declared contract",
                code="candle-price-basis-contract-mismatch",
                data={
                    "provider": provider.name,
                    "expected": policy.expected_basis,
                    "observed": observed,
                    "rule_version": policy.rule_version,
                },
            )
        return ValidatedCandleBatch(candles, provider, policy)
