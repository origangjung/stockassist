from collections.abc import Iterator

import numpy as np


class PurgedWalkForwardSplit:
    """Expanding-window chronological split with a label-horizon purge gap."""

    def __init__(self, *, horizon_days: int, min_train_size: int = 60, n_splits: int = 3) -> None:
        self.horizon_days = horizon_days
        self.min_train_size = min_train_size
        self.n_splits = n_splits

    def split(self, sample_count: int) -> Iterator[tuple[np.ndarray, np.ndarray]]:
        test_size = max(
            10, (sample_count - self.min_train_size - self.horizon_days) // self.n_splits
        )
        test_start = self.min_train_size + self.horizon_days
        yielded = 0
        while test_start < sample_count and yielded < self.n_splits:
            test_end = min(sample_count, test_start + test_size)
            train_end = test_start - self.horizon_days
            if train_end >= self.min_train_size and test_end > test_start:
                yield np.arange(train_end), np.arange(test_start, test_end)
                yielded += 1
            test_start = test_end
