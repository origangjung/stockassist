"""fred 파일은 직접 학습 AI 특성과 실행 기능을 담당한다."""

from __future__ import annotations

from datetime import date, timedelta
from time import monotonic

import httpx2

from app.local_ai.macro_features import FRED_SERIES
from app.local_ai.macro_features import macro_features_at
from app.local_ai.http_security import bounded_json, validate_https_endpoint


MAX_FRED_RESPONSE_BYTES = 8 * 1024 * 1024


class FredClient:
    """외부 서비스의 인증·요청·응답 검증을 캡슐화하는 client입니다."""

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str = "https://api.stlouisfed.org/fred",
        timeout_seconds: float = 30.0,
    ) -> None:
        """`__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다."""

        self._api_key = api_key
        self._base_url = validate_https_endpoint(base_url, name="FRED_BASE_URL")
        self._http = httpx2.Client(timeout=timeout_seconds)
        self._latest_cache: tuple[dict[str, float], float] | None = None

    def latest_macro_features(self) -> dict[str, float] | None:
        """`latest_macro_features`은(는) 필요한 데이터를 조회해 반환합니다."""

        if self._latest_cache and self._latest_cache[1] > monotonic():
            return self._latest_cache[0]
        today = date.today()
        observations = self.macro_observations(
            observation_start=today - timedelta(days=120),
            observation_end=today,
        )
        values = macro_features_at(observations, today)
        if values is not None:
            self._latest_cache = (values, monotonic() + 3600)
        return values

    def macro_observations(
        self, *, observation_start: date, observation_end: date
    ) -> dict[str, list[tuple[date, float]]]:
        """`macro_observations`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        return {
            name: self.observations(
                series_id,
                observation_start=observation_start,
                observation_end=observation_end,
            )
            for name, series_id in FRED_SERIES.items()
        }

    def observations(
        self,
        series_id: str,
        *,
        observation_start: date,
        observation_end: date,
    ) -> list[tuple[date, float]]:
        """`observations`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        response = self._http.get(
            f"{self._base_url}/series/observations",
            params={
                "series_id": series_id,
                "api_key": self._api_key,
                "file_type": "json",
                "observation_start": observation_start.isoformat(),
                "observation_end": observation_end.isoformat(),
            },
        )
        payload = bounded_json(
            response, provider="FRED", maximum_bytes=MAX_FRED_RESPONSE_BYTES
        )
        rows = payload.get("observations") if isinstance(payload, dict) else None
        if not isinstance(rows, list):
            raise ValueError("FRED response does not contain observations")
        values = []
        for row in rows:
            try:
                value = float(row["value"])
                observed = date.fromisoformat(str(row["date"]))
            except (KeyError, TypeError, ValueError):
                continue
            values.append((observed, value))
        return values

    def close(self) -> None:
        """`close`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        self._http.close()
