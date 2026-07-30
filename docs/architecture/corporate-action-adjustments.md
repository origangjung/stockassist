# Point-in-time corporate action adjustments

Stored-candle provider provenance and the non-mutating classification inventory are documented in
[Candle price-basis provenance and inventory](candle-price-basis-inventory.md).

Corporate actions can make historical prices discontinuous, but rewriting source candles would
destroy auditability and make past model or backtest results impossible to reproduce. StockPilot
therefore stores action revisions separately and creates adjusted candle views in memory.

## Immutable source and price basis

Every candle carries a `price_basis`:

- `unadjusted`: eligible for the StockPilot corporate-action engine.
- `provider_adjusted`: already adjusted by the external provider and rejected by this engine to
  prevent double adjustment. Toss daily candles currently use this value because the request sets
  `adjusted=true`.
- `unknown`: migrated legacy data; it cannot be adjusted until its provenance is verified.
- `point_in_time_adjusted`: an in-memory output view produced by adjustment version `2026.1`.

Raw and cleaned database rows are not overwritten by the adjustment engine. Weekly and monthly
aggregation preserves a single price basis and refuses mixed-basis input.

## Event revision model

Migration `20260719_0018` adds `corporate_actions` and the candle `price_basis` column. Each action
revision records:

- symbol, source and source event ID;
- immutable positive revision number;
- split, reverse split, cash dividend, stock dividend or rights issue classification;
- announcement time, effective time and `known_at` time;
- positive price and volume factors;
- announced, confirmed or cancelled status;
- deterministic adjustment-rule version and database recording time.

`(source, symbol, event_id, revision)` is unique. Replaying an identical revision is idempotent,
while a different payload for an existing revision is rejected. Corrections must create a new
revision so the old knowledge state remains reproducible.

## Source contract and bounded ingestion

Corporate-action sources implement a separate provider contract instead of becoming another
market-data capability. Each source declares its stable name, supported markets, revision strategy
and one of three trust states: `experimental`, `verified` or `disabled`.

Only `verified` sources may write revisions. Manual ingestion requires an administrator, an
explicit source and symbol, timezone-aware start/end timestamps, and a limit of 1–500 records. The
service rejects responses when source, symbol, effective-time range or fetched-time provenance does
not match the request. `known_at` after the provider's `fetched_at` is also rejected.

The repository stores each fetched batch in one transaction. An immutable-revision conflict rolls
back new rows from the same batch; identical replays are counted as unchanged. Automatic collection
is disabled until a concrete domestic or US source passes contract and historical reconciliation
tests.

## Evaluated source candidates

The admin status lists evaluated candidates separately from registered providers. A candidate is
not ingestible and does not contribute to `verified_source_count`.

- `dart` (`KR`, experimental): OpenDART has structured paid/bonus issue and capital-reduction
  endpoints with receipt identifiers, allocation ratios, outstanding-share counts and record-date
  fields. The initial mapper supports reviewed bonus issues and proportional share consolidations.
  It does not infer the exchange-effective ex-date from the disclosure record date, and mapped rows
  remain `announced` unless a later reconciliation explicitly confirms them.
- `sec-edgar` (`US`, experimental): SEC `submissions` and XBRL APIs are authoritative filing feeds,
  but they are not a dedicated corporate-action factor feed. StockPilot therefore treats SEC as a
  filing-candidate source only; no price or volume factor is generated from SEC data alone.

