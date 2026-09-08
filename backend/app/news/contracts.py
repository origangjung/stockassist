"""contracts 파일은 백엔드 도메인 기능을 담당한다."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class NewsArticle:
    """`NewsArticle` 관련 상태와 동작을 하나의 객체로 묶습니다."""

    symbol: str
    title: str
    url: str
    publisher: str
    published_at: datetime
    summary: str | None


class NewsProvider(ABC):
    """`NewsProvider` 구현체가 제공해야 하는 메서드 계약을 정의합니다."""

    name: str

    @abstractmethod
    def latest(self, symbol: str, *, limit: int) -> list[NewsArticle]: ...

    def close(self) -> None:
        """Release resources held by a provider when the application stops."""
