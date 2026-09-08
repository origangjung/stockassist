"""전문 AI별 역할에 맞는 예측 기간과 정답 의미를 정의한다."""

from dataclasses import dataclass

from app.local_ai.contracts import AgentName


@dataclass(frozen=True)
class AgentHorizonPolicy:
    """전문 AI 하나가 검증할 기본 기간과 비교 후보 기간을 묶는다."""

    primary_days: int
    candidate_days: tuple[int, ...]
    target: str


HORIZON_POLICIES: dict[AgentName, AgentHorizonPolicy] = {
    "technical": AgentHorizonPolicy(10, (5, 10), "benchmark_relative_direction"),
    # 5일은 기존 artifact를 읽기 위한 호환 기간이며 새 후보의 기본값은 20일이다.
    "financial": AgentHorizonPolicy(20, (5, 20, 60), "fundamental_repricing"),
    "news": AgentHorizonPolicy(3, (3, 5), "event_price_reaction"),
    "investor_flow": AgentHorizonPolicy(10, (5, 10), "flow_persistence"),
    "risk": AgentHorizonPolicy(5, (5, 20), "downside_event"),
}


def validate_horizon(agent: AgentName, days: int) -> int:
    """예측 기간이 해당 전문 AI의 사전 등록 후보인지 검증한다."""

    if days not in HORIZON_POLICIES[agent].candidate_days:
        allowed = ",".join(str(value) for value in HORIZON_POLICIES[agent].candidate_days)
        raise ValueError(f"{agent} horizon must be one of {allowed} trading days")
    return days


def target_name(agent: AgentName, days: int) -> str:
    """API와 로그에서 기간을 숨기지 않는 정답 이름을 만든다."""

    validate_horizon(agent, days)
    return f"{HORIZON_POLICIES[agent].target}_{days}d"
