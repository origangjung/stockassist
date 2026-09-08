"""Build a recent multi-source news dataset aligned to provider candles."""

import argparse
import csv
from datetime import date, timedelta
from pathlib import Path
import shutil
import sys
import time
from typing import Callable

import httpx2


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "backend"))

from app.config import Settings  # noqa: E402
from app.local_ai.gdelt import GdeltNewsClient, canonical_article_url  # noqa: E402
from app.local_ai.news_api import NewsApiClient, article_matches_symbol  # noqa: E402
from app.local_ai.news_features import NEWS_FEATURES, build_news_training_rows  # noqa: E402
from app.local_ai.official_rss import (  # noqa: E402
    OfficialRssNewsClient,
    official_rss_metadata_allowed,
)
from app.providers import build_providers  # noqa: E402
from app.providers.errors import ProviderError  # noqa: E402


def parse_args() -> argparse.Namespace:
    """`parse_args`은(는) 원시 입력을 해석하고 필요한 값을 정규화해 추출합니다."""

    parser = argparse.ArgumentParser(description="Build the news specialist dataset")
    parser.add_argument("--symbols", nargs="+", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=80)
    parser.add_argument("--horizon-days", type=int, default=3)
    parser.add_argument("--window-days", type=int, default=7)
    parser.add_argument("--windows", type=int, default=4)
    parser.add_argument("--minimum-articles", type=int, default=0)
    parser.add_argument("--minimum-absolute-excess-return", type=float, default=0.005)
    parser.add_argument("--benchmark-symbol", default="SPY")
    parser.add_argument(
        "--source",
        choices=("newsapi", "gdelt", "both", "official_rss"),
        help="설정값 NEWS_TRAINING_SOURCE보다 우선할 뉴스 공급자",
    )
    return parser.parse_args()


def build_news_clients(settings: Settings, source: str) -> list[tuple[str, object]]:
    """활성화한 뉴스 공급자 클라이언트를 생성한다."""

    clients: list[tuple[str, object]] = []
    if source in {"newsapi", "both"}:
        api_key = settings.news_api_key.get_secret_value().strip() if settings.news_api_key else ""
        if not api_key and source == "newsapi":
            raise ValueError("NEWS_API_KEY is required for NEWS_TRAINING_SOURCE=newsapi")
        if api_key:
            clients.append(
                (
                    "NewsAPI",
                    NewsApiClient(
                        api_key=api_key,
                        base_url=settings.news_api_base_url,
                        timeout_seconds=settings.news_timeout_seconds,
                        daily_request_limit=settings.news_api_daily_request_limit,
                    ),
                )
            )
    if source in {"gdelt", "both"}:
        clients.append(
            (
                "GDELT",
                GdeltNewsClient(
                    base_url=settings.gdelt_doc_api_url,
                    timeout_seconds=settings.news_timeout_seconds,
                    daily_request_limit=settings.gdelt_daily_request_limit,
                ),
            )
        )
    if settings.official_rss_enabled:
        user_agent = (settings.sec_user_agent or "").strip()
        if user_agent:
            clients.append(
                (
                    "OfficialRSS",
                    OfficialRssNewsClient(
                        user_agent=user_agent,
                        timeout_seconds=settings.news_timeout_seconds,
                        daily_request_limit=settings.official_rss_daily_request_limit,
                    ),
                )
            )
        elif source == "official_rss":
            raise ValueError("SEC_USER_AGENT is required for official RSS collection")
    if not clients:
        raise ValueError("no usable news provider is configured")
    return clients


def article_metadata(symbol: str, provider: str, article: dict) -> dict[str, str]:
    """본문을 제외한 출처 추적용 기사 메타데이터만 반환한다."""

    source = article.get("source")
    publisher = source.get("name") if isinstance(source, dict) else ""
    return {
        "symbol": symbol,
        "provider": str(article.get("provider") or provider),
        "publisher": str(publisher or ""),
        "title": str(article.get("title") or ""),
        "url": canonical_article_url(str(article.get("url") or "")),
        "published_at": str(article.get("publishedAt") or ""),
        "retrieved_at": str(article.get("retrievedAt") or ""),
        "license_class": str(article.get("licenseClass") or provider.casefold()),
    }


