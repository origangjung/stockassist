"""financial 파일은 애플리케이션 사용 사례 기능을 담당한다."""

from app.financials.contracts import FinancialProvider
from app.repositories.contracts import FinancialRepository


class FinancialAnalysisService:
    """사용 사례의 처리 순서와 하위 의존성 호출을 조율하는 서비스입니다."""

    def __init__(
        self, provider: FinancialProvider, repository: FinancialRepository | None = None
    ) -> None:
        """`__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다."""

        self._provider = provider
        self._repository = repository

    def snapshot(self, symbol: str, fiscal_year: int, report_code: str = "11011") -> dict:
        """`snapshot`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        snapshot = self._provider.get_snapshot(symbol, fiscal_year, report_code)
        if self._repository is not None:
            self._repository.save(snapshot, source=self._provider.name)
        return {
            **snapshot.__dict__,
            "provider": self._provider.name,
            "persistence_status": "saved" if self._repository is not None else "disabled",
        }
