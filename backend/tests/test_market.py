from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_quote_contains_compliance_metadata():
    response = client.get(
        "/api/v1/stocks/005930/quote", headers={"X-Request-ID": "test-request-id"}
    )
    body = response.json()
    assert response.status_code == 200
    assert body["success"] is True
    assert body["data"]["provider"] == "mock"
    assert body["data"]["symbol"] == "005930"
    assert body["is_investment_advice"] is False
    assert body["disclaimer"]
    assert body["request_id"] == "test-request-id"
    assert response.headers["X-Request-ID"] == "test-request-id"


def test_unknown_symbol_is_not_found():
    response = client.get("/api/v1/stocks/999999/quote")
    assert response.status_code == 404
    assert response.json()["success"] is False
    assert response.json()["error"]["code"] == "HTTP_404"
    assert response.json()["request_id"] == response.headers["X-Request-ID"]
    assert response.json()["is_investment_advice"] is False


def test_candle_limit_is_applied():
    response = client.get("/api/v1/stocks/005930/candles?limit=3")
    assert response.status_code == 200
    assert len(response.json()["data"]["candles"]) == 3


def test_stock_information_and_trades_follow_provider_contract():
    stock = client.get("/api/v1/stocks/035420")
    trades = client.get("/api/v1/stocks/035420/trades?limit=4")
    assert stock.status_code == 200
    assert stock.json()["data"]["market"] == "KOSDAQ"
    assert trades.status_code == 200
    assert len(trades.json()["data"]["trades"]) == 4
    assert {trade["side"] for trade in trades.json()["data"]["trades"]} <= {"buy", "sell"}


def test_us_stock_quote_and_chart_are_available_from_the_same_api():
    quote = client.get("/api/v1/stocks/AAPL/quote")
    chart = client.get("/api/v1/stocks/AAPL/candles/processed?interval=1d&limit=30")

    assert quote.status_code == 200
    assert quote.json()["data"]["currency"] == "USD"
    assert chart.status_code == 200
    assert chart.json()["data"]["symbol"] == "AAPL"


def test_warning_endpoint_uses_capability_routing():
    response = client.get("/api/v1/stocks/005930/warnings")
    assert response.status_code == 200
    assert response.json()["data"] == {
        "symbol": "005930",
        "provider": "mock",
        "warnings": [],
    }


def test_pattern_endpoint_returns_experimental_structured_analysis():
    response = client.get("/api/v1/stocks/005930/patterns?limit=60")
    body = response.json()["data"]

    assert response.status_code == 200
    assert body["provider"] == "mock"
    assert body["engine_version"] == "patterns-2026.1"
    assert body["validation_status"] == "experimental"
    assert isinstance(body["patterns"], list)


def test_investor_flow_endpoint_is_experimental_reference_data():
    response = client.get("/api/v1/stocks/005930/investor-flow")
    body = response.json()

    assert response.status_code == 200
    assert body["data"]["provider"] == "mock"
    assert body["data"]["experimental"] is True
    assert body["data"]["reference_signal"] == "net_inflow"


def test_financial_endpoint_returns_normalized_snapshot():
    response = client.get("/api/v1/stocks/005930/financials?fiscal_year=2025")
    assert response.status_code == 200
    body = response.json()["data"]
    assert body["symbol"] == "005930"
    assert body["provider"] == "mock"
    assert body["revenue"] is not None


def test_content_endpoints_are_experimental():
    disclosures = client.get("/api/v1/stocks/005930/disclosures")
    news = client.get("/api/v1/stocks/005930/news")

    assert disclosures.status_code == 200
    assert disclosures.json()["data"]["experimental"] is True
    assert news.status_code == 200
    assert news.json()["data"]["sentiment_label"] == "neutral"


def test_processed_candles_have_aggregation_metadata():
    response = client.get("/api/v1/stocks/005930/candles/processed?interval=1w&limit=30")
    body = response.json()["data"]
    assert response.status_code == 200
    assert body["raw_count"] == 30
    assert body["aggregation_version"] == "2026.2"
    assert 4 <= len(body["candles"]) <= 6


def test_backtest_api_exposes_experimental_metrics_and_compliance():
    response = client.post(
        "/api/v1/backtests",
        json={
            "symbol": "005930",
            "strategy": "ma_cross",
            "limit": 90,
            "fast_period": 5,
            "slow_period": 20,
        },
    )
    body = response.json()
    assert response.status_code == 200
    assert body["data"]["validation_status"] == "experimental"
    assert "max_drawdown" in body["data"]["metrics"]
    assert body["data"]["persistence_status"] == "disabled"
    assert body["data"]["corporate_action_adjustment"]["mode"] == "none"
    assert body["data"]["corporate_action_adjustment"]["enabled"] is False
    assert body["data"]["corporate_action_adjustment"]["input_price_basis_policy"] == {
        "provider": "mock",
        "expected_basis": "unadjusted",
        "verification_status": "synthetic",
        "rule_version": "mock-candles-v1",
    }
    assert body["is_investment_advice"] is False


