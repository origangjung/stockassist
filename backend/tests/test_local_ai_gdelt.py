"""GDELT 뉴스 수집기의 응답 검증과 정규화를 확인한다."""

from datetime import date

import httpx2

from app.local_ai.gdelt import (
    GdeltNewsClient,
    canonical_article_url,
    parse_gdelt_timestamp,
)
from scripts.ai.data.build_news_local_ai_dataset import load_saved_articles


def test_gdelt_client_maps_only_valid_article_metadata():
    """정상 기사만 기존 뉴스 AI 입력 형식으로 변환하는지 확인한다."""

    def handler(request: httpx2.Request) -> httpx2.Response:
        assert request.url.params["mode"] == "artlist"
        assert request.url.params["format"] == "json"
        assert request.url.params["startdatetime"] == "20260801000000"
        return httpx2.Response(
            200,
            json={
                "articles": [
                    {
                        "url": "https://Example.com/a?utm_source=test&id=7",
                        "title": "Apple earnings beat expectations",
                        "seendate": "20260801T123000Z",
                        "domain": "Example.com",
                    },
                    {
                        "url": "https://example.com/unrelated",
                        "title": "Weyerhaeuser analyst report",
                        "seendate": "20260801T123000Z",
                        "domain": "Example.com",
                    },
                    {"url": "javascript:alert(1)", "title": "invalid", "seendate": "bad"},
                ]
            },
        )

    client = GdeltNewsClient(
        transport=httpx2.MockTransport(handler),
        daily_request_limit=2,
        minimum_interval_seconds=0,
    )
    try:
        articles = client.articles("AAPL", start=date(2026, 8, 1), end=date(2026, 8, 2))
    finally:
        client.close()

    assert len(articles) == 1
    assert articles[0]["url"] == "https://example.com/a?id=7"
    assert articles[0]["provider"] == "GDELT"
    assert articles[0]["licenseClass"] == "gdelt-open-metadata"


def test_gdelt_timestamp_and_canonical_url_are_stable():
    """날짜 형식과 추적 URL을 재현 가능한 값으로 정규화한다."""

    timestamp = parse_gdelt_timestamp("20260801T123000Z")

    assert timestamp is not None
    assert timestamp.isoformat() == "2026-08-01T12:30:00+00:00"
    assert canonical_article_url("https://EXAMPLE.com/a?fbclid=x&q=1#top") == (
        "https://example.com/a?q=1"
    )


def test_gdelt_retries_rate_limit_before_mapping_articles():
    attempts = 0

    def handler(_request: httpx2.Request) -> httpx2.Response:
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            return httpx2.Response(429, headers={"retry-after": "0"})
        return httpx2.Response(200, json={"articles": []})

    client = GdeltNewsClient(
        transport=httpx2.MockTransport(handler),
        daily_request_limit=1,
        minimum_interval_seconds=0,
    )
    try:
        assert client.articles(
            "AAPL", start=date(2026, 8, 1), end=date(2026, 8, 2)
        ) == []
    finally:
        client.close()

    assert attempts == 3


def test_saved_metadata_can_be_reused_for_later_outcome_labels(tmp_path):
    """수집 당시 정답 가격이 없던 기사도 다음 실행에서 복원되는지 확인한다."""

    target = tmp_path / "news-articles.csv"
    target.write_text(
        "symbol,provider,publisher,title,url,published_at,retrieved_at,license_class\n"
        "AAPL,GDELT,Example,Apple earnings headline,https://example.com/a,"
        "2026-08-01T12:30:00+00:00,2026-08-01T13:00:00+00:00,gdelt-open-metadata\n",
        encoding="utf-8",
    )

    articles = load_saved_articles(target)

    assert articles["AAPL"][0]["title"] == "Apple earnings headline"
    assert articles["AAPL"][0]["publishedAt"] == "2026-08-01T12:30:00+00:00"
