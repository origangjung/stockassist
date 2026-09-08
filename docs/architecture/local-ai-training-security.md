# Local AI Training and Security

The daily collection and delayed-label procedure is documented in
`docs/operations/local-ai-data-accumulation-ko.md`. The collector keeps source features separate
and writes only rows with resolved five-session outcomes to `labeled/`; it never guesses labels for
recent unresolved rows.

## Data boundaries

- Market candles are adjusted by the configured stock provider and joined by trading date.
- SEC features use the original filing date, not the fiscal period end date.
- FINRA short-interest features become available only after the conservative publication delay.
- FRED values are joined as-of the observation date. Future revisions must not replace point-in-time
  values in a production backtest.
- News history must be stored continuously. A short recent NewsAPI window is not sufficient for a
  production synthesis model.

Training CSV files must be ordered by timestamp and contain no duplicate `(timestamp, symbol)` rows.
The trainer moves the validation boundary to the first row of a timestamp group so one trading day
cannot appear in both training and validation.

## Outcome target version 2

New candidate datasets must evaluate signals against market outcomes rather than proxy-label
continuations:

- Technical: positive when the stock's future return exceeds SPY over the same trading sessions.
- News: positive when the stock outperforms SPY after the article window.
- Investor flow: positive when the stock underperforms SPY after the FINRA signal.
- Risk: positive when the future path crosses the configured downside threshold; the true
  peak-to-trough drawdown is retained for audit.
- Financial outcome experiment: positive when the stock outperforms SPY from the first trading
  session strictly after the SEC filing date. The alignment session must be within seven calendar
  days and is stored as `outcome_start_timestamp`.

`future_return`, `benchmark_future_return`, `future_excess_return`, and
`future_max_drawdown` are label-audit fields. They must never be passed to a model as inference
features. Ambiguous outcomes may be excluded by magnitude before fitting, but the threshold must be
recorded and applied inside each walk-forward training experiment.

Production artifacts trained on the earlier proxy targets retain their existing runtime target
names until a version-2 candidate passes an untouched forward period. A dataset target change alone
must never overwrite or silently reinterpret a production artifact.

## Promotion rules

Candidate models are compared on a final chronological holdout. More rows alone are not a reason to
promote a model. Accuracy, majority-class baseline improvement, balanced accuracy, ROC AUC, Brier
score, and expected calibration error (ECE) must be reviewed together. Runtime inference rejects
models that do not beat the majority baseline, have balanced accuracy or ROC AUC at or below random
performance, have Brier score at or above the binary baseline, exceed ECE `0.10`, or do not meet the
model-specific minimum validation sample count.

Selective accuracy must always be reported with coverage, balanced accuracy, Brier score, and the
minimum time-fold balanced accuracy. Abstaining near probability 0.5 can increase reported accuracy
by removing difficult cases, but it does not improve the underlying full-coverage model and must not
be presented as such. Probability cutoffs must be fixed before an untouched forward evaluation.

Raw local-model probabilities are retained for internal signal thresholds and diagnostics but are
not presented as investment success probabilities. User-facing reports show positive, neutral, or
negative signal bands and a low, medium, or high evidence-confidence label. Until a unified-target
candidate passes an untouched period, synthesis uses the versioned rule-based diagnostic engine and
only specialists that pass the runtime quality gate.

A future learned synthesis model must use walk-forward specialist predictions. In-sample specialist
predictions must never be used as synthesis training features.

## ETF models

ETF requests use separate `etf_technical.json` and `etf_risk.json` artifacts. The training universe
contains broad-market, sector, bond, commodity, REIT, thematic, developed-market, and emerging-market
ETFs. ETF technical features include VTI-relative return and trend plus point-in-time macro context.
SPY runtime analysis uses VTI as its benchmark so it never compares SPY with itself.
The technical model also uses deterministic one-hot asset classes for broad equity, commodity,
fixed income, international, real estate, sector, and thematic ETFs. On the final 4,006-row holdout,
this raised accuracy from 0.5751 to 0.5811 and balanced accuracy from 0.5266 to 0.5335 while holding
the Brier score at 0.2398. The promoted artifact is `local-etf_technical-3548ba612cc2`.

ETF financial analysis is intentionally unavailable because an ETF does not have operating-company
financial statements. Holdings, NAV premium or discount, tracking error, expense ratio, and historical
fund flows require a separately licensed point-in-time dataset and are not inferred from candles.

