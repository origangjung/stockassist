"""Secret-safe production environment preflight.

Run explicitly with ``python -m scripts.check_production_env --env-file PATH``.
The command never prints environment values.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from urllib.parse import unquote, urlsplit

from scripts.check_env_contract import parse_env_template


PLACEHOLDERS = {"", "change-me"}
LOCAL_HOSTS = {"127.0.0.1", "::1", "localhost", "testserver"}


def _enabled(value: str | None) -> bool:
    return (value or "").strip().casefold() in {"1", "true", "yes", "on"}


def _usable_secret(value: str | None, *, minimum: int = 1) -> bool:
    candidate = (value or "").strip()
    return candidate not in PLACEHOLDERS and len(candidate) >= minimum


def _parsed_url(value: str | None):
    try:
        return urlsplit((value or "").strip())
    except ValueError:
        return None


def _choice(
    values: dict[str, str],
    name: str,
    allowed: set[str],
    *,
    default: str,
    violations: list[str],
) -> str:
    value = values.get(name, default).strip().casefold()
    if value not in allowed:
        violations.append(f"{name}: must be one of {', '.join(sorted(allowed))}")
    return value


def _active_http_provider_urls(
    values: dict[str, str],
    *,
    stock_provider: str,
    financial_provider: str,
    disclosure_provider: str,
    news_provider: str,
    investor_flow_provider: str,
    ai_report_provider: str,
) -> list[tuple[str, str | None]]:
    corporate_action_approval_enabled = _enabled(values.get("CORPORATE_ACTION_APPROVAL_ENABLED"))
    urls: list[tuple[str, str | None]] = []
    if stock_provider == "toss" or _enabled(values.get("ACCOUNT_SYNC_ENABLED")):
        urls.append(("TOSS_BASE_URL", values.get("TOSS_BASE_URL")))
    if (
        financial_provider == "dart"
        or disclosure_provider == "dart"
        or corporate_action_approval_enabled
    ):
        urls.append(("DART_BASE_URL", values.get("DART_BASE_URL")))
    if news_provider == "rss":
        urls.append(("NEWS_RSS_SEARCH_URL", values.get("NEWS_RSS_SEARCH_URL")))
    if investor_flow_provider == "kis":
        urls.append(("KIS_BASE_URL", values.get("KIS_BASE_URL")))
    if ai_report_provider == "openai":
        urls.append(("OPENAI_BASE_URL", values.get("OPENAI_BASE_URL")))
    return urls


def validate_production_environment(values: dict[str, str]) -> list[str]:
    violations: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            violations.append(message)

    require(
        values.get("APP_ENVIRONMENT", "").casefold() == "production",
        "APP_ENVIRONMENT: must be production",
    )
    require(_enabled(values.get("PERSISTENCE_ENABLED")), "PERSISTENCE_ENABLED: must be true")
    require(_enabled(values.get("RATE_LIMIT_ENABLED")), "RATE_LIMIT_ENABLED: must be true")
    require(
        values.get("RATE_LIMIT_BACKEND", "").casefold() == "redis",
        "RATE_LIMIT_BACKEND: must be redis",
    )
    require(_enabled(values.get("TRUST_PROXY_HEADERS")), "TRUST_PROXY_HEADERS: must be true")
    require(_enabled(values.get("METRICS_ENABLED")), "METRICS_ENABLED: must be true")
    require(values.get("LOG_FORMAT", "").casefold() == "json", "LOG_FORMAT: must be json")

    database = _parsed_url(values.get("DATABASE_URL"))
    database_scheme = database.scheme.casefold() if database else ""
    require(
        database_scheme == "postgresql" or database_scheme.startswith("postgresql+"),
        "DATABASE_URL: must use PostgreSQL",
    )
    require(bool(database and database.hostname), "DATABASE_URL: database host is required")
    require(bool(database and database.username), "DATABASE_URL: database user is required")
    database_password = unquote(database.password) if database and database.password else ""
    require(
        _usable_secret(database_password, minimum=16),
        "DATABASE_URL: database password must contain 16+ non-placeholder characters",
    )

    postgres_password = values.get("POSTGRES_PASSWORD")
    require(
        _usable_secret(postgres_password, minimum=16),
        "POSTGRES_PASSWORD: must contain 16+ non-placeholder characters",
    )
    require(bool(values.get("POSTGRES_DB", "").strip()), "POSTGRES_DB: is required")
    require(bool(values.get("POSTGRES_USER", "").strip()), "POSTGRES_USER: is required")
    if database_password and _usable_secret(postgres_password):
        require(
            database_password == postgres_password,
            "DATABASE_URL and POSTGRES_PASSWORD: passwords must match",
        )

    redis = _parsed_url(values.get("REDIS_URL"))
    require(
        bool(redis and redis.scheme.casefold() in {"redis", "rediss"} and redis.hostname),
        "REDIS_URL: must be a valid Redis URL",
    )

    public_url = _parsed_url(values.get("PUBLIC_API_URL"))
    public_host = public_url.hostname.casefold() if public_url and public_url.hostname else ""
    require(
        bool(public_url and public_url.scheme.casefold() == "https" and public_host),
        "PUBLIC_API_URL: must be an absolute HTTPS URL",
    )
    require(public_host not in LOCAL_HOSTS, "PUBLIC_API_URL: must not use a local host")

    origins = [item.strip() for item in values.get("CORS_ORIGINS", "").split(",") if item.strip()]
    valid_origins = []
    for origin in origins:
        parsed = _parsed_url(origin)
        if parsed and parsed.scheme.casefold() == "https" and parsed.hostname:
            valid_origins.append(parsed)
    require(bool(origins), "CORS_ORIGINS: at least one origin is required")
    require(
        len(valid_origins) == len(origins),
        "CORS_ORIGINS: every production origin must use HTTPS",
    )
    require(
        all((item.hostname or "").casefold() not in LOCAL_HOSTS for item in valid_origins),
        "CORS_ORIGINS: local hosts are not allowed in production",
    )

    hosts = {
        item.strip().casefold()
        for item in values.get("ALLOWED_HOSTS", "").split(",")
        if item.strip()
    }
    require(bool(hosts), "ALLOWED_HOSTS: at least one host is required")
    require("*" not in hosts, "ALLOWED_HOSTS: global wildcard is not allowed")
    require(not (hosts & LOCAL_HOSTS), "ALLOWED_HOSTS: local hosts are not allowed")
    if public_host:
        require(public_host in hosts, "ALLOWED_HOSTS: must include the PUBLIC_API_URL host")

    for name, minimum in (
        ("ADMIN_API_KEY", 32),
        ("ANALYSIS_API_KEY", 32),
        ("ADMIN_UI_PASSWORD", 16),
        ("GRAFANA_ADMIN_PASSWORD", 16),
    ):
        require(
            _usable_secret(values.get(name), minimum=minimum),
            f"{name}: must contain {minimum}+ non-placeholder characters",
        )
    require(bool(values.get("ADMIN_UI_USERNAME", "").strip()), "ADMIN_UI_USERNAME: is required")

    stock_provider = _choice(
        values, "STOCK_PROVIDER", {"mock", "toss"}, default="mock", violations=violations
    )
    financial_provider = _choice(
        values, "FINANCIAL_PROVIDER", {"mock", "dart"}, default="mock", violations=violations
    )
    disclosure_provider = _choice(
        values, "DISCLOSURE_PROVIDER", {"mock", "dart"}, default="mock", violations=violations
    )
    news_provider = _choice(
        values, "NEWS_PROVIDER", {"mock", "rss"}, default="mock", violations=violations
    )
    investor_flow_provider = _choice(
        values, "INVESTOR_FLOW_PROVIDER", {"mock", "kis"}, default="mock", violations=violations
    )
    ai_report_provider = _choice(
        values, "AI_REPORT_PROVIDER", {"mock", "openai"}, default="mock", violations=violations
    )
    prediction_engine = _choice(
        values, "PREDICTION_ENGINE", {"lightweight", "xgboost"}, default="lightweight", violations=violations
    )

    if stock_provider == "toss":
        require(_usable_secret(values.get("TOSS_CLIENT_ID")), "TOSS_CLIENT_ID: is required")
        require(
            _usable_secret(values.get("TOSS_CLIENT_SECRET")),
            "TOSS_CLIENT_SECRET: is required",
        )
    corporate_action_approval_enabled = _enabled(values.get("CORPORATE_ACTION_APPROVAL_ENABLED"))
    dart_enabled = (
        financial_provider == "dart"
        or disclosure_provider == "dart"
        or corporate_action_approval_enabled
    )
    if dart_enabled:
        require(_usable_secret(values.get("DART_API_KEY")), "DART_API_KEY: is required")
    kis_enabled = investor_flow_provider == "kis" or (
        _enabled(values.get("REALTIME_ENABLED"))
        and values.get("REALTIME_SOURCE", "polling").casefold() == "kis"
    )
    if kis_enabled:
        require(_usable_secret(values.get("KIS_APP_KEY")), "KIS_APP_KEY: is required")
        require(_usable_secret(values.get("KIS_APP_SECRET")), "KIS_APP_SECRET: is required")
    if ai_report_provider == "openai":
        require(_usable_secret(values.get("OPENAI_API_KEY")), "OPENAI_API_KEY: is required")
    if _enabled(values.get("MODEL_ARTIFACT_ACTIVATION_ENABLED")):
        require(
            prediction_engine == "xgboost",
            "MODEL_ARTIFACT_ACTIVATION_ENABLED: requires PREDICTION_ENGINE=xgboost",
        )
        require(
            _enabled(values.get("PERSISTENCE_ENABLED")),
            "MODEL_ARTIFACT_ACTIVATION_ENABLED: requires PERSISTENCE_ENABLED=true",
        )

    for name, value in _active_http_provider_urls(
        values,
        stock_provider=stock_provider,
        financial_provider=financial_provider,
        disclosure_provider=disclosure_provider,
        news_provider=news_provider,
        investor_flow_provider=investor_flow_provider,
        ai_report_provider=ai_report_provider,
    ):
        parsed = _parsed_url(value)
        require(
            bool(parsed and parsed.scheme.casefold() == "https" and parsed.hostname),
            f"{name}: must be an absolute HTTPS URL",
        )

    return violations


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a production env file without printing values")
    parser.add_argument("--env-file", required=True, type=Path)
    args = parser.parse_args()

    if not args.env_file.is_file():
        print("Production preflight failed: the requested env file does not exist.")
        return 1
    values, parse_violations = parse_env_template(args.env_file)
    violations = parse_violations + validate_production_environment(values)
    if violations:
        print("Production preflight failed:")
        for violation in violations:
            print(f"- {violation}")
        print("No environment values were printed.")
        return 1
    print("Production environment preflight passed. No environment values were printed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
