"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import {
  addWatchlist,
  createPriceAlert,
  disablePriceAlert,
  evaluatePriceAlerts,
  fetchPriceAlerts,
  fetchWatchlist,
  PriceAlertData,
  removeWatchlist,
  WatchlistData,
} from "../lib/admin-api";

const price = (value: number | string | null) =>
  value == null ? "-" : new Intl.NumberFormat("ko-KR", { maximumFractionDigits: 6 }).format(Number(value));

export function WatchlistAlerts() {
  const [watchlist, setWatchlist] = useState<WatchlistData | null>(null);
  const [alerts, setAlerts] = useState<PriceAlertData | null>(null);
  const [watchSymbol, setWatchSymbol] = useState("");
  const [alertSymbol, setAlertSymbol] = useState("");
  const [condition, setCondition] = useState<"above" | "below">("above");
  const [targetPrice, setTargetPrice] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    try {
      const [watchlistData, alertData] = await Promise.all([fetchWatchlist(), fetchPriceAlerts()]);
      setWatchlist(watchlistData);
      setAlerts(alertData);
      setError(null);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "관심 종목과 알림을 불러오지 못했습니다.");
    }
  }, []);

  useEffect(() => { void load(); }, [load]);

  const run = async (action: () => Promise<unknown>, success: string) => {
    setBusy(true);
    setError(null);
    setMessage(null);
    try {
      await action();
      setMessage(success);
      await load();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "요청을 처리하지 못했습니다.");
    } finally {
      setBusy(false);
    }
  };

  const submitWatchlist = (event: FormEvent) => {
    event.preventDefault();
    const symbol = watchSymbol.trim().toUpperCase();
    if (!symbol) return;
    void run(() => addWatchlist(symbol), `${symbol}을(를) 관심 종목에 저장했습니다.`);
    setWatchSymbol("");
  };

  const submitAlert = (event: FormEvent) => {
    event.preventDefault();
    const symbol = alertSymbol.trim().toUpperCase();
    const target = Number(targetPrice);
    if (!symbol || !Number.isFinite(target) || target <= 0) return;
    void run(
      () => createPriceAlert(symbol, condition, target),
      `${symbol} 참고 가격 알림을 등록했습니다.`,
    );
    setTargetPrice("");
  };

  const evaluate = () => {
    setBusy(true);
    setError(null);
    setMessage(null);
    void evaluatePriceAlerts()
      .then(async (result) => {
        setMessage(`${result.evaluated}건 평가 · ${result.triggered.length}건 조건 도달 · 주문 실행 0건`);
        await load();
      })
      .catch((reason) => setError(reason instanceof Error ? reason.message : "알림 평가에 실패했습니다."))
      .finally(() => setBusy(false));
  };

  const persistenceDisabled = watchlist?.persistence_status === "disabled" || alerts?.persistence_status === "disabled";

  return (
    <section className="admin-shell alert-admin">
      <header className="admin-heading">
        <div><p>OPERATIONS / REFERENCE ALERTS</p><h1>관심 종목 · 참고 알림</h1></div>
        <button disabled={busy || persistenceDisabled} onClick={evaluate} type="button">지금 평가</button>
      </header>
      <div className="reference-only"><b>REFERENCE ONLY</b><span>가격 조건 도달을 기록할 뿐 매수·매도 주문은 실행하지 않습니다.</span></div>
      {persistenceDisabled && <div className="admin-state"><b>DB 저장 비활성화</b><span>PERSISTENCE_ENABLED=true 설정과 최신 마이그레이션이 필요합니다.</span></div>}
      {error && <div className="admin-state error"><b>처리 실패</b><span>{error}</span></div>}
      {message && <div className="alert-message">{message}</div>}
      {!persistenceDisabled && (
        <div className="alert-grid">
          <article className="alert-card">
            <h2>관심 종목</h2>
            <form onSubmit={submitWatchlist}>
              <input aria-label="관심 종목 코드" maxLength={16} onChange={(event) => setWatchSymbol(event.target.value)} placeholder="005930 또는 AAPL" value={watchSymbol} />
              <button disabled={busy} type="submit">추가</button>
            </form>
            <ul>{watchlist?.items.map((item) => (
              <li key={item.symbol}><div><b>{item.symbol}</b><span>{item.name} · {item.market}</span></div><button disabled={busy} onClick={() => void run(() => removeWatchlist(item.symbol), `${item.symbol}을(를) 삭제했습니다.`)} type="button">삭제</button></li>
            ))}</ul>
            {watchlist?.items.length === 0 && <p className="empty-copy">저장된 관심 종목이 없습니다.</p>}
          </article>
          <article className="alert-card">
            <h2>가격 참고 알림</h2>
            <form className="alert-form" onSubmit={submitAlert}>
              <input aria-label="알림 종목 코드" maxLength={16} onChange={(event) => setAlertSymbol(event.target.value)} placeholder="종목 코드" value={alertSymbol} />
              <select aria-label="가격 조건" onChange={(event) => setCondition(event.target.value as "above" | "below")} value={condition}><option value="above">이상 도달</option><option value="below">이하 도달</option></select>
              <input aria-label="목표 가격" min="0.000001" onChange={(event) => setTargetPrice(event.target.value)} placeholder="목표 가격" step="0.000001" type="number" value={targetPrice} />
              <button disabled={busy} type="submit">등록</button>
            </form>
            <div className="admin-table-wrap"><table className="admin-table"><thead><tr><th>종목</th><th>조건</th><th>최근가</th><th>상태</th><th /></tr></thead><tbody>{alerts?.items.map((alert) => (
              <tr key={alert.alert_id}><td><b>{alert.symbol}</b></td><td>{price(alert.target_price)} {alert.condition === "above" ? "이상" : "이하"}</td><td>{price(alert.last_price)}</td><td><span className={`alert-status ${alert.status}`}>{alert.status}</span></td><td>{alert.status === "active" && <button disabled={busy} onClick={() => void run(() => disablePriceAlert(alert.alert_id), "알림을 비활성화했습니다.")} type="button">끄기</button>}</td></tr>
            ))}</tbody></table></div>
            {alerts?.items.length === 0 && <p className="empty-copy">등록된 참고 알림이 없습니다.</p>}
          </article>
        </div>
      )}
    </section>
  );
}
