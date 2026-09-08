"""security 파일은 백엔드 도메인 기능을 담당한다."""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

_SENSITIVE_PREFIXES = (
    "/api/v1/admin",
    "/api/v1/broker-accounts",
    "/api/v1/portfolios",
)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """요청과 응답 사이에서 공통 정책을 적용하는 미들웨어입니다."""

    async def dispatch(self, request: Request, call_next):
        """`dispatch`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault(
            "Permissions-Policy",
            "camera=(), microphone=(), geolocation=(), payment=()",
        )
        if request.url.path in {"/docs", "/redoc", "/docs/oauth2-redirect"}:
            response.headers.setdefault(
                "Content-Security-Policy",
                "default-src 'self'; script-src 'self' https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "img-src 'self' data: https://fastapi.tiangolo.com; "
                "connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'",
            )
        else:
            response.headers.setdefault(
                "Content-Security-Policy",
                "default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'",
            )
        if request.url.path.startswith(_SENSITIVE_PREFIXES):
            response.headers["Cache-Control"] = "no-store, private"
            response.headers["Pragma"] = "no-cache"
        return response
