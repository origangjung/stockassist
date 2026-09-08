"""investor_flow 파일은 애플리케이션 사용 사례 기능을 담당한다."""

from app.investor_flow.contracts import InvestorFlowProvider
from app.repositories.contracts import InvestorFlowRepository


class InvestorFlowService:
    """사용 사례의 처리 순서와 하위 의존성 호출을 조율하는 서비스입니다."""

    def __init__(
        self, provider: InvestorFlowProvider, repository: InvestorFlowRepository | None = None
    ) -> None:
        """`__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다."""

        self._provider = provider
        self._repository = repository

    def snapshot(self, symbol: str) -> dict:
        """`snapshot`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

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
