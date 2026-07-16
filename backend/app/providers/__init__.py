"""External market-data provider implementations."""

from app.config import Settings
from app.providers.contracts import StockProvider
from app.providers.mock import MockProvider
from app.providers.audit import ProviderAuditSink


def build_providers(
    settings: Settings, audit_sink: ProviderAuditSink | None = None
) -> list[StockProvider]:
    if settings.stock_provider == "mock":
        return [MockProvider()]
    secret = (
        settings.toss_client_secret.get_secret_value()
        if settings.toss_client_secret is not None
        else ""
    )
    if not settings.toss_client_id or not secret:
        raise ValueError(
            "TOSS_CLIENT_ID and TOSS_CLIENT_SECRET are required when STOCK_PROVIDER=toss"
        )
    from app.providers.toss import TossProvider
    from app.providers.toss.auth import RedisTokenCache

    return [
        TossProvider.create(
            base_url=settings.toss_base_url,
            client_id=settings.toss_client_id,
            client_secret=secret,
            timeout_seconds=settings.toss_timeout_seconds,
            max_retries=settings.toss_max_retries,
            token_cache=RedisTokenCache(settings.redis_url),
            audit_sink=audit_sink,
        )
    ]


__all__ = ["build_providers"]
