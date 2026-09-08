"""Add point-in-time FINRA short-interest features to an existing flow dataset."""

import argparse
import csv
from datetime import date
from pathlib import Path
import sys
import time

import httpx2


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "backend"))

from app.config import Settings  # noqa: E402
from app.local_ai.finra import FinraShortVolumeClient  # noqa: E402
from app.local_ai.flow_features import (  # noqa: E402
    SHORT_INTEREST_FEATURES,
    short_interest_features_by_date,
)
from app.providers.errors import ProviderError  # noqa: E402


def parse_args() -> argparse.Namespace:
    """`parse_args`은(는) 원시 입력을 해석하고 필요한 값을 정규화해 추출합니다."""

    parser = argparse.ArgumentParser(description="Enrich flow data with short interest")
    parser.add_argument("--data-dir", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    """`main`은(는) 명령행 인자를 해석하고 이 스크립트의 전체 작업 순서를 실행합니다."""

    args = parse_args()
    path = args.data_dir / "investor_flow.csv"
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        rows = list(csv.DictReader(source))
    settings = Settings()
    client_id = (settings.finra_client_id or "").strip()
    client_secret = (
        settings.finra_client_secret.get_secret_value().strip()
        if settings.finra_client_secret
        else ""
    )
    if not client_id or not client_secret:
        raise ValueError("FINRA_CLIENT_ID and FINRA_CLIENT_SECRET are required")
    client = FinraShortVolumeClient(
        base_url=settings.finra_api_base_url,
        token_url=settings.finra_token_url,
        client_id=client_id,
        client_secret=client_secret,
    )
    enriched = []
    failures: list[str] = []
    try:
        for symbol in sorted({str(row["symbol"]) for row in rows}):
            symbol_rows = [row for row in rows if row["symbol"] == symbol]
            dates = [date.fromisoformat(str(row["timestamp"])[:10]) for row in symbol_rows]
            try:
                records = client.short_interest_records(symbol)
            except (ValueError, httpx2.HTTPError, ProviderError):
                failures.append(symbol)
                continue
            features = short_interest_features_by_date(records, dates)
            for row, trade_date in zip(symbol_rows, dates, strict=True):
                if trade_date in features:
                    enriched.append({**row, **features[trade_date]})
    finally:
        client.close()
    enriched.sort(key=lambda row: (row["timestamp"], row["symbol"]))
    fieldnames = list(rows[0])
    for name in SHORT_INTEREST_FEATURES:
        if name not in fieldnames:
            fieldnames.insert(-1, name)
    temporary = path.with_suffix(".csv.tmp")
    with temporary.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(enriched)
    for attempt in range(5):
        try:
            temporary.replace(path)
            break
        except PermissionError:
            if attempt == 4:
                raise
            time.sleep(0.2 * (attempt + 1))
    print(
        f"investor_flow.csv={len(enriched)} "
        f"failed_symbols={','.join(failures) or 'none'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
