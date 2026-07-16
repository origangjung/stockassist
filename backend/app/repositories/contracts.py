from abc import ABC, abstractmethod

from app.pipeline.candles import DataQualityLog, DataQualityLogRecord
from app.providers.contracts import Candle, StockInfo
from app.backtest.models import (
    BacktestConfig,
    BacktestResult,
    BacktestRunDetail,
    BacktestRunSummary,
)
from app.score.engine import ScoreWeights
from app.financials.contracts import FinancialSnapshot
from app.disclosures.contracts import Disclosure
from app.news.contracts import NewsArticle
from app.investor_flow.contracts import InvestorFlow
from app.prediction.contracts import ModelVersionRecord, PredictionResult
from app.providers.contracts import BrokerAccount, HoldingsSnapshot


class StockRepository(ABC):
    @abstractmethod
    def upsert(self, stock: StockInfo) -> None: ...


class CandleRepository(ABC):
    @abstractmethod
    def save_many(
        self,
        symbol: str,
        candles: list[Candle],
        *,
        interval: str,
        stage: str,
        aggregation_version: str,
    ) -> None: ...

    @abstractmethod
    def find(self, symbol: str, *, interval: str, stage: str, limit: int) -> list[Candle]: ...


class QualityLogRepository(ABC):
    @abstractmethod
    def save_many(self, symbol: str, logs: list[DataQualityLog]) -> None: ...


class QualityLogReadRepository(ABC):
    @abstractmethod
    def list_recent(
        self,
        *,
        limit: int,
        offset: int,
        symbol: str | None = None,
        severity: str | None = None,
    ) -> tuple[list[DataQualityLogRecord], int, dict[str, int]]: ...


class BacktestRepository(ABC):
    @abstractmethod
    def save(self, symbol: str, config: BacktestConfig, result: BacktestResult) -> str: ...

    @abstractmethod
    def list_runs(
        self,
        *,
        limit: int,
        offset: int,
        symbol: str | None = None,
    ) -> tuple[list[BacktestRunSummary], int]: ...

    @abstractmethod
    def get_run(self, run_id: str) -> BacktestRunDetail | None: ...


class ScoreWeightRepository(ABC):
    @abstractmethod
    def get_active(self) -> ScoreWeights: ...

    @abstractmethod
    def save(self, weights: ScoreWeights, *, activate: bool = False) -> None: ...


class FinancialRepository(ABC):
    @abstractmethod
    def save(self, snapshot: FinancialSnapshot, *, source: str) -> None: ...


class DisclosureRepository(ABC):
    @abstractmethod
    def save_many(self, disclosures: list[Disclosure], *, source: str) -> None: ...


class NewsRepository(ABC):
    @abstractmethod
    def save_many(self, articles: list[NewsArticle], *, source: str) -> None: ...


class InvestorFlowRepository(ABC):
    @abstractmethod
    def save(self, flow: InvestorFlow, *, source: str) -> None: ...


class PredictionRepository(ABC):
    @abstractmethod
    def save(self, prediction: PredictionResult, *, algorithm: str) -> None: ...

    @abstractmethod
    def list_versions(
        self,
        *,
        limit: int,
        offset: int,
        symbol: str | None = None,
        algorithm: str | None = None,
        horizon_days: int | None = None,
    ) -> tuple[list[ModelVersionRecord], int]: ...

    @abstractmethod
    def get_version(self, version: str) -> ModelVersionRecord | None: ...

    @abstractmethod
    def promote(self, version: str) -> ModelVersionRecord | None: ...


class AIReportRepository(ABC):
    @abstractmethod
    def save(self, report: dict) -> None: ...


class PortfolioRepository(ABC):
    @abstractmethod
    def save_snapshot(
        self, provider: str, account: BrokerAccount, snapshot: HoldingsSnapshot
    ) -> None: ...
