"use client";

import { useQuery } from "@tanstack/react-query";
import { useEffect, useMemo, useRef, useState, type CSSProperties } from "react";
import {
  fetchAnalysisReport,
  type AIAnalysisReport,
  type ReferenceSignal,
} from "../lib/market-api";
import { stockResultUrl } from "../lib/share-url";
import {
  AgentMeetingStage,
  AnalystAvatar,
  chefMenus,
  type MeetingAgentKey,
  type MeetingPhase,
  type MeetingSceneAgent,
} from "./agent-meeting-stage";

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
  technical: "차트 셰프",
  financial: "재무 셰프",
  news: "뉴스·공시 셰프",
  investor_flow: "수급 셰프",
  risk: "리스크 셰프",
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
};

const meetingSequence: MeetingAgentKey[] = ["technical", "financial", "news", "investor_flow", "risk"];

// Keep the visual kitchen choreography and the result-card reveal on one shared timeline.
const KITCHEN_TIMING = {
  briefingMs: 650,
  courseMs: 1120,
  finalServiceMs: 1250,
} as const;

interface MeetingPresentationState {
  announcement: string;
  complete: boolean;
  phase: MeetingPhase;
  revealedCount: number;
}

interface MeetingEntry extends MeetingSceneAgent {
  availability: "available" | "unavailable";
  dataAsOf: string | null;
  details: string[];
  headline: string;
}

const unavailableCourseCopy = "사용 가능한 근거가 없어 이번 분석 코스는 종합 결과에 반영하지 않았습니다.";

function fallbackMeetingContent(report: AIAnalysisReport, agent: MeetingAgentKey) {
  switch (agent) {
    case "technical":
      return {
        details: report.key_points.slice(1, 3),
        headline: report.key_points[0] ?? report.summary,
      };
    case "financial":
      return {
        details: report.signal_basis.slice(0, 2),
        headline: report.key_points[1] ?? "재무 데이터와 밸류에이션 지표를 함께 검토했습니다.",
      };
    case "news":
      return {
        details: report.counterpoints.slice(0, 2),
        headline: report.key_points[2] ?? "뉴스와 공시에서 확인된 정형 신호를 반영했습니다.",
      };
    case "investor_flow":
      return {
        details: report.signal_basis.slice(1, 3),
        headline: report.signal_basis[0] ?? "수급과 시장 환경을 교차 검토했습니다.",
      };
    case "risk":
      return {
        details: report.risk_factors.slice(1, 3),
        headline: report.risk_factors[0] ?? "현재 확인된 주요 위험 신호가 없습니다.",
      };
  }
}

