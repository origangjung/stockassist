"""score 파일은 데이터베이스 영속 모델 기능을 담당한다."""

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class ScoreWeightModel(Base):
    """데이터베이스에 저장되는 필드와 관계를 정의하는 ORM 모델입니다."""

    __tablename__ = "score_weights"

    version: Mapped[str] = mapped_column(String(40), primary_key=True)
    weights: Mapped[dict] = mapped_column(JSON, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
