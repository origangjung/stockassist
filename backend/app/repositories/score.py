"""score 파일은 데이터 저장과 조회 기능을 담당한다."""

from sqlalchemy import select, update
from sqlalchemy.orm import Session, sessionmaker

from app.models.score import ScoreWeightModel
from app.repositories.contracts import ScoreWeightRepository
from app.score.engine import ScoreWeights


class SqlAlchemyScoreWeightRepository(ScoreWeightRepository):
    """도메인 객체의 저장·조회 방식을 캡슐화하는 저장소입니다."""

    def __init__(self, sessions: sessionmaker[Session]):
        """`__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다."""

        self._sessions = sessions

    def get_active(self) -> ScoreWeights:
        """`get_active`은(는) 필요한 데이터를 조회해 반환합니다."""

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
        """`save`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

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