def test_backtest_corporate_action_opt_in_fails_closed_without_persistence():
    response = client.post(
        "/api/v1/backtests",
        json={
            "symbol": "005930",
            "strategy": "buy_and_hold",
            "limit": 30,
            "corporate_action_mode": "forward_point_in_time",
        },
    )

    assert response.status_code == 503
    assert "persistence is required" in response.json()["error"]["message"]


def test_event_driven_backtest_api_exposes_auditable_events():
    response = client.post(
        "/api/v1/backtests",
        json={
            "symbol": "005930",
            "strategy": "buy_and_hold",
            "engine": "event_driven",
            "limit": 30,
            "commission_rate": 0,
            "tax_rate": 0,
            "slippage_rate": 0,
        },
    )
    body = response.json()["data"]
    assert response.status_code == 200
    assert body["engine"] == "event_driven"
    assert body["engine_version"].startswith("event-backtest-")
    assert {event["event_type"] for event in body["events"]} >= {
        "market",
        "signal",
        "order",
        "fill",
    }
    assert body["trades"][0]["quantity"] > 0


def test_pattern_reference_backtest_is_available_from_api():
    response = client.post(
        "/api/v1/backtests",
        json={
            "symbol": "005930",
            "strategy": "pattern_reference",
            "engine": "event_driven",
            "limit": 80,
        },
    )
    body = response.json()["data"]

    assert response.status_code == 200
    assert body["strategy"] == "pattern_reference"
    assert body["engine"] == "event_driven"
    assert body["validation_status"] == "experimental"


def test_walk_forward_backtest_api_returns_fold_metrics():
    response = client.post(
        "/api/v1/backtests/walk-forward",
        json={
            "symbol": "005930",
            "strategy": "pattern_reference",
            "engine": "event_driven",
            "limit": 180,
            "n_splits": 3,
            "warmup_candles": 60,
        },
    )
    body = response.json()["data"]

    assert response.status_code == 200
    assert body["validation_version"] == "walk-forward-backtest-2026.2"
    assert body["validation_status"] == "experimental"
    assert len(body["folds"]) == 3
    assert 0 <= body["aggregate"]["profitable_fold_ratio"] <= 1
    assert body["execution_model"]["volume_limit_applied"] is True
    assert "total_partial_fill_count" in body["aggregate"]


