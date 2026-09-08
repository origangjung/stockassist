from app.local_ai.sector_features import sector_etf, sector_features


def test_sector_mapping_and_relative_features():
    assert sector_etf("aapl") == "XLK"
    assert sector_etf("UNKNOWN") == "SPY"
    result = sector_features(
        {"return_5d": 0.08, "sma_20_gap": 0.04},
        {"return_5d": 0.03, "sma_20_gap": 0.01, "volatility_20": 0.02},
    )
    assert result["relative_return_5d_sector"] == 0.05
    assert result["relative_trend_sector"] == 0.03
