from datetime import date

import httpx2
import pytest

from app.local_ai.official_rss import (
    OfficialFeed,
    OfficialRssNewsClient,
    _parse_feed_response,
)
from scripts.ai.data.build_news_local_ai_dataset import (
    article_metadata_allowed,
    load_saved_articles,
    merge_csv,
)


RSS = b"""<?xml version="1.0"?>
<rss version="2.0"><channel><item>
<title>SEC publishes a market update</title>
<link>https://www.sec.gov/news/example?utm_source=rss</link>
<pubDate>Fri, 28 Aug 2026 14:00:00 GMT</pubDate>
</item></channel></rss>"""

ATOM = b"""<?xml version="1.0"?>
<feed xmlns="http://www.w3.org/2005/Atom"><entry>
<title>Apple reports quarterly results</title>
<link href="https://www.apple.com/newsroom/2026/08/results/" />
<updated>2026-08-28T12:00:00Z</updated>
</entry></feed>"""


def test_official_rss_maps_metadata_and_enforces_symbol_scope_with_one_fetch():
    requests = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        requests.append(str(request.url))
        return httpx2.Response(200, content=ATOM if "apple.com" in request.url.host else RSS)

    feeds = (
        OfficialFeed(
            "U.S. SEC",
            "https://www.sec.gov/news/pressreleases.rss",
            frozenset({"SPY"}),
        ),
        OfficialFeed(
            "Apple Newsroom",
            "https://www.apple.com/newsroom/rss-feed.rss",
            frozenset({"AAPL"}),
        ),
    )
    client = OfficialRssNewsClient(
        user_agent="StockPilot test@example.com",
        feeds=feeds,
        transport=httpx2.MockTransport(handler),
    )
    try:
        apple = client.articles(
            "AAPL", start=date(2026, 8, 28), end=date(2026, 8, 29)
        )
        microsoft = client.articles(
            "MSFT", start=date(2026, 8, 28), end=date(2026, 8, 29)
        )
    finally:
        client.close()

    assert len(requests) == 2
    assert len(apple) == 1
    assert len(microsoft) == 0
    assert apple[0]["description"] == ""
    assert apple[0]["provider"] == "OfficialRSS"
    assert apple[0]["licenseClass"] == "publisher-official-rss-metadata"
    assert apple[0]["url"] == "https://www.apple.com/newsroom/2026/08/results/"


def test_official_rss_rejects_dtd_and_external_entity_declarations():
    response = httpx2.Response(
        200,
        content=b'<!DOCTYPE rss [<!ENTITY xxe SYSTEM "file:///etc/passwd">]><rss/>',
    )

    with pytest.raises(ValueError, match="declarations"):
        _parse_feed_response(response, publisher="Unsafe")


def test_official_rss_rejects_non_allowlisted_hosts():
    with pytest.raises(ValueError, match="allowlisted"):
        OfficialRssNewsClient(
            user_agent="StockPilot test@example.com",
            feeds=(
                OfficialFeed(
                    "Unknown",
                    "https://example.com/feed.xml",
                    frozenset({"SPY"}),
                ),
            ),
        )


def test_official_rss_rejects_a_feed_without_symbol_scope():
    with pytest.raises(ValueError, match="explicit symbol scope"):
        OfficialRssNewsClient(
            user_agent="StockPilot test@example.com",
            feeds=(
                OfficialFeed(
                    "U.S. SEC",
                    "https://www.sec.gov/news/pressreleases.rss",
                    frozenset(),
                ),
            ),
        )


def test_saved_official_metadata_is_filtered_and_pruned_by_symbol_scope(tmp_path):
    target = tmp_path / "news-articles.csv"
    target.write_text(
        "symbol,provider,publisher,title,url,published_at,retrieved_at,license_class\n"
        "MSFT,OfficialRSS,Federal Reserve Board,Fed update,https://www.federalreserve.gov/a,"
        "2026-08-28T12:00:00+00:00,2026-08-28T12:01:00+00:00,official\n"
        "AAPL,OfficialRSS,Apple Newsroom,Apple update,https://www.apple.com/a,"
        "2026-08-28T12:00:00+00:00,2026-08-28T12:01:00+00:00,official\n",
        encoding="utf-8",
    )

    loaded = load_saved_articles(target)
    merged = merge_csv(
        target,
        [],
        keys=("symbol", "url"),
        include=article_metadata_allowed,
    )

    assert "MSFT" not in loaded
    assert len(loaded["AAPL"]) == 1
    assert [(row["symbol"], row["publisher"]) for row in merged] == [
        ("AAPL", "Apple Newsroom")
    ]
