"""backend.app.ai_reports 패키지의 공개 구성 요소를 묶는다."""

from app.ai_reports.factory import build_ai_report_generator

__all__ = ["build_ai_report_generator"]
