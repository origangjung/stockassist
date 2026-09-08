# Local AI unified-target candidate: 2026-08-13

This candidate tests the shared target requested by the model-quality review:
`future 5-session excess return versus SPY is positive`. Production artifacts were not replaced.

## Construction

- Market outcomes: `datasets/local-ai-outcome-v2-20260812/technical.csv`
- Specialist features: `datasets/local-ai-diverse-v3-20260812`
- Candidate output: `datasets/local-ai-unified-target-v1-20260813`
- Builder: `scripts/ai/data/relabel_specialists_with_market_outcomes.py`
- Technical, news, investor-flow, and risk rows use an exact symbol/date outcome join.
- Financial filings use the first strictly later market session within seven calendar days and
  retain `outcome_start_timestamp` for auditability.
- Every specialist now assigns label `1` only when the aligned five-session SPY excess return is
  positive. The previous inverse investor-flow label and downside-event risk label are not used in
  this candidate.

## Dataset audit

| Agent | Rows | Symbols | Coverage | Positive rate | Result |
| --- | ---: | ---: | ---: | ---: | --- |
| Technical | 108,752 | 83 | 100.00% | 48.77% | Passed |
| Financial | 4,590 | 79 | 99.80% | 47.69% | Passed |
| News | 128 | 15 | 100.00% | 53.12% | Passed; insufficient history |
| Investor flow | 5,921 | 31 | 100.00% | 47.17% | Passed |
| Risk | 108,602 | 83 | 88.18% | 48.78% | Passed |

The audit found no duplicate keys, missing values, non-finite features, future timestamps, or
timestamp ordering failures.

## Purged walk-forward result

Four timestamp-grouped folds and a five-timestamp purge were used where history allowed it. The
news dataset supported only three folds and 41 validation rows.

| Agent | Feature set selected | Validation rows | Accuracy | Balanced accuracy | Minimum fold | Brier | ROC AUC |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Technical | Base | 72,345 | 0.5215 | 0.5125 | 0.5007 | 0.2496 | 0.5151 |
| Financial | Base | 3,054 | 0.5200 | 0.5190 | 0.5068 | 0.2507 | 0.5155 |
| News | Base | 41 | 0.3415 | 0.5000 | 0.5000 | 0.2574 | 0.4524 |
| Investor flow | Base | 3,823 | 0.5156 | 0.4880 | 0.4649 | 0.2508 | 0.4398 |
| Risk | Base | 72,349 | 0.5206 | 0.5186 | 0.5031 | 0.2496 | 0.5218 |

Adding all audited sector, macro, long-regime, short-interest, and SEC-event features did not
improve the promotion decision. The best all-feature balanced accuracy was 0.5098 for risk, while
technical, financial, news, and investor flow were 0.5061, 0.4988, 0.4180, and 0.4851.

## Decision

Do not promote any unified-target candidate. None demonstrates stable economic signal across
walk-forward folds, and the news history is far below the 200-row validation gate. The production
specialists keep their diagnostic targets, while `rule-based-diagnostic-v1` remains the only local
synthesis path. The next useful work is accumulating longer point-in-time news and financial-event
history before repeating this comparison on a new untouched period.
