"use client";

/**
 * AI 리포트 하나를 단계적으로 공개되는 접근 가능한 분석 화면으로 변환한다.
 * 시간표는 화면 공개와 오피스 이벤트만 제어하며 점수와 근거는 백엔드 값을 그대로 사용한다.
 */

import { useQuery } from "@tanstack/react-query";
import { useEffect, useMemo, useRef, useState, type CSSProperties } from "react";
import {
  fetchAnalysisReport,
  type AIAnalysisReport,
  type ReferenceSignal,
} from "../../lib/market-api";
import { stockResultUrl } from "../../lib/share-url";
import {
  isLocalQualityEvidence,
  localConfidenceLabel,
  localEvidenceLabel,
  humanizeAnalysisText,
} from "../../lib/local-ai-presentation";
import {
  analysisAgentOrder,
  buildAnalysisSequence,
  orderedAvailableAgents,
} from "../../lib/analysis-sequence";
import { createTimedAnalysisEventStream } from "../../features/office/analysis-events";
import { useOfficeAnalysisStore } from "../../features/office/office-store";
import {
  chefMenus,
  type MeetingAgentKey,
  type MeetingPhase,
  type MeetingSceneAgent,
} from "./agent-meeting-stage";
import { AnalysisProgress, PixelAnalyst } from "./analysis-progress";
import { FinalVerdictModal } from "./final-verdict-modal";

/** 종목 식별 정보와 현재 시세를 분석 결과 화면에 전달하는 컴포넌트 입력 계약입니다. */
interface AnalysisResultProps {
  autoRun?: boolean;
  activeAgent?: string;
  symbol: string;
  name: string;
  market: string;
  currency: string;
  currentPrice?: string;
  changePercent?: string | null;
}

const signalLabels: Record<ReferenceSignal, string> = {
  positive_watch: "매수 참고 신호",
  neutral_watch: "관망",
  defensive_watch: "매도 참고 신호",
  risk_aware: "위험 우선 관망",
  data_insufficient: "데이터 부족",
};

const confidenceLabels = { low: "낮음", medium: "보통", high: "높음" };
const downsideRiskLabels = { low: "낮음", medium: "보통", high: "높음" };
const agentFocusLabels: Record<string, string> = {
  technical: "기술 분석",
  financial: "재무 분석",
  news: "뉴스·공시 분석",
  investor_flow: "수급 분석",
  risk: "위험 분석",
};

const agentLabels: Record<string, string> = {
  score: "점수 분석",
  technical: "기술 분석",
  financial: "재무 분석",
  news: "뉴스 분석",
  disclosure: "공시 분석",
  chart_pattern: "차트 패턴",
  prediction: "가격 예측",
  risk: "위험 분석",
  investor_flow: "수급 분석",
  support_resistance: "가격 구간",
};

const patternLabels: Record<string, string> = {
  doji: "도지",
  hammer: "해머",
  shooting_star: "슈팅스타",
  bullish_engulfing: "상승 장악형",
  bearish_engulfing: "하락 장악형",
  range_breakout_up: "20봉 상단 돌파",
  range_breakout_down: "20봉 하단 이탈",
  double_top_confirmed: "이중 천장 확인",
  double_bottom_confirmed: "이중 바닥 확인",
  head_and_shoulders_confirmed: "헤드앤숄더 확인",
  inverse_head_and_shoulders_confirmed: "역헤드앤숄더 확인",
  symmetrical_triangle: "대칭 삼각수렴",
  ascending_triangle: "상승 삼각수렴",
  descending_triangle: "하락 삼각수렴",
};

/** 분석 회의 애니메이션에서 현재 단계와 공개된 전문가 수를 관리하는 화면 상태입니다. */
interface MeetingPresentationState {
  announcement: string;
  complete: boolean;
  phase: MeetingPhase;
  revealedCount: number;
}

/** 전문가 한 명의 화면 표시 정보에 데이터 가용성, 근거, 실험 모델 여부를 결합한 계약입니다. */
interface MeetingEntry extends MeetingSceneAgent {
  availability: "available" | "unavailable";
  dataAsOf: string | null;
  details: string[];
  experimental: boolean;
  headline: string;
}

const unavailableCourseCopy = "사용 가능한 근거가 없어 이번 분석 관점은 종합 결과에 반영하지 않았습니다.";

