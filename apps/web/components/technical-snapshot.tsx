"use client";

import { useQuery } from "@tanstack/react-query";
import {
  fetchPatternAnalysis,
  fetchTechnicalAnalysis,
  type DetectedPattern,
  type IndicatorPoint,
} from "../lib/market-api";

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

const directionLabels: Record<DetectedPattern["direction"], string> = {
  upward: "상향",
  downward: "하향",
  neutral: "중립",
};

function number(value: number | null | undefined, digits = 2) {
  return value == null || !Number.isFinite(value)
    ? "—"
    : new Intl.NumberFormat("ko-KR", { maximumFractionDigits: digits }).format(value);
}

function price(value: number | null | undefined, currency: string) {
  if (value == null || !Number.isFinite(value)) return "—";
  const formatted = new Intl.NumberFormat(currency === "KRW" ? "ko-KR" : "en-US", {
    maximumFractionDigits: currency === "KRW" ? 0 : 2,
  }).format(value);
  return `${currency === "USD" ? "$" : "₩"} ${formatted}`;
}

function latestValues(latest: IndicatorPoint) {
  return [
    { label: "RSI 14", value: number(latest.rsi_14), hint: "0–100 상대강도" },
    { label: "MACD 히스토그램", value: number(latest.macd_histogram, 4), hint: "추세 모멘텀 차이" },
    { label: "ADX 14", value: number(latest.adx_14), hint: "추세 강도" },
    { label: "MFI 14", value: number(latest.mfi_14), hint: "가격·거래량 자금 흐름" },
    { label: "ATR 14", value: latest.atr_14, hint: "평균 변동 범위", isPrice: true },
    {
      label: "SuperTrend",
      value: latest.supertrend_direction == null
        ? "—"
        : latest.supertrend_direction > 0 ? "상향 추세" : "하향 추세",
      hint: "10기간 · 3배 ATR",
    },
  ];
}

export function TechnicalSnapshot({ symbol, currency }: { symbol: string; currency: string }) {
  const technical = useQuery({
    queryKey: ["technical", symbol],
    queryFn: () => fetchTechnicalAnalysis(symbol),
    staleTime: 60_000,
    retry: 1,
  });
  const patterns = useQuery({
    queryKey: ["patterns", symbol],
    queryFn: () => fetchPatternAnalysis(symbol),
    staleTime: 60_000,
    retry: 1,
  });
  const latest = technical.data?.indicators.at(-1);
  const detected = patterns.data
    ? [...patterns.data.patterns]
        .sort((left, right) => right.ended_at.localeCompare(left.ended_at))
        .slice(0, 6)
    : [];
  const loading = technical.isPending || patterns.isPending;
  const failed = technical.isError || patterns.isError;

  return (
    <section className="technical-snapshot">
      <header>
        <div><span>DETERMINISTIC ANALYSIS</span><h3>기술지표 · 패턴 스냅샷</h3></div>
        <small>EXPERIMENTAL · 계산 결과는 참고 정보입니다.</small>
      </header>

      {loading && <div className="technical-state">기술 계산 결과를 불러오는 중입니다.</div>}
      {failed && (
        <div className="technical-state error">
          <span>기술지표 또는 패턴 결과를 불러오지 못했습니다.</span>
          <button onClick={() => { void technical.refetch(); void patterns.refetch(); }} type="button">다시 시도</button>
        </div>
      )}
      {!loading && !failed && latest && (
        <>
          <div className="technical-metrics">
            {latestValues(latest).map((metric) => (
              <article key={metric.label}>
                <span>{metric.label}</span>
                <strong>{metric.isPrice ? price(metric.value as number | null, currency) : metric.value}</strong>
                <small>{metric.hint}</small>
              </article>
            ))}
          </div>
          <div className="pattern-strip">
            <div><b>최근 감지 패턴</b><span>{patterns.data?.engine_version}</span></div>
            {detected.length === 0 && <p>현재 분석 구간에서 감지된 패턴이 없습니다.</p>}
            {detected.map((pattern) => (
              <article className={pattern.direction} key={`${pattern.name}-${pattern.ended_at}`}>
                <span>{directionLabels[pattern.direction]}</span>
                <b>{patternLabels[pattern.name] ?? pattern.name}</b>
                <small>규칙 강도 {Math.round(pattern.confidence * 100)} · {new Date(pattern.ended_at).toLocaleDateString("ko-KR")}</small>
              </article>
            ))}
          </div>
          <footer>
            <span>{technical.data?.provider} · {technical.data?.engine_version}</span>
            <span>기준 {new Date(latest.timestamp).toLocaleString("ko-KR")}</span>
          </footer>
        </>
      )}
      {!loading && !failed && !latest && <div className="technical-state">계산 가능한 기술지표가 없습니다.</div>}
    </section>
  );
}
