"""자금배분 엔진이 위험 한도를 지키고 실제 주문을 만들지 않는지 검증한다."""

from decimal import Decimal
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


def test_allocation_proposal_uses_optimizer_without_executing_orders():
    """두 미국 종목의 목표 비중과 모의 리밸런싱 제안만 반환해야 한다."""
    client = TestClient(app)
    account_id = str(uuid4())

    response = client.post(
        f"/api/v1/paper-portfolios/{account_id}/allocation-proposals",
        json={
            "symbols": ["AAPL", "MSFT", "NVDA"],
            "objective": "min_volatility",
            "invest_ratio": "0.90",
            "max_asset_weight": "0.40",
            "lookback_days": 120,
        },
    )

    assert response.status_code == 200
    result = response.json()["data"]
    weights = {symbol: Decimal(value) for symbol, value in result["target_weights"].items()}
    assert result["optimizer"] == "PyPortfolioOpt-1.6"
    assert sum(weights.values()) == Decimal("0.9")
    assert max(weights.values()) <= Decimal("0.40")
    assert result["target_cash_weight"] == "0.10"
    assert result["execution_enabled"] is False
    assert result["is_real_order"] is False
    assert all(action["side"] == "buy" for action in result["rebalance_actions"])
    assert all(Decimal(action["notional"]) <= Decimal("3000") for action in result["rebalance_actions"])
    assert client.get(f"/api/v1/paper-portfolios/{account_id}").json()["data"]["orders"] == []


def test_allocation_proposal_rejects_mixed_currencies():
    """환전 가정을 숨기지 않도록 원화와 달러 종목 혼합 요청을 거절해야 한다."""
    response = TestClient(app).post(
        f"/api/v1/paper-portfolios/{uuid4()}/allocation-proposals",
        json={"symbols": ["AAPL", "MSFT", "005930"]},
    )

    assert response.status_code == 422
    assert "같은 통화" in response.json()["error"]["message"]


def test_allocation_proposal_rejects_impossible_weight_bounds():
    """종목 수로 합계 100%를 만들 수 없는 최대 비중 조합을 일찍 거절해야 한다."""
    response = TestClient(app).post(
        f"/api/v1/paper-portfolios/{uuid4()}/allocation-proposals",
        json={
            "symbols": ["AAPL", "MSFT", "NVDA"],
            "max_asset_weight": "0.30",
        },
    )

    assert response.status_code == 422
    assert "포트폴리오" in response.json()["error"]["message"]
