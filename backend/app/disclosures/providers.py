"""providers 파일은 백엔드 도메인 기능을 담당한다."""

from datetime import datetime, timedelta, timezone

from app.config import Settings
from app.disclosures.contracts import Disclosure, DisclosureProvider
from app.providers.errors import ProviderNotFoundError


class MockDisclosureProvider(DisclosureProvider):
    """외부 또는 모의 데이터 원천을 동일한 계약으로 제공하는 구현체입니다."""

    name = "mock"
    _corp_codes = {"005930": "00126380", "000660": "00164779", "035420": "00266961"}

    def list_disclosures(self, symbol: str, *, days: int, limit: int) -> list[Disclosure]:
        """`list_disclosures`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

        try:
            corp_code = self._corp_codes[symbol]
        except KeyError as exc:
            raise ProviderNotFoundError(
                f"Mock disclosure data does not contain {symbol}", code="disclosure-not-found"
            ) from exc
        now = datetime.now(timezone.utc)
        samples = [
            Disclosure(
                symbol,
                corp_code,
                f"202607{symbol}00001",
                "Mock Corporation",
                "Quarterly report",
                now - timedelta(days=7),
                "Mock Corporation",
                None,
                f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo=202607{symbol}00001",
            ),
            Disclosure(
                symbol,
                corp_code,
                f"202606{symbol}00002",
                "Mock Corporation",
                "Material event report",
                now - timedelta(days=24),
                "Mock Corporation",
                "Supplementary filing",
                f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo=202606{symbol}00002",
            ),
        ]
        cutoff = now - timedelta(days=days)
        return [item for item in samples if item.filed_at >= cutoff][:limit]


def build_disclosure_provider(settings: Settings) -> DisclosureProvider:
    """`build_disclosure_provider`은(는) 입력 값과 설정을 결합해 새 결과 객체를 생성합니다."""

    if settings.disclosure_provider == "mock":
        return MockDisclosureProvider()
    key = settings.dart_api_key.get_secret_value() if settings.dart_api_key else ""
    if not key:
        raise ValueError("DART_API_KEY is required when DISCLOSURE_PROVIDER=dart")
    from app.disclosures.dart import DartDisclosureProvider

    return DartDisclosureProvider.create(
        base_url=settings.dart_base_url,
        api_key=key,
        timeout_seconds=settings.dart_timeout_seconds,
    )
