"""factory 파일은 백엔드 도메인 기능을 담당한다."""

from app.ai_reports.contracts import AIReportGenerator
from app.ai_reports.mock import MockAIReportGenerator
from app.ai_reports.openai import OpenAIReportGenerator
from app.config.settings import Settings


def build_ai_report_generator(settings: Settings) -> AIReportGenerator:
    """`build_ai_report_generator`은(는) 입력 값과 설정을 결합해 새 결과 객체를 생성합니다."""

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
