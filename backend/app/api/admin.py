from secrets import compare_digest

from fastapi import Depends, Header, HTTPException, Request, status

from app.config import Settings, get_settings
from app.core.rate_limit import RedisSlidingWindowLimiter, SlidingWindowLimiter
from redis.exceptions import RedisError

_failed_attempts = SlidingWindowLimiter(max_keys=4_096)


async def require_admin_access(
    request: Request,
    x_admin_key: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
) -> None:
    configured = settings.admin_api_key
    expected = configured.get_secret_value() if configured else ""
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin API is not configured",
        )
    client = request.client.host if request.client else "unknown"
    limit = settings.admin_max_failed_attempts
    window = settings.admin_lockout_seconds
    distributed: RedisSlidingWindowLimiter | None = (
        getattr(request.app.state, "distributed_rate_limiter", None)
        if settings.rate_limit_backend == "redis"
        else None
    )
    if settings.rate_limit_backend == "redis" and distributed is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin authentication limiter is unavailable",
        )
    try:
        limited = (
            await distributed.is_limited(client, limit=limit, window=window)
            if distributed is not None
            else _failed_attempts.is_limited(client, limit=limit, window=window)
        )
    except RedisError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin authentication limiter is unavailable",
        ) from exc
    if limited:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many invalid admin authentication attempts",
            headers={"Retry-After": str(settings.admin_lockout_seconds)},
        )
    if not x_admin_key or not compare_digest(x_admin_key, expected):
        try:
            allowed, remaining, _ = (
                await distributed.consume(client, limit=limit, window=window)
                if distributed is not None
                else _failed_attempts.consume(client, limit=limit, window=window)
            )
        except RedisError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Admin authentication limiter is unavailable",
            ) from exc
        blocked = not allowed or remaining == 0
        raise HTTPException(
            status_code=(
                status.HTTP_429_TOO_MANY_REQUESTS if blocked else status.HTTP_401_UNAUTHORIZED
            ),
            detail=(
                "Too many invalid admin authentication attempts"
                if blocked
                else "Invalid admin credentials"
            ),
            headers={"Retry-After": str(settings.admin_lockout_seconds)} if blocked else None,
        )
    try:
        if distributed is not None:
            await distributed.clear(client)
        else:
            _failed_attempts.clear(client)
    except RedisError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin authentication limiter is unavailable",
        ) from exc


def reset_admin_rate_limiter() -> None:
    """Reset process-local state for deterministic tests."""
    _failed_attempts.clear()
