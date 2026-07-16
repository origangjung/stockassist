from sqlalchemy import select, update
from sqlalchemy.orm import Session, sessionmaker

from app.models.score import ScoreWeightModel
from app.repositories.contracts import ScoreWeightRepository
from app.score.engine import ScoreWeights


class SqlAlchemyScoreWeightRepository(ScoreWeightRepository):
    def __init__(self, sessions: sessionmaker[Session]):
        self._sessions = sessions

    def get_active(self) -> ScoreWeights:
        with self._sessions() as session:
            model = session.scalar(
                select(ScoreWeightModel).where(ScoreWeightModel.is_active.is_(True))
            )
            if model is None:
                raise LookupError("active score weight version does not exist")
            return ScoreWeights(
                model.version, {key: float(value) for key, value in model.weights.items()}
            )

    def save(self, weights: ScoreWeights, *, activate: bool = False) -> None:
        with self._sessions.begin() as session:
            if activate:
                session.execute(update(ScoreWeightModel).values(is_active=False))
            model = session.get(ScoreWeightModel, weights.version)
            if model is None:
                session.add(
                    ScoreWeightModel(
                        version=weights.version, weights=weights.weights, is_active=activate
                    )
                )
            else:
                model.weights = weights.weights
                model.is_active = activate or model.is_active
