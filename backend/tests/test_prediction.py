from app.prediction.features import build_feature_dataset
from app.prediction.lightweight import LightweightPredictionEngine
from app.prediction.validation import PurgedWalkForwardSplit
from app.providers.mock import MockProvider


def test_lightweight_prediction_engine_runs_without_model_training():
    candles = MockProvider().get_candles("005930", 60)

    result = LightweightPredictionEngine().predict("005930", candles, horizon_days=5)

    assert 0 <= result.rise_probability <= 1
    assert result.model_version.startswith("light-")
    assert result.validation_status == "experimental"
    assert result.validation_metrics["folds"] == 0


def test_feature_rows_do_not_use_future_prices():
    candles = MockProvider().get_candles("005930", 100)
    dataset = build_feature_dataset(candles, horizon_days=5)
    altered = [*candles]
    altered[-1] = altered[-1].__class__(
        altered[-1].timestamp,
        altered[-1].open,
        altered[-1].high,
        altered[-1].low,
        altered[-1].close * 2,
        altered[-1].volume,
    )
    altered_dataset = build_feature_dataset(altered, horizon_days=5)

    assert (dataset.features[:-1] == altered_dataset.features[:-1]).all()
    assert (dataset.labels[:-1] == altered_dataset.labels[:-1]).all()
    assert not (dataset.prediction_features == altered_dataset.prediction_features).all()


def test_purged_walk_forward_keeps_label_horizon_out_of_train_set():
    splits = list(PurgedWalkForwardSplit(horizon_days=5, min_train_size=40, n_splits=3).split(120))

    assert len(splits) == 3
    for train, test in splits:
        assert train.max() + 5 < test.min()
