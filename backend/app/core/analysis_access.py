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
        super().__init__(app)
        self._api_key = api_key or ""

    async def dispatch(self, request: Request, call_next):
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
    path = request.url.path.rstrip("/")
    if path.startswith("/api/v1/admin/"):
        return False
    return (
        request.method == "POST" and path in _PROTECTED_POSTS
    ) or (request.method == "GET" and path.endswith(_PROTECTED_SUFFIXES))
