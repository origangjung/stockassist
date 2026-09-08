"""contracts 파일은 백엔드 도메인 기능을 담당한다."""

from abc import ABC, abstractmethod


class AIReportGenerator(ABC):
    """Turns already computed facts into explanatory report language only."""

    name: str
    model: str

    @abstractmethod
    def generate(self, facts: dict) -> dict: ...

    def close(self) -> None:
        """Release external client resources when the application stops."""
