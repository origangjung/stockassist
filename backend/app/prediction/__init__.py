from app.prediction.contracts import PredictionEngine
from app.prediction.lightweight import LightweightPredictionEngine
from app.prediction.artifacts import ModelArtifactStore


def build_prediction_engine(
    name: str,
    artifact_store: ModelArtifactStore | None = None,
) -> PredictionEngine:
    if name == "lightweight":
        return LightweightPredictionEngine()
    if name == "xgboost":
        try:
            from app.prediction.engine import XGBoostPredictionEngine
        except ModuleNotFoundError as exc:
            if exc.name in {"sklearn", "xgboost"}:
                raise RuntimeError(
                    "XGBoost prediction requires the optional 'ml' dependency extra"
                ) from exc
            raise
        return XGBoostPredictionEngine(artifact_store=artifact_store)
    raise ValueError(f"unsupported prediction engine: {name}")


def __getattr__(name: str):
    if name == "XGBoostPredictionEngine":
        from app.prediction.engine import XGBoostPredictionEngine

        return XGBoostPredictionEngine
    raise AttributeError(name)


__all__ = [
    "LightweightPredictionEngine",
    "PredictionEngine",
    "XGBoostPredictionEngine",
    "build_prediction_engine",
]
