"""providers 파일은 백엔드 도메인 기능을 담당한다."""

from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import quote_plus
from xml.etree import ElementTree

import httpx2

from app.config import Settings
from app.news.contracts import NewsArticle, NewsProvider
from app.providers.errors import ProviderUnavailableError


class MockNewsProvider(NewsProvider):
    """외부 또는 모의 데이터 원천을 동일한 계약으로 제공하는 구현체입니다."""

    name = "mock"

    def latest(self, symbol: str, *, limit: int) -> list[NewsArticle]:
        """`latest`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

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
    """외부 또는 모의 데이터 원천을 동일한 계약으로 제공하는 구현체입니다."""

    name = "rss"

    def __init__(self, client: httpx2.Client, search_url: str) -> None:
        """`__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다."""

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
        """`create`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        return cls(httpx2.Client(timeout=timeout_seconds, transport=transport), search_url)

    def latest(self, symbol: str, *, limit: int) -> list[NewsArticle]:
        """`latest`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

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
        """`close`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        self._client.close()


def build_news_provider(settings: Settings) -> NewsProvider:
    """`build_news_provider`은(는) 입력 값과 설정을 결합해 새 결과 객체를 생성합니다."""

    if settings.news_provider == "mock":
        return MockNewsProvider()
    return RssNewsProvider.create(
        search_url=settings.news_rss_search_url,
        timeout_seconds=settings.news_timeout_seconds,
    )


def _text(item: ElementTree.Element, name: str) -> str:
    """`_text`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    return (item.findtext(name) or "").strip()


def _published_at(value: str) -> datetime:
    """`_published_at`은(는) 연결 또는 메시지 전달 생명주기를 관리합니다."""

    if not value:
        return datetime.now(timezone.utc)
    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return datetime.now(timezone.utc)
    return parsed.astimezone(timezone.utc) if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
