# News and disclosure analysis

Phase 10 keeps raw content separate from deterministic interpretation.

- `DisclosureProvider` offers reproducible Mock data and an official DART implementation.
- `NewsProvider` offers Mock data and an RSS implementation. Its server-side feed URL is set with `NEWS_RSS_SEARCH_URL`.
- `DisclosureAnalysisService` stores standard disclosure records and produces keyword-based risk flags.
- `NewsAnalysisService` stores standard articles and produces a simple keyword sentiment score.

All interpretation is explicitly marked `experimental: true`: it is context only, not a recommendation or a trade instruction. The later AI-report phase must retain the compliance metadata.

Set `DISCLOSURE_PROVIDER=dart` with `DART_API_KEY` to use DART disclosures. Set `NEWS_PROVIDER=rss` to enable the configured RSS search feed. Both default to Mock mode so local work and contract tests remain deterministic.
