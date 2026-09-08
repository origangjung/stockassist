"""로컬 전문 AI 5개와 최종 진단을 실행하는 런타임이다.

서명된 JSON 모델을 읽고 당시 시점 기준 외부 특성을 선택적으로 결합하며, 품질 기준을
통과하지 못한 모델은 제외한다. 결과에는 사용 가능 상태를 명시하며 외부 LLM은 호출하지 않는다.
"""

from pathlib import Path
from typing import Callable

from app.local_ai.contracts import AgentName, LocalAgentResult, LocalSynthesisResult, ModelName
from app.local_ai.diagnostic import (
    RULE_SYNTHESIS_VERSION,
    SIGNAL_BANDS,
    calculate_diagnostic,
    directional_signal as _directional_signal,
    load_diagnostic_policy,
)
from app.local_ai.etf import etf_asset_class_features, is_etf
from app.local_ai.features import (
    ETF_MODEL_FEATURES,
    FEATURES,
    TARGETS,
    extract_features,
)
from app.local_ai.model import LocalLogisticModel
from app.local_ai.quality import assess_model_quality, quality_evidence
from app.local_ai.horizons import target_name


AGENTS: tuple[AgentName, ...] = (
    "technical",
    "financial",
    "news",
    "investor_flow",
    "risk",
)

