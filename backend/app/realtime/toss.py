"""토스증권 공식 AsyncAPI의 선언형 체결 구독을 내부 실시간 시세로 변환한다."""

from __future__ import annotations

import asyncio
import json
import logging
from contextlib import suppress
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Awaitable, Callable

from websockets.asyncio.client import ClientConnection, connect

from app.providers.contracts import Quote
from app.providers.errors import ProviderUnavailableError, ProviderValidationError
from app.providers.toss.provider import TossProvider
from app.realtime.contracts import QuotePublisher, StreamingQuoteSource

logger = logging.getLogger(__name__)


def toss_trade_declaration(symbols: set[str], request_id: str = "stockpilot-quotes") -> list[dict]:
    """현재 심볼 집합을 KR·US 토픽으로 묶은 full-replace 선언을 만든다."""
    domestic = sorted(symbol for symbol in symbols if symbol.isdigit() and len(symbol) == 6)
    overseas = sorted(symbol for symbol in symbols if symbol not in domestic)
    declaration: list[dict] = [{"id": request_id}]
    if domestic:
        declaration.append({"type": "trade:kr", "codes": domestic})
    if overseas:
        declaration.append({"type": "trade:us", "codes": overseas})
    return declaration if symbols else []


def parse_toss_trade_message(raw: str, names: dict[str, str]) -> Quote | None:
    """체결 message 프레임만 Quote로 정규화하고 ack·pong은 무시한다."""
    try:
        message = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ProviderValidationError(
            "Toss WebSocket returned invalid JSON",
            code="toss-realtime-message-invalid",
        ) from exc
    if not isinstance(message, dict) or message.get("type") != "message":
        return None
    topic = message.get("topic")
    data = message.get("data")
    if not isinstance(topic, str) or not topic.startswith("trade:") or not isinstance(data, dict):
        return None
    symbol = topic.rsplit(":", 1)[-1].upper()
    try:
        price = Decimal(str(data["price"]))
        timestamp = datetime.fromisoformat(str(data["timestamp"]))
    except (InvalidOperation, KeyError, TypeError, ValueError) as exc:
        raise ProviderValidationError(
            "Toss WebSocket trade payload is invalid",
            code="toss-realtime-message-invalid",
        ) from exc
    return Quote(
        symbol=symbol,
        name=names.get(symbol, symbol),
        price=price,
        change=None,
        change_percent=None,
        volume=int(Decimal(str(data.get("volume", "0")))),
        as_of=timestamp,
        currency=str(data.get("currency") or "") or None,
    )


class TossStreamingQuoteSource(StreamingQuoteSource):
    """OAuth 토큰을 서버에만 보관하며 토스 체결 스트림을 자동 재연결한다."""

    name = "toss"

    def __init__(
        self,
        provider: TossProvider,
        *,
        websocket_url: str,
        reconnect_max_seconds: float = 30.0,
        connector: Callable[..., Awaitable[ClientConnection]] | None = None,
    ) -> None:
        """`__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다."""

        self._provider = provider
        self._websocket_url = websocket_url
        self._reconnect_max_seconds = reconnect_max_seconds
        self._connector = connector or connect
        self._publish: QuotePublisher | None = None
        self._subscriptions: set[str] = set()
        self._names: dict[str, str] = {}
        self._lock = asyncio.Lock()
        self._changed = asyncio.Event()
        self._has_subscriptions = asyncio.Event()
        self._task: asyncio.Task[None] | None = None
        self._connection: ClientConnection | None = None

    async def start(self, publish: QuotePublisher) -> None:
        """`start`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        self._publish = publish
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self._run(), name="toss-realtime-stream")

    async def subscribe(self, symbol: str) -> None:
        """`subscribe`은(는) 비동기로 연결 또는 메시지 전달 생명주기를 관리합니다."""

        normalized = symbol.strip().upper()
        stock = await asyncio.to_thread(self._provider.get_stock_info, normalized)
        async with self._lock:
            if normalized in self._subscriptions:
                return
            if len(self._subscriptions) >= 40:
                raise ProviderValidationError(
                    "Toss WebSocket quote subscription limit reached",
                    code="toss-realtime-subscription-limit",
                    status_code=503,
                )
            self._subscriptions.add(normalized)
            self._names[normalized] = stock.name
            self._has_subscriptions.set()
            self._changed.set()

    async def unsubscribe(self, symbol: str) -> None:
        """`unsubscribe`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        normalized = symbol.strip().upper()
        async with self._lock:
            self._subscriptions.discard(normalized)
            self._names.pop(normalized, None)
            if not self._subscriptions:
                self._has_subscriptions.clear()
            self._changed.set()

    async def stop(self) -> None:
        """`stop`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        if self._task is not None:
            self._task.cancel()
            with suppress(asyncio.CancelledError):
                await self._task
            self._task = None
        if self._connection is not None:
            with suppress(Exception):
                await self._connection.close()
            self._connection = None

    async def _run(self) -> None:
        """`_run`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        backoff = 1.0
        while True:
            await self._has_subscriptions.wait()
            try:
                token = await asyncio.to_thread(self._provider.websocket_access_token)
                async with self._connector(
                    self._websocket_url,
                    additional_headers={"Authorization": f"Bearer {token}"},
                    ping_interval=None,
                ) as websocket:
                    self._connection = websocket
                    self._changed.set()
                    backoff = 1.0
                    receiver = asyncio.create_task(self._receive(websocket))
                    sender = asyncio.create_task(self._declare_changes(websocket))
                    keepalive = asyncio.create_task(self._keepalive(websocket))
                    done, pending = await asyncio.wait(
                        {receiver, sender, keepalive}, return_when=asyncio.FIRST_COMPLETED
                    )
                    for task in pending:
                        task.cancel()
                    for task in pending:
                        with suppress(asyncio.CancelledError):
                            await task
                    for task in done:
                        task.result()
                    raise ConnectionError("Toss WebSocket connection closed")
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("Toss realtime connection failed; reconnecting")
                await asyncio.sleep(backoff)
                backoff = min(self._reconnect_max_seconds, backoff * 2)
            finally:
                self._connection = None

    async def _declare_changes(self, websocket: ClientConnection) -> None:
        """`_declare_changes`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        while True:
            await self._changed.wait()
            self._changed.clear()
            async with self._lock:
                declaration = toss_trade_declaration(set(self._subscriptions))
            await websocket.send(json.dumps(declaration, separators=(",", ":")))

    async def _receive(self, websocket: ClientConnection) -> None:
        """`_receive`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        async for raw_message in websocket:
            raw = raw_message.decode() if isinstance(raw_message, bytes) else raw_message
            try:
                decoded = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise ProviderValidationError(
                    "Toss WebSocket returned invalid JSON",
                    code="toss-realtime-message-invalid",
                ) from exc
            if isinstance(decoded, dict) and decoded.get("type") == "error":
                error = decoded.get("error") if isinstance(decoded.get("error"), dict) else {}
                raise ProviderUnavailableError(
                    "Toss WebSocket reported an error",
                    code=f"toss-realtime-{str(error.get('code') or 'error')}",
                )
            async with self._lock:
                names = dict(self._names)
            quote = parse_toss_trade_message(raw, names)
            if quote is not None and self._publish is not None:
                await self._publish(quote)

    @staticmethod
    async def _keepalive(websocket: ClientConnection) -> None:
        """`_keepalive`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        while True:
            await asyncio.sleep(50)
            await websocket.send("PING")
