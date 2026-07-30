from scripts.check_production_env import validate_production_environment


def _valid_environment() -> dict[str, str]:
    postgres_password = "postgres-production-password"
    return {
        "APP_ENVIRONMENT": "production",
        "PERSISTENCE_ENABLED": "true",
        "RATE_LIMIT_ENABLED": "true",
        "RATE_LIMIT_BACKEND": "redis",
        "TRUST_PROXY_HEADERS": "true",
        "METRICS_ENABLED": "true",
        "LOG_FORMAT": "json",
        "DATABASE_URL": (
            "postgresql+psycopg://stockpilot:"
            f"{postgres_password}@postgres:5432/stockpilot"
        ),
        "POSTGRES_DB": "stockpilot",
        "POSTGRES_USER": "stockpilot",
        "POSTGRES_PASSWORD": postgres_password,
        "REDIS_URL": "redis://redis:6379/0",
        "PUBLIC_API_URL": "https://stocks.example.com",
        "CORS_ORIGINS": "https://stocks.example.com",
        "ALLOWED_HOSTS": "stocks.example.com,api",
        "ADMIN_API_KEY": "a" * 32,
        "ANALYSIS_API_KEY": "b" * 32,
        "ADMIN_UI_USERNAME": "operator",
        "ADMIN_UI_PASSWORD": "admin-ui-password",
        "GRAFANA_ADMIN_PASSWORD": "grafana-password",
        "STOCK_PROVIDER": "mock",
        "FINANCIAL_PROVIDER": "mock",
        "DISCLOSURE_PROVIDER": "mock",
        "NEWS_PROVIDER": "mock",
        "INVESTOR_FLOW_PROVIDER": "mock",
        "AI_REPORT_PROVIDER": "mock",
        "PREDICTION_ENGINE": "lightweight",
        "REALTIME_ENABLED": "false",
        "REALTIME_SOURCE": "polling",
        "TOSS_BASE_URL": "https://openapi.tossinvest.com",
        "DART_BASE_URL": "https://opendart.fss.or.kr/api",
        "NEWS_RSS_SEARCH_URL": "https://news.example.com/rss?q={query}",
        "KIS_BASE_URL": "https://openapi.koreainvestment.com:9443",
        "OPENAI_BASE_URL": "https://api.openai.com/v1",
    }


def test_valid_production_environment_passes():
    assert validate_production_environment(_valid_environment()) == []


def test_preflight_rejects_local_urls_defaults_and_mismatched_database_password():
    values = _valid_environment()
    values.update(
        {
            "PUBLIC_API_URL": "http://localhost:8080",
            "CORS_ORIGINS": "http://localhost:3000",
            "ALLOWED_HOSTS": "localhost,*",
            "POSTGRES_PASSWORD": "another-production-password",
            "ADMIN_API_KEY": "change-me",
        }
    )

    violations = validate_production_environment(values)

    assert "PUBLIC_API_URL: must be an absolute HTTPS URL" in violations
    assert "PUBLIC_API_URL: must not use a local host" in violations
    assert "CORS_ORIGINS: every production origin must use HTTPS" in violations
    assert "ALLOWED_HOSTS: global wildcard is not allowed" in violations
    assert "DATABASE_URL and POSTGRES_PASSWORD: passwords must match" in violations
    assert "ADMIN_API_KEY: must contain 32+ non-placeholder characters" in violations


def test_enabled_external_providers_require_credentials():
    values = _valid_environment()
    values.update(
        {
            "STOCK_PROVIDER": "toss",
            "FINANCIAL_PROVIDER": "dart",
            "INVESTOR_FLOW_PROVIDER": "kis",
            "AI_REPORT_PROVIDER": "openai",
        }
    )

    violations = validate_production_environment(values)

    assert "TOSS_CLIENT_ID: is required" in violations
    assert "TOSS_CLIENT_SECRET: is required" in violations
    assert "DART_API_KEY: is required" in violations
    assert "KIS_APP_KEY: is required" in violations
    assert "KIS_APP_SECRET: is required" in violations
    assert "OPENAI_API_KEY: is required" in violations


def test_preflight_messages_never_include_secret_values():
    values = _valid_environment()
    marker = "SENSITIVE_TEST_MARKER_42"
    values["POSTGRES_PASSWORD"] = marker
    values["ADMIN_API_KEY"] = marker

    rendered = "\n".join(validate_production_environment(values))

    assert marker not in rendered


def test_percent_encoded_database_password_matches_plain_postgres_password():
    values = _valid_environment()
    password = "postgres-password@2026"
    values["POSTGRES_PASSWORD"] = password
    values["DATABASE_URL"] = (
        "postgresql+psycopg://stockpilot:postgres-password%402026@postgres:5432/stockpilot"
    )

    assert validate_production_environment(values) == []


def test_preflight_matches_corporate_action_and_artifact_dependencies():
    corporate_action_values = _valid_environment()
    corporate_action_values["CORPORATE_ACTION_APPROVAL_ENABLED"] = "true"

    corporate_action_violations = validate_production_environment(corporate_action_values)

    assert "DART_API_KEY: is required" in corporate_action_violations

    artifact_values = _valid_environment()
    artifact_values["MODEL_ARTIFACT_ACTIVATION_ENABLED"] = "true"

    artifact_violations = validate_production_environment(artifact_values)

    assert (
        "MODEL_ARTIFACT_ACTIVATION_ENABLED: requires PREDICTION_ENGINE=xgboost"
        in artifact_violations
    )


def test_active_provider_urls_require_https():
    values = _valid_environment()
    values.update(
        {
            "STOCK_PROVIDER": "toss",
            "TOSS_CLIENT_ID": "toss-client",
            "TOSS_CLIENT_SECRET": "toss-secret",
            "FINANCIAL_PROVIDER": "dart",
            "DART_API_KEY": "dart-key",
            "NEWS_PROVIDER": "rss",
            "INVESTOR_FLOW_PROVIDER": "kis",
            "KIS_APP_KEY": "kis-key",
            "KIS_APP_SECRET": "kis-secret",
            "AI_REPORT_PROVIDER": "openai",
            "OPENAI_API_KEY": "openai-key",
            "TOSS_BASE_URL": "http://toss.example.com",
            "DART_BASE_URL": "http://dart.example.com",
            "NEWS_RSS_SEARCH_URL": "http://news.example.com/rss?q={query}",
            "KIS_BASE_URL": "http://kis.example.com",
            "OPENAI_BASE_URL": "http://openai.example.com",
        }
    )

    violations = validate_production_environment(values)

    for name in (
        "TOSS_BASE_URL",
        "DART_BASE_URL",
        "NEWS_RSS_SEARCH_URL",
        "KIS_BASE_URL",
        "OPENAI_BASE_URL",
    ):
        assert f"{name}: must be an absolute HTTPS URL" in violations


def test_account_sync_also_requires_an_https_toss_base_url():
    values = _valid_environment()
    values.update(
        {
            "ACCOUNT_SYNC_ENABLED": "true",
            "TOSS_BASE_URL": "http://toss.example.com",
        }
    )

    violations = validate_production_environment(values)

    assert "TOSS_BASE_URL: must be an absolute HTTPS URL" in violations


def test_preflight_rejects_unknown_provider_or_prediction_modes():
    values = _valid_environment()
    values.update({"NEWS_PROVIDER": "unknown", "PREDICTION_ENGINE": "custom"})

    violations = validate_production_environment(values)

    assert "NEWS_PROVIDER: must be one of mock, rss" in violations
    assert "PREDICTION_ENGINE: must be one of lightweight, xgboost" in violations
