"""로컬 모델의 학습·평가·저장·추론을 안전하게 처리한다.

모델은 실행 가능한 pickle 대신 크기가 제한되고 체크섬이 있는 JSON으로 저장한다. 특성 순서,
표준화 값, 계수, 정답 정의와 시간 외 검증 지표를 함께 보관해 호환되지 않으면 사용을 거부한다.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from hashlib import sha256
from hmac import compare_digest
import json
import math
from pathlib import Path
import re
from typing import Any

import numpy as np

from app.local_ai.contracts import ModelName


SCHEMA_VERSION = 2
MAX_ARTIFACT_BYTES = 2 * 1024 * 1024
_VERSION_PATTERN = re.compile(r"^local-[a-z_]+-[0-9a-f]{12}$")


@dataclass(frozen=True)
class LocalModelArtifact:
    """학습 결과와 재현·검증 정보를 함께 저장하는 JSON 모델 계약이다."""

    schema_version: int
    agent: ModelName
    model_version: str
    feature_names: list[str]
    means: list[float]
    scales: list[float]
    coefficients: list[float]
    intercept: float
    metrics: dict[str, float]
    training_samples: int
    trained_at: str
    content_sha256: str


class LocalLogisticModel:
    """표준화와 확률 보정을 포함하는 로컬 로지스틱 회귀 모델이다."""

    def __init__(self, artifact: LocalModelArtifact) -> None:
        """검증된 모델 artifact를 메모리에 올려 추론 가능한 상태로 만든다."""

        self.artifact = artifact

    @classmethod
    def train(
        cls,
        agent: ModelName,
        feature_names: tuple[str, ...],
        features: np.ndarray,
        labels: np.ndarray,
        *,
        iterations: int = 1200,
        learning_rate: float = 0.05,
        l2: float = 0.001,
        validation_gap: int = 0,
        validation_start: int | None = None,
        decision_threshold: float = 0.5,
        prediction_horizon_days: int = 5,
    ) -> LocalLogisticModel:
        """시간순 학습·검증 구간으로 모델을 학습하고 검증 지표를 artifact에 기록한다."""

        x = np.asarray(features, dtype=float)
        y = np.asarray(labels, dtype=float)
        if x.ndim != 2 or x.shape[1] != len(feature_names) or len(x) != len(y):
            raise ValueError("training feature shape does not match the agent schema")
        if len(x) < 50:
            raise ValueError("at least 50 labeled rows are required")
        if not np.isfinite(x).all() or not np.isfinite(y).all():
            raise ValueError("training data contains non-finite values")
        if set(np.unique(y)) != {0.0, 1.0}:
            raise ValueError("labels must contain both binary classes 0 and 1")

        split = _validation_split(len(x), validation_start)
        validation_x, validation_y = x[split:], y[split:]
        train_end = split - validation_gap
        if train_end < 25:
            raise ValueError("validation gap leaves too few training rows")
        train_x, train_y = x[:train_end], y[:train_end]
        means = train_x.mean(axis=0)
        scales = train_x.std(axis=0)
        scales[scales < 1e-12] = 1.0
        coefficients, intercept = _fit(
            (train_x - means) / scales,
            train_y,
            iterations=iterations,
            learning_rate=learning_rate,
            l2=l2,
        )
        probabilities = _sigmoid(((validation_x - means) / scales) @ coefficients + intercept)
        metrics = classification_metrics(
            probabilities,
            validation_y,
            threshold=decision_threshold,
        )
        _record_prediction_horizon(metrics, prediction_horizon_days)
        fingerprint = sha256()
        fingerprint.update(agent.encode())
        fingerprint.update(x.tobytes())
        fingerprint.update(y.tobytes())
        fingerprint.update(
            json.dumps(
                {
                    "iterations": iterations,
                    "learning_rate": learning_rate,
                    "l2": l2,
                    "validation_gap": validation_gap,
                    "validation_start": validation_start,
                    "decision_threshold": decision_threshold,
                    "prediction_horizon_days": prediction_horizon_days,
                },
                sort_keys=True,
            ).encode()
        )
        version = f"local-{agent}-{fingerprint.hexdigest()[:12]}"
        artifact = LocalModelArtifact(
            schema_version=SCHEMA_VERSION,
            agent=agent,
            model_version=version,
            feature_names=list(feature_names),
            means=means.tolist(),
            scales=scales.tolist(),
            coefficients=coefficients.tolist(),
            intercept=float(intercept),
            metrics=metrics,
            training_samples=len(x),
            trained_at=datetime.now(timezone.utc).isoformat(),
            content_sha256="",
        )
        return cls(_signed_artifact(artifact))

    @classmethod
    def train_sklearn(
        cls,
        agent: ModelName,
        feature_names: tuple[str, ...],
        features: np.ndarray,
        labels: np.ndarray,
        *,
        inverse_regularization: float = 0.1,
        validation_gap: int = 0,
        validation_start: int | None = None,
        class_weight_balanced: bool = False,
        positive_class_weight: float | None = None,
        refit_full_data: bool = False,
        decision_threshold: float = 0.5,
        prediction_horizon_days: int = 5,
    ) -> LocalLogisticModel:
        """scikit-learn으로 후보를 학습하되 동일한 안전한 JSON 계약으로 반환한다."""

        try:
            from sklearn.linear_model import LogisticRegression
        except ImportError as exc:
            raise ValueError("scikit-learn is required for the sklearn trainer") from exc
        x = np.asarray(features, dtype=float)
        y = np.asarray(labels, dtype=float)
        _validate_training_data(x, y, feature_names)
        split = _validation_split(len(x), validation_start)
        validation_x, validation_y = x[split:], y[split:]
        train_end = split - validation_gap
        if train_end < 25:
            raise ValueError("validation gap leaves too few training rows")
        train_x, train_y = x[:train_end], y[:train_end]
        if class_weight_balanced and positive_class_weight is not None:
            raise ValueError("balanced and explicit positive class weights are exclusive")
        if positive_class_weight is not None and positive_class_weight <= 0:
            raise ValueError("positive class weight must be positive")
        means = train_x.mean(axis=0)
        scales = train_x.std(axis=0)
        scales[scales < 1e-12] = 1.0
        classifier = LogisticRegression(
            C=inverse_regularization,
            class_weight=(
                {0: 1.0, 1: positive_class_weight}
                if positive_class_weight is not None
                else "balanced"
                if class_weight_balanced
                else None
            ),
            max_iter=3000,
            random_state=42,
        )
        classifier.fit((train_x - means) / scales, train_y)
        coefficients = classifier.coef_[0]
        intercept = float(classifier.intercept_[0])
        probabilities = _sigmoid(
            ((validation_x - means) / scales) @ coefficients + intercept
        )
        metrics = classification_metrics(
            probabilities,
            validation_y,
            threshold=decision_threshold,
        )
        _record_prediction_horizon(metrics, prediction_horizon_days)
        if refit_full_data:
            # 검증 지표는 시간순 홀드아웃에서 고정하고, 운영 계수만 최신 창 전체로 다시 학습한다.
            means = x.mean(axis=0)
            scales = x.std(axis=0)
            scales[scales < 1e-12] = 1.0
            classifier.fit((x - means) / scales, y)
            coefficients = classifier.coef_[0]
            intercept = float(classifier.intercept_[0])
        fingerprint = sha256()
        fingerprint.update(agent.encode())
        fingerprint.update(x.tobytes())
        fingerprint.update(y.tobytes())
        fingerprint.update(
            json.dumps(
                {
                    "trainer": "sklearn-logistic",
                    "inverse_regularization": inverse_regularization,
                    "validation_gap": validation_gap,
                    "validation_start": validation_start,
                    "class_weight_balanced": class_weight_balanced,
                    "positive_class_weight": positive_class_weight,
                    "refit_full_data": refit_full_data,
                    "decision_threshold": decision_threshold,
                    "prediction_horizon_days": prediction_horizon_days,
                },
                sort_keys=True,
            ).encode()
        )
        artifact = LocalModelArtifact(
            schema_version=SCHEMA_VERSION,
            agent=agent,
            model_version=f"local-{agent}-{fingerprint.hexdigest()[:12]}",
            feature_names=list(feature_names),
            means=means.tolist(),
            scales=scales.tolist(),
            coefficients=coefficients.tolist(),
            intercept=intercept,
            metrics=metrics,
            training_samples=len(x),
            trained_at=datetime.now(timezone.utc).isoformat(),
            content_sha256="",
        )
        return cls(_signed_artifact(artifact))

    def predict_probability(self, values: dict[str, float]) -> float:
        """학습 당시 특성 순서와 표준화를 적용해 보정된 양성 확률을 계산한다."""

        names = self.artifact.feature_names
        if set(values) != set(names):
            raise ValueError("inference features do not match the trained model")
        row = np.asarray([values[name] for name in names], dtype=float)
        if not np.isfinite(row).all():
            raise ValueError("inference features contain non-finite values")
        means = np.asarray(self.artifact.means)
        scales = np.asarray(self.artifact.scales)
        coefficients = np.asarray(self.artifact.coefficients)
        return float(_sigmoid(((row - means) / scales) @ coefficients + self.artifact.intercept))

    def save(self, path: str | Path) -> None:
        """체크섬을 포함한 실행 불가능 JSON 형식으로 모델을 원자적으로 저장한다."""

        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix(f"{target.suffix}.tmp")
        artifact = _signed_artifact(self.artifact)
        temporary.write_text(
            json.dumps(asdict(artifact), ensure_ascii=True), encoding="utf-8"
        )
        temporary.replace(target)

    @classmethod
    def load(cls, path: str | Path, *, expected_agent: ModelName) -> LocalLogisticModel:
        """크기·스키마·체크섬·AI 종류를 검증한 뒤 모델을 불러온다."""

        source = Path(path)
        if not source.is_file() or source.is_symlink():
            raise ValueError("local model artifact is missing or invalid")
        try:
            raw = source.read_bytes()
            if len(raw) > MAX_ARTIFACT_BYTES:
                raise ValueError("local model artifact is too large")
            decoded = json.loads(raw)
            if not isinstance(decoded, dict):
                raise ValueError("local model artifact root must be an object")
            payload: dict[str, Any] = decoded
            supplied_checksum = str(payload.get("content_sha256") or "")
            expected_checksum = _payload_checksum(payload)
            if not compare_digest(supplied_checksum, expected_checksum):
                raise ValueError("local model artifact checksum is invalid")
            artifact = LocalModelArtifact(**payload)
        except (OSError, ValueError, TypeError) as exc:
            raise ValueError("local model artifact cannot be decoded") from exc
        if artifact.schema_version != SCHEMA_VERSION or artifact.agent != expected_agent:
            raise ValueError("local model artifact schema or scope mismatch")
        if (
            not isinstance(artifact.feature_names, list)
            or not isinstance(artifact.means, list)
            or not isinstance(artifact.scales, list)
            or not isinstance(artifact.coefficients, list)
            or not isinstance(artifact.metrics, dict)
            or not isinstance(artifact.training_samples, int)
            or isinstance(artifact.training_samples, bool)
            or not isinstance(artifact.trained_at, str)
            or not isinstance(artifact.model_version, str)
        ):
            raise ValueError("local model artifact field types are invalid")
        width = len(artifact.feature_names)
        if width == 0 or any(
            len(values) != width
            for values in (artifact.means, artifact.scales, artifact.coefficients)
        ):
            raise ValueError("local model artifact dimensions are invalid")
        if (
            len(set(artifact.feature_names)) != width
            or width > 256
            or artifact.training_samples < 50
            or not _VERSION_PATTERN.fullmatch(artifact.model_version)
            or not artifact.model_version.startswith(f"local-{expected_agent}-")
            or any(not isinstance(name, str) or not name for name in artifact.feature_names)
        ):
            raise ValueError("local model artifact metadata is invalid")
        numeric_values = [
            *artifact.means,
            *artifact.scales,
            *artifact.coefficients,
            artifact.intercept,
            *artifact.metrics.values(),
        ]
        if (
            any(not isinstance(value, (int, float)) or not math.isfinite(value) for value in numeric_values)
            or any(value <= 0 for value in artifact.scales)
        ):
            raise ValueError("local model artifact contains invalid numeric values")
        try:
            datetime.fromisoformat(artifact.trained_at)
        except (TypeError, ValueError) as exc:
            raise ValueError("local model artifact timestamp is invalid") from exc
        return cls(artifact)


def _payload_checksum(payload: dict[str, Any]) -> str:
    """`_payload_checksum`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    unsigned = {key: value for key, value in payload.items() if key != "content_sha256"}
    encoded = json.dumps(
        unsigned, ensure_ascii=True, sort_keys=True, separators=(",", ":")
    ).encode()
    return sha256(encoded).hexdigest()


