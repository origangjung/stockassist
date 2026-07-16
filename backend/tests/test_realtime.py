import asyncio
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from decimal import Decimal

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest
from starlette.websockets import WebSocketDisconnect

from app.providers.contracts import Quote
from app.providers.errors import ProviderAuthenticationError
from app.realtime.bus import InMemoryQuoteBus
from app.realtime.contracts import RealtimeQuoteSource
from app.realtime.contracts import QuotePublisher, StreamingQuoteSource
from app.realtime.hub import (
    InvalidRealtimeSymbolError,
    RealtimeCapacityError,
    RealtimeDisabledError,
    RealtimeQuoteHub,
    StreamingRealtimeQuoteHub,
)
from app.websocket import router as websocket_router


class FakeQuoteSource(RealtimeQuoteSource):
    def __init__(self) -> None:
        self.validated: list[str] = []
        self.fetch_count = 0

    @property
    def name(self) -> str:
        return "fake"

    async def validate(self, symbol: str) -> None:
        self.validated.append(symbol)

    async def fetch(self, symbol: str) -> Quote:
        self.fetch_count += 1
        return Quote(
            symbol=symbol,
            name="Test Stock",
            price=Decimal("123.45"),
            change=Decimal("1.25"),
            change_percent=Decimal("1.02"),
            volume=1234,
            as_of=datetime(2026, 7, 14, tzinfo=UTC),
            currency="USD",
        )


class FakeStreamingSource(StreamingQuoteSource):
    def __init__(self) -> None:
        self.publish: QuotePublisher | None = None
        self.subscribed: list[str] = []
        self.unsubscribed: list[str] = []

    @property
    def name(self) -> str:
        return "fake-stream"

    async def start(self, publish: QuotePublisher) -> None:
        self.publish = publish

    async def subscribe(self, symbol: str) -> None:
        self.subscribed.append(symbol)
        assert self.publish is not None
        await self.publish(
            Quote(
                symbol,
                "Streamed Stock",
                Decimal("321.00"),
                Decimal("2.00"),
                Decimal("0.63"),
                999,
                datetime(2026, 7, 15, tzinfo=UTC),
                "USD",
            )
        )

    async def unsubscribe(self, symbol: str) -> None:
        self.unsubscribed.append(symbol)

    async def stop(self) -> None:
        self.publish = None


class FailingQuoteSource(FakeQuoteSource):
    async def fetch(self, symbol: str) -> Quote:
        raise ProviderAuthenticationError(
            "Bearer realtime-secret-token",
            code="provider-authentication-failed",
            data={"access_token": "realtime-secret-token"},
        )


def test_in_memory_bus_fans_out_and_caches_latest_quote():
    async def scenario() -> None:
        bus = InMemoryQuoteBus()
        listener = bus.listen("aapl")
        received = asyncio.create_task(anext(listener))
        await asyncio.sleep(0)
        message = {"type": "quote", "symbol": "AAPL", "price": "123.45"}
        await bus.publish("AAPL", message)

        assert await asyncio.wait_for(received, timeout=0.5) == message
        assert await bus.get_cached("aapl") == message
        await listener.aclose()
        await bus.close()

    asyncio.run(scenario())


def test_polling_hub_publishes_normalized_compliance_message():
    async def scenario() -> None:
        source = FakeQuoteSource()
        hub = RealtimeQuoteHub(
            source,
            InMemoryQuoteBus(),
            enabled=True,
            poll_interval_seconds=0.01,
            max_symbols=2,
        )
        await hub.start()
        stream = hub.stream("aapl")
        message = await asyncio.wait_for(anext(stream), timeout=1)

        assert source.validated == ["AAPL"]
        assert source.fetch_count >= 1
        assert message["type"] == "quote"
        assert message["symbol"] == "AAPL"
        assert message["price"] == "123.45"
        assert message["provider"] == "fake"
        assert message["is_investment_advice"] is False
        await stream.aclose()
        await hub.stop()

    asyncio.run(scenario())


