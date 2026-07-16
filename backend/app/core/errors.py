import logging
from datetime import datetime, timezone

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from app.core.compliance import DISCLAIMER
from app.core.sanitization import (
    public_provider_error_message,
    sanitize_external_data,
    sanitize_external_text,
)
from app.providers.errors import ProviderError

logger = logging.getLogger(__name__)


def _error_response(
    request: Request, status_code: int, code: str, message: str, data=None
) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "unknown")
    response = JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "request_id": request_id,
            "error": {"code": code, "message": message, "data": data},
            "data_as_of": datetime.now(timezone.utc).isoformat(),
            "disclaimer": DISCLAIMER,
            "is_investment_advice": False,
        },
    )
    response.headers["X-Request-ID"] = request_id
    return response


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    message = exc.detail if isinstance(exc.detail, str) else "요청을 처리할 수 없습니다."
    data = None if isinstance(exc.detail, str) else exc.detail
    response = _error_response(
        request,
        exc.status_code,
        f"HTTP_{exc.status_code}",
        message,
        data,
    )
    if exc.headers:
        for name, value in exc.headers.items():
            response.headers[name] = value
    return response


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return _error_response(
        request,
        422,
        "VALIDATION_ERROR",
        "요청 값이 유효하지 않습니다.",
        jsonable_encoder(exc.errors()),
    )


async def provider_exception_handler(request: Request, exc: ProviderError) -> JSONResponse:
    logger.warning(
        "Provider API error code=%s provider_request_id=%s",
        exc.code,
        exc.request_id,
    )
    sanitized = sanitize_external_data(exc.data or {})
    data = sanitized if isinstance(sanitized, dict) else {}
    if exc.request_id:
        data["provider_request_id"] = sanitize_external_text(exc.request_id, maximum=128)
    message = public_provider_error_message(exc)
    return _error_response(
        request,
        exc.status_code,
        exc.code,
        message,
        data or None,
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled API error", exc_info=exc)
    return _error_response(request, 500, "INTERNAL_ERROR", "서버 내부 오류가 발생했습니다.")
