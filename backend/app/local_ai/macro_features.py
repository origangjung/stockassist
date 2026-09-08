"""macro_features 파일은 직접 학습 AI 특성과 실행 기능을 담당한다."""

from __future__ import annotations

from bisect import bisect_right
from datetime import date


MACRO_FEATURES = (
    "vix_level",
    "treasury_10y",
    "yield_curve_10y_2y",
    "fed_funds_rate",
    "broad_dollar_change_20d",
)

FRED_SERIES = {
    "vix_level": "VIXCLS",
    "treasury_10y": "DGS10",
    "treasury_2y": "DGS2",
    "fed_funds_rate": "DFF",
    "broad_dollar": "DTWEXBGS",
}


def build_macro_features(observations: dict[str, list[tuple[date, float]]]) -> dict[date, dict[str, float]]:
    """Align released observations without looking ahead to a future date."""
    normalized = {
        name: sorted(values, key=lambda item: item[0])
        for name, values in observations.items()
    }
    all_dates = sorted({day for values in normalized.values() for day, _ in values})
    return {
        day: values
        for day in all_dates
        if (values := macro_features_at(normalized, day)) is not None
    }


def macro_features_at(
    observations: dict[str, list[tuple[date, float]]], as_of: date
) -> dict[str, float] | None:
    """`macro_features_at`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    current = {name: _latest(values, as_of) for name, values in observations.items()}
    if any(current.get(name) is None for name in FRED_SERIES):
        return None
    dollar_values = observations["broad_dollar"]
    dollar_index = bisect_right([item[0] for item in dollar_values], as_of) - 1
    if dollar_index < 20:
        return None
    dollar_now = dollar_values[dollar_index][1]
    dollar_previous = dollar_values[dollar_index - 20][1]
    if dollar_previous == 0:
        return None
    return {
        "vix_level": float(current["vix_level"]) / 100.0,
        "treasury_10y": float(current["treasury_10y"]) / 100.0,
        "yield_curve_10y_2y": (
            float(current["treasury_10y"]) - float(current["treasury_2y"])
        )
        / 100.0,
        "fed_funds_rate": float(current["fed_funds_rate"]) / 100.0,
        "broad_dollar_change_20d": dollar_now / dollar_previous - 1.0,
    }


def _latest(values: list[tuple[date, float]], as_of: date) -> float | None:
    """`_latest`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    if not values:
        return None
    index = bisect_right([item[0] for item in values], as_of) - 1
    return values[index][1] if index >= 0 else None
