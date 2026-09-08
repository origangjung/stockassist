"""contracts 파일은 데이터 저장과 조회 기능을 담당한다."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

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
    """`StockRepository` 구현체가 제공해야 하는 메서드 계약을 정의합니다."""

    @abstractmethod
    def upsert(self, stock: StockInfo) -> None: ...


@dataclass(frozen=True)
class CandlePriceBasisInventoryRow:
    """`CandlePriceBasisInventoryRow` 관련 상태와 동작을 하나의 객체로 묶습니다."""

    source_provider: str
    price_basis: str
    price_basis_rule_version: str
    data_stage: str
    interval: str
    aggregation_version: str
    candle_count: int
    first_timestamp: datetime
    last_timestamp: datetime


@dataclass(frozen=True)
class CandlePriceBasisInventory:
    """`CandlePriceBasisInventory` 관련 상태와 동작을 하나의 객체로 묶습니다."""

    rows: list[CandlePriceBasisInventoryRow]
    total_candles: int
    unknown_candles: int
    legacy_unknown_candles: int
    legacy_rule_candles: int
    total_groups: int


class CandleRepository(ABC):
    """`CandleRepository` 구현체가 제공해야 하는 메서드 계약을 정의합니다."""

    @abstractmethod
    def save_many(
        self,
        symbol: str,
        candles: list[Candle],
        *,
        interval: str,
        stage: str,
        aggregation_version: str,
        source_provider: str,
        price_basis_rule_version: str,
    ) -> None: ...

    @abstractmethod
    def find(self, symbol: str, *, interval: str, stage: str, limit: int) -> list[Candle]: ...

    @abstractmethod
    def price_basis_inventory(
        self,
        *,
        symbol: str,
        limit: int = 200,
    ) -> CandlePriceBasisInventory: ...


class QualityLogRepository(ABC):
    """`QualityLogRepository` 구현체가 제공해야 하는 메서드 계약을 정의합니다."""

    @abstractmethod
    def save_many(self, symbol: str, logs: list[DataQualityLog]) -> None: ...


@dataclass(frozen=True)
class CandleIngestionWrite:
    """`CandleIngestionWrite` 관련 상태와 동작을 하나의 객체로 묶습니다."""

    stock: StockInfo
    raw_candles: list[Candle]
    cleaned_candles: list[Candle]
    quality_logs: list[DataQualityLog]
    interval: str
    cleaned_aggregation_version: str
    source_provider: str
    price_basis_rule_version: str


class CandleIngestionRepository(ABC):
    """`CandleIngestionRepository` 구현체가 제공해야 하는 메서드 계약을 정의합니다."""

    @abstractmethod
    def save(self, batch: CandleIngestionWrite) -> None: ...


class QualityLogReadRepository(ABC):
    """`QualityLogReadRepository` 구현체가 제공해야 하는 메서드 계약을 정의합니다."""

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
    """`BacktestRepository` 구현체가 제공해야 하는 메서드 계약을 정의합니다."""

    @abstractmethod
    def save(
        self,
        symbol: str,
        config: BacktestConfig,
        result: BacktestResult,
        *,
        metadata: dict[str, object] | None = None,
    ) -> str: ...

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
    """`ScoreWeightRepository` 구현체가 제공해야 하는 메서드 계약을 정의합니다."""

    @abstractmethod
    def get_active(self) -> ScoreWeights: ...

    @abstractmethod
    def save(self, weights: ScoreWeights, *, activate: bool = False) -> None: ...


class FinancialRepository(ABC):
    """`FinancialRepository` 구현체가 제공해야 하는 메서드 계약을 정의합니다."""

    @abstractmethod
    def save(self, snapshot: FinancialSnapshot, *, source: str) -> None: ...


class DisclosureRepository(ABC):
    """`DisclosureRepository` 구현체가 제공해야 하는 메서드 계약을 정의합니다."""

    @abstractmethod
    def save_many(self, disclosures: list[Disclosure], *, source: str) -> None: ...


class NewsRepository(ABC):
    """`NewsRepository` 구현체가 제공해야 하는 메서드 계약을 정의합니다."""

    @abstractmethod
    def save_many(self, articles: list[NewsArticle], *, source: str) -> None: ...


class InvestorFlowRepository(ABC):
    """`InvestorFlowRepository` 구현체가 제공해야 하는 메서드 계약을 정의합니다."""

    @abstractmethod
    def save(self, flow: InvestorFlow, *, source: str) -> None: ...


class PredictionRepository(ABC):
    """`PredictionRepository` 구현체가 제공해야 하는 메서드 계약을 정의합니다."""

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
    """`AIReportRepository` 구현체가 제공해야 하는 메서드 계약을 정의합니다."""

    @abstractmethod
    def save(self, report: dict) -> None: ...


class PortfolioRepository(ABC):
    """`PortfolioRepository` 구현체가 제공해야 하는 메서드 계약을 정의합니다."""

    @abstractmethod
    def save_snapshot(
        self, provider: str, account: BrokerAccount, snapshot: HoldingsSnapshot
    ) -> None: ...
