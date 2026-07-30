from dataclasses import asdict
from datetime import UTC, date, datetime
from urllib.parse import parse_qs, urlsplit
from zoneinfo import ZoneInfo

from app.corporate_actions import (
    ADJUSTMENT_VERSION,
    AdjustmentResult,
    BacktestAdjustmentResult,
    CorporateActionAdjustmentUnavailableError,
    CorporateActionAdjustmentEngine,
    CorporateActionBacktestAdjustmentEngine,
    CorporateActionIngestionUnavailableError,
    CorporateActionProvider,
    CorporateActionRepository,
    CorporateActionSourceMetadata,
    CorporateActionSourceNotFoundError,
    UntrustedCorporateActionSourceError,
)
from app.corporate_actions.sources import SOURCE_CANDIDATES
from app.corporate_actions.candidate_contracts import CorporateActionCandidateProvider
from app.corporate_actions.reconciliation import CorporateActionRevisionReconciler
from app.corporate_actions.exchange_verification import (
    CorporateActionExchangeVerificationService,
)
from app.corporate_actions.approval_contracts import (
    CorporateActionApprovalConflictError,
    CorporateActionApprovalEvidence,
    CorporateActionApprovalRepository,
    CorporateActionApprovalUnavailableError,
)
from app.corporate_actions.contracts import CorporateActionRecord
from app.providers.contracts import Candle


class CorporateActionService:
    def __init__(
        self,
        repository: CorporateActionRepository | None,
        engine: CorporateActionAdjustmentEngine | None = None,
        backtest_engine: CorporateActionBacktestAdjustmentEngine | None = None,
    ) -> None:
        self._repository = repository
        self._engine = engine or CorporateActionAdjustmentEngine()
        self._backtest_engine = backtest_engine or CorporateActionBacktestAdjustmentEngine()

    def recent(
        self,
        *,
        limit: int,
        offset: int,
        symbol: str | None = None,
        as_of: datetime | None = None,
    ) -> dict[str, object]:
        point_in_time = as_of or datetime.now(UTC)
        self._require_aware(point_in_time)
        if self._repository is None:
            return {
                "persistence_status": "disabled",
                "items": [],
                "total": 0,
                "limit": limit,
                "offset": offset,
                "data_as_of": point_in_time,
                "adjustment_version": ADJUSTMENT_VERSION,
                "application_mode": "preview_only",
                "raw_candles_mutated": False,
            }
        items, total = self._repository.list_recent(
            limit=limit,
            offset=offset,
            symbol=symbol,
            as_of=point_in_time,
        )
        return {
            "persistence_status": "enabled",
            "items": [asdict(item) for item in items],
            "total": total,
            "limit": limit,
            "offset": offset,
            "data_as_of": point_in_time,
            "adjustment_version": ADJUSTMENT_VERSION,
            "application_mode": "preview_only",
            "raw_candles_mutated": False,
        }

    def adjusted_view(
        self,
        symbol: str,
        candles: list[Candle],
        *,
        as_of: datetime,
    ) -> AdjustmentResult:
        self._require_aware(as_of)
        actions = (
            self._repository.list_known(symbol, as_of=as_of) if self._repository is not None else []
        )
        return self._engine.adjust(
            candles,
            actions,
            as_of=as_of,
        )

    def backtest_view(
        self,
        symbol: str,
        candles: list[Candle],
        *,
        as_of: datetime,
    ) -> BacktestAdjustmentResult:
        self._require_aware(as_of)
        if self._repository is None:
            raise CorporateActionAdjustmentUnavailableError(
                "Corporate action persistence is required for backtest adjustment"
            )
        actions = self._repository.list_known(symbol, as_of=as_of)
        return self._backtest_engine.adjust(candles, actions, as_of=as_of)

    @staticmethod
    def _require_aware(value: datetime) -> None:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Corporate action as_of must be timezone-aware")


