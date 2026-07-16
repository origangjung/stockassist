from io import BytesIO
from zipfile import ZipFile

import httpx2

from app.disclosures.dart import DartDisclosureProvider
from app.disclosures.providers import MockDisclosureProvider
from app.news.providers import MockNewsProvider, RssNewsProvider
from app.repositories.memory import InMemoryDisclosureRepository, InMemoryNewsRepository
from app.services.content import DisclosureAnalysisService, NewsAnalysisService


def test_mock_content_is_persisted_and_marked_experimental():
    disclosure_repository = InMemoryDisclosureRepository()
    news_repository = InMemoryNewsRepository()

    disclosures = DisclosureAnalysisService(MockDisclosureProvider(), disclosure_repository).latest(
        "005930", days=90, limit=20
    )
    news = NewsAnalysisService(MockNewsProvider(), news_repository).latest("005930", limit=20)

    assert disclosures["experimental"] is True
    assert disclosures["persistence_status"] == "saved"
    assert len(disclosure_repository.items) == 2
    assert news["experimental"] is True
    assert news["sentiment_label"] == "neutral"
    assert len(news_repository.items) == 2


def test_dart_disclosure_provider_resolves_corp_code_and_maps_rows():
    archive = BytesIO()
    with ZipFile(archive, "w") as zip_file:
        zip_file.writestr(
            "CORPCODE.xml",
            "<result><list><corp_code>00126380</corp_code><stock_code>005930</stock_code></list></result>",
        )

    def handler(request: httpx2.Request) -> httpx2.Response:
        assert request.url.params["crtfc_key"] == "dart-key"
        if request.url.path == "/api/corpCode.xml":
            return httpx2.Response(200, content=archive.getvalue())
        assert request.url.path == "/api/list.json"
        assert request.url.params["corp_code"] == "00126380"
        assert request.url.params["last_reprt_at"] == "Y"
        return httpx2.Response(
            200,
            json={
                "status": "000",
                "list": [
                    {
                        "corp_code": "00126380",
                        "corp_name": "Example Corporation",
                        "rcept_no": "20260713000001",
                        "rcept_dt": "20260713",
                        "report_nm": "Material event report",
                        "flr_nm": "Example Corporation",
                        "rm": "",
                    }
                ],
            },
        )

    provider = DartDisclosureProvider.create(
        base_url="https://opendart.fss.or.kr/api",
        api_key="dart-key",
        transport=httpx2.MockTransport(handler),
    )
    try:
        result = provider.list_disclosures("005930", days=90, limit=20)
    finally:
        provider.close()

    assert len(result) == 1
    assert result[0].receipt_no == "20260713000001"
    assert result[0].document_url.endswith("rcpNo=20260713000001")


def test_rss_provider_parses_articles():
    feed = b"""<?xml version='1.0'?><rss><channel><item>
        <title>Example growth story</title><link>https://example.invalid/1</link>
        <source>Example News</source><pubDate>Mon, 13 Jul 2026 09:00:00 GMT</pubDate>
        <description>Growth and profit were reported.</description>
    </item></channel></rss>"""

    provider = RssNewsProvider.create(
        search_url="https://example.invalid/rss?q={query}",
        transport=httpx2.MockTransport(lambda _: httpx2.Response(200, content=feed)),
    )
    try:
        articles = provider.latest("005930", limit=20)
    finally:
        provider.close()

    assert len(articles) == 1
    assert articles[0].publisher == "Example News"
    assert articles[0].url == "https://example.invalid/1"
