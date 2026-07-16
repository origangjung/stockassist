from app.investor_flow.contracts import InvestorFlowProvider
from app.repositories.contracts import InvestorFlowRepository


class InvestorFlowService:
    def __init__(
        self, provider: InvestorFlowProvider, repository: InvestorFlowRepository | None = None
    ) -> None:
        self._provider = provider
        self._repository = repository

    def snapshot(self, symbol: str) -> dict:
        flow = self._provider.get_flow(symbol)
        if self._repository is not None:
            self._repository.save(flow, source=self._provider.name)
        combined = flow.foreign_net_quantity + flow.institution_net_quantity
        if combined > 0:
            reference_signal = "net_inflow"
        elif combined < 0:
            reference_signal = "net_outflow"
        else:
            reference_signal = "balanced"
        return {
            **flow.__dict__,
            "provider": self._provider.name,
            "experimental": True,
            "foreign_institution_net_quantity": combined,
            "reference_signal": reference_signal,
            "persistence_status": "saved" if self._repository is not None else "disabled",
        }
