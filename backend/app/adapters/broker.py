from app.providers.contracts import Capability, StockProvider


class CapabilityUnavailableError(LookupError):
    pass


class BrokerAdapter:
    """Selects an active provider without exposing provider choice to services."""

    def __init__(self, providers: list[StockProvider]):
        self._providers = providers

    def provider_for(self, capability: Capability) -> StockProvider:
        for provider in self._providers:
            if provider.capabilities.supports(capability):
                return provider
        raise CapabilityUnavailableError(f"활성 Provider에 {capability.value} 기능이 없습니다.")
