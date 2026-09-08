"""호가 잔량과 최근 체결량으로 단기 매수·매도 압력을 계산한다."""

from decimal import Decimal
from typing import Iterable

from app.providers.contracts import OrderbookLevel, Trade


BUY_SIDES = frozenset({"buy", "bid", "b", "purchase", "매수"})
SELL_SIDES = frozenset({"sell", "ask", "s", "sale", "매도"})


def calculate_market_pressure(
    asks: Iterable[OrderbookLevel],
    bids: Iterable[OrderbookLevel],
    trades: Iterable[Trade],
) -> dict[str, object]:
    """호가 불균형과 방향이 확인된 체결량을 결합해 -1~1 압력을 반환한다.

    양수는 매수 우위, 음수는 매도 우위다. 체결 방향이 없으면 현재 최우선
    호가에 닿은 가격으로만 보조 추정하며, 어느 쪽도 확인할 수 없으면 호가
    잔량만 사용하고 출처를 명시한다.
    """

    ask_rows, bid_rows, trade_rows = list(asks), list(bids), list(trades)
    ask_quantity = sum((Decimal(str(row.quantity)) for row in ask_rows), Decimal(0))
    bid_quantity = sum((Decimal(str(row.quantity)) for row in bid_rows), Decimal(0))
    book_total = ask_quantity + bid_quantity
    book_score = (
        float((bid_quantity - ask_quantity) / book_total) if book_total > 0 else None
    )

    best_ask = min((Decimal(str(row.price)) for row in ask_rows), default=None)
    best_bid = max((Decimal(str(row.price)) for row in bid_rows), default=None)
    buy_quantity = Decimal(0)
    sell_quantity = Decimal(0)
    known_quantity = Decimal(0)
    total_trade_quantity = Decimal(0)
    explicit_quantity = Decimal(0)
    for trade in trade_rows:
        quantity = max(Decimal(0), Decimal(str(trade.quantity)))
        total_trade_quantity += quantity
        side = str(trade.side or "").strip().casefold()
        if side in BUY_SIDES:
            buy_quantity += quantity
            known_quantity += quantity
            explicit_quantity += quantity
        elif side in SELL_SIDES:
            sell_quantity += quantity
            known_quantity += quantity
            explicit_quantity += quantity
        else:
            price = Decimal(str(trade.price))
            if best_ask is not None and price >= best_ask:
                buy_quantity += quantity
                known_quantity += quantity
            elif best_bid is not None and price <= best_bid:
                sell_quantity += quantity
                known_quantity += quantity

    trade_score = (
        float((buy_quantity - sell_quantity) / known_quantity)
        if known_quantity > 0
        else None
    )
    if trade_score is not None and book_score is not None:
        score = trade_score * 0.65 + book_score * 0.35
        source = "trades_and_orderbook"
    elif trade_score is not None:
        score = trade_score
        source = "trades_only"
    elif book_score is not None:
        score = book_score
        source = "orderbook_only"
    else:
        score = 0.0
        source = "unavailable"

    signal = (
        "buying"
        if score >= 0.10
        else "selling"
        if score <= -0.10
        else "balanced"
        if source != "unavailable"
        else "unavailable"
    )
    known_ratio = (
        float(known_quantity / total_trade_quantity)
        if total_trade_quantity > 0
        else 0.0
    )
    explicit_ratio = (
        float(explicit_quantity / total_trade_quantity)
        if total_trade_quantity > 0
        else 0.0
    )
    return {
        "signal": signal,
        "score": round(score, 4),
        "strength": round(abs(score), 4),
        "source": source,
        "book_imbalance": round(book_score, 4) if book_score is not None else None,
        "trade_imbalance": round(trade_score, 4) if trade_score is not None else None,
        "bid_quantity": str(bid_quantity),
        "ask_quantity": str(ask_quantity),
        "buy_trade_quantity": str(buy_quantity),
        "sell_trade_quantity": str(sell_quantity),
        "known_trade_ratio": round(known_ratio, 4),
        "explicit_side_ratio": round(explicit_ratio, 4),
        "is_estimate": explicit_ratio < 0.9999,
    }
