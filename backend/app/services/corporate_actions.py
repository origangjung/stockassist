from dataclasses import asdict
from datetime import UTC, datetime

from app.corporate_actions import (
    ADJUSTMENT_VERSION,
    AdjustmentResult,
    CorporateActionAdjustmentEngine,
    CorporateActionRepository,
)
from app.providers.contracts import Candle


class CorporateActionService:
    def __init__(
        self,
        repository: CorporateActionRepository | None,
        engine: CorporateActionAdjustmentEngine | None = None,
    ) -> None:
        self._repository = repository
        self._engine = engine or CorporateActionAdjustmentEngine()

    def recent(
        self,
        *,
        limit: int,
        offset: int,
        symbol: str | None = None,
        as_of: datetime | None = None,
    ) -> dict[str, object]:
        point_in_time = as_of or datetime.now(UTC)
        self._require_aware(point_in_time)
        if self._repository is None:
            return {
                "persistence_status": "disabled",
                "items": [],
                "total": 0,
                "limit": limit,
                "offset": offset,
                "data_as_of": point_in_time,
                "adjustment_version": ADJUSTMENT_VERSION,
                "application_mode": "preview_only",
                "raw_candles_mutated": False,
            }
        items, total = self._repository.list_recent(
            limit=limit,
            offset=offset,
            symbol=symbol,
            as_of=point_in_time,
        )
        return {
            "persistence_status": "enabled",
            "items": [asdict(item) for item in items],
            "total": total,
            "limit": limit,
            "offset": offset,
            "data_as_of": point_in_time,
            "adjustment_version": ADJUSTMENT_VERSION,
            "application_mode": "preview_only",
            "raw_candles_mutated": False,
        }

    def adjusted_view(
        self,
        symbol: str,
        candles: list[Candle],
        *,
        as_of: datetime,
    ) -> AdjustmentResult:
        self._require_aware(as_of)
        actions = (
            self._repository.list_known(symbol, as_of=as_of)
            if self._repository is not None
            else []
        )
        return self._engine.adjust(
            candles,
            actions,
            as_of=as_of,
        )

    @staticmethod
    def _require_aware(value: datetime) -> None:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Corporate action as_of must be timezone-aware")
