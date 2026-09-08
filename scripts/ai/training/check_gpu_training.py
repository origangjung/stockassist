"""Verify that XGBoost performs a small training job on the CUDA device."""

import json

import numpy as np
from xgboost import XGBClassifier


def main() -> int:
    """`main`은(는) 명령행 인자를 해석하고 이 스크립트의 전체 작업 순서를 실행합니다."""

    rng = np.random.default_rng(42)
    features = rng.normal(size=(4096, 16)).astype(np.float32)
    labels = (features[:, 0] + features[:, 1] * 0.5 > 0).astype(np.int8)
    model = XGBClassifier(
        n_estimators=24,
        max_depth=4,
        learning_rate=0.1,
        tree_method="hist",
        device="cuda",
        random_state=42,
        n_jobs=1,
    )
    model.fit(features, labels)
    config = json.loads(model.get_booster().save_config())
    device = config["learner"]["generic_param"]["device"]
    if not str(device).startswith("cuda"):
        raise RuntimeError("XGBoost did not select a CUDA device")
    print(f"gpu_training=ok device={device} rows={len(features)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
