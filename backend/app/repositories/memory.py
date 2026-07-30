from dataclasses import replace
from datetime import datetime, timezone

from app.pipeline.candles import DataQualityLog
from app.providers.contracts import Candle, StockInfo
from app.repositories.contracts import (
    CandlePriceBasisInventory,
    CandlePriceBasisInventoryRow,
    CandleRepository,
    QualityLogRepository,
    StockRepository,
)
from app.financials.contracts import FinancialSnapshot
from app.repositories.contracts import FinancialRepository
from app.disclosures.contracts import Disclosure
from app.news.contracts import NewsArticle
from app.repositories.contracts import DisclosureRepository, NewsRepository
from app.investor_flow.contracts import InvestorFlow
from app.repositories.contracts import InvestorFlowRepository
from app.prediction.contracts import ModelVersionRecord, PredictionResult
from app.repositories.contracts import PredictionRepository
from app.repositories.contracts import AIReportRepository
from app.repositories.contracts import PortfolioRepository
from app.providers.contracts import BrokerAccount, HoldingsSnapshot


class InMemoryStockRepository(StockRepository):
    def __init__(self):
        self.items: dict[str, StockInfo] = {}

    def upsert(self, stock: StockInfo) -> None:
        self.items[stock.symbol] = stock


class InMemoryCandleRepository(CandleRepository):
    def __init__(self):
        self.items: dict[tuple[str, str, str, str], dict[object, Candle]] = {}
        self.sources: dict[tuple[str, str, str, str], dict[object, str]] = {}
        self.price_basis_rules: dict[tuple[str, str, str, str], dict[object, str]] = {}

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
    ) -> None:
        if not source_provider or len(source_provider) > 32:
            raise ValueError("Candle source provider must contain 1 to 32 characters")
        if not price_basis_rule_version or len(price_basis_rule_version) > 32:
            raise ValueError("Candle price-basis rule version must contain 1 to 32 characters")
        key = (symbol, interval, stage, aggregation_version)
        bucket = self.items.setdefault(key, {})
        sources = self.sources.setdefault(key, {})
        rules = self.price_basis_rules.setdefault(key, {})
        for candle in candles:
            bucket[candle.timestamp] = candle
            sources[candle.timestamp] = source_provider
            rules[candle.timestamp] = price_basis_rule_version

    def find(self, symbol: str, *, interval: str, stage: str, limit: int) -> list[Candle]:
        matches: list[Candle] = []
        for (stored_symbol, stored_interval, stored_stage, _), values in self.items.items():
            if (stored_symbol, stored_interval, stored_stage) == (symbol, interval, stage):
                matches.extend(values.values())
        return sorted(matches, key=lambda value: value.timestamp)[-limit:]

    def price_basis_inventory(
        self,
        *,
        symbol: str,
        limit: int = 200,
    ) -> CandlePriceBasisInventory:
        groups: dict[tuple[str, str, str, str, str, str], list[object]] = {}
        for key, values in self.items.items():
            stored_symbol, interval, stage, aggregation_version = key
            if stored_symbol != symbol:
                continue
            for candle in values.values():
                source_provider = self.sources.get(key, {}).get(candle.timestamp, "legacy_unknown")
                rule_version = self.price_basis_rules.get(key, {}).get(
                    candle.timestamp, "legacy_unknown"
                )
                group = (
                    source_provider,
                    candle.price_basis,
                    rule_version,
                    stage,
                    interval,
                    aggregation_version,
                )
                groups.setdefault(group, []).append(candle.timestamp)
        rows = [
            CandlePriceBasisInventoryRow(
                source_provider=key[0],
                price_basis=key[1],
                price_basis_rule_version=key[2],
                data_stage=key[3],
                interval=key[4],
                aggregation_version=key[5],
                candle_count=len(timestamps),
                first_timestamp=min(timestamps),
                last_timestamp=max(timestamps),
            )
            for key, timestamps in sorted(groups.items())
        ]
        total = sum(row.candle_count for row in rows)
        unknown = sum(row.candle_count for row in rows if row.price_basis == "unknown")
        legacy_unknown = sum(
            row.candle_count for row in rows if row.source_provider == "legacy_unknown"
        )
        legacy_rule = sum(
            row.candle_count for row in rows if row.price_basis_rule_version == "legacy_unknown"
        )
        return CandlePriceBasisInventory(
            rows[:limit], total, unknown, legacy_unknown, legacy_rule, len(rows)
        )


