"""etf 파일은 직접 학습 AI 특성과 실행 기능을 담당한다."""

from __future__ import annotations


ETF_SYMBOLS = frozenset(
    {
        "AGG", "ARKK", "DIA", "EEM", "EFA", "GLD", "HYG", "IEF", "IWM",
        "JEPI", "LQD", "QQQ", "SCHD", "SHY", "SLV", "SMH", "SOXX", "SPY",
        "TLT", "USO", "VIG", "VNQ", "VOO", "VTI", "VTV", "VUG", "XLC",
        "XLE", "XLF", "XLI", "XLK", "XLP", "XLRE", "XLU", "XLV", "XLY",
    }
)

ETF_ASSET_CLASSES = (
    "broad_equity",
    "commodity",
    "fixed_income",
    "international",
    "real_estate",
    "sector",
    "thematic",
)
ETF_ASSET_CLASS_FEATURES = tuple(
    f"asset_class_{asset_class}" for asset_class in ETF_ASSET_CLASSES
)
ETF_ASSET_CLASS_SYMBOLS = {
    "commodity": frozenset({"GLD", "SLV", "USO"}),
    "fixed_income": frozenset({"AGG", "HYG", "IEF", "LQD", "SHY", "TLT"}),
    "international": frozenset({"EEM", "EFA"}),
    "real_estate": frozenset({"VNQ", "XLRE"}),
    "sector": frozenset(
        {"SMH", "SOXX", "XLC", "XLE", "XLF", "XLI", "XLK", "XLP", "XLU", "XLV", "XLY"}
    ),
    "thematic": frozenset({"ARKK"}),
}


def is_etf(symbol: str, stock: dict | None = None) -> bool:
    """`is_etf`은(는) 입력 또는 현재 상태가 규칙을 만족하는지 검증합니다."""

    if symbol.strip().upper() in ETF_SYMBOLS:
        return True
    if not isinstance(stock, dict):
        return False
    text = " ".join(str(stock.get(name) or "") for name in ("name", "sector"))
    normalized = text.casefold()
    return " etf" in f" {normalized}" or "exchange traded fund" in normalized


def etf_asset_class(symbol: str) -> str:
    """`etf_asset_class`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    normalized = symbol.strip().upper()
    return next(
        (
            asset_class
            for asset_class, symbols in ETF_ASSET_CLASS_SYMBOLS.items()
            if normalized in symbols
        ),
        "broad_equity",
    )


def etf_asset_class_features(symbol: str) -> dict[str, float]:
    """`etf_asset_class_features`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    selected = etf_asset_class(symbol)
    return {
        f"asset_class_{asset_class}": float(asset_class == selected)
        for asset_class in ETF_ASSET_CLASSES
    }
