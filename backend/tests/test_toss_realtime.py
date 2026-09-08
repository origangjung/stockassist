from decimal import Decimal

from app.realtime.toss import parse_toss_trade_message, toss_trade_declaration


def test_toss_declaration_groups_domestic_and_overseas_symbols():
    declaration = toss_trade_declaration({"AAPL", "005930", "TSLA"}, "request-1")

    assert declaration == [
        {"id": "request-1"},
        {"type": "trade:kr", "codes": ["005930"]},
        {"type": "trade:us", "codes": ["AAPL", "TSLA"]},
    ]
    assert toss_trade_declaration(set()) == []


def test_toss_trade_message_is_normalized_without_exposing_auth_data():
    quote = parse_toss_trade_message(
        '{"type":"message","topic":"trade:us:AAPL","data":'
        '{"price":"243.26","volume":"8","timestamp":'
        '"2026-06-18T23:30:00.000+09:00","currency":"USD"}}',
        {"AAPL": "Apple"},
    )

    assert quote is not None
    assert quote.symbol == "AAPL"
    assert quote.name == "Apple"
    assert quote.price == Decimal("243.26")
    assert quote.volume == 8
    assert quote.currency == "USD"


def test_toss_system_frames_are_ignored_by_quote_parser():
    assert parse_toss_trade_message('{"type":"pong"}', {}) is None
    assert (
        parse_toss_trade_message(
            '{"type":"subscriptions","subscribed":["trade:kr:005930"],"rejected":[]}',
            {},
        )
        is None
    )
