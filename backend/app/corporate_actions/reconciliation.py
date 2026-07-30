import re
from dataclasses import dataclass
from datetime import date
from hashlib import sha256

from app.corporate_actions.candidate_contracts import CorporateActionCandidate


@dataclass(frozen=True)
class CorporateActionRevisionGroup:
    group_hint: str
    source: str
    symbol: str
    action_type: str
    anchor_date: date | None
    receipt_nos: tuple[str, ...]
    suggested_revisions: tuple[int, ...]
    confidence: str
    reasons: tuple[str, ...]
    requires_manual_confirmation: bool = True
    persistence_allowed: bool = False


class CorporateActionRevisionReconciler:
    """Suggest revision families without asserting an upstream relationship."""

    def propose(
        self,
        candidates: tuple[CorporateActionCandidate, ...],
    ) -> tuple[CorporateActionRevisionGroup, ...]:
        buckets: dict[
            tuple[str, str, str, str, date | None],
            list[CorporateActionCandidate],
        ] = {}
        for candidate in candidates:
            normalized_name = self._report_name(candidate.report_name)
            anchor_date = candidate.decision_date or candidate.record_date
            discriminator = normalized_name or candidate.receipt_no
            key = (
                candidate.source,
                candidate.symbol,
                candidate.action_type,
                discriminator,
                anchor_date,
            )
            buckets.setdefault(key, []).append(candidate)

        groups = []
        for key, items in buckets.items():
            ordered = sorted(items, key=lambda item: (item.filed_on, item.receipt_no))
            confidence, reasons = self._confidence(ordered)
            digest = sha256("|".join(map(str, key)).encode()).hexdigest()[:20]
            groups.append(
                CorporateActionRevisionGroup(
                    group_hint=f"candidate:{digest}",
                    source=key[0],
                    symbol=key[1],
                    action_type=key[2],
                    anchor_date=key[4],
                    receipt_nos=tuple(item.receipt_no for item in ordered),
                    suggested_revisions=tuple(range(1, len(ordered) + 1)),
                    confidence=confidence,
                    reasons=reasons,
                )
            )
        return tuple(sorted(groups, key=lambda item: item.group_hint))

    @staticmethod
    def _confidence(
        items: list[CorporateActionCandidate],
    ) -> tuple[str, tuple[str, ...]]:
        if len(items) == 1:
            return "isolated", ("no_matching_receipt",)
        reasons = ["same_normalized_report_and_anchor"]
        if any(item.superseded_hint for item in items):
            reasons.append("original_reports_later_correction")
        if any(item.correction_hint for item in items):
            reasons.append("correction_title_detected")
        confidence = (
            "likely_correction"
            if len(reasons) == 3
            else "ambiguous_multiple_receipts"
        )
        return confidence, tuple(reasons)

    @staticmethod
    def _report_name(value: str | None) -> str:
        if not value:
            return ""
        normalized = re.sub(r"^\s*(?:\[[^\]]*정정[^\]]*\]\s*)+", "", value)
        return re.sub(r"\s+", "", normalized).casefold()