def _signed_artifact(artifact: LocalModelArtifact) -> LocalModelArtifact:
    """`_signed_artifact`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    payload = asdict(artifact)
    payload["content_sha256"] = _payload_checksum(payload)
    return LocalModelArtifact(**payload)


def _fit(
    x: np.ndarray,
    y: np.ndarray,
    *,
    iterations: int,
    learning_rate: float,
    l2: float,
) -> tuple[np.ndarray, float]:
    """`_fit`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    coefficients = np.zeros(x.shape[1], dtype=float)
    intercept = 0.0
    for _ in range(iterations):
        probabilities = _sigmoid(x @ coefficients + intercept)
        error = probabilities - y
        coefficients -= learning_rate * ((x.T @ error) / len(x) + l2 * coefficients)
        intercept -= learning_rate * float(error.mean())
    return coefficients, intercept


def _validate_training_data(
    x: np.ndarray, y: np.ndarray, feature_names: tuple[str, ...]
) -> None:
    """`_validate_training_data`은(는) 입력 또는 현재 상태가 규칙을 만족하는지 검증합니다."""

    if x.ndim != 2 or x.shape[1] != len(feature_names) or len(x) != len(y):
        raise ValueError("training feature shape does not match the agent schema")
    if len(x) < 50:
        raise ValueError("at least 50 labeled rows are required")
    if not np.isfinite(x).all() or not np.isfinite(y).all():
        raise ValueError("training data contains non-finite values")
    if set(np.unique(y)) != {0.0, 1.0}:
        raise ValueError("labels must contain both binary classes 0 and 1")


