"""financial_features 파일은 직접 학습 AI 특성과 실행 기능을 담당한다."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


FINANCIAL_FEATURES = (
    "revenue_growth_yoy",
    "net_income_growth_yoy",
    "net_margin",
    "debt_to_assets",
    "equity_to_assets",
    "asset_growth_yoy",
)

_CONCEPTS = {
    "revenue": (
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "Revenues",
        "SalesRevenueNet",
    ),
    "net_income": ("NetIncomeLoss", "ProfitLoss"),
    "assets": ("Assets",),
    "liabilities": ("Liabilities",),
    "equity": (
        "StockholdersEquity",
        "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
    ),
}

_ANNUAL_CONCEPTS = {
    "revenue": _CONCEPTS["revenue"],
    "net_income": _CONCEPTS["net_income"],
    "equity": _CONCEPTS["equity"],
}


@dataclass(frozen=True)
class FinancialSnapshot:
    """특정 시점에 관측된 데이터 상태를 변경 없이 전달하는 값 객체입니다."""

    filed: date
    fiscal_year: int
    fiscal_period: str
    accession: str
    revenue: float
    net_income: float
    assets: float
    liabilities: float
    equity: float


@dataclass(frozen=True)
class AnnualValuationSnapshot:
    """특정 10-K가 처음 공개된 시점에 사용 가능했던 연간 재무 값이다."""

    filed: date
    accession: str
    revenue: float
    net_income: float
    equity: float
    shares_outstanding: float | None


def latest_financial_features(companyfacts: dict) -> dict[str, float] | None:
    """`latest_financial_features`은(는) 필요한 데이터를 조회해 반환합니다."""

    rows = _feature_rows(extract_financial_snapshots(companyfacts))
    return rows[-1][1] if rows else None


def latest_annual_valuation_inputs(companyfacts: dict) -> dict[str, float | str]:
    """`latest_annual_valuation_inputs`은(는) 필요한 데이터를 조회해 반환합니다."""

    snapshots = extract_annual_valuation_snapshots(companyfacts)
    if not snapshots:
        raise ValueError("SEC Company Facts has no complete annual valuation period")
    latest = snapshots[-1]
    result: dict[str, float | str] = {
        "filed": latest.filed.isoformat(),
        "accession": latest.accession,
        "revenue": latest.revenue,
        "net_income": latest.net_income,
        "equity": latest.equity,
    }
    if latest.shares_outstanding is not None:
        result["shares_outstanding"] = latest.shares_outstanding
    return result


def extract_annual_valuation_snapshots(
    companyfacts: dict,
) -> list[AnnualValuationSnapshot]:
    """수정 공시의 미래 값 없이 최초 10-K별 밸류에이션 입력 이력을 복원한다."""

    facts = companyfacts.get("facts") or {}
    us_gaap = facts.get("us-gaap") or {}
    annual: dict[str, list[dict]] = {}
    for metric, concepts in _ANNUAL_CONCEPTS.items():
        annual[metric] = _first_available_unit_entries(us_gaap, concepts, "USD")

    candidates: list[dict[str, float | str]] = []
    for revenue in annual["revenue"]:
        if revenue.get("form") != "10-K" or not _is_annual_duration(revenue):
            continue
        accession = str(revenue.get("accn") or "")
        filed = str(revenue.get("filed") or "")[:10]
        if not accession or not filed:
            continue
        row: dict[str, float | str] = {
            "filed": filed,
            "accession": accession,
            "revenue": float(revenue["val"]),
        }
        for metric in ("net_income", "equity"):
            match = next(
                (
                    item
                    for item in annual[metric]
                    if item.get("form") == "10-K" and str(item.get("accn") or "") == accession
                ),
                None,
            )
            if match is not None:
                row[metric] = float(match["val"])
        if {"net_income", "equity"}.issubset(row):
            candidates.append(row)
    dei = facts.get("dei") or {}
    share_entries = _first_available_unit_entries(
        dei, ("EntityCommonStockSharesOutstanding",), "shares"
    )
    snapshots: list[AnnualValuationSnapshot] = []
    for candidate in sorted(candidates, key=lambda item: str(item["filed"])):
        filed = date.fromisoformat(str(candidate["filed"]))
        eligible_shares = [
            item
            for item in share_entries
            if str(item.get("filed") or "")[:10] <= filed.isoformat()
            and item.get("form") in {"10-K", "10-Q", "8-K"}
            and _positive_number(item.get("val"))
        ]
        share = (
            max(eligible_shares, key=lambda item: str(item.get("filed") or ""))
            if eligible_shares
            else None
        )
        snapshots.append(
            AnnualValuationSnapshot(
                filed=filed,
                accession=str(candidate["accession"]),
                revenue=float(candidate["revenue"]),
                net_income=float(candidate["net_income"]),
                equity=float(candidate["equity"]),
                shares_outstanding=float(share["val"]) if share else None,
            )
        )
    return snapshots


def build_financial_training_rows(companyfacts: dict) -> list[dict]:
    """`build_financial_training_rows`은(는) 입력 값과 설정을 결합해 새 결과 객체를 생성합니다."""

    feature_rows = _feature_rows(extract_financial_snapshots(companyfacts))
    rows: list[dict] = []
    for index in range(len(feature_rows) - 1):
        snapshot, features, quality = feature_rows[index]
        next_quality = feature_rows[index + 1][2]
        rows.append(
            {
                "timestamp": snapshot.filed.isoformat(),
                **features,
                "label": int(next_quality > quality),
            }
        )
    return rows


def extract_financial_snapshots(companyfacts: dict) -> list[FinancialSnapshot]:
    """`extract_financial_snapshots`은(는) 원시 입력을 해석하고 필요한 값을 정규화해 추출합니다."""

    facts = (companyfacts.get("facts") or {}).get("us-gaap") or {}
    values: dict[str, dict[str, float | str | int | date]] = {}
    for metric, candidates in _CONCEPTS.items():
        entries = _first_available_entries(facts, candidates)
        for entry in entries:
            if entry.get("form") != "10-Q" or not entry.get("accn"):
                continue
            if metric in {"revenue", "net_income"} and not _is_quarter_duration(entry):
                continue
            try:
                accession = str(entry["accn"])
                filed = date.fromisoformat(str(entry["filed"])[:10])
                fiscal_year = int(entry["fy"])
                fiscal_period = str(entry["fp"])
                value = float(entry["val"])
            except (KeyError, TypeError, ValueError):
                continue
            if fiscal_period not in {"Q1", "Q2", "Q3"}:
                continue
            row = values.setdefault(
                accession,
                {
                    "filed": filed,
                    "fiscal_year": fiscal_year,
                    "fiscal_period": fiscal_period,
                    "accession": accession,
                },
            )
            row.setdefault(metric, value)

    snapshots = []
    required = {
        "revenue",
        "net_income",
        "assets",
        "filed",
        "fiscal_year",
        "fiscal_period",
        "accession",
    }
    for row in values.values():
        if not required.issubset(row) or float(row["assets"]) <= 0:
            continue
        if "liabilities" not in row and "equity" in row:
            row["liabilities"] = float(row["assets"]) - float(row["equity"])
        if "equity" not in row and "liabilities" in row:
            row["equity"] = float(row["assets"]) - float(row["liabilities"])
        if "liabilities" not in row or "equity" not in row:
            continue
        snapshots.append(FinancialSnapshot(**row))
    earliest: dict[tuple[int, str], FinancialSnapshot] = {}
    for snapshot in sorted(snapshots, key=lambda item: item.filed):
        earliest.setdefault((snapshot.fiscal_year, snapshot.fiscal_period), snapshot)
    return sorted(earliest.values(), key=lambda item: item.filed)


def _feature_rows(
    snapshots: list[FinancialSnapshot],
) -> list[tuple[FinancialSnapshot, dict[str, float], float]]:
    """`_feature_rows`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    by_period = {(item.fiscal_year, item.fiscal_period): item for item in snapshots}
    rows = []
    for snapshot in snapshots:
        previous = by_period.get((snapshot.fiscal_year - 1, snapshot.fiscal_period))
        if previous is None or previous.revenue == 0 or previous.assets == 0:
            continue
        features = {
            "revenue_growth_yoy": snapshot.revenue / previous.revenue - 1,
            "net_income_growth_yoy": (snapshot.net_income - previous.net_income)
            / max(abs(previous.net_income), 1.0),
            "net_margin": snapshot.net_income / max(abs(snapshot.revenue), 1.0),
            "debt_to_assets": snapshot.liabilities / snapshot.assets,
            "equity_to_assets": snapshot.equity / snapshot.assets,
            "asset_growth_yoy": snapshot.assets / previous.assets - 1,
        }
        rows.append((snapshot, features, _quality(features)))
    return rows


