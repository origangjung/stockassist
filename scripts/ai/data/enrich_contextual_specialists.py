"""Add past-only trend and FRED context to financial and news datasets."""

import argparse
import csv
from datetime import date, timedelta
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "backend"))

from app.config import Settings  # noqa: E402
from app.local_ai.context_features import (  # noqa: E402
    FINANCIAL_TREND_FEATURES,
    NEWS_TREND_FEATURES,
    add_financial_trends,
    add_news_trends,
)
from app.local_ai.fred import FredClient  # noqa: E402
from app.local_ai.macro_features import MACRO_FEATURES, macro_features_at  # noqa: E402


def parse_args() -> argparse.Namespace:
    """`parse_args`은(는) 원시 입력을 해석하고 필요한 값을 정규화해 추출합니다."""

    parser = argparse.ArgumentParser(description="Enrich financial and news datasets")
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument(
        "--dataset", choices=("both", "financial", "news"), default="both"
    )
    return parser.parse_args()


def _read(path: Path) -> list[dict]:
    """`_read`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    with path.open("r", encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def _write(path: Path, rows: list[dict], extra_names: tuple[str, ...]) -> None:
    """`_write`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    fieldnames = list(rows[0])
    for name in extra_names:
        if name not in fieldnames:
            fieldnames.insert(-1, name)
    temporary = path.with_suffix(".csv.tmp")
    with temporary.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)


def main() -> int:
    """`main`은(는) 명령행 인자를 해석하고 이 스크립트의 전체 작업 순서를 실행합니다."""

    args = parse_args()
    output_dir = args.output_dir or args.data_dir
    selected = (
        ("financial", "news")
        if args.dataset == "both"
        else (args.dataset,)
    )
    datasets = [
        (
            name,
            output_dir / f"{name}.csv",
            add_financial_trends(_read(args.data_dir / f"{name}.csv"))
            if name == "financial"
            else add_news_trends(_read(args.data_dir / f"{name}.csv")),
        )
        for name in selected
    ]
    datasets = [item for item in datasets if item[2]]
    if not datasets:
        print("contextual_enrichment=skipped reason=no_source_rows")
        return 0
    all_dates = sorted(
        {
            date.fromisoformat(str(row["timestamp"])[:10])
            for _, _, rows in datasets
            for row in rows
        }
    )
    settings = Settings()
    api_key = settings.fred_api_key.get_secret_value().strip() if settings.fred_api_key else ""
    if not api_key:
        raise ValueError("FRED_API_KEY is required")
    client = FredClient(api_key=api_key, base_url=settings.fred_base_url)
    try:
        observations = client.macro_observations(
            observation_start=min(all_dates) - timedelta(days=60),
            observation_end=max(all_dates),
        )
    finally:
        client.close()
    macro_by_date = {
        day: values
        for day in all_dates
        if (values := macro_features_at(observations, day)) is not None
    }
    for name, path, rows in datasets:
        enriched = []
        for row in rows:
            values = macro_by_date.get(date.fromisoformat(str(row["timestamp"])[:10]))
            if values is not None:
                enriched.append({**row, **values})
        if not enriched:
            raise ValueError(f"{path.name}: no complete point-in-time macro rows")
        trend_names = FINANCIAL_TREND_FEATURES if name == "financial" else NEWS_TREND_FEATURES
        path.parent.mkdir(parents=True, exist_ok=True)
        _write(path, enriched, (*trend_names, *MACRO_FEATURES))
        print(f"{path.name}={len(enriched)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
