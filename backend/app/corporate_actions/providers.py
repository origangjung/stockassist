"""providers 파일은 백엔드 도메인 기능을 담당한다."""

from app.config import Settings
from app.corporate_actions.candidate_contracts import CorporateActionCandidateProvider


def build_corporate_action_candidate_providers(
    settings: Settings,
) -> list[CorporateActionCandidateProvider]:
    """`build_corporate_action_candidate_providers`은(는) 입력 값과 설정을 결합해 새 결과 객체를 생성합니다."""

    key = settings.dart_api_key.get_secret_value() if settings.dart_api_key else ""
    if not key:
        return []
    from app.corporate_actions.dart_candidates import (
        DartCorporateActionCandidateProvider,
    )

    return [
        DartCorporateActionCandidateProvider.create(
            base_url=settings.dart_base_url,
            api_key=key,
            timeout_seconds=settings.dart_timeout_seconds,
        )
    ]
