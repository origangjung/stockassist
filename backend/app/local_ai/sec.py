"""sec 파일은 직접 학습 AI 특성과 실행 기능을 담당한다."""

from __future__ import annotations

from time import monotonic

import httpx2

from app.local_ai.financial_features import (
    latest_annual_valuation_inputs,
    latest_financial_features,
)
from app.local_ai.http_security import bounded_json, validate_https_endpoint, validate_symbol


MAX_SEC_RESPONSE_BYTES = 32 * 1024 * 1024


class SecCompanyFactsClient:
    """외부 서비스의 인증·요청·응답 검증을 캡슐화하는 client입니다."""

    def __init__(
        self,
        *,
        user_agent: str,
        base_url: str = "https://data.sec.gov",
        timeout_seconds: float = 30.0,
        cache_seconds: float = 3600.0,
    ) -> None:
        """`__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다."""

        if "@" not in user_agent or " " not in user_agent.strip():
            raise ValueError("SEC_USER_AGENT must include an application name and contact email")
        self._base_url = validate_https_endpoint(base_url, name="SEC_BASE_URL")
        self._http = httpx2.Client(
            timeout=timeout_seconds,
            headers={"User-Agent": user_agent, "Accept-Encoding": "gzip, deflate"},
        )
        self._cache_seconds = cache_seconds
        self._facts: dict[str, tuple[dict, float]] = {}
        self._submissions: dict[str, tuple[dict, float]] = {}
        self._ticker_map: dict[str, str] | None = None

    def companyfacts(self, symbol: str) -> dict:
        """`companyfacts`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        cik = self.cik(symbol)
        cached = self._facts.get(cik)
        if cached and cached[1] > monotonic():
            return cached[0]
        response = self._http.get(f"{self._base_url}/api/xbrl/companyfacts/CIK{cik}.json")
        payload = bounded_json(
            response, provider="SEC", maximum_bytes=MAX_SEC_RESPONSE_BYTES
        )
        if not isinstance(payload, dict):
            raise ValueError("SEC companyfacts response must be an object")
        self._facts[cik] = (payload, monotonic() + self._cache_seconds)
        return payload

    def cik(self, symbol: str) -> str:
        """`cik`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        symbol = validate_symbol(symbol)
        if self._ticker_map is None:
            response = self._http.get("https://www.sec.gov/files/company_tickers.json")
            payload = bounded_json(
                response, provider="SEC", maximum_bytes=4 * 1024 * 1024
            )
            self._ticker_map = {
                str(item["ticker"]).upper(): str(item["cik_str"]).zfill(10)
                for item in payload.values()
            }
        try:
            return self._ticker_map[symbol]
        except KeyError as exc:
            raise ValueError(f"SEC CIK not found for {symbol}") from exc

    def latest_features(self, symbol: str) -> dict[str, float] | None:
        """`latest_features`은(는) 필요한 데이터를 조회해 반환합니다."""

        return latest_financial_features(self.companyfacts(symbol))

    def latest_annual_valuation_inputs(self, symbol: str) -> dict[str, float | str]:
        """`latest_annual_valuation_inputs`은(는) 필요한 데이터를 조회해 반환합니다."""

        return latest_annual_valuation_inputs(self.companyfacts(symbol))

    def submissions(self, symbol: str) -> dict:
        """`submissions`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        cik = self.cik(symbol)
        cached = self._submissions.get(cik)
        if cached and cached[1] > monotonic():
            return cached[0]
        response = self._http.get(f"{self._base_url}/submissions/CIK{cik}.json")
        payload = bounded_json(
            response, provider="SEC", maximum_bytes=8 * 1024 * 1024
        )
        if not isinstance(payload, dict):
            raise ValueError("SEC submissions response must be an object")
        self._submissions[cik] = (payload, monotonic() + self._cache_seconds)
        return payload

    def release_cached_symbol(self, symbol: str) -> None:
        """대량 배치에서 처리가 끝난 종목의 대용량 SEC 응답만 메모리에서 해제한다."""

        normalized = validate_symbol(symbol)
        cik = self._ticker_map.get(normalized) if self._ticker_map else None
        if cik is None:
            return
        self._facts.pop(cik, None)
        self._submissions.pop(cik, None)

    def close(self) -> None:
        """`close`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        self._http.close()
