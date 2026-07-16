import asyncio
import json
import logging
from collections.abc import Awaitable, Callable
from contextlib import suppress
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from zoneinfo import ZoneInfo

import httpx2
from websockets.asyncio.client import ClientConnection, connect

from app.providers.contracts import Quote, StockInfo, StockProvider
from app.providers.errors import (
    ProviderAuthenticationError,
    ProviderUnavailableError,
    ProviderValidationError,
)
from app.realtime.contracts import QuotePublisher, StreamingQuoteSource

logger = logging.getLogger(__name__)

DOMESTIC_TR_ID = "H0STCNT0"
OVERSEAS_TR_ID = "HDFSCNT0"
DOMESTIC_FIELD_COUNT = 46
OVERSEAS_FIELD_COUNT = 25
KST = ZoneInfo("Asia/Seoul")
NEW_YORK = ZoneInfo("America/New_York")


@dataclass(frozen=True)
class KISSubscription:
    symbol: str
    name: str
    tr_id: str
    tr_key: str
    currency: str


def resolve_subscription(stock: StockInfo) -> KISSubscription:
    symbol = stock.symbol.upper()
    if symbol.isdigit() and len(symbol) == 6:
        return KISSubscription(symbol, stock.name, DOMESTIC_TR_ID, symbol, "KRW")
    if stock.currency.upper() != "USD":
        raise ProviderValidationError(
            "KIS realtime currently supports Korean and US stocks only",
            code="kis-realtime-market-not-supported",
        )
    market = stock.market.upper()
    market_code = (
        "NAS"
        if "NAS" in market
        else "NYS"
        if "NYS" in market or "NYSE" in market
        else "AMS"
        if "AMS" in market or "AMEX" in market
        else None
    )
    if market_code is None:
        raise ProviderValidationError(
            "KIS realtime requires a supported US exchange code",
            code="kis-realtime-exchange-not-supported",
            data={"market": stock.market},
        )
    return KISSubscription(symbol, stock.name, OVERSEAS_TR_ID, f"D{market_code}{symbol}", "USD")


def subscription_message(approval_key: str, subscription: KISSubscription, action: str) -> dict:
    if action not in {"1", "2"}:
        raise ValueError("KIS subscription action must be 1 (subscribe) or 2 (unsubscribe)")
    return {
        "header": {
            "approval_key": approval_key,
            "custtype": "P",
            "tr_type": action,
            "content-type": "utf-8",
        },
        "body": {
            "input": {
                "tr_id": subscription.tr_id,
                "tr_key": subscription.tr_key,
            }
        },
    }


def parse_realtime_quotes(
    raw: str,
    subscriptions: dict[tuple[str, str], KISSubscription],
) -> list[Quote]:
    parts = raw.split("|", 3)
    if len(parts) != 4 or parts[0] not in {"0", "1"}:
        return []
    tr_id = parts[1]
    if tr_id not in {DOMESTIC_TR_ID, OVERSEAS_TR_ID}:
        return []
    try:
        count = int(parts[2])
    except ValueError as exc:
        raise ProviderValidationError(
            "KIS realtime message has an invalid record count",
            code="kis-realtime-message-invalid",
        ) from exc
    width = DOMESTIC_FIELD_COUNT if tr_id == DOMESTIC_TR_ID else OVERSEAS_FIELD_COUNT
    fields = parts[3].split("^")
    if count < 1 or len(fields) < count * width:
        raise ProviderValidationError(
            "KIS realtime message has insufficient fields",
            code="kis-realtime-message-invalid",
            data={"tr_id": tr_id, "record_count": count, "field_count": len(fields)},
        )
    quotes: list[Quote] = []
    for index in range(count):
        values = fields[index * width : (index + 1) * width]
        subscription = _find_subscription(tr_id, values[0], subscriptions)
        if subscription is None:
            continue
        quotes.append(
            _domestic_quote(values, subscription)
            if tr_id == DOMESTIC_TR_ID
            else _overseas_quote(values, subscription)
        )
    return quotes


def _find_subscription(
    tr_id: str,
    received_key: str,
    subscriptions: dict[tuple[str, str], KISSubscription],
) -> KISSubscription | None:
    direct = subscriptions.get((tr_id, received_key))
    if direct is not None:
        return direct
    for (candidate_tr_id, _), subscription in subscriptions.items():
        if candidate_tr_id == tr_id and received_key.endswith(subscription.symbol):
            return subscription
    return None


