/** analysis-events 파일은 프론트 기능 상태와 이벤트 기능을 담당한다. */

import type {
  AnalysisAgentKey,
  AnalysisSequenceStep,
} from "../../lib/analysis-sequence";
import type { OfficeRoomId } from "./office-map.config";

export type AgentId =
  | AnalysisAgentKey
  | "chart"
  | "ledger"
  | "balance"
  | "volguard"
  | "bull"
  | "bear"
  | "lead"
  | "trader"
  | "chair";

export type AnalysisEvent =
  | { type: "room_active"; payload: { room: OfficeRoomId } }
  | { type: "agent_speak"; payload: { agent: AgentId; message: string } }
  | { type: "verdict_ready"; payload: { analysisId: string } };

/** 시간표에서 발생한 분석 이벤트를 구독하고 해제하는 최소 stream 계약이다. */
export interface AnalysisEventStream {
  /** listener를 등록하고 모든 예약 타이머를 취소하는 해제 함수를 반환한다. */
  subscribe: (listener: (event: AnalysisEvent) => void) => () => void;
}

const phaseRoom: Record<AnalysisSequenceStep["phase"], OfficeRoomId> = {
  technical: "analysts",
  financial: "analysts",
  news: "analysts",
  investor_flow: "risk",
  risk: "risk",
  research: "research",
  trading: "trading",
  serving: "pm",
  synthesis: "pm",
};

const phaseSpeaker: Record<AnalysisAgentKey, AgentId> = {
  technical: "chart",
  financial: "ledger",
  news: "news",
  investor_flow: "balance",
  risk: "volguard",
};

const defaultMessages: Record<AnalysisAgentKey, string> = {
  technical: "가격·거래량 구조와 추세 신호를 점검했습니다.",
  financial: "공개 시점 기준 실적과 재무 건전성을 검토했습니다.",
  news: "뉴스와 공시의 시점별 영향을 확인했습니다.",
  investor_flow: "공매도와 투자자 흐름의 변화 방향을 분석했습니다.",
  risk: "시장 변동성과 하락 위험, 반대 근거를 점검했습니다.",
};

/** `createTimedAnalysisEventStream`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export function createTimedAnalysisEventStream({
  analysisId,
  messages,
  steps,
}: {
  analysisId: string;
  messages?: Partial<Record<AnalysisAgentKey, string>>;
  steps: AnalysisSequenceStep[];
}): AnalysisEventStream {
  // 컴포넌트와 타이머 생명주기를 분리해 replay와 unmount 때 한 번에 취소할 수 있게 한다.
  return {
    subscribe(listener) {
      const timers: Array<ReturnType<typeof setTimeout>> = [];
      const schedule = (atMs: number, event: AnalysisEvent) => {
        timers.push(globalThis.setTimeout(() => listener(event), atMs));
      };

      for (const step of steps) {
        schedule(step.atMs, { type: "room_active", payload: { room: phaseRoom[step.phase] } });
        if (step.phase in phaseSpeaker) {
          const agent = step.phase as AnalysisAgentKey;
          schedule(step.atMs + 120, {
            type: "agent_speak",
            payload: { agent: phaseSpeaker[agent], message: messages?.[agent] ?? defaultMessages[agent] },
          });
        } else if (step.phase === "research") {
          schedule(step.atMs + 150, { type: "agent_speak", payload: { agent: "bull", message: "긍정 신호가 유지될 조건부터 확인하죠." } });
          schedule(step.atMs + 1450, { type: "agent_speak", payload: { agent: "bear", message: "반대로 실패할 조건과 하방 위험도 봐야 합니다." } });
          schedule(step.atMs + 2750, { type: "agent_speak", payload: { agent: "bull", message: "그 위험을 감안해도 확인된 회복 신호는 남아 있습니다." } });
          schedule(step.atMs + 3900, { type: "agent_speak", payload: { agent: "lead", message: "양쪽 주장에 실제 데이터 근거가 있는지 비교했습니다." } });
        } else if (step.phase === "trading") {
          schedule(step.atMs + 150, { type: "agent_speak", payload: { agent: "trader", message: "가격 구간은 주문 지시가 아닌 관찰 기준으로만 정리합니다." } });
        } else if (step.phase === "serving") {
          schedule(step.atMs + 150, { type: "agent_speak", payload: { agent: "chair", message: "검증을 통과한 전문 신호만 최종 판단 후보로 반영합니다." } });
        }
        if (step.complete) schedule(step.atMs, { type: "verdict_ready", payload: { analysisId } });
      }

      return () => timers.forEach((timer) => globalThis.clearTimeout(timer));
    },
  };
}
