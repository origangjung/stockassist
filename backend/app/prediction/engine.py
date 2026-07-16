from datetime import timezone
from decimal import Decimal
from hashlib import sha256

import numpy as np
from sklearn.metrics import accuracy_score, brier_score_loss
from xgboost import XGBClassifier

from app.prediction.contracts import PredictionResult
from app.prediction.features import build_feature_dataset
from app.prediction.validation import PurgedWalkForwardSplit
from app.providers.contracts import Candle


class XGBoostPredictionEngine:
    algorithm = "xgboost"

    def predict(self, symbol: str, candles: list[Candle], *, horizon_days: int) -> PredictionResult:
        dataset = build_feature_dataset(candles, horizon_days)
        splitter = PurgedWalkForwardSplit(horizon_days=horizon_days)
        probabilities: list[float] = []
        actuals: list[int] = []
        for train_indices, test_indices in splitter.split(len(dataset.labels)):
            train_labels = dataset.labels[train_indices]
            if len(np.unique(train_labels)) < 2:
                continue
            model = self._new_model()
            model.fit(dataset.features[train_indices], train_labels)
            probabilities.extend(model.predict_proba(dataset.features[test_indices])[:, 1])
            actuals.extend(dataset.labels[test_indices])
        if not probabilities:
            raise ValueError("insufficient class variation for walk-forward validation")
        final_model = self._new_model()
        final_model.fit(dataset.features, dataset.labels)
        probability = float(final_model.predict_proba(dataset.prediction_features)[0, 1])
        validation_count = len(probabilities)
        uncertainty = 1.96 * np.sqrt(probability * (1 - probability) / validation_count)
        metrics = {
            "accuracy": round(float(accuracy_score(actuals, np.asarray(probabilities) >= 0.5)), 4),
            "brier_score": round(float(brier_score_loss(actuals, probabilities)), 4),
            "validation_samples": float(validation_count),
            "folds": float(sum(1 for _ in splitter.split(len(dataset.labels)))),
        }
        training_fingerprint = sha256()
        training_fingerprint.update(dataset.features.tobytes())
        training_fingerprint.update(dataset.labels.tobytes())
        version_input = (
            f"{self.algorithm}|{symbol.upper()}|{horizon_days}|{dataset.data_as_of.isoformat()}|"
            f"{len(dataset.labels)}|{dataset.feature_names}|{training_fingerprint.hexdigest()}"
        )
        model_version = f"xgb-{sha256(version_input.encode()).hexdigest()[:12]}"
        return PredictionResult(
            symbol=symbol,
            horizon_days=horizon_days,
            rise_probability=_decimal(probability),
            confidence_lower=_decimal(max(0.0, probability - uncertainty)),
            confidence_upper=_decimal(min(1.0, probability + uncertainty)),
            model_version=model_version,
            validation_metrics=metrics,
            validation_status="experimental",
            data_as_of=dataset.data_as_of.astimezone(timezone.utc),
        )

    @staticmethod
    def _new_model() -> XGBClassifier:
        return XGBClassifier(
            n_estimators=40,
            max_depth=3,
            learning_rate=0.05,
            subsample=0.9,
            colsample_bytree=0.9,
            objective="binary:logistic",
            eval_metric="logloss",
            random_state=42,
            n_jobs=1,
        )


def _decimal(value: float) -> Decimal:
    return Decimal(str(round(value, 6)))
