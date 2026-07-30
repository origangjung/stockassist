from collections.abc import Mapping
from datetime import datetime
from decimal import Decimal, InvalidOperation
from zoneinfo import ZoneInfo

from app.corporate_actions.contracts import ACTION_STATUSES, CorporateActionRecord
from app.corporate_actions.sources import DART_SOURCE

DART_MAPPING_VERSION = "dart-corporate-action-2026.1"
SEOUL = ZoneInfo("Asia/Seoul")


class DartCorporateActionMapper:
    """Normalize reviewed DART rows without claiming exchange-effective dates."""

    def map_bonus_issue(
        self,
        row: Mapping[str, object],
        *,
        symbol: str,
        event_id: str,
        revision: int,
        known_at: datetime,
        effective_at: datetime,
        status: str = "announced",
    ) -> CorporateActionRecord:
        ratio = self._positive_decimal(row, "fric_nstk_ascnt_ps_ostk")
        multiplier = Decimal(1) + ratio
        return self._record(
            symbol=symbol,
            event_id=event_id,
            revision=revision,
            known_at=known_at,
            effective_at=effective_at,
            announced_at=self._optional_date(row.get("fric_bddd")),
            action_type="stock_dividend",
            price_factor=Decimal(1) / multiplier,
            volume_factor=multiplier,
            status=status,
        )

    def map_proportional_capital_reduction(
        self,
        row: Mapping[str, object],
        *,
        symbol: str,
        event_id: str,
        revision: int,
        known_at: datetime,
        effective_at: datetime,
        proportional_share_consolidation: bool,
        status: str = "announced",
    ) -> CorporateActionRecord:
        if not proportional_share_consolidation:
            raise ValueError(
                "DART capital reduction requires reviewed proportional consolidation evidence"
            )
        before = self._positive_decimal(row, "bfcr_tisstk_ostk")
        after = self._positive_decimal(row, "atcr_tisstk_ostk")
        if after >= before:
            raise ValueError("DART capital reduction must reduce outstanding common shares")
        volume_factor = after / before
        return self._record(
            symbol=symbol,
            event_id=event_id,
            revision=revision,
            known_at=known_at,
            effective_at=effective_at,
            announced_at=self._optional_date(row.get("bddd")),
            action_type="reverse_split",
            price_factor=before / after,
            volume_factor=volume_factor,
            status=status,
        )

    @staticmethod
    def _record(
        *,
        symbol: str,
        event_id: str,
        revision: int,
        known_at: datetime,
        effective_at: datetime,
        announced_at: datetime | None,
        action_type: str,
        price_factor: Decimal,
        volume_factor: Decimal,
        status: str,
    ) -> CorporateActionRecord:
        DartCorporateActionMapper._require_aware(known_at)
        DartCorporateActionMapper._require_aware(effective_at)
        if not symbol or not event_id or revision < 1 or status not in ACTION_STATUSES:
            raise ValueError("Invalid DART corporate action identity or status")
        return CorporateActionRecord(
            symbol=symbol.upper(),
            action_type=action_type,
            event_id=event_id,
            revision=revision,
            effective_at=effective_at,
            announced_at=announced_at,
            known_at=known_at,
            price_factor=price_factor,
            volume_factor=volume_factor,
            status=status,
            source=DART_SOURCE.name,
            rule_version=DART_MAPPING_VERSION,
        )

    @staticmethod
    def _positive_decimal(row: Mapping[str, object], field: str) -> Decimal:
        raw = str(row.get(field) or "").replace(",", "").strip()
        try:
            value = Decimal(raw)
        except InvalidOperation as exc:
            raise ValueError(f"DART field {field} is not numeric") from exc
        if not value.is_finite() or value <= 0:
            raise ValueError(f"DART field {field} must be positive")
        return value

    @staticmethod
    def _optional_date(value: object) -> datetime | None:
        raw = str(value or "").strip().replace("-", "").replace(".", "")
        if not raw:
            return None
        try:
            parsed = datetime.strptime(raw, "%Y%m%d")
        except ValueError as exc:
            raise ValueError("DART decision date must use YYYYMMDD") from exc
        return parsed.replace(tzinfo=SEOUL)

    @staticmethod
    def _require_aware(value: datetime) -> None:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("DART corporate action timestamps must be timezone-aware")
