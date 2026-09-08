"""공식 기관과 발행사가 배포하는 RSS 메타데이터를 안전하게 수집한다."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from email.utils import parsedate_to_datetime
from time import monotonic
from urllib.parse import urlsplit
from xml.etree import ElementTree

import httpx2

from app.local_ai.gdelt import canonical_article_url
from app.local_ai.http_security import (
    DailyRequestBudget,
    validate_https_endpoint,
    validate_symbol,
)


MAX_RSS_RESPONSE_BYTES = 2 * 1024 * 1024
ALLOWED_RSS_HOSTS = frozenset(
    {"www.sec.gov", "www.federalreserve.gov", "www.apple.com"}
)


@dataclass(frozen=True)
class OfficialFeed:
    """허용된 공식 RSS 주소와 적용할 종목 범위를 선언한다."""

    publisher: str
    url: str
    symbols: frozenset[str]


OFFICIAL_FEEDS = (
    OfficialFeed(
        "U.S. SEC",
        "https://www.sec.gov/news/pressreleases.rss",
        frozenset({"SPY"}),
    ),
    OfficialFeed(
        "Federal Reserve Board",
        "https://www.federalreserve.gov/feeds/press_all.xml",
        frozenset({"SPY"}),
    ),
    OfficialFeed(
        "Apple Newsroom",
        "https://www.apple.com/newsroom/rss-feed.rss",
        frozenset({"AAPL"}),
    ),
)


class OfficialRssNewsClient:
    """화이트리스트 RSS에서 기사 본문을 제외한 공개 메타데이터만 읽는다."""

    def __init__(
        self,
        *,
        user_agent: str,
        timeout_seconds: float = 30.0,
        cache_seconds: float = 900.0,
        daily_request_limit: int = 12,
        feeds: tuple[OfficialFeed, ...] = OFFICIAL_FEEDS,
        transport: httpx2.BaseTransport | None = None,
    ) -> None:
        if not user_agent.strip():
            raise ValueError("official RSS collection requires a contact user agent")
        self._feeds = tuple(_validate_feed(feed) for feed in feeds)
        self._http = httpx2.Client(
            timeout=timeout_seconds,
            transport=transport,
            headers={"User-Agent": user_agent.strip(), "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml"},
        )
        self._budget = DailyRequestBudget(daily_request_limit)
        self._cache_seconds = cache_seconds
        self._cache: tuple[list[tuple[dict, frozenset[str]]], float] | None = None

    def articles(self, symbol: str, *, start: date, end: date) -> list[dict]:
        """공개 시각과 종목 범위가 요청 구간에 맞는 RSS 항목만 반환한다."""

        normalized = validate_symbol(symbol)
        if end < start:
            raise ValueError("RSS end date must not precede start date")
        return [
            article
            for article, symbols in self._entries()
            if normalized in symbols
            and start <= datetime.fromisoformat(article["publishedAt"]).date() <= end
        ]

    def _entries(self) -> list[tuple[dict, frozenset[str]]]:
        """피드당 한 번만 요청하고 일시적 장애도 캐시해 반복 호출을 막는다."""

        if self._cache and self._cache[1] > monotonic():
            return self._cache[0]
        entries: list[tuple[dict, frozenset[str]]] = []
        failures = 0
        for feed in self._feeds:
            try:
                self._budget.consume(provider="OfficialRSS")
                response = self._http.get(feed.url)
                entries.extend(
                    (article, feed.symbols)
                    for article in _parse_feed_response(response, publisher=feed.publisher)
                )
            except (ValueError, httpx2.HTTPError):
                failures += 1
        self._cache = (entries, monotonic() + self._cache_seconds)
        if failures == len(self._feeds):
            raise ValueError("all official RSS feeds failed")
        return entries

    def close(self) -> None:
        """HTTP 연결 자원을 반환한다."""

        self._http.close()


def _validate_feed(feed: OfficialFeed) -> OfficialFeed:
    """코드에 등록된 HTTPS 피드가 공식 허용 호스트 안에 있는지 검사한다."""

    endpoint = validate_https_endpoint(feed.url, name="OFFICIAL_RSS_URL")
    if (urlsplit(endpoint).hostname or "").casefold() not in ALLOWED_RSS_HOSTS:
        raise ValueError("official RSS host is not allowlisted")
    if not feed.symbols:
        raise ValueError("official RSS feed requires an explicit symbol scope")
    symbols = frozenset(validate_symbol(symbol) for symbol in feed.symbols)
    return OfficialFeed(feed.publisher.strip(), endpoint, symbols)


def official_rss_metadata_allowed(*, publisher: str, symbol: str) -> bool:
    """저장된 공식 RSS 메타데이터가 선언된 종목 범위에 속하는지 확인한다."""

    normalized_publisher = publisher.strip().casefold()
    normalized_symbol = validate_symbol(symbol)
    return any(
        feed.publisher.casefold() == normalized_publisher
        and normalized_symbol in feed.symbols
        for feed in OFFICIAL_FEEDS
    )


def _parse_feed_response(response: httpx2.Response, *, publisher: str) -> list[dict]:
    """크기가 제한되고 외부 엔티티가 없는 RSS/Atom 응답만 파싱한다."""

    if not 200 <= response.status_code < 300:
        raise ValueError(f"OfficialRSS request failed with HTTP {response.status_code}")
    declared = response.headers.get("content-length")
    if declared and int(declared) > MAX_RSS_RESPONSE_BYTES:
        raise ValueError("OfficialRSS response exceeds the size limit")
    content = bytes(response.content)
    if len(content) > MAX_RSS_RESPONSE_BYTES:
        raise ValueError("OfficialRSS response exceeds the size limit")
    lowered = content.lower()
    if b"<!doctype" in lowered or b"<!entity" in lowered:
        raise ValueError("OfficialRSS XML declarations are not allowed")
    try:
        root = ElementTree.fromstring(content)
    except ElementTree.ParseError as exc:
        raise ValueError("OfficialRSS response is not valid XML") from exc
    retrieved_at = datetime.now(timezone.utc).isoformat()
    articles = []
    for item in root.iter():
        if _local_name(item.tag) not in {"item", "entry"}:
            continue
        title = _child_text(item, "title")
        url = canonical_article_url(_entry_link(item))
        published = _entry_date(item)
        if not title or not url or published is None:
            continue
        articles.append(
            {
                "title": title,
                "description": "",
                "url": url,
                "publishedAt": published.astimezone(timezone.utc).isoformat(),
                "source": {"name": publisher},
                "provider": "OfficialRSS",
                "retrievedAt": retrieved_at,
                "licenseClass": "publisher-official-rss-metadata",
            }
        )
    return articles


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].casefold()


def _child_text(item: ElementTree.Element, name: str) -> str:
    for child in item:
        if _local_name(child.tag) == name:
            return " ".join("".join(child.itertext()).split())
    return ""


def _entry_link(item: ElementTree.Element) -> str:
    for child in item:
        if _local_name(child.tag) != "link":
            continue
        if child.attrib.get("rel", "alternate") == "alternate" and child.attrib.get("href"):
            return child.attrib["href"]
        if child.text:
            return child.text.strip()
    return ""


def _entry_date(item: ElementTree.Element) -> datetime | None:
    raw = next(
        (
            _child_text(item, name)
            for name in ("pubdate", "published", "updated")
            if _child_text(item, name)
        ),
        "",
    )
    if not raw:
        return None
    try:
        parsed = parsedate_to_datetime(raw)
    except (TypeError, ValueError):
        try:
            parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed
