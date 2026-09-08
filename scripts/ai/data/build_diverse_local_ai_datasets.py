"""Build diversified specialist datasets from point-in-time candidate sources."""

import argparse
from bisect import bisect_left, bisect_right
import csv
from datetime import date, timedelta
import json
from pathlib import Path


MARKET_FIELDS = (
    "return_1d",
    "return_5d",
    "sma_20_gap",
    "volatility_20",
    "volume_ratio",
    "market_return_5d",
    "relative_return_5d",
    "relative_sma_20_gap",
    "sector_return_5d",
    "sector_sma_20_gap",
    "sector_volatility_20",
    "relative_return_5d_sector",
    "relative_trend_sector",
)
MACRO_FIELDS = (
    "vix_level",
    "treasury_10y",
    "yield_curve_10y_2y",
    "fed_funds_rate",
    "broad_dollar_change_20d",
)
LONG_RISK_FIELDS = (
    "return_20d",
    "sma_60_gap",
    "volatility_60",
    "drawdown_60",
    "downside_deviation_60",
    "volatility_ratio_20_60",
)
FINANCIAL_TREND_FIELDS = (
    "revenue_growth_acceleration",
    "net_income_growth_acceleration",
    "margin_change",
    "leverage_change",
)
FINANCIAL_FIELDS = (
    "revenue_growth_yoy",
    "net_income_growth_yoy",
    "net_margin",
    "debt_to_assets",
    "equity_to_assets",
    "asset_growth_yoy",
)
EVENT_BINARY_FIELDS = (
    "event_results",
    "event_guidance_or_disclosure",
    "event_material_agreement",
    "event_acquisition",
    "event_leadership",
    "event_other",
)


def parse_args() -> argparse.Namespace:
    """`parse_args`은(는) 원시 입력을 해석하고 필요한 값을 정규화해 추출합니다."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--technical", type=Path, required=True)
    parser.add_argument("--risk", type=Path, required=True)
    parser.add_argument("--financial-events", type=Path, required=True)
    parser.add_argument("--financial-trends", type=Path, required=True)
    parser.add_argument("--news", type=Path, required=True)
    parser.add_argument("--investor-flow", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def _read(path: Path) -> list[dict[str, str]]:
    """`_read`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    with path.open("r", encoding="utf-8-sig", newline="") as source:
        rows = list(csv.DictReader(source))
    if not rows or not {"timestamp", "symbol", "label"}.issubset(rows[0]):
        raise ValueError(f"{path.name}: invalid specialist dataset")
    return rows


def _day(row: dict[str, str]) -> date:
    """`_day`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    return date.fromisoformat(str(row["timestamp"])[:10])


def _index(rows: list[dict[str, str]]):
    """`_index`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    grouped: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        grouped.setdefault(str(row["symbol"]).strip().upper(), []).append(row)
    result = {}
    for symbol, values in grouped.items():
        values.sort(key=lambda row: str(row["timestamp"]))
        result[symbol] = ([ _day(row) for row in values ], values)
    return result


def _latest(
    index,
    symbol: str,
    target: date,
    *,
    maximum_age_days: int,
    strictly_before: bool = False,
) -> dict[str, str] | None:
    """`_latest`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    values = index.get(symbol.upper())
    if values is None:
        return None
    dates, rows = values
    position = (
        bisect_left(dates, target) - 1
        if strictly_before
        else bisect_right(dates, target) - 1
    )
    if position < 0 or (target - dates[position]).days > maximum_age_days:
        return None
    return rows[position]


def _select(row: dict[str, str] | None, fields: tuple[str, ...], prefix: str = ""):
    """`_select`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    if row is None or any(row.get(name) in {None, ""} for name in fields):
        return None
    return {f"{prefix}{name}": row[name] for name in fields}


def _recent_events(event_index, symbol: str, target: date, days: int = 7):
    """`_recent_events`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    values = event_index.get(symbol.upper())
    if values is None:
        return {
            "recent_sec_event_count_7d": 0.0,
            **{f"recent_sec_{name[6:]}": 0.0 for name in EVENT_BINARY_FIELDS},
        }
    dates, rows = values
    end = bisect_left(dates, target)
    start = bisect_left(dates, target - timedelta(days=days))
    selected = rows[start:end]
    return {
        "recent_sec_event_count_7d": float(len(selected)),
        **{
            f"recent_sec_{name[6:]}": max(
                (float(row[name]) for row in selected), default=0.0
            )
            for name in EVENT_BINARY_FIELDS
        },
    }


def _write(path: Path, rows: list[dict]) -> None:
    """`_write`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    if not rows:
        raise ValueError(f"{path.name}: diversified dataset is empty")
    fieldnames = list(rows[0])
    if any(set(row) != set(fieldnames) for row in rows):
        raise ValueError(f"{path.name}: diversified rows have inconsistent schemas")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".csv.tmp")
    with temporary.open("w", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)


