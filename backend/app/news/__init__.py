"""backend.app.news 패키지의 공개 구성 요소를 묶는다."""

from app.news.contracts import NewsArticle, NewsProvider
from app.news.providers import build_news_provider

__all__ = ["NewsArticle", "NewsProvider", "build_news_provider"]
