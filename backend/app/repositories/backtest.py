from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from app.backtest.models import (
    BacktestConfig,
    BacktestResult,
    BacktestRunDetail,
    BacktestRunSummary,
)
from app.models.backtest import BacktestResultModel, BacktestRunModel
from app.repositories.contracts import BacktestRepository


def _json_safe(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    return value


class SqlAlchemyBacktestRepository(BacktestRepository):
    def __init__(self, sessions: sessionmaker[Session]):
        self._sessions = sessions

    def save(
        self,
        symbol: str,
        config: BacktestConfig,
        result: BacktestResult,
        *,
        metadata: dict[str, object] | None = None,
    ) -> str:
        now = datetime.now(timezone.utc)
        engine = "event_driven" if result.events else "vectorized"
        config_payload = {
            **_json_safe(asdict(config)),
            "engine": engine,
            "engine_version": result.engine_version,
            "market_data_adjustment": _json_safe(metadata or {"mode": "none"}),
        }
        run = BacktestRunModel(
            symbol=symbol,
            strategy=result.strategy,
            status=result.validation_status,
            config=config_payload,
            started_at=now,
            finished_at=now,
        )
        with self._sessions.begin() as session:
            session.add(run)
            session.flush()
            session.add(
                BacktestResultModel(
                    run_id=run.id,
                    metrics=_json_safe(asdict(result.metrics)),
                    equity_curve=_json_safe([asdict(point) for point in result.equity_curve]),
                    trades=_json_safe([asdict(trade) for trade in result.trades]),
                    events=_json_safe([asdict(event) for event in result.events]),
                )
            )
        return run.id

    def list_runs(
        self,
        *,
        limit: int,
        offset: int,
        symbol: str | None = None,
    ) -> tuple[list[BacktestRunSummary], int]:
        conditions = []
        if symbol:
            conditions.append(BacktestRunModel.symbol == symbol)
        count_query = select(func.count()).select_from(BacktestRunModel).where(*conditions)
        query = (
            select(BacktestRunModel, BacktestResultModel)
            .join(BacktestResultModel, BacktestResultModel.run_id == BacktestRunModel.id)
            .where(*conditions)
            .order_by(BacktestRunModel.started_at.desc(), BacktestRunModel.id.desc())
            .offset(offset)
            .limit(limit)
        )
        with self._sessions() as session:
            total = int(session.scalar(count_query) or 0)
            rows = session.execute(query).all()
        return [self._summary(run, result) for run, result in rows], total

    def get_run(self, run_id: str) -> BacktestRunDetail | None:
        query = (
            select(BacktestRunModel, BacktestResultModel)
            .join(BacktestResultModel, BacktestResultModel.run_id == BacktestRunModel.id)
            .where(BacktestRunModel.id == run_id)
        )
        with self._sessions() as session:
            row = session.execute(query).one_or_none()
        if row is None:
            return None
        run, result = row
        return BacktestRunDetail(
            summary=self._summary(run, result),
            config=dict(run.config or {}),
            equity_curve=list(result.equity_curve or []),
            trades=list(result.trades or []),
            events=list(result.events or []),
        )

    @staticmethod
    def _summary(
        run: BacktestRunModel,
        result: BacktestResultModel,
    ) -> BacktestRunSummary:
        config = dict(run.config or {})
        has_events = bool(result.events)
        engine = str(config.get("engine") or ("event_driven" if has_events else "vectorized"))
        fallback_version = "event-backtest-2026.2" if has_events else "backtest-2026.1"
        return BacktestRunSummary(
            run_id=run.id,
            symbol=run.symbol,
            strategy=run.strategy,
            status=run.status,
            engine=engine,
            engine_version=str(config.get("engine_version") or fallback_version),
            started_at=run.started_at,
            finished_at=run.finished_at,
            metrics=dict(result.metrics or {}),
        )
