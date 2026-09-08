# Local reliability and model validation: 2026-08-12

This record covers free, local-only reliability work. No deployment was performed, no model was
promoted, and no credentials or provider response bodies were recorded.

## Redis

- Atomic distributed limiter: 500 concurrent operations produced exactly 240 allowed and 260
  rejected requests at approximately 12,299 operations per second.
- Pub/Sub: 10 subscribers received 100 ordered messages each, for 1,000 verified deliveries at
  approximately 28,316 deliveries per second.
- Latest-value cache: value and two-second expiry both passed.
- Failure behavior: stopping Redis made the API fail closed with HTTP 503; after Redis restarted,
  readiness recovered to HTTP 200.

The reusable check is `scripts/operations/benchmark_redis_runtime.py`. It reads `REDIS_URL` only from the
process environment and does not print it.

## Local AI walk-forward evaluation

Six models were evaluated over four timestamp-grouped expanding windows. Same-timestamp rows stay
in one fold and a bounded purge gap separates training and validation. The reusable evaluator is
`scripts/ai/training/walk_forward_local_agents.py`.

| Model | Validation rows | Balanced accuracy | Minimum fold balanced accuracy | ROC AUC |
| --- | ---: | ---: | ---: | ---: |
| Technical | 39,524 | 0.5000 | 0.5000 | 0.4855 |
| Financial | 529 | 0.5938 | 0.5401 | 0.6413 |
| News | 100 | 0.7278 | 0.6793 | 0.8091 |
| Investor flow | 5,904 | 0.7471 | 0.7452 | 0.8230 |
| Risk | 39,524 | 0.5928 | 0.5628 | 0.6317 |
| Synthesis | 11,519 | 0.5353 | 0.5058 | 0.5503 |

Candidate artifacts were written under the ignored
`artifacts/local-ai-walk-forward-candidate` directory. They were not promoted because the same
walk-forward history selected their hyperparameters; a later untouched time period is still
required for independent promotion evidence. Technical and synthesis candidates remain below the
quality threshold.

## CUDA XGBoost

The isolated, network-disabled training container selected `cuda:0`. Each benchmark used four
purged folds and 400 trees per fold over 59,614 rows.

| Dataset | Validation rows | Balanced accuracy | Brier score | ROC AUC |
| --- | ---: | ---: | ---: | ---: |
| Technical | 39,524 | 0.5025 | 0.2523 | 0.5041 |
| Risk | 39,524 | 0.5634 | 0.2589 | 0.5882 |

Neither result justified promotion. The benchmark is
`scripts/ai/training/benchmark_gpu_xgboost_local_ai.py`; it always reports `artifact_promoted=false`.

An additional CUDA search compared the baseline with shallow and regularized configurations for
stock and ETF datasets. The strongest risk configuration used 600 trees, depth 2, learning rate
0.02, minimum child weight 16, and L2 regularization 10.

| Dataset | Validation rows | Balanced accuracy | Brier score | ROC AUC |
| --- | ---: | ---: | ---: | ---: |
| Stock technical, shallow | 39,524 | 0.5025 | 0.2507 | 0.5061 |
| Stock risk, shallow | 39,524 | 0.5792 | 0.2493 | 0.6046 |
| ETF technical, shallow | 34,920 | 0.4828 | 0.2749 | 0.4855 |
| ETF risk, shallow | 34,920 | 0.6128 | 0.1830 | 0.6870 |

The ETF risk configuration was refitted over all 52,650 rows on `cuda:0`. Its ignored candidate
model and SHA-256 manifest are stored under `artifacts/gpu-candidates`. The model loads with 600
trees and its checksum matches, but the manifest retains `promoted=false`. A later untouched time
period is required before considering runtime integration or promotion.

## High-quality source refresh

The quality candidate directory is `datasets/local-ai-quality-20260812`. Raw provider payloads and
credentials were not retained. `scripts/ai/training/audit_local_ai_datasets.py` checks required features,
timestamp ordering, duplicate symbol/timestamp keys, non-finite values, future timestamps, class
coverage, and symbol concentration before training.

| Specialist | Source | Rows | Symbols | Period | Quality result |
| --- | --- | ---: | ---: | --- | --- |
| Financial | SEC Company Facts | 1,588 | 83 | 2010-08-06 to 2026-05-11 | Passed |
| News | NewsAPI, Toss candles, FRED context | 232 | 20 | 2026-07-15 to 2026-08-07 | Passed |
| Investor flow | FINRA short volume, Toss market context | 9,307 | 41 | 2025-09-09 to 2026-08-04 | Passed |

The news collector now refuses request plans above `NEWS_API_DAILY_REQUEST_LIMIT`, deduplicates
symbols and articles, preserves enriched columns, and replaces the CSV atomically. News labels can
also require a minimum article count and minimum future tone change. FRED enrichment requests 60
days of lookback before the first training date so 20-day macro features are complete.

The refreshed investor-flow data scored 0.7463 balanced accuracy over 5,904 purged walk-forward
validation rows, slightly below the previous data's 0.7480 under identical settings. It was not
promoted. The expanded synthesis dataset passed quality checks and grew from 16,873 to 29,807 rows,
but balanced accuracy fell from 0.5327 to 0.5146. News remained unavailable to synthesis folds
because its 24-day history cannot train a pre-fold specialist without future leakage.

CUDA XGBoost found a useful nonlinear financial candidate on the SEC data:

| Model | Validation rows | Balanced accuracy | Brier score | ROC AUC |
| --- | ---: | ---: | ---: | ---: |
| Financial, depth 3 | 1,176 | 0.6784 | 0.2222 | 0.6929 |
| Investor flow, depth 2 | 5,904 | 0.7404 | 0.1740 | 0.8189 |

