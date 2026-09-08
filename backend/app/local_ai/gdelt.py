"""GDELT DOC API에서 뉴스 메타데이터를 안전하게 수집한다."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from time import monotonic, sleep
import re
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import httpx2

from app.local_ai.http_security import (
    DailyRequestBudget,
    bounded_json,
    validate_https_endpoint,
    validate_symbol,
)
from app.local_ai.news_api import NEWS_QUERIES, article_matches_symbol
from app.local_ai.news_features import latest_news_features


MAX_GDELT_RESPONSE_BYTES = 8 * 1024 * 1024
TRACKING_QUERY_KEYS = frozenset(
    {"fbclid", "gclid", "mc_cid", "mc_eid", "ref", "ref_src", "source"}
)


class GdeltNewsClient:
    """무료 공개 GDELT API 응답을 기존 뉴스 학습 형식으로 변환한다."""

    def __init__(
        self,
        *,
        base_url: str = "https://api.gdeltproject.org/api/v2/doc/doc",
        timeout_seconds: float = 30.0,
        cache_seconds: float = 900.0,
        daily_request_limit: int = 500,
        minimum_interval_seconds: float = 5.1,
        transport: httpx2.BaseTransport | None = None,
    ) -> None:
        self._base_url = validate_https_endpoint(base_url, name="GDELT_DOC_API_URL")
        self._http = httpx2.Client(timeout=timeout_seconds, transport=transport)
        self._cache_seconds = cache_seconds
        self._features: dict[str, tuple[dict[str, float], float]] = {}
        self._budget = DailyRequestBudget(daily_request_limit)
        self._minimum_interval_seconds = max(0.0, minimum_interval_seconds)
        self._last_request_at = 0.0

    def articles(self, symbol: str, *, start: date, end: date) -> list[dict]:
        """종목 관련 기사 메타데이터를 지정한 날짜 구간에서 조회한다."""

        symbol = validate_symbol(symbol)
        query = NEWS_QUERIES.get(symbol, f'"{symbol}" (stock OR shares OR earnings)')
        self._budget.consume(provider="GDELT")
        params = {
                "query": query,
                "mode": "artlist",
                "format": "json",
                "maxrecords": 250,
                "sort": "datedesc",
                "sourcelang": "english",
                "startdatetime": datetime.combine(start, time.min).strftime("%Y%m%d%H%M%S"),
                "enddatetime": datetime.combine(end, time.max).strftime("%Y%m%d%H%M%S"),
        }
        response = self._request(params)
        payload = bounded_json(
            response, provider="GDELT", maximum_bytes=MAX_GDELT_RESPONSE_BYTES
        )
        raw_articles = payload.get("articles") if isinstance(payload, dict) else None
        if not isinstance(raw_articles, list):
            raise ValueError("GDELT response does not contain articles")
        retrieved_at = datetime.now(timezone.utc).isoformat()
        articles: list[dict] = []
        for item in raw_articles:
            if not isinstance(item, dict):
                continue
            url = canonical_article_url(str(item.get("url") or ""))
            published_at = parse_gdelt_timestamp(item.get("seendate"))
            title = str(item.get("title") or "").strip()
            if not url or not published_at or not title:
                continue
            publisher = str(item.get("domain") or "GDELT").strip()
            article = {
                "title": title,
                "description": "",
                "url": url,
                "publishedAt": published_at.isoformat(),
                "source": {"name": publisher},
                "provider": "GDELT",
                "retrievedAt": retrieved_at,
                "licenseClass": "gdelt-open-metadata",
            }
            if article_matches_symbol(symbol, article):
                articles.append(article)
        return articles

    def _request(self, params: dict[str, object]) -> httpx2.Response:
        """GDELT의 5초 호출 간격을 지키고 429 응답만 제한적으로 재시도한다."""

        for attempt in range(3):
            remaining = self._minimum_interval_seconds - (monotonic() - self._last_request_at)
            if remaining > 0:
                sleep(remaining)
            response = self._http.get(self._base_url, params=params)
            self._last_request_at = monotonic()
            if response.status_code != 429:
                return response
            if attempt < 2:
                retry_after = response.headers.get("retry-after", "")
                try:
                    delay = max(
                        self._minimum_interval_seconds * (2 ** attempt),
                        float(retry_after),
                    )
                except ValueError:
                    delay = self._minimum_interval_seconds * (2 ** attempt)
                sleep(delay)
        return response

    def latest_features(self, symbol: str) -> dict[str, float]:
        """최근 7일 기사에서 뉴스 AI 입력 특성을 계산한다."""

        key = validate_symbol(symbol)
        cached = self._features.get(key)
        if cached and cached[1] > monotonic():
            return cached[0]
        today = date.today()
        features = latest_news_features(
            self.articles(key, start=today - timedelta(days=7), end=today)
        )
        self._features[key] = (features, monotonic() + self._cache_seconds)
        return features

    def close(self) -> None:
        """HTTP 연결 자원을 반환한다."""

        self._http.close()


def canonical_article_url(value: str) -> str:
    """추적 매개변수를 제거해 기사 중복 판별에 사용할 URL을 만든다."""

    parsed = urlsplit(value.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return ""
    query = urlencode(
        [
            (key, item)
            for key, item in parse_qsl(parsed.query, keep_blank_values=True)
            if not key.casefold().startswith("utm_")
            and key.casefold() not in TRACKING_QUERY_KEYS
        ],
        doseq=True,
    )
    return urlunsplit((parsed.scheme, parsed.netloc.casefold(), parsed.path, query, ""))


def parse_gdelt_timestamp(value: object) -> datetime | None:
    """GDELT의 여러 `seendate` 표기를 UTC datetime으로 정규화한다."""

    digits = "".join(re.findall(r"\d", str(value or "")))
    if len(digits) < 14:
        return None
    try:
        return datetime.strptime(digits[:14], "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
    except ValueError:
        return None
