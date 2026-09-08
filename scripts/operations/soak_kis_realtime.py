"""KIS WebSocket의 연결, 시세 수신, 지연과 재연결 상태를 안전하게 기록한다."""

import argparse
import asyncio
from collections import Counter
from datetime import UTC, datetime
import json
import os
from pathlib import Path
import re
import sys
import tracemalloc


ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_ROOT = (ROOT / "artifacts" / "realtime-validation").resolve()
sys.path.insert(0, str(ROOT / "backend"))

from app.config import Settings  # noqa: E402
from app.providers import build_providers  # noqa: E402
from app.providers.contracts import Quote  # noqa: E402
from app.realtime.kis import KISStreamingQuoteSource  # noqa: E402


SYMBOL_PATTERN = re.compile(r"^[A-Z0-9.-]{1,16}$")


def parse_args() -> argparse.Namespace:
    """`parse_args`은(는) 원시 입력을 해석하고 필요한 값을 정규화해 추출합니다."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--symbols", nargs="+", default=["005930", "AAPL"])
    parser.add_argument("--duration-seconds", type=int, default=600)
    parser.add_argument("--require-quotes", action="store_true")
    parser.add_argument(
        "--output",
        type=Path,
        default=ARTIFACT_ROOT / "latest.json",
    )
    return parser.parse_args()


def safe_output_path(value: Path) -> Path:
    """`safe_output_path`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    path = value.expanduser().resolve()
    if path.suffix.casefold() != ".json" or not path.is_relative_to(ARTIFACT_ROOT):
        raise ValueError("output must be JSON inside artifacts/realtime-validation")
    return path


def normalized_symbols(values: list[str]) -> list[str]:
    """`normalized_symbols`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    symbols = list(dict.fromkeys(value.strip().upper() for value in values))
    if not symbols or len(symbols) > 10 or any(not SYMBOL_PATTERN.fullmatch(v) for v in symbols):
        raise ValueError("symbols are empty, invalid, or exceed the soak-test limit")
    return symbols


async def run_soak(
    settings: Settings, symbols: list[str], duration_seconds: int
) -> dict[str, object]:
    """`run_soak`은(는) 비동기로 해당 작업의 전체 처리 흐름을 실행하고 결과를 반환합니다."""

    if not 5 <= duration_seconds <= 14_400:
        raise ValueError("duration must be between 5 seconds and 4 hours")
    app_key = settings.kis_app_key.get_secret_value().strip() if settings.kis_app_key else ""
    app_secret = (
        settings.kis_app_secret.get_secret_value().strip() if settings.kis_app_secret else ""
    )
    if not app_key or not app_secret:
        raise ValueError("KIS_APP_KEY and KIS_APP_SECRET are required")
    resolver = build_providers(settings)[0]
    source = KISStreamingQuoteSource(
        base_url=settings.kis_base_url,
        websocket_url=settings.kis_ws_url,
        app_key=app_key,
        app_secret=app_secret,
        resolver=resolver,
        timeout_seconds=settings.kis_timeout_seconds,
        reconnect_max_seconds=settings.kis_ws_reconnect_max_seconds,
    )
    counts: Counter[str] = Counter()
    maximum_lag = 0.0
    started_at = datetime.now(UTC)

    async def publish(quote: Quote) -> None:
        """`publish`은(는) 비동기로 연결 또는 메시지 전달 생명주기를 관리합니다."""

        nonlocal maximum_lag
        counts[quote.symbol] += 1
        if quote.as_of is not None:
            maximum_lag = max(maximum_lag, (datetime.now(UTC) - quote.as_of).total_seconds())

    tracemalloc.start()
    approval_ok = False
    try:
        await source.get_approval_key()
        approval_ok = True
        await source.start(publish)
        for symbol in symbols:
            await source.subscribe(symbol)
        await asyncio.sleep(duration_seconds)
    finally:
        diagnostics = source.diagnostics()
        await source.stop()
        resolver.close()
        _, peak_memory = tracemalloc.get_traced_memory()
        tracemalloc.stop()
    total = sum(counts.values())
    return {
        "status": "quotes_received" if total else "connected_without_quotes",
        "approval_ok": approval_ok,
        "started_at": started_at.isoformat(),
        "completed_at": datetime.now(UTC).isoformat(),
        "duration_seconds": duration_seconds,
        "symbols": symbols,
        "quote_counts": dict(counts),
        "total_quotes": total,
        "maximum_quote_lag_seconds": round(maximum_lag, 3) if total else None,
        "peak_traced_memory_bytes": peak_memory,
        "diagnostics": diagnostics,
        "contains_credentials": False,
    }


def save_report(path: Path, report: dict[str, object]) -> None:
    """`save_report`은(는) 데이터를 저장하거나 기존 상태에 추가합니다."""

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(report, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def main() -> int:
    """`main`은(는) 명령행 인자를 해석하고 이 스크립트의 전체 작업 순서를 실행합니다."""

    args = parse_args()
    symbols = normalized_symbols(args.symbols)
    report = asyncio.run(run_soak(Settings(), symbols, args.duration_seconds))
    save_report(safe_output_path(args.output), report)
    print(json.dumps(report, ensure_ascii=True))
    return 2 if args.require_quotes and not report["total_quotes"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
