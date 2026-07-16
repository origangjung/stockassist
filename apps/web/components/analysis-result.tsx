"use client";

import { useQuery } from "@tanstack/react-query";
import type { CSSProperties } from "react";
import {
  fetchAnalysisReport,
  type AIAnalysisReport,
  type ReferenceSignal,
} from "../lib/market-api";

interface AnalysisResultProps {
  symbol: string;
  name: string;
  currency: string;
}

const signalLabels: Record<ReferenceSignal, string> = {
  positive_watch: "매수 참고 신호",
  neutral_watch: "관망",
  defensive_watch: "매도 참고 신호",
  risk_aware: "위험 우선 관망",
  data_insufficient: "데이터 부족",
};

const confidenceLabels = { low: "낮음", medium: "보통", high: "높음" };

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

function DetailList({ title, items, tone }: { title: string; items: string[]; tone?: string }) {
  return (
    <article className={`analysis-detail ${tone ?? ""}`}>
      <h4>{title}</h4>
      <ul>{items.map((item) => <li key={item}>{item}</li>)}</ul>
    </article>
  );
}

function Report({ report, currency }: { report: AIAnalysisReport; currency: string }) {
  const score = report.overall_score ?? 0;
  const scoreStyle = { "--score-angle": `${Math.max(0, Math.min(100, score)) * 3.6}deg` } as CSSProperties;
  const signalClass = report.reference_signal.replace("_watch", "");
  const levels = report.support_resistance;
  const patterns = report.chart_patterns?.patterns ?? [];

  return (
    <div className="analysis-report">
      <div className={`signal-summary ${signalClass}`}>
        <div>
          <span className="experimental-badge">EXPERIMENTAL REFERENCE SIGNAL</span>
          <h3>{signalLabels[report.reference_signal]}</h3>
          <p>{report.summary}</p>
          <div className="signal-meta">
            <span>신뢰도 {confidenceLabels[report.confidence]}</span>
            <span>신호 강도 {report.signal_strength.toFixed(0)}%</span>
            <span>{report.prediction_horizon_days ?? 5}일 관점</span>
          </div>
        </div>
        <div className="score-gauge" style={scoreStyle} aria-label={`종합 점수 ${score.toFixed(1)}`}>
          <div><strong>{score.toFixed(1)}</strong><small>/ 100</small></div>
        </div>
      </div>

      <div className="analysis-metrics">
        <article><span>상승 확률</span><strong>{formatPercent(report.rise_probability)}</strong><small>실험 모델 추정치</small></article>
        <article><span>분석 범위</span><strong>{report.score_coverage === null ? "—" : `${(report.score_coverage * 100).toFixed(0)}%`}</strong><small>6개 점수 축 가용 비율</small></article>
        <article><span>하락 위험도</span><strong>{report.downside_risk.toUpperCase()}</strong><small>{report.risk_warnings.length}개 투자유의 신호</small></article>
      </div>

      {levels && (
        <div className="reference-levels">
          <div><span>하방 이탈 참고선</span><strong>{formatLevel(levels.support, currency)}</strong><small>최근 20개 캔들 지지 구간</small></div>
          <div className="level-track"><i /><b /></div>
          <div><span>상방 저항 참고선</span><strong>{formatLevel(levels.resistance, currency)}</strong><small>최근 20개 캔들 저항 구간</small></div>
        </div>
      )}

      <div className="signal-basis">
        <h4>신호 계산 근거</h4>
        <div>{report.signal_basis.map((item, index) => <span key={item}><b>{index + 1}</b>{item}</span>)}</div>
      </div>

      {patterns.length > 0 && (
        <div className="signal-basis">
          <h4>감지된 실험 패턴</h4>
          <div>
            {patterns.map((pattern) => (
              <span key={`${pattern.name}-${pattern.ended_at}`}>
                <b>{Math.round(pattern.confidence * 100)}</b>
                {patternLabels[pattern.name] ?? pattern.name} · {pattern.direction}
              </span>
            ))}
          </div>
        </div>
      )}

      <div className="analysis-detail-grid">
        <DetailList title="핵심 근거" items={report.key_points} />
        <DetailList title="위험 요소" items={report.risk_factors} tone="risk" />
        <DetailList title="반대 의견" items={report.counterpoints} tone="counter" />
      </div>

      <div className="agent-status-row">
        {Object.entries(report.agent_status).map(([agent, status]) => (
          <span className={status} key={agent}><i />{agentLabels[agent] ?? agent}</span>
        ))}
      </div>

      <footer className="analysis-compliance">
        <div><b>Compliance passed</b><span>{report.model_version} • {new Date(report.data_as_of).toLocaleString("ko-KR")}</span></div>
        <p>{report.disclaimer}</p>
      </footer>
    </div>
  );
}

export function AnalysisResult({ symbol, name, currency }: AnalysisResultProps) {
  const query = useQuery({
    queryKey: ["ai-analysis", symbol],
    queryFn: () => fetchAnalysisReport(symbol),
    enabled: false,
    retry: false,
  });

  return (
    <section className="analysis-panel">
      <header className="analysis-panel-heading">
        <div><span className="label">MULTI-AGENT DECISION SUPPORT</span><h2>{name} AI 종합 분석</h2><p>점수·예측·수급·위험 에이전트의 계산 결과를 통합합니다.</p></div>
        <button onClick={() => query.refetch()} disabled={query.isFetching}>
          {query.isFetching ? "에이전트 분석 중…" : query.data ? "다시 분석" : "AI 분석 실행"}
        </button>
      </header>

      {!query.data && !query.isFetching && !query.isError && (
        <div className="analysis-empty">
          <div className="agent-orbit" aria-hidden="true"><i>차트</i><i>뉴스</i><b>AI</b><i>수급</i><i>위험</i></div>
          <div><strong>분석 에이전트가 대기 중입니다.</strong><span>실행하면 계산된 근거와 참고 신호를 확인할 수 있습니다.</span></div>
        </div>
      )}
      {query.isFetching && <div className="analysis-loading"><i /><span>각 분석 에이전트의 결과를 취합하고 있습니다.</span></div>}
      {query.isError && <div className="analysis-error"><b>분석을 완료하지 못했습니다.</b><span>{query.error.message}</span><button onClick={() => query.refetch()}>재시도</button></div>}
      {query.data && !query.isFetching && <Report report={query.data} currency={currency} />}
    </section>
  );
}
