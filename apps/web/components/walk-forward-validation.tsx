"use client";

import { FormEvent, useState } from "react";
import {
  BacktestEngineName,
  BacktestStrategy,
  WalkForwardValidation,
  runWalkForwardValidation,
} from "../lib/admin-api";

const percent = (value?: number) =>
  value == null ? "-" : `${(value * 100).toFixed(2)}%`;

const number = (value?: number) =>
  value == null
    ? "-"
    : new Intl.NumberFormat("ko-KR", { maximumFractionDigits: 2 }).format(value);

const date = (value: string) =>
  new Intl.DateTimeFormat("ko-KR", { dateStyle: "medium" }).format(new Date(value));

const stabilityLabel: Record<WalkForwardValidation["aggregate"]["stability"], string> = {
  consistent_positive: "양(+) 구간 일관",
  mixed: "혼합",
  consistent_negative: "음(-) 구간 일관",
};

export function WalkForwardValidationPanel() {
  const [symbol, setSymbol] = useState("005930");
  const [strategy, setStrategy] = useState<BacktestStrategy>("pattern_reference");
  const [engine, setEngine] = useState<BacktestEngineName>("vectorized");
  const [nSplits, setNSplits] = useState(3);
  const [warmup, setWarmup] = useState(60);
  const [limit, setLimit] = useState(240);
  const [volumeParticipation, setVolumeParticipation] = useState(10);
  const [result, setResult] = useState<WalkForwardValidation | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    const normalizedSymbol = symbol.trim().toUpperCase();
    setError(null);
    if (!/^[0-9A-Z]{1,16}$/.test(normalizedSymbol)) {
      setError("종목 코드는 영문 대문자 또는 숫자 1~16자로 입력하세요.");
      return;
    }
    if (limit < warmup + nSplits * 10) {
      setError(`데이터 수는 최소 ${warmup + nSplits * 10}개가 필요합니다.`);
      return;
    }
    if (
      engine === "event_driven" &&
      (!Number.isFinite(volumeParticipation) || volumeParticipation < 1 || volumeParticipation > 100)
    ) {
      setError("이벤트 엔진 거래량 참여율은 1~100%로 입력하세요.");
      return;
    }

    setLoading(true);
    setResult(null);
    try {
      setResult(
        await runWalkForwardValidation({
          symbol: normalizedSymbol,
          strategy,
          engine,
          limit,
          n_splits: nSplits,
          warmup_candles: warmup,
          fast_period: 5,
          slow_period: 20,
          max_volume_participation: engine === "event_driven" ? volumeParticipation / 100 : 1,
        }),
      );
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "검증을 실행하지 못했습니다.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="admin-shell validation-admin">
      <header className="admin-heading">
        <div><p>RESEARCH / WALK-FORWARD</p><h1>전략 구간 검증</h1></div>
      </header>

      <div className="reference-only">
        <b>Experimental</b>
        <span>
          시간 순서를 보존한 미래 구간별 결과입니다. 안정성 표시는 관측 결과의 설명이며
          전략 승인, 미래 성과 보장 또는 투자 자문이 아닙니다.
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
          <span>엔진</span>
          <select onChange={(event) => setEngine(event.target.value as BacktestEngineName)} value={engine}>
            <option value="vectorized">Vectorized</option>
            <option value="event_driven">Event-driven</option>
          </select>
        </label>
        <label>
          <span>검증 구간</span>
          <input max={6} min={2} onChange={(event) => setNSplits(Number(event.target.value))} type="number" value={nSplits} />
        </label>
        <label>
          <span>준비 캔들</span>
          <input max={120} min={21} onChange={(event) => setWarmup(Number(event.target.value))} type="number" value={warmup} />
        </label>
        <label>
          <span>전체 캔들</span>
          <input max={365} min={30} onChange={(event) => setLimit(Number(event.target.value))} type="number" value={limit} />
        </label>
        <label>
          <span>거래량 참여율 (%)</span>
          <input disabled={engine !== "event_driven"} max={100} min={1} onChange={(event) => setVolumeParticipation(Number(event.target.value))} type="number" value={engine === "event_driven" ? volumeParticipation : 100} />
        </label>
        <button disabled={loading} type="submit">
          {loading ? "검증 실행 중..." : "Walk-Forward 실행"}
        </button>
      </form>

      {error && <div className="admin-state error validation-state"><b>검증 실패</b><span>{error}</span></div>}

      {result && (
        <div className="validation-result">
          <div className="validation-meta">
            <span>{result.symbol} · {result.strategy} · {result.provider}</span>
            <span>{result.validation_version} · 데이터 기준 {date(result.data_as_of)}</span>
          </div>
          <div className="execution-model-note">
            <b>{result.execution_model.volume_limit_applied ? `이벤트 체결 한도 ${(result.execution_model.max_volume_participation * 100).toFixed(0)}%` : "벡터 체결 모델"}</b>
            <span>{result.execution_model.force_close_bypasses_volume_limit ? "마지막 강제 청산은 거래량 한도를 우회하고 감사 이벤트에 기록됩니다." : "거래량 참여 제한은 이벤트 엔진에서만 적용됩니다."}</span>
          </div>
          <div className="admin-summary validation-summary">
            <article>
              <span>평균 구간 수익률</span>
              <strong className={result.aggregate.mean_total_return >= 0 ? "positive-text" : "negative-text"}>
                {percent(result.aggregate.mean_total_return)}
              </strong>
            </article>
            <article><span>수익 구간 비율</span><strong>{percent(result.aggregate.profitable_fold_ratio)}</strong></article>
            <article><span>최악 MDD</span><strong>{percent(result.aggregate.worst_max_drawdown)}</strong></article>
            <article><span>평균 Sharpe</span><strong>{number(result.aggregate.mean_sharpe_ratio)}</strong></article>
            <article><span>전체 거래 수</span><strong>{result.aggregate.total_trade_count}</strong></article>
            <article><span>부분 체결</span><strong>{result.aggregate.total_partial_fill_count}</strong></article>
            <article><span>유동성 거절</span><strong>{result.aggregate.total_rejected_order_count}</strong></article>
            <article>
              <span>구간 안정성</span>
              <strong className={`stability-badge ${result.aggregate.stability}`}>
                {stabilityLabel[result.aggregate.stability]}
              </strong>
            </article>
          </div>

          <div className="admin-table-wrap">
            <table className="admin-table">
              <thead><tr><th>구간</th><th>테스트 기간</th><th>캔들</th><th>수익률</th><th>MDD</th><th>Sharpe</th><th>승률</th><th>거래</th><th>부분 체결</th><th>거절</th></tr></thead>
              <tbody>
                {result.folds.map((fold) => (
                  <tr key={fold.fold}>
                    <td><b>Fold {fold.fold}</b></td>
                    <td>{date(fold.test_started_at)} – {date(fold.test_ended_at)}</td>
                    <td>{fold.test_candles}</td>
                    <td className={(fold.metrics.total_return ?? 0) >= 0 ? "positive-text" : "negative-text"}>{percent(fold.metrics.total_return)}</td>
                    <td>{percent(fold.metrics.max_drawdown)}</td>
                    <td>{number(fold.metrics.sharpe_ratio)}</td>
                    <td>{percent(fold.metrics.win_rate)}</td>
                    <td>{fold.metrics.trade_count ?? 0}</td>
                    <td>{fold.execution.partial_fill_count}</td>
                    <td>{fold.execution.rejected_order_count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </section>
  );
}