def _first_available_entries(facts: dict, candidates: tuple[str, ...]) -> list[dict]:
    """`_first_available_entries`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    return _first_available_unit_entries(facts, candidates, "USD")


def _first_available_unit_entries(
    facts: dict, candidates: tuple[str, ...], unit: str
) -> list[dict]:
    """`_first_available_unit_entries`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    for concept in candidates:
        units = ((facts.get(concept) or {}).get("units") or {}).get(unit)
        if isinstance(units, list) and units:
            return units
    return []


def _is_quarter_duration(entry: dict) -> bool:
    """`_is_quarter_duration`은(는) 입력 또는 현재 상태가 규칙을 만족하는지 검증합니다."""

    try:
        start = date.fromisoformat(str(entry["start"])[:10])
        end = date.fromisoformat(str(entry["end"])[:10])
    except (KeyError, TypeError, ValueError):
        return False
    return 70 <= (end - start).days <= 110


def _is_annual_duration(entry: dict) -> bool:
    """`_is_annual_duration`은(는) 입력 또는 현재 상태가 규칙을 만족하는지 검증합니다."""

    try:
        start = date.fromisoformat(str(entry["start"])[:10])
        end = date.fromisoformat(str(entry["end"])[:10])
    except (KeyError, TypeError, ValueError):
        return False
    return 300 <= (end - start).days <= 400


def _quality(features: dict[str, float]) -> float:
    """`_quality`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    return (
        0.30 * _clip(features["revenue_growth_yoy"], -1.0, 1.0)
        + 0.25 * _clip(features["net_income_growth_yoy"], -2.0, 2.0) / 2
        + 0.20 * _clip(features["net_margin"], -1.0, 1.0)
        + 0.15 * _clip(features["equity_to_assets"], -1.0, 1.0)
        - 0.10 * _clip(features["debt_to_assets"], 0.0, 2.0) / 2
    )


def _clip(value: float, low: float, high: float) -> float:
    """`_clip`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    return min(max(value, low), high)


def _positive_number(value: object) -> bool:
    """`_positive_number`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    try:
        return float(value) > 0
    except (TypeError, ValueError):
        return False