def test_backtest_api_bounds_volume_participation():
    response = client.post(
        "/api/v1/backtests",
        json={
            "symbol": "005930",
            "engine": "event_driven",
            "max_volume_participation": 1.01,
        },
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_admin_backtest_engine_comparison_uses_one_set_of_assumptions():
    response = client.post(
        "/api/v1/admin/backtests/compare",
        headers={"X-Admin-Key": "test-admin-secret"},
        json={
            "symbol": "005930",
            "strategy": "buy_and_hold",
            "limit": 240,
            "commission_rate": 0,
            "tax_rate": 0,
            "slippage_rate": 0,
            "max_volume_participation": 0.1,
        },
    )
    body = response.json()["data"]

    assert response.status_code == 200
    assert body["comparison_version"] == "engine-comparison-2026.1"
    assert body["validation_status"] == "experimental"
    assert body["assumptions"]["same_market_data_snapshot"] is True
    assert body["assumptions"]["candle_count"] == 240
    assert body["vectorized"]["engine_version"] == "backtest-2026.1"
    assert body["event_driven"]["engine_version"] == "event-backtest-2026.2"
    assert body["event_driven"]["execution"]["volume_limit_applied"] is True
    assert len(body["vectorized"]["equity_curve"]) == 120
    assert len(body["event_driven"]["equity_curve"]) == 120
    assert body["vectorized"]["equity_curve"][0]["normalized_equity"] == 100
    assert (
        body["vectorized"]["equity_curve"][0]["timestamp"]
        == body["event_driven"]["equity_curve"][0]["timestamp"]
    )
    assert (
        body["vectorized"]["equity_curve"][-1]["timestamp"]
        == body["event_driven"]["equity_curve"][-1]["timestamp"]
    )
    assert set(body["deltas"]) == {
        "total_return",
        "cagr",
        "max_drawdown",
        "sharpe_ratio",
        "final_equity",
        "trade_count",
    }
    expected = (
        body["event_driven"]["metrics"]["final_equity"]
        - body["vectorized"]["metrics"]["final_equity"]
    )
    assert body["deltas"]["final_equity"] == round(expected, 8)
    assert response.json()["is_investment_advice"] is False


def test_admin_backtest_engine_comparison_is_protected():
    response = client.post(
        "/api/v1/admin/backtests/compare",
        json={"symbol": "005930"},
    )

    assert response.status_code == 401


def test_admin_strategy_comparison_uses_buy_and_hold_as_neutral_benchmark():
    response = client.post(
        "/api/v1/admin/backtests/strategies/compare",
        headers={"X-Admin-Key": "test-admin-secret"},
        json={
            "symbol": "005930",
            "engine": "event_driven",
            "limit": 80,
            "commission_rate": 0,
            "tax_rate": 0,
            "slippage_rate": 0,
            "max_volume_participation": 0.1,
        },
    )
    body = response.json()["data"]

    assert response.status_code == 200
    assert body["comparison_version"] == "strategy-comparison-2026.1"
    assert body["validation_status"] == "experimental"
    assert body["benchmark"] == "buy_and_hold"
    assert body["engine"] == "event_driven"
    assert body["engine_version"] == "event-backtest-2026.2"
    assert body["assumptions"]["same_market_data_snapshot"] is True
    assert [item["strategy"] for item in body["strategies"]] == [
        "buy_and_hold",
        "ma_cross",
        "pattern_reference",
    ]
    benchmark = body["strategies"][0]
    assert all(value == 0 for value in benchmark["deltas_vs_buy_and_hold"].values())
    assert all("execution" in item for item in body["strategies"])
    assert all(len(item["equity_curve"]) == 80 for item in body["strategies"])
    assert len({item["equity_curve"][0]["timestamp"] for item in body["strategies"]}) == 1
    assert len({item["equity_curve"][-1]["timestamp"] for item in body["strategies"]}) == 1
    assert response.json()["is_investment_advice"] is False


def test_admin_strategy_comparison_is_protected():
    response = client.post(
        "/api/v1/admin/backtests/strategies/compare",
        json={"symbol": "005930"},
    )

    assert response.status_code == 401


def test_validation_error_and_post_cors_use_standard_envelope():
    invalid = client.post("/api/v1/backtests", json={"symbol": "!"})
    assert invalid.status_code == 422
    assert invalid.json()["error"]["code"] == "VALIDATION_ERROR"
    preflight = client.options(
        "/api/v1/backtests",
        headers={"Origin": "http://localhost:3000", "Access-Control-Request-Method": "POST"},
    )
    assert preflight.status_code == 200
    assert "POST" in preflight.headers["access-control-allow-methods"]


def test_score_api_exposes_all_six_connected_axes():
    response = client.get("/api/v1/stocks/005930/score?limit=60")
    body = response.json()
    assert response.status_code == 200
    assert body["data"]["validation_status"] == "experimental"
    assert body["data"]["coverage_ratio"] == 1.0
    assert body["data"]["is_partial"] is False
    assert sum(axis["available"] for axis in body["data"]["axes"]) == 6
    assert body["is_investment_advice"] is False


def test_prediction_api_returns_an_experimental_probability():
    response = client.get("/api/v1/stocks/005930/prediction?horizon_days=5&limit=180")
    body = response.json()

    assert response.status_code == 200
    assert body["data"]["validation_status"] == "experimental"
    assert 0 <= float(body["data"]["rise_probability"]) <= 1
    assert body["is_investment_advice"] is False


def test_ai_report_api_is_compliance_checked_and_experimental():
    response = client.get("/api/v1/stocks/005930/ai-report?horizon_days=5&limit=180")
    body = response.json()

    assert response.status_code == 200
    assert body["data"]["generator"] == "mock"
    assert body["data"]["validation_status"] == "experimental"
    assert body["data"]["compliance_status"] == "passed"
    assert body["data"]["is_investment_advice"] is False
    assert body["data"]["reference_signal"] in {
        "positive_watch",
        "neutral_watch",
        "defensive_watch",
        "risk_aware",
        "data_insufficient",
    }
    assert body["data"]["signal_basis"]


def test_account_sync_api_masks_account_number_and_is_read_only():
    headers = {"X-Admin-Key": "test-admin-secret"}
    accounts = client.get("/api/v1/broker-accounts", headers=headers)
    synced = client.post("/api/v1/portfolios/1/sync", headers=headers)

    assert accounts.status_code == 200
    assert accounts.json()["data"]["accounts"][0]["account_no_masked"].endswith("8901")
    assert synced.status_code == 200
    assert synced.json()["data"]["is_read_only"] is True


def test_account_sync_api_requires_admin_access():
    assert client.get("/api/v1/broker-accounts").status_code == 401
    assert client.post("/api/v1/portfolios/1/sync").status_code == 401


def test_realtime_status_exposes_source_without_credentials():
    response = client.get("/api/v1/realtime/status")

    assert response.status_code == 200
    assert response.json()["data"] == {
        "enabled": False,
        "source": "mock",
        "transport": "polling",
    }
