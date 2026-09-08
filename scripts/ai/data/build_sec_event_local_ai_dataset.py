"""Build a point-in-time SEC 8-K event dataset with later market outcomes."""

import argparse
from bisect import bisect_right
import csv
from datetime import date
from pathlib import Path
import sys
import time

import httpx2


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT))

from app.config import Settings  # noqa: E402
from app.local_ai.financial_features import FINANCIAL_FEATURES  # noqa: E402
from app.local_ai.sec import SecCompanyFactsClient  # noqa: E402
from app.local_ai.sec_event_features import (  # noqa: E402
    SEC_EVENT_FEATURES,
    extract_8k_events,
)
from scripts.ai.data.relabel_specialists_with_market_outcomes import (  # noqa: E402
    OUTCOME_FIELDS,
    _next_outcome,
    _outcome_index,
    _outcomes,
)


def parse_args() -> argparse.Namespace:
    """`parse_args`은(는) 원시 입력을 해석하고 필요한 값을 정규화해 추출합니다."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--symbols", nargs="+", required=True)
    parser.add_argument("--financial-data-dir", type=Path, required=True)
    parser.add_argument("--market-data-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--request-delay", type=float, default=0.15)
    parser.add_argument("--maximum-financial-age-days", type=int, default=550)
    return parser.parse_args()


def _read_financial(path: Path) -> dict[str, tuple[list[date], list[dict]]]:
    """`_read_financial`은(는) 필요한 데이터를 조회해 반환합니다."""

    with path.open("r", encoding="utf-8-sig", newline="") as source:
        rows = list(csv.DictReader(source))
    grouped: dict[str, list[dict]] = {}
    for row in rows:
        grouped.setdefault(str(row["symbol"]).upper(), []).append(row)
    result = {}
    for symbol, values in grouped.items():
        values.sort(key=lambda row: str(row["timestamp"]))
        result[symbol] = (
            [date.fromisoformat(str(row["timestamp"])[:10]) for row in values],
            values,
        )
    return result


def _latest_financial(
    index: dict[str, tuple[list[date], list[dict]]],
    symbol: str,
    event_date: date,
    maximum_age_days: int,
) -> dict | None:
    """`_latest_financial`은(는) 필요한 데이터를 조회해 반환합니다."""

    values = index.get(symbol)
    if values is None:
        return None
    dates, rows = values
    position = bisect_right(dates, event_date) - 1
    if position < 0 or (event_date - dates[position]).days > maximum_age_days:
        return None
    return rows[position]


def main() -> int:
    """`main`은(는) 명령행 인자를 해석하고 이 스크립트의 전체 작업 순서를 실행합니다."""

    args = parse_args()
    if not 30 <= args.maximum_financial_age_days <= 730:
        raise ValueError("maximum financial age must be between 30 and 730 days")
    settings = Settings()
    user_agent = (settings.sec_user_agent or "").strip()
    if not user_agent:
        raise ValueError("SEC_USER_AGENT is required")
    financial_index = _read_financial(args.financial_data_dir / "financial.csv")
    outcomes = _outcomes(args.market_data_dir / "technical.csv")
    outcome_index = _outcome_index(outcomes)
    client = SecCompanyFactsClient(
        user_agent=user_agent,
        base_url=settings.sec_base_url,
    )
    rows = []
    failures = []
    try:
        for raw_symbol in dict.fromkeys(args.symbols):
            symbol = raw_symbol.strip().upper()
            try:
                events = extract_8k_events(client.submissions(symbol))
            except (ValueError, httpx2.HTTPError):
                failures.append(symbol)
                continue
            for event in events:
                event_date = date.fromisoformat(str(event["timestamp"])[:10])
                financial = _latest_financial(
                    financial_index,
                    symbol,
                    event_date,
                    args.maximum_financial_age_days,
                )
                outcome = _next_outcome(
                    outcome_index,
                    {"timestamp": event["timestamp"], "symbol": symbol},
                )
                if financial is None or outcome is None:
                    continue
                rows.append(
                    {
                        "timestamp": event["timestamp"],
                        "symbol": symbol,
                        **{name: financial[name] for name in FINANCIAL_FEATURES},
                        **{name: event[name] for name in SEC_EVENT_FEATURES},
                        **{name: outcome[name] for name in OUTCOME_FIELDS},
                        "outcome_start_timestamp": outcome["timestamp"],
                        "label": int(float(outcome["future_excess_return"]) > 0),
                    }
                )
            time.sleep(max(args.request_delay, 0.1))
    finally:
        client.close()
    rows.sort(key=lambda row: (str(row["timestamp"]), str(row["symbol"])))
    target = args.output_dir / "financial.csv"
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(".csv.tmp")
    with temporary.open("w", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(
            output,
            fieldnames=[
                "timestamp",
                "symbol",
                *FINANCIAL_FEATURES,
                *SEC_EVENT_FEATURES,
                *OUTCOME_FIELDS,
                "outcome_start_timestamp",
                "label",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(target)
    print(
        f"financial_events={len(rows)} "
        f"failed_symbols={','.join(failures) or 'none'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
