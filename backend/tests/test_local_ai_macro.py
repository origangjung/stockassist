from datetime import date

import pytest

from app.local_ai.macro_features import macro_features_at
from scripts.ai.data.enrich_local_ai_macro import safe_data_dir


def test_macro_features_use_latest_observation_without_lookahead():
    days = [date(2026, 1, day) for day in range(1, 23)]
    observations = {
        "vix_level": [(date(2026, 1, 1), 20.0), (date(2026, 1, 22), 40.0)],
        "treasury_10y": [(date(2026, 1, 1), 4.5)],
        "treasury_2y": [(date(2026, 1, 1), 4.0)],
        "fed_funds_rate": [(date(2026, 1, 1), 3.5)],
        "broad_dollar": list(zip(days, range(100, 122), strict=True)),
    }

    values = macro_features_at(observations, date(2026, 1, 21))

    assert values is not None
    assert values["vix_level"] == 0.2
    assert values["yield_curve_10y_2y"] == 0.005
    assert values["broad_dollar_change_20d"] == pytest.approx(0.2)


def test_macro_enrichment_paths_stay_inside_datasets(tmp_path, monkeypatch):
    """예약 거시 결합기는 datasets 밖의 경로를 읽거나 쓰지 않아야 한다."""

    root = (tmp_path / "datasets").resolve()
    source = root / "market"
    source.mkdir(parents=True)
    monkeypatch.setattr("scripts.ai.data.enrich_local_ai_macro.DATASET_ROOT", root)

    assert safe_data_dir(source, must_exist=True) == source
    with pytest.raises(ValueError, match="below datasets"):
        safe_data_dir(tmp_path / "outside", must_exist=False)
