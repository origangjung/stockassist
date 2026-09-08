"""SEC 재무와 뉴스 증분 수집에 사용하는 업종 균형 기본 종목군이다."""


COLLECTION_SYMBOLS_BY_SECTOR: dict[str, tuple[str, ...]] = {
    "technology": (
        "AAPL", "MSFT", "NVDA", "AVGO", "ORCL", "CRM", "ADBE", "AMD",
        "QCOM", "TXN", "INTU", "AMAT", "MU",
    ),
    "communication_services": ("GOOGL", "META", "NFLX", "DIS", "TMUS", "VZ", "T"),
    "consumer_discretionary": (
        "AMZN", "TSLA", "HD", "MCD", "NKE", "SBUX", "LOW", "TJX", "BKNG", "GM",
    ),
    "consumer_staples": ("WMT", "COST", "PG", "KO", "PEP", "PM", "CL", "MDLZ", "KHC"),
    "financials": ("JPM", "BAC", "WFC", "GS", "MS", "BLK", "C", "AXP", "SCHW", "PNC"),
    "health_care": (
        "JNJ", "UNH", "LLY", "MRK", "ABBV", "TMO", "ABT", "PFE", "DHR", "BMY", "MDT",
    ),
    "industrials": ("CAT", "GE", "HON", "UPS", "BA", "DE", "LMT", "RTX", "UNP"),
    "energy": ("XOM", "CVX", "COP", "SLB", "EOG", "OXY", "MPC"),
    "utilities": ("NEE", "DUK", "SO"),
    "real_estate": ("AMT", "PLD", "EQIX"),
    "materials": ("LIN", "APD", "SHW"),
}

DEFAULT_COLLECTION_SYMBOLS: tuple[str, ...] = tuple(
    symbol
    for symbols in COLLECTION_SYMBOLS_BY_SECTOR.values()
    for symbol in symbols
)


# KIS 종목별 투자자 수급을 누적할 국내 대형주 기본 표본이다.
DEFAULT_KIS_FLOW_SYMBOLS: tuple[str, ...] = (
    "005930", "000660", "035420", "035720", "005380", "068270",
    "051910", "207940", "005490", "105560", "006400", "373220",
    "012330", "000270", "055550", "086790", "028260", "066570",
    "033780", "096770", "015760", "329180", "017670", "032830",
    "034020", "012450", "011200", "009150", "090430", "003550",
)
