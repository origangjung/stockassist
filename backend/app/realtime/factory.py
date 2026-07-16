from app.adapters.broker import BrokerAdapter
from app.config import Settings
from app.providers.contracts import Capability
from app.realtime.bus import RedisQuoteBus
from app.realtime.contracts import RealtimeHub
from app.realtime.hub import RealtimeQuoteHub, StreamingRealtimeQuoteHub
from app.realtime.kis import KISStreamingQuoteSource
from app.realtime.source import PollingQuoteSource


def build_realtime_quote_hub(settings: Settings, broker: BrokerAdapter) -> RealtimeHub:
    if settings.realtime_source == "kis":
        app_key = settings.kis_app_key.get_secret_value() if settings.kis_app_key else ""
        app_secret = settings.kis_app_secret.get_secret_value() if settings.kis_app_secret else ""
        if not app_key or not app_secret:
            raise ValueError("KIS_APP_KEY and KIS_APP_SECRET are required when REALTIME_SOURCE=kis")
        bus = RedisQuoteBus(settings.redis_url, settings.realtime_cache_ttl_seconds)
        source = KISStreamingQuoteSource(
            base_url=settings.kis_base_url,
            websocket_url=settings.kis_ws_url,
            app_key=app_key,
            app_secret=app_secret,
            resolver=broker.provider_for(Capability.QUOTE),
            timeout_seconds=settings.kis_timeout_seconds,
            reconnect_max_seconds=settings.kis_ws_reconnect_max_seconds,
        )
        return StreamingRealtimeQuoteHub(
            source,
            bus,
            enabled=settings.realtime_enabled,
            max_symbols=min(settings.realtime_max_symbols, 40),
            max_connections=settings.realtime_max_connections,
        )
    bus = RedisQuoteBus(settings.redis_url, settings.realtime_cache_ttl_seconds)
    source = PollingQuoteSource(broker)
    return RealtimeQuoteHub(
        source,
        bus,
        enabled=settings.realtime_enabled,
        poll_interval_seconds=settings.realtime_poll_interval_seconds,
        max_symbols=settings.realtime_max_symbols,
        max_connections=settings.realtime_max_connections,
    )
