# Risk AI stability candidate (2026-08-28)

## Result

The risk candidate locks logistic regularization to `C=0.01`, disables class balancing, and uses
`0.55` only as the validation classification threshold. The runtime probability and conservative
risk signal band remain unchanged.

| Metric | Previous nested candidate | Stability candidate |
|---|---:|---:|
| Accuracy | 64.83% | 65.07% |
| Baseline improvement | +1.53%p | +1.77%p |
| Balanced accuracy | 56.24% | 55.16% |
| Brier score | 0.2232 | 0.2226 |
| ROC AUC | 0.6265 | 0.6270 |
| Minimum fold baseline improvement | -0.61%p | +0.34%p |
| Stable setting selection | No | Yes, 5/5 folds |

The refitted candidate artifact also passed its timestamp-aligned holdout with 64.41% accuracy,
52.11% balanced accuracy, 0.2280 Brier score, and 0.6050 ROC AUC. It is stored under
`artifacts/local-ai-candidates/risk-stability-20260828/candidate` and was not copied to the runtime
artifact directory.

## Promotion restriction

This threshold was proposed after inspecting an earlier outer-fold report. The result is useful as
a challenger but is not untouched evidence. Promotion therefore remains blocked until labeled rows
strictly later than `2026-08-20` provide enough independent timestamps and the candidate beats the
same-period majority baseline without refitting.

The candidate pipeline keeps `automatic_promotion=false`. This prevents an apparently improved
historical result from replacing the current model before forward validation.

## Automated forward validation

The existing Saturday candidate-validation task now performs these additional steps:

1. Enrich the incremental market dataset with point-in-time FRED observations into a separate
   `forward-risk-enriched` directory.
2. Load the frozen challenger and current champion without refitting either model.
3. Evaluate only labeled rows strictly after `2026-08-20`.
4. Keep the report in `awaiting_data` until at least 1,000 rows and 20 independent timestamps exist.
5. Mark `promotion_ready` only when the challenger passes the quality gate and its accuracy is
   above the champion on exactly the same forward period.

Even a ready report cannot copy the model automatically. The scheduled runner and report both keep
`automatic_promotion=false`. A Docker Dry Run completed all four scheduled validation stages with
exit code 0 on 2026-08-28.

## Other specialist stability controls

The same predefined `C=0.01`, unweighted, `0.50` threshold control was evaluated without model
promotion. It did not improve the remaining specialists enough to justify replacement.

| AI | Accuracy | Baseline | Balanced accuracy | ROC AUC | Result |
|---|---:|---:|---:|---:|---|
| Technical | 50.12% | 50.89% | 50.44% | 0.5091 | Reject |
| Financial | 49.17% | 50.39% | 49.31% | 0.4854 | Reject |
| Investor flow | 45.12% | 51.47% | 45.14% | 0.4524 | Reject |
| Synthesis | 51.53% | 51.84% | 51.13% | 0.5144 | Reject |

News remained skipped because 304 rows provide only 74 validation rows across three validation
timestamp groups. These results confirm that a stable optimizer setting cannot replace missing or
weak predictive information.

## Reproduce

```powershell
.venv\Scripts\python.exe scripts\ai\training\validate_local_ai_candidates.py `
  --data-dir datasets\local-ai-retrain-20260827-enriched `
  --output-dir artifacts\local-ai-candidates\risk-stability-20260828\candidate `
  --agent risk --c-grid 0.01 --class-weight-mode unweighted `
  --fixed-decision-threshold 0.55
```
