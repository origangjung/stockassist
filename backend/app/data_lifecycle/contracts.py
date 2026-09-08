"""contracts 파일은 백엔드 도메인 기능을 담당한다."""

from datetime import datetime
from typing import Protocol


class DataLifecycleRepository(Protocol):
    """`DataLifecycleRepository` 구현체가 제공해야 하는 메서드 계약을 정의합니다."""

    def count_before(self, cutoffs: dict[str, datetime]) -> dict[str, int]: ...

    def delete_before(self, cutoffs: dict[str, datetime]) -> dict[str, int]: ...