/** `fallbackMeetingContent`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
function fallbackMeetingContent(report: AIAnalysisReport, agent: MeetingAgentKey) {
  switch (agent) {
    case "technical":
      return {
        details: report.key_points.slice(1, 3).map(humanizeAnalysisText),
        headline: humanizeAnalysisText(report.key_points[0] ?? report.summary),
      };
    case "financial":
      return {
        details: report.signal_basis.slice(0, 2).map(humanizeAnalysisText),
        headline: humanizeAnalysisText(report.key_points[1] ?? "재무 데이터와 밸류에이션 지표를 함께 검토했습니다."),
      };
    case "news":
      return {
        details: report.counterpoints.slice(0, 2).map(humanizeAnalysisText),
        headline: humanizeAnalysisText(report.key_points[2] ?? "뉴스와 공시에서 확인된 정형 신호를 반영했습니다."),
      };
    case "investor_flow":
      return {
        details: report.signal_basis.slice(1, 3).map(humanizeAnalysisText),
        headline: humanizeAnalysisText(report.signal_basis[0] ?? "수급과 시장 환경을 교차 검토했습니다."),
      };
    case "risk":
      return {
        details: report.risk_factors.slice(1, 3).map(humanizeAnalysisText),
        headline: humanizeAnalysisText(report.risk_factors[0] ?? "현재 확인된 주요 위험 신호가 없습니다."),
      };
  }
}

/** `meetingFromReport`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
function meetingFromReport(report: AIAnalysisReport, agent: MeetingAgentKey): MeetingEntry {
  const menu = chefMenus[agent];
  const finding = report.agent_findings?.[agent];
  const localFinding = report.local_ai_findings?.[agent];
  const reportedStatus = report.agent_status?.[agent];
  const unavailable = finding?.status === "unavailable" || reportedStatus === "unavailable";

  if (unavailable) {
    return {
      agent,
      availability: "unavailable",
      dataAsOf: finding?.data_as_of ?? null,
      details: [],
      experimental: true,
      headline: unavailableCourseCopy,
      name: menu.chefName,
      role: "이번 분석 제외",
    };
  }

  if (localFinding?.status === "available" && localFinding.probability !== null) {
    const localSignal = localFinding.signal === "positive"
      ? "긍정"
      : localFinding.signal === "negative"
        ? "부정"
        : "중립";
    const presentedEvidence = localFinding.evidence
      .map((item) => ({ item, label: localEvidenceLabel(agent, item) }))
      .filter((item): item is { item: string; label: string } => item.label !== null);
    const factEvidence = presentedEvidence
      .filter(({ item }) => !isLocalQualityEvidence(item))
      .slice(0, 3)
      .map(({ label }) => label);
    const qualityEvidence = presentedEvidence
      .filter(({ item }) => isLocalQualityEvidence(item))
      .slice(0, 2)
      .map(({ label }) => label);
    return {
      agent,
      availability: "available",
      dataAsOf: finding?.data_as_of ?? null,
      details: [
        ...factEvidence,
        ...qualityEvidence,
        `검증 모델 ${localFinding.model_version ?? "버전 미상"}`,
      ],
      experimental: false,
      headline: `${localSignal} 신호 · 신뢰도 ${localConfidenceLabel(localFinding.confidence)}`,
      name: menu.chefName,
      role: "StockPilot 자체 학습 AI",
    };
  }

  if (finding?.status === "available") {
    const evidence = finding.evidence.filter((item) => item.trim().length > 0);
    return {
      agent,
      availability: "available",
      dataAsOf: finding.data_as_of,
      details: evidence.slice(1, 4).map(humanizeAnalysisText),
      experimental: localFinding != null && localFinding.status !== "available",
      headline: humanizeAnalysisText(evidence[0] ?? "구조화된 분석 근거를 확인했습니다."),
      name: menu.chefName,
      role: menu.dish,
    };
  }

  // Older/mock report payloads can omit per-agent findings. Keep the established
  // summary fallback only when there is no explicit unavailable status to honor.
  const fallback = fallbackMeetingContent(report, agent);
  return {
    agent,
    availability: "available",
    dataAsOf: null,
    details: fallback.details,
    experimental: true,
    headline: fallback.headline,
    name: menu.chefName,
    role: "종합 리포트 요약",
  };
}

/** `useMeetingPresentation`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
function useMeetingPresentation(
  runKey: number,
  activeAgent: string | undefined,
  availableMeetings: readonly MeetingEntry[],
) {
  const [replayNonce, setReplayNonce] = useState(0);
  const [skipRunKey, setSkipRunKey] = useState<number | null>(null);
  const [presentation, setPresentation] = useState<MeetingPresentationState>({
    announcement: "분석 관점별 근거를 준비하고 있습니다.",
    complete: false,
    phase: "gathering",
    revealedCount: 0,
  });
  const shouldSkip = skipRunKey === runKey;
  const sequenceKey = availableMeetings.map((meeting) => meeting.agent).join("|");
  const activeSequence = useMemo(() => {
    return orderedAvailableAgents(sequenceKey.split("|").filter(Boolean));
  }, [sequenceKey]);
  const messageKey = availableMeetings.map((meeting) => `${meeting.agent}:${meeting.headline}`).join("|");
  const meetingMessages = useMemo(
    () => Object.fromEntries(availableMeetings.map((meeting) => [meeting.agent, meeting.headline])),
    [messageKey],
  );

  useEffect(() => {
    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const agentCount = activeSequence.length;
    const analysisId = `${runKey}-${replayNonce}`;
    const officeStore = useOfficeAnalysisStore.getState();
    const showAll = (announcement: string) => {
      setPresentation({
        announcement,
        complete: true,
        phase: "synthesis",
        revealedCount: agentCount,
      });
    };

    setPresentation({
      announcement: "분석 관점별 근거를 준비하고 있습니다.",
      complete: false,
      phase: "gathering",
      revealedCount: 0,
    });
    officeStore.begin(analysisId);

    if (shouldSkip) {
      showAll("모든 분석 근거와 종합 결과를 표시했습니다.");
      officeStore.complete(analysisId);
      return;
    }

    const steps = buildAnalysisSequence(
      activeSequence,
      reducedMotion
        ? {
            briefingMs: 250,
            courseMs: 900,
            researchDebateMs: 4200,
            tradingReviewMs: 1200,
            finalServiceMs: 1100,
          }
        : undefined,
    );
    const unsubscribe = createTimedAnalysisEventStream({ analysisId, messages: meetingMessages, steps }).subscribe((event) => {
      const store = useOfficeAnalysisStore.getState();
      if (event.type === "room_active") store.focusRoom(event.payload.room);
      if (event.type === "agent_speak") store.speak(event.payload.agent, event.payload.message);
      if (event.type === "verdict_ready") store.complete(event.payload.analysisId);
    });
    const timers = steps.map((step) => window.setTimeout(() => {
      setPresentation({
        announcement: step.complete || step.phase === activeSequence.at(-1)
          ? step.announcement
          : "분석 관점별 근거를 순서대로 확인하고 있습니다.",
        complete: step.complete,
        phase: step.phase,
        revealedCount: step.revealedCount,
      });
    }, step.atMs));

    return () => {
      timers.forEach((timer) => window.clearTimeout(timer));
      unsubscribe();
    };
  }, [activeSequence, meetingMessages, replayNonce, runKey, shouldSkip]);

  useEffect(() => {
    const requestedIndex = activeSequence.indexOf(activeAgent as MeetingAgentKey);
    if (requestedIndex < 0 || shouldSkip) return;

    setPresentation((current) => {
      if (current.revealedCount >= requestedIndex + 1) return current;
      const agent = activeSequence[requestedIndex];
      return {
        ...current,
        announcement: `${chefMenus[agent].chefName} 근거를 먼저 표시했습니다.`,
        phase: agent,
        revealedCount: requestedIndex + 1,
      };
    });
  }, [activeAgent, activeSequence, shouldSkip]);

  return {
    presentation,
    replay: () => {
      setSkipRunKey(null);
      setReplayNonce((value) => value + 1);
    },
    skip: () => setSkipRunKey(runKey),
  };
}

/** `formatLevel`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
function formatLevel(value: string | number, currency: string) {
  const number = Number(value);
  if (!Number.isFinite(number)) return String(value);
  const formatted = new Intl.NumberFormat(currency === "KRW" ? "ko-KR" : "en-US", {
    maximumFractionDigits: currency === "KRW" ? 0 : 2,
  }).format(number);
  return `${currency === "USD" ? "$" : "₩"} ${formatted}`;
}

/** `formatCurrentPrice`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
function formatCurrentPrice(value: string | undefined, currency: string) {
  if (value == null) return "—";
  return formatLevel(value, currency);
}

/** `formatChangePercent`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
function formatChangePercent(value: string | null | undefined) {
  if (value == null) return "—";
  const number = Number(value);
  if (!Number.isFinite(number)) return "—";
  return `${number >= 0 ? "+" : ""}${number.toFixed(2)}%`;
}

/** `liveStageLabel`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
function liveStageLabel(phase: MeetingPhase, complete: boolean) {
  if (complete) return "최종 판단 완료";
  if (phase === "risk" || phase === "research") return "리스크팀 검토 중";
  if (phase === "investor_flow" || phase === "trading") return "수급·가격 구간 검토 중";
  if (phase === "serving" || phase === "synthesis") return "종합 판단 정리 중";
  return "애널리스트팀 분석 중";
}

/** `analysisFreshness`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
function analysisFreshness(dataAsOf: string): { label: string; stale: boolean } {
  const timestamp = new Date(dataAsOf).getTime();
  if (!Number.isFinite(timestamp)) return { label: "분석 기준 시각을 확인할 수 없습니다.", stale: true };
  const ageMinutes = Math.max(0, Math.round((Date.now() - timestamp) / 60_000));
  if (ageMinutes <= 5) return { label: "분석 근거가 최근 5분 이내입니다.", stale: false };
  if (ageMinutes <= 60) return { label: `분석 근거 ${ageMinutes}분 전 · 필요하면 다시 분석하세요.`, stale: false };
  return { label: `분석 근거 ${Math.floor(ageMinutes / 60)}시간 전 · 최신 시세와 함께 다시 확인하세요.`, stale: true };
}

/** `Report`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
function Report({
  report,
  name,
  market,
  currency,
  currentPrice,
  changePercent,
  activeAgent = "all",
  reportUpdatedAt,
}: {
  report: AIAnalysisReport;
  name: string;
  market: string;
  currency: string;
  currentPrice?: string;
  changePercent?: string | null;
  activeAgent?: string;
  reportUpdatedAt: number;
}) {
  const [shareStatus, setShareStatus] = useState<"idle" | "shared" | "copied" | "failed">("idle");
  const reportRef = useRef<HTMLDivElement>(null);
  const score = report.overall_score ?? 0;
  const scoreStyle = { "--score-angle": `${Math.max(0, Math.min(100, score)) * 3.6}deg` } as CSSProperties;
  const signalClass = report.reference_signal.replace("_watch", "");
  const levels = report.support_resistance;
  const patterns = report.chart_patterns?.patterns ?? [];
  const change = Number(changePercent ?? 0);
  const freshness = analysisFreshness(report.data_as_of);
  const localSynthesis = report.local_ai_synthesis;
  const meetings = useMemo(
    () => analysisAgentOrder.map((agent) => meetingFromReport(report, agent)),
    [report],
  );
  const servedMeetings = meetings.filter((meeting) => meeting.availability === "available");
  const unavailableMeetings = meetings.filter((meeting) => meeting.availability === "unavailable");
  const { presentation, replay, skip } = useMeetingPresentation(
    reportUpdatedAt,
    activeAgent,
    servedMeetings,
  );
  const resultAnchorPrefix = `analysis-${report.symbol}`;
  const shareText = [
    `${name} (${report.symbol})`,
    `참고 시그널: ${signalLabels[report.reference_signal]}`,
    `종합 점수: ${score.toFixed(1)} / 100`,
    `신뢰도: ${confidenceLabels[report.confidence]}`,
    `기준 시각: ${new Date(report.data_as_of).toLocaleString("ko-KR")}`,
    report.disclaimer,
  ].join("\n");

  useEffect(() => {
    if (!presentation.complete) return;
    const frame = requestAnimationFrame(() => {
      const panel = reportRef.current?.closest<HTMLElement>(".analysis-panel");
      if (!panel) return;
      const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      panel.scrollTo({ top: 0, behavior: reduceMotion ? "auto" : "smooth" });
    });
    return () => cancelAnimationFrame(frame);
  }, [presentation.complete]);

  const copySharePayload = async (value: string) => {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(value);
      return;
    }

    const temporaryTextarea = document.createElement("textarea");
    temporaryTextarea.value = value;
    temporaryTextarea.setAttribute("readonly", "");
    temporaryTextarea.style.position = "fixed";
    temporaryTextarea.style.opacity = "0";
    document.body.appendChild(temporaryTextarea);
    temporaryTextarea.select();
    const copied = document.execCommand("copy");
    temporaryTextarea.remove();

    if (!copied) throw new Error("Clipboard access is unavailable");
  };

  const share = async () => {
    const shareUrl = stockResultUrl(report.symbol);
    const sharePayload = `${shareText}\n${shareUrl}`;

    if (navigator.share) {
      try {
        await navigator.share({ title: `${name} 참고 시그널`, text: shareText, url: shareUrl });
        setShareStatus("shared");
        return;
      } catch (reason) {
        if (reason instanceof DOMException && reason.name === "AbortError") return;
      }
    }

    try {
      await copySharePayload(sharePayload);
      setShareStatus("copied");
    } catch {
      setShareStatus("failed");
    }
  };

  return (
    <div className={`analysis-report meeting-report signal-${signalClass} active-${activeAgent}`} ref={reportRef}>
      <div className="analysis-ticker-bar" aria-label={`${name} 분석 현황`}>
        <div><b>{report.symbol}</b><span>{name}</span></div>
        <strong>{formatCurrentPrice(currentPrice, currency)}</strong>
        <em className={change < 0 ? "negative" : "positive"}>{formatChangePercent(changePercent)}</em>
        <small><i />{liveStageLabel(presentation.phase, presentation.complete)}</small>
      </div>
      <FinalVerdictModal
        currency={currency}
        currentPrice={currentPrice}
        inline
        name={name}
        open={presentation.complete}
        report={report}
        transcript={servedMeetings}
      />
      <div className="meeting-thread">
        <div className="analysis-office-layout">
          <div className="analysis-office-column">
            <AnalysisProgress
              agents={meetings}
              availableAgentKeys={servedMeetings.map((meeting) => meeting.agent)}
              complete={presentation.complete}
              onReplay={replay}
              onSkip={skip}
              phase={presentation.phase}
              revealedCount={presentation.revealedCount}
            />
          </div>
          <aside className="analysis-live-feed" aria-labelledby={`${resultAnchorPrefix}-live-feed`}>
            <header><div><span>LIVE RESEARCH FEED</span><h3 id={`${resultAnchorPrefix}-live-feed`}>실시간 분석 피드</h3></div><small>{presentation.revealedCount} / {servedMeetings.length}</small></header>
            <p className="meeting-presentation-status" role="status" aria-atomic="true" aria-live="polite">{presentation.announcement}</p>
            <div className="analysis-live-feed__items">
              {servedMeetings.slice(0, presentation.revealedCount).map((meeting) => (
                <article className={`agent-${meeting.agent}`} key={meeting.agent}>
                  <PixelAnalyst agent={meeting.agent} size="message" />
                  <div><header><b>{meeting.name}</b><span>{meeting.role}</span></header><strong>{meeting.headline}</strong><dl>{meeting.details.slice(0, 3).map((detail, index) => <div key={detail}><dt>{index + 1}</dt><dd>{detail}</dd></div>)}</dl></div>
                </article>
              ))}
              {presentation.revealedCount === 0 && <div className="analysis-live-feed__waiting"><i /><b>첫 번째 분석을 기다리고 있어요</b><span>검증된 근거가 도착하면 이곳에 계속 기록됩니다.</span></div>}
            </div>
          </aside>
        </div>

        <details className="meeting-detail-disclosure">
          <summary><span>DETAILED RESEARCH</span><b>전문 AI 근거와 반대 의견 보기</b></summary>

        {presentation.complete && (
          <nav className="analysis-jump-nav" aria-label={`${name} 분석 결과 바로가기`}>
            <span>RESULT MAP</span>
            <a href={`#${resultAnchorPrefix}-verdict`}>종합 결과</a>
            <a href={`#${resultAnchorPrefix}-evidence`}>분석 근거</a>
            {report.counterpoints.length > 0 && <a href={`#${resultAnchorPrefix}-counterpoints`}>반대 의견</a>}
            <a href={`#${resultAnchorPrefix}-footer`}>기준·면책</a>
          </nav>
        )}

        {presentation.complete && (
          <article
            /** Name 클래스는 AI 분석 진행과 결과 표현을 담당합니다.의 상태와 동작을 캡슐화합니다. */
            className={`meeting-verdict meeting-verdict--primary is-revealed ${signalClass}`}
            id={`${resultAnchorPrefix}-verdict`}
          >
            <header>
              <PixelAnalyst agent="director" size="message" />
              <div><span>FINAL VERDICT · EXPERIMENTAL</span><b>리서치 책임자 · 종합 의견</b></div>
              <div className="score-gauge" style={scoreStyle} aria-label={`종합 점수 ${score.toFixed(1)}`}>
                <div><strong>{score.toFixed(0)}</strong><small>/100</small></div>
              </div>
            </header>
            <h3>{signalLabels[report.reference_signal]}</h3>
            <p>{report.summary}</p>
            <div className="verdict-metrics">
              <span><small>현재가</small><b>{formatCurrentPrice(currentPrice, currency)}</b><em className={change < 0 ? "negative-text" : ""}>{formatChangePercent(changePercent)}</em></span>
              <span><small>분석 기간</small><b>{report.prediction_horizon_days ? `${report.prediction_horizon_days}거래일` : "단기"}</b></span>
              <span><small>하락 위험</small><b>{downsideRiskLabels[report.downside_risk]}</b></span>
              <span><small>신뢰도</small><b>{confidenceLabels[report.confidence]}</b></span>
            </div>
            {localSynthesis?.status === "available" && localSynthesis.diagnostic_score != null && (
              <section className="local-synthesis-result" aria-label="StockPilot 자체 종합 AI 결과">
                <div>
                  <span>LOCAL DIAGNOSTIC ENGINE</span>
                  <strong>
                    {localSynthesis.signal === "positive" ? "긍정" : localSynthesis.signal === "negative" ? "부정" : "중립"}
                    {" · 종합 진단 "}{Math.round(localSynthesis.diagnostic_score ?? 50)} / 100
                  </strong>
                </div>
                <dl>
                  <div><dt>진단 신뢰도</dt><dd>{localConfidenceLabel(localSynthesis.confidence)}</dd></div>
                  <div><dt>참여 전문 AI</dt><dd>{localSynthesis.available_agents} / 5</dd></div>
                  <div><dt>의견 불일치</dt><dd>{Math.round((localSynthesis.disagreement ?? 0) * 100)}%</dd></div>
                </dl>
                <small>{localSynthesis.model_version}</small>
              </section>
            )}
            {levels && (
              <div className="verdict-levels">
                <span>지지 참고선 <b>{formatLevel(levels.support, currency)}</b></span>
                <span>저항 참고선 <b>{formatLevel(levels.resistance, currency)}</b></span>
              </div>
            )}
          </article>
        )}

        {presentation.complete && (
          <div className="meeting-evidence-heading" id={`${resultAnchorPrefix}-evidence`}>
            <span>RESEARCH NOTES · EVIDENCE</span>
            <h3>관점별 판단 근거</h3>
            <p>아래 내용은 투자 자문이나 매매 지시가 아닌 참고 정보입니다.</p>
          </div>
        )}

        <div className="meeting-evidence-grid">
          {servedMeetings.slice(0, presentation.revealedCount).map((meeting) => (
            <article
              aria-labelledby={`agent-message-${meeting.agent}`}
              /** Name 클래스는 AI 분석 진행과 결과 표현을 담당합니다.의 상태와 동작을 캡슐화합니다. */
              className={`meeting-message is-revealed agent-${meeting.agent}`}
              key={meeting.name}
            >
              <PixelAnalyst agent={meeting.agent} size="message" />
              <div>
                <header><h3 id={`agent-message-${meeting.agent}`}>{meeting.name}</h3><span>{meeting.role}</span></header>
                <div className="chef-course-meta">
                  <span>{chefMenus[meeting.agent].course}</span>
                  <small>DATA · {chefMenus[meeting.agent].ingredient}</small>
                </div>
                <strong>{meeting.headline}</strong>
                {meeting.details.map((detail) => <p key={detail}>{detail}</p>)}
                {meeting.dataAsOf && <small>근거 기준 {new Date(meeting.dataAsOf).toLocaleString("ko-KR")}</small>}
              </div>
            </article>
          ))}
        </div>

        {presentation.complete && unavailableMeetings.length > 0 && (
          <section className="meeting-unavailable-courses" aria-label="이번 분석에서 제외된 관점">
            <p role="status">
              {servedMeetings.length}개 관점의 근거를 반영했으며, {unavailableMeetings.length}개 관점은 사용 가능한 데이터가 없어 제외했습니다.
            </p>
            {unavailableMeetings.map((meeting) => (
              <article
                aria-labelledby={`agent-message-${meeting.agent}`}
                /** Name 클래스는 AI 분석 진행과 결과 표현을 담당합니다.의 상태와 동작을 캡슐화합니다. */
                className={`meeting-message is-unavailable agent-${meeting.agent}`}
                key={meeting.name}
              >
                <PixelAnalyst agent={meeting.agent} size="message" />
                <div>
                  <header><h3 id={`agent-message-${meeting.agent}`}>{meeting.name}</h3><span>{meeting.role}</span></header>
                  <div className="chef-course-meta">
                    <span>{chefMenus[meeting.agent].course}</span>
                    <small>DATA · 이용 불가</small>
                  </div>
                  <strong>{meeting.headline}</strong>
                </div>
              </article>
            ))}
          </section>
        )}

        {presentation.complete && patterns.length > 0 && (
          <article aria-labelledby="agent-message-pattern" className="meeting-message is-revealed agent-technical">
            <span className="meeting-evidence-mark" aria-hidden="true" />
            <div>
              <header><h3 id="agent-message-pattern">패턴</h3><span>차트 패턴 분석가</span></header>
              <strong>{patterns.map((pattern) => patternLabels[pattern.name] ?? pattern.name).join(" · ")}</strong>
              <p>{report.chart_patterns?.reference_signals?.length ? "검증된 신호는 10일 SPY 상대 약세 참고용이며 " : ""}감지 패턴은 다른 근거와 함께 해석해야 합니다.</p>
            </div>
          </article>
        )}

        {presentation.complete && report.market_pressure && (
          <article aria-labelledby="agent-message-pressure" className="meeting-message is-revealed agent-flow">
            <span className="meeting-evidence-mark" aria-hidden="true" />
            <div>
              <header><h3 id="agent-message-pressure">주문 압력</h3><span>호가·체결 분석가</span></header>
              <strong>{{ buying: "매수세 우위", selling: "매도세 우위", balanced: "매수·매도 균형", unavailable: "계산 불가" }[report.market_pressure.signal]}</strong>
              <p>단기 압력 점수 {report.market_pressure.score > 0 ? "+" : ""}{Math.round(report.market_pressure.score * 100)} · {report.market_pressure.is_estimate ? "추정 체결 포함" : "체결 방향 확인"}</p>
            </div>
          </article>
        )}

        {presentation.complete && report.counterpoints.length > 0 && (
          <article className="meeting-counterpoint" id={`${resultAnchorPrefix}-counterpoints`}>
            <span>반대 의견</span>
            {report.counterpoints.map((point) => <p key={point}>{point}</p>)}
          </article>
        )}
        </details>
      </div>

      {presentation.complete && (
        <div className="meeting-footer" id={`${resultAnchorPrefix}-footer`}>
          <div className="agent-status-row">
            {Object.entries(report.agent_status).map(([agent, status]) => (
              <span className={status} key={agent}><i />{agentLabels[agent] ?? agent}</span>
            ))}
          </div>
          <div className="meeting-actions">
            <button className="share-result" onClick={share} type="button">결과 공유</button>
            <span className="share-status" role="status" aria-live="polite">
              {shareStatus === "shared" && "공유했습니다."}
              {shareStatus === "copied" && "복사했습니다."}
              {shareStatus === "failed" && "공유하지 못했습니다."}
            </span>
          </div>
          <p>{report.disclaimer}</p>
          <small className={`analysis-freshness ${freshness.stale ? "stale" : ""}`}>{freshness.label}</small>
          <small>{report.model_version} · {market} · {new Date(report.data_as_of).toLocaleString("ko-KR")}</small>
        </div>
      )}
    </div>
  );
}