def _domestic_quote(values: list[str], subscription: KISSubscription) -> Quote:
    return Quote(
        symbol=subscription.symbol,
        name=subscription.name,
        price=_decimal(values[2]),
        change=_signed_decimal(values[4], values[3]),
        change_percent=_signed_decimal(values[5], values[3]),
        volume=_integer(values[13]),
        as_of=_timestamp(values[33], values[1], KST),
        currency=subscription.currency,
    )


def _overseas_quote(values: list[str], subscription: KISSubscription) -> Quote:
    return Quote(
        symbol=subscription.symbol,
        name=subscription.name,
        price=_decimal(values[10]),
        change=_signed_decimal(values[12], values[11]),
        change_percent=_signed_decimal(values[13], values[11]),
        volume=_integer(values[19]),
        as_of=_timestamp(values[3], values[4], NEW_YORK),
        currency=subscription.currency,
    )


def _decimal(value: str) -> Decimal:
    try:
        return Decimal(value.strip())
    except InvalidOperation as exc:
        raise ProviderValidationError(
            "KIS realtime message contains an invalid decimal",
            code="kis-realtime-message-invalid",
        ) from exc


def _signed_decimal(value: str, sign_code: str) -> Decimal:
    number = _decimal(value)
    return -abs(number) if sign_code in {"4", "5"} else number


def _integer(value: str) -> int:
    return int(_decimal(value))


def _timestamp(date_value: str, time_value: str, timezone: ZoneInfo) -> datetime:
    try:
        parsed = datetime.strptime(f"{date_value}{time_value[:6]}", "%Y%m%d%H%M%S")
        return parsed.replace(tzinfo=timezone).astimezone(UTC)
    except ValueError:
        return datetime.now(UTC)