The financial result improves on the logistic candidate's 0.6017 balanced accuracy over a similar
walk-forward span. Its model and checksum manifest are stored under the ignored
`artifacts/gpu-candidates` directory with `promoted=false`. Runtime integration remains blocked on
an untouched later reporting period and an XGBoost inference adapter. The flow tree model did not
beat the logistic model and was discarded.

## Market-outcome target audit

The `outcome-v2` experiment replaced proxy targets with same-session SPY-relative outcomes. It used
free Toss candles for 83 SEC-covered US companies and SPY, point-in-time FRED context, SEC Company
Facts, FINRA short volume, and previously collected NewsAPI features. No paid API or external LLM
was used. Credentials and raw provider bodies were not written to the datasets.

The five-day market ledger contains 112,694 significant technical rows after excluding absolute
SPY-relative moves below 0.5 percentage points. The unfiltered 20-day ledger contains 129,197 rows.
Both cover 83 symbols from 2020 through 2026, have no duplicate keys, missing features, non-finite
values, or future timestamps, and keep maximum symbol concentration at or below 1.31%.

| Outcome target | Validation rows | Balanced accuracy | Minimum fold | ROC AUC | Decision |
| --- | ---: | ---: | ---: | ---: | --- |
| 5-day technical excess return | 74,727 | 0.5121 | 0.5039 | 0.5142 | Reject |
| 5-day news-driven excess return | 44 | 0.4644 | 0.4444 | 0.5011 | Reject; history too short |
| 5-day FINRA-driven underperformance | 4,059 | 0.4940 | 0.4653 | 0.4684 | Reject |
| 5-day downside event | 86,320 | 0.5549 | 0.5245 | 0.5734 | Candidate only |
| 20-day downside event at 8% | 84,328 | 0.5698 | 0.5124 | 0.6114 | Candidate only |
| Post-SEC-filing 20-day excess return | 820 | 0.5095 | 0.4923 | 0.5216 | Reject |

Adding SPY-relative, sector ETF, and FRED features did not make technical return direction stable.
Filtering for one- and two-percentage-point outcomes also failed to improve minimum-fold quality.
CUDA XGBoost did not beat the logistic candidates for technical, flow, financial outcome, or 20-day
risk targets. No outcome-v2 model was promoted.

This audit establishes that the earlier approximately 75% news and flow results measured future
news-tone and future short-volume continuation, not investable return direction. Raising real return
accuracy now requires historical article text and relevance labels, point-in-time earnings
expectations and guidance, actual short interest or borrow cost, options positioning, and a new
untouched forward period. Algorithm changes alone are not supported by this evidence.

## Event, short-interest, and selective-risk follow-up

FINRA consolidated short interest was added with a conservative 14-day publication delay. All
6,262 outcome-aligned rows across 31 symbols received short-interest change, days-to-cover, and
change-acceleration features. The linear candidate reached 0.4958 balanced accuracy and the CUDA
candidate reached 0.4898, so neither was promoted.

SEC submissions metadata produced 4,936 point-in-time 8-K events across 80 symbols. Features retain
only item categories, item count, acceptance timing, and event spacing; filing bodies are not stored.
Every event uses the first market session strictly after acceptance and a 20-session SPY-relative
outcome. Results and guidance subsets raised isolated aggregate scores in some searches but minimum
fold balanced accuracy fell as low as 0.4077, so no event candidate was promoted.

The 20-session risk experiment was expanded with past-only 60-session trend, volatility, drawdown,
downside deviation, and short/long volatility ratio features. Purged eight-fold results improved
from 0.5698 to 0.5844 balanced accuracy and from 0.6114 to 0.6311 ROC AUC. The unweighted expanded
candidate achieved 0.7136 accuracy, 0.5803 balanced accuracy, and a 0.2006 Brier score on the final
25,232-row holdout. A same-data base-feature control scored 0.7477, 0.5769, and 0.1892 respectively,
so the long-horizon schema was not promoted: its small class-balance gain did not justify lower
accuracy and calibration quality.

Selective prediction was evaluated at fixed probability cutoffs. With a 0.65 cutoff, the weighted
long-horizon walk-forward candidate covered 63.31% of validation rows and reached 0.7881 accuracy,
0.5621 balanced accuracy, and a 0.1664 Brier score. Its minimum-fold balanced accuracy was only
0.5053. This is useful evidence for abstaining on low-confidence cases, not evidence for model
promotion. The runtime artifact and feature contract remain unchanged pending a new untouched
forward period.

## Live provider checks

- SEC, FRED, FINRA, and NewsAPI returned all expected bounded feature groups for AAPL.
- Toss returned one quote and five daily candles for `005930`; all five candles were classified
  as `provider_adjusted`, and none were persisted.
- KIS credentials were not configured, so no live KIS WebSocket claim is made. Its authentication,
  reconnect, and subscription-limit behavior remains covered by isolated tests.

## PostgreSQL temporary benchmark

The benchmark used session-scoped temporary tables only. It did not insert, update, or delete
application data.

- Lifecycle table: 250,000 rows; indexed 105,408-row cutoff count in 11.44 ms.
- Rolled-back cleanup plan: 105,408-row delete in 16.24 ms.
- Partition table: 240,000 rows across 24 monthly partitions.
- Partition pruning: one 9,960-row monthly partition counted in 0.71 ms.

The repeatable SQL is `scripts/operations/benchmark_postgres_maintenance.sql`.
