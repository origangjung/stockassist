"use client";

/** agent-meeting-stage 파일은 AI 분석 진행과 결과 화면 기능을 담당한다. */

import {
  useEffect,
  useId,
  useRef,
  type KeyboardEvent as ReactKeyboardEvent,
  type RefObject,
} from "react";

export type MeetingAgentKey = "technical" | "financial" | "news" | "investor_flow" | "risk";
export type MeetingPhase = MeetingAgentKey | "gathering" | "research" | "trading" | "serving" | "synthesis";

/** MeetingSceneAgent 인터페이스는 AI 분석 진행과 결과 표현을 담당합니다.에서 교환하는 필드 계약을 정의합니다. */
export interface MeetingSceneAgent {
  agent: MeetingAgentKey;
  name: string;
  role: string;
}

/** ChefMenu 인터페이스는 AI 분석 진행과 결과 표현을 담당합니다.에서 교환하는 필드 계약을 정의합니다. */
export interface ChefMenu {
  chefName: string;
  course: string;
  dish: string;
  ingredient: string;
}

/** `chefMenus`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export const chefMenus: Record<MeetingAgentKey, ChefMenu> = {
  technical: {
    chefName: "기술 분석",
    course: "LENS 01 · TECHNICAL",
    dish: "추세와 모멘텀",
    ingredient: "가격 · 거래량 · 기술 지표",
  },
  financial: {
    chefName: "재무 분석",
    course: "LENS 02 · FUNDAMENTALS",
    dish: "실적과 밸류에이션",
    ingredient: "실적 · 재무 구조 · 밸류에이션",
  },
  news: {
    chefName: "뉴스·공시 분석",
    course: "LENS 03 · EVENTS",
    dish: "이슈와 공시",
    ingredient: "뉴스 · 공시 · 시장 반응",
  },
  investor_flow: {
    chefName: "수급 분석",
    course: "LENS 04 · FLOW",
    dish: "투자자 흐름",
    ingredient: "투자자 흐름 · 시장 환경",
  },
  risk: {
    chefName: "위험 분석",
    course: "LENS 05 · RISK",
    dish: "위험과 반대 근거",
    ingredient: "경고 신호 · 반대 근거 · 위험 요인",
  },
};

/** AnalystAvatarProps 인터페이스는 AI 분석 진행과 결과 표현을 담당합니다.에서 교환하는 필드 계약을 정의합니다. */
interface AnalystAvatarProps {
  agent: MeetingAgentKey | "master";
  size?: "message" | "roster" | "scene";
}

/** AgentMeetingStageProps 인터페이스는 AI 분석 진행과 결과 표현을 담당합니다.에서 교환하는 필드 계약을 정의합니다. */
interface AgentMeetingStageProps {
  agents: MeetingSceneAgent[];
  phase: MeetingPhase;
  revealedCount: number;
  complete: boolean;
  loading?: boolean;
  /**
   * The cinematic stage visually covers the page. Keep this enabled by default
   * so assistive technology receives the same modal context as sighted users.
   */
  cinematicDialog?: boolean;
  /** An optional focus target to receive focus when the cinematic stage opens. */
  initialFocusRef?: RefObject<HTMLElement | null>;
  /** An optional focus target to receive focus once the cinematic stage closes. */
  restoreFocusRef?: RefObject<HTMLElement | null>;
  /** Lifecycle hook for callers that need to react to the cinematic stage opening. */
  onCinematicEnter?: () => void;
  /** Lifecycle hook for callers that need to react after focus is restored. */
  onCinematicExit?: () => void;
  onReplay?: () => void;
  onSkip?: () => void;
}