def main() -> int:
    """`main`은(는) 명령행 인자를 해석하고 이 스크립트의 전체 작업 순서를 실행합니다."""

    args = parse_args()
    technical = _read(args.technical)
    risk = _read(args.risk)
    financial = _read(args.financial_events)
    financial_trends = _read(args.financial_trends)
    news = _read(args.news)
    flow = _read(args.investor_flow)
    market_index = _index(technical)
    risk_index = _index(risk)
    event_index = _index(financial)
    financial_index = _index(financial_trends)

    diverse_technical = []
    for row in technical:
        extra = _select(
            _latest(risk_index, row["symbol"], _day(row), maximum_age_days=3),
            LONG_RISK_FIELDS,
            "long_",
        )
        if extra is not None:
            diverse_technical.append({**row, **extra})

    diverse_risk = []
    for row in risk:
        market = _select(
            _latest(market_index, row["symbol"], _day(row), maximum_age_days=3),
            (
                "market_return_5d",
                "relative_return_5d",
                "sector_volatility_20",
                "relative_return_5d_sector",
            ),
            "context_",
        )
        if market is not None:
            diverse_risk.append(
                {**row, **market, **_recent_events(event_index, row["symbol"], _day(row))}
            )

    diverse_financial = []
    for row in financial:
        event_day = _day(row)
        market = _select(
            _latest(
                market_index,
                row["symbol"],
                event_day,
                maximum_age_days=7,
                strictly_before=True,
            ),
            MARKET_FIELDS,
            "pre_event_",
        )
        trends = _select(
            _latest(financial_index, row["symbol"], event_day, maximum_age_days=550),
            FINANCIAL_TREND_FIELDS,
        )
        if market is not None and trends is not None:
            diverse_financial.append({**row, **market, **trends})

    diverse_news = []
    for row in news:
        target = _day(row)
        market = _select(
            _latest(market_index, row["symbol"], target, maximum_age_days=3),
            MARKET_FIELDS,
            "market_",
        )
        financial_values = _select(
            _latest(
                event_index,
                row["symbol"],
                target,
                maximum_age_days=550,
                strictly_before=True,
            ),
            FINANCIAL_FIELDS,
            "financial_",
        )
        if market is not None and financial_values is not None:
            diverse_news.append(
                {
                    **row,
                    **market,
                    **financial_values,
                    **_recent_events(event_index, row["symbol"], target),
                }
            )

    diverse_flow = []
    for row in flow:
        target = _day(row)
        market = _select(
            _latest(market_index, row["symbol"], target, maximum_age_days=3),
            (
                "market_return_5d",
                "relative_return_5d",
                "sector_volatility_20",
                "relative_return_5d_sector",
                *MACRO_FIELDS,
            ),
            "context_",
        )
        risk_values = _select(
            _latest(risk_index, row["symbol"], target, maximum_age_days=3),
            LONG_RISK_FIELDS,
            "risk_",
        )
        if market is not None and risk_values is not None:
            diverse_flow.append(
                {
                    **row,
                    **market,
                    **risk_values,
                    **_recent_events(event_index, row["symbol"], target),
                }
            )

    outputs = {
        "technical": diverse_technical,
        "financial": diverse_financial,
        "news": diverse_news,
        "investor_flow": diverse_flow,
        "risk": diverse_risk,
    }
    for agent, rows in outputs.items():
        rows.sort(key=lambda row: (str(row["timestamp"]), str(row["symbol"])))
        _write(args.output_dir / f"{agent}.csv", rows)
    manifest = {
        "schema_version": 1,
        "status": "candidate",
        "promoted": False,
        "rows": {agent: len(rows) for agent, rows in outputs.items()},
        "sources": {
            "market": str(args.technical),
            "risk": str(args.risk),
            "sec_events": str(args.financial_events),
            "financial_trends": str(args.financial_trends),
            "news": str(args.news),
            "investor_flow": str(args.investor_flow),
        },
        "training_policy": {
            "technical": "base_features_only",
            "financial": "base_features_only",
            "news": "base_features_only_until_history_expands",
            "investor_flow": "base_features_only_until_directional_signal_exists",
            "risk": {
                "status": "candidate",
                "additional_features": list(LONG_RISK_FIELDS),
            },
        },
    }
    (args.output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=True, indent=2), encoding="utf-8"
    )
    print(json.dumps(manifest["rows"], ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
