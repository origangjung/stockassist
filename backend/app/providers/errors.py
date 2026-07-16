from typing import Any


class ProviderError(RuntimeError):
    status_code = 502

    def __init__(
        self,
        message: str,
        *,
        code: str = "provider-error",
        request_id: str | None = None,
        data: dict[str, Any] | None = None,
        status_code: int | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.request_id = request_id
        self.data = data
        if status_code is not None:
            self.status_code = status_code


class ProviderAuthenticationError(ProviderError):
    status_code = 502


class ProviderForbiddenError(ProviderError):
    status_code = 502


class ProviderNotFoundError(ProviderError, ValueError):
    status_code = 404


class ProviderConflictError(ProviderError):
    status_code = 409


class ProviderValidationError(ProviderError):
    status_code = 422


class ProviderRateLimitError(ProviderError):
    status_code = 503


class ProviderUnavailableError(ProviderError):
    status_code = 503
