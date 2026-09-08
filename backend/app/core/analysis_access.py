"""analysis_access 파일은 백엔드 도메인 기능을 담당한다."""

from datetime import datetime, timezone
from secrets import compare_digest
from uuid import uuid4

from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.core.compliance import DISCLAIMER


_PROTECTED_SUFFIXES = (
    "/ai-report",
    "/prediction",
    "/score",
    "/financials",
    "/news",
    "/disclosures",
    "/investor-flow",
)
_PROTECTED_POSTS = {
    "/api/v1/backtests",
    "/api/v1/backtests/walk-forward",
}


class AnalysisAccessMiddleware(BaseHTTPMiddleware):
    """Optional server-side key boundary for costly public analysis endpoints."""

    def __init__(self, app, *, api_key: str | None) -> None:
        """`__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다."""

        super().__init__(app)
        self._api_key = api_key or ""

    async def dispatch(self, request: Request, call_next):
        """`dispatch`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        if not self._api_key or not is_protected_analysis_request(request):
            return await call_next(request)
        supplied = request.headers.get("X-Analysis-Key", "")
        if supplied and compare_digest(supplied, self._api_key):
            return await call_next(request)
        request_id = getattr(request.state, "request_id", str(uuid4()))
        return JSONResponse(
            status_code=401,
            content={
                "success": False,
                "request_id": request_id,
                "error": {
                    "code": "ANALYSIS_AUTHENTICATION_REQUIRED",
                    "message": "분석 API 인증이 필요합니다.",
                    "data": None,
                },
                "data_as_of": datetime.now(timezone.utc).isoformat(),
                "disclaimer": DISCLAIMER,
                "is_investment_advice": False,
            },
            headers={
                "Cache-Control": "no-store, private",
                "WWW-Authenticate": 'ApiKey realm="StockPilot Analysis"',
            },
        )


def is_protected_analysis_request(request: Request) -> bool:
    """`is_protected_analysis_request`은(는) 입력 또는 현재 상태가 규칙을 만족하는지 검증합니다."""

    path = request.url.path.rstrip("/")
    if path.startswith("/api/v1/admin/"):
        return False
    return (
        request.method == "POST" and path in _PROTECTED_POSTS
    ) or (request.method == "GET" and path.endswith(_PROTECTED_SUFFIXES))
