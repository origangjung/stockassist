from datetime import datetime, timezone

from sqlalchemy import delete, func, select, update
from sqlalchemy.orm import Session, sessionmaker

from app.models.market import DataQualityLogModel, StockCandleModel, StockModel
from app.models.financial import CompanyModel, FinancialModel
from app.models.content import DisclosureModel, NewsArticleModel
from app.models.investor_flow import InvestorFlowModel
from app.models.prediction import ModelVersionModel, PredictionModel
from app.models.ai_report import AIReportModel
from app.models.portfolio import BrokerAccountModel, HoldingModel
from app.pipeline.candles import DataQualityLog, DataQualityLogRecord, QualitySeverity
from app.providers.contracts import Candle, StockInfo
from app.repositories.contracts import (
    CandleRepository,
    QualityLogReadRepository,
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


class SqlAlchemyStockRepository(StockRepository):
    def __init__(self, sessions: sessionmaker[Session]):
        self._sessions = sessions

    def upsert(self, stock: StockInfo) -> None:
        with self._sessions.begin() as session:
            model = session.get(StockModel, stock.symbol)
            if model is None:
                session.add(StockModel(**stock.__dict__))
            else:
                model.name = stock.name
                model.market = stock.market
                model.currency = stock.currency
                model.sector = stock.sector
                model.listed_at = stock.listed_at


class SqlAlchemyCandleRepository(CandleRepository):
    def __init__(self, sessions: sessionmaker[Session]):
        self._sessions = sessions

    def save_many(
        self,
        symbol: str,
        candles: list[Candle],
        *,
        interval: str,
        stage: str,
        aggregation_version: str,
    ) -> None:
        with self._sessions.begin() as session:
            for candle in candles:
                statement = select(StockCandleModel).where(
                    StockCandleModel.symbol == symbol,
                    StockCandleModel.timestamp == candle.timestamp,
                    StockCandleModel.interval == interval,
                    StockCandleModel.data_stage == stage,
                    StockCandleModel.aggregation_version == aggregation_version,
                )
                model = session.scalar(statement)
                values = {
                    "open": candle.open,
                    "high": candle.high,
                    "low": candle.low,
                    "close": candle.close,
                    "volume": candle.volume,
                    "price_basis": candle.price_basis,
                }
                if model is None:
                    session.add(
                        StockCandleModel(
                            symbol=symbol,
                            timestamp=candle.timestamp,
                            interval=interval,
                            data_stage=stage,
                            aggregation_version=aggregation_version,
                            **values,
                        )
                    )
                else:
                    for key, value in values.items():
                        setattr(model, key, value)

    def find(self, symbol: str, *, interval: str, stage: str, limit: int) -> list[Candle]:
        with self._sessions() as session:
            statement = (
                select(StockCandleModel)
                .where(
                    StockCandleModel.symbol == symbol,
                    StockCandleModel.interval == interval,
                    StockCandleModel.data_stage == stage,
                )
                .order_by(StockCandleModel.timestamp.desc())
                .limit(limit)
            )
            models = list(reversed(session.scalars(statement).all()))
            return [
                Candle(
                    model.timestamp,
                    model.open,
                    model.high,
                    model.low,
                    model.close,
                    model.volume,
                    model.price_basis,
                )
                for model in models
            ]


class SqlAlchemyQualityLogRepository(QualityLogRepository, QualityLogReadRepository):
    def __init__(self, sessions: sessionmaker[Session]):
        self._sessions = sessions

    def save_many(self, symbol: str, logs: list[DataQualityLog]) -> None:
        with self._sessions.begin() as session:
            session.add_all(
                [
                    DataQualityLogModel(
                        symbol=symbol,
                        rule=log.rule,
                        severity=log.severity.value,
                        message=log.message,
                        observed_at=log.timestamp,
                    )
                    for log in logs
                ]
            )

    def list_recent(
        self,
        *,
        limit: int,
        offset: int,
        symbol: str | None = None,
        severity: str | None = None,
    ) -> tuple[list[DataQualityLogRecord], int, dict[str, int]]:
        filters = []
        if symbol:
            filters.append(DataQualityLogModel.symbol == symbol)
        if severity:
            filters.append(DataQualityLogModel.severity == severity)
        with self._sessions() as session:
            total = session.scalar(
                select(func.count()).select_from(DataQualityLogModel).where(*filters)
            ) or 0
            counts = {
                row.severity: row.total
                for row in session.execute(
                    select(
                        DataQualityLogModel.severity.label("severity"),
                        func.count().label("total"),
                    )
                    .where(*filters)
                    .group_by(DataQualityLogModel.severity)
                )
            }
            models = session.scalars(
                select(DataQualityLogModel)
                .where(*filters)
                .order_by(DataQualityLogModel.created_at.desc(), DataQualityLogModel.id.desc())
                .offset(offset)
                .limit(limit)
            ).all()
            return (
                [
                    DataQualityLogRecord(
                        log_id=model.id,
                        symbol=model.symbol,
                        rule=model.rule,
                        severity=QualitySeverity(model.severity),
                        message=model.message,
                        observed_at=model.observed_at,
                        created_at=model.created_at,
                    )
                    for model in models
                ],
                total,
                counts,
            )


class SqlAlchemyFinancialRepository(FinancialRepository):
    def __init__(self, sessions: sessionmaker[Session]):
        self._sessions = sessions

    def save(self, snapshot: FinancialSnapshot, *, source: str) -> None:
        with self._sessions.begin() as session:
            company = session.get(CompanyModel, snapshot.symbol)
            if company is None:
                session.add(CompanyModel(symbol=snapshot.symbol, dart_corp_code=snapshot.corp_code))
            else:
                company.dart_corp_code = snapshot.corp_code
            statement = select(FinancialModel).where(
                FinancialModel.symbol == snapshot.symbol,
                FinancialModel.fiscal_year == snapshot.fiscal_year,
                FinancialModel.report_code == snapshot.report_code,
                FinancialModel.statement_type == snapshot.statement_type,
            )
            model = session.scalar(statement)
            values = {
                "corp_code": snapshot.corp_code,
                "currency": snapshot.currency,
                "revenue": snapshot.revenue,
                "operating_income": snapshot.operating_income,
                "net_income": snapshot.net_income,
                "total_assets": snapshot.total_assets,
                "total_liabilities": snapshot.total_liabilities,
                "total_equity": snapshot.total_equity,
                "data_as_of": snapshot.data_as_of,
                "source": source,
            }
            if model is None:
                session.add(
                    FinancialModel(
                        symbol=snapshot.symbol,
                        fiscal_year=snapshot.fiscal_year,
                        report_code=snapshot.report_code,
                        statement_type=snapshot.statement_type,
                        **values,
                    )
                )
            else:
                for key, value in values.items():
                    setattr(model, key, value)


class SqlAlchemyDisclosureRepository(DisclosureRepository):
    def __init__(self, sessions: sessionmaker[Session]):
        self._sessions = sessions

    def save_many(self, disclosures: list[Disclosure], *, source: str) -> None:
        with self._sessions.begin() as session:
            for disclosure in disclosures:
                model = session.scalar(
                    select(DisclosureModel).where(
                        DisclosureModel.receipt_no == disclosure.receipt_no
                    )
                )
                values = {**disclosure.__dict__, "source": source}
                if model is None:
                    session.add(DisclosureModel(**values))
                else:
                    for key, value in values.items():
                        setattr(model, key, value)


class SqlAlchemyNewsRepository(NewsRepository):
    def __init__(self, sessions: sessionmaker[Session]):
        self._sessions = sessions

    def save_many(self, articles: list[NewsArticle], *, source: str) -> None:
        with self._sessions.begin() as session:
            for article in articles:
                model = session.scalar(
                    select(NewsArticleModel).where(NewsArticleModel.url == article.url)
                )
                values = {**article.__dict__, "source": source}
                if model is None:
                    session.add(NewsArticleModel(**values))
                else:
                    for key, value in values.items():
                        setattr(model, key, value)


class SqlAlchemyInvestorFlowRepository(InvestorFlowRepository):
    def __init__(self, sessions: sessionmaker[Session]):
        self._sessions = sessions

    def save(self, flow: InvestorFlow, *, source: str) -> None:
        with self._sessions.begin() as session:
            model = session.scalar(
                select(InvestorFlowModel).where(
                    InvestorFlowModel.symbol == flow.symbol,
                    InvestorFlowModel.as_of_date == flow.as_of_date,
                    InvestorFlowModel.source == source,
                )
            )
            values = {**flow.__dict__, "source": source}
            if model is None:
                session.add(InvestorFlowModel(**values))
            else:
                for key, value in values.items():
                    setattr(model, key, value)


class SqlAlchemyPredictionRepository(PredictionRepository):
    def __init__(self, sessions: sessionmaker[Session]):
        self._sessions = sessions

    def save(self, prediction: PredictionResult, *, algorithm: str) -> None:
        with self._sessions.begin() as session:
            version = session.get(ModelVersionModel, prediction.model_version)
            if version is None:
                session.add(
                    ModelVersionModel(
                        version=prediction.model_version,
                        scope_symbol=prediction.symbol,
                        algorithm=algorithm,
                        horizon_days=prediction.horizon_days,
                        validation_status=prediction.validation_status,
                        validation_metrics=prediction.validation_metrics,
                        data_as_of=prediction.data_as_of,
                    )
                )
            session.add(
                PredictionModel(
                    symbol=prediction.symbol,
                    horizon_days=prediction.horizon_days,
                    rise_probability=prediction.rise_probability,
                    confidence_lower=prediction.confidence_lower,
                    confidence_upper=prediction.confidence_upper,
                    model_version=prediction.model_version,
                    validation_status=prediction.validation_status,
                    data_as_of=prediction.data_as_of,
                )
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
        filters = []
        if symbol is not None:
            filters.append(ModelVersionModel.scope_symbol == symbol)
        if algorithm is not None:
            filters.append(ModelVersionModel.algorithm == algorithm)
        if horizon_days is not None:
            filters.append(ModelVersionModel.horizon_days == horizon_days)
        with self._sessions() as session:
            total = (
                session.scalar(select(func.count()).select_from(ModelVersionModel).where(*filters))
                or 0
            )
            statement = (
                select(ModelVersionModel)
                .where(*filters)
                .order_by(ModelVersionModel.created_at.desc(), ModelVersionModel.version)
                .limit(limit)
                .offset(offset)
            )
            return [
                _model_version_record(model) for model in session.scalars(statement).all()
            ], int(total)

    def get_version(self, version: str) -> ModelVersionRecord | None:
        with self._sessions() as session:
            model = session.get(ModelVersionModel, version)
            return None if model is None else _model_version_record(model)

    def promote(self, version: str) -> ModelVersionRecord | None:
        with self._sessions.begin() as session:
            target = session.get(ModelVersionModel, version, with_for_update=True)
            if target is None:
                return None
            session.execute(
                update(ModelVersionModel)
                .where(
                    ModelVersionModel.scope_symbol == target.scope_symbol,
                    ModelVersionModel.algorithm == target.algorithm,
                    ModelVersionModel.horizon_days == target.horizon_days,
                    ModelVersionModel.registry_stage == "champion",
                    ModelVersionModel.version != target.version,
                )
                .values(registry_stage="challenger", promoted_at=None)
            )
            target.registry_stage = "champion"
            target.promoted_at = datetime.now(timezone.utc)
            session.flush()
            return _model_version_record(target)


class SqlAlchemyAIReportRepository(AIReportRepository):
    def __init__(self, sessions: sessionmaker[Session]):
        self._sessions = sessions

    def save(self, report: dict) -> None:
        with self._sessions.begin() as session:
            session.add(
                AIReportModel(
                    symbol=report["symbol"],
                    generator=report["generator"],
                    model_version=report["model_version"],
                    validation_status=report["validation_status"],
                    data_as_of=report["data_as_of"],
                    report=report,
                )
            )


class SqlAlchemyPortfolioRepository(PortfolioRepository):
    def __init__(self, sessions: sessionmaker[Session]):
        self._sessions = sessions

    def save_snapshot(
        self, provider: str, account: BrokerAccount, snapshot: HoldingsSnapshot
    ) -> None:
        with self._sessions.begin() as session:
            model = session.scalar(
                select(BrokerAccountModel).where(
                    BrokerAccountModel.provider == provider,
                    BrokerAccountModel.account_seq == account.account_seq,
                )
            )
            values = {
                "account_no_masked": _mask_account_no(account.account_no),
                "account_type": account.account_type,
                "sync_status": "synced",
                "last_synced_at": snapshot.fetched_at,
            }
            if model is None:
                session.add(
                    BrokerAccountModel(provider=provider, account_seq=account.account_seq, **values)
                )
            else:
                for key, value in values.items():
                    setattr(model, key, value)
            session.execute(
                delete(HoldingModel).where(
                    HoldingModel.provider == provider,
                    HoldingModel.account_seq == account.account_seq,
                )
            )
            session.add_all(
                HoldingModel(
                    provider=provider,
                    account_seq=account.account_seq,
                    data_as_of=snapshot.fetched_at,
                    updated_at=snapshot.fetched_at,
                    **holding.__dict__,
                )
                for holding in snapshot.holdings
            )


def _mask_account_no(account_no: str) -> str:
    visible = account_no[-4:]
    return f"{'*' * max(0, len(account_no) - len(visible))}{visible}"


def _model_version_record(model: ModelVersionModel) -> ModelVersionRecord:
    return ModelVersionRecord(
        version=model.version,
        symbol=model.scope_symbol,
        algorithm=model.algorithm,
        horizon_days=model.horizon_days,
        validation_status=model.validation_status,
        validation_metrics=model.validation_metrics,
        registry_stage=model.registry_stage,
        data_as_of=model.data_as_of,
        promoted_at=model.promoted_at,
        created_at=model.created_at,
    )
