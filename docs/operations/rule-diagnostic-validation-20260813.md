# Rule diagnostic validation: 2026-08-13

The `rule-based-diagnostic-v1` combiner was evaluated before user-facing activation. The source was
`datasets/local-ai/synthesis.csv`, which contains timestamp-grouped walk-forward specialist
predictions rather than in-sample predictions.

## Evaluation scope

- Included specialists: investor flow and risk, the two production specialists that currently pass
  individual quality gates.
- Target: the existing synthesis row label, future positive return used by the technical dataset.
- Signals: each specialist's frozen probability band was converted to positive, neutral, or
  negative. The combiner abstained when the combined score remained neutral.
- Policy thresholds: at least 1,000 directional rows, 5% coverage, balanced accuracy above 0.52,
  minimum-fold balanced accuracy above 0.50, and positive improvement over the majority baseline.

## Result

| Metric | Value |
| --- | ---: |
| Source rows | 11,350 |
| Directional rows | 2,366 |
| Coverage | 20.85% |
| Accuracy | 51.94% |
| Balanced accuracy | 50.36% |
| Majority baseline | 54.23% |
| Baseline improvement | -2.28%p |
| Minimum-fold balanced accuracy | 48.04% |

## Decision

The rule diagnostic is **not approved**. It fails aggregate balanced accuracy, majority-baseline
improvement, and minimum-period stability. The signed policy is stored at
`artifacts/local-ai/diagnostic-policy.json`; runtime validates its checksum and returns
`quality_rejected`, so no diagnostic score is displayed. Investor-flow and risk specialists remain
available independently because this result evaluates only their combination.

Re-evaluate after specialist targets are aligned and a new untouched forward period exists. Do not
change weights or thresholds against this same evaluation period and then claim it as independent
validation.
