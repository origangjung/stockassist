"use client";

import { useEffect, useState } from "react";
import {
  BrokerAccount,
  fetchBrokerAccounts,
  PortfolioSyncResult,
  syncPortfolio,
} from "../lib/admin-api";

const number = (value: number | string, digits = 0) =>
  new Intl.NumberFormat("ko-KR", { maximumFractionDigits: digits }).format(Number(value));
const percent = (value: number | string) => `${(Number(value) * 100).toFixed(2)}%`;

export function PortfolioAnalysis() {
  const [accounts, setAccounts] = useState<BrokerAccount[]>([]);
  const [portfolio, setPortfolio] = useState<PortfolioSyncResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);

  useEffect(() => {
    void fetchBrokerAccounts()
      .then((result) => { setAccounts(result.accounts); setError(null); })
      .catch((reason) => setError(reason instanceof Error ? reason.message : "계좌를 불러오지 못했습니다."))
      .finally(() => setLoading(false));
  }, []);

  const synchronize = async (account: BrokerAccount) => {
    setSyncing(true);
    setError(null);
    try {
      setPortfolio(await syncPortfolio(account.account_seq));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "포트폴리오 동기화에 실패했습니다.");
    } finally {
      setSyncing(false);
    }
  };

  return (
    <section className="admin-shell portfolio-admin">
      <header className="admin-heading">
        <div><p>OPERATIONS / OWN ACCOUNT</p><h1>포트폴리오 위험 분석</h1></div>
        <div className="account-actions">{accounts.map((account) => (
          <button disabled={syncing} key={account.account_seq} onClick={() => void synchronize(account)} type="button">
            {account.account_no_masked} 동기화
          </button>
        ))}</div>
      </header>
      <div className="reference-only"><b>READ ONLY</b><span>본인 계좌 보유 현황만 조회하며 주문·리밸런싱을 실행하지 않습니다.</span></div>
      {loading && <div className="admin-state">연결된 계좌를 확인하는 중입니다.</div>}
      {error && <div className="admin-state error"><b>계좌 조회 실패</b><span>{error}</span><small>ACCOUNT_SYNC_ENABLED와 Toss 계좌 권한을 확인하세요.</small></div>}
      {!loading && !error && accounts.length === 0 && <div className="admin-state">연결된 본인 계좌가 없습니다.</div>}
      {!loading && !error && accounts.length > 0 && portfolio === null && <div className="admin-state"><b>수동 동기화 대기</b><span>마스킹된 계좌 버튼을 눌러 최신 보유 현황을 분석하세요.</span></div>}
      {portfolio && (
        <div className="portfolio-result">
          <div className="portfolio-meta"><b>{portfolio.account.account_no_masked}</b><span>{portfolio.provider} · {portfolio.analysis.analysis_version} · Experimental</span></div>
          <div className="currency-analysis">{Object.entries(portfolio.analysis.currencies).map(([currency, item]) => (
            <article key={currency}>
              <header><b>{currency}</b><span className={`concentration ${item.concentration_level}`}>{item.concentration_level}</span></header>
              <dl>
                <div><dt>평가금액</dt><dd>{number(item.market_value, 2)}</dd></div>
                <div><dt>비용 반영 손익</dt><dd>{number(item.profit_loss_after_cost, 2)}</dd></div>
                <div><dt>비용 반영 수익률</dt><dd>{percent(item.profit_rate_after_cost)}</dd></div>
                <div><dt>최대 비중</dt><dd>{item.largest_symbol} · {percent(item.largest_allocation)}</dd></div>
                <div><dt>집중도 HHI</dt><dd>{number(item.concentration_index, 4)}</dd></div>
                <div><dt>실효 종목 수</dt><dd>{number(item.effective_holding_count, 2)}</dd></div>
                <div><dt>손실 노출</dt><dd>{percent(item.loss_exposure)}</dd></div>
                <div><dt>보유 종목</dt><dd>{item.holding_count}개</dd></div>
              </dl>
              <p>{item.risk_flags.length ? item.risk_flags.join(" · ") : "활성 위험 플래그 없음"}</p>
            </article>
          ))}</div>
          <div className="admin-table-wrap"><table className="admin-table"><thead><tr><th>종목</th><th>통화</th><th>평가금액</th><th>비중</th><th>비용 반영 손익</th></tr></thead><tbody>{portfolio.holdings.map((holding) => (
            <tr key={`${holding.currency}:${holding.symbol}`}><td><b>{holding.symbol}</b><small>{holding.name}</small></td><td>{holding.currency}</td><td>{number(holding.market_value, 2)}</td><td>{holding.allocation_within_currency == null ? "-" : percent(holding.allocation_within_currency)}</td><td>{number(holding.profit_loss_after_cost, 2)}</td></tr>
          ))}</tbody></table></div>
        </div>
      )}
    </section>
  );
}
