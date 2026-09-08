"""과거 OHLCV에서 차트 패턴의 미래 방향 적중률을 시점 누출 없이 평가한다."""

import argparse
from collections import defaultdict
from dataclasses import dataclass
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import sys

import httpx2


ROOT = Path(__file__).resolve().parents[3]
ARTIFACT_ROOT = (ROOT / "artifacts").resolve()
sys.path.insert(0, str(ROOT / "backend"))

from app.config import Settings  # noqa: E402
from app.patterns import PatternEngine  # noqa: E402
from app.providers import build_providers  # noqa: E402
from app.providers.contracts import Candle  # noqa: E402
from app.providers.errors import ProviderError  # noqa: E402


@dataclass
class OutcomeStats:
    """한 패턴·평가기간에서 적중 수와 방향 조정 수익률을 누적한다."""

    samples: int = 0
    hits: int = 0
    positive_outcomes: int = 0
    signed_return_sum: float = 0.0

    def add(self, direction: str, future_return: float) -> None:
        """패턴 방향과 실제 수익률 한 건을 누적한다."""

        expected_sign = 1 if direction == "upward" else -1
        self.samples += 1
        self.hits += int(future_return * expected_sign > 0)
        self.positive_outcomes += int(future_return > 0)
        self.signed_return_sum += future_return * expected_sign

    def report(self) -> dict[str, object]:
        """적중률, 단순 방향 기준선, Wilson 95% 신뢰구간을 반환한다."""

        if not self.samples:
            return {"samples": 0}
        accuracy = self.hits / self.samples
        positive_rate = self.positive_outcomes / self.samples
        lower, upper = _wilson_interval(self.hits, self.samples)
        return {
            "samples": self.samples,
            "hits": self.hits,
            "accuracy": round(accuracy, 4),
            "baseline_accuracy": round(max(positive_rate, 1 - positive_rate), 4),
            "baseline_improvement": round(
                accuracy - max(positive_rate, 1 - positive_rate), 4
            ),
            "average_direction_adjusted_return": round(
                self.signed_return_sum / self.samples, 6
            ),
            "confidence_interval_95": [round(lower, 4), round(upper, 4)],
        }