def load_saved_articles(path: Path) -> dict[str, list[dict]]:
    """이전에 저장한 메타데이터를 다시 읽어 향후 수익률 라벨 생성에 사용한다."""

    if not path.is_file():
        return {}
    by_symbol: dict[str, list[dict]] = {}
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        for row in csv.DictReader(source):
            symbol = str(row.get("symbol") or "").strip().upper()
            url = canonical_article_url(str(row.get("url") or ""))
            if not symbol or not url or not row.get("published_at"):
                continue
            if not article_metadata_allowed(row):
                continue
            by_symbol.setdefault(symbol, []).append(
                {
                    "title": str(row.get("title") or ""),
                    "description": "",
                    "url": url,
                    "publishedAt": str(row["published_at"]),
                    "source": {"name": str(row.get("publisher") or "")},
                    "provider": str(row.get("provider") or ""),
                    "retrievedAt": str(row.get("retrieved_at") or ""),
                    "licenseClass": str(row.get("license_class") or ""),
                }
            )
    return by_symbol


def article_metadata_allowed(row: dict) -> bool:
    """공식 RSS는 선언된 종목에만 허용하고 다른 공급자 메타데이터는 유지한다."""

    provider = str(row.get("provider") or "").strip().casefold()
    if provider in {"newsapi", "gdelt"}:
        return article_matches_symbol(
            str(row.get("symbol") or ""),
            {
                "title": str(row.get("title") or ""),
                "description": "",
            },
        )
    if provider != "officialrss":
        return True
    try:
        return official_rss_metadata_allowed(
            publisher=str(row.get("publisher") or ""),
            symbol=str(row.get("symbol") or ""),
        )
    except ValueError:
        return False


