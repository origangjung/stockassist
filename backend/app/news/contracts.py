from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class NewsArticle:
    symbol: str
    title: str
    url: str
    publisher: str
    published_at: datetime
    summary: str | None


class NewsProvider(ABC):
    name: str

    @abstractmethod
    def latest(self, symbol: str, *, limit: int) -> list[NewsArticle]: ...

    def close(self) -> None:
        """Release resources held by a provider when the application stops."""
