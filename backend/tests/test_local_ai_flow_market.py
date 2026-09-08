from app.local_ai.flow_market_features import flow_market_features


def test_flow_market_features_prefixes_market_values():
    result = flow_market_features(
        {
            "return_1d": 0.01,
            "return_5d": 0.03,
            "sma_20_gap": 0.02,
            "volatility_20": 0.04,
            "volume_ratio": 1.2,
        }
    )
    assert result["price_return_5d"] == 0.03
    assert result["price_volatility_20"] == 0.04
