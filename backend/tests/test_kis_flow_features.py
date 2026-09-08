from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from app.investor_flow.kis import DailyKisInvestorFlow
from app.local_ai.kis_flow_features import KIS_FLOW_FEATURES, build_kis_flow_training_rows
from app.providers.contracts import Candle


def _candle(day: date, close: float, volume: int = 1_000) -> Candle:
    price = Decimal(str(close))
    return Candle(datetime.combine(day, datetime.min.time(), timezone.utc), price, price, price, price, volume)


def test_kis_flow_features_use_only_current_and_past_rows():
    start = date(2026, 1, 1)
    days = [start + timedelta(days=index) for index in range(30)]
    flows = [
        DailyKisInvestorFlow(
            symbol="005930",
            trade_date=day,
            foreign_net_quantity=Decimal(index * 10),
            institution_net_quantity=Decimal(index * -5),
            individual_net_quantity=Decimal(index * -5),
        )
        for index, day in enumerate(days)
    ]
    candles = [_candle(day, 100 + index) for index, day in enumerate(days)]
    benchmark = [_candle(day, 100 + index / 2) for index, day in enumerate(days)]

    rows = build_kis_flow_training_rows(
        flows,
        candles,
        benchmark_candles=benchmark,
        minimum_absolute_excess_return=0,
    )

    assert rows
    assert set(KIS_FLOW_FEATURES).issubset(rows[0])
    assert rows[0]["timestamp"] == days[20].isoformat()
    assert rows[0]["foreign_net_volume_ratio"] == 0.20
    assert rows[0]["price_return_5d"] > 0
    assert rows[0]["market_return_5d"] > 0
    assert rows[0]["label"] == 0
