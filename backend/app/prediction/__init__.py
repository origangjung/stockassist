"""backend.app.prediction 패키지의 공개 구성 요소를 묶는다."""

from app.prediction.contracts import PredictionEngine
from app.prediction.lightweight import LightweightPredictionEngine
from app.prediction.artifacts import ModelArtifactStore


def build_prediction_engine(
    name: str,
    artifact_store: ModelArtifactStore | None = None,
) -> PredictionEngine:
    """`build_prediction_engine`은(는) 입력 값과 설정을 결합해 새 결과 객체를 생성합니다."""

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
    """`__getattr__`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

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
