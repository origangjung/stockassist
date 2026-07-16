"use client";

import { FormEvent, useState } from "react";
import {
  BacktestEngineComparison,
  BacktestEngineComparisonSummary,
  BacktestStrategy,
  compareBacktestEngines,
} from "../lib/admin-api";
import { NormalizedEquityChart } from "./normalized-equity-chart";

const percent = (value?: number) =>
  value == null ? "-" : `${(value * 100).toFixed(2)}%`;

const number = (value?: number) =>
  value == null
    ? "-"
    : new Intl.NumberFormat("ko-KR", { maximumFractionDigits: 2 }).format(value);

const currency = (value?: number) =>
  value == null
    ? "-"
    : new Intl.NumberFormat("ko-KR", {
        maximumFractionDigits: 0,
      }).format(value);

function EngineCard({
  name,
  summary,
}: {
  name: string;
  summary: BacktestEngineComparisonSummary;
}) {
  return (
    <article className="comparison-card">
      <header>
        <div><span>ENGINE</span><h2>{name}</h2></div>
        <code>{summary.engine_version}</code>
      </header>
      <dl>
        <div><dt>총수익률</dt><dd>{percent(summary.metrics.total_return)}</dd></div>
        <div><dt>MDD</dt><dd>{percent(summary.metrics.max_drawdown)}</dd></div>
        <div><dt>Sharpe</dt><dd>{number(summary.metrics.sharpe_ratio)}</dd></div>
        <div><dt>최종 자산</dt><dd>{currency(summary.metrics.final_equity)}</dd></div>
        <div><dt>거래 수</dt><dd>{summary.metrics.trade_count ?? 0}</dd></div>
        <div><dt>체결 이벤트</dt><dd>{summary.execution.fill_count}</dd></div>
        <div><dt>부분 체결</dt><dd>{summary.execution.partial_fill_count}</dd></div>
        <div><dt>주문 거절</dt><dd>{summary.execution.rejected_order_count}</dd></div>
      </dl>
    </article>
  );
}

export function EngineComparisonPanel() {
  const [symbol, setSymbol] = useState("005930");
  const [strategy, setStrategy] = useState<BacktestStrategy>("pattern_reference");
  const [limit, setLimit] = useState(240);
  const [initialCapital, setInitialCapital] = useState(10_000_000);
  const [volumeParticipation, setVolumeParticipation] = useState(10);
  const [result, setResult] = useState<BacktestEngineComparison | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    const normalizedSymbol = symbol.trim().toUpperCase();
    setError(null);
    if (!/^[0-9A-Z.-]{1,16}$/.test(normalizedSymbol)) {
      setError("종목 코드는 영문 대문자, 숫자, 점 또는 하이픈 1~16자로 입력하세요.");
      return;
    }
    if (!Number.isFinite(volumeParticipation) || volumeParticipation < 1 || volumeParticipation > 100) {
      setError("거래량 참여율은 1~100%로 입력하세요.");
      return;
    }

    setLoading(true);
    setResult(null);
    try {
      setResult(
        await compareBacktestEngines({
          symbol: normalizedSymbol,
          strategy,
          limit,
          fast_period: 5,
          slow_period: 20,
          initial_capital: initialCapital,
          commission_rate: 0.00015,
          tax_rate: 0.0018,
          slippage_rate: 0.0005,
          max_volume_participation: volumeParticipation / 100,
        }),
      );
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "엔진 비교를 실행하지 못했습니다.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="admin-shell comparison-admin">
      <header className="admin-heading">
        <div><p>RESEARCH / ENGINE PARITY</p><h1>백테스트 엔진 비교</h1></div>
      </header>

      <div className="reference-only">
        <b>Experimental</b>
        <span>
          같은 데이터·전략·비용으로 두 체결 모델을 비교합니다. 결과 차이는 투자 의견이 아니라
          주문, 현금, 수량 및 유동성 제약을 반영하는 방식의 차이입니다.
        </span>
      </div>

      <form className="validation-form" onSubmit={submit}>
        <label>
          <span>종목 코드</span>
          <input maxLength={16} onChange={(event) => setSymbol(event.target.value)} required value={symbol} />
        </label>
        <label>
          <span>전략</span>
          <select onChange={(event) => setStrategy(event.target.value as BacktestStrategy)} value={strategy}>
            <option value="pattern_reference">패턴 참고 시그널</option>
            <option value="ma_cross">이동평균 교차</option>
            <option value="buy_and_hold">매수 후 보유 기준선</option>
          </select>
        </label>
        <label>
          <span>캔들 수</span>
          <input max={365} min={30} onChange={(event) => setLimit(Number(event.target.value))} type="number" value={limit} />
        </label>
        <label>
          <span>초기 자산</span>
          <input min={1} onChange={(event) => setInitialCapital(Number(event.target.value))} type="number" value={initialCapital} />
        </label>
        <label>
          <span>이벤트 엔진 거래량 참여율 (%)</span>
          <input max={100} min={1} onChange={(event) => setVolumeParticipation(Number(event.target.value))} type="number" value={volumeParticipation} />
        </label>
        <button disabled={loading} type="submit">
          {loading ? "동일 조건 비교 중..." : "두 엔진 비교 실행"}
        </button>
      </form>

      {error && <div className="admin-state error validation-state"><b>비교 실패</b><span>{error}</span></div>}

      {result && (
        <div className="comparison-result">
          <div className="validation-meta">
            <span>{result.symbol} · {result.strategy} · {result.provider}</span>
            <span>{result.comparison_version} · 데이터 기준 {new Date(result.data_as_of).toLocaleDateString("ko-KR")}</span>
          </div>
          <div className="comparison-grid">
            <EngineCard name="Vectorized" summary={result.vectorized} />
            <EngineCard name="Event-driven" summary={result.event_driven} />
          </div>
          <NormalizedEquityChart
            ariaLabel="벡터형 및 이벤트형 백테스트의 정규화 자산곡선"
            series={[
              { name: "Vectorized", color: "#61d9a4", points: result.vectorized.equity_curve },
              { name: "Event-driven", color: "#72b8ff", points: result.event_driven.equity_curve },
            ]}
            title="자산곡선 비교"
          />
          <div className="comparison-deltas">
            <b>차이 (Event-driven − Vectorized)</b>
            <span>수익률 {percent(result.deltas.total_return)}</span>
            <span>MDD {percent(result.deltas.max_drawdown)}</span>
            <span>최종 자산 {number(result.deltas.final_equity)}</span>
            <span>거래 수 {number(result.deltas.trade_count)}</span>
          </div>
          <small>
            비용: 수수료 {percent(result.assumptions.costs.commission_rate)}, 세금 {percent(result.assumptions.costs.tax_rate)},
            슬리피지 {percent(result.assumptions.costs.slippage_rate)} · 이벤트 거래량 한도 {(result.assumptions.max_volume_participation * 100).toFixed(0)}%
          </small>
        </div>
      )}
    </section>
  );
}
