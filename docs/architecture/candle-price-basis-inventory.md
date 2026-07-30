# Candle price-basis provenance and inventory

`stock_candles.price_basis` states whether a candle is `unknown`, `unadjusted`,
`provider_adjusted`, or `point_in_time_adjusted`. The classification is evidence, not a value that
may be guessed from the OHLC series. `stock_candles.source_provider` records which provider most
recently supplied the stored row. `stock_candles.price_basis_rule_version` records the exact
versioned Provider rule used to classify it.

Migration `20260720_0020` assigns `source_provider=legacy_unknown` to every existing row. It does
not change `price_basis`. New raw and cleaned ingestion writes the selected Provider name to both
stages. A later ingestion that updates an existing candle updates its values, price basis, and
provider provenance together in the same transaction.

Migration `20260720_0021` assigns `price_basis_rule_version=legacy_unknown` to existing rows. New
ingestion receives this value from a `CandlePriceBasisPolicy` declared by the Provider. Unverified
policies are permitted to declare only `unknown`; known bases require either verified external
semantics or an explicitly synthetic source. The Broker Adapter validates every returned batch
against the declaration before any chart, indicator, score, prediction, backtest, or persistence
consumer receives it.

The administrator inventory endpoint is read-only:

```text
GET /api/v1/admin/candles/price-basis-inventory?symbol=005930&limit=200
```

`symbol` is required. The endpoint deliberately rejects unbounded, all-symbol requests so opening
the administrator screen cannot trigger a full-history aggregation as the candle table grows. The
supporting index starts with `symbol` before the provenance and classification columns.

It groups candles by Provider, price basis, rule version, stage, interval, and aggregation version,
and reports counts plus the first and last timestamps. Totals for `unknown`, legacy Provider, and
legacy rule rows are computed independently of the bounded group list. `groups_truncated` tells an
operator when the requested list did not contain every group.

Each returned group also has a read-only evidence checklist. `review_status=evidence_required`
enumerates the missing original Provider identifier, response or contract reference, endpoint
adjustment semantics, Provider contract test, and/or versioned rule. `evidence_recorded` means those
provenance fields already exist in the stored group; it is not a new claim that historical values
were independently audited. `review_ready_groups` and `blocked_review_groups` count only the bounded
group list and therefore must be read together with `groups_truncated`.

The response always includes `automatic_relabel=false` and `mutation_performed=false`. There is no
bulk relabel endpoint. In particular:

- `unknown_price_basis_requires_source_specific_evidence` means at least one row still lacks a
  verified adjustment classification.
- `legacy_rows_lack_provider_provenance` means the row predates explicit source recording.
- `legacy_rows_lack_price_basis_rule_version` means the row predates versioned policy recording.
- Provider provenance alone is insufficient to relabel a row; the Provider contract and actual
  endpoint semantics must first be verified and covered by contract tests.

Backtests requesting point-in-time corporate-action adjustment continue to reject `unknown`,
mixed, and already adjusted inputs. Inventory completion therefore improves observability without
weakening the backtest safety gate or rewriting historical raw data.

The internal administrator workspace renders this inventory under the operations tab through the
server-side admin proxy. Provider credentials and `X-Admin-Key` remain unavailable to browser
JavaScript. The UI waits for a required symbol before querying and deliberately contains no
mutation control.