class CorporateActionIngestionService:
    """Bounded, explicit ingestion for independently verified action sources."""

    def __init__(
        self,
        repository: CorporateActionRepository | None,
        providers: list[CorporateActionProvider] | None = None,
        source_candidates: tuple[CorporateActionSourceMetadata, ...] = SOURCE_CANDIDATES,
    ) -> None:
        self._repository = repository
        self._source_candidates = source_candidates
        self._providers: dict[str, CorporateActionProvider] = {}
        for provider in providers or []:
            name = provider.metadata.name
            if name in self._providers:
                raise ValueError(f"Duplicate corporate action source: {name}")
            self._providers[name] = provider

    def status(self) -> dict[str, object]:
        sources = [
            asdict(provider.metadata)
            for provider in sorted(self._providers.values(), key=lambda item: item.metadata.name)
        ]
        verified = sum(item["trust_status"] == "verified" for item in sources)
        return {
            "persistence_status": "enabled" if self._repository is not None else "disabled",
            "ingestion_available": self._repository is not None and verified > 0,
            "sources": sources,
            "source_candidates": [
                asdict(candidate)
                for candidate in sorted(self._source_candidates, key=lambda item: item.name)
            ],
            "verified_source_count": verified,
            "automatic_ingestion": False,
            "consumer_adjustment_mode": "opt_in_disabled",
            "max_batch_records": 500,
        }

    def ingest(
        self,
        source: str,
        symbol: str,
        *,
        start: datetime,
        end: datetime,
        limit: int,
    ) -> dict[str, object]:
        self._require_aware(start)
        self._require_aware(end)
        if start > end:
            raise ValueError("Corporate action ingestion start must not be after end")
        if limit < 1 or limit > 500:
            raise ValueError("Corporate action ingestion limit must be between 1 and 500")
        if self._repository is None:
            raise CorporateActionIngestionUnavailableError(
                "Corporate action persistence is disabled"
            )
        provider = self._providers.get(source)
        if provider is None:
            raise CorporateActionSourceNotFoundError(f"Unknown corporate action source: {source}")
        if provider.metadata.trust_status != "verified":
            raise UntrustedCorporateActionSourceError(
                f"Corporate action source is not verified: {source}"
            )

        normalized_symbol = symbol.strip().upper()
        result = provider.fetch_actions(
            normalized_symbol,
            start=start,
            end=end,
            limit=limit,
        )
        self._require_aware(result.fetched_at)
        if result.source != source or result.symbol.upper() != normalized_symbol:
            raise ValueError("Corporate action provider returned mismatched provenance")
        if len(result.actions) > limit:
            raise ValueError("Corporate action provider exceeded the requested batch limit")
        actions = list(result.actions)
        for action in actions:
            if action.source != source or action.symbol.upper() != normalized_symbol:
                raise ValueError("Corporate action record has mismatched provenance")
            self._require_aware(action.effective_at)
            self._require_aware(action.known_at)
            if not start <= action.effective_at <= end:
                raise ValueError("Corporate action effective_at is outside the requested range")
            if action.known_at > result.fetched_at:
                raise ValueError("Corporate action known_at cannot be after fetched_at")
        created, unchanged = self._repository.save_batch(actions)
        return {
            "source": source,
            "symbol": normalized_symbol,
            "requested_start": start,
            "requested_end": end,
            "data_as_of": result.fetched_at,
            "fetched": len(actions),
            "created": created,
            "unchanged": unchanged,
            "atomic_batch": True,
            "consumer_adjustment_mode": "opt_in_disabled",
        }

    @staticmethod
    def _require_aware(value: datetime) -> None:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Corporate action ingestion timestamps must be timezone-aware")


