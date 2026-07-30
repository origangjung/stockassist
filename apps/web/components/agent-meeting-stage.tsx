"use client";

import {
  useEffect,
  useId,
  useRef,
  type KeyboardEvent as ReactKeyboardEvent,
  type RefObject,
} from "react";

export type MeetingAgentKey = "technical" | "financial" | "news" | "investor_flow" | "risk";
export type MeetingPhase = MeetingAgentKey | "gathering" | "serving" | "synthesis";

export interface MeetingSceneAgent {
  agent: MeetingAgentKey;
  name: string;
  role: string;
}

export interface ChefMenu {
  chefName: string;
  course: string;
  dish: string;
  ingredient: string;
}

export const chefMenus: Record<MeetingAgentKey, ChefMenu> = {
  technical: {
    chefName: "차트 셰프",
    course: "COURSE 01 · TREND SAUCE",
    dish: "추세 소스",
    ingredient: "캔들 · 거래량 · 기술 지표",
  },
  financial: {
    chefName: "재무 셰프",
    course: "COURSE 02 · VALUE BROTH",
    dish: "가치 육수",
    ingredient: "실적 · 재무 구조 · 밸류에이션",
  },
  news: {
    chefName: "뉴스·공시 셰프",
    course: "COURSE 03 · EVENT GARNISH",
    dish: "이슈 가니시",
    ingredient: "뉴스 · 공시 · 시장 반응",
  },
  investor_flow: {
    chefName: "수급 셰프",
    course: "COURSE 04 · FLOW REDUCTION",
    dish: "수급 리덕션",
    ingredient: "투자자 흐름 · 시장 환경",
  },
  risk: {
    chefName: "리스크 셰프",
    course: "COURSE 05 · RISK CHECK",
    dish: "안전 점검 코스",
    ingredient: "경고 신호 · 반대 근거 · 위험 요인",
  },
};

interface AnalystAvatarProps {
  agent: MeetingAgentKey | "master";
  size?: "message" | "roster" | "scene";
}

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

function sceneMessage({ agents, phase, complete, loading }: AgentMeetingStageProps) {
  const courseCount = agents.length;
  if (loading) {
    return {
      eyebrow: "STOCKPILOT OPEN KITCHEN · INGREDIENT PREP",
      title: "AI 셰프들이 분석 재료를 정리하고 있습니다.",
      detail: "음식 비유는 분석 진행을 보여주기 위한 연출이며, 실제 근거와 결과는 이어지는 분석 카드에서 확인할 수 있습니다.",
    };
  }

  if (complete) {
    return {
      eyebrow: "STOCKPILOT OPEN KITCHEN · SERVICE COMPLETE",
      title: `${courseCount}개 분석 코스의 최종 서빙이 완료되었습니다.`,
      detail: "종합 결과와 반대 근거를 함께 확인하세요. 아래 내용은 투자 자문이나 매매 지시가 아닌 참고 정보입니다.",
    };
  }

  if (phase === "serving") {
    return {
      eyebrow: "STOCKPILOT OPEN KITCHEN · FINAL SERVICE",
      title: "완성된 코스를 중앙 패스로 모아 최종 서빙하고 있습니다.",
      detail: "서빙이 끝나면 종합 참고 신호와 위험·반대 근거가 함께 이어집니다.",
    };
  }

  if (phase === "gathering") {
    return {
      eyebrow: "STOCKPILOT OPEN KITCHEN · CHEF BRIEFING",
      title: courseCount > 0
        ? `${courseCount}명의 셰프가 각자의 분석 코스를 준비합니다.`
        : "현재 제공 가능한 분석 코스를 확인하고 있습니다.",
      detail: "각 코스는 실제 분석 근거를 순서대로 플레이팅하는 시각적 비유입니다.",
    };
  }

  const currentAgent = agents.find((agent) => agent.agent === phase);
  const menu = currentAgent ? chefMenus[currentAgent.agent] : undefined;
  return {
    eyebrow: menu?.course ?? "STOCKPILOT OPEN KITCHEN · PLATING",
    title: `${menu?.chefName ?? currentAgent?.name ?? "담당 셰프"}가 ${menu?.dish ?? "분석 코스"}를 플레이팅합니다.`,
    detail: "음식 이름은 진행 비유이며, 실제 분석 문장과 근거는 아래 카드에 그대로 표시됩니다.",
  };
}

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
    ? "분석 재료를 확인하는 중"
    : complete
      ? "모든 코스 서빙 완료"
      : phase === "serving"
        ? "총괄 셰프가 최종 결과를 서빙하는 중"
      : phase === "gathering"
        ? "셰프 브리핑 진행 중"
        : phase === "synthesis"
          ? "각 코스 근거를 종합하는 중"
        : `${chefMenus[phase].chefName} · ${chefMenus[phase].dish} 준비 중`;

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
          <span className="scene-analyst__label">총괄 셰프</span>
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
        <span className="kitchen-stage__counter" aria-hidden="true"><b>{revealedCount}</b> / {agents.length} COURSES</span>
        {!loading && (complete ? onReplay : onSkip) && (
          <button
            aria-label={complete ? "주방 브리핑 애니메이션 다시 보기" : "분석 코스 애니메이션 건너뛰기"}
            onClick={complete ? onReplay : onSkip}
            ref={!complete ? skipButtonRef : undefined}
            type="button"
          >
            {complete ? "주방 브리핑 다시 보기" : "애니메이션 건너뛰기"}
          </button>
        )}
      </div>
    </section>
  );
}
