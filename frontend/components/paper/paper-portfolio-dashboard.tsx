"use client";

/** 모의 계좌의 자산, 보유 종목, 누적 수익률과 체결 내역을 관리하는 독립 화면이다. */
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  ArrowLeft,
  BarChart3,
  Check,
  Clock3,
  Coins,
  RefreshCw,
  Search,
  ShieldCheck,
  TrendingDown,
  TrendingUp,
  WalletCards,
} from "lucide-react";
import { fetchPaperPortfolio, getPaperAccountId, type PaperPortfolio } from "../../lib/paper-api";
import { FundAllocationPlanner } from "./fund-allocation-planner";

type Currency = "KRW" | "USD";

/** `money`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
function money(value: string | number, currency: Currency) {
  return new Intl.NumberFormat("ko-KR", {
    style: "currency",
    currency,
    maximumFractionDigits: currency === "KRW" ? 0 : 2,
  }).format(Number(value));
}

/** `percent`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
function percent(value: string | number) {
  const numeric = Number(value);
  return `${numeric > 0 ? "+" : ""}${numeric.toFixed(2)}%`;
}

/** `dateTime`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
function dateTime(value: string) {
  return new Intl.DateTimeFormat("ko-KR", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

/** `PaperPortfolioDashboard`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export function PaperPortfolioDashboard() {
  const [portfolio, setPortfolio] = useState<PaperPortfolio | null>(null);
  const [currency, setCurrency] = useState<Currency>("KRW");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  /** 브라우저 전용 계좌를 최신 시세로 다시 평가한다. */
  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setPortfolio(await fetchPaperPortfolio(getPaperAccountId()));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "모의 계좌를 불러오지 못했습니다.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void load(); }, [load]);

  const positions = useMemo(
    () => portfolio?.positions.filter((position) => position.currency === currency) ?? [],
    [currency, portfolio],
  );
  const orders = useMemo(
    () => portfolio?.orders.filter((order) => order.currency === currency).slice(0, 12) ?? [],
    [currency, portfolio],
  );
  const totals = portfolio?.totals[currency];
  const risk = portfolio?.risk[currency];
  const investedPercent = Math.min(100, Number(risk?.invested_ratio ?? 0) * 100);
  const concentrationPercent = Math.min(100, Number(risk?.largest_position_ratio ?? 0) * 100);
  const riskLimits = risk ? [
    Number(risk.limits.max_order_ratio) * 100,
    Number(risk.limits.max_position_ratio) * 100,
    Number(risk.limits.max_invested_ratio) * 100,
  ] : [];
  const returnValue = Number(totals?.return_percent ?? 0);
  const totalPnl = Number(totals?.total_pnl ?? 0);
  const gainClass = totalPnl < 0 ? "loss" : totalPnl > 0 ? "gain" : "flat";

  return (
    <main className="paper-page">
      <header className="paper-page-header">
        <nav aria-label="모의투자 메뉴">
          <a aria-label="StockPilot AI 홈" className="paper-brand" href="/">
            <span aria-hidden="true">SP</span><strong>StockPilot <em>AI</em></strong>
          </a>
          <a className="paper-back" href="/"><ArrowLeft size={17} /> 종목 찾기</a>
        </nav>
      </header>

      <section className="paper-portfolio" aria-labelledby="paper-portfolio-title">
        <div className="paper-portfolio-topline">
          <div><span>가상 자산</span><h1 id="paper-portfolio-title">내 모의투자</h1>{portfolio && <small className={`paper-save-state ${portfolio.persistence_status}`}><Check size={13} />{portfolio.persistence_status === "saved" ? "모든 거래 자동 저장됨" : "현재 실행 중 임시 저장"}</small>}</div>
          <button aria-label="자산 새로고침" disabled={loading} onClick={() => void load()} title="자산 새로고침" type="button">
            <RefreshCw className={loading ? "is-spinning" : ""} size={18} />
          </button>
        </div>

        <div className="paper-currency-tabs" role="tablist" aria-label="계좌 통화">
          {(["KRW", "USD"] as const).map((item) => (
            <button aria-selected={currency === item} key={item} onClick={() => setCurrency(item)} role="tab" type="button">
              {item === "KRW" ? "원화 계좌" : "달러 계좌"}
            </button>
          ))}
        </div>

        {error && <div className="paper-page-error" role="alert"><b>계좌를 불러오지 못했어요</b><span>{error}</span><button onClick={() => void load()} type="button">다시 시도</button></div>}

        {!error && (
          <>
            <section className="paper-balance" aria-label={`${currency} 자산 요약`}>
              <div className="paper-balance-primary">
                <span>총 자산</span>
                <strong>{totals ? money(totals.equity, currency) : "-"}</strong>
                <p className={gainClass}>
                  {totalPnl < 0 ? <TrendingDown size={16} /> : <TrendingUp size={16} />}
                  처음보다 {totals ? `${money(totals.total_pnl, currency)} (${percent(totals.return_percent)})` : "-"}
                </p>
              </div>
              <dl>
                <div><dt><WalletCards size={16} /> 주문 가능</dt><dd>{totals ? money(totals.cash, currency) : "-"}</dd></div>
                <div><dt><BarChart3 size={16} /> 주식 평가금</dt><dd>{totals ? money(totals.market_value, currency) : "-"}</dd></div>
                <div><dt><Coins size={16} /> 평가 손익</dt><dd className={Number(totals?.unrealized_pnl ?? 0) < 0 ? "loss" : Number(totals?.unrealized_pnl ?? 0) > 0 ? "gain" : "flat"}>{totals ? money(totals.unrealized_pnl, currency) : "-"}</dd></div>
              </dl>
            </section>

            {risk && (
              <section className={`paper-risk-overview ${risk.status}`} aria-labelledby="paper-risk-title">
                <header>
                  <div><ShieldCheck size={18} /><h2 id="paper-risk-title">위험 관리</h2></div>
                  <strong>{risk.status === "stable" ? "안정" : risk.status === "caution" ? "주의 필요" : "위험 높음"}</strong>
                </header>
                <div className="paper-risk-bars">
                  <div><span>전체 투자 비중 <b>{investedPercent.toFixed(1)}%</b></span><i><em style={{ width: `${investedPercent}%` }} /></i></div>
                  <div><span>최대 종목 비중 <b>{concentrationPercent.toFixed(1)}%</b></span><i><em style={{ width: `${concentrationPercent}%` }} /></i></div>
                </div>
                <p>
                  {risk.warnings.includes("single_position_concentration") && `${risk.largest_position_symbol ?? "단일 종목"} 비중이 높아요. `}
                  {risk.warnings.includes("low_cash_buffer") && "현금 여유가 부족해요. "}
                  {!risk.warnings.length && "현재 설정된 집중도와 현금 한도 안에 있어요. "}
                  <span>매수는 1회 {riskLimits[0]}%, 종목당 {riskLimits[1]}%, 총 투자 {riskLimits[2]}%까지 허용됩니다.</span>
                </p>
              </section>
            )}

            <FundAllocationPlanner
              currency={currency}
              key={currency}
              onPortfolioChanged={load}
            />

            <section className="paper-holdings" aria-labelledby="paper-holdings-title">
              <header><div><h2 id="paper-holdings-title">보유 종목</h2><span>{positions.length}개</span></div><a href="/?focus=search"><Search size={15} /> 종목 추가</a></header>
              {loading && !portfolio ? <div className="paper-page-loading" aria-label="보유 종목 불러오는 중" /> : positions.length ? (
                <div className="paper-holding-list">
                  {positions.map((position) => {
                    const positionReturn = Number(position.return_percent);
                    return (
                      <a href={`/?symbol=${encodeURIComponent(position.symbol)}`} key={position.symbol}>
                        <span className="paper-holding-symbol">{position.symbol.slice(0, 2)}</span>
                        <div className="paper-holding-name"><b>{position.name}</b><span>{position.symbol} · {Number(position.quantity).toLocaleString("ko-KR")}주</span></div>
                        <div className="paper-holding-value"><b>{money(position.market_value, currency)}</b><span className={positionReturn < 0 ? "loss" : positionReturn > 0 ? "gain" : "flat"}>{money(position.unrealized_pnl, currency)} ({percent(position.return_percent)})</span></div>
                      </a>
                    );
                  })}
                </div>
              ) : (
                <div className="paper-page-empty"><BarChart3 size={28} /><b>아직 보유한 종목이 없어요</b><span>분석 화면에서 관심 종목을 모의 매수해 보세요.</span><a href="/"><Search size={15} /> 종목 찾아보기</a></div>
              )}
            </section>

            <section className="paper-activity" aria-labelledby="paper-activity-title">
              <header><h2 id="paper-activity-title">최근 활동</h2><Clock3 size={17} /></header>
              {orders.length ? <ul>{orders.map((order) => <li key={order.order_id}><span className={order.side}>{order.side === "buy" ? "매수" : "매도"}</span><div><b>{order.name}</b><small>{dateTime(order.executed_at)}</small></div><strong>{Number(order.quantity).toLocaleString("ko-KR")}주 · {money(order.fill_price, currency)}</strong></li>)}</ul> : <p>아직 {currency === "KRW" ? "원화" : "달러"} 체결 내역이 없어요.</p>}
            </section>
          </>
        )}
      </section>
    </main>
  );
}
