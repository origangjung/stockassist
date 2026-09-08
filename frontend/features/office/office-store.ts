/** office-store 파일은 프론트 기능 상태와 이벤트 기능을 담당한다. */

import { create } from "zustand";
import type { OfficeRoomId } from "./office-map.config";

/** OfficeActivity 인터페이스는 화면 기능별 상태와 도메인 이벤트를 관리합니다.에서 교환하는 필드 계약을 정의합니다. */
export interface OfficeActivity {
  /** 발언을 만든 캐릭터 식별자이며 시스템 이벤트는 null이다. */
  agent: string | null;
  /** 표시 순서와 React key에 사용하는 분석 내 증가 번호다. */
  id: number;
  /** 시스템 시작, 방 이동, 발언, 최종 판정을 구분한다. */
  kind: "system" | "room" | "speech" | "verdict";
  /** 사용자 이벤트 기록에 표시하는 한글 설명이다. */
  message: string;
  /** 이벤트가 발생한 방이며 방과 무관하면 null이다. */
  room: OfficeRoomId | null;
}

/** 오피스 화면 값과 그 값을 변경하는 action을 함께 정의하는 Zustand 상태 계약이다. */
export interface OfficeAnalysisState {
  activeMessage: string | null;
  activeRoom: OfficeRoomId | null;
  activeSpeaker: string | null;
  analysisId: string | null;
  events: OfficeActivity[];
  eventSequence: number;
  status: "idle" | "running" | "complete";
  begin: (analysisId: string) => void;
  complete: (analysisId: string) => void;
  focusRoom: (room: OfficeRoomId) => void;
  speak: (agent: string, message: string) => void;
  reset: () => void;
}

const initialState = {
  activeMessage: null,
  activeRoom: null,
  activeSpeaker: null,
  analysisId: null,
  events: [] as OfficeActivity[],
  eventSequence: 0,
  status: "idle" as const,
};

/** `appendEvent`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
function appendEvent(
  state: OfficeAnalysisState,
  event: Omit<OfficeActivity, "id">,
): Pick<OfficeAnalysisState, "events" | "eventSequence"> {
  // 한 분석이 무한히 메모리를 사용하지 않도록 최근 24개 이벤트만 유지한다.
  const eventSequence = state.eventSequence + 1;
  return {
    eventSequence,
    events: [...state.events, { ...event, id: eventSequence }].slice(-24),
  };
}

/** `useOfficeAnalysisStore`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export const useOfficeAnalysisStore = create<OfficeAnalysisState>((set) => ({
  ...initialState,
  begin: (analysisId) => set(() => ({
    ...initialState,
    analysisId,
    eventSequence: 1,
    events: [{
      agent: null,
      id: 1,
      kind: "system",
      message: "분석 요청을 접수하고 전문 AI에 자료를 배포했습니다.",
      room: null,
    }],
    status: "running",
  })),
  complete: (analysisId) => set((state) => ({
    ...appendEvent(state, {
      agent: "chair",
      kind: "verdict",
      message: "검증을 통과한 근거만 모아 최종 참고 결과를 정리했습니다.",
      room: "pm",
    }),
    activeMessage: "검증을 통과한 근거만으로 최종 참고 결과를 정리했습니다.",
    activeRoom: "pm",
    activeSpeaker: "chair",
    analysisId,
    status: "complete",
  })),
  focusRoom: (activeRoom) => set((state) => ({
    ...appendEvent(state, {
      agent: null,
      kind: "room",
      message: `${activeRoom.toUpperCase()} 단계로 분석을 인계했습니다.`,
      room: activeRoom,
    }),
    activeRoom,
  })),
  speak: (activeSpeaker, activeMessage) => set((state) => ({
    ...appendEvent(state, {
      agent: activeSpeaker,
      kind: "speech",
      message: activeMessage,
      room: state.activeRoom,
    }),
    activeMessage,
    activeSpeaker,
  })),
  reset: () => set(initialState),
}));