/** `AnalysisResult`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export function AnalysisResult({
  autoRun = false,
  symbol,
  name,
  market,
  currency,
  currentPrice,
  changePercent,
  activeAgent,
}: AnalysisResultProps) {
  const panelRef = useRef<HTMLElement>(null);
  const query = useQuery({
    queryKey: ["ai-analysis", symbol],
    queryFn: ({ signal }) => fetchAnalysisReport(symbol, signal),
    enabled: autoRun,
    retry: 2,
    retryDelay: (attempt) => Math.min(1_000 * 2 ** attempt, 4_000),
  });
  const activeAgentLabel = activeAgent ? agentFocusLabels[activeAgent] : undefined;

  useEffect(() => {
    if (!activeAgent || activeAgent === "all" || !query.data) return;
    const scrollToAgent = () => {
      const target = panelRef.current?.querySelector<HTMLElement>(`.agent-${activeAgent}`);
      if (!target) return;
      const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      target.scrollIntoView({ behavior: reduceMotion ? "auto" : "smooth", block: "nearest" });
    };
    const timer = window.setTimeout(scrollToAgent, 80);
    return () => window.clearTimeout(timer);
  }, [activeAgent, query.data, query.dataUpdatedAt]);

  return (
    <section
      aria-busy={query.isFetching}
      aria-labelledby={`analysis-title-${symbol}`}
      aria-label={`${name} AI 분석`}
      /** Name 클래스는 AI 분석 진행과 결과 표현을 담당합니다.의 상태와 동작을 캡슐화합니다. */
      className="analysis-panel"
      ref={panelRef}
      role="region"
      tabIndex={0}
    >
      <header className="meeting-heading">
        <div>
          <span>ANALYSIS LOG · {symbol}</span>
          <h2 id={`analysis-title-${symbol}`}>AI 리서치</h2>
        </div>
        <small className={query.isFetching ? "working" : "complete"}><i />{query.isFetching ? "분석 근거 확인 중" : "분석 준비 완료"}</small>
        <button onClick={() => query.refetch()} disabled={query.isFetching} type="button">
          {query.isFetching ? "분석 중…" : query.data ? "다시 분석" : "분석 시작"}
        </button>
      </header>
      <p className="meeting-focus-status" role="status" aria-live="polite">
        {activeAgentLabel ? `${activeAgentLabel} 의견을 강조합니다.` : "모든 에이전트 의견을 표시합니다."}
      </p>

      {!query.data && !query.isFetching && !query.isError && (
        <div className="analysis-empty">
          <div className="agent-orbit" aria-hidden="true"><i>차트</i><i>뉴스</i><b>AI</b><i>수급</i><i>위험</i></div>
          <div className="analysis-empty-copy">
            <span>READY TO SCAN · {market}</span>
            <strong>{name}의 참고 시그널을 생성합니다.</strong>
            <p>종합 점수, 상승 확률, 위험도, 지지·저항 구간과 반대 의견까지 함께 표시합니다.</p>
            <div><i>01 데이터 수집</i><i>02 교차 분석</i><i>03 준법 검증</i></div>
            <nav aria-label="예시 종목"><a href="/?symbol=AAPL">애플</a><a href="/?symbol=005930">삼성전자</a><a href="/?symbol=SPY">SPY ETF</a></nav>
          </div>
        </div>
      )}
      {query.isPending && (
        <div className="analysis-loading meeting-loading">
          <AnalysisProgress
            agents={[
              { agent: "technical", name: "차트", role: "테크니컬 애널리스트" },
              { agent: "financial", name: "재무", role: "기업 분석가" },
              { agent: "news", name: "민심", role: "뉴스·공시 애널리스트" },
              { agent: "investor_flow", name: "수급", role: "플로우 애널리스트" },
              { agent: "risk", name: "위험", role: "리스크 매니저" },
            ]}
            complete={false}
            loading
            phase="gathering"
            revealedCount={0}
          />
          <div className="meeting-loading-copy" role="status" aria-atomic="true" aria-live="polite">
            <strong>분석을 준비하고 있습니다</strong>
            <span>공개 자료와 저장된 정형 데이터를 교차 확인하고 있습니다.</span>
            <ol aria-label="분석 진행 단계"><li>데이터 확인</li><li>관점별 분석</li><li>근거 종합</li></ol>
          </div>
        </div>
      )}
      {query.isError && !query.data && <div className="analysis-error" role="alert"><b>분석을 완료하지 못했습니다.</b><span>{query.error.message}</span><button onClick={() => query.refetch()} type="button">재시도</button></div>}
      {query.data && (
        <Report
          report={query.data}
          name={name}
          market={market}
          currency={currency}
          currentPrice={currentPrice}
          changePercent={changePercent}
          activeAgent={activeAgent}
          reportUpdatedAt={query.dataUpdatedAt}
        />
      )}
      {query.isError && query.data && (
        <div className="analysis-refresh-error" role="status">
          최신 분석을 불러오지 못해 이전 결과를 유지하고 있습니다.
          <button onClick={() => query.refetch()} type="button">다시 시도</button>
        </div>
      )}
    </section>
  );
}
