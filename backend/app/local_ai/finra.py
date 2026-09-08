"""finra 파일은 직접 학습 AI 특성과 실행 기능을 담당한다."""

from __future__ import annotations

import base64
from time import monotonic

import httpx2

from app.local_ai.flow_features import latest_flow_features
from app.local_ai.http_security import bounded_json, validate_https_endpoint, validate_symbol


MAX_FINRA_RESPONSE_BYTES = 8 * 1024 * 1024


class FinraShortVolumeClient:
    """외부 서비스의 인증·요청·응답 검증을 캡슐화하는 client입니다."""

    def __init__(
        self,
        *,
        base_url: str,
        token_url: str,
        client_id: str,
        client_secret: str,
        timeout_seconds: float = 30.0,
        cache_seconds: float = 900.0,
    ) -> None:
        """`__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다."""

        self._base_url = validate_https_endpoint(base_url, name="FINRA_API_BASE_URL")
        self._token_url = validate_https_endpoint(token_url, name="FINRA_TOKEN_URL")
        self._client_id = client_id
        self._client_secret = client_secret
        self._http = httpx2.Client(timeout=timeout_seconds)
        self._token: tuple[str, float] | None = None
        self._cache_seconds = cache_seconds
        self._features: dict[str, tuple[dict[str, float], float]] = {}

    def records(self, symbol: str) -> list[dict]:
        """`records`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        symbol = validate_symbol(symbol)
        body = {
            "limit": 5000,
            "fields": [
                "tradeReportDate",
                "securitiesInformationProcessorSymbolIdentifier",
                "shortParQuantity",
                "shortExemptParQuantity",
                "totalParQuantity",
                "reportingFacilityCode",
            ],
            "compareFilters": [
                {
                    "compareType": "equal",
                    "fieldName": "securitiesInformationProcessorSymbolIdentifier",
                    "fieldValue": symbol,
                }
            ],
        }
        response = self._http.post(
            f"{self._base_url}/data/group/otcMarket/name/regShoDaily",
            headers={"Authorization": f"Bearer {self._access_token()}", "Accept": "application/json"},
            json=body,
        )
        payload = bounded_json(
            response, provider="FINRA", maximum_bytes=MAX_FINRA_RESPONSE_BYTES
        )
        if not isinstance(payload, list):
            raise ValueError("FINRA Reg SHO response must be a list")
        return payload

    def short_interest_records(self, symbol: str) -> list[dict]:
        """`short_interest_records`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        symbol = validate_symbol(symbol)
        body = {
            "limit": 5000,
            "compareFilters": [
                {
                    "compareType": "equal",
                    "fieldName": "symbolCode",
                    "fieldValue": symbol,
                }
            ],
        }
        response = self._http.post(
            f"{self._base_url}/data/group/otcMarket/name/consolidatedShortInterest",
            headers={
                "Authorization": f"Bearer {self._access_token()}",
                "Accept": "application/json",
            },
            json=body,
        )
        payload = bounded_json(
            response, provider="FINRA", maximum_bytes=MAX_FINRA_RESPONSE_BYTES
        )
        if not isinstance(payload, list):
            raise ValueError("FINRA short-interest response must be a list")
        return payload

    def latest_features(self, symbol: str) -> dict[str, float] | None:
        """`latest_features`은(는) 필요한 데이터를 조회해 반환합니다."""

        key = validate_symbol(symbol)
        cached = self._features.get(key)
        if cached and cached[1] > monotonic():
            return cached[0]
        features = latest_flow_features(self.records(key))
        if features is not None:
            self._features[key] = (features, monotonic() + self._cache_seconds)
        return features

    def close(self) -> None:
        """`close`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        self._http.close()

    def _access_token(self) -> str:
        """`_access_token`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        if self._token and self._token[1] > monotonic() + 60:
            return self._token[0]
        basic = base64.b64encode(
            f"{self._client_id}:{self._client_secret}".encode()
        ).decode()
        response = self._http.post(
            self._token_url,
            params={"grant_type": "client_credentials"},
            headers={"Authorization": f"Basic {basic}"},
        )
        payload = bounded_json(response, provider="FINRA", maximum_bytes=64 * 1024)
        token = str(payload["access_token"])
        expires_in = max(float(payload.get("expires_in", 3600)), 120.0)
        self._token = (token, monotonic() + expires_in)
        return token
