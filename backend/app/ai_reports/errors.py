from app.providers.errors import ProviderUnavailableError, ProviderValidationError


class ReportComplianceError(ProviderValidationError):
    """A generated report failed the mandatory decision-support safety gate."""


class ReportGenerationError(ProviderUnavailableError):
    """The configured report generator could not produce a usable report."""
