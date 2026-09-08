"""errors 파일은 백엔드 도메인 기능을 담당한다."""

from app.providers.errors import ProviderUnavailableError, ProviderValidationError


class ReportComplianceError(ProviderValidationError):
    """A generated report failed the mandatory decision-support safety gate."""


class ReportGenerationError(ProviderUnavailableError):
    """The configured report generator could not produce a usable report."""
