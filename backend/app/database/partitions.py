from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime
import re

from sqlalchemy import text
from sqlalchemy.orm import Session, sessionmaker

_PARTITION_NAME = re.compile(r"^stock_candles_[0-9]{4}_[0-9]{2}$")


@dataclass(frozen=True)
class PlannedPartition:
    name: str
    starts_at: date
    ends_at: date


def _shift_month(value: date, offset: int) -> date:
    month_index = value.year * 12 + value.month - 1 + offset
    return date(month_index // 12, month_index % 12 + 1, 1)


def plan_future_partitions(reference: date, lookahead_months: int) -> list[PlannedPartition]:
    current_month = reference.replace(day=1)
    return [
        PlannedPartition(
            name=f"stock_candles_{start.year:04d}_{start.month:02d}",
            starts_at=start,
            ends_at=_shift_month(start, 1),
        )
        for offset in range(1, lookahead_months + 1)
        for start in [_shift_month(current_month, offset)]
    ]


class CandlePartitionMaintenanceService:
    def __init__(self, sessions: sessionmaker[Session], lookahead_months: int) -> None:
        self._sessions = sessions
        self._lookahead_months = lookahead_months

    @property
    def supported(self) -> bool:
        engine = self._sessions.kw["bind"]
        return engine.dialect.name == "postgresql"

    def ensure_future(self, reference: date | None = None) -> dict[str, object]:
        planned = plan_future_partitions(
            reference or datetime.now(UTC).date(),
            self._lookahead_months,
        )
        if not self.supported:
            return {
                "status": "unsupported",
                "dialect": self._sessions.kw["bind"].dialect.name,
                "created_or_existing": [],
                "planned": [asdict(item) for item in planned],
            }
        with self._sessions.begin() as session:
            for partition in planned:
                if not _PARTITION_NAME.fullmatch(partition.name):
                    raise ValueError("Generated an invalid partition identifier")
                session.execute(
                    text(
                        f"CREATE TABLE IF NOT EXISTS {partition.name} "
                        "PARTITION OF stock_candles "
                        f"FOR VALUES FROM ('{partition.starts_at.isoformat()}') "
                        f"TO ('{partition.ends_at.isoformat()}')"
                    )
                )
        return {
            "status": "ready",
            "dialect": "postgresql",
            "created_or_existing": [item.name for item in planned],
            "planned": [asdict(item) for item in planned],
        }

    def status(self) -> dict[str, object]:
        if not self.supported:
            return {
                "status": "unsupported",
                "dialect": self._sessions.kw["bind"].dialect.name,
                "items": [],
                "lookahead_months": self._lookahead_months,
            }
        with self._sessions() as session:
            rows = session.execute(
                text(
                    "SELECT child.relname AS name, "
                    "pg_get_expr(child.relpartbound, child.oid) AS bounds "
                    "FROM pg_inherits "
                    "JOIN pg_class parent ON pg_inherits.inhparent = parent.oid "
                    "JOIN pg_class child ON pg_inherits.inhrelid = child.oid "
                    "WHERE parent.relname = 'stock_candles' "
                    "ORDER BY child.relname"
                )
            ).mappings()
            items = [{"name": row["name"], "bounds": row["bounds"]} for row in rows]
        return {
            "status": "ready",
            "dialect": "postgresql",
            "items": items,
            "lookahead_months": self._lookahead_months,
        }
