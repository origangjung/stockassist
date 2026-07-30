from dataclasses import asdict

from app.repositories.contracts import CandleRepository


class CandlePriceBasisInventoryService:
    """Read-only evidence inventory for safe candle price-basis classification."""

    def __init__(self, repository: CandleRepository | None) -> None:
        self._repository = repository

    def summarize(
        self,
        *,
        symbol: str,
        limit: int = 200,
    ) -> dict[str, object]:
        if self._repository is None:
            return {
                "persistence_status": "disabled",
                "symbol": symbol,
                "items": [],
                "total_candles": 0,
                "unknown_candles": 0,
                "legacy_unknown_candles": 0,
                "legacy_rule_candles": 0,
                "total_groups": 0,
                "review_ready_groups": 0,
                "blocked_review_groups": 0,
                "groups_truncated": False,
                "automatic_relabel": False,
                "mutation_performed": False,
            }
        inventory = self._repository.price_basis_inventory(symbol=symbol, limit=limit)
        blockers = []
        if inventory.unknown_candles:
            blockers.append("unknown_price_basis_requires_source_specific_evidence")
        if inventory.legacy_unknown_candles:
            blockers.append("legacy_rows_lack_provider_provenance")
        if inventory.legacy_rule_candles:
            blockers.append("legacy_rows_lack_price_basis_rule_version")
        items = [self._review_item(asdict(row)) for row in inventory.rows]
        review_ready_groups = sum(item["review_status"] == "evidence_recorded" for item in items)
        return {
            "persistence_status": "enabled",
            "symbol": symbol,
            "items": items,
            "total_candles": inventory.total_candles,
            "unknown_candles": inventory.unknown_candles,
            "legacy_unknown_candles": inventory.legacy_unknown_candles,
            "legacy_rule_candles": inventory.legacy_rule_candles,
            "total_groups": inventory.total_groups,
            "review_ready_groups": review_ready_groups,
            "blocked_review_groups": len(items) - review_ready_groups,
            "groups_truncated": inventory.total_groups > len(inventory.rows),
            "classification_blockers": blockers,
            "automatic_relabel": False,
            "mutation_performed": False,
        }

    @staticmethod
    def _review_item(item: dict[str, object]) -> dict[str, object]:
        requirements = []
        if item["source_provider"] == "legacy_unknown":
            requirements.extend(
                ["original_provider_identifier", "provider_response_or_contract_reference"]
            )
        if item["price_basis"] == "unknown":
            requirements.extend(["endpoint_adjustment_semantics", "provider_contract_test"])
        if item["price_basis_rule_version"] == "legacy_unknown":
            requirements.append("versioned_price_basis_rule")
        return {
            **item,
            "review_status": "evidence_required" if requirements else "evidence_recorded",
            "required_evidence": list(dict.fromkeys(requirements)),
        }
