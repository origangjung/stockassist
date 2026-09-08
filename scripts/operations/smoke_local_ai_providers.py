"""Run bounded live smoke checks without printing credentials or response bodies."""

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from app.config.settings import Settings  # noqa: E402
from app.local_ai.finra import FinraShortVolumeClient  # noqa: E402
from app.local_ai.fred import FredClient  # noqa: E402
from app.local_ai.news_api import NewsApiClient  # noqa: E402
from app.local_ai.sec import SecCompanyFactsClient  # noqa: E402


PROVIDERS = ("sec", "fred", "finra", "news")


def parse_args() -> argparse.Namespace:
    """`parse_args`은(는) 원시 입력을 해석하고 필요한 값을 정규화해 추출합니다."""

    parser = argparse.ArgumentParser(description="Smoke-check local AI data providers")
    parser.add_argument("--env-file", type=Path, required=True)
    parser.add_argument("--symbol", default="AAPL")
    parser.add_argument("--provider", choices=("all", *PROVIDERS), default="all")
    return parser.parse_args()


def _feature_count(values: dict[str, float] | None) -> int:
    """`_feature_count`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    return len(values) if values is not None else 0


def _check_sec(settings: Settings, symbol: str) -> int:
    """`_check_sec`은(는) 입력 또는 현재 상태가 규칙을 만족하는지 검증합니다."""

    if not settings.sec_user_agent:
        return _missing("sec")
    client = SecCompanyFactsClient(
        user_agent=settings.sec_user_agent,
        base_url=settings.sec_base_url,
    )
    try:
        return _success("sec", _feature_count(client.latest_features(symbol)))
    finally:
        client.close()


def _check_fred(settings: Settings, _symbol: str) -> int:
    """`_check_fred`은(는) 입력 또는 현재 상태가 규칙을 만족하는지 검증합니다."""

    if not settings.fred_api_key:
        return _missing("fred")
    client = FredClient(
        api_key=settings.fred_api_key.get_secret_value(),
        base_url=settings.fred_base_url,
    )
    try:
        return _success("fred", _feature_count(client.latest_macro_features()))
    finally:
        client.close()


def _check_finra(settings: Settings, symbol: str) -> int:
    """`_check_finra`은(는) 입력 또는 현재 상태가 규칙을 만족하는지 검증합니다."""

    if not settings.finra_client_id or not settings.finra_client_secret:
        return _missing("finra")
    client = FinraShortVolumeClient(
        base_url=settings.finra_api_base_url,
        token_url=settings.finra_token_url,
        client_id=settings.finra_client_id,
        client_secret=settings.finra_client_secret.get_secret_value(),
    )
    try:
        return _success("finra", _feature_count(client.latest_features(symbol)))
    finally:
        client.close()


def _check_news(settings: Settings, symbol: str) -> int:
    """`_check_news`은(는) 입력 또는 현재 상태가 규칙을 만족하는지 검증합니다."""

    if not settings.news_api_key:
        return _missing("news")
    client = NewsApiClient(
        api_key=settings.news_api_key.get_secret_value(),
        base_url=settings.news_api_base_url,
        timeout_seconds=settings.news_timeout_seconds,
        daily_request_limit=settings.news_api_daily_request_limit,
    )
    try:
        return _success("news", _feature_count(client.latest_features(symbol)))
    finally:
        client.close()


def _success(provider: str, features: int) -> int:
    """`_success`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    print(f"provider={provider} status=ok features={features}")
    return 0


def _missing(provider: str) -> int:
    """`_missing`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    print(f"provider={provider} status=not_configured")
    return 1


def main() -> int:
    """`main`은(는) 명령행 인자를 해석하고 이 스크립트의 전체 작업 순서를 실행합니다."""

    args = parse_args()
    settings = Settings(_env_file=args.env_file.resolve())
    checks = {
        "sec": _check_sec,
        "fred": _check_fred,
        "finra": _check_finra,
        "news": _check_news,
    }
    selected = PROVIDERS if args.provider == "all" else (args.provider,)
    failures = 0
    for provider in selected:
        try:
            failures += checks[provider](settings, args.symbol)
        except Exception as exc:
            print(f"provider={provider} status=failed error_type={type(exc).__name__}")
            failures += 1
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
