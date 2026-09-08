# Local AI diverse data candidate: 2026-08-13

This record covers the free, local-only `diverse-v3` candidate. No production artifact was
replaced. Provider credentials, filing bodies, article bodies, and raw API responses are not stored
in the generated datasets.

## Point-in-time sources

- Technical: stock candles, SPY-relative returns, sector ETF context, FRED macro state, and past
  20/60-session regime features.
- Financial: SEC Company Facts, SEC 8-K item metadata, filing acceptance timing, previous-session
  market and sector context, and past-quarter financial changes.
- News: article-window sentiment and source diversity, past-only news trends, FRED macro state,
  stock, SPY and sector context, latest published financial state, and SEC events strictly before
  the target date.
- Investor flow: FINRA daily short volume, consolidated short interest after a conservative 14-day
  publication delay, days-to-cover, stock and sector context, FRED macro state, long risk regime,
  and SEC events strictly before the target date.
- Risk: 20/60-session volatility, drawdown, downside deviation and trend, SPY and sector context,
  FRED macro state, and SEC events strictly before the target date.

The reproducible builder is `scripts/ai/data/build_diverse_local_ai_datasets.py`. Its as-of joins reject
future rows; financial event features use market data strictly before the event date. Outcome audit
columns are blocked from automatic model feature discovery.

## Dataset quality

| Agent | Rows | Symbols | Audited features | Period | Result |
| --- | ---: | ---: | ---: | --- | --- |
| Technical | 108,752 | 83 | 27 | 2020-06-25 to 2026-07-17 | Passed |
| Financial | 4,599 | 79 | 32 | 2020-07-13 to 2026-07-14 | Passed |
| News | 128 | 15 | 41 | 2026-07-15 to 2026-08-05 | Passed; insufficient history |
| Investor flow | 5,921 | 31 | 36 | 2025-09-09 to 2026-07-17 | Passed |
| Risk | 123,156 | 83 | 29 | 2020-06-25 to 2026-07-15 | Passed |

Every dataset has zero duplicate keys, missing feature values, non-finite values, and future
timestamps. The dataset directory and manifest are `datasets/local-ai-diverse-v3-20260812`; the
directory remains Git-ignored.

## Feature-group evaluation

All comparisons use timestamp-grouped purged walk-forward folds on identical rows.

| Agent | Base balanced accuracy | All-data balanced accuracy | Minimum fold change | Policy |
| --- | ---: | ---: | ---: | --- |
| Technical | 0.5089 | 0.5078 | 0.4956 to 0.4880 | Base only |
| Financial | 0.5123 | 0.5077 | 0.4841 to 0.4732 | Base only |
| News | 0.4431 | 0.4180 | 0.3889 to 0.2778 | Do not train until history expands |
| Investor flow | 0.4887 | 0.4959 | 0.3935 to 0.4402 | Keep research data; no directional model |
| Risk | 0.5807 | 0.5784 | 0.5102 to 0.5073 | Select long-regime group only |

Using only the six 60-session risk-regime additions reached 0.6727 accuracy, 0.5848 balanced
accuracy, 0.2109 Brier score, and 0.6306 ROC AUC over 80,618 walk-forward validation rows. This
improves all aggregate metrics over the same-row base comparison, but its minimum-fold balanced
accuracy fell from 0.5102 to 0.5046.

On the final 24,674-row holdout, the long-regime candidate scored 0.7114 accuracy, 0.5809 balanced
accuracy, and 0.2017 Brier score. The same-data base control scored 0.7460, 0.5770, and 0.1902.
The candidate is retained under `artifacts/local-ai-diverse-v3-risk-candidate` with no runtime
promotion because the small balanced-accuracy gain did not compensate for lower accuracy,
calibration quality, and minimum-fold stability.

## Next data requirement

Adding columns is not equivalent to adding independent signal. The next useful expansion is longer
historical news text with relevance and event labels, point-in-time analyst expectations and company
guidance, options positioning, borrow cost and availability, and a new untouched forward period.
Until those sources exist, the manifest keeps diverse columns for research while recommending only
feature groups that passed comparative evidence.
