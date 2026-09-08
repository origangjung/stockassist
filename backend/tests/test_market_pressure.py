from datetime import datetime, timezone
from decimal import Decimal

from app.microstructure import calculate_market_pressure
from app.providers.contracts import OrderbookLevel, Trade


def _trade(side: str | None, price: str, quantity: str) -> Trade:
    return Trade(
        "AAPL",
        Decimal(price),
        Decimal(quantity),
        side,
        datetime(2026, 8, 22, tzinfo=timezone.utc),
    )


def test_market_pressure_combines_book_and_explicit_trade_sides():
    asks = [OrderbookLevel(Decimal("101"), Decimal("100"))]
    bids = [OrderbookLevel(Decimal("100"), Decimal("300"))]
    trades = [_trade("buy", "101", "80"), _trade("sell", "100", "20")]

    result = calculate_market_pressure(asks, bids, trades)

    assert result["signal"] == "buying"
    assert result["score"] == 0.565
    assert result["source"] == "trades_and_orderbook"
    assert result["explicit_side_ratio"] == 1.0
    assert result["is_estimate"] is False


def test_market_pressure_marks_price_inferred_trade_direction_as_estimate():
    asks = [OrderbookLevel(Decimal("101"), Decimal("100"))]
    bids = [OrderbookLevel(Decimal("100"), Decimal("100"))]

    result = calculate_market_pressure(
        asks,
        bids,
        [_trade(None, "101", "50"), _trade(None, "100", "10")],
    )

    assert result["signal"] == "buying"
    assert result["trade_imbalance"] == 0.6667
    assert result["known_trade_ratio"] == 1.0
    assert result["explicit_side_ratio"] == 0.0
    assert result["is_estimate"] is True


def test_market_pressure_can_fall_back_to_orderbook_only():
    result = calculate_market_pressure(
        [OrderbookLevel(Decimal("101"), Decimal("300"))],
        [OrderbookLevel(Decimal("100"), Decimal("100"))],
        [],
    )

    assert result["signal"] == "selling"
    assert result["score"] == -0.5
    assert result["source"] == "orderbook_only"