class KISStreamingQuoteSource(StreamingQuoteSource):
    name = "kis"

    def __init__(
        self,
        *,
        base_url: str,
        websocket_url: str,
        app_key: str,
        app_secret: str,
        resolver: StockProvider,
        timeout_seconds: float = 15.0,
        reconnect_max_seconds: float = 30.0,
        transport: httpx2.AsyncBaseTransport | None = None,
        connector: Callable[..., Awaitable[ClientConnection]] | None = None,
    ) -> None:
        self._app_key = app_key
        self._app_secret = app_secret
        self._websocket_url = websocket_url
        self._resolver = resolver
        self._reconnect_max_seconds = reconnect_max_seconds
        self._client = httpx2.AsyncClient(
            base_url=base_url.rstrip("/"),
            timeout=timeout_seconds,
            transport=transport,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
        )
        self._connector = connector or connect
        self._publish: QuotePublisher | None = None
        self._subscriptions: dict[str, KISSubscription] = {}
        self._lock = asyncio.Lock()
        self._actions: asyncio.Queue[tuple[str, KISSubscription]] = asyncio.Queue()
        self._has_subscriptions = asyncio.Event()
        self._task: asyncio.Task[None] | None = None
        self._connection: ClientConnection | None = None
        self._approval_key: str | None = None
        self._approval_expires_at = 0.0

    async def start(self, publish: QuotePublisher) -> None:
        self._publish = publish
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self._run(), name="kis-realtime-stream")

    async def subscribe(self, symbol: str) -> None:
        stock = await asyncio.to_thread(self._resolver.get_stock_info, symbol)
        subscription = resolve_subscription(stock)
        async with self._lock:
            if symbol in self._subscriptions:
                return
            if len(self._subscriptions) >= 40:
                raise ProviderValidationError(
                    "KIS WebSocket supports at most 40 active subscriptions",
                    code="kis-realtime-subscription-limit",
                    status_code=503,
                )
            self._subscriptions[symbol] = subscription
            connected = self._connection is not None
            self._has_subscriptions.set()
        if connected:
            await self._actions.put(("1", subscription))

    async def unsubscribe(self, symbol: str) -> None:
        async with self._lock:
            subscription = self._subscriptions.pop(symbol, None)
            connected = self._connection is not None
            empty = not self._subscriptions
            if empty:
                self._has_subscriptions.clear()
        if subscription is not None and connected:
            await self._actions.put(("2", subscription))
        if empty and self._connection is not None:
            await self._connection.close()

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            with suppress(asyncio.CancelledError):
                await self._task
            self._task = None
        if self._connection is not None:
            with suppress(Exception):
                await self._connection.close()
            self._connection = None
        await self._client.aclose()

    async def get_approval_key(self) -> str:
        now = asyncio.get_running_loop().time()
        if self._approval_key is not None and now < self._approval_expires_at:
            return self._approval_key
        try:
            response = await self._client.post(
                "/oauth2/Approval",
                json={
                    "grant_type": "client_credentials",
                    "appkey": self._app_key,
                    "secretkey": self._app_secret,
                },
            )
        except httpx2.HTTPError as exc:
            raise ProviderUnavailableError(
                "KIS WebSocket approval request failed",
                code="kis-realtime-approval-failed",
            ) from exc
        if response.status_code >= 400:
            raise ProviderAuthenticationError(
                "KIS rejected the WebSocket approval request",
                code="kis-realtime-approval-rejected",
                request_id=response.headers.get("x-request-id"),
                data={"status_code": response.status_code},
            )
        approval_key = response.json().get("approval_key")
        if not isinstance(approval_key, str) or not approval_key:
            raise ProviderAuthenticationError(
                "KIS approval response omitted approval_key",
                code="kis-realtime-approval-invalid",
            )
        self._approval_key = approval_key
        self._approval_expires_at = now + 23 * 60 * 60
        return approval_key

    async def _run(self) -> None:
        backoff = 1.0
        while True:
            await self._has_subscriptions.wait()
            try:
                approval_key = await self.get_approval_key()
                async with self._connector(self._websocket_url) as websocket:
                    async with self._lock:
                        self._connection = websocket
                        subscriptions = tuple(self._subscriptions.values())
                    self._drain_actions()
                    for subscription in subscriptions:
                        await self._send(websocket, approval_key, "1", subscription)
                    backoff = 1.0
                    receiver = asyncio.create_task(self._receive(websocket))
                    sender = asyncio.create_task(self._send_actions(websocket, approval_key))
                    done, pending = await asyncio.wait(
                        {receiver, sender}, return_when=asyncio.FIRST_COMPLETED
                    )
                    for task in pending:
                        task.cancel()
                    for task in pending:
                        with suppress(asyncio.CancelledError):
                            await task
                    for task in done:
                        task.result()
                    raise ConnectionError("KIS WebSocket connection closed")
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("KIS realtime connection failed; reconnecting")
                await asyncio.sleep(backoff)
                backoff = min(self._reconnect_max_seconds, backoff * 2)
            finally:
                async with self._lock:
                    self._connection = None

    async def _send_actions(self, websocket: ClientConnection, approval_key: str) -> None:
        while True:
            action, subscription = await self._actions.get()
            await self._send(websocket, approval_key, action, subscription)

    @staticmethod
    async def _send(
        websocket: ClientConnection,
        approval_key: str,
        action: str,
        subscription: KISSubscription,
    ) -> None:
        await websocket.send(json.dumps(subscription_message(approval_key, subscription, action)))
        await asyncio.sleep(0.05)

    async def _receive(self, websocket: ClientConnection) -> None:
        async for raw_message in websocket:
            raw = raw_message.decode() if isinstance(raw_message, bytes) else raw_message
            if raw and raw[0] in {"0", "1"}:
                async with self._lock:
                    lookup = {
                        (item.tr_id, item.tr_key): item for item in self._subscriptions.values()
                    }
                for quote in parse_realtime_quotes(raw, lookup):
                    if self._publish is not None:
                        await self._publish(quote)
                continue
            await self._handle_system_message(websocket, raw)

    @staticmethod
    async def _handle_system_message(websocket: ClientConnection, raw: str) -> None:
        try:
            message = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ProviderValidationError(
                "KIS WebSocket returned an invalid system message",
                code="kis-realtime-message-invalid",
            ) from exc
        header = message.get("header") or {}
        if header.get("tr_id") == "PINGPONG":
            await websocket.pong(raw.encode())
            return
        body = message.get("body") or {}
        if body.get("rt_cd") not in {None, "0"}:
            logger.warning(
                "KIS realtime subscription rejected tr_id=%s tr_key=%s code=%s",
                header.get("tr_id"),
                header.get("tr_key"),
                body.get("msg_cd"),
            )

    def _drain_actions(self) -> None:
        while not self._actions.empty():
            with suppress(asyncio.QueueEmpty):
                self._actions.get_nowait()
