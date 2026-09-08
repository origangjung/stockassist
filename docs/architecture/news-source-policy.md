# News source policy

## Current decision

StockPilot must collect news only through a documented API, licensed feed, or a publisher-provided
feed whose terms permit automated collection and the intended storage/training use.

- Keep `NewsAPI` as the current general-news adapter and SEC EDGAR as the authoritative US filing
  source.
- Use the official `GDELT DOC 2.0 API` as the default no-key training-news source. Store only
  article metadata and derived features, cite GDELT, and preserve the original publisher URL.
- Collect publisher-provided RSS metadata from the SEC, Federal Reserve Board, and Apple Newsroom.
  These feeds are fixed in an HTTPS host allowlist; only titles, canonical source links,
  publication/retrieval times, publisher names, and license classes are retained.
- Do not scrape Investing.com. Its terms explicitly prohibit automated extraction, scraping, data
  mining, and use of platform content to build a similar service.
- Do not depend on undocumented Yahoo Finance endpoints or HTML pages. Yahoo's public developer API
  catalog does not currently expose a supported Finance news API, and its API terms require valid
  credentials, attribution, and compliance with API-specific storage/use rules.
- Yahoo or Investing may be added later only through a written commercial license or an official,
  documented feed that permits this product's display, retention, and machine-learning use.

## Adapter boundary

Any future news provider belongs behind the existing news provider interface. The adapter must:

1. Record provider, canonical article URL, publication time, retrieval time, and license class.
2. Store metadata and derived features by default, not full copyrighted article bodies.
3. Enforce per-provider rate limits, timeouts, retries, and a kill switch.
4. Preserve point-in-time publication timestamps for training and deduplicate canonical URLs.
5. Pass a terms/licensing review before it is enabled in collection jobs.

The official RSS adapter additionally rejects DTD/entity declarations, limits responses to 2 MiB,
caches each feed to avoid repeated requests, requires a contact-form `SEC_USER_AGENT`, and can be
disabled with `OFFICIAL_RSS_ENABLED=false`.

## References checked on 2026-08-14

- Yahoo Developer API terms: <https://legal.yahoo.com/us/en/yahoo/terms/product-atos/apiforydn/index.html>
- Yahoo public API catalog: <https://developer.yahoo.com/api/>
- Investing.com terms: <https://www.investing.com/about-us/terms-and-conditions>
- GDELT terms and attribution requirement: <https://www.gdeltproject.org/about.html>
- GDELT DOC 2.0 API: <https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/>
- SEC RSS feeds: <https://www.sec.gov/about/rss-feeds>
- Federal Reserve RSS feeds: <https://www.federalreserve.gov/feeds/feeds.htm>
- Apple RSS information: <https://www.apple.com/ca/rss/>