/** `AnalystAvatar`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export function AnalystAvatar({ agent, size = "message" }: AnalystAvatarProps) {
  return (
    <span className={`analyst-avatar analyst-avatar--${agent} analyst-avatar--${size}`} aria-hidden="true">
      <span className="analyst-avatar__floor" />
      <span className="analyst-avatar__hat"><i /><i /><i /></span>
      <span className="analyst-avatar__hair" />
      <span className="analyst-avatar__face" />
      <span className="analyst-avatar__body">
        <span className="analyst-avatar__arm analyst-avatar__arm--left" />
        <span className="analyst-avatar__arm analyst-avatar__arm--right" />
        <span className="analyst-avatar__tool" />
      </span>
    </span>
  );
}

/** `sceneMessage`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
function sceneMessage({ agents, phase, complete, loading }: AgentMeetingStageProps) {
  const courseCount = agents.length;
  if (loading) {
    return {
      eyebrow: "STOCKPILOT RESEARCH FLOOR · DATA INTAKE",
      title: "AI 애널리스트가 분석 데이터를 정리하고 있습니다.",
      detail: "수집이 끝나면 각 분석 관점의 핵심 근거와 종합 결과가 순서대로 표시됩니다.",
    };
  }

  if (complete) {
    return {
      eyebrow: "STOCKPILOT RESEARCH FLOOR · REVIEW COMPLETE",
      title: `${courseCount}개 분석 관점의 최종 검토가 완료되었습니다.`,
      detail: "종합 결과와 반대 근거를 함께 확인하세요. 아래 내용은 투자 자문이나 매매 지시가 아닌 참고 정보입니다.",
    };
  }

  if (phase === "serving") {
    return {
      eyebrow: "STOCKPILOT RESEARCH FLOOR · FINAL REVIEW",
      title: "각 부서의 근거를 모아 최종 결론을 검토하고 있습니다.",
      detail: "검토가 끝나면 종합 참고 신호와 위험·반대 근거가 함께 이어집니다.",
    };
  }

  if (phase === "research") {
    return {
      eyebrow: "STOCKPILOT RESEARCH FLOOR · DEBATE",
      title: "강세와 약세 관점이 서로의 근거를 검증합니다.",
      detail: "한쪽 방향만 강조하지 않도록 반대 의견과 실패 조건을 함께 확인합니다.",
    };
  }

  if (phase === "trading") {
    return {
      eyebrow: "STOCKPILOT RESEARCH FLOOR · MARKET CHECK",
      title: "시장 실행 관점에서 가격 구간과 유동성을 확인합니다.",
      detail: "표시되는 가격은 주문 지시가 아닌 관찰용 참고 구간입니다.",
    };
  }

  if (phase === "gathering") {
    return {
      eyebrow: "STOCKPILOT RESEARCH FLOOR · TEAM BRIEFING",
      title: courseCount > 0
        ? `${courseCount}명의 애널리스트가 각자의 분석 관점을 검토합니다.`
        : "현재 제공 가능한 분석 관점을 확인하고 있습니다.",
      detail: "검토가 완료되는 순서대로 실제 분석 근거가 결과 화면에 표시됩니다.",
    };
  }

  const currentAgent = agents.find((agent) => agent.agent === phase);
  const menu = currentAgent ? chefMenus[currentAgent.agent] : undefined;
  return {
    eyebrow: menu?.course ?? "STOCKPILOT RESEARCH FLOOR · ANALYSIS",
    title: `${menu?.chefName ?? currentAgent?.name ?? "담당 애널리스트"}가 ${menu?.dish ?? "분석 관점"}을 검토합니다.`,
    detail: "검토 중인 분석 문장과 근거는 아래 결과 영역에 그대로 표시됩니다.",
  };
}

/** `AgentMeetingStage`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export function AgentMeetingStage(props: AgentMeetingStageProps) {
  const {
    agents,
    phase,
    revealedCount,
    complete,
    loading = false,
    cinematicDialog = true,
    initialFocusRef,
    restoreFocusRef,
    onCinematicEnter,
    onCinematicExit,
    onReplay,
    onSkip,
  } = props;
  const titleId = useId();
  const descriptionId = useId();
  const stageRef = useRef<HTMLElement>(null);
  const skipButtonRef = useRef<HTMLButtonElement>(null);
  const previouslyFocusedRef = useRef<HTMLElement | null>(null);
  const wasCinematicRef = useRef(false);
  const latestExitConfigRef = useRef({ onCinematicExit, restoreFocusRef });
  const message = sceneMessage(props);
  const activeChef = agents.some((agent) => agent.agent === phase) ? phase : "master";
  const stageMode = loading ? "loading" : complete ? "summary" : "cinematic";
  const isCinematicDialog = cinematicDialog && stageMode === "cinematic";
  const progressLabel = loading
    ? "분석 데이터를 확인하는 중"
    : complete
      ? "모든 분석 검토 완료"
      : phase === "serving"
        ? "리서치 책임자가 최종 결과를 검토하는 중"
      : phase === "gathering"
        ? "애널리스트 브리핑 진행 중"
        : phase === "research"
          ? "강세·약세 리서처가 반대 근거를 토론하는 중"
        : phase === "trading"
          ? "트레이딩 데스크가 가격 구간을 검토하는 중"
        : phase === "synthesis"
          ? "각 관점의 근거를 종합하는 중"
        : `${chefMenus[phase as MeetingAgentKey].chefName} · ${chefMenus[phase as MeetingAgentKey].dish} 준비 중`;

  useEffect(() => {
    latestExitConfigRef.current = { onCinematicExit, restoreFocusRef };
  }, [onCinematicExit, restoreFocusRef]);

  useEffect(() => {
    if (isCinematicDialog) {
      if (wasCinematicRef.current) return;

      wasCinematicRef.current = true;
      previouslyFocusedRef.current = document.activeElement instanceof HTMLElement
        ? document.activeElement
        : null;
      const focusFrame = window.requestAnimationFrame(() => {
        const focusTarget = initialFocusRef?.current ?? skipButtonRef.current ?? stageRef.current;
        focusTarget?.focus({ preventScroll: true });
      });
      onCinematicEnter?.();

      return () => window.cancelAnimationFrame(focusFrame);
    }

    if (!wasCinematicRef.current) return;

    wasCinematicRef.current = false;
    const focusTarget = restoreFocusRef?.current ?? previouslyFocusedRef.current;
    if (focusTarget?.isConnected) {
      focusTarget.focus({ preventScroll: true });
    }
    previouslyFocusedRef.current = null;
    onCinematicExit?.();
  }, [initialFocusRef, isCinematicDialog, onCinematicEnter, onCinematicExit, restoreFocusRef]);

  useEffect(() => () => {
    if (!wasCinematicRef.current) return;

    wasCinematicRef.current = false;
    const { onCinematicExit: notifyExit, restoreFocusRef: focusRestoreRef } = latestExitConfigRef.current;
    const focusTarget = focusRestoreRef?.current ?? previouslyFocusedRef.current;
    if (focusTarget?.isConnected) {
      focusTarget.focus({ preventScroll: true });
    }
    previouslyFocusedRef.current = null;
    notifyExit?.();
  }, []);

  const handleDialogKeyDown = (event: ReactKeyboardEvent<HTMLElement>) => {
    if (!isCinematicDialog) return;

    if (event.key === "Escape" && onSkip) {
      event.preventDefault();
      onSkip();
      return;
    }

    if (event.key !== "Tab") return;

    const focusable = Array.from(
      stageRef.current?.querySelectorAll<HTMLElement>(
        'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])',
      ) ?? [],
    );
    if (focusable.length === 0) {
      event.preventDefault();
      stageRef.current?.focus({ preventScroll: true });
      return;
    }

    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    const activeElement = document.activeElement;
    if (event.shiftKey && activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  };

  return (
    <section
      /** Name 클래스는 AI 분석 진행과 결과 표현을 담당합니다.의 상태와 동작을 캡슐화합니다. */
      className={`agent-meeting-stage kitchen-stage kitchen-stage--${stageMode} ${loading ? "is-loading" : ""} ${complete ? "is-complete" : ""}`}
      aria-describedby={isCinematicDialog ? descriptionId : undefined}
      aria-labelledby={titleId}
      aria-modal={isCinematicDialog || undefined}
      data-phase={phase}
      onKeyDown={handleDialogKeyDown}
      ref={stageRef}
      role={isCinematicDialog ? "dialog" : undefined}
      tabIndex={isCinematicDialog ? -1 : undefined}
    >
      <div className="agent-meeting-stage__copy">
        <span>{message.eyebrow}</span>
        <h3 id={titleId}>{message.title}</h3>
        <p id={descriptionId}>{message.detail}</p>
      </div>

      <div className="meeting-tableau kitchen-tableau" aria-hidden="true" data-active-chef={activeChef} data-phase={phase}>
        <span className="kitchen-room__tile" />
        <span className="kitchen-room__grain" />
        <span className="kitchen-pendant kitchen-pendant--left" />
        <span className="kitchen-pendant kitchen-pendant--right" />
        <span className="meeting-tableau__halo" />
        <span className="meeting-tableau__table" />
        <span className="kitchen-pass-window">
          <span className="kitchen-pass__rail" />
          <span className="kitchen-pass">ANALYSIS PASS</span>
          <span className="kitchen-pass__ticket">{agents.length} COURSE TASTING</span>
          <span className="kitchen-pass__cloche"><i /></span>
          <span className="kitchen-pass__platter">
            {agents.map((agent, index) => (
              <i
                /** Name 클래스는 AI 분석 진행과 결과 표현을 담당합니다.의 상태와 동작을 캡슐화합니다. */
                className={index < revealedCount ? `is-ready dish-${agent.agent}` : ""}
                key={agent.agent}
              />
            ))}
          </span>
          <span className="kitchen-pass__counter" />
        </span>

        {agents.map((agent, index) => {
          const isSpeaking = !loading && !complete && phase === agent.agent;
          const isRevealed = index < revealedCount;
          const isGathering = loading || (!complete && phase === "gathering");
          const menu = chefMenus[agent.agent];
          const state = isGathering
            ? "is-whispering"
            : isSpeaking
              ? "is-speaking"
              : isRevealed
                ? "is-finished"
                : "is-waiting";

          return (
            <div
              /** Name 클래스는 AI 분석 진행과 결과 표현을 담당합니다.의 상태와 동작을 캡슐화합니다. */
              className={`scene-analyst scene-analyst--${agent.agent} ${state}`}
              data-state={state}
              key={agent.agent}
            >
              <span className="kitchen-station__spotlight" />
              <span className="kitchen-station__rail" />
              <span className="kitchen-station__board"><i /><i /><i /></span>
              <span className="kitchen-station__steam"><i /><i /><i /></span>
              <span className="scene-analyst__bubble"><i /><i /><i /></span>
              <span className={`chef-course-dish chef-course-dish--${agent.agent} ${isRevealed ? "is-ready" : ""}`} />
              <span className={`kitchen-course-token kitchen-course-token--${agent.agent} ${isSpeaking ? "is-delivering" : ""}`} />
              <AnalystAvatar agent={agent.agent} size="scene" />
              <span className="scene-analyst__course">{String(index + 1).padStart(2, "0")}</span>
              <span className="scene-analyst__label">{menu.chefName}</span>
            </div>
          );
        })}

        <span className="kitchen-service-tray"><i /><i /><i /></span>
        <div className={`scene-master ${complete ? "is-speaking" : ""} ${phase === "serving" ? "is-serving" : ""}`}>
          <span className="kitchen-expediter__light" />
          <span className="kitchen-expediter__clipboard" />
          <AnalystAvatar agent="master" size="scene" />
          <span className="scene-analyst__label">리서치 책임자</span>
        </div>
        <span className="kitchen-counterfront" />
      </div>

      <div className="agent-meeting-stage__footer">
        <div className="kitchen-stage__progress">
          <span className="kitchen-stage__progress-label">{progressLabel}</span>
          <div className="meeting-progress" aria-hidden="true">
            {agents.map((agent, index) => {
              const isActive = !complete && phase === agent.agent;
              const isComplete = index < revealedCount;
              return <i className={`${isComplete ? "is-complete" : ""} ${isActive ? "is-active" : ""}`} key={agent.agent} />;
            })}
          </div>
        </div>
        <span className="kitchen-stage__counter" aria-hidden="true"><b>{revealedCount}</b> / {agents.length} LENSES</span>
        {!loading && (complete ? onReplay : onSkip) && (
          <button
            aria-label={complete ? "분석 브리핑 애니메이션 다시 보기" : "분석 애니메이션 건너뛰기"}
            onClick={complete ? onReplay : onSkip}
            ref={!complete ? skipButtonRef : undefined}
            type="button"
          >
            {complete ? "분석 흐름 다시 보기" : "결과 바로 보기"}
          </button>
        )}
      </div>
    </section>
  );
}
