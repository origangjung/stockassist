"""contracts 파일은 실시간 시세 연결 기능을 담당한다."""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator, Awaitable, Callable
from typing import Any, Protocol

from app.providers.contracts import Quote

QuoteMessage = dict[str, Any]
QuotePublisher = Callable[[Quote], Awaitable[None]]


class RealtimeQuoteSource(ABC):
    """Normalizes polling and future streaming providers behind one contract."""

    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    async def validate(self, symbol: str) -> None: ...

    @abstractmethod
    async def fetch(self, symbol: str) -> Quote: ...


class StreamingQuoteSource(ABC):
    """Push source contract used by KIS and future streaming providers."""

    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    async def start(self, publish: QuotePublisher) -> None: ...

    @abstractmethod
    async def subscribe(self, symbol: str) -> None: ...

    @abstractmethod
    async def unsubscribe(self, symbol: str) -> None: ...

    @abstractmethod
    async def stop(self) -> None: ...


class QuoteBus(ABC):
    """`QuoteBus` 구현체가 제공해야 하는 메서드 계약을 정의합니다."""

    @abstractmethod
    async def publish(self, symbol: str, message: QuoteMessage) -> None: ...

    @abstractmethod
    async def get_cached(self, symbol: str) -> QuoteMessage | None: ...

    @abstractmethod
    def listen(self, symbol: str) -> AsyncIterator[QuoteMessage]: ...

    @abstractmethod
    async def close(self) -> None: ...


class RealtimeHub(Protocol):
    """`RealtimeHub` 구현체가 제공해야 하는 메서드 계약을 정의합니다."""

    @property
    def enabled(self) -> bool: ...

    @property
    def source_name(self) -> str: ...

    @property
    def transport(self) -> str: ...

    async def start(self) -> None: ...

    async def stop(self) -> None: ...

    def stream(self, symbol: str) -> AsyncIterator[QuoteMessage]: ...
