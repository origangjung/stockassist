from app.local_ai.financial_features import (
    FINANCIAL_FEATURES,
    build_financial_training_rows,
    extract_annual_valuation_snapshots,
    latest_annual_valuation_inputs,
    latest_financial_features,
)


def _entry(*, accn, filed, fy, fp, value, start=None, end):
    row = {
        "accn": accn,
        "filed": filed,
        "fy": fy,
        "fp": fp,
        "form": "10-Q",
        "end": end,
        "val": value,
    }
    if start:
        row["start"] = start
    return row


def _companyfacts():
    periods = [
        ("a1", "2024-05-01", 2024, "Q1", "2024-01-01", "2024-03-31", 100, 10, 500, 200, 300),
        ("a2", "2025-05-01", 2025, "Q1", "2025-01-01", "2025-03-31", 120, 15, 550, 210, 340),
        ("a3", "2025-08-01", 2025, "Q2", "2025-04-01", "2025-06-30", 130, 18, 570, 215, 355),
        ("a4", "2026-05-01", 2026, "Q1", "2026-01-01", "2026-03-31", 145, 22, 600, 220, 380),
        ("a5", "2026-08-01", 2026, "Q2", "2026-04-01", "2026-06-30", 160, 25, 630, 225, 405),
    ]
    concepts = {
        "RevenueFromContractWithCustomerExcludingAssessedTax": [],
        "NetIncomeLoss": [],
        "Assets": [],
        "Liabilities": [],
        "StockholdersEquity": [],
    }
    for accn, filed, fy, fp, start, end, revenue, income, assets, debt, equity in periods:
        common = {"accn": accn, "filed": filed, "fy": fy, "fp": fp, "end": end}
        concepts["RevenueFromContractWithCustomerExcludingAssessedTax"].append(
            _entry(**common, start=start, value=revenue)
        )
        concepts["NetIncomeLoss"].append(_entry(**common, start=start, value=income))
        concepts["Assets"].append(_entry(**common, value=assets))
        concepts["Liabilities"].append(_entry(**common, value=debt))
        concepts["StockholdersEquity"].append(_entry(**common, value=equity))
    return {
        "facts": {
            "us-gaap": {
                name: {"units": {"USD": entries}} for name, entries in concepts.items()
            }
        }
    }


def test_financial_features_use_prior_year_comparisons():
    features = latest_financial_features(_companyfacts())

    assert features is not None
    assert set(features) == set(FINANCIAL_FEATURES)
    assert features["revenue_growth_yoy"] == 160 / 130 - 1
    assert features["debt_to_assets"] == 225 / 630


def test_financial_training_labels_compare_to_next_filing():
    rows = build_financial_training_rows(_companyfacts())

    assert len(rows) == 2
    assert [row["timestamp"] for row in rows] == ["2025-05-01", "2026-05-01"]
    assert all(row["label"] in {0, 1} for row in rows)


def test_annual_valuation_inputs_join_same_filing_and_prior_share_count():
    companyfacts = {
        "facts": {
            "us-gaap": {
                "RevenueFromContractWithCustomerExcludingAssessedTax": {
                    "units": {
                        "USD": [
                            {
                                "accn": "annual-1",
                                "filed": "2025-02-01",
                                "form": "10-K",
                                "start": "2024-01-01",
                                "end": "2024-12-31",
                                "val": 1_000,
                            }
                        ]
                    }
                },
                "NetIncomeLoss": {
                    "units": {
                        "USD": [
                            {
                                "accn": "annual-1",
                                "filed": "2025-02-01",
                                "form": "10-K",
                                "val": 100,
                            }
                        ]
                    }
                },
                "StockholdersEquity": {
                    "units": {
                        "USD": [
                            {
                                "accn": "annual-1",
                                "filed": "2025-02-01",
                                "form": "10-K",
                                "val": 500,
                            }
                        ]
                    }
                },
            },
            "dei": {
                "EntityCommonStockSharesOutstanding": {
                    "units": {
                        "shares": [
                            {"filed": "2025-01-15", "form": "10-Q", "val": 10},
                            {"filed": "2025-03-01", "form": "10-Q", "val": 99},
                        ]
                    }
                }
            },
        }
    }

    result = latest_annual_valuation_inputs(companyfacts)

    assert result["accession"] == "annual-1"
    assert result["revenue"] == 1_000
    assert result["net_income"] == 100
    assert result["equity"] == 500
    assert result["shares_outstanding"] == 10


def test_annual_valuation_history_never_uses_a_future_share_count():
    companyfacts = {
        "facts": {
            "us-gaap": {
                name: {
                    "units": {
                        "USD": [
                            {
                                "accn": accession,
                                "filed": filed,
                                "form": "10-K",
                                "start": f"{year}-01-01",
                                "end": f"{year}-12-31",
                                "val": value,
                            }
                            for accession, filed, year, value in (
                                ("annual-1", "2024-02-01", 2023, first),
                                ("annual-2", "2025-02-01", 2024, second),
                            )
                        ]
                    }
                }
                for name, first, second in (
                    ("RevenueFromContractWithCustomerExcludingAssessedTax", 1000, 1200),
                    ("NetIncomeLoss", 100, 130),
                    ("StockholdersEquity", 500, 560),
                )
            },
            "dei": {
                "EntityCommonStockSharesOutstanding": {
                    "units": {
                        "shares": [
                            {"filed": "2024-01-15", "form": "10-Q", "val": 10},
                            {"filed": "2024-03-01", "form": "10-Q", "val": 11},
                            {"filed": "2025-01-15", "form": "10-Q", "val": 12},
                        ]
                    }
                }
            },
        }
    }

    snapshots = extract_annual_valuation_snapshots(companyfacts)

    assert [item.accession for item in snapshots] == ["annual-1", "annual-2"]
    assert [item.shares_outstanding for item in snapshots] == [10, 12]
