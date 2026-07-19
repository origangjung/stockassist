from datetime import datetime
from typing import Protocol


class DataLifecycleRepository(Protocol):
    def count_before(self, cutoffs: dict[str, datetime]) -> dict[str, int]: ...

    def delete_before(self, cutoffs: dict[str, datetime]) -> dict[str, int]: ...
