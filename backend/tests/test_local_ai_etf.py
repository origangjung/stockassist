from app.local_ai.etf import etf_asset_class, etf_asset_class_features, is_etf


def test_etf_detection_uses_known_symbols_and_provider_name():
    assert is_etf("spy") is True
    assert is_etf("CUSTOM", {"name": "Example Exchange Traded Fund"}) is True
    assert is_etf("AAPL", {"name": "Apple Inc."}) is False


def test_etf_asset_class_features_are_stable_one_hot_values():
    assert etf_asset_class("TLT") == "fixed_income"
    assert etf_asset_class("GLD") == "commodity"
    assert etf_asset_class("SPY") == "broad_equity"
    values = etf_asset_class_features("XLK")

    assert values["asset_class_sector"] == 1.0
    assert sum(values.values()) == 1.0
