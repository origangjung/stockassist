import pytest

from app.config import Settings


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"stock_provider": "toss"}, "TOSS_CLIENT_ID"),
        ({"financial_provider": "dart"}, "DART_API_KEY"),
        ({"disclosure_provider": "dart"}, "DART_API_KEY"),
        ({"investor_flow_provider": "kis"}, "KIS_APP_KEY"),
        ({"ai_report_provider": "openai"}, "OPENAI_API_KEY"),
        ({"realtime_enabled": True, "realtime_source": "kis"}, "KIS_APP_KEY"),
    ],
)
def test_active_external_features_require_credentials(overrides, message):
    with pytest.raises(ValueError, match=message):
        Settings(_env_file=None, **overrides)


def test_whitespace_only_external_credentials_are_rejected():
    with pytest.raises(ValueError, match="TOSS_CLIENT_SECRET"):
        Settings(
            _env_file=None,
            stock_provider="toss",
            toss_client_id="client-id",
            toss_client_secret="   ",
        )


def test_validation_errors_do_not_echo_secret_inputs():
    marker = "SENSITIVE_TEST_MARKER_9f3a"

    with pytest.raises(ValueError) as error:
        Settings(
            _env_file=None,
            stock_provider="toss",
            toss_client_id="client-id",
            toss_client_secret=marker,
            cors_origins="invalid-origin",
        )

    rendered = str(error.value)
    assert marker not in rendered
    assert "input_value=" not in rendered


def test_external_features_accept_complete_credentials():
    settings = Settings(
        _env_file=None,
        stock_provider="toss",
        toss_client_id="client-id",
        toss_client_secret="client-secret",
        financial_provider="dart",
        disclosure_provider="dart",
        dart_api_key="dart-key",
        investor_flow_provider="kis",
        kis_app_key="kis-key",
        kis_app_secret="kis-secret",
        ai_report_provider="openai",
        openai_api_key="openai-key",
        realtime_enabled=True,
        realtime_source="kis",
    )

    assert settings.stock_provider == "toss"
    assert settings.financial_provider == "dart"
    assert settings.investor_flow_provider == "kis"
    assert settings.ai_report_provider == "openai"


def test_disabled_kis_realtime_source_does_not_require_credentials():
    settings = Settings(
        _env_file=None,
        realtime_enabled=False,
        realtime_source="kis",
    )

    assert settings.realtime_enabled is False


def test_corporate_action_approval_requires_dart_credentials():
    with pytest.raises(ValueError, match="DART_API_KEY"):
        Settings(
            _env_file=None,
            persistence_enabled=True,
            corporate_action_approval_enabled=True,
            admin_api_key="admin-key",
        )


def test_model_artifact_activation_requires_xgboost_mode():
    with pytest.raises(ValueError, match="PREDICTION_ENGINE=xgboost"):
        Settings(
            _env_file=None,
            persistence_enabled=True,
            model_artifact_activation_enabled=True,
            prediction_engine="lightweight",
            admin_api_key="admin-key",
        )


def test_production_active_provider_urls_require_https():
    with pytest.raises(ValueError, match="Production TOSS_BASE_URL must use HTTPS"):
        Settings(
            _env_file=None,
            app_environment="production",
            persistence_enabled=True,
            database_url="postgresql+psycopg://stockpilot:password@database/stockpilot",
            admin_api_key="a" * 32,
            analysis_api_key="b" * 32,
            cors_origins="https://stocks.example.com",
            allowed_hosts="stocks.example.com",
            stock_provider="toss",
            toss_client_id="client-id",
            toss_client_secret="client-secret",
            toss_base_url="http://toss.example.com",
        )


def test_production_account_sync_toss_url_requires_https():
    with pytest.raises(ValueError, match="Production TOSS_BASE_URL must use HTTPS"):
        Settings(
            _env_file=None,
            app_environment="production",
            persistence_enabled=True,
            database_url="postgresql+psycopg://stockpilot:password@database/stockpilot",
            admin_api_key="a" * 32,
            analysis_api_key="b" * 32,
            cors_origins="https://stocks.example.com",
            allowed_hosts="stocks.example.com",
            account_sync_enabled=True,
            toss_base_url="http://toss.example.com",
        )


def test_production_persistence_rejects_non_postgresql_database_url():
    with pytest.raises(ValueError, match="requires PostgreSQL DATABASE_URL"):
        Settings(
            _env_file=None,
            app_environment="production",
            admin_api_key="a" * 32,
            analysis_api_key="b" * 32,
            persistence_enabled=True,
            database_url="mysql+pymysql://stockpilot:secret@database/stockpilot",
        )
