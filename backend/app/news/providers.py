from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import quote_plus
from xml.etree import ElementTree

import httpx2

from app.config import Settings
from app.news.contracts import NewsArticle, NewsProvider
from app.providers.errors import ProviderUnavailableError


class MockNewsProvider(NewsProvider):
    name = "mock"

    def latest(self, symbol: str, *, limit: int) -> list[NewsArticle]:
        now = datetime.now(timezone.utc)
        articles = [
            NewsArticle(
                symbol,
                "Mock earnings growth outlook remains constructive",
                "https://example.invalid/news/1",
                "Mock Wire",
                now - timedelta(hours=3),
                "Offline development fixture.",
            ),
            NewsArticle(
                symbol,
                "Mock market report flags valuation risk",
                "https://example.invalid/news/2",
                "Mock Wire",
                now - timedelta(hours=18),
                "Offline development fixture.",
            ),
        ]
        return articles[:limit]


class RssNewsProvider(NewsProvider):
    name = "rss"

    def __init__(self, client: httpx2.Client, search_url: str) -> None:
        self._client = client
        self._search_url = search_url

    @classmethod
    def create(
        cls,
        *,
        search_url: str,
        timeout_seconds: float = 10,
        transport: httpx2.BaseTransport | None = None,
    ) -> "RssNewsProvider":
        return cls(httpx2.Client(timeout=timeout_seconds, transport=transport), search_url)

    def latest(self, symbol: str, *, limit: int) -> list[NewsArticle]:
        try:
            response = self._client.get(self._search_url.format(query=quote_plus(symbol)))
            response.raise_for_status()
            root = ElementTree.fromstring(response.content)
        except (httpx2.RequestError, ElementTree.ParseError) as exc:
            raise ProviderUnavailableError(
                "News RSS feed is unavailable", code="news-rss-unavailable"
            ) from exc
        articles: list[NewsArticle] = []
        for item in root.findall("./channel/item")[:limit]:
            title = _text(item, "title")
            url = _text(item, "link")
            if not title or not url:
                continue
            published_at = _published_at(_text(item, "pubDate"))
            articles.append(
                NewsArticle(
                    symbol=symbol,
                    title=title,
                    url=url,
                    publisher=_text(item, "source") or "RSS",
                    published_at=published_at,
                    summary=_text(item, "description") or None,
                )
            )
        return articles

    def close(self) -> None:
        self._client.close()


def build_news_provider(settings: Settings) -> NewsProvider:
    if settings.news_provider == "mock":
        return MockNewsProvider()
    return RssNewsProvider.create(
        search_url=settings.news_rss_search_url,
        timeout_seconds=settings.news_timeout_seconds,
    )


def _text(item: ElementTree.Element, name: str) -> str:
    return (item.findtext(name) or "").strip()


def _published_at(value: str) -> datetime:
    if not value:
        return datetime.now(timezone.utc)
    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return datetime.now(timezone.utc)
    return parsed.astimezone(timezone.utc) if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
