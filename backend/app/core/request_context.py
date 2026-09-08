"""request_context 파일은 백엔드 도메인 기능을 담당한다."""

from contextvars import ContextVar
import re
from uuid import uuid4
from time import perf_counter

import structlog
from structlog.contextvars import bind_contextvars, clear_contextvars
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

_request_id: ContextVar[str | None] = ContextVar("request_id", default=None)
_SAFE_REQUEST_ID = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")
logger = structlog.get_logger(__name__)


def current_request_id() -> str:
    """`current_request_id`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    request_id = _request_id.get()
    return request_id if request_id is not None else str(uuid4())


class RequestIdMiddleware(BaseHTTPMiddleware):
    """요청과 응답 사이에서 공통 정책을 적용하는 미들웨어입니다."""

    async def dispatch(self, request: Request, call_next):
        """`dispatch`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        supplied = request.headers.get("X-Request-ID", "")
        request_id = supplied if _SAFE_REQUEST_ID.fullmatch(supplied) else str(uuid4())
        token = _request_id.set(request_id)
        clear_contextvars()
        bind_contextvars(request_id=request_id)
        request.state.request_id = request_id
        started_at = perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            route_object = request.scope.get("route")
            logger.info(
                "http_request_completed",
                method=request.method,
                route=getattr(route_object, "path", "unmatched"),
                status=status_code,
                duration_ms=round((perf_counter() - started_at) * 1000, 3),
            )
            clear_contextvars()
            _request_id.reset(token)
