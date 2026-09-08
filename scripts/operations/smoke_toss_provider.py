"""Run a bounded Toss market-data smoke check without printing sensitive values."""

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from app.config.settings import Settings  # noqa: E402
from app.providers.toss.provider import TossProvider  # noqa: E402


def parse_args() -> argparse.Namespace:
    """`parse_args`은(는) 원시 입력을 해석하고 필요한 값을 정규화해 추출합니다."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", type=Path, required=True)
    parser.add_argument("--symbol", default="005930")
    return parser.parse_args()


def main() -> int:
    """`main`은(는) 명령행 인자를 해석하고 이 스크립트의 전체 작업 순서를 실행합니다."""

    args = parse_args()
    settings = Settings(_env_file=args.env_file.resolve())
    if not settings.toss_client_id or not settings.toss_client_secret:
        print("provider=toss status=not_configured")
        return 1
    provider = TossProvider.create(
        base_url=settings.toss_base_url,
        client_id=settings.toss_client_id,
        client_secret=settings.toss_client_secret.get_secret_value(),
        timeout_seconds=settings.toss_timeout_seconds,
        max_retries=settings.toss_max_retries,
    )
    try:
        quote = provider.get_quote(args.symbol.upper())
        candles = provider.get_candles(args.symbol.upper(), limit=5)
    except Exception as exc:
        print(f"provider=toss status=failed error_type={type(exc).__name__}")
        return 1
    finally:
        provider.close()
    adjusted = sum(candle.price_basis == "provider_adjusted" for candle in candles)
    if quote.symbol != args.symbol.upper() or not candles or adjusted != len(candles):
        print("provider=toss status=failed error_type=ValidationError")
        return 1
    print(
        f"provider=toss status=ok quote=1 candles={len(candles)} "
        f"provider_adjusted={adjusted} persisted=false"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
