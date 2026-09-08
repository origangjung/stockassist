"""sector_features 파일은 직접 학습 AI 특성과 실행 기능을 담당한다."""

from __future__ import annotations

from app.providers.contracts import Candle


SECTOR_FEATURES = (
    "sector_return_5d",
    "sector_sma_20_gap",
    "sector_volatility_20",
    "relative_return_5d_sector",
    "relative_trend_sector",
)

SECTOR_ETFS: dict[str, str] = {
    "AAPL": "XLK", "MSFT": "XLK", "NVDA": "XLK", "AMD": "XLK",
    "AVGO": "XLK", "ADBE": "XLK", "CRM": "XLK", "CSCO": "XLK",
    "IBM": "XLK", "INTC": "XLK", "ORCL": "XLK", "QCOM": "XLK",
    "GOOGL": "XLC", "META": "XLC", "NFLX": "XLC", "DIS": "XLC",
    "T": "XLC", "VZ": "XLC",
    "AMZN": "XLY", "TSLA": "XLY", "HD": "XLY", "MCD": "XLY", "NKE": "XLY",
    "JPM": "XLF", "BAC": "XLF", "GS": "XLF", "V": "XLF", "MA": "XLF",
    "JNJ": "XLV", "PFE": "XLV", "ABBV": "XLV", "LLY": "XLV",
    "MRK": "XLV", "UNH": "XLV",
    "XOM": "XLE", "CVX": "XLE",
    "WMT": "XLP", "COST": "XLP", "KO": "XLP", "PEP": "XLP",
    "GE": "XLI",
}


def sector_etf(symbol: str) -> str:
    """`sector_etf`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    return SECTOR_ETFS.get(symbol.upper(), "SPY")


def latest_sector_features(
    stock_features: dict[str, float] | None,
    sector_candles: list[Candle],
) -> dict[str, float] | None:
    """`latest_sector_features`은(는) 필요한 데이터를 조회해 반환합니다."""

    if stock_features is None:
        return None
    from app.local_ai.market_features import latest_market_features

    sector = latest_market_features(sector_candles)
    if sector is None:
        return None
    return sector_features(stock_features, sector)


def sector_features(
    stock: dict[str, float], sector: dict[str, float]
) -> dict[str, float]:
    """`sector_features`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    return {
        "sector_return_5d": sector["return_5d"],
        "sector_sma_20_gap": sector["sma_20_gap"],
        "sector_volatility_20": sector["volatility_20"],
        "relative_return_5d_sector": stock["return_5d"] - sector["return_5d"],
        "relative_trend_sector": stock["sma_20_gap"] - sector["sma_20_gap"],
    }