class InMemoryQualityLogRepository(QualityLogRepository):
    def __init__(self):
        self.items: list[tuple[str, DataQualityLog]] = []

    def save_many(self, symbol: str, logs: list[DataQualityLog]) -> None:
        self.items.extend((symbol, log) for log in logs)


class InMemoryFinancialRepository(FinancialRepository):
    def __init__(self) -> None:
        self.items: dict[tuple[str, int, str, str], FinancialSnapshot] = {}

    def save(self, snapshot: FinancialSnapshot, *, source: str) -> None:
        del source
        key = (snapshot.symbol, snapshot.fiscal_year, snapshot.report_code, snapshot.statement_type)
        self.items[key] = snapshot


class InMemoryDisclosureRepository(DisclosureRepository):
    def __init__(self) -> None:
        self.items: dict[str, Disclosure] = {}

    def save_many(self, disclosures: list[Disclosure], *, source: str) -> None:
        del source
        for disclosure in disclosures:
            self.items[disclosure.receipt_no] = disclosure


class InMemoryNewsRepository(NewsRepository):
    def __init__(self) -> None:
        self.items: dict[str, NewsArticle] = {}

    def save_many(self, articles: list[NewsArticle], *, source: str) -> None:
        del source
        for article in articles:
            self.items[article.url] = article


class InMemoryInvestorFlowRepository(InvestorFlowRepository):
    def __init__(self) -> None:
        self.items: dict[tuple[str, object], InvestorFlow] = {}

    def save(self, flow: InvestorFlow, *, source: str) -> None:
        del source
        self.items[(flow.symbol, flow.as_of_date)] = flow


class InMemoryPredictionRepository(PredictionRepository):
    def __init__(self) -> None:
        self.items: list[PredictionResult] = []
        self.versions: dict[str, ModelVersionRecord] = {}

    def save(self, prediction: PredictionResult, *, algorithm: str) -> None:
        self.items.append(prediction)
        self.versions.setdefault(
            prediction.model_version,
            ModelVersionRecord(
                version=prediction.model_version,
                symbol=prediction.symbol,
                algorithm=algorithm,
                horizon_days=prediction.horizon_days,
                validation_status=prediction.validation_status,
                validation_metrics=prediction.validation_metrics,
                registry_stage="challenger",
                data_as_of=prediction.data_as_of,
            ),
        )

    def list_versions(
        self,
        *,
        limit: int,
        offset: int,
        symbol: str | None = None,
        algorithm: str | None = None,
        horizon_days: int | None = None,
    ) -> tuple[list[ModelVersionRecord], int]:
        matches = [
            record
            for record in self.versions.values()
            if (symbol is None or record.symbol == symbol)
            and (algorithm is None or record.algorithm == algorithm)
            and (horizon_days is None or record.horizon_days == horizon_days)
        ]
        matches.sort(key=lambda record: (record.data_as_of, record.version), reverse=True)
        return matches[offset : offset + limit], len(matches)

    def get_version(self, version: str) -> ModelVersionRecord | None:
        return self.versions.get(version)

    def promote(self, version: str) -> ModelVersionRecord | None:
        target = self.versions.get(version)
        if target is None:
            return None
        for key, record in tuple(self.versions.items()):
            if (
                record.registry_stage == "champion"
                and record.symbol == target.symbol
                and record.algorithm == target.algorithm
                and record.horizon_days == target.horizon_days
            ):
                self.versions[key] = replace(record, registry_stage="challenger")
        promoted = replace(
            target,
            registry_stage="champion",
            promoted_at=datetime.now(timezone.utc),
        )
        self.versions[version] = promoted
        return promoted


class InMemoryAIReportRepository(AIReportRepository):
    def __init__(self) -> None:
        self.items: list[dict] = []

    def save(self, report: dict) -> None:
        self.items.append(report)


class InMemoryPortfolioRepository(PortfolioRepository):
    def __init__(self) -> None:
        self.accounts: dict[tuple[str, int], BrokerAccount] = {}
        self.snapshots: dict[tuple[str, int], HoldingsSnapshot] = {}

    def save_snapshot(
        self, provider: str, account: BrokerAccount, snapshot: HoldingsSnapshot
    ) -> None:
        key = (provider, account.account_seq)
        self.accounts[key] = account
        self.snapshots[key] = snapshot
