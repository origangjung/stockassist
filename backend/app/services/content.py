from collections.abc import Iterable

from app.disclosures.contracts import Disclosure, DisclosureProvider
from app.news.contracts import NewsArticle, NewsProvider
from app.repositories.contracts import DisclosureRepository, NewsRepository

_POSITIVE_TERMS = ("growth", "record", "approval", "profit", "dividend", "contract")
_NEGATIVE_TERMS = ("risk", "loss", "delay", "lawsuit", "warning", "recall")
_HIGH_RISK_TERMS = ("trading halt", "going concern", "lawsuit", "capital reduction")


class DisclosureAnalysisService:
    def __init__(
        self, provider: DisclosureProvider, repository: DisclosureRepository | None = None
    ) -> None:
        self._provider = provider
        self._repository = repository

    def latest(self, symbol: str, *, days: int, limit: int) -> dict:
        disclosures = self._provider.list_disclosures(symbol, days=days, limit=limit)
        if self._repository is not None:
            self._repository.save_many(disclosures, source=self._provider.name)
        high_risk = [
            item.report_name
            for item in disclosures
            if _contains(item.report_name, _HIGH_RISK_TERMS)
        ]
        return {
            "symbol": symbol,
            "provider": self._provider.name,
            "experimental": True,
            "risk_flags": high_risk,
            "disclosures": [
                {**item.__dict__, "risk_level": _disclosure_risk(item)} for item in disclosures
            ],
            "persistence_status": "saved" if self._repository is not None else "disabled",
        }


class NewsAnalysisService:
    def __init__(self, provider: NewsProvider, repository: NewsRepository | None = None) -> None:
        self._provider = provider
        self._repository = repository

    def latest(self, symbol: str, *, limit: int) -> dict:
        articles = self._provider.latest(symbol, limit=limit)
        if self._repository is not None:
            self._repository.save_many(articles, source=self._provider.name)
        scores = [_news_score(article) for article in articles]
        average = sum(scores) / len(scores) if scores else 0.0
        return {
            "symbol": symbol,
            "provider": self._provider.name,
            "experimental": True,
            "sentiment_score": round(average, 3),
            "sentiment_label": "positive"
            if average > 0.1
            else "negative"
            if average < -0.1
            else "neutral",
            "articles": [
                {**article.__dict__, "sentiment_score": score}
                for article, score in zip(articles, scores, strict=True)
            ],
            "persistence_status": "saved" if self._repository is not None else "disabled",
        }


def _news_score(article: NewsArticle) -> float:
    text = f"{article.title} {article.summary or ''}".casefold()
    return float(
        sum(term in text for term in _POSITIVE_TERMS)
        - sum(term in text for term in _NEGATIVE_TERMS)
    )


def _disclosure_risk(disclosure: Disclosure) -> str:
    return "high" if _contains(disclosure.report_name, _HIGH_RISK_TERMS) else "normal"


def _contains(text: str, terms: Iterable[str]) -> bool:
    normalized = text.casefold()
    return any(term in normalized for term in terms)
