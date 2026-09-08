"""전문 AI별 예측 기간 정책과 모델 메타데이터를 검증한다."""

import numpy as np
import pytest

from app.local_ai.horizons import HORIZON_POLICIES, target_name, validate_horizon
from app.local_ai.model import LocalLogisticModel


def test_agent_horizons_match_each_specialist_role() -> None:
    """재무·뉴스·수급은 더 이상 모두 5일 기본값을 공유하지 않는다."""

    assert HORIZON_POLICIES["technical"].primary_days == 10
    assert HORIZON_POLICIES["financial"].primary_days == 20
    assert HORIZON_POLICIES["news"].primary_days == 3
    assert HORIZON_POLICIES["investor_flow"].primary_days == 10
    assert HORIZON_POLICIES["risk"].primary_days == 5
    assert target_name("financial", 20) == "fundamental_repricing_20d"
    with pytest.raises(ValueError, match="horizon"):
        validate_horizon("news", 20)


def test_trained_model_signs_prediction_horizon_into_metrics() -> None:
    """학습 artifact의 기간은 체크섬 대상 품질 메타데이터에 포함돼야 한다."""

    values = np.linspace(-2.0, 2.0, 100).reshape(-1, 1)
    labels = np.asarray([index % 2 for index in range(100)], dtype=np.int8)

    model = LocalLogisticModel.train_sklearn(
        "financial",
        ("feature",),
        values,
        labels,
        prediction_horizon_days=20,
    )

    assert model.artifact.metrics["prediction_horizon_days"] == 20.0
