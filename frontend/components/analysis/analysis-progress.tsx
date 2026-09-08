"use client";

/**
 * 분석 데이터를 직접 계산하지 않고 의미 있는 오피스 이벤트를 시각화한다.
 * 접근성 설정으로 캐릭터 움직임을 줄여도 방 이동·발언·최종 판정 기록은 유지한다.
 */

import { useEffect, useMemo, useState, type CSSProperties } from "react";
import { createPortal } from "react-dom";
import {
  officeCharacters,
  officeRooms,
  type OfficeCharacter,
  type OfficeRoomId,
} from "../../features/office/office-map.config";
import { useOfficeAnalysisStore } from "../../features/office/office-store";
import type {
  MeetingAgentKey,
  MeetingPhase,
  MeetingSceneAgent,
} from "./agent-meeting-stage";

/** AI 사무실의 진행 단계, 참여 가능한 전문가, 재생 제어를 전달하는 컴포넌트 계약입니다. */
interface AnalysisProgressProps {
  agents: MeetingSceneAgent[];
  availableAgentKeys?: readonly MeetingAgentKey[];
  complete: boolean;
  loading?: boolean;
  onReplay?: () => void;
  onSkip?: () => void;
  phase: MeetingPhase;
  revealedCount: number;
}

/** 전문가 종류에 맞는 픽셀 캐릭터와 표시 크기를 선택하는 입력 계약입니다. */
interface PixelAnalystProps {
  agent: MeetingAgentKey | "director";
  size?: "office" | "message";
}

const agentBriefs: Record<MeetingAgentKey, string> = {
  technical: "가격·거래량 구조를 점검합니다.",
  financial: "실적과 재무 건전성을 검토합니다.",
  news: "뉴스와 공시의 영향을 확인합니다.",
  investor_flow: "투자자별 수급 흐름을 추적합니다.",
  risk: "반대 근거와 하락 위험을 점검합니다.",
};

const roomForPhase = (phase: MeetingPhase): OfficeRoomId => {
  if (phase === "technical" || phase === "financial" || phase === "news" || phase === "gathering") return "analysts";
  if (phase === "investor_flow" || phase === "risk") return "risk";
  if (phase === "research") return "research";
  if (phase === "trading") return "trading";
  return "pm";
};

