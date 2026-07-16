from app.ai_reports.contracts import AIReportGenerator
from app.ai_reports.mock import MockAIReportGenerator
from app.ai_reports.openai import OpenAIReportGenerator
from app.config.settings import Settings


def build_ai_report_generator(settings: Settings) -> AIReportGenerator:
    if settings.ai_report_provider == "mock":
        return MockAIReportGenerator()
    return OpenAIReportGenerator(
        api_key=(
            settings.openai_api_key.get_secret_value()
            if settings.openai_api_key is not None
            else None
        ),
        base_url=settings.openai_base_url,
        model=settings.openai_model,
        timeout_seconds=settings.openai_timeout_seconds,
    )
