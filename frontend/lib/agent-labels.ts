/** 내부 AI 식별자가 사용자 화면에 노출되지 않도록 한글 표시 정보를 한곳에서 관리한다. */
export const agentPresentation: Record<string, { name: string; role: string }> = {
  technical: { name: "기술 분석", role: "차트·추세" },
  financial: { name: "재무 분석", role: "실적·밸류에이션" },
  news: { name: "뉴스 분석", role: "뉴스·공시" },
  investor_flow: { name: "수급 분석", role: "투자자 흐름" },
  risk: { name: "위험 분석", role: "하락 위험" },
  master: { name: "종합 판단", role: "최종 검토" },
  synthesis: { name: "종합 판단", role: "최종 검토" },
};

/** `agentDisplayName`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export function agentDisplayName(agent: string) {
  return agentPresentation[agent]?.name ?? "분석 모델";
}

/** `agentRoleName`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export function agentRoleName(agent: string) {
  return agentPresentation[agent]?.role ?? "참고 분석";
}
