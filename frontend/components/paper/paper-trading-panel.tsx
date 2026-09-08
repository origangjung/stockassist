"use client";

/** 현재 종목의 모의 주문과 통화별 계좌 현황을 한 화면에서 관리한다. */
import { FormEvent, useEffect, useMemo, useState } from "react";
import { ArrowDownToLine, ArrowUpFromLine, Check, CircleDollarSign, History, RotateCcw, ShieldCheck, WalletCards } from "lucide-react";
import {
  createPaperOrder,
  fetchPaperPortfolio,
  getPaperAccountId,
  resetPaperPortfolio,
  type PaperPortfolio,
} from "../../lib/paper-api";

/** `money`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
function money(value: string | number, currency: string) {
  return new Intl.NumberFormat("ko-KR", {
    style: "currency",
    currency,
    maximumFractionDigits: currency === "KRW" ? 0 : 2,
  }).format(Number(value));
}

/** Props 인터페이스는 모의투자 주문과 자산 화면을 담당합니다.에서 교환하는 필드 계약을 정의합니다. */
interface Props {
  symbol: string;
  name: string;
  currency: string;
  currentPrice?: string | number | null;
}

/** `PaperTradingPanel`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export function PaperTradingPanel({ symbol, name, currency, currentPrice }: Props) {
  const [id, setId] = useState<string | null>(null);
  const [portfolio, setPortfolio] = useState<PaperPortfolio | null>(null);
  const [side, setSide] = useState<"buy" | "sell">("buy");
  const [quantity, setQuantity] = useState("1");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [confirmReset, setConfirmReset] = useState(false);

  useEffect(() => {
    const nextId = getPaperAccountId();
    setId(nextId);
    fetchPaperPortfolio(nextId).then(setPortfolio).catch((reason: Error) => setError(reason.message));
  }, []);

  const normalizedCurrency = currency === "USD" ? "USD" : "KRW";
  const selectedPosition = portfolio?.positions.find((item) => item.symbol === symbol);
  const estimate = useMemo(
    () => Number(currentPrice ?? 0) * Number(quantity || 0),
    [currentPrice, quantity],
  );

  /** `submit`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!id || pending || !Number.isFinite(Number(quantity)) || Number(quantity) <= 0) return;
    setPending(true);
    setError(null);
    try {
      setPortfolio(await createPaperOrder(id, {
        symbol,
        side,
        quantity,
        idempotency_key: crypto.randomUUID(),
      }));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "모의 주문을 처리하지 못했습니다.");
    } finally {
      setPending(false);
    }
  }

  /** `reset`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
  async function reset() {
    if (!id || pending) return;
    setPending(true);
    setError(null);
    try {
      setPortfolio(await resetPaperPortfolio(id));
      setConfirmReset(false);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "모의 계좌를 초기화하지 못했습니다.");
    } finally {
      setPending(false);
    }
  }

  const totals = portfolio?.totals[normalizedCurrency];
  const risk = portfolio?.risk[normalizedCurrency];
  const investedPercent = Math.min(100, Number(risk?.invested_ratio ?? 0) * 100);
  const riskLimits = risk ? [
    Number(risk.limits.max_order_ratio) * 100,
    Number(risk.limits.max_position_ratio) * 100,
    Number(risk.limits.max_invested_ratio) * 100,
  ] : [];
  return (
    <section className="paper-trading" id="paper-trading" aria-labelledby="paper-trading-title">
      <header className="paper-heading">
        <div>
          <span><CircleDollarSign size={15} /> PAPER TRADING</span>
          <h3 id="paper-trading-title">모의투자</h3>
          <p>실제 주문이 아닌 현재 조회가 기준의 연습 거래입니다.</p>
          {portfolio && <small className={`paper-save-state ${portfolio.persistence_status}`}><Check size={13} />{portfolio.persistence_status === "saved" ? "자동 저장됨" : "현재 실행 중 임시 저장"}</small>}
        </div>
        <button className="paper-reset" onClick={() => setConfirmReset(true)} title="모의 계좌 초기화" type="button">
          <RotateCcw size={16} /><span>초기화</span>
        </button>
      </header>

      <div className="paper-summary" aria-label={`${normalizedCurrency} 모의 계좌 요약`}>
        <div><WalletCards size={17} /><span>총 자산</span><b>{totals ? money(totals.equity, normalizedCurrency) : "-"}</b></div>
        <div><span>주문 가능</span><b>{totals ? money(totals.cash, normalizedCurrency) : "-"}</b></div>
        <div><span>평가 손익</span><b className={Number(totals?.unrealized_pnl ?? 0) < 0 ? "loss" : "gain"}>{totals ? money(totals.unrealized_pnl, normalizedCurrency) : "-"}</b></div>
      </div>

      {risk && (
        <div className={`paper-risk-strip ${risk.status}`}>
          <div>
            <ShieldCheck size={16} />
            <span>포트폴리오 위험</span>
            <b>{risk.status === "stable" ? "안정" : risk.status === "caution" ? "주의" : "높음"}</b>
          </div>
          <div className="paper-risk-meter">
            <span>투자 비중 {investedPercent.toFixed(1)}%</span>
            <div aria-label={`투자 비중 ${investedPercent.toFixed(1)}%`} aria-valuemax={100} aria-valuemin={0} aria-valuenow={investedPercent} role="progressbar">
              <i style={{ width: `${investedPercent}%` }} />
            </div>
          </div>
          <small>1회 {riskLimits[0]}% · 종목당 {riskLimits[1]}% · 총 투자 {riskLimits[2]}% 한도</small>
        </div>
      )}

      <div className="paper-workspace">
        <form className="paper-order" onSubmit={submit}>
          <div className="paper-symbol"><b>{name}</b><span>{symbol} · {normalizedCurrency}</span></div>
          <div className="paper-side" role="group" aria-label="주문 방향">
            <button aria-pressed={side === "buy"} onClick={() => setSide("buy")} type="button"><ArrowDownToLine size={15} />매수</button>
            <button aria-pressed={side === "sell"} onClick={() => setSide("sell")} type="button"><ArrowUpFromLine size={15} />매도</button>
          </div>
          <label>
            <span>수량</span>
            <div><input inputMode="decimal" min="0.000001" max="1000000" onChange={(event) => setQuantity(event.target.value)} step="0.000001" type="number" value={quantity} />
              {side === "sell" && selectedPosition && <button onClick={() => setQuantity(selectedPosition.quantity)} type="button">전량</button>}
            </div>
          </label>
          <div className="paper-estimate"><span>예상 주문금액</span><b>{money(estimate, normalizedCurrency)}</b><small>모의 수수료 0.1% 별도</small></div>
          <button className={`paper-submit ${side}`} disabled={!portfolio || pending || estimate <= 0} type="submit">
            {pending ? "처리 중" : `${side === "buy" ? "매수" : "매도"} 주문`}
          </button>
          {error && <p className="paper-error" role="alert">{error}</p>}
        </form>

        <div className="paper-ledger">
          <section aria-labelledby="paper-positions-title">
            <h4 id="paper-positions-title">보유 종목 <small>{portfolio?.positions.length ?? 0}</small></h4>
            {portfolio?.positions.length ? (
              <div className="paper-table-wrap"><table><thead><tr><th>종목</th><th>수량</th><th>평가금액</th><th>수익률</th></tr></thead><tbody>
                {portfolio.positions.map((position) => <tr key={position.symbol}><td><b>{position.name}</b><span>{position.symbol}</span></td><td>{Number(position.quantity).toLocaleString()}</td><td>{money(position.market_value, position.currency)}</td><td className={Number(position.return_percent) < 0 ? "loss" : "gain"}>{Number(position.return_percent).toFixed(2)}%</td></tr>)}
              </tbody></table></div>
            ) : <p className="paper-empty">아직 보유한 모의 종목이 없습니다.</p>}
          </section>
          <section aria-labelledby="paper-orders-title">
            <h4 id="paper-orders-title"><History size={15} /> 최근 체결</h4>
            {portfolio?.orders.length ? <ul className="paper-orders">{portfolio.orders.slice(0, 5).map((order) => <li key={order.order_id}><span className={order.side}>{order.side === "buy" ? "매수" : "매도"}</span><b>{order.name}</b><em>{Number(order.quantity).toLocaleString()}주 · {money(order.fill_price, order.currency)}</em></li>)}</ul> : <p className="paper-empty">체결 내역이 없습니다.</p>}
          </section>
        </div>
      </div>

      {confirmReset && <div className="paper-confirm" role="alertdialog" aria-modal="true" aria-labelledby="paper-confirm-title"><div><h4 id="paper-confirm-title">모의 계좌를 초기화할까요?</h4><p>보유 종목과 체결 내역이 모두 삭제됩니다. 실제 계좌에는 영향이 없습니다.</p><footer><button onClick={() => setConfirmReset(false)} type="button">취소</button><button disabled={pending} onClick={reset} type="button">초기화</button></footer></div></div>}
    </section>
  );
}