def merge_csv(
    target: Path,
    rows: list[dict],
    *,
    keys: tuple[str, ...],
    include: Callable[[dict], bool] | None = None,
) -> list[dict]:
    """기존 CSV와 신규 행을 키 기준으로 병합한 뒤 원자적으로 저장한다."""

    existing: list[dict] = []
    if target.is_file():
        with target.open("r", encoding="utf-8-sig", newline="") as source:
            existing = list(csv.DictReader(source))
    candidates = [*existing, *rows]
    if include is not None:
        candidates = [row for row in candidates if include(row)]
    merged = {
        tuple(str(row.get(name, "")) for name in keys): row
        for row in candidates
    }
    result = list(merged.values())
    if not result:
        return []
    fieldnames = list(dict.fromkeys(name for row in result for name in row))
    temporary = target.with_suffix(target.suffix + ".tmp")
    target.parent.mkdir(parents=True, exist_ok=True)
    with temporary.open("w", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(result)
    for attempt in range(5):
        try:
            temporary.replace(target)
            break
        except PermissionError:
            if attempt == 4:
                raise
            time.sleep(0.2 * (attempt + 1))
    return result


def _load_compatible_rows(target: Path, *, horizon_days: int) -> list[dict]:
    """같은 예측 기간의 기존 행만 불러오고, 다른 기간 자료는 별도 보관한다."""

    if not target.is_file():
        return []
    with target.open("r", encoding="utf-8-sig", newline="") as source:
        rows = list(csv.DictReader(source))
    if not rows:
        return []
    horizons = {int(row.get("horizon_days") or 5) for row in rows}
    if len(horizons) != 1:
        raise ValueError(f"mixed prediction horizons in {target}: {sorted(horizons)}")
    existing_horizon = horizons.pop()
    if existing_horizon == horizon_days:
        for row in rows:
            row["horizon_days"] = str(existing_horizon)
        return rows

    archive = target.with_name(f"{target.stem}-legacy-{existing_horizon}d.csv")
    if not archive.exists():
        temporary = archive.with_suffix(archive.suffix + ".tmp")
        shutil.copyfile(target, temporary)
        temporary.replace(archive)
    return []


def main() -> int:
    """`main`은(는) 명령행 인자를 해석하고 이 스크립트의 전체 작업 순서를 실행합니다."""

    args = parse_args()
    settings = Settings()
    selected_source = args.source or settings.news_training_source
    symbols = list(dict.fromkeys(raw.strip().upper() for raw in args.symbols if raw.strip()))
    if not symbols or not 1 <= args.windows <= 12 or not 1 <= args.window_days <= 30:
        raise ValueError("symbols, windows, or window days are outside the supported range")
    projected_requests = len(symbols) * args.windows
    if (
        selected_source in {"newsapi", "both"}
        and projected_requests > settings.news_api_daily_request_limit
    ):
        raise ValueError(
            "projected NewsAPI requests exceed NEWS_API_DAILY_REQUEST_LIMIT"
        )
    if (
        selected_source in {"gdelt", "both"}
        and projected_requests > settings.gdelt_daily_request_limit
    ):
        raise ValueError("projected GDELT requests exceed GDELT_DAILY_REQUEST_LIMIT")
    news_clients = build_news_clients(settings, selected_source)
    stock_provider = build_providers(settings)[0]
    rows: list[dict] = []
    metadata_rows: list[dict] = []
    metadata_target = args.output_dir / "news-articles.csv"
    saved_articles = load_saved_articles(metadata_target)
    failures: list[str] = []
    source_errors: dict[str, int] = {}
    try:
        benchmark_candles = stock_provider.get_candles(
            args.benchmark_symbol.upper(), args.limit
        )
        for symbol in symbols:
            articles_by_url = {
                canonical_article_url(str(article.get("url") or "")): article
                for article in saved_articles.get(symbol, [])
                if canonical_article_url(str(article.get("url") or ""))
            }
            try:
                end = date.today()
                for _ in range(args.windows):
                    start = end - timedelta(days=args.window_days)
                    for provider_name, news in news_clients:
                        try:
                            provider_articles = news.articles(symbol, start=start, end=end)
                        except (ValueError, httpx2.HTTPError):
                            source_errors[provider_name] = source_errors.get(provider_name, 0) + 1
                            continue
                        for article in provider_articles:
                            key = canonical_article_url(str(article.get("url") or ""))
                            if not key:
                                continue
                            articles_by_url[key] = article
                            metadata_rows.append(
                                article_metadata(symbol, provider_name, article)
                            )
                    end = start
                candles = stock_provider.get_candles(symbol, args.limit)
            except (ValueError, httpx2.HTTPError, ProviderError):
                failures.append(symbol)
                continue
            symbol_rows = build_news_training_rows(
                list(articles_by_url.values()),
                candles,
                horizon_days=args.horizon_days,
                minimum_articles=args.minimum_articles,
                minimum_absolute_excess_return=args.minimum_absolute_excess_return,
                benchmark_candles=benchmark_candles,
            )
            rows.extend(
                {
                    **row,
                    "symbol": symbol,
                    "horizon_days": args.horizon_days,
                }
                for row in symbol_rows
            )
    finally:
        for _provider_name, news in news_clients:
            news.close()
        stock_provider.close()
    expected_source_calls = len(symbols) * args.windows * len(news_clients)
    if not rows and sum(source_errors.values()) >= expected_source_calls:
        raise RuntimeError("all configured news provider requests failed")
    rows.sort(key=lambda row: (row["timestamp"], row["symbol"]))
    target = args.output_dir / "news.csv"
    target.parent.mkdir(parents=True, exist_ok=True)
    existing = _load_compatible_rows(target, horizon_days=args.horizon_days)
    merged = {(str(row["timestamp"]), str(row["symbol"])): row for row in [*existing, *rows]}
    rows = sorted(merged.values(), key=lambda row: (row["timestamp"], row["symbol"]))
    base_fieldnames = ["timestamp", "symbol", *NEWS_FEATURES]
    extra_fieldnames = sorted(
        {
            name
            for row in rows
            for name in row
            if name not in {*base_fieldnames, "label"}
        }
    )
    temporary = target.with_suffix(".csv.tmp")
    with temporary.open("w", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(
            output,
            fieldnames=[*base_fieldnames, *extra_fieldnames, "label"],
        )
        writer.writeheader()
        writer.writerows(rows)
    for attempt in range(5):
        try:
            temporary.replace(target)
            break
        except PermissionError:
            if attempt == 4:
                raise
            time.sleep(0.2 * (attempt + 1))
    metadata = merge_csv(
        metadata_target,
        metadata_rows,
        keys=("symbol", "url"),
        include=article_metadata_allowed,
    )
    providers = ",".join(name for name, _client in news_clients)
    print(
        f"news={len(rows)} articles={len(metadata)} providers={providers} "
        f"failed_symbols={','.join(failures) or 'none'} "
        f"source_errors={source_errors or 'none'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
