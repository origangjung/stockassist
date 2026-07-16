from app.ai_reports.contracts import AIReportGenerator


class MockAIReportGenerator(AIReportGenerator):
    """Deterministic generator used until an LLM API key is intentionally enabled."""

    name = "mock"
    model = "deterministic-report-v1"

    def generate(self, facts: dict) -> dict:
        score = facts.get("score") or {}
        prediction = facts.get("prediction") or {}
        warnings = facts.get("warnings") or []
        chart_patterns = (facts.get("chart_patterns") or {}).get("patterns", [])
        points: list[str] = []
        if score.get("overall_score") is not None:
            points.append(
                f"종합 점수는 {float(score['overall_score']):.1f}/100이며, "
                f"현재 분석 축 커버리지는 {float(score.get('coverage_ratio', 0)):.0%}입니다."
            )
        if prediction.get("rise_probability") is not None:
            points.append(
                f"실험 상태의 {prediction.get('horizon_days', 0)}일 모델이 추정한 "
                f"상승 확률은 {float(prediction['rise_probability']):.1%}입니다."
            )
        if warnings:
            points.append(f"Provider 데이터에 투자유의 신호 {len(warnings)}개가 확인됩니다.")
        if chart_patterns:
            names = ", ".join(str(item["name"]) for item in chart_patterns[:3])
            points.append(f"실험 패턴 엔진에서 {names} 패턴이 감지되었습니다.")
        if not points:
            points.append("종합 설명을 생성하기에 가용 데이터가 부족합니다.")
        return {
            "summary": "가용 시장 데이터와 실험 모델 출력을 종합한 의사결정 참고 결과입니다.",
            "key_points": points,
            "risk_factors": (
                ["Provider 데이터에 투자유의 신호가 존재합니다."]
                if warnings
                else ["시장 상황과 모델 출력은 예고 없이 달라질 수 있습니다."]
            ),
            "counterpoints": ["과거 패턴과 모델 확률은 미래 성과를 보장하지 않습니다."],
        }
