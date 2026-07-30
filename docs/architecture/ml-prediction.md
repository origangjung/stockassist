# ML prediction

Phase 12 provides an optional XGBoost model that estimates the probability that the close price
will be higher after a requested number of trading days. To keep local previews and the default
Docker image small, runtime prediction defaults to `lightweight`.

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
boundary. Runtime activation remains disabled by default. When
`MODEL_ARTIFACT_ACTIVATION_ENABLED=true`, XGBoost training writes an immutable UBJ artifact and a
bounded JSON manifest under `MODEL_ARTIFACT_DIR`. Promotion first verifies the version, symbol,
algorithm, horizon, regular-file boundary, size, and SHA-256 checksum. It then updates registry
metadata and atomically replaces the active scope pointer. Inference reloads only the verified
active artifact and otherwise follows the normal training path. The store retains one previous
version and supports checksum-verified atomic rollback; deployment orchestration must keep registry
and runtime rollback coordinated.

Activation requires XGBoost mode, persistence, and an administrator API key. Artifacts are ignored
by Git and must be transferred through an access-controlled artifact store rather than the source
repository. Validation remains `experimental`; promotion is not evidence of investment efficacy.
Docker Compose stores this directory in the dedicated `model-artifacts` volume so an explicitly
enabled active model survives API container recreation. Back up and validate that volume separately
from PostgreSQL; it must never contain Provider credentials or raw private account responses.

The endpoint is `GET /api/v1/stocks/{symbol}/prediction?horizon_days=5&limit=180`. It is a reference probability, not a target price, recommendation, or trade instruction.
