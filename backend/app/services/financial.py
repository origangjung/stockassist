from app.financials.contracts import FinancialProvider
from app.repositories.contracts import FinancialRepository


class FinancialAnalysisService:
    def __init__(
        self, provider: FinancialProvider, repository: FinancialRepository | None = None
    ) -> None:
        self._provider = provider
        self._repository = repository

    def snapshot(self, symbol: str, fiscal_year: int, report_code: str = "11011") -> dict:
        snapshot = self._provider.get_snapshot(symbol, fiscal_year, report_code)
        if self._repository is not None:
            self._repository.save(snapshot, source=self._provider.name)
        return {
            **snapshot.__dict__,
            "provider": self._provider.name,
            "persistence_status": "saved" if self._repository is not None else "disabled",
        }
