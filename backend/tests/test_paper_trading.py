"""모의투자가 실제 주문 없이 현금·보유 수량·중복 요청을 올바르게 처리하는지 검증한다."""

from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from fastapi.testclient import TestClient
import pytest

from app.main import app
from app.paper_trading.contracts import (
    InsufficientPaperPositionError,
    PaperAccount,
    PaperFill,
    PaperPosition,
    PaperRiskLimitError,
    PaperTradingError,
)
from app.paper_trading.risk import summarize_portfolio_risk, validate_buy_risk
from app.repositories.paper_trading import InMemoryPaperTradingRepository
from app.services.paper_trading import PaperTradingService
from app.services.market import MarketDataService
from app.adapters.broker import BrokerAdapter
from app.providers.mock import MockProvider


def service() -> PaperTradingService:
    """외부 네트워크 없이 결정적인 시세로 검증할 모의투자 서비스를 만든다."""
    market = MarketDataService(BrokerAdapter([MockProvider()]))
    return PaperTradingService(market, InMemoryPaperTradingRepository())


def test_buy_sell_and_idempotency_keep_a_consistent_ledger():
    paper = service()
    account_id = str(uuid4())
    key = str(uuid4())

    bought = paper.execute(
        account_id, symbol="AAPL", side="buy", quantity=Decimal("2"), idempotency_key=key
    )
    duplicated = paper.execute(
        account_id, symbol="AAPL", side="buy", quantity=Decimal("2"), idempotency_key=key
    )
    sold = paper.execute(
        account_id, symbol="AAPL", side="sell", quantity=Decimal("1"),
        idempotency_key=str(uuid4()),
    )

    assert len(bought["orders"]) == 1
    assert len(duplicated["orders"]) == 1
    assert sold["positions"][0]["quantity"] == Decimal("1.000000")
    assert len(sold["orders"]) == 2
    assert sold["is_real_order"] is False
    assert sold["persistence_status"] == "temporary"
    assert sold["saved_at"] == sold["account"]["updated_at"]


def test_sell_rejects_short_position():
    paper = service()
    try:
        paper.execute(
            str(uuid4()), symbol="AAPL", side="sell", quantity=Decimal("1"),
            idempotency_key=str(uuid4()),
        )
    except InsufficientPaperPositionError:
        return
    raise AssertionError("보유하지 않은 종목의 매도가 허용되었습니다.")


def test_idempotency_key_rejects_a_different_order_payload():
    paper = service()
    account_id, key = str(uuid4()), str(uuid4())
    paper.execute(account_id, symbol="AAPL", side="buy", quantity=Decimal("1"), idempotency_key=key)

    with pytest.raises(PaperTradingError, match="중복 방지 키"):
        paper.execute(
            account_id, symbol="AAPL", side="buy", quantity=Decimal("2"), idempotency_key=key
        )


def test_paper_trading_api_initializes_and_executes_order():
    client = TestClient(app)
    account_id = str(uuid4())
    initial = client.get(f"/api/v1/paper-portfolios/{account_id}")
    order = client.post(
        f"/api/v1/paper-portfolios/{account_id}/orders",
        json={
            "symbol": "AAPL",
            "side": "buy",
            "quantity": "10",
            "idempotency_key": str(uuid4()),
        },
    )

    assert initial.status_code == 200
    assert initial.json()["data"]["totals"]["USD"]["return_percent"] == "0.00"
    assert order.status_code == 200
    portfolio = order.json()["data"]
    assert Decimal(portfolio["totals"]["USD"]["total_pnl"]) < 0
    assert Decimal(portfolio["totals"]["USD"]["return_percent"]) < 0
    assert order.json()["data"]["positions"][0]["symbol"] == "AAPL"


def test_paper_trading_api_rejects_invalid_account_identifier():
    response = TestClient(app).get("/api/v1/paper-portfolios/not-an-account")
    assert response.status_code == 422


def test_paper_trading_api_rejects_an_order_over_the_central_risk_limit():
    response = TestClient(app).post(
        f"/api/v1/paper-portfolios/{uuid4()}/orders",
        json={
            "symbol": "AAPL",
            "side": "buy",
            "quantity": "100",
            "idempotency_key": str(uuid4()),
        },
    )

    assert response.status_code == 409
    assert "총자산" in response.json()["error"]["message"]


def test_central_risk_policy_rejects_a_concentrated_buy():
    now = datetime.now(timezone.utc)
    account = PaperAccount(
        "account", Decimal("10000"), Decimal("10000"),
        Decimal("10000"), Decimal("7500"), now, now,
    )
    positions = [
        PaperPosition(
            "AAPL", "Apple", "NASDAQ", "USD", Decimal("25"),
            Decimal("100"), Decimal("100"), Decimal("0"), now,
        )
    ]
    fill = PaperFill(
        "key", "AAPL", "Apple", "NASDAQ", "USD", "buy",
        Decimal("20"), Decimal("100"), Decimal("0.001"), now,
    )

    with pytest.raises(PaperRiskLimitError, match="한 종목"):
        validate_buy_risk(account, positions, fill)


def test_risk_summary_exposes_concentration_and_cash_buffer():
    now = datetime.now(timezone.utc)
    account = PaperAccount(
        "account", Decimal("10000"), Decimal("10000"),
        Decimal("10000"), Decimal("500"), now, now,
    )
    positions = [
        PaperPosition(
            "AAPL", "Apple", "NASDAQ", "USD", Decimal("95"),
            Decimal("100"), Decimal("100"), Decimal("0"), now,
        )
    ]

    summary = summarize_portfolio_risk(account, positions, "USD")

    assert summary["status"] == "high"
    assert summary["largest_position_symbol"] == "AAPL"
    assert summary["warnings"] == ["single_position_concentration", "low_cash_buffer"]