/** `phaseLabel`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
function phaseLabel(phase: MeetingPhase, complete: boolean, loading: boolean) {
  if (loading || phase === "gathering") return "분석 자료를 각 부서에 배포하고 있습니다.";
  if (complete || phase === "synthesis") return "최종 검토가 완료됐습니다.";
  if (phase === "research") return "강세와 약세 관점이 반대 근거를 토론합니다.";
  if (phase === "trading") return "트레이딩 데스크가 가격 구간을 검토합니다.";
  if (phase === "serving") return "회장님이 통과한 근거만 종합하고 있습니다.";
  return agentBriefs[phase];
}

/** `agentState`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
function agentState(
  character: OfficeCharacter,
  phase: MeetingPhase,
  revealedCount: number,
  availableAgentKeys: readonly MeetingAgentKey[],
  activeSpeaker: string | null,
) {
  if (character.id === activeSpeaker) return "active";
  if (!character.agent || character.agent === "director") return roomForPhase(phase) === character.room ? "active" : "support";
  const availableIndex = availableAgentKeys.indexOf(character.agent);
  if (availableIndex === -1) return "unavailable";
  if (character.agent === phase) return "active";
  if (availableIndex < revealedCount) return "complete";
  return "pending";
}

/** `stateLabel`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
function stateLabel(state: ReturnType<typeof agentState>) {
  if (state === "complete") return "검토 완료";
  if (state === "active") return "발언 중";
  if (state === "unavailable") return "데이터 없음";
  if (state === "support") return "대기";
  return "분석 대기";
}

/** `PixelAnalyst`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export function PixelAnalyst({ agent, size = "office" }: PixelAnalystProps) {
  return (
    <span className={`pixel-analyst pixel-analyst--${agent} pixel-analyst--${size}`} aria-hidden="true">
      <i className="pixel-analyst__shadow" />
      <i className="pixel-analyst__hair" />
      <i className="pixel-analyst__face" />
      <i className="pixel-analyst__eye pixel-analyst__eye--left" />
      <i className="pixel-analyst__eye pixel-analyst__eye--right" />
      <i className="pixel-analyst__body" />
      <i className="pixel-analyst__arm pixel-analyst__arm--left" />
      <i className="pixel-analyst__arm pixel-analyst__arm--right" />
      <i className="pixel-analyst__prop" />
      <i className="pixel-analyst__legs" />
    </span>
  );
}

/** `TypingBubble`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
function TypingBubble({ message }: { message: string }) {
  const [visibleCharacters, setVisibleCharacters] = useState(0);

  useEffect(() => {
    setVisibleCharacters(0);
    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reducedMotion) {
      setVisibleCharacters(message.length);
      return;
    }
    const timer = window.setInterval(() => {
      setVisibleCharacters((count) => {
        if (count >= message.length) {
          window.clearInterval(timer);
          return count;
        }
        return count + 1;
      });
    }, 28);
    return () => window.clearInterval(timer);
  }, [message]);

  return <span className="office-character__bubble">{message.slice(0, visibleCharacters)}<i aria-hidden="true" /></span>;
}

/** `AnalysisProgress`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export function AnalysisProgress({
  agents,
  availableAgentKeys = agents.map((agent) => agent.agent),
  complete,
  loading = false,
  onReplay,
  onSkip,
  phase,
  revealedCount,
}: AnalysisProgressProps) {
  const [selectedCharacter, setSelectedCharacter] = useState<OfficeCharacter | null>(null);
  const [eventHistoryOpen, setEventHistoryOpen] = useState(false);
  const streamedRoom = useOfficeAnalysisStore((state) => state.activeRoom);
  const activeSpeaker = useOfficeAnalysisStore((state) => state.activeSpeaker);
  const activeMessage = useOfficeAnalysisStore((state) => state.activeMessage);
  const events = useOfficeAnalysisStore((state) => state.events);
  const availableCount = availableAgentKeys.length;
  const completion = availableCount ? Math.round((revealedCount / availableCount) * 100) : 100;
  const activeRoom = streamedRoom ?? roomForPhase(phase);
  const activeSpeech = useMemo(
    () => officeCharacters.find((character) => character.id === activeSpeaker) ?? null,
    [activeSpeaker],
  );

  useEffect(() => {
    if (!selectedCharacter) return;
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") setSelectedCharacter(null);
    };
    window.addEventListener("keydown", closeOnEscape);
    return () => window.removeEventListener("keydown", closeOnEscape);
  }, [selectedCharacter]);

  return (
    <section
      aria-label="AI 애널리스트 오피스 분석 진행 상태"
      /** Name 클래스는 AI 분석 진행과 결과 표현을 담당합니다.의 상태와 동작을 캡슐화합니다. */
      className={`broker-office ${complete ? "is-complete" : ""}`}
      data-phase={phase}
    >
      <header className="broker-office__header">
        <div>
          <span>STOCKPILOT · AI ANALYST OFFICE</span>
          <strong>{phaseLabel(phase, complete, loading)}</strong>
        </div>
        <div className="broker-office__status" role="status" aria-live="polite">
          <i aria-hidden="true" />
          {complete ? "회의 완료" : loading ? "자료 수집 중" : "애널리스트팀 분석 중"}
        </div>
      </header>

      <div className="broker-office__viewport">
        <div className="broker-office__scene">
          <div className="broker-office__shade" aria-hidden="true" />
          {officeRooms.map((room) => (
            <button
              aria-label={`${room.label} 팀 소개 보기`}
              /** Name 클래스는 AI 분석 진행과 결과 표현을 담당합니다.의 상태와 동작을 캡슐화합니다. */
              className={`office-room ${room.className} ${activeRoom === room.id ? "is-active" : ""}`}
              key={room.id}
              onClick={() => setSelectedCharacter(officeCharacters.find((character) => character.room === room.id) ?? null)}
              type="button"
            >
              {room.label}
            </button>
          ))}

          {officeCharacters.map((character) => {
            const state = agentState(character, phase, revealedCount, availableAgentKeys, activeSpeaker);
            const speech = activeSpeaker === character.id ? activeMessage : null;
            const avatarAgent = character.agent ?? (character.room === "research" ? "technical" : "director");
            return (
              <button
                aria-label={`${character.name}, ${character.role}. 소개 보기`}
                /** Name 클래스는 AI 분석 진행과 결과 표현을 담당합니다.의 상태와 동작을 캡슐화합니다. */
                className={`office-character office-character--${character.id} motion-${character.motion} is-${state}`}
                key={character.id}
                onClick={() => setSelectedCharacter(character)}
                style={{ "--office-x": `${character.x}%`, "--office-y": `${character.y}%`, "--motion-delay": `${(character.x % 7) * -0.13}s` } as CSSProperties}
                type="button"
              >
                {speech && <TypingBubble message={speech} />}
                <PixelAnalyst agent={avatarAgent} />
                <b>{character.name}</b>
                <small>{stateLabel(state)}</small>
              </button>
            );
          })}

          <span className="office-debate-line" data-visible={phase === "research"} aria-hidden="true" />
          {activeSpeech && <span className="sr-only">{activeSpeech.name} 발언 중</span>}
        </div>
      </div>

      <section
        aria-label="실시간 분석 이벤트"
        aria-live="polite"
        /** Name 클래스는 AI 분석 진행과 결과 표현을 담당합니다.의 상태와 동작을 캡슐화합니다. */
        className="office-event-feed"
        data-event-count={events.length}
        role="log"
      >
        <header><span>LIVE EVENTS</span><b>{events.length}</b></header>
        <ol>
          {events.slice(eventHistoryOpen ? -5 : -1).map((event) => {
            const speaker = event.agent
              ? officeCharacters.find((character) => character.id === event.agent)?.name
              : null;
            return (
              <li className={`is-${event.kind}`} key={event.id}>
                <i aria-hidden="true" />
                <span>{speaker ?? (event.room ? event.room.toUpperCase() : "SYSTEM")}</span>
                <p>{event.message}</p>
              </li>
            );
          })}
        </ol>
        {events.length > 1 && <button className="office-event-toggle" onClick={() => setEventHistoryOpen((open) => !open)} type="button">{eventHistoryOpen ? "최근 이벤트만" : `이전 이벤트 ${Math.min(events.length - 1, 4)}개`}</button>}
      </section>

      <footer className="broker-office__footer">
        <div className="broker-office__progress">
          <span><b>{revealedCount}</b> / {availableCount} SPECIALISTS · {officeCharacters.length} STAFF</span>
          <div aria-hidden="true"><i style={{ "--progress": `${completion}%` } as CSSProperties} /></div>
        </div>
        <p>캐릭터나 팀 라벨을 누르면 자세한 소개를 볼 수 있어요</p>
        {!loading && !complete && onSkip && <button onClick={onSkip} type="button">결과 바로 보기</button>}
        {complete && onReplay && <button onClick={onReplay} type="button">회의 다시 보기</button>}
      </footer>

      {selectedCharacter && createPortal(
        <div className="office-profile-backdrop" onMouseDown={() => setSelectedCharacter(null)}>
          <aside
            aria-label={`${selectedCharacter.name} 소개`}
            aria-modal="true"
            /** Name 클래스는 AI 분석 진행과 결과 표현을 담당합니다.의 상태와 동작을 캡슐화합니다. */
            className="office-profile-sheet"
            onMouseDown={(event) => event.stopPropagation()}
            role="dialog"
          >
            <button aria-label="소개 닫기" className="office-profile-sheet__close" onClick={() => setSelectedCharacter(null)} type="button">×</button>
            <PixelAnalyst agent={selectedCharacter.agent ?? "director"} size="message" />
            <div><span>{officeRooms.find((room) => room.id === selectedCharacter.room)?.label}</span><h3>{selectedCharacter.name}</h3><b>{selectedCharacter.role}</b></div>
            <p>{selectedCharacter.intro}</p>
          </aside>
        </div>,
        document.body,
      )}
    </section>
  );
}