function meetingFromReport(report: AIAnalysisReport, agent: MeetingAgentKey): MeetingEntry {
  const menu = chefMenus[agent];
  const finding = report.agent_findings?.[agent];
  const reportedStatus = report.agent_status?.[agent];
  const unavailable = finding?.status === "unavailable" || reportedStatus === "unavailable";

  if (unavailable) {
    return {
      agent,
      availability: "unavailable",
      dataAsOf: finding?.data_as_of ?? null,
      details: [],
      headline: unavailableCourseCopy,
      name: menu.chefName,
      role: "이번 코스 제외",
    };
  }

  if (finding?.status === "available") {
    const evidence = finding.evidence.filter((item) => item.trim().length > 0);
    return {
      agent,
      availability: "available",
      dataAsOf: finding.data_as_of,
      details: evidence.slice(1, 4),
      headline: evidence[0] ?? "구조화된 분석 근거를 확인했습니다.",
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
    headline: fallback.headline,
    name: menu.chefName,
    role: "종합 리포트 요약",
  };
}

function useMeetingPresentation(
  runKey: number,
  activeAgent: string | undefined,
  availableAgentKeys: readonly MeetingAgentKey[],
) {
  const [replayNonce, setReplayNonce] = useState(0);
  const [skipRunKey, setSkipRunKey] = useState<number | null>(null);
  const [presentation, setPresentation] = useState<MeetingPresentationState>({
    announcement: "AI 셰프들이 분석 코스를 준비하고 있습니다.",
    complete: false,
    phase: "gathering",
    revealedCount: 0,
  });
  const shouldSkip = skipRunKey === runKey;
  const sequenceKey = availableAgentKeys.join("|");
  const activeSequence = useMemo(() => {
    const available = new Set(sequenceKey.split("|").filter(Boolean));
    return meetingSequence.filter((agent) => available.has(agent));
  }, [sequenceKey]);

  useEffect(() => {
    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const agentCount = activeSequence.length;
    const showAll = (announcement: string) => {
      setPresentation({
        announcement,
        complete: true,
        phase: "synthesis",
        revealedCount: agentCount,
      });
    };

    setPresentation({
      announcement: "AI 셰프들이 분석 코스를 준비하고 있습니다.",
      complete: false,
      phase: "gathering",
      revealedCount: 0,
    });

    if (agentCount === 0) {
      showAll("사용 가능한 분석 코스가 없어 종합 참고 결과만 표시합니다.");
      return;
    }

    if (reducedMotion || shouldSkip) {
      showAll(
        reducedMotion
          ? `${agentCount}개 분석 코스와 최종 서빙 결과를 표시했습니다.`
          : "모든 분석 코스와 최종 서빙 결과를 표시했습니다.",
      );
      return;
    }

    const timers = activeSequence.map((agent, index) => window.setTimeout(() => {
      setPresentation((current) => {
        if (current.revealedCount > index + 1) return current;
        return {
          // Avoid queuing five rapid polite announcements while the visual scene still progresses.
          announcement: index === agentCount - 1
            ? `${index + 1}/${agentCount} ${chefMenus[agent].chefName}의 ${chefMenus[agent].dish} 코스가 준비되었습니다.`
            : current.announcement,
          complete: false,
          phase: agent,
          revealedCount: index + 1,
        };
      });
    }, KITCHEN_TIMING.briefingMs + index * KITCHEN_TIMING.courseMs));

    const servingStart = KITCHEN_TIMING.briefingMs + agentCount * KITCHEN_TIMING.courseMs;
    timers.push(window.setTimeout(() => {
      setPresentation({
        announcement: `${agentCount}개 분석 코스를 한 접시에 담아 최종 서빙하고 있습니다.`,
        complete: false,
        phase: "serving",
        revealedCount: agentCount,
      });
    }, servingStart));
    timers.push(window.setTimeout(() => {
      showAll("서빙이 완료되었습니다. 종합 참고 결과와 반대 의견을 표시합니다.");
    }, servingStart + KITCHEN_TIMING.finalServiceMs));

    return () => timers.forEach((timer) => window.clearTimeout(timer));
  }, [activeSequence, replayNonce, runKey, shouldSkip]);

  useEffect(() => {
    const requestedIndex = activeSequence.indexOf(activeAgent as MeetingAgentKey);
    if (requestedIndex < 0 || shouldSkip) return;

    setPresentation((current) => {
      if (current.revealedCount >= requestedIndex + 1) return current;
      const agent = activeSequence[requestedIndex];
      return {
        ...current,
        announcement: `${chefMenus[agent].chefName}의 ${chefMenus[agent].dish} 코스를 먼저 표시했습니다.`,
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

function formatPercent(value: string | number | null) {
  if (value === null) return "—";
  const number = Number(value);
  return Number.isFinite(number) ? `${(number * 100).toFixed(1)}%` : "—";
}

function formatLevel(value: string | number, currency: string) {
  const number = Number(value);
  if (!Number.isFinite(number)) return String(value);
  const formatted = new Intl.NumberFormat(currency === "KRW" ? "ko-KR" : "en-US", {
    maximumFractionDigits: currency === "KRW" ? 0 : 2,
  }).format(number);
  return `${currency === "USD" ? "$" : "₩"} ${formatted}`;
}

function formatCurrentPrice(value: string | undefined, currency: string) {
  if (value == null) return "—";
  return formatLevel(value, currency);
}

function formatChangePercent(value: string | null | undefined) {
  if (value == null) return "—";
  const number = Number(value);
  if (!Number.isFinite(number)) return "—";
  return `${number >= 0 ? "+" : ""}${number.toFixed(2)}%`;
}

function analysisFreshness(dataAsOf: string): { label: string; stale: boolean } {
  const timestamp = new Date(dataAsOf).getTime();
  if (!Number.isFinite(timestamp)) return { label: "분석 기준 시각을 확인할 수 없습니다.", stale: true };
  const ageMinutes = Math.max(0, Math.round((Date.now() - timestamp) / 60_000));
  if (ageMinutes <= 5) return { label: "분석 근거가 최근 5분 이내입니다.", stale: false };
  if (ageMinutes <= 60) return { label: `분석 근거 ${ageMinutes}분 전 · 필요하면 다시 조리하세요.`, stale: false };
  return { label: `분석 근거 ${Math.floor(ageMinutes / 60)}시간 전 · 최신 시세와 함께 다시 확인하세요.`, stale: true };
}

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
  const score = report.overall_score ?? 0;
  const scoreStyle = { "--score-angle": `${Math.max(0, Math.min(100, score)) * 3.6}deg` } as CSSProperties;
  const signalClass = report.reference_signal.replace("_watch", "");
  const levels = report.support_resistance;
  const patterns = report.chart_patterns?.patterns ?? [];
  const change = Number(changePercent ?? 0);
  const freshness = analysisFreshness(report.data_as_of);
  const meetings = useMemo(
    () => meetingSequence.map((agent) => meetingFromReport(report, agent)),
    [report],
  );
  const servedMeetings = meetings.filter((meeting) => meeting.availability === "available");
  const unavailableMeetings = meetings.filter((meeting) => meeting.availability === "unavailable");
  const { presentation, replay, skip } = useMeetingPresentation(
    reportUpdatedAt,
    activeAgent,
    servedMeetings.map((meeting) => meeting.agent),
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
    <div className={`analysis-report meeting-report signal-${signalClass} active-${activeAgent}`}>
      <div className="meeting-thread">
        <AgentMeetingStage
          agents={servedMeetings}
          complete={presentation.complete}
          onReplay={replay}
          onSkip={skip}
          phase={presentation.phase}
          revealedCount={presentation.revealedCount}
        />
        <p className="meeting-presentation-status" role="status" aria-atomic="true" aria-live="polite">
          {presentation.announcement}
        </p>

        {presentation.complete && (
          <nav className="analysis-jump-nav" aria-label={`${name} 분석 결과 바로가기`}>
            <span>RESULT MAP</span>
            <a href={`#${resultAnchorPrefix}-verdict`}>종합 결과</a>
            <a href={`#${resultAnchorPrefix}-evidence`}>코스 근거</a>
            {report.counterpoints.length > 0 && <a href={`#${resultAnchorPrefix}-counterpoints`}>반대 의견</a>}
            <a href={`#${resultAnchorPrefix}-footer`}>기준·면책</a>
          </nav>
        )}

        {presentation.complete && (
          <article
            className={`meeting-verdict meeting-verdict--primary is-revealed ${signalClass}`}
            id={`${resultAnchorPrefix}-verdict`}
          >
            <header>
              <div><span>FINAL SERVICE · EXPERIMENTAL</span><b>{name} 종합 참고 코스</b></div>
              <div className="score-gauge" style={scoreStyle} aria-label={`종합 점수 ${score.toFixed(1)}`}>
                <div><strong>{score.toFixed(0)}</strong><small>/100</small></div>
              </div>
            </header>
            <h3>{signalLabels[report.reference_signal]}</h3>
            <p>{report.summary}</p>
            <div className="verdict-metrics">
              <span><small>현재가</small><b>{formatCurrentPrice(currentPrice, currency)}</b><em className={change < 0 ? "negative-text" : ""}>{formatChangePercent(changePercent)}</em></span>
              <span><small>상승 확률</small><b>{formatPercent(report.rise_probability)}</b></span>
              <span><small>하락 위험</small><b>{downsideRiskLabels[report.downside_risk]}</b></span>
              <span><small>신뢰도</small><b>{confidenceLabels[report.confidence]}</b></span>
            </div>
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
            <span>CHEF NOTES · EVIDENCE</span>
            <h3>코스별 판단 근거</h3>
            <p>음식 비유는 분석 과정을 설명하기 위한 연출입니다. 아래 내용은 투자 자문이나 매매 지시가 아닌 참고 정보입니다.</p>
          </div>
        )}

        {servedMeetings.slice(0, presentation.revealedCount).map((meeting) => (
          <article
            aria-labelledby={`agent-message-${meeting.agent}`}
            className={`meeting-message is-revealed agent-${meeting.agent}`}
            key={meeting.name}
          >
            <AnalystAvatar agent={meeting.agent} />
            <div>
              <div className="chef-course-meta">
                <span>{chefMenus[meeting.agent].course}</span>
                <b>{chefMenus[meeting.agent].dish}</b>
                <small>분석 재료 · {chefMenus[meeting.agent].ingredient}</small>
              </div>
              <header><h3 id={`agent-message-${meeting.agent}`}>{meeting.name}</h3><span>{meeting.role}</span></header>
              <strong>{meeting.headline}</strong>
              {meeting.details.map((detail) => <p key={detail}>{detail}</p>)}
              {meeting.dataAsOf && <small>근거 기준 {new Date(meeting.dataAsOf).toLocaleString("ko-KR")}</small>}
            </div>
          </article>
        ))}

        {presentation.complete && unavailableMeetings.length > 0 && (
          <section className="meeting-unavailable-courses" aria-label="이번 분석에서 제외된 코스">
            <p role="status">
              {servedMeetings.length}개 코스의 근거를 반영했으며, {unavailableMeetings.length}개 코스는 사용 가능한 데이터가 없어 제외했습니다.
            </p>
            {unavailableMeetings.map((meeting) => (
              <article
                aria-labelledby={`agent-message-${meeting.agent}`}
                className={`meeting-message is-unavailable agent-${meeting.agent}`}
                key={meeting.name}
              >
                <AnalystAvatar agent={meeting.agent} />
                <div>
                  <div className="chef-course-meta">
                    <span>{chefMenus[meeting.agent].course}</span>
                    <b>{chefMenus[meeting.agent].dish}</b>
                    <small>분석 재료 · 이용 불가</small>
                  </div>
                  <header><h3 id={`agent-message-${meeting.agent}`}>{meeting.name}</h3><span>{meeting.role}</span></header>
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
              <p>감지 패턴은 실험 상태이며 다른 근거와 함께 해석해야 합니다.</p>
            </div>
          </article>
        )}

        {presentation.complete && report.counterpoints.length > 0 && (
          <article className="meeting-counterpoint" id={`${resultAnchorPrefix}-counterpoints`}>
            <span>반대 의견</span>
            {report.counterpoints.map((point) => <p key={point}>{point}</p>)}
          </article>
        )}
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
    retry: false,
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
      aria-label={`${name} AI 셰프 키친 분석 코스`}
      className="analysis-panel"
      ref={panelRef}
      role="region"
      tabIndex={0}
    >
      <header className="meeting-heading">
        <div>
          <span>KITCHEN LOG · {symbol}</span>
          <h2 id={`analysis-title-${symbol}`}>AI 셰프 키친</h2>
        </div>
        <small className={query.isFetching ? "working" : "complete"}><i />{query.isFetching ? "셰프팀 분석 준비 중" : "서빙 준비 완료"}</small>
        <button onClick={() => query.refetch()} disabled={query.isFetching} type="button">
          {query.isFetching ? "조리 중…" : query.data ? "다시 조리" : "코스 시작"}
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
          </div>
        </div>
      )}
      {query.isPending && (
        <div className="analysis-loading meeting-loading">
          <AgentMeetingStage
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
            <strong>AI 셰프 키친 준비 중</strong>
            <span>공개 자료와 저장된 정형 데이터를 분석 재료로 교차 확인하고 있습니다.</span>
            <ol aria-label="분석 진행 단계"><li>재료 확인</li><li>코스 준비</li><li>플레이팅</li></ol>
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