ETF synthesis has its own `etf_synthesis.json` scope and consumes only technical and risk specialist
probability and confidence summaries plus point-in-time FRED macro context already used by the
specialists. Build its dataset with
`scripts/ai/data/build_etf_synthesis_local_ai_dataset.py`; each fold applies a 10-day embargo, evaluates the
specialists on earlier data, and then refits them through the embargo cutoff before producing later
predictions. The candidate evaluated on 2026 holdout data on 2026-08-09 did not pass the promotion
gate (accuracy 0.5504, balanced accuracy 0.4846, Brier score 0.2628), so it remains outside the
production artifact directory. Do not lower the gate or promote the candidate without new evidence.
Repeating the walk-forward experiment after adding asset classes still failed the gate (accuracy
0.5444, balanced accuracy 0.4903, Brier score 0.2633).

Adding the point-in-time macro context produced exploratory aggregate metrics of 0.5905 accuracy,
0.5500 balanced accuracy, and a 0.2471 Brier score on 1,846 rows. It was not promoted: regularization
was selected after observing that aggregate period, and monthly stability checks found 0.4527
balanced accuracy in January 2026 and majority-class behavior in March and April. The candidate is
retained in `artifacts/local-ai-etf-synthesis-macro-candidate` for comparison with a genuinely new
forward period. Runtime returns `data_unavailable` rather than imputing macro context when those
point-in-time values are missing.

## Artifact controls

Local models use bounded JSON artifacts and never load pickle data or executable model code. Schema
version 2 artifacts include a SHA-256 content checksum. Runtime loading rejects symlinks, oversized
files, checksum mismatches, duplicate feature names, invalid dimensions, non-finite numbers, and
unexpected model scope.

Artifacts and datasets remain outside Git. Keep their archive directories access-controlled and back
them up separately from application source.

## Provider controls

Local AI providers require credential-free HTTPS endpoint configuration. Symbols and response sizes
are bounded before data is processed. Provider failures expose only provider name and HTTP status;
credentials, request URLs, and response bodies are not included in public errors.

Production must set a 32-character or longer `ANALYSIS_API_KEY` in both FastAPI and the Next.js BFF.
Keep `ADMIN_API_KEY`, provider credentials, and `.env` out of browser bundles and source control.

## Required checks

Generate the production quality report before and after every candidate comparison:

```powershell
.venv\Scripts\python.exe scripts/ai/training/report_local_ai_accuracy.py --include-etf
```

The report verifies artifact checksums and displays accuracy, balanced accuracy, Brier score, final
holdout size, a 95% Wilson interval, and the runtime quality status. Accuracy without balanced
accuracy is not sufficient because a model can obtain a misleading score by predicting only the
majority class.

As of 2026-08-09, the general technical and synthesis artifacts remain quality-rejected. A refreshed
49,500-row candle dataset, return-magnitude filters, benchmark-relative features, symbol and sector
identity, logistic models, and tree models did not produce stable directional separation on the
untouched 2024-08-09 onward holdout. The expanded risk candidate also underperformed the production
risk model and was not promoted. The next useful data work is point-in-time earnings expectations,
event calendars, historical news coverage, ETF holdings and fund flows, and longer market-regime
coverage; changing algorithms without those inputs is not supported by the current evidence.

A higher-quality financial candidate was rebuilt from SEC Company Facts for 99 large US companies.
Rows use the original 10-Q filing date, retain the earliest filing for each fiscal period, and join
FRED observations only as of that filing date. After complete-case filtering, the dataset contains
1,628 rows across 83 companies. `local-financial-41260784b7bb` achieved 0.6391 accuracy, 0.6379
balanced accuracy, and a 0.2229 Brier score on 327 chronological validation rows. It remains a
candidate because it did not beat every production metric; the much larger validation set alone is
not sufficient reason to replace the champion. MMC failed SEC collection and was excluded rather
than imputed.

```powershell
.venv\Scripts\ruff.exe check backend scripts
.venv\Scripts\python.exe -m pytest backend/tests -q
corepack pnpm --dir frontend test
corepack pnpm audit --prod
```

Use `STOCKPILOT_NEXT_BUILD_VALIDATION=true` and a temporary `STOCKPILOT_NEXT_DIST_DIR` for Windows
build validation when standalone output cannot create symbolic links.
