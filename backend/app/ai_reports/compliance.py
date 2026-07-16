import re
from datetime import datetime
from typing import Any

from app.ai_reports.errors import ReportComplianceError


FORBIDDEN_ACTION_PATTERNS = (
    r"\b(?:strong\s+)?buy\b",
    r"\b(?:strong\s+)?sell\b",
    r"\bmust\s+(?:buy|sell)\b",
    r"\ub9e4\uc218(?:\ud558\uc138\uc694|\ud558\ub77c|\ud574\uc57c|\ucd94\ucc9c)?",
    r"\ub9e4\ub3c4(?:\ud558\uc138\uc694|\ud558\ub77c|\ud574\uc57c|\ucd94\ucc9c)?",
    r"\uc0ac\uc57c\s*(?:\ud569\ub2c8\ub2e4|\ud55c\ub2e4|\ud574\uc694)",
    r"\ud314\uc544\uc57c\s*(?:\ud569\ub2c8\ub2e4|\ud55c\ub2e4|\ud574\uc694)",
)


class ComplianceValidator:
    """Final, deterministic gate for all user-visible AI report content."""

    allowed_reference_signals = {
        "positive_watch",
        "neutral_watch",
        "defensive_watch",
        "risk_aware",
        "data_insufficient",
    }

    def validate(self, report: dict[str, Any]) -> None:
        required = ("disclaimer", "data_as_of", "is_investment_advice", "reference_signal")
        missing = [name for name in required if name not in report or report[name] in (None, "")]
        if missing:
            raise ReportComplianceError(
                "AI report is missing mandatory compliance metadata",
                code="report-compliance-metadata-missing",
                data={"fields": missing},
            )
        if report["is_investment_advice"] is not False:
            raise ReportComplianceError(
                "AI reports must never be marked as investment advice",
                code="report-investment-advice-forbidden",
            )
        if report["reference_signal"] not in self.allowed_reference_signals:
            raise ReportComplianceError(
                "AI report contains an unsupported reference signal",
                code="report-reference-signal-invalid",
            )
        if not isinstance(report["data_as_of"], datetime):
            raise ReportComplianceError(
                "AI report data_as_of must be a datetime",
                code="report-data-as-of-invalid",
            )

        text = "\n".join(self._strings(report))
        for pattern in FORBIDDEN_ACTION_PATTERNS:
            if re.search(pattern, text, flags=re.IGNORECASE):
                raise ReportComplianceError(
                    "AI report was blocked because it contains a trading instruction",
                    code="report-compliance-blocked",
                    data={"pattern": pattern},
                )

    def _strings(self, value: Any):
        if isinstance(value, str):
            yield value
        elif isinstance(value, dict):
            for item in value.values():
                yield from self._strings(item)
        elif isinstance(value, (list, tuple)):
            for item in value:
                yield from self._strings(item)