def classification_metrics(
    probabilities: np.ndarray,
    labels: np.ndarray,
    *,
    threshold: float = 0.5,
) -> dict[str, float]:
    """검증 라벨과 확률에서 품질 게이트가 사용하는 분류 지표를 계산한다."""

    probabilities = np.asarray(probabilities, dtype=float)
    labels = np.asarray(labels, dtype=float)
    if probabilities.ndim != 1 or labels.ndim != 1 or len(probabilities) != len(labels):
        raise ValueError("probabilities and labels must be aligned one-dimensional arrays")
    if len(labels) == 0 or set(np.unique(labels)) != {0.0, 1.0}:
        raise ValueError("classification metrics require both binary classes")
    if not np.isfinite(probabilities).all() or not np.isfinite(labels).all():
        raise ValueError("classification metrics contain non-finite values")
    if not 0.0 < threshold < 1.0:
        raise ValueError("decision threshold must be between zero and one")
    predictions = probabilities >= threshold
    positive = labels == 1
    negative = ~positive
    true_positive_rate = float(np.mean(predictions[positive])) if positive.any() else 0.0
    true_negative_rate = float(np.mean(~predictions[negative])) if negative.any() else 0.0
    accuracy = float(np.mean(predictions == labels))
    positive_rate = float(np.mean(positive))
    baseline_accuracy = max(positive_rate, 1.0 - positive_rate)
    return {
        "accuracy": round(accuracy, 4),
        "baseline_accuracy": round(baseline_accuracy, 4),
        "baseline_improvement": round(accuracy - baseline_accuracy, 4),
        "balanced_accuracy": round((true_positive_rate + true_negative_rate) / 2, 4),
        "brier_score": round(float(np.mean((probabilities - labels) ** 2)), 4),
        "calibration_error": round(
            _expected_calibration_error(probabilities, labels), 4
        ),
        "roc_auc": round(_roc_auc(probabilities, labels), 4),
        "positive_rate": round(positive_rate, 4),
        "validation_samples": float(len(labels)),
        "decision_threshold": round(float(threshold), 4),
    }