def test_hub_rejects_disabled_and_invalid_subscriptions():
    async def scenario() -> None:
        disabled = RealtimeQuoteHub(FakeQuoteSource(), InMemoryQuoteBus(), enabled=False)
        disabled_stream = disabled.stream("AAPL")
        try:
            await anext(disabled_stream)
        except RealtimeDisabledError:
            pass
        else:
            raise AssertionError("Disabled realtime stream should fail")
        await disabled.stop()

        enabled = RealtimeQuoteHub(FakeQuoteSource(), InMemoryQuoteBus(), enabled=True)
        invalid_stream = enabled.stream("AAPL/$")
        try:
            await anext(invalid_stream)
        except InvalidRealtimeSymbolError:
            pass
        else:
            raise AssertionError("Invalid symbol should fail")
        await enabled.stop()

    asyncio.run(scenario())


def test_polling_hub_redacts_provider_error_and_caps_same_symbol_connections():
    async def scenario() -> None:
        bus = InMemoryQuoteBus()
        hub = RealtimeQuoteHub(
            FailingQuoteSource(),
            bus,
            enabled=True,
            max_symbols=2,
            max_connections=1,
        )
        listener = bus.listen("AAPL")
        received = asyncio.create_task(anext(listener))
        await asyncio.sleep(0)
        await hub._poll_symbol("AAPL")
        message = await asyncio.wait_for(received, timeout=0.5)

        assert message["error"]["message"] == "외부 데이터 제공자의 인증에 실패했습니다."
        assert "realtime-secret-token" not in str(message)

        await hub._register("AAPL")
        with pytest.raises(RealtimeCapacityError):
            await hub._register("AAPL")
        await hub._unregister("AAPL")
        await listener.aclose()
        await hub.stop()

    asyncio.run(scenario())


def test_websocket_route_streams_quote_message():
    hub = RealtimeQuoteHub(
        FakeQuoteSource(),
        InMemoryQuoteBus(),
        enabled=True,
        poll_interval_seconds=0.01,
    )

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        await hub.start()
        try:
            yield
        finally:
            await hub.stop()

    test_app = FastAPI(lifespan=lifespan)
    test_app.state.realtime_quote_hub = hub
    test_app.include_router(websocket_router)

    with TestClient(test_app) as client:
        with client.websocket_connect("/ws/v1/quotes/AAPL") as websocket:
            message = websocket.receive_json()

    assert message["type"] == "quote"
    assert message["symbol"] == "AAPL"
    assert message["is_investment_advice"] is False


def test_websocket_route_rejects_untrusted_browser_origin():
    test_app = FastAPI()
    test_app.state.realtime_quote_hub = RealtimeQuoteHub(
        FakeQuoteSource(),
        InMemoryQuoteBus(),
        enabled=True,
    )
    test_app.state.allowed_origins = frozenset({"http://localhost:3000"})
    test_app.include_router(websocket_router)

    with TestClient(test_app) as client:
        with pytest.raises(WebSocketDisconnect) as exc_info:
            with client.websocket_connect(
                "/ws/v1/quotes/AAPL",
                headers={"Origin": "https://evil.example"},
            ):
                pass
    assert exc_info.value.code == 4403


def test_streaming_hub_shares_push_source_with_websocket_contract():
    async def scenario() -> None:
        source = FakeStreamingSource()
        hub = StreamingRealtimeQuoteHub(
            source,
            InMemoryQuoteBus(),
            enabled=True,
            max_symbols=2,
        )
        await hub.start()
        stream = hub.stream("aapl")
        message = await asyncio.wait_for(anext(stream), timeout=0.5)

        assert source.subscribed == ["AAPL"]
        assert message["symbol"] == "AAPL"
        assert message["provider"] == "fake-stream"
        assert message["price"] == "321.00"
        await stream.aclose()
        assert source.unsubscribed == ["AAPL"]
        await hub.stop()

    asyncio.run(scenario())
