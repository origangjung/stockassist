from functools import lru_cache
import re
from typing import Literal

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./stockpilot.db"
    redis_url: str = "redis://localhost:6379/0"
    scheduler_enabled: bool = False
    scheduler_interval_minutes: int = 5
    scheduler_symbols: str = "005930,000660,035420,AAPL,MSFT"
    scheduler_ingestion_limit: int = Field(default=120, ge=30, le=365)
    partition_maintenance_enabled: bool = False
    partition_lookahead_months: int = Field(default=3, ge=1, le=12)
    provider_audit_cleanup_enabled: bool = False
    provider_audit_retention_days: int = Field(default=90, ge=7, le=3650)
    provider_audit_cleanup_hour_kst: int = Field(default=4, ge=0, le=23)
    persistence_enabled: bool = False
    admin_api_key: SecretStr | None = None
    admin_max_failed_attempts: int = Field(default=5, ge=3, le=20)
    admin_lockout_seconds: int = Field(default=60, ge=10, le=3600)
    cors_origins: str = "http://localhost:3000,http://localhost:8080"
    rate_limit_enabled: bool = True
    rate_limit_backend: Literal["memory", "redis"] = "memory"
    rate_limit_window_seconds: int = Field(default=60, ge=1, le=3600)
    rate_limit_requests: int = Field(default=240, ge=10, le=10000)
    expensive_rate_limit_requests: int = Field(default=30, ge=1, le=1000)
    trust_proxy_headers: bool = False
    metrics_enabled: bool = True
    health_check_timeout_seconds: float = Field(default=2.0, gt=0, le=10)
    app_environment: Literal["development", "test", "staging", "production"] = "development"
    app_release: str = "stockpilot-ai@0.1.0"
    log_level: str = "INFO"
    log_format: Literal["json", "console"] = "json"
    sentry_dsn: SecretStr | None = None
    sentry_traces_sample_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    reference_alerts_enabled: bool = False
    reference_alert_interval_seconds: int = Field(default=30, ge=5, le=3600)
    stock_provider: Literal["mock", "toss"] = "mock"
    toss_base_url: str = "https://openapi.tossinvest.com"
    toss_client_id: str | None = None
    toss_client_secret: SecretStr | None = None
    toss_timeout_seconds: float = Field(default=10.0, gt=0, le=60)
    toss_max_retries: int = Field(default=3, ge=0, le=5)
    financial_provider: Literal["mock", "dart"] = "mock"
    dart_base_url: str = "https://opendart.fss.or.kr/api"
    dart_api_key: SecretStr | None = None
    dart_timeout_seconds: float = Field(default=15.0, gt=0, le=60)
    disclosure_provider: Literal["mock", "dart"] = "mock"
    news_provider: Literal["mock", "rss"] = "mock"
    news_rss_search_url: str = "https://news.google.com/rss/search?q={query}&hl=ko&gl=KR&ceid=KR:ko"
    news_timeout_seconds: float = Field(default=10.0, gt=0, le=60)
    investor_flow_provider: Literal["mock", "kis"] = "mock"
    prediction_engine: Literal["lightweight", "xgboost"] = "lightweight"
    kis_base_url: str = "https://openapi.koreainvestment.com:9443"
    kis_app_key: SecretStr | None = None
    kis_app_secret: SecretStr | None = None
    kis_timeout_seconds: float = Field(default=15.0, gt=0, le=60)
    ai_report_provider: Literal["mock", "openai"] = "mock"
    openai_api_key: SecretStr | None = None
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-5"
    openai_timeout_seconds: float = Field(default=30.0, gt=0, le=120)
    account_sync_enabled: bool = False
    realtime_enabled: bool = False
    realtime_source: Literal["polling", "kis"] = "polling"
    realtime_poll_interval_seconds: float = Field(default=2.0, ge=1.0, le=10.0)
    realtime_cache_ttl_seconds: int = Field(default=3, ge=1, le=30)
    realtime_max_symbols: int = Field(default=20, ge=1, le=100)
    realtime_max_connections: int = Field(default=200, ge=1, le=10_000)
    kis_ws_url: str = "ws://ops.koreainvestment.com:21000/tryitout"
    kis_ws_reconnect_max_seconds: float = Field(default=30.0, ge=1.0, le=300.0)

    @model_validator(mode="after")
    def validate_feature_dependencies(self):
        scheduled_symbols = self.scheduled_symbols
        if self.scheduler_enabled and not scheduled_symbols:
            raise ValueError("SCHEDULER_ENABLED requires at least one SCHEDULER_SYMBOLS value")
        if len(scheduled_symbols) > 50:
            raise ValueError("SCHEDULER_SYMBOLS supports at most 50 symbols")
        if any(not re.fullmatch(r"[0-9A-Z.-]{1,16}", symbol) for symbol in scheduled_symbols):
            raise ValueError("SCHEDULER_SYMBOLS contains an invalid symbol")
        if self.scheduler_enabled and not self.persistence_enabled:
            raise ValueError("SCHEDULER_ENABLED requires PERSISTENCE_ENABLED=true")
        if self.partition_maintenance_enabled and not self.persistence_enabled:
            raise ValueError("PARTITION_MAINTENANCE_ENABLED requires PERSISTENCE_ENABLED=true")
        if self.provider_audit_cleanup_enabled and not self.persistence_enabled:
            raise ValueError("PROVIDER_AUDIT_CLEANUP_ENABLED requires PERSISTENCE_ENABLED=true")
        if self.reference_alerts_enabled and not self.persistence_enabled:
            raise ValueError("REFERENCE_ALERTS_ENABLED requires PERSISTENCE_ENABLED=true")
        origins = self.allowed_origins
        if not origins or any(not origin.startswith(("http://", "https://")) for origin in origins):
            raise ValueError("CORS_ORIGINS must contain comma-separated HTTP(S) origins")
        if self.app_environment.casefold() == "production":
            admin_key = self.admin_api_key.get_secret_value() if self.admin_api_key else ""
            if admin_key and len(admin_key) < 32:
                raise ValueError("Production ADMIN_API_KEY must contain 32+ characters")
            if (self.account_sync_enabled or self.reference_alerts_enabled) and not admin_key:
                raise ValueError(
                    "Production account sync and reference alerts require a 32+ character ADMIN_API_KEY"
                )
            if self.persistence_enabled and self.database_url.startswith("sqlite"):
                raise ValueError("Production persistence requires PostgreSQL, not SQLite")
            for name, url in self._active_http_provider_urls():
                if not url.casefold().startswith("https://"):
                    raise ValueError(f"Production {name} must use HTTPS")
        return self

    def _active_http_provider_urls(self) -> list[tuple[str, str]]:
        urls: list[tuple[str, str]] = []
        if self.stock_provider == "toss" or self.account_sync_enabled:
            urls.append(("TOSS_BASE_URL", self.toss_base_url))
        if self.financial_provider == "dart" or self.disclosure_provider == "dart":
            urls.append(("DART_BASE_URL", self.dart_base_url))
        if self.news_provider == "rss":
            urls.append(("NEWS_RSS_SEARCH_URL", self.news_rss_search_url))
        if self.investor_flow_provider == "kis":
            urls.append(("KIS_BASE_URL", self.kis_base_url))
        if self.ai_report_provider == "openai":
            urls.append(("OPENAI_BASE_URL", self.openai_base_url))
        return urls

    @property
    def allowed_origins(self) -> list[str]:
        return [
            origin.strip().rstrip("/") for origin in self.cors_origins.split(",") if origin.strip()
        ]

    @property
    def scheduled_symbols(self) -> list[str]:
        return list(
            dict.fromkeys(
                symbol.strip().upper()
                for symbol in self.scheduler_symbols.split(",")
                if symbol.strip()
            )
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