def _record_prediction_horizon(metrics: dict[str, float], days: int) -> None:
    """서명되는 품질 지표에 실제 예측 거래일 수를 기록한다."""

    if not 1 <= days <= 252:
        raise ValueError("prediction horizon must be between 1 and 252 trading days")
    metrics["prediction_horizon_days"] = float(days)


def _expected_calibration_error(
    probabilities: np.ndarray, labels: np.ndarray, bins: int = 10
) -> float:
    """`_expected_calibration_error`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    if bins < 2:
        raise ValueError("calibration bins must be at least two")
    error = 0.0
    for index in range(bins):
        lower = index / bins
        upper = (index + 1) / bins
        selected = (
            (probabilities >= lower) & (probabilities <= upper)
            if index == bins - 1
            else (probabilities >= lower) & (probabilities < upper)
        )
        if not selected.any():
            continue
        observed = float(np.mean(labels[selected]))
        predicted = float(np.mean(probabilities[selected]))
        error += float(np.mean(selected)) * abs(observed - predicted)
    return error


def _roc_auc(probabilities: np.ndarray, labels: np.ndarray) -> float:
    """`_roc_auc`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    positive_count = int(np.sum(labels == 1))
    negative_count = int(np.sum(labels == 0))
    if positive_count == 0 or negative_count == 0:
        return 0.5
    order = np.argsort(probabilities, kind="stable")
    sorted_probabilities = probabilities[order]
    ranks = np.empty(len(probabilities), dtype=float)
    start = 0
    while start < len(probabilities):
        end = start + 1
        while (
            end < len(probabilities)
            and sorted_probabilities[end] == sorted_probabilities[start]
        ):
            end += 1
        ranks[order[start:end]] = (start + 1 + end) / 2.0
        start = end
    positive_rank_sum = float(np.sum(ranks[labels == 1]))
    return (
        positive_rank_sum - positive_count * (positive_count + 1) / 2
    ) / (positive_count * negative_count)


def _validation_split(rows: int, validation_start: int | None) -> int:
    """`_validation_split`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    split = int(rows * 0.8) if validation_start is None else validation_start
    if not 1 <= split < rows:
        raise ValueError("validation split must leave training and validation rows")
    return split


def _sigmoid(value):
    """`_sigmoid`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    return 1.0 / (1.0 + np.exp(-np.clip(value, -35, 35)))
