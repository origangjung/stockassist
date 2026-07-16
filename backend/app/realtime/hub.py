import asyncio
import logging
import re
from collections.abc import AsyncIterator

from app.core.sanitization import public_provider_error_message
from app.providers.errors import ProviderError
from app.providers.contracts import Quote
from app.realtime.contracts import (
    QuoteBus,
    QuoteMessage,
    RealtimeQuoteSource,
    StreamingQuoteSource,
)
from app.realtime.messages import quote_message

logger = logging.getLogger(__name__)

_SYMBOL_PATTERN = re.compile(r"^[A-Z0-9.-]{1,16}$")


class RealtimeDisabledError(RuntimeError):
    pass


class RealtimeCapacityError(RuntimeError):
    pass


class InvalidRealtimeSymbolError(ValueError):
    pass


class RealtimeQuoteHub:
    def __init__(
        self,
        source: RealtimeQuoteSource,
        bus: QuoteBus,
        *,
        enabled: bool,
        poll_interval_seconds: float = 2.0,
        max_symbols: int = 20,
        max_connections: int = 200,
    ) -> None:
        self._source = source
        self._bus = bus
        self._enabled = enabled
        self._poll_interval_seconds = poll_interval_seconds
        self._max_symbols = max_symbols
        self._max_connections = max_connections
        self._subscriptions: dict[str, int] = {}
        self._lock = asyncio.Lock()
        self._task: asyncio.Task[None] | None = None

    @property
    def enabled(self) -> bool:
        return self._enabled

    @property
    def source_name(self) -> str:
        return self._source.name

    @property
    def transport(self) -> str:
        return "polling"

    async def start(self) -> None:
        if self._enabled and (self._task is None or self._task.done()):
            self._task = asyncio.create_task(self._poll_loop(), name="realtime-quote-poller")

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        await self._bus.close()

    async def stream(self, symbol: str) -> AsyncIterator[QuoteMessage]:
        if not self._enabled:
            raise RealtimeDisabledError("Realtime quotes are disabled")
        normalized = self._normalize_symbol(symbol)
        await self._source.validate(normalized)
        await self._register(normalized)
        try:
            cached = await self._bus.get_cached(normalized)
            if cached is not None:
                yield cached
            async for message in self._bus.listen(normalized):
                yield message
        finally:
            await self._unregister(normalized)

    @staticmethod
    def _normalize_symbol(symbol: str) -> str:
        normalized = symbol.strip().upper()
        if not _SYMBOL_PATTERN.fullmatch(normalized):
            raise InvalidRealtimeSymbolError("Invalid stock symbol")
        return normalized

    async def _register(self, symbol: str) -> None:
        async with self._lock:
            if sum(self._subscriptions.values()) >= self._max_connections:
                raise RealtimeCapacityError("Realtime connection capacity has been reached")
            if symbol not in self._subscriptions and len(self._subscriptions) >= self._max_symbols:
                raise RealtimeCapacityError("Realtime symbol capacity has been reached")
            self._subscriptions[symbol] = self._subscriptions.get(symbol, 0) + 1

    async def _unregister(self, symbol: str) -> None:
        async with self._lock:
            subscribers = self._subscriptions.get(symbol, 0) - 1
            if subscribers <= 0:
                self._subscriptions.pop(symbol, None)
            else:
                self._subscriptions[symbol] = subscribers

    async def _active_symbols(self) -> list[str]:
        async with self._lock:
            return sorted(
                self._subscriptions,
                key=lambda symbol: (-self._subscriptions[symbol], symbol),
            )

    async def _poll_loop(self) -> None:
        while True:
            symbols = await self._active_symbols()
            if not symbols:
                await asyncio.sleep(0.1)
                continue
            started_at = asyncio.get_running_loop().time()
            for symbol in symbols:
                await self._poll_symbol(symbol)
            elapsed = asyncio.get_running_loop().time() - started_at
            await asyncio.sleep(max(0.05, self._poll_interval_seconds - elapsed))

    async def _poll_symbol(self, symbol: str) -> None:
        try:
            quote = await self._source.fetch(symbol)
            await self._publish(symbol, quote_message(quote, self._source.name))
        except ProviderError as exc:
            logger.warning(
                "Realtime quote polling failed provider=%s symbol=%s code=%s request_id=%s",
                self._source.name,
                symbol,
                exc.code,
                exc.request_id,
            )
            await self._publish(
                symbol,
                {
                    "type": "error",
                    "symbol": symbol,
                    "error": {
                        "code": exc.code,
                        "message": public_provider_error_message(exc),
                    },
                    "provider": self._source.name,
                    "retryable": exc.status_code >= 500,
                    "is_investment_advice": False,
                },
            )
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception(
                "Unexpected realtime quote polling failure provider=%s symbol=%s",
                self._source.name,
                symbol,
            )

    async def _publish(self, symbol: str, message: QuoteMessage) -> None:
        try:
            await self._bus.publish(symbol, message)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Realtime quote bus publish failed symbol=%s", symbol)


class StreamingRealtimeQuoteHub:
    def __init__(
        self,
        source: StreamingQuoteSource,
        bus: QuoteBus,
        *,
        enabled: bool,
        max_symbols: int = 40,
        max_connections: int = 200,
    ) -> None:
        self._source = source
        self._bus = bus
        self._enabled = enabled
        self._max_symbols = max_symbols
        self._max_connections = max_connections
        self._subscriptions: dict[str, int] = {}
        self._lock = asyncio.Lock()

    @property
    def enabled(self) -> bool:
        return self._enabled

    @property
    def source_name(self) -> str:
        return self._source.name

    @property
    def transport(self) -> str:
        return "streaming"

    async def start(self) -> None:
        if self._enabled:
            await self._source.start(self._on_quote)

    async def stop(self) -> None:
        await self._source.stop()
        await self._bus.close()

    async def stream(self, symbol: str) -> AsyncIterator[QuoteMessage]:
        if not self._enabled:
            raise RealtimeDisabledError("Realtime quotes are disabled")
        normalized = RealtimeQuoteHub._normalize_symbol(symbol)
        first_subscriber = await self._register(normalized)
        try:
            if first_subscriber:
                await self._source.subscribe(normalized)
            cached = await self._bus.get_cached(normalized)
            if cached is not None:
                yield cached
            async for message in self._bus.listen(normalized):
                yield message
        finally:
            last_subscriber = await self._unregister(normalized)
            if last_subscriber:
                await self._source.unsubscribe(normalized)

    async def _register(self, symbol: str) -> bool:
        async with self._lock:
            if sum(self._subscriptions.values()) >= self._max_connections:
                raise RealtimeCapacityError("Realtime connection capacity has been reached")
            if symbol not in self._subscriptions and len(self._subscriptions) >= self._max_symbols:
                raise RealtimeCapacityError("Realtime symbol capacity has been reached")
            first = symbol not in self._subscriptions
            self._subscriptions[symbol] = self._subscriptions.get(symbol, 0) + 1
            return first

    async def _unregister(self, symbol: str) -> bool:
        async with self._lock:
            subscribers = self._subscriptions.get(symbol, 0) - 1
            if subscribers <= 0:
                self._subscriptions.pop(symbol, None)
                return True
            self._subscriptions[symbol] = subscribers
            return False

    async def _on_quote(self, quote: Quote) -> None:
        try:
            await self._bus.publish(quote.symbol, quote_message(quote, self._source.name))
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Streaming quote bus publish failed symbol=%s", quote.symbol)
