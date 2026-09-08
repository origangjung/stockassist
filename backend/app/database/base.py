"""base 파일은 백엔드 도메인 기능을 담당한다."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """`Base` 관련 상태와 동작을 하나의 객체로 묶습니다."""

    pass
