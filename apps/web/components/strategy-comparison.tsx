"use client";

import { FormEvent, useState } from "react";
import {
  BacktestEngineName,
  BacktestStrategy,
  BacktestStrategyComparison,
  compareBacktestStrategies,
} from "../lib/admin-api";
import { NormalizedEquityChart } from "./normalized-equity-chart";

const strategyLabel: Record<BacktestStrategy, string> = {
  buy_and_hold: "매수 후 보유 기준선",
  ma_cross: "이동평균 교차",
  pattern_reference: "패턴 참고 시그널",
};

const percent = (value?: number) =>
  value == null ? "-" : `${(value * 100).toFixed(2)}%`;

const signedPercent = (value: number) =>
  `${value > 0 ? "+" : ""}${(value * 100).toFixed(2)}%`;

const number = (value?: number) =>
  value == null
    ? "-"
    : new Intl.NumberFormat("ko-KR", { maximumFractionDigits: 2 }).format(value);

const currency = (value?: number) =>
  value == null
    ? "-"
    : new Intl.NumberFormat("ko-KR", { maximumFractionDigits: 0 }).format(value);

export function StrategyComparisonPanel() {
  const [symbol, setSymbol] = useState("005930");
  const [engine, setEngine] = useState<BacktestEngineName>("event_driven");
  const [limit, setLimit] = useState(240);
  const [fastPeriod, setFastPeriod] = useState(5);
  const [slowPeriod, setSlowPeriod] = useState(20);
  const [initialCapital, setInitialCapital] = useState(10_000_000);
  const [volumeParticipation, setVolumeParticipation] = useState(10);
  const [result, setResult] = useState<BacktestStrategyComparison | null>(null);
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
    if (fastPeriod >= slowPeriod) {
      setError("단기 이동평균 기간은 장기 이동평균 기간보다 작아야 합니다.");
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
        await compareBacktestStrategies({
          symbol: normalizedSymbol,
          engine,
          limit,
          fast_period: fastPeriod,
          slow_period: slowPeriod,
          initial_capital: initialCapital,
          commission_rate: 0.00015,
          tax_rate: 0.0018,
          slippage_rate: 0.0005,
          max_volume_participation: engine === "event_driven" ? volumeParticipation / 100 : 1,
        }),
      );
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "전략 비교를 실행하지 못했습니다.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="admin-shell strategy-comparison-admin">
      <header className="admin-heading">
        <div><p>RESEARCH / STRATEGY PARITY</p><h1>동일 조건 전략 비교</h1></div>
      </header>

      <div className="reference-only">
        <b>Experimental</b>
        <span>
          모든 전략을 같은 캔들·비용·체결 엔진으로 계산합니다. 기준선 대비 과거 차이일 뿐,
          전략 순위나 미래 성과 예측 및 투자 권유가 아닙니다.
        </span>
      </div>

      <form className="validation-form" onSubmit={submit}>
        <label>
          <span>종목 코드</span>
          <input maxLength={16} onChange={(event) => setSymbol(event.target.value)} required value={symbol} />
        </label>
        <label>
          <span>체결 엔진</span>
          <select onChange={(event) => setEngine(event.target.value as BacktestEngineName)} value={engine}>
            <option value="event_driven">Event-driven</option>
            <option value="vectorized">Vectorized</option>
          </select>
        </label>
        <label>
          <span>캔들 수</span>
          <input max={365} min={30} onChange={(event) => setLimit(Number(event.target.value))} type="number" value={limit} />
        </label>
        <label>
          <span>단기 이동평균</span>
          <input max={60} min={2} onChange={(event) => setFastPeriod(Number(event.target.value))} type="number" value={fastPeriod} />
        </label>
        <label>
          <span>장기 이동평균</span>
          <input max={200} min={3} onChange={(event) => setSlowPeriod(Number(event.target.value))} type="number" value={slowPeriod} />
        </label>
        <label>
          <span>초기 자산</span>
          <input min={1} onChange={(event) => setInitialCapital(Number(event.target.value))} type="number" value={initialCapital} />
        </label>
        <label>
          <span>거래량 참여율 (%)</span>
          <input disabled={engine !== "event_driven"} max={100} min={1} onChange={(event) => setVolumeParticipation(Number(event.target.value))} type="number" value={engine === "event_driven" ? volumeParticipation : 100} />
        </label>
        <button disabled={loading} type="submit">
          {loading ? "세 전략 비교 중..." : "전략 비교 실행"}
        </button>
      </form>

      {error && <div className="admin-state error validation-state"><b>비교 실패</b><span>{error}</span></div>}

      {result && (
        <div className="strategy-comparison-result">
          <div className="validation-meta">
            <span>{result.symbol} · {result.engine} · {result.provider}</span>
            <span>{result.comparison_version} · 데이터 기준 {new Date(result.data_as_of).toLocaleDateString("ko-KR")}</span>
          </div>
          <div className="admin-table-wrap">
            <table className="admin-table strategy-comparison-table">
              <thead>
                <tr><th>전략</th><th>총수익률</th><th>기준선 대비</th><th>MDD</th><th>Sharpe</th><th>승률</th><th>최종 자산</th><th>거래</th><th>부분 체결</th><th>거절</th></tr>
              </thead>
              <tbody>
                {result.strategies.map((item) => (
                  <tr className={item.strategy === result.benchmark ? "benchmark-row" : ""} key={item.strategy}>
                    <td><b>{strategyLabel[item.strategy]}</b>{item.strategy === result.benchmark && <small>비교 기준선</small>}</td>
                    <td className={(item.metrics.total_return ?? 0) >= 0 ? "positive-text" : "negative-text"}>{percent(item.metrics.total_return)}</td>
                    <td className={item.deltas_vs_buy_and_hold.total_return >= 0 ? "positive-text" : "negative-text"}>{signedPercent(item.deltas_vs_buy_and_hold.total_return)}</td>
                    <td>{percent(item.metrics.max_drawdown)}</td>
                    <td>{number(item.metrics.sharpe_ratio)}</td>
                    <td>{percent(item.metrics.win_rate)}</td>
                    <td>{currency(item.metrics.final_equity)}</td>
                    <td>{item.metrics.trade_count ?? 0}</td>
                    <td>{item.execution.partial_fill_count}</td>
                    <td>{item.execution.rejected_order_count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <NormalizedEquityChart
            ariaLabel="세 백테스트 전략의 정규화 자산곡선"
            series={result.strategies.map((item) => ({
              name: strategyLabel[item.strategy],
              color: {
                buy_and_hold: "#8b9bb2",
                ma_cross: "#f3cb66",
                pattern_reference: "#72b8ff",
              }[item.strategy],
              points: item.equity_curve,
            }))}
            title="전략별 자산곡선"
          />
          <div className="execution-model-note">
            <b>{result.engine_version}</b>
            <span>비용과 이동평균 설정을 포함한 모든 비교 가정은 세 전략에 동일하게 적용됩니다.</span>
          </div>
        </div>
      )}
    </section>
  );
}