class CorporateActionCandidateService:
    """Expose bounded source evidence without persisting or confirming revisions."""

    def __init__(
        self,
        providers: list[CorporateActionCandidateProvider],
        reconciler: CorporateActionRevisionReconciler | None = None,
    ) -> None:
        self._providers: dict[str, CorporateActionCandidateProvider] = {}
        self._reconciler = reconciler or CorporateActionRevisionReconciler()
        for provider in providers:
            name = provider.metadata.name
            if name in self._providers:
                raise ValueError(f"Duplicate corporate action candidate source: {name}")
            self._providers[name] = provider

    def status(self) -> dict[str, object]:
        return {
            "available": bool(self._providers),
            "sources": [
                asdict(provider.metadata)
                for provider in sorted(
                    self._providers.values(), key=lambda item: item.metadata.name
                )
            ],
            "read_only": True,
            "automatic_confirmation": False,
            "point_in_time_eligible": False,
            "max_range_days": 366,
            "max_candidates": 200,
        }

    def preview(
        self,
        source: str,
        symbol: str,
        *,
        start: date,
        end: date,
        limit: int,
    ) -> dict[str, object]:
        if start > end:
            raise ValueError("Corporate action candidate start must not be after end")
        if (end - start).days > 366:
            raise ValueError("Corporate action candidate range cannot exceed 366 days")
        if limit < 1 or limit > 200:
            raise ValueError("Corporate action candidate limit must be between 1 and 200")
        provider = self._providers.get(source)
        if provider is None:
            raise CorporateActionSourceNotFoundError(
                f"Unknown corporate action candidate source: {source}"
            )
        normalized_symbol = symbol.strip().upper()
        result = provider.fetch_candidates(
            normalized_symbol,
            start=start,
            end=end,
            limit=limit,
        )
        self._require_aware(result.fetched_at)
        if result.source != source or result.symbol.upper() != normalized_symbol:
            raise ValueError("Corporate action candidate provider returned mismatched provenance")
        if len(result.candidates) > limit:
            raise ValueError("Corporate action candidate provider exceeded the requested limit")
        for candidate in result.candidates:
            if candidate.source != source or candidate.symbol.upper() != normalized_symbol:
                raise ValueError("Corporate action candidate has mismatched provenance")
            if candidate.confirmation_ready:
                raise ValueError("Candidate preview cannot claim confirmation readiness")
        revision_groups = self._reconciler.propose(result.candidates)
        return {
            "source": source,
            "symbol": normalized_symbol,
            "requested_start": start,
            "requested_end": end,
            "data_as_of": result.fetched_at,
            "items": [asdict(candidate) for candidate in result.candidates],
            "revision_groups": [asdict(group) for group in revision_groups],
            "count": len(result.candidates),
            "read_only": True,
            "write_performed": False,
            "automatic_confirmation": False,
            "point_in_time_eligible": False,
        }

    def close(self) -> None:
        for provider in self._providers.values():
            provider.close()

    @staticmethod
    def _require_aware(value: datetime) -> None:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Corporate action candidate fetched_at must be timezone-aware")


