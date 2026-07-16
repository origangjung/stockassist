# ML prediction

Phase 12 provides an optional XGBoost model that estimates the probability that the close price
will be higher after a requested number of trading days. To keep local previews and the default
Docker image small, runtime prediction defaults to `lightweight_momentum`.

## Runtime modes

- `PREDICTION_ENGINE=lightweight` uses a deterministic 20-candle momentum/volatility baseline.
  It needs no scikit-learn, XGBoost, SciPy, CUDA or NVIDIA NCCL packages. It is intended for UI,
  pipeline and compliance testing; it reports zero validation folds and remains `experimental`.
- `PREDICTION_ENGINE=xgboost` enables the Phase 12 research model. Install it with
  `uv sync --locked --extra dev --extra ml`. For Docker set `INSTALL_ML=true` during the build.

- Features use only candles at or before the prediction timestamp: short returns, moving-average gaps, realised volatility, volume ratio, and RSI.
- Labels are separated from validation training windows with a horizon-sized purge gap.
- Evaluation uses expanding-window walk-forward splits only; rows are never randomly shuffled.
- Each XGBoost response contains a model version, validation accuracy and Brier score, a
  probability interval, and `validation_status: experimental`.

## Model Registry

Every persisted prediction registers a per-symbol model version. The version fingerprint includes
the normalized symbol, horizon, feature schema, data timestamp, and a digest of the training
features and labels, preventing different symbol-specific models from sharing an identifier.

New versions enter as `challenger`. The protected administrator API can promote one version to
`champion` for each `(symbol, algorithm, horizon_days)` scope; the repository demotes the previous
Champion in the same transaction and a partial unique index enforces the invariant at the database
boundary. Promotion changes registry metadata only. It does not deploy an artifact or change
runtime inference, and the outward validation status remains `experimental` until the separate
quantitative validation and artifact deployment workflow is implemented.
- Metadata is persisted in `model_versions` and results in `predictions`. Model artifacts are intentionally not promoted or reused until a later champion-challenger registry phase.

The endpoint is `GET /api/v1/stocks/{symbol}/prediction?horizon_days=5&limit=180`. It is a reference probability, not a target price, recommendation, or trade instruction.
