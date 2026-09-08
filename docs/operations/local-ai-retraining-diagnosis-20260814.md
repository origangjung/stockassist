# Local AI retraining diagnosis: 2026-08-14

## Conclusion

The broader candidate did not fail because training stopped or the GPU was unused. It failed because
the target definition, universe, and time regimes changed while the available features contain little
stable out-of-time directional signal. The promotion gate correctly prevented a regression.

## Measured causes

1. The old and new datasets are not direct extensions of the same target.
   - Investor-flow overlap: 5,921 rows, only 44.57% label agreement.
   - News overlap: 109 rows, only 51.38% label agreement.
   - Financial rows use a market-outcome target in the candidate, while the original diagnostic set
     predicts whether the next filing's engineered financial-quality score improves.
   - The unified target asks whether five-session SPY-relative return is positive. This is harder and
     economically different from the original specialist diagnostics.

2. News has too little independent history.
   - 128 rows represent only 16 unique dates and 15 symbols.
   - The validation positive rate jumps from 47.00% to 75.00%.
   - Train AUC is 0.6929, but validation AUC is 0.4422.
   - Yield-curve, dollar, and VIX features shift by 3.178, 1.937, and 1.635 training standard
     deviations. The model is learning a short market regime, not durable news effects.

3. More rows do not provide the same number of independent observations.
   - Technical: 108,752 rows but 1,522 dates, averaging 71.45 correlated symbols per date.
   - Risk: 123,156 rows but 1,520 dates, averaging 81.02 correlated symbols per date.
   - Investor flow: 5,921 rows but only 215 dates.
   Cross-sectional rows from one market day share the same macro regime and cannot be treated as
   thousands of independent market episodes.

4. The current features have weak directional information.
   - Technical train/validation AUC: 0.5206 / 0.5102.
   - Financial train/validation AUC: 0.5339 / 0.4891 on the diverse target.
   - Investor-flow train/validation AUC: 0.5284 / 0.5011.
   - Risk retains useful downside separation at 0.6805 / 0.6372, but its 24.37% event rate means raw
     accuracy is dominated by the no-event class.

5. Market-regime drift remains material.
   - Investor-flow price volatility shifts by 0.442 standard deviations.
   - Risk Treasury 10-year, yield curve, and fed-funds features shift by 0.962, 0.547, and 0.501
     standard deviations.
   This explains why a coefficient fitted to an earlier period does not retain the same threshold in
   the final period.

## Correct next experiment

- Keep diagnostic specialists and the five-session relative-return model as separate targets.
- Accumulate at least several hundred independent news dates before retraining news.
- Add point-in-time earnings surprise, consensus revision, guidance change, event type, and sector
  interaction data instead of adding more transforms of the same price series.
- Evaluate by date and market regime, with purged walk-forward folds and symbol-group reports.
- Weight or subsample cross-sectional rows so one market date cannot dominate training.
- Promote only on a new untouched period after AUC, balanced accuracy, Brier score, calibration, and
  minimum-fold gates all pass.

Reproduce the measurements with:

```powershell
.venv\Scripts\python.exe scripts\ai\training\diagnose_local_ai_retraining.py `
  --data-dir datasets\local-ai-diverse-v3-20260812 `
  --reference-data-dir datasets\local-ai
```
