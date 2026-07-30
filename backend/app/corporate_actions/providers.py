from app.config import Settings
from app.corporate_actions.candidate_contracts import CorporateActionCandidateProvider


def build_corporate_action_candidate_providers(
    settings: Settings,
) -> list[CorporateActionCandidateProvider]:
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
