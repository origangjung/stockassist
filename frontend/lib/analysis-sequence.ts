/** `analysisAgentOrder`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export const analysisAgentOrder = [
  "technical",
  "financial",
  "news",
  "investor_flow",
  "risk",
] as const;

export type AnalysisAgentKey = (typeof analysisAgentOrder)[number];
export type AnalysisSequencePhase =
  | AnalysisAgentKey
  | "research"
  | "trading"
  | "serving"
  | "synthesis";

/** AnalysisSequenceTiming 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. */
export interface AnalysisSequenceTiming {
  /** 분석 시작 뒤 첫 전문 AI를 공개하기 전 대기 시간이다. */
  briefingMs: number;
  /** 전문 AI 하나에서 다음 전문 AI로 넘어가는 간격이다. */
  courseMs: number;
  /** 강세·약세 교차 검증 장면에 할당한 시간이다. */
  researchDebateMs: number;
  /** 가격 구간과 실행 위험 검토 장면에 할당한 시간이다. */
  tradingReviewMs: number;
  /** 최종 판정을 정리하고 공개하기까지의 시간이다. */
  finalServiceMs: number;
}

/** 발표 시간표에서 한 시점에 공개할 단계와 완료 상태를 나타내는 계약이다. */
export interface AnalysisSequenceStep {
  announcement: string;
  atMs: number;
  complete: boolean;
  phase: AnalysisSequencePhase;
  revealedCount: number;
}

/** `defaultAnalysisSequenceTiming`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export const defaultAnalysisSequenceTiming: AnalysisSequenceTiming = {
  briefingMs: 1200,
  courseMs: 2600,
  researchDebateMs: 5000,
  tradingReviewMs: 2400,
  finalServiceMs: 2200,
};

/** `orderedAvailableAgents`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export function orderedAvailableAgents(
  availableAgentKeys: readonly string[],
): AnalysisAgentKey[] {
  // API 응답 순서와 무관하게 서비스가 약속한 전문 AI 순서를 유지한다.
  const available = new Set(availableAgentKeys);
  return analysisAgentOrder.filter((agent) => available.has(agent));
}

/** `buildAnalysisSequence`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export function buildAnalysisSequence(
  availableAgentKeys: readonly string[],
  timing: AnalysisSequenceTiming = defaultAnalysisSequenceTiming,
): AnalysisSequenceStep[] {
  // 데이터가 없는 전문 AI는 시간표에서 제외해 빈 발표 구간이 생기지 않게 한다.
  const agents = orderedAvailableAgents(availableAgentKeys);
  if (agents.length === 0) {
    return [{
      announcement: "사용 가능한 분석 근거가 없어 종합 참고 결과만 표시합니다.",
      atMs: 0,
      complete: true,
      phase: "synthesis",
      revealedCount: 0,
    }];
  }

  const specialistSteps = agents.map((agent, index): AnalysisSequenceStep => ({
    announcement: `${index + 1}/${agents.length} 전문 AI 근거를 확인했습니다.`,
    atMs: timing.briefingMs + index * timing.courseMs,
    complete: false,
    phase: agent,
    revealedCount: index + 1,
  }));
  const researchStart = timing.briefingMs + agents.length * timing.courseMs;
  const tradingStart = researchStart + timing.researchDebateMs;
  const servingStart = tradingStart + timing.tradingReviewMs;

  return [
    ...specialistSteps,
    {
      announcement: "강세와 약세 관점이 서로의 근거를 검증하고 있습니다.",
      atMs: researchStart,
      complete: false,
      phase: "research",
      revealedCount: agents.length,
    },
    {
      announcement: "트레이딩 데스크가 가격 구간과 유동성을 점검하고 있습니다.",
      atMs: tradingStart,
      complete: false,
      phase: "trading",
      revealedCount: agents.length,
    },
    {
      announcement: `${agents.length}개 전문 관점 중 품질 기준을 통과한 근거를 종합하고 있습니다.`,
      atMs: servingStart,
      complete: false,
      phase: "serving",
      revealedCount: agents.length,
    },
    {
      announcement: "종합 검토가 완료되었습니다. 최종 참고 결과와 반대 의견을 표시합니다.",
      atMs: servingStart + timing.finalServiceMs,
      complete: true,
      phase: "synthesis",
      revealedCount: agents.length,
    },
  ];
}
