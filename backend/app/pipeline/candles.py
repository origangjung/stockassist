from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from enum import Enum

from app.providers.contracts import Candle


class CandleInterval(str, Enum):
    DAY = "1d"
    WEEK = "1w"
    MONTH = "1M"


class QualitySeverity(str, Enum):
    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True)
class DataQualityLog:
    rule: str
    severity: QualitySeverity
    message: str
    timestamp: datetime | None = None


@dataclass(frozen=True)
class DataQualityLogRecord:
    log_id: int
    symbol: str
    rule: str
    severity: QualitySeverity
    message: str
    observed_at: datetime | None
    created_at: datetime


@dataclass(frozen=True)
class PipelineResult:
    raw_count: int
    cleaned_candles: list[Candle]
    quality_logs: list[DataQualityLog]
    aggregation_version: str = "2026.2"


MIN_SUSPICIOUS_MISSING_BUSINESS_DAYS = 5


def _business_days_between(start: date, end: date) -> int:
    current = start + timedelta(days=1)
    count = 0
    while current < end:
        if current.weekday() < 5:
            count += 1
        current += timedelta(days=1)
    return count


def _detect_suspicious_daily_gaps(candles: list[Candle]) -> list[DataQualityLog]:
    timestamps = sorted({candle.timestamp for candle in candles})
    logs: list[DataQualityLog] = []
    for previous, current in zip(timestamps, timestamps[1:], strict=False):
        missing_business_days = _business_days_between(previous.date(), current.date())
        if missing_business_days < MIN_SUSPICIOUS_MISSING_BUSINESS_DAYS:
            continue
        logs.append(
            DataQualityLog(
                "missing_daily_candles",
                QualitySeverity.WARNING,
                (
                    f"{previous.date().isoformat()}~{current.date().isoformat()} 사이에 "
                    f"최소 {missing_business_days}영업일의 캔들 공백이 감지되었습니다."
                ),
                current,
            )
        )
    return logs


def validate_candles(candles: list[Candle]) -> list[DataQualityLog]:
    """Validate OHLCV invariants without silently altering source data."""
    logs: list[DataQualityLog] = []
    timestamps: set[datetime] = set()
    previous: datetime | None = None
    price_bases = {candle.price_basis for candle in candles}
    if len(price_bases) > 1:
        logs.append(
            DataQualityLog(
                "mixed_price_basis",
                QualitySeverity.ERROR,
                "서로 다른 가격 보정 기준의 캔들을 함께 처리할 수 없습니다.",
            )
        )
    for candle in candles:
        if candle.timestamp in timestamps:
            logs.append(
                DataQualityLog(
                    "duplicate_timestamp",
                    QualitySeverity.ERROR,
                    "중복 캔들이 감지되었습니다.",
                    candle.timestamp,
                )
            )
        timestamps.add(candle.timestamp)
        if candle.low > min(candle.open, candle.close) or candle.high < max(
            candle.open, candle.close
        ):
            logs.append(
                DataQualityLog(
                    "invalid_ohlc",
                    QualitySeverity.ERROR,
                    "OHLC 가격 범위가 유효하지 않습니다.",
                    candle.timestamp,
                )
            )
        if candle.volume < 0:
            logs.append(
                DataQualityLog(
                    "negative_volume",
                    QualitySeverity.ERROR,
                    "거래량은 음수일 수 없습니다.",
                    candle.timestamp,
                )
            )
        if previous and candle.timestamp <= previous:
            logs.append(
                DataQualityLog(
                    "out_of_order",
                    QualitySeverity.ERROR,
                    "캔들 시각이 오름차순이 아닙니다.",
                    candle.timestamp,
                )
            )
        previous = candle.timestamp
    return [*logs, *_detect_suspicious_daily_gaps(candles)]


def clean_candles(candles: list[Candle]) -> list[Candle]:
    """Keep the first valid record per timestamp and exclude invalid OHLCV records."""
    cleaned: list[Candle] = []
    seen: set[datetime] = set()
    for candle in sorted(candles, key=lambda value: value.timestamp):
        valid = (
            candle.low <= min(candle.open, candle.close)
            and candle.high >= max(candle.open, candle.close)
            and candle.volume >= 0
        )
        if candle.timestamp not in seen and valid:
            cleaned.append(candle)
            seen.add(candle.timestamp)
    return cleaned


def aggregate_candles(candles: list[Candle], interval: CandleInterval) -> list[Candle]:
    if interval == CandleInterval.DAY:
        return candles
    price_bases = {candle.price_basis for candle in candles}
    if len(price_bases) > 1:
        raise ValueError("Cannot aggregate candles with mixed price bases")
    groups: dict[tuple[int, int], list[Candle]] = defaultdict(list)
    for candle in candles:
        if interval == CandleInterval.WEEK:
            iso = candle.timestamp.isocalendar()
            key = (iso.year, iso.week)
        else:
            key = (candle.timestamp.year, candle.timestamp.month)
        groups[key].append(candle)

    aggregated: list[Candle] = []
    for group in groups.values():
        ordered = sorted(group, key=lambda value: value.timestamp)
        aggregated.append(
            Candle(
                timestamp=ordered[0].timestamp,
                open=ordered[0].open,
                high=max(value.high for value in ordered),
                low=min(value.low for value in ordered),
                close=ordered[-1].close,
                volume=sum(value.volume for value in ordered),
                price_basis=ordered[0].price_basis,
            )
        )
    return aggregated


class CandlePipeline:
    def process(
        self, raw_candles: list[Candle], interval: CandleInterval = CandleInterval.DAY
    ) -> PipelineResult:
        logs = validate_candles(raw_candles)
        cleaned = (
            []
            if any(log.rule == "mixed_price_basis" for log in logs)
            else clean_candles(raw_candles)
        )
        return PipelineResult(len(raw_candles), aggregate_candles(cleaned, interval), logs)