class LocalAnalysisRuntime:
    """외부 AI API 없이 직접 학습한 전문 모델을 실행하고 최종 진단을 조합한다."""

    def __init__(
        self,
        artifact_dir: str | Path,
        flow_feature_loader: Callable[[str], dict[str, float] | None] | None = None,
        financial_feature_loader: Callable[[str], dict[str, float] | None] | None = None,
        news_feature_loader: Callable[[str], dict[str, float] | None] | None = None,
        macro_feature_loader: Callable[[], dict[str, float] | None] | None = None,
    ) -> None:
        """모델 경로와 전문 AI별 최신 특성 공급 함수를 등록한다."""

        self._artifact_dir = Path(artifact_dir).expanduser().resolve()
        self._flow_feature_loader = flow_feature_loader
        self._financial_feature_loader = financial_feature_loader
        self._news_feature_loader = news_feature_loader
        self._macro_feature_loader = macro_feature_loader

    def analyze(self, facts: dict, *, symbol: str | None = None) -> dict[str, dict]:
        """종목 facts를 전문 AI 5개에 전달하고 각 모델의 상태와 진단 결과를 반환한다."""

        etf_scope = bool(symbol and is_etf(symbol, facts.get("stock")))
        if symbol and self._flow_feature_loader and (self._artifact_dir / "investor_flow.json").is_file():
            try:
                facts["local_flow_features"] = self._flow_feature_loader(symbol)
            except Exception:
                facts["local_flow_features"] = None
        if (
            symbol
            and not etf_scope
            and self._financial_feature_loader
            and (self._artifact_dir / "financial.json").is_file()
        ):
            try:
                facts["local_financial_features"] = self._financial_feature_loader(symbol)
            except Exception:
                facts["local_financial_features"] = None
        if symbol and self._news_feature_loader and (self._artifact_dir / "news.json").is_file():
            try:
                facts["local_news_features"] = self._news_feature_loader(symbol)
            except Exception:
                facts["local_news_features"] = None
        risk_artifact = "etf_risk.json" if etf_scope else "risk.json"
        if self._macro_feature_loader and (self._artifact_dir / risk_artifact).is_file():
            try:
                facts["local_macro_features"] = self._macro_feature_loader()
            except Exception:
                facts["local_macro_features"] = None
        return {
            agent: self._analyze_one(
                agent, facts, etf_scope=etf_scope, symbol=symbol
            ).to_dict()
            for agent in AGENTS
        }

    def synthesize(
        self,
        results: dict[str, dict],
        *,
        symbol: str | None = None,
        stock: dict | None = None,
        macro_features: dict[str, float] | None = None,
    ) -> dict:
        """품질 승인된 전문 AI만 골라 신뢰도 가중 최종 진단을 생성한다."""

        etf_scope = bool(symbol and is_etf(symbol, stock))
        if etf_scope:
            specialist_names = ("technical", "risk")
            policy = None
        else:
            try:
                policy = load_diagnostic_policy(
                    self._artifact_dir / "diagnostic-policy.json"
                )
            except (OSError, ValueError) as exc:
                return LocalSynthesisResult(
                    "quality_rejected",
                    "multi_factor_diagnostic",
                    None,
                    None,
                    None,
                    RULE_SYNTHESIS_VERSION,
                    0,
                    None,
                    [str(exc)],
                ).to_dict()
            specialist_names = policy.specialists
        available = {
            name: results[name]
            for name in specialist_names
            if (results.get(name) or {}).get("status") == "available"
        }
        required_specialists = 2
        if policy is not None and not policy.approved:
            return LocalSynthesisResult(
                "quality_rejected",
                "multi_factor_diagnostic",
                None,
                None,
                None,
                RULE_SYNTHESIS_VERSION,
                len(available),
                None,
                [
                    "diagnostic_validation_failed "
                    f"accuracy={policy.metrics.get('accuracy', 0.0):.4f} "
                    f"balanced_accuracy={policy.metrics.get('balanced_accuracy', 0.0):.4f} "
                    f"baseline_improvement={policy.metrics.get('baseline_improvement', 0.0):.4f} "
                    "minimum_fold_balanced_accuracy="
                    f"{policy.metrics.get('minimum_fold_balanced_accuracy', 0.0):.4f}"
                ],
            ).to_dict()
        if len(available) < required_specialists:
            return LocalSynthesisResult(
                "insufficient_specialists",
                "multi_factor_diagnostic",
                None,
                None,
                None,
                RULE_SYNTHESIS_VERSION,
                len(available),
                None,
                [
                    f"at least {required_specialists} quality-approved specialists are required",
                    *_excluded_evidence(results, specialist_names),
                ],
            ).to_dict()
        calculation = calculate_diagnostic(results, specialist_names)
        if calculation is None:
            return LocalSynthesisResult(
                "data_unavailable",
                "multi_factor_diagnostic",
                None,
                None,
                None,
                RULE_SYNTHESIS_VERSION,
                len(available),
                None,
                ["approved specialists did not provide usable diagnostic signals"],
            ).to_dict()
        return LocalSynthesisResult(
            status="available",
            target="multi_factor_diagnostic",
            signal=calculation.signal,
            probability=None,
            confidence=calculation.confidence,
            model_version=RULE_SYNTHESIS_VERSION,
            available_agents=len(available),
            disagreement=calculation.disagreement,
            evidence=[
                f"asset_scope={'etf' if etf_scope else 'equity'}",
                f"specialist_coverage={len(available)}/{len(specialist_names)}",
                f"diagnostic_score={calculation.score:.2f}",
                f"specialist_disagreement={calculation.disagreement:.6f}",
                *(
                    f"included_{name}=horizon_days:"
                    f"{results[name].get('horizon_days', 'unknown')},"
                    f"signal:{value:+.0f},effective_weight:{weight:.6f}"
                    for name, value, weight in calculation.included
                ),
                *_excluded_evidence(results, specialist_names),
            ],
            diagnostic_score=calculation.score,
        ).to_dict()

    def _analyze_one(
        self,
        agent: AgentName,
        facts: dict,
        *,
        etf_scope: bool = False,
        symbol: str | None = None,
    ) -> LocalAgentResult:
        """전문 AI 하나의 artifact·특성·품질을 검증하고 사용 가능 상태를 결정한다."""

        model_name: ModelName = (
            "etf_technical"
            if etf_scope and agent == "technical"
            else "etf_risk"
            if etf_scope and agent == "risk"
            else agent
        )
        path = self._artifact_dir / f"{model_name}.json"
        if not path.is_file():
            return LocalAgentResult(
                agent, TARGETS[agent], "model_missing", None, None, None, None,
                ["trained artifact missing"],
            )
        values = extract_features(agent, facts)
        if model_name == "etf_technical":
            combined = {
                **(facts.get("local_market_features") or {}),
                **(facts.get("local_macro_features") or {}),
                **etf_asset_class_features(symbol or ""),
            }
            names = ETF_MODEL_FEATURES[model_name]
            values = (
                {name: float(combined[name]) for name in names}
                if all(combined.get(name) is not None for name in names)
                else None
            )
        if values is None:
            return LocalAgentResult(
                agent, TARGETS[agent], "data_unavailable", None, None, None, None,
                ["required features missing"],
            )
        try:
            model = LocalLogisticModel.load(path, expected_agent=model_name)
            expected_features = ETF_MODEL_FEATURES.get(model_name, FEATURES[agent])
            if tuple(model.artifact.feature_names) != expected_features:
                raise ValueError("trained feature schema is not current")
            metrics = model.artifact.metrics
            horizon_days = int(metrics.get("prediction_horizon_days", 5))
            validation_accuracy = metrics.get("accuracy", 0.0)
            assessment = assess_model_quality(model_name, metrics)
            if not assessment.accepted:
                return LocalAgentResult(
                    agent,
                    TARGETS[agent],
                    "quality_rejected",
                    None,
                    None,
                    None,
                    model.artifact.model_version,
                    [
                        quality_evidence(metrics, assessment)
                    ],
                )
            probability = model.predict_probability(values)
        except ValueError as exc:
            return LocalAgentResult(
                agent, TARGETS[agent], "artifact_invalid", None, None, None, None, [str(exc)]
            )
        signal = _directional_signal(agent, probability)
        confidence = min(1.0, abs(probability - 0.5) * 2 * max(validation_accuracy, 0.5))
        evidence = [
            f"asset_scope={'etf' if etf_scope else 'equity'}",
            f"decision_band={SIGNAL_BANDS[agent]:.3f}",
            *(f"{name}={value:.6g}" for name, value in values.items()),
            f"validation_balanced_accuracy={metrics.get('balanced_accuracy', 0.0):.6g}",
            f"validation_roc_auc={metrics.get('roc_auc', 0.5):.6g}",
            f"validation_calibration_error={metrics.get('calibration_error', 1.0):.6g}",
            f"validation_decision_threshold={metrics.get('decision_threshold', 0.5):.6g}",
            f"prediction_horizon_days={horizon_days}",
        ]
        return LocalAgentResult(
            agent=agent,
            target=target_name(agent, horizon_days),
            status="available",
            signal=signal,
            probability=round(probability, 6),
            confidence=round(confidence, 6),
            model_version=model.artifact.model_version,
            evidence=evidence,
            horizon_days=horizon_days,
        )


def _excluded_evidence(
    results: dict[str, dict], specialist_names: tuple[AgentName, ...]
) -> list[str]:
    """`_excluded_evidence`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    return [
        f"excluded_{name}=status:{(results.get(name) or {}).get('status', 'missing')}"
        for name in specialist_names
        if (results.get(name) or {}).get("status") != "available"
    ]
