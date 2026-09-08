"""flow_market_features 파일은 직접 학습 AI 특성과 실행 기능을 담당한다."""

FLOW_MARKET_FEATURES = (
    "price_return_1d",
    "price_return_5d",
    "price_sma_20_gap",
    "price_volatility_20",
    "price_volume_ratio",
)


def flow_market_features(market: dict[str, float]) -> dict[str, float]:
    """`flow_market_features`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    return {
        "price_return_1d": market["return_1d"],
        "price_return_5d": market["return_5d"],
        "price_sma_20_gap": market["sma_20_gap"],
        "price_volatility_20": market["volatility_20"],
        "price_volume_ratio": market["volume_ratio"],
    }