OpenDART references:
[bonus/paid-in capital increase](https://opendart.fss.or.kr/guide/detail.do?apiGrpCd=DS005&apiId=2020025),
[capital reduction](https://opendart.fss.or.kr/guide/detail.do?apiGrpCd=DS005&apiId=2020026).
SEC reference:
[EDGAR data APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces).

With an existing server-side `DART_API_KEY`, StockPilot registers a read-only DART candidate
collector. It resolves the symbol through the DART corporation-code catalog and queries
`fricDecsn.json` plus `crDecsn.json` for an administrator-selected range of at most 366 days.
The collector returns no more than 200 candidates. Invalid receipt numbers fail the response;
missing or ambiguous ratios remain visible with warnings instead of being silently confirmed.
The candidate preview is never persisted and cannot call the immutable revision repository.

## DART correction reconciliation

DART disclosure search is queried with `last_reprt_at=N`, so original and amended filings remain
visible. Its `rm` value can state that a later correction exists (`정`), and the report title can
identify a correction, but the documented response does not directly link an amended receipt to
its original receipt. StockPilot therefore produces revision-group suggestions rather than source
event revisions.

Candidates are grouped only when normalized report name, action type and decision/record anchor
match. Receipt date and number determine the suggested order. A group becomes
`likely_correction` only when both an original's later-correction remark and a correction title are
present; weaker matches are `ambiguous_multiple_receipts`, and single receipts are `isolated`.
Every group returns `requires_manual_confirmation=true` and `persistence_allowed=false`. The group
hash is an operational hint, not a durable source event ID.

Official reference:
[OpenDART disclosure search](https://opendart.fss.or.kr/guide/detail.do?apiGrpCd=DS001&apiId=2019001).

## Manual confirmation and evidence audit

Migration `20260720_0019` adds `corporate_action_approvals`. It links one immutable approval record
to one confirmed corporate-action revision and stores the reviewed DART receipt, candidate group,
DART filing URL, KRX evidence URL, reviewer boundary, approval time and a canonical evidence hash.
The action and evidence are committed in one transaction. A stock-master row is locked while the
next revision is assigned, so concurrent approvals for the same symbol cannot select the same
revision. Replaying identical evidence returns the existing revision.

This path is deliberately narrow: it currently supports DART candidates only, accepts KRX HTTPS
evidence only, has no bulk mode and is disabled unless explicitly configured. The server re-fetches
the exact candidate group and receipt before writing and never accepts user-supplied factors.
`known_at` is the server's approval time, not the filing or effective date, so manual review cannot
backdate knowledge into a backtest. The current `admin-api` reviewer value identifies the shared
administrator security boundary; named reviewer identity requires future RBAC and must not be
inferred from client input.

## Exchange effective-date verification boundary

The KRX OPEN API service catalog currently lists daily trading and instrument-reference APIs, but
does not list a corporate-action or ex-date endpoint. StockPilot records this source as
`not_available` for structured corporate-action verification instead of scraping the Data
Marketplace website or inferring an ex-date from price movements.

KRX separately describes security events as part of its end-of-day reference-information data
products. That candidate is recorded as `requires_contract` with an `unverified` effective-date
field until the licensed schema, redistribution terms and historical correction behavior are
reviewed. It cannot be registered as a verified provider merely because a feed is reachable.

The exchange verification provider contract requires a stable authority, market, access mode,
integration status and verified effective-date field. Results must carry matching source, symbol,
action type, requested/matched timezone-aware timestamps, evidence ID, HTTPS evidence URL and
fetch time. Unknown sources, unverified sources, inconsistent match flags and provenance mismatches
fail closed. The approval status exposes this catalog and reports
`automatic_effective_date_lookup=false`; the fallback remains a manually reviewed KRX evidence URL.

Official references:
[KRX OPEN API service catalog](https://openapi.krx.co.kr/contents/OPP/INFO/service/OPPINFO004.cmd),
[KRX data-distribution products](https://openapi.krx.co.kr/contents/OPP/DATA/OPPDATA002.jsp),
[KRX OPEN API usage process](https://openapi.krx.co.kr/contents/OPP/INFO/OPPINFO003.jsp).

## United States source policy

No single free SEC endpoint is treated as an authoritative normalized factor feed. EDGAR's public
APIs provide submission history and XBRL facts; they remain a filing crosscheck because corporate
action ratios and market-effective ex-dates can appear in issuer-specific narrative disclosures
rather than a uniform event schema.

The preferred venue-authoritative combination is Nasdaq Daily List for Nasdaq-listed securities
and NYSE Market Event Feed for NYSE Group listings. Nasdaq documents stock splits, stock/cash
dividends and a next-business-day ex-date list. NYSE documents programmatic current and historical
corporate-action access for NYSE, NYSE American, NYSE Arca and NYSE Texas listings. Both are
contract products, so their source definitions remain `experimental` and cannot write confirmed
revisions until entitlement, technical schema, correction semantics and redistribution rights are
validated. DTCC Asset Servicing is retained as a broader licensed candidate, but its automated
schema is marked `unverified` from the public material currently reviewed.

The resulting policy is:

1. use a contracted listing-venue source as the primary effective-date and factor source;
2. use SEC EDGAR only to crosscheck issuer intent and filing history;
3. require stable event identifiers and immutable corrections from each contracted source;
4. never combine Nasdaq coverage with NYSE coverage implicitly or label either one US-complete;
5. keep all three candidates non-ingestible until provider contract fixtures pass.

Official references:
[Nasdaq Daily List](https://nasdaqtrader.com/Trader.aspx?id=DailyListPD),
[NYSE corporate actions](https://www.nyse.com/market-data/corporate-actions),
[NYSE Market Event Feed](https://www.nyse.com/market-data/corporate-actions/market-event-feed),
[DTCC/DTC asset servicing](https://www.dtcc.com/about/businesses-and-subsidiaries/dtc.aspx),
[SEC EDGAR APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces).

## Look-ahead protection

For an analysis timestamp `T`, the engine:

1. ignores revisions whose `known_at` is after `T`;
2. ignores events whose effective time is after `T`;
3. chooses the latest known revision for each source event;
4. applies only the latest revision when its status is `confirmed`;
5. adjusts only candles strictly before the event's effective timestamp.

A cancellation or correction therefore changes results only after that revision became known. All
timestamps must be timezone-aware. Price and volume factors must be positive.

## Current integration boundary

`GET /api/v1/admin/corporate-actions` provides authenticated, read-only revision history with an
optional symbol and point-in-time filter. The admin UI exposes the same history and explicitly
reports `preview_only` and `raw_candles_mutated=false`.

`GET /api/v1/admin/corporate-actions/ingestion` exposes secret-free source and trust status.
`POST /api/v1/admin/corporate-actions/ingestion/{source}/{symbol}` is a bounded manual trigger and
uses the expensive-operation rate-limit group. With no verified provider registered it fails
closed and the dashboard reports `공급자 미등록`.

The dashboard can explicitly request the last year of DART candidates for a symbol. It displays
the proposed factors, review warnings and official filing link in a separate read-only section.
When manual approval is explicitly enabled, the screen exposes a separate fail-closed approval
form. It does not prefill the effective timestamp, KRX evidence URL or confirmation phrase. The
request travels through the authenticated server-side BFF and must satisfy the same candidate
re-fetch, evidence and confirmation contract as the admin API. Candidate preview itself remains
read-only.

The engine is not automatically inserted into indicators, Score or ML. Backtests now expose an
explicit `forward_point_in_time` opt-in that is separate from the backward-adjusted chart view.
It requires persistence and candles explicitly marked `unadjusted`; provider-adjusted,
legacy-unknown, mixed-basis, late-known and corrected event histories fail closed. The default
backtest mode remains `none`, and no consumer enables adjustment implicitly.

Legacy `unknown` rows must be classified outside the request path: inventory by provider and date
range, compare a sample against the source's adjusted/unadjusted definition, document evidence,
back up and restore-test the database, then update only the approved range. The application does
not contain a bulk relabel endpoint. Large reconciliation and backfill jobs belong to the desktop
validation workflow.