class CorporateActionApprovalService:
    """Promote one re-fetched candidate after explicit, evidenced admin review."""

    CONFIRMATION = "CONFIRM_CORPORATE_ACTION"
    EXCHANGE_EVIDENCE_HOSTS = frozenset({"kind.krx.co.kr", "data.krx.co.kr", "global.krx.co.kr"})

    def __init__(
        self,
        repository: CorporateActionApprovalRepository | None,
        candidate_service: CorporateActionCandidateService,
        *,
        enabled: bool = False,
        exchange_verification: CorporateActionExchangeVerificationService | None = None,
        clock=None,
    ) -> None:
        self._repository = repository
        self._candidate_service = candidate_service
        self._enabled = enabled
        self._exchange_verification = (
            exchange_verification or CorporateActionExchangeVerificationService()
        )
        self._clock = clock or (lambda: datetime.now(UTC))

    def status(self) -> dict[str, object]:
        available = self._enabled and self._repository is not None
        return {
            "enabled": self._enabled,
            "available": available,
            "persistence_status": ("enabled" if self._repository is not None else "disabled"),
            "confirmation_phrase": self.CONFIRMATION,
            "candidate_refetch_required": True,
            "supported_sources": ["dart"],
            "exchange_evidence_required": True,
            "allowed_exchange_evidence_hosts": sorted(self.EXCHANGE_EVIDENCE_HOSTS),
            "known_at_policy": "approval_time",
            "bulk_approval": False,
            "automatic_execution": False,
            "raw_candles_mutated": False,
            "exchange_verification": self._exchange_verification.status(),
        }

    def approve(
        self,
        source: str,
        symbol: str,
        *,
        start: date,
        end: date,
        group_hint: str,
        receipt_no: str,
        effective_at: datetime,
        exchange_evidence_url: str,
        confirmation: str,
    ) -> dict[str, object]:
        if not self._enabled or self._repository is None:
            raise CorporateActionApprovalUnavailableError(
                "Corporate action manual approval is disabled"
            )
        if confirmation != self.CONFIRMATION:
            raise ValueError("Corporate action approval confirmation phrase is invalid")
        if source != "dart":
            raise ValueError("Manual corporate action approval currently supports DART only")
        self._require_aware(effective_at)
        self._validate_url(exchange_evidence_url, self.EXCHANGE_EVIDENCE_HOSTS)

        preview = self._candidate_service.preview(
            source,
            symbol,
            start=start,
            end=end,
            limit=200,
        )
        groups = preview["revision_groups"]
        group = next(
            (item for item in groups if item["group_hint"] == group_hint),
            None,
        )
        if group is None or receipt_no not in group["receipt_nos"]:
            raise CorporateActionApprovalConflictError(
                "Candidate revision group changed during approval; review it again"
            )
        candidate = next(
            (item for item in preview["items"] if item["receipt_no"] == receipt_no),
            None,
        )
        if candidate is None:
            raise CorporateActionApprovalConflictError(
                "Candidate receipt changed during approval; review it again"
            )
        price_factor = candidate["proposed_price_factor"]
        volume_factor = candidate["proposed_volume_factor"]
        if price_factor is None or volume_factor is None:
            raise ValueError("Candidate factors are incomplete and cannot be approved")
        filing_evidence_url = str(candidate["evidence_url"])
        self._validate_filing_url(filing_evidence_url, receipt_no)

        reviewed_at = self._clock()
        self._require_aware(reviewed_at)
        announced_at = datetime.combine(
            candidate["filed_on"],
            datetime.min.time(),
            tzinfo=ZoneInfo("Asia/Seoul"),
        )
        normalized_symbol = symbol.strip().upper()
        action = CorporateActionRecord(
            symbol=normalized_symbol,
            action_type=candidate["action_type"],
            event_id=f"reviewed:{group_hint.removeprefix('candidate:')}",
            revision=1,
            effective_at=effective_at,
            announced_at=announced_at,
            known_at=reviewed_at,
            price_factor=price_factor,
            volume_factor=volume_factor,
            status="confirmed",
            source=f"{source}-reviewed",
            rule_version="manual-review-2026.1",
        )
        evidence = CorporateActionApprovalEvidence(
            group_hint=group_hint,
            receipt_no=receipt_no,
            filing_evidence_url=filing_evidence_url,
            exchange_evidence_url=exchange_evidence_url,
            reviewed_by="admin-api",
            reviewed_at=reviewed_at,
        )
        result = self._repository.approve(action, evidence)
        return {
            "action": asdict(result.action),
            "evidence_hash": result.evidence_hash,
            "created": result.created,
            "candidate_refetched_at": preview["data_as_of"],
            "known_at_policy": "approval_time",
            "automatic_execution": False,
            "raw_candles_mutated": False,
        }

    @staticmethod
    def _require_aware(value: datetime) -> None:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Corporate action approval timestamps must be timezone-aware")

    @staticmethod
    def _validate_url(value: str, hosts: frozenset[str]) -> None:
        parsed = urlsplit(value)
        try:
            port = parsed.port
        except ValueError as exc:
            raise ValueError(
                "Corporate action evidence must use an approved HTTPS host"
            ) from exc
        if (
            parsed.scheme != "https"
            or parsed.hostname not in hosts
            or parsed.username is not None
            or parsed.password is not None
            or port not in (None, 443)
            or bool(parsed.fragment)
        ):
            raise ValueError("Corporate action evidence must use an approved HTTPS host")

    @classmethod
    def _validate_filing_url(cls, value: str, receipt_no: str) -> None:
        cls._validate_url(value, frozenset({"dart.fss.or.kr"}))
        parsed = urlsplit(value)
        if parse_qs(parsed.query).get("rcpNo") != [receipt_no]:
            raise ValueError("DART evidence URL does not match the selected receipt")
