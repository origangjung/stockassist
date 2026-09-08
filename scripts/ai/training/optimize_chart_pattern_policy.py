"""과거 구간에서만 패턴 필터를 선택해 다음 구간의 적중률을 검증한다."""

import argparse
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
import json
from pathlib import Path
import sys

import httpx2


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))

from app.config import Settings  # noqa: E402
from app.patterns import PatternEngine  # noqa: E402
from app.providers import build_providers  # noqa: E402
from app.providers.contracts import Candle  # noqa: E402
from app.providers.errors import ProviderError  # noqa: E402
from scripts.ai.training.evaluate_chart_patterns import (  # noqa: E402
    OutcomeStats,
    _safe_output,
    _save,
    _symbols,
    _wilson_interval,
)


@dataclass(frozen=True)
class PatternEvent:
    """한 패턴 발생 시점의 관측 특성과 이후 수익률을 보존한다."""

    timestamp: date
    symbol: str
    name: str
    direction: str
    confidence: float
    volume_ratio: float
    trend_gap: float
    absolute_returns: dict[int, float]
    relative_returns: dict[int, float]


FILTERS = (
    "unfiltered",
    "volume_confirmed",
    "trend_aligned",
    "volume_and_trend",
    "high_rule_strength",
)


def parse_args() -> argparse.Namespace:
    """데이터 범위와 중첩 시간 검증 설정을 읽는다."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--symbols", nargs="*")
    parser.add_argument("--benchmark", default="SPY")
    parser.add_argument("--limit", type=int, default=1800)
    parser.add_argument("--horizons", default="1,5,10")
    parser.add_argument("--folds", type=int, default=5)
    parser.add_argument("--minimum-training-samples", type=int, default=200)
    parser.add_argument("--minimum-training-accuracy", type=float, default=0.52)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def extract_events(
    symbol: str,
    candles: list[Candle],
    benchmark: list[Candle],
    horizons: tuple[int, ...],
    *,
    window: int = 60,
) -> list[PatternEvent]:
    """패턴 사건을 연속 중복 없이 만들고 다음 시가 진입 수익률을 연결한다."""

    ordered = sorted(candles, key=lambda item: item.timestamp)
    benchmark_by_date = {item.timestamp.date(): item for item in benchmark}
    engine = PatternEngine()
    previous_names: set[str] = set()
    events: list[PatternEvent] = []
    maximum_horizon = max(horizons)
    for index in range(window - 1, len(ordered) - maximum_horizon):
        patterns = [
            item
            for item in engine.analyze(ordered[index - window + 1 : index + 1])["patterns"]
            if item["direction"] in {"upward", "downward"}
            and float(item["confidence"]) >= 0.68
        ]
        names = {str(item["name"]) for item in patterns}
        fresh = [item for item in patterns if str(item["name"]) not in previous_names]
        previous_names = names
        if not fresh:
            continue
        recent = ordered[max(0, index - 19) : index + 1]
        average_volume = sum(item.volume for item in recent) / len(recent)
        average_close = sum(float(item.close) for item in recent) / len(recent)
        volume_ratio = ordered[index].volume / average_volume if average_volume else 0.0
        trend_gap = float(ordered[index].close) / average_close - 1 if average_close else 0.0
        entry_candle = ordered[index + 1]
        benchmark_entry = benchmark_by_date.get(entry_candle.timestamp.date())
        for pattern in fresh:
            absolute_returns: dict[int, float] = {}
            relative_returns: dict[int, float] = {}
            for horizon in horizons:
                exit_candle = ordered[index + horizon]
                stock_return = float(exit_candle.close) / float(entry_candle.open) - 1
                absolute_returns[horizon] = stock_return
                benchmark_exit = benchmark_by_date.get(exit_candle.timestamp.date())
                if benchmark_entry is not None and benchmark_exit is not None:
                    market_return = (
                        float(benchmark_exit.close) / float(benchmark_entry.open) - 1
                    )
                    relative_returns[horizon] = stock_return - market_return
            events.append(
                PatternEvent(
                    ordered[index].timestamp.date(),
                    symbol,
                    str(pattern["name"]),
                    str(pattern["direction"]),
                    float(pattern["confidence"]),
                    volume_ratio,
                    trend_gap,
                    absolute_returns,
                    relative_returns,
                )
            )
    return events


def _matches(event: PatternEvent, filter_name: str) -> bool:
    """사전에 정한 거래량·추세·규칙 강도 필터를 적용한다."""

    trend_aligned = (
        event.trend_gap > 0 if event.direction == "upward" else event.trend_gap < 0
    )
    if filter_name == "unfiltered":
        return True
    if filter_name == "volume_confirmed":
        return event.volume_ratio >= 1.2
    if filter_name == "trend_aligned":
        return trend_aligned
    if filter_name == "volume_and_trend":
        return event.volume_ratio >= 1.2 and trend_aligned
    if filter_name == "high_rule_strength":
        return event.confidence >= 0.76
    raise ValueError(f"unsupported filter: {filter_name}")


def _accuracy(events: list[PatternEvent], horizon: int, *, relative: bool) -> OutcomeStats:
    """선택된 사건의 방향 적중 통계를 계산한다."""

    stats = OutcomeStats()
    for event in events:
        outcomes = event.relative_returns if relative else event.absolute_returns
        if horizon in outcomes:
            stats.add(event.direction, outcomes[horizon])
    return stats


def walk_forward_policy(
    events: list[PatternEvent],
    *,
    horizons: tuple[int, ...],
    folds: int,
    minimum_training_samples: int,
    minimum_training_accuracy: float,
) -> dict[str, object]:
    """이전 날짜에서 통과한 패턴·필터만 다음 날짜 블록에 적용한다."""

    dates = sorted({event.timestamp for event in events})
    if len(dates) < (folds + 1) * 30:
        raise ValueError("not enough distinct dates for walk-forward policy evaluation")
    boundaries = [dates[len(dates) * index // (folds + 1)] for index in range(1, folds + 1)]
    boundaries.append(date.max)
    aggregate_absolute: dict[int, OutcomeStats] = defaultdict(OutcomeStats)
    aggregate_relative: dict[int, OutcomeStats] = defaultdict(OutcomeStats)
    fold_reports: list[dict[str, object]] = []
    eligible_validation_events = 0
    selected_validation_events = 0

    for fold in range(folds):
        validation_start, validation_end = boundaries[fold], boundaries[fold + 1]
        training = [event for event in events if event.timestamp < validation_start]
        validation = [
            event
            for event in events
            if validation_start <= event.timestamp < validation_end
        ]
        eligible_validation_events += len(validation)
        selections: dict[int, dict[str, str]] = {}
        fold_absolute: dict[int, OutcomeStats] = {}
        fold_relative: dict[int, OutcomeStats] = {}
        for horizon in horizons:
            candidates: list[tuple[tuple[float, float, int], str, str]] = []
            for name in sorted({event.name for event in training}):
                for filter_name in FILTERS:
                    selected = [
                        event
                        for event in training
                        if event.name == name and _matches(event, filter_name)
                    ]
                    stats = _accuracy(selected, horizon, relative=True)
                    if stats.samples < minimum_training_samples:
                        continue
                    accuracy = stats.hits / stats.samples
                    lower, _upper = _wilson_interval(stats.hits, stats.samples)
                    if accuracy >= minimum_training_accuracy and lower > 0.5:
                        candidates.append(
                            ((lower, accuracy, stats.samples), name, filter_name)
                        )
            chosen: dict[str, str] = {}
            for _score, name, filter_name in sorted(candidates, reverse=True):
                chosen.setdefault(name, filter_name)
            selections[horizon] = chosen
            selected = [
                event
                for event in validation
                if event.name in chosen and _matches(event, chosen[event.name])
            ]
            selected_validation_events += len(selected)
            absolute = _accuracy(selected, horizon, relative=False)
            relative = _accuracy(selected, horizon, relative=True)
            fold_absolute[horizon], fold_relative[horizon] = absolute, relative
            _add_stats(aggregate_absolute[horizon], absolute)
            _add_stats(aggregate_relative[horizon], relative)
        fold_reports.append(
            {
                "fold": fold + 1,
                "validation_start": validation_start.isoformat(),
                "validation_end": (
                    None if validation_end == date.max else validation_end.isoformat()
                ),
                "training_events": len(training),
                "validation_events": len(validation),
                "selections": {str(key): value for key, value in selections.items()},
                "absolute": {
                    str(key): value.report() for key, value in fold_absolute.items()
                },
                "relative": {
                    str(key): value.report() for key, value in fold_relative.items()
                },
            }
        )
    return {
        "coverage_ratio": round(
            selected_validation_events / max(eligible_validation_events * len(horizons), 1),
            4,
        ),
        "absolute": {
            str(key): value.report() for key, value in aggregate_absolute.items()
        },
        "relative": {
            str(key): value.report() for key, value in aggregate_relative.items()
        },
        "folds": fold_reports,
    }


def _add_stats(target: OutcomeStats, source: OutcomeStats) -> None:
    """한 fold 통계를 전체 외부 검증 통계에 누적한다."""

    target.samples += source.samples
    target.hits += source.hits
    target.positive_outcomes += source.positive_outcomes
    target.signed_return_sum += source.signed_return_sum


def main() -> int:
    """실제 공급자 데이터를 수집해 선택형 패턴 정책을 검증한다."""

    args = parse_args()
    horizons = tuple(sorted({int(value) for value in args.horizons.split(",")}))
    symbols = _symbols(args)
    provider = build_providers(Settings())[0]
    events: list[PatternEvent] = []
    failed: list[str] = []
    try:
        benchmark = provider.get_candles(args.benchmark.upper(), args.limit)
        for symbol in symbols:
            try:
                events.extend(
                    extract_events(
                        symbol,
                        provider.get_candles(symbol, args.limit),
                        benchmark,
                        horizons,
                    )
                )
            except (ValueError, httpx2.HTTPError, ProviderError):
                failed.append(symbol)
                continue
            print(f"completed={symbol}")
    finally:
        provider.close()
    events.sort(key=lambda event: (event.timestamp, event.symbol, event.name))
    report = {
        "engine_version": PatternEngine.version,
        "method": "nested_expanding_walk_forward_selective_pattern_policy",
        "events": len(events),
        "symbols": len(symbols) - len(failed),
        "failed_symbols": failed,
        "horizons": list(horizons),
        "folds": args.folds,
        "minimum_training_samples": args.minimum_training_samples,
        "minimum_training_accuracy": args.minimum_training_accuracy,
        "result": walk_forward_policy(
            events,
            horizons=horizons,
            folds=args.folds,
            minimum_training_samples=args.minimum_training_samples,
            minimum_training_accuracy=args.minimum_training_accuracy,
        ),
    }
    output = _safe_output(args.output)
    _save(output, report)
    print(json.dumps(report, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
