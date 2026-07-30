from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

from app.corporate_actions.contracts import ACTION_STATUSES, ACTION_TYPES, CorporateActionRecord
from app.providers.contracts import Candle

ADJUSTMENT_VERSION = "2026.1"


@dataclass(frozen=True)
class AdjustmentResult:
    candles: list[Candle]
    applied_actions: list[CorporateActionRecord]
    data_as_of: datetime
    adjustment_version: str = ADJUSTMENT_VERSION
    raw_candles_mutated: bool = False
    source_price_basis: str = "unadjusted"
    output_price_basis: str = "point_in_time_adjusted"


@dataclass(frozen=True)
class BacktestAdjustmentResult:
    candles: list[Candle]
    applied_actions: list[CorporateActionRecord]
    data_as_of: datetime
    adjustment_version: str = ADJUSTMENT_VERSION
    adjustment_direction: str = "forward"
    look_ahead_safe: bool = True
    raw_candles_mutated: bool = False
    source_price_basis: str = "unadjusted"
    output_price_basis: str = "point_in_time_adjusted"


class CorporateActionAdjustmentEngine:
    """Create an adjusted view while preserving raw and cleaned source candles."""

    def adjust(
        self,
        candles: list[Candle],
        actions: list[CorporateActionRecord],
        *,
        as_of: datetime,
    ) -> AdjustmentResult:
        if candles and {candle.price_basis for candle in candles} != {"unadjusted"}:
            raise ValueError(
                "Corporate action adjustment requires explicitly unadjusted source candles"
            )
        self._require_aware(as_of, "as_of")
        for candle in candles:
            self._require_aware(candle.timestamp, "candle timestamp")
        selected = self._latest_effective_revisions(actions, as_of)
        affecting = [
            action
            for action in selected
            if any(candle.timestamp < action.effective_at for candle in candles)
        ]
        adjusted: list[Candle] = []
        for candle in candles:
            price_factor = Decimal("1")
            volume_factor = Decimal("1")
            for action in affecting:
                if candle.timestamp < action.effective_at:
                    price_factor *= action.price_factor
                    volume_factor *= action.volume_factor
            adjusted.append(
                Candle(
                    timestamp=candle.timestamp,
                    open=candle.open * price_factor,
                    high=candle.high * price_factor,
                    low=candle.low * price_factor,
                    close=candle.close * price_factor,
                    volume=int(
                        (Decimal(candle.volume) * volume_factor).quantize(
                            Decimal("1"), rounding=ROUND_HALF_UP
                        )
                    ),
                    price_basis="point_in_time_adjusted",
                )
            )
        return AdjustmentResult(adjusted, affecting, as_of)

    def _latest_effective_revisions(
        self,
        actions: list[CorporateActionRecord],
        as_of: datetime,
    ) -> list[CorporateActionRecord]:
        latest: dict[tuple[str, str], CorporateActionRecord] = {}
        if len({action.symbol for action in actions}) > 1:
            raise ValueError("Corporate action input must contain only one symbol")
        for action in actions:
            self._validate_action(action)
            if action.known_at > as_of or action.effective_at > as_of:
                continue
            key = (action.source, action.event_id)
            current = latest.get(key)
            if current is None or (action.known_at, action.revision) > (
                current.known_at,
                current.revision,
            ):
                latest[key] = action
        return sorted(
            (action for action in latest.values() if action.status == "confirmed"),
            key=lambda action: (action.effective_at, action.source, action.event_id),
        )

    def _validate_action(self, action: CorporateActionRecord) -> None:
        self._require_aware(action.effective_at, "effective_at")
        self._require_aware(action.known_at, "known_at")
        if action.announced_at is not None:
            self._require_aware(action.announced_at, "announced_at")
        if action.revision < 1:
            raise ValueError("Corporate action revision must be positive")
        if action.action_type not in ACTION_TYPES:
            raise ValueError("Unsupported corporate action type")
        if action.status not in ACTION_STATUSES:
            raise ValueError("Unsupported corporate action status")
        if action.price_factor <= 0 or action.volume_factor <= 0:
            raise ValueError("Corporate action factors must be positive")

    @staticmethod
    def _require_aware(value: datetime, field: str) -> None:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"Corporate action {field} must be timezone-aware")


class CorporateActionBacktestAdjustmentEngine:
    """Forward-normalize confirmed actions without rewriting pre-event history."""

    def adjust(
        self,
        candles: list[Candle],
        actions: list[CorporateActionRecord],
        *,
        as_of: datetime,
    ) -> BacktestAdjustmentResult:
        CorporateActionAdjustmentEngine._require_aware(as_of, "as_of")
        if candles and {candle.price_basis for candle in candles} != {"unadjusted"}:
            raise ValueError(
                "Backtest corporate action adjustment requires explicitly unadjusted candles"
            )
        for candle in candles:
            CorporateActionAdjustmentEngine._require_aware(candle.timestamp, "candle timestamp")

        grouped: dict[tuple[str, str], list[CorporateActionRecord]] = {}
        for action in actions:
            CorporateActionAdjustmentEngine()._validate_action(action)
            if action.known_at <= as_of and action.effective_at <= as_of:
                grouped.setdefault((action.source, action.event_id), []).append(action)

        selected: list[CorporateActionRecord] = []
        for revisions in grouped.values():
            if len(revisions) != 1:
                raise ValueError(
                    "Backtest adjustment rejects corrected or cancelled event histories"
                )
            action = revisions[0]
            if action.known_at > action.effective_at:
                raise ValueError(
                    "Backtest adjustment rejects actions known after their effective time"
                )
            if action.status == "confirmed":
                selected.append(action)

        adjusted: list[Candle] = []
        for candle in candles:
            price_factor = Decimal("1")
            volume_factor = Decimal("1")
            for action in selected:
                if candle.timestamp >= action.effective_at:
                    price_factor /= action.price_factor
                    volume_factor /= action.volume_factor
            adjusted.append(
                Candle(
                    timestamp=candle.timestamp,
                    open=candle.open * price_factor,
                    high=candle.high * price_factor,
                    low=candle.low * price_factor,
                    close=candle.close * price_factor,
                    volume=int(
                        (Decimal(candle.volume) * volume_factor).quantize(
                            Decimal("1"), rounding=ROUND_HALF_UP
                        )
                    ),
                    price_basis="point_in_time_adjusted",
                )
            )
        return BacktestAdjustmentResult(
            candles=adjusted,
            applied_actions=sorted(
                selected, key=lambda item: (item.effective_at, item.source, item.event_id)
            ),
            data_as_of=as_of,
        )
