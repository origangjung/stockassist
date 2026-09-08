"""errors 파일은 외부 데이터 공급자 연동 기능을 담당한다."""

from typing import Any


class ProviderError(RuntimeError):
    """해당 실패 조건을 호출 계층에 구분해 전달하는 예외입니다."""

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
        """`__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다."""

        super().__init__(message)
        self.code = code
        self.request_id = request_id
        self.data = data
        if status_code is not None:
            self.status_code = status_code


class ProviderAuthenticationError(ProviderError):
    """해당 실패 조건을 호출 계층에 구분해 전달하는 예외입니다."""

    status_code = 502


class ProviderForbiddenError(ProviderError):
    """해당 실패 조건을 호출 계층에 구분해 전달하는 예외입니다."""

    status_code = 502


class ProviderNotFoundError(ProviderError, ValueError):
    """해당 실패 조건을 호출 계층에 구분해 전달하는 예외입니다."""

    status_code = 404


class ProviderConflictError(ProviderError):
    """해당 실패 조건을 호출 계층에 구분해 전달하는 예외입니다."""

    status_code = 409


class ProviderValidationError(ProviderError):
    """해당 실패 조건을 호출 계층에 구분해 전달하는 예외입니다."""

    status_code = 422


class ProviderRateLimitError(ProviderError):
    """해당 실패 조건을 호출 계층에 구분해 전달하는 예외입니다."""

    status_code = 503


class ProviderUnavailableError(ProviderError):
    """해당 실패 조건을 호출 계층에 구분해 전달하는 예외입니다."""

    status_code = 503
