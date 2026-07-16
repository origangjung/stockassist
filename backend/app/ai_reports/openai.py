import json
from typing import Any

import httpx2

from app.ai_reports.contracts import AIReportGenerator
from app.ai_reports.errors import ReportGenerationError


REPORT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "summary": {"type": "string"},
        "key_points": {"type": "array", "items": {"type": "string"}},
        "risk_factors": {"type": "array", "items": {"type": "string"}},
        "counterpoints": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["summary", "key_points", "risk_factors", "counterpoints"],
}


class OpenAIReportGenerator(AIReportGenerator):
    """Server-side Responses API adapter; it receives facts, never raw user prompts."""

    name = "openai"

    def __init__(
        self,
        *,
        api_key: str | None,
        base_url: str,
        model: str,
        timeout_seconds: float,
        transport: httpx2.BaseTransport | None = None,
    ) -> None:
        self._api_key = api_key
        self.model = model
        self._client = httpx2.Client(
            base_url=base_url.rstrip("/"),
            timeout=timeout_seconds,
            transport=transport,
            headers={"Accept": "application/json"},
        )

    def generate(self, facts: dict) -> dict:
        if not self._api_key:
            raise ReportGenerationError(
                "OPENAI_API_KEY is required when AI_REPORT_PROVIDER=openai",
                code="openai-api-key-missing",
            )
        payload = {
            "model": self.model,
            "instructions": (
                "You write an educational investment decision-support report. "
                "Write all narrative fields in Korean. "
                "Use only the supplied facts. Do not calculate new figures or make trading "
                "instructions. Never use buy, sell, recommend, target price, or imperative "
                "language. Describe uncertainty and risks in neutral language."
            ),
            "input": json.dumps(facts, default=str, ensure_ascii=False),
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "stockpilot_ai_report",
                    "strict": True,
                    "schema": REPORT_SCHEMA,
                }
            },
        }
        try:
            response = self._client.post(
                "/responses",
                json=payload,
                headers={"Authorization": f"Bearer {self._api_key}"},
            )
        except httpx2.HTTPError as exc:
            raise ReportGenerationError(
                "OpenAI report request failed", code="openai-request-failed"
            ) from exc
        request_id = response.headers.get("x-request-id")
        if response.status_code >= 400:
            raise ReportGenerationError(
                "OpenAI report request was rejected",
                code="openai-request-rejected",
                request_id=request_id,
                data={"status_code": response.status_code},
                status_code=502,
            )
        try:
            content = _output_text(response.json())
            generated = json.loads(content)
        except (ValueError, TypeError, KeyError) as exc:
            raise ReportGenerationError(
                "OpenAI returned an invalid structured report",
                code="openai-invalid-structured-output",
                request_id=request_id,
            ) from exc
        if not isinstance(generated, dict):
            raise ReportGenerationError(
                "OpenAI returned a non-object structured report",
                code="openai-invalid-structured-output",
                request_id=request_id,
            )
        return generated

    def close(self) -> None:
        self._client.close()


def _output_text(payload: dict[str, Any]) -> str:
    for output in payload.get("output", []):
        if not isinstance(output, dict):
            continue
        for content in output.get("content", []):
            if isinstance(content, dict) and content.get("type") == "output_text":
                text = content.get("text")
                if isinstance(text, str):
                    return text
    raise KeyError("output_text")