def parse_args() -> argparse.Namespace:
    """평가 종목, 기간, 공급자 조회량과 결과 경로를 읽는다."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--symbols", nargs="*")
    parser.add_argument("--benchmark", default="SPY")
    parser.add_argument("--limit", type=int, default=1800)
    parser.add_argument("--horizons", default="1,5,10")
    parser.add_argument("--minimum-confidence", type=float, default=0.68)
    parser.add_argument("--window", type=int, default=60)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def evaluate_symbol(
    candles: list[Candle],
    benchmark: list[Candle],
    *,
    horizons: tuple[int, ...],
    minimum_confidence: float,
    window: int,
) -> tuple[
    dict[tuple[str, str, int], OutcomeStats],
    dict[tuple[str, str, int], OutcomeStats],
    dict[str, int],
]:
    """한 종목에서 연속 중복을 제거한 패턴 사건과 미래 결과를 계산한다."""

    ordered = sorted(candles, key=lambda item: item.timestamp)
    benchmark_by_date = {item.timestamp.date(): item for item in benchmark}
    engine = PatternEngine()
    absolute: dict[tuple[str, str, int], OutcomeStats] = defaultdict(OutcomeStats)
    relative: dict[tuple[str, str, int], OutcomeStats] = defaultdict(OutcomeStats)
    neutral_events: dict[str, int] = defaultdict(int)
    previous_names: set[str] = set()
    maximum_horizon = max(horizons)

    for index in range(min(window - 1, len(ordered)), len(ordered) - maximum_horizon):
        visible = ordered[max(0, index - window + 1) : index + 1]
        patterns = [
            item
            for item in engine.analyze(visible)["patterns"]
            if float(item["confidence"]) >= minimum_confidence
        ]
        current_names = {str(item["name"]) for item in patterns}
        events = [item for item in patterns if str(item["name"]) not in previous_names]
        previous_names = current_names
        for pattern in events:
            name, direction = str(pattern["name"]), str(pattern["direction"])
            if direction == "neutral":
                neutral_events[name] += 1
                continue
            if direction not in {"upward", "downward"}:
                continue
            entry = float(ordered[index + 1].open)
            benchmark_entry_candle = benchmark_by_date.get(ordered[index + 1].timestamp.date())
            for horizon in horizons:
                exit_candle = ordered[index + horizon]
                future_return = float(exit_candle.close) / entry - 1
                absolute[(name, direction, horizon)].add(direction, future_return)
                benchmark_exit = benchmark_by_date.get(exit_candle.timestamp.date())
                if benchmark_entry_candle is not None and benchmark_exit is not None:
                    benchmark_return = (
                        float(benchmark_exit.close) / float(benchmark_entry_candle.open) - 1
                    )
                    relative[(name, direction, horizon)].add(
                        direction,
                        future_return - benchmark_return,
                    )
    return absolute, relative, neutral_events


def _merge(
    target: dict[tuple[str, str, int], OutcomeStats],
    source: dict[tuple[str, str, int], OutcomeStats],
) -> None:
    """종목별 통계를 전체 통계에 더한다."""

    for key, value in source.items():
        aggregate = target[key]
        aggregate.samples += value.samples
        aggregate.hits += value.hits
        aggregate.positive_outcomes += value.positive_outcomes
        aggregate.signed_return_sum += value.signed_return_sum


def _reports(stats: dict[tuple[str, str, int], OutcomeStats]) -> dict[str, object]:
    """패턴별 통계와 모든 방향성 패턴 통계를 JSON 구조로 만든다."""

    patterns: dict[str, dict[str, object]] = {}
    overall: dict[int, OutcomeStats] = defaultdict(OutcomeStats)
    for (name, direction, horizon), values in sorted(stats.items()):
        patterns.setdefault(name, {"direction": direction, "horizons": {}})
        horizons = patterns[name]["horizons"]
        assert isinstance(horizons, dict)
        horizons[str(horizon)] = values.report()
        aggregate = overall[horizon]
        aggregate.samples += values.samples
        aggregate.hits += values.hits
        aggregate.positive_outcomes += values.positive_outcomes
        aggregate.signed_return_sum += values.signed_return_sum
    return {
        "overall": {str(key): value.report() for key, value in sorted(overall.items())},
        "patterns": patterns,
    }


def _wilson_interval(hits: int, samples: int) -> tuple[float, float]:
    """이항 적중률의 Wilson 95% 신뢰구간을 계산한다."""

    if samples <= 0:
        return 0.0, 0.0
    z = 1.959963984540054
    probability = hits / samples
    denominator = 1 + z * z / samples
    center = (probability + z * z / (2 * samples)) / denominator
    margin = z * math.sqrt(
        probability * (1 - probability) / samples + z * z / (4 * samples * samples)
    ) / denominator
    return max(0.0, center - margin), min(1.0, center + margin)


def _symbols(args: argparse.Namespace) -> list[str]:
    """명시 종목 또는 기존 데이터 manifest에서 검증된 종목을 읽는다."""

    selected = [str(value).strip().upper() for value in (args.symbols or []) if value.strip()]
    if args.manifest:
        payload = json.loads(args.manifest.read_text(encoding="utf-8"))
        selected.extend(str(value).upper() for value in (payload.get("files") or {}))
    result = sorted(set(selected) - {args.benchmark.upper()})
    if not result:
        raise ValueError("at least one evaluation symbol is required")
    return result


def _safe_output(path: Path) -> Path:
    """검증 보고서는 Git 제외 artifacts 경로의 JSON에만 기록한다."""

    resolved = path.expanduser().resolve()
    if resolved.suffix.casefold() != ".json" or not resolved.is_relative_to(ARTIFACT_ROOT):
        raise ValueError("output must be JSON inside artifacts")
    return resolved


def _save(path: Path, payload: dict[str, object]) -> None:
    """완성된 보고서만 보이도록 임시 파일을 원자 교체한다."""

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        with temporary.open("x", encoding="utf-8") as stream:
            json.dump(payload, stream, ensure_ascii=True, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def main() -> int:
    """공급자 OHLCV를 순회해 패턴 성공률 보고서를 생성한다."""

    args = parse_args()
    horizons = tuple(sorted({int(value) for value in args.horizons.split(",")}))
    if not horizons or min(horizons) < 1 or max(horizons) > 60:
        raise ValueError("horizons must stay between 1 and 60")
    if not 0.0 <= args.minimum_confidence <= 1.0 or not 21 <= args.window <= 252:
        raise ValueError("pattern evaluation settings are invalid")
    symbols = _symbols(args)
    provider = build_providers(Settings())[0]
    absolute: dict[tuple[str, str, int], OutcomeStats] = defaultdict(OutcomeStats)
    relative: dict[tuple[str, str, int], OutcomeStats] = defaultdict(OutcomeStats)
    neutral_events: dict[str, int] = defaultdict(int)
    completed: list[str] = []
    failed: list[str] = []
    try:
        benchmark = provider.get_candles(args.benchmark.upper(), args.limit)
        for symbol in symbols:
            try:
                candles = provider.get_candles(symbol, args.limit)
                symbol_absolute, symbol_relative, symbol_neutral = evaluate_symbol(
                    candles,
                    benchmark,
                    horizons=horizons,
                    minimum_confidence=args.minimum_confidence,
                    window=args.window,
                )
            except (ValueError, httpx2.HTTPError, ProviderError):
                failed.append(symbol)
                continue
            _merge(absolute, symbol_absolute)
            _merge(relative, symbol_relative)
            for name, count in symbol_neutral.items():
                neutral_events[name] += count
            completed.append(symbol)
            print(f"completed={symbol}")
    finally:
        provider.close()

    report = {
        "engine_version": PatternEngine.version,
        "evaluation_method": "signal_at_close_entry_next_open_episode_deduplicated",
        "benchmark": args.benchmark.upper(),
        "requested_symbols": len(symbols),
        "completed_symbols": completed,
        "failed_symbols": failed,
        "limit": args.limit,
        "window": args.window,
        "horizons": list(horizons),
        "minimum_confidence": args.minimum_confidence,
        "absolute_return": _reports(absolute),
        "benchmark_excess_return": _reports(relative),
        "neutral_pattern_events": dict(sorted(neutral_events.items())),
    }
    report["content_sha256"] = sha256(
        json.dumps(report, sort_keys=True, ensure_ascii=True).encode()
    ).hexdigest()
    output = _safe_output(args.output)
    _save(output, report)
    print(json.dumps(report, ensure_ascii=True, indent=2))
    return 0 if completed else 2


if __name__ == "__main__":
    raise SystemExit(main())
