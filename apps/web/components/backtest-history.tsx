"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import {
  BacktestHistory,
  BacktestRunDetail,
  BacktestRunSummary,
  fetchBacktestHistory,
  fetchBacktestRun,
} from "../lib/admin-api";

const percent = (value?: number) =>
  value == null ? "-" : `${(value * 100).toFixed(2)}%`;

const number = (value?: number) =>
  value == null ? "-" : new Intl.NumberFormat("ko-KR", { maximumFractionDigits: 2 }).format(value);

const time = (value: string) =>
  new Intl.DateTimeFormat("ko-KR", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value));

export function BacktestHistoryPanel() {
  const [history, setHistory] = useState<BacktestHistory | null>(null);
  const [detail, setDetail] = useState<BacktestRunDetail | null>(null);
  const [symbol, setSymbol] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async (filter = "") => {
    setLoading(true);
    setError(null);
    setDetail(null);
    try {
      setHistory(await fetchBacktestHistory(filter));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "이력을 불러오지 못했습니다.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void load(); }, [load]);

  const submit = (event: FormEvent) => {
    event.preventDefault();
    void load(symbol.trim().toUpperCase());
  };

  const selectRun = async (run: BacktestRunSummary) => {
    setError(null);
    try {
      setDetail(await fetchBacktestRun(run.run_id));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "상세 이력을 불러오지 못했습니다.");
    }
  };

  return (
    <section className="admin-shell">
      <header className="admin-heading">
        <div><p>OPERATIONS / BACKTEST</p><h1>백테스트 실행 이력</h1></div>
        <form onSubmit={submit}>
          <input
            aria-label="종목 코드"
            maxLength={16}
            onChange={(event) => setSymbol(event.target.value)}
            placeholder="종목 코드 필터"
            value={symbol}
          />
          <button type="submit">조회</button>
        </form>
      </header>

      {loading && <div className="admin-state">실행 이력을 불러오는 중입니다.</div>}
      {error && <div className="admin-state error"><b>조회 실패</b><span>{error}</span></div>}
      {!loading && !error && history?.persistence_status === "disabled" && (
        <div className="admin-state"><b>DB 저장 비활성화</b><span>PERSISTENCE_ENABLED를 켜야 이력이 저장됩니다.</span></div>
      )}
      {!loading && !error && history?.persistence_status === "enabled" && history.items.length === 0 && (
        <div className="admin-state">저장된 백테스트 실행 이력이 없습니다.</div>
      )}

      {history && history.items.length > 0 && (
        <>
          <div className="admin-summary">
            <article><span>전체 실행</span><strong>{history.total}</strong></article>
            <article><span>표시 중</span><strong>{history.items.length}</strong></article>
            <article><span>검증 상태</span><strong>Experimental</strong></article>
          </div>
          <div className="admin-table-wrap">
            <table className="admin-table">
              <thead><tr><th>실행 시각</th><th>종목</th><th>전략</th><th>엔진</th><th>수익률</th><th>MDD</th><th>Sharpe</th><th /></tr></thead>
              <tbody>{history.items.map((run) => (
                <tr key={run.run_id}>
                  <td>{time(run.started_at)}</td><td><b>{run.symbol}</b></td><td>{run.strategy}</td>
                  <td><span className={`engine-badge ${run.engine}`}>{run.engine}</span></td>
                  <td className={(run.metrics.total_return ?? 0) >= 0 ? "positive-text" : "negative-text"}>{percent(run.metrics.total_return)}</td>
                  <td>{percent(run.metrics.max_drawdown)}</td><td>{number(run.metrics.sharpe_ratio)}</td>
                  <td><button onClick={() => void selectRun(run)} type="button">상세</button></td>
                </tr>
              ))}</tbody>
            </table>
          </div>
        </>
      )}

      {detail && (
        <aside className="run-detail">
          <header><div><span>RUN DETAIL</span><h2>{detail.summary.symbol} · {detail.summary.strategy}</h2></div><button onClick={() => setDetail(null)} type="button">닫기</button></header>
          <div className="detail-metrics">
            <article><span>최종 자산</span><strong>{number(detail.summary.metrics.final_equity)}</strong></article>
            <article><span>총수익률</span><strong>{percent(detail.summary.metrics.total_return)}</strong></article>
            <article><span>최대 낙폭</span><strong>{percent(detail.summary.metrics.max_drawdown)}</strong></article>
            <article><span>승률</span><strong>{percent(detail.summary.metrics.win_rate)}</strong></article>
          </div>
          <dl><div><dt>실행 ID</dt><dd>{detail.summary.run_id}</dd></div><div><dt>엔진</dt><dd>{detail.summary.engine_version}</dd></div><div><dt>거래 수</dt><dd>{detail.trades.length}</dd></div><div><dt>감사 이벤트</dt><dd>{detail.events.length}</dd></div></dl>
        </aside>
      )}
    </section>
  );
}
