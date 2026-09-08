"""settings 파일은 백엔드 도메인 기능을 담당한다."""

from functools import lru_cache
import re
from typing import Literal

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """`Settings` 관련 상태와 동작을 하나의 객체로 묶습니다."""

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        hide_input_in_errors=True,
    )

    database_url: str = "sqlite:///./stockpilot.db"
    redis_url: str = "redis://localhost:6379/0"
    scheduler_enabled: bool = False
    scheduler_interval_minutes: int = 5
    scheduler_symbols: str = "005930,000660,035420,AAPL,MSFT"
    scheduler_ingestion_limit: int = Field(default=120, ge=30, le=365)
    partition_maintenance_enabled: bool = False
    partition_lookahead_months: int = Field(default=3, ge=1, le=12)
    partition_archive_after_months: int = Field(default=120, ge=12, le=600)
    provider_audit_cleanup_enabled: bool = False
    provider_audit_retention_days: int = Field(default=90, ge=7, le=3650)
    provider_audit_cleanup_hour_kst: int = Field(default=4, ge=0, le=23)
    data_lifecycle_cleanup_enabled: bool = False
    data_lifecycle_cleanup_hour_kst: int = Field(default=4, ge=0, le=23)
    data_quality_retention_days: int = Field(default=180, ge=30, le=3650)
    news_retention_days: int = Field(default=730, ge=30, le=3650)
    disclosure_retention_days: int = Field(default=3650, ge=365, le=7300)
    persistence_enabled: bool = False
    corporate_action_approval_enabled: bool = False
    admin_api_key: SecretStr | None = None
    analysis_api_key: SecretStr | None = None
    admin_max_failed_attempts: int = Field(default=5, ge=3, le=20)
    admin_lockout_seconds: int = Field(default=60, ge=10, le=3600)
    cors_origins: str = (
        "http://localhost:3000,http://localhost:8080,"
        "http://127.0.0.1:3000,http://127.0.0.1:8080"
    )
    allowed_hosts: str = "localhost,127.0.0.1,testserver"
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
    news_api_base_url: str = "https://newsapi.org/v2"
    news_api_key: SecretStr | None = None
    news_api_daily_request_limit: int = Field(default=90, ge=1, le=100)
    news_training_source: Literal["newsapi", "gdelt", "both", "official_rss"] = "gdelt"
    gdelt_doc_api_url: str = "https://api.gdeltproject.org/api/v2/doc/doc"
    gdelt_daily_request_limit: int = Field(default=80, ge=1, le=5000)
    official_rss_enabled: bool = True
    official_rss_daily_request_limit: int = Field(default=12, ge=3, le=100)
    alpha_vantage_base_url: str = "https://www.alphavantage.co/query"
    alpha_vantage_api_key: SecretStr | None = None
    alpha_vantage_daily_request_limit: int = Field(default=25, ge=1, le=25)
    fred_base_url: str = "https://api.stlouisfed.org/fred"
    fred_api_key: SecretStr | None = None
    finra_api_base_url: str = "https://api.finra.org"
    finra_token_url: str = (
        "https://ews.fip.finra.org/fip/rest/ews/oauth2/access_token"
    )
    finra_client_id: str | None = None
    finra_client_secret: SecretStr | None = None
    sec_base_url: str = "https://data.sec.gov"
    sec_user_agent: str | None = None
    investor_flow_provider: Literal["mock", "kis"] = "mock"
    prediction_engine: Literal["lightweight", "xgboost"] = "lightweight"
    model_artifact_activation_enabled: bool = False
    model_artifact_dir: str = "./artifacts/models"
    local_ai_enabled: bool = False
    local_ai_artifact_dir: str = "./artifacts/local-ai"
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
    toss_trading_enabled: bool = False
    realtime_enabled: bool = False
    realtime_source: Literal["polling", "kis", "toss"] = "polling"
    realtime_poll_interval_seconds: float = Field(default=2.0, ge=1.0, le=10.0)
    realtime_cache_ttl_seconds: int = Field(default=3, ge=1, le=30)
    realtime_max_symbols: int = Field(default=20, ge=1, le=100)
    realtime_max_connections: int = Field(default=200, ge=1, le=10_000)
    kis_ws_url: str = "ws://ops.koreainvestment.com:21000/tryitout"
    kis_ws_reconnect_max_seconds: float = Field(default=30.0, ge=1.0, le=300.0)
    toss_ws_url: str = "wss://openapi-ws.tossinvest.com/ws/v1"
    toss_ws_reconnect_max_seconds: float = Field(default=30.0, ge=1.0, le=300.0)

    @model_validator(mode="after")
    def validate_feature_dependencies(self):
        """`validate_feature_dependencies`은(는) 입력 또는 현재 상태가 규칙을 만족하는지 검증합니다."""

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
        if self.data_lifecycle_cleanup_enabled and not self.persistence_enabled:
            raise ValueError("DATA_LIFECYCLE_CLEANUP_ENABLED requires PERSISTENCE_ENABLED=true")
        if self.reference_alerts_enabled and not self.persistence_enabled:
            raise ValueError("REFERENCE_ALERTS_ENABLED requires PERSISTENCE_ENABLED=true")
        if self.corporate_action_approval_enabled:
            if not self.persistence_enabled:
                raise ValueError(
                    "CORPORATE_ACTION_APPROVAL_ENABLED requires PERSISTENCE_ENABLED=true"
                )
            if not self.admin_api_key or not self.admin_api_key.get_secret_value():
                raise ValueError("CORPORATE_ACTION_APPROVAL_ENABLED requires ADMIN_API_KEY")
            if not self.dart_api_key or not self.dart_api_key.get_secret_value():
                raise ValueError("CORPORATE_ACTION_APPROVAL_ENABLED requires DART_API_KEY")
        toss_secret = (
            self.toss_client_secret.get_secret_value().strip()
            if self.toss_client_secret
            else ""
        )
        if self.stock_provider == "toss" and (
            not self.toss_client_id or not self.toss_client_id.strip() or not toss_secret
        ):
            raise ValueError(
                "STOCK_PROVIDER=toss requires TOSS_CLIENT_ID and TOSS_CLIENT_SECRET"
            )
        if self.toss_trading_enabled:
            admin_key = self.admin_api_key.get_secret_value() if self.admin_api_key else ""
            if self.stock_provider != "toss" or not self.account_sync_enabled:
                raise ValueError(
                    "TOSS_TRADING_ENABLED requires STOCK_PROVIDER=toss and ACCOUNT_SYNC_ENABLED=true"
                )
            if len(admin_key) < 32:
                raise ValueError("TOSS_TRADING_ENABLED requires a 32+ character ADMIN_API_KEY")
        if self.realtime_enabled and self.realtime_source == "toss" and self.stock_provider != "toss":
            raise ValueError("REALTIME_SOURCE=toss requires STOCK_PROVIDER=toss")
        dart_key = self.dart_api_key.get_secret_value().strip() if self.dart_api_key else ""
        if (
            self.financial_provider == "dart"
            or self.disclosure_provider == "dart"
            or self.corporate_action_approval_enabled
        ) and not dart_key:
            raise ValueError("Active DART features require DART_API_KEY")
        kis_key = self.kis_app_key.get_secret_value().strip() if self.kis_app_key else ""
        kis_secret = (
            self.kis_app_secret.get_secret_value().strip() if self.kis_app_secret else ""
        )
        kis_enabled = self.investor_flow_provider == "kis" or (
            self.realtime_enabled and self.realtime_source == "kis"
        )
        if kis_enabled and (not kis_key or not kis_secret):
            raise ValueError("Active KIS features require KIS_APP_KEY and KIS_APP_SECRET")
        openai_key = (
            self.openai_api_key.get_secret_value().strip() if self.openai_api_key else ""
        )
        if self.ai_report_provider == "openai" and not openai_key:
            raise ValueError("AI_REPORT_PROVIDER=openai requires OPENAI_API_KEY")
        if self.model_artifact_activation_enabled:
            if self.prediction_engine != "xgboost":
                raise ValueError("MODEL_ARTIFACT_ACTIVATION_ENABLED requires PREDICTION_ENGINE=xgboost")
            if not self.persistence_enabled:
                raise ValueError("MODEL_ARTIFACT_ACTIVATION_ENABLED requires PERSISTENCE_ENABLED=true")
            if not self.admin_api_key or not self.admin_api_key.get_secret_value():
                raise ValueError("MODEL_ARTIFACT_ACTIVATION_ENABLED requires ADMIN_API_KEY")
        origins = self.allowed_origins
        if not origins or any(not origin.startswith(("http://", "https://")) for origin in origins):
            raise ValueError("CORS_ORIGINS must contain comma-separated HTTP(S) origins")
        hosts = self.trusted_hosts
        if not hosts or any(
            "://" in host or "/" in host or not re.fullmatch(r"\*|\*\.[A-Za-z0-9.-]+|[A-Za-z0-9.-]+", host)
            for host in hosts
        ):
            raise ValueError("ALLOWED_HOSTS must contain comma-separated host names without ports")
        if self.app_environment.casefold() == "production":
            admin_key = self.admin_api_key.get_secret_value() if self.admin_api_key else ""
            analysis_key = (
                self.analysis_api_key.get_secret_value() if self.analysis_api_key else ""
            )
            if admin_key and len(admin_key) < 32:
                raise ValueError("Production ADMIN_API_KEY must contain 32+ characters")
            if (self.account_sync_enabled or self.reference_alerts_enabled) and not admin_key:
                raise ValueError(
                    "Production account sync and reference alerts require a 32+ character ADMIN_API_KEY"
                )
            if self.persistence_enabled and not self.database_url.casefold().startswith(
                ("postgresql://", "postgresql+")
            ):
                raise ValueError("Production persistence requires PostgreSQL DATABASE_URL")
            if "*" in hosts:
                raise ValueError("Production ALLOWED_HOSTS must not contain a wildcard host")
            if len(analysis_key) < 32:
                raise ValueError("Production ANALYSIS_API_KEY must contain 32+ characters")
            for name, url in self._active_http_provider_urls():
                if not url.casefold().startswith("https://"):
                    raise ValueError(f"Production {name} must use HTTPS")
        return self

    def _active_http_provider_urls(self) -> list[tuple[str, str]]:
        """`_active_http_provider_urls`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        urls: list[tuple[str, str]] = []
        if self.stock_provider == "toss" or self.account_sync_enabled:
            urls.append(("TOSS_BASE_URL", self.toss_base_url))
        if (
            self.financial_provider == "dart"
            or self.disclosure_provider == "dart"
            or self.corporate_action_approval_enabled
        ):
            urls.append(("DART_BASE_URL", self.dart_base_url))
        if self.news_provider == "rss":
            urls.append(("NEWS_RSS_SEARCH_URL", self.news_rss_search_url))
        if self.investor_flow_provider == "kis":
            urls.append(("KIS_BASE_URL", self.kis_base_url))
        if self.ai_report_provider == "openai":
            urls.append(("OPENAI_BASE_URL", self.openai_base_url))
        if self.local_ai_enabled:
            if self.news_training_source in {"gdelt", "both"}:
                urls.append(("GDELT_DOC_API_URL", self.gdelt_doc_api_url))
            if self.news_api_key:
                urls.append(("NEWS_API_BASE_URL", self.news_api_base_url))
            if self.fred_api_key:
                urls.append(("FRED_BASE_URL", self.fred_base_url))
            if self.finra_client_id or self.finra_client_secret:
                urls.extend(
                    (
                        ("FINRA_API_BASE_URL", self.finra_api_base_url),
                        ("FINRA_TOKEN_URL", self.finra_token_url),
                    )
                )
            if self.sec_user_agent:
                urls.append(("SEC_BASE_URL", self.sec_base_url))
        return urls

    @property
    def allowed_origins(self) -> list[str]:
        """`allowed_origins`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        return [
            origin.strip().rstrip("/") for origin in self.cors_origins.split(",") if origin.strip()
        ]

    @property
    def trusted_hosts(self) -> list[str]:
        """`trusted_hosts`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        return list(
            dict.fromkeys(host.strip().casefold() for host in self.allowed_hosts.split(",") if host.strip())
        )

    @property
    def scheduled_symbols(self) -> list[str]:
        """`scheduled_symbols`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        return list(
            dict.fromkeys(
                symbol.strip().upper()
                for symbol in self.scheduler_symbols.split(",")
                if symbol.strip()
            )
        )

    @property
    def data_retention_days(self) -> dict[str, int]:
        """`data_retention_days`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        return {
            "data_quality_logs": self.data_quality_retention_days,
            "news": self.news_retention_days,
            "disclosures": self.disclosure_retention_days,
        }


@lru_cache
def get_settings() -> Settings:
    """`get_settings`은(는) 필요한 데이터를 조회해 반환합니다."""

    return Settings()
