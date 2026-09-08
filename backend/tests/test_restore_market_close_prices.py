from datetime import date

from scripts.ai.data.restore_market_close_prices import restore_symbol_rows


def test_restore_close_prices_uses_return_chain_and_checks_overlaps():
    rows = [
        {"timestamp": "2025-01-01", "symbol": "AAPL", "return_1d": "0.1"},
        {"timestamp": "2025-01-02", "symbol": "AAPL", "return_1d": "0.1"},
        {"timestamp": "2025-01-03", "symbol": "AAPL", "return_1d": "-0.05"},
    ]
    anchors = {
        date(2025, 1, 2): 110.0,
        date(2025, 1, 3): 104.5,
    }

    restored = restore_symbol_rows(rows, anchors)

    assert [round(float(row["close_price"]), 2) for row in restored] == [100, 110, 104.5]


def test_restore_close_prices_fails_closed_when_price_basis_differs():
    rows = [
        {"timestamp": "2025-01-01", "symbol": "AAPL", "return_1d": "0.1"},
        {"timestamp": "2025-01-02", "symbol": "AAPL", "return_1d": "0.1"},
    ]
    anchors = {date(2025, 1, 1): 100.0, date(2025, 1, 2): 120.0}

    assert restore_symbol_rows(rows, anchors) == []
