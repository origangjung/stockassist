"""news_api 파일은 직접 학습 AI 특성과 실행 기능을 담당한다."""

from __future__ import annotations

from datetime import date, timedelta
from time import monotonic
import re

import httpx2

from app.local_ai.news_features import latest_news_features
from app.local_ai.http_security import (
    DailyRequestBudget,
    bounded_json,
    validate_https_endpoint,
    validate_symbol,
)


MAX_NEWS_RESPONSE_BYTES = 4 * 1024 * 1024


NEWS_ENTITY_TERMS: dict[str, tuple[str, ...]] = {
    "AAPL": ("Apple",), "MSFT": ("Microsoft",), "NVDA": ("Nvidia",),
    "AVGO": ("Broadcom",), "ORCL": ("Oracle",), "CRM": ("Salesforce",),
    "ADBE": ("Adobe",), "AMD": ("Advanced Micro Devices", "AMD"),
    "QCOM": ("Qualcomm",), "TXN": ("Texas Instruments",), "INTU": ("Intuit",),
    "AMAT": ("Applied Materials",), "MU": ("Micron",),
    "GOOGL": ("Alphabet", "Google"), "META": ("Meta Platforms", "Facebook"),
    "NFLX": ("Netflix",), "DIS": ("Walt Disney", "Disney"),
    "TMUS": ("T-Mobile", "T Mobile"), "VZ": ("Verizon",), "T": ("AT&T",),
    "AMZN": ("Amazon",), "TSLA": ("Tesla",), "HD": ("Home Depot",),
    "MCD": ("McDonald's", "McDonald"), "NKE": ("Nike",),
    "SBUX": ("Starbucks",), "LOW": ("Lowe's", "Lowes"), "TJX": ("TJX",),
    "BKNG": ("Booking Holdings", "Booking.com"), "GM": ("General Motors",),
    "WMT": ("Walmart",), "COST": ("Costco",),
    "PG": ("Procter & Gamble", "Procter and Gamble"),
    "KO": ("Coca-Cola", "Coca Cola"), "PEP": ("PepsiCo", "Pepsi"),
    "PM": ("Philip Morris",), "CL": ("Colgate-Palmolive", "Colgate"),
    "MDLZ": ("Mondelez",), "KHC": ("Kraft Heinz",),
    "JPM": ("JPMorgan", "JP Morgan"), "BAC": ("Bank of America",),
    "WFC": ("Wells Fargo",), "GS": ("Goldman Sachs",),
    "MS": ("Morgan Stanley",), "BLK": ("BlackRock",),
    "C": ("Citigroup", "Citibank"), "AXP": ("American Express",),
    "SCHW": ("Charles Schwab",), "PNC": ("PNC Financial", "PNC Bank"),
    "JNJ": ("Johnson & Johnson", "Johnson and Johnson"),
    "UNH": ("UnitedHealth", "United Healthcare"), "LLY": ("Eli Lilly",),
    "MRK": ("Merck",), "ABBV": ("AbbVie",), "TMO": ("Thermo Fisher",),
    "ABT": ("Abbott",), "PFE": ("Pfizer",), "DHR": ("Danaher",),
    "BMY": ("Bristol Myers Squibb", "Bristol-Myers"), "MDT": ("Medtronic",),
    "CAT": ("Caterpillar",), "GE": ("General Electric", "GE Aerospace"),
    "HON": ("Honeywell",), "UPS": ("United Parcel Service",),
    "BA": ("Boeing",), "DE": ("John Deere", "Deere"),
    "LMT": ("Lockheed Martin",), "RTX": ("Raytheon", "RTX"),
    "UNP": ("Union Pacific",), "XOM": ("Exxon Mobil", "Exxon"),
    "CVX": ("Chevron",), "COP": ("ConocoPhillips",),
    "SLB": ("Schlumberger", "SLB"), "EOG": ("EOG Resources",),
    "OXY": ("Occidental Petroleum",), "MPC": ("Marathon Petroleum",),
    "NEE": ("NextEra Energy",), "DUK": ("Duke Energy",),
    "SO": ("Southern Company",), "AMT": ("American Tower",),
    "PLD": ("Prologis",), "EQIX": ("Equinix",), "LIN": ("Linde",),
    "APD": ("Air Products",), "SHW": ("Sherwin-Williams", "Sherwin Williams"),
}

NEWS_QUERIES = {
    symbol: f'"{terms[0]}" AND (stock OR shares OR earnings)'
    for symbol, terms in NEWS_ENTITY_TERMS.items()
}


def article_matches_symbol(symbol: str, article: dict) -> bool:
    """기사 제목·설명에 해당 회사의 명시적 이름이 있을 때만 관련 기사로 인정한다."""

    normalized_symbol = validate_symbol(symbol)
    terms = NEWS_ENTITY_TERMS.get(normalized_symbol, (normalized_symbol,))
    text = _normalized_news_text(
        f"{article.get('title') or ''} {article.get('description') or ''}"
    )
    padded = f" {text} "
    return any(f" {_normalized_news_text(term)} " in padded for term in terms)


def _normalized_news_text(value: str) -> str:
    """대소문자와 구두점 차이를 제거하되 단어 경계는 유지한다."""

    return " ".join(re.sub(r"[^a-z0-9]+", " ", value.casefold()).split())


class NewsApiClient:
    """외부 서비스의 인증·요청·응답 검증을 캡슐화하는 client입니다."""

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str = "https://newsapi.org/v2",
        timeout_seconds: float = 30.0,
        cache_seconds: float = 900.0,
        daily_request_limit: int = 90,
    ) -> None:
        """`__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다."""

        self._base_url = validate_https_endpoint(base_url, name="NEWS_API_BASE_URL")
        self._http = httpx2.Client(
            timeout=timeout_seconds, headers={"X-Api-Key": api_key}
        )
        self._cache_seconds = cache_seconds
        self._features: dict[str, tuple[dict[str, float], float]] = {}
        self._budget = DailyRequestBudget(daily_request_limit)

    def articles(self, symbol: str, *, start: date, end: date) -> list[dict]:
        """`articles`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        symbol = validate_symbol(symbol)
        query = NEWS_QUERIES.get(symbol, f'"{symbol}" stock')
        self._budget.consume(provider="NewsAPI")
        response = self._http.get(
            f"{self._base_url}/everything",
            params={
                "q": query,
                "from": start.isoformat(),
                "to": end.isoformat(),
                "language": "en",
                "sortBy": "publishedAt",
                "pageSize": 100,
                "page": 1,
            },
        )
        payload = bounded_json(
            response, provider="NewsAPI", maximum_bytes=MAX_NEWS_RESPONSE_BYTES
        )
        articles = payload.get("articles") if isinstance(payload, dict) else None
        if not isinstance(articles, list):
            raise ValueError("NewsAPI response does not contain articles")
        return [article for article in articles if article_matches_symbol(symbol, article)]

    def latest_features(self, symbol: str) -> dict[str, float]:
        """`latest_features`은(는) 필요한 데이터를 조회해 반환합니다."""

        key = validate_symbol(symbol)
        cached = self._features.get(key)
        if cached and cached[1] > monotonic():
            return cached[0]
        end = date.today()
        features = latest_news_features(
            self.articles(key, start=end - timedelta(days=7), end=end)
        )
        self._features[key] = (features, monotonic() + self._cache_seconds)
        return features

    def close(self) -> None:
        """`close`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        self._http.close()
