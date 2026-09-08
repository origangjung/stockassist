"use client";

/** 목표 투자비중을 만들고 각 제안을 확인 후 모의주문으로 적용하는 화면이다. */
import { useEffect, useMemo, useState } from "react";
import { Check, ChevronDown, LoaderCircle, PieChart, ShieldCheck } from "lucide-react";
import {
  createAllocationProposal,
  createPaperOrder,
  getPaperAccountId,
  type FundAllocationProposal,
} from "../../lib/paper-api";
import { stockCatalog } from "../../lib/stock-catalog";

type Currency = "KRW" | "USD";
type Objective = "min_volatility" | "max_sharpe";

const DEFAULT_SYMBOLS: Record<Currency, string[]> = {
  KRW: ["005930", "000660", "035420"],
  USD: ["AAPL", "MSFT", "NVDA"],
};

interface FundAllocationPlannerProps {
  currency: Currency;
  onPortfolioChanged: () => Promise<void>;
}

function percent(value: string | number) {
  return `${(Number(value) * 100).toFixed(1)}%`;
}

function money(value: string | number, currency: Currency) {
  return new Intl.NumberFormat("ko-KR", {
    style: "currency",
    currency,
    maximumFractionDigits: currency === "KRW" ? 0 : 2,
  }).format(Number(value));
}

/** 통화별 종목 선택, 운용 성향, 투자 한도를 하나의 제안 요청으로 조합한다. */
export function FundAllocationPlanner({ currency, onPortfolioChanged }: FundAllocationPlannerProps) {
  const candidates = useMemo(
    () => stockCatalog.filter((stock) => stock.currency === currency),
    [currency],
  );
  const [symbols, setSymbols] = useState<string[]>(DEFAULT_SYMBOLS[currency]);
  const [objective, setObjective] = useState<Objective>("min_volatility");
  const [investPercent, setInvestPercent] = useState(90);
  const [proposal, setProposal] = useState<FundAllocationProposal | null>(null);
  const [pending, setPending] = useState(false);
  const [applyingSymbol, setApplyingSymbol] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setSymbols(DEFAULT_SYMBOLS[currency]);
    setProposal(null);
    setError(null);
  }, [currency]);

  function toggleSymbol(symbol: string) {
    setProposal(null);
    setSymbols((current) => (
      current.includes(symbol)
        ? current.filter((item) => item !== symbol)
        : current.length < 8 ? [...current, symbol] : current
    ));
  }

  async function analyze() {
    setPending(true);
    setError(null);
    try {
      setProposal(await createAllocationProposal(getPaperAccountId(), {
        symbols,
        objective,
        invest_ratio: (investPercent / 100).toFixed(2),
        max_asset_weight: "0.40",
        lookback_days: 180,
      }));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "자금배분 제안을 만들지 못했습니다.");
    } finally {
      setPending(false);
    }
  }

  async function applyAction(action: FundAllocationProposal["rebalance_actions"][number]) {
    setApplyingSymbol(action.symbol);
    setError(null);
    try {
      await createPaperOrder(getPaperAccountId(), {
        symbol: action.symbol,
        side: action.side,
        quantity: action.quantity,
        idempotency_key: crypto.randomUUID(),
      });
      await onPortfolioChanged();
      setProposal(null);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "모의주문을 적용하지 못했습니다.");
    } finally {
      setApplyingSymbol(null);
    }
  }

  const canAnalyze = symbols.length >= 3 && symbols.length <= 8 && !pending;

  return (
    <section className="fund-planner" aria-labelledby="fund-planner-title">
      <header>
        <div><PieChart size={19} /><div><h2 id="fund-planner-title">AI 자금배분</h2><span>과거 변동성과 수익률로 목표 비중을 계산해요</span></div></div>
        <strong><ShieldCheck size={14} /> 모의투자 전용</strong>
      </header>

      <div className="fund-settings">
        <div className="fund-objective" role="group" aria-label="운용 목표">
          <button aria-pressed={objective === "min_volatility"} onClick={() => { setObjective("min_volatility"); setProposal(null); }} type="button">안정형</button>
          <button aria-pressed={objective === "max_sharpe"} onClick={() => { setObjective("max_sharpe"); setProposal(null); }} type="button">균형형</button>
        </div>
        <label className="fund-investment-range">
          <span>주식 투자 비중 <b>{investPercent}%</b></span>
          <input aria-label="주식 투자 비중" max="95" min="50" onChange={(event) => { setInvestPercent(Number(event.target.value)); setProposal(null); }} step="5" type="range" value={investPercent} />
          <small>현금 {100 - investPercent}%를 남겨요</small>
        </label>
      </div>

      <details className="fund-universe">
        <summary>분석 종목 <b>{symbols.length}개</b><ChevronDown size={16} /></summary>
        <div>{candidates.map((stock) => (
          <button aria-pressed={symbols.includes(stock.symbol)} key={stock.symbol} onClick={() => toggleSymbol(stock.symbol)} type="button">
            <span>{stock.symbol.slice(0, 2)}</span><b>{stock.name}</b><small>{stock.symbol}</small>{symbols.includes(stock.symbol) && <Check size={14} />}
          </button>
        ))}</div>
        <small>위험 한도를 지키려면 최소 3개, 최대 8개를 선택해 주세요.</small>
      </details>

      <button className="fund-analyze" disabled={!canAnalyze} onClick={() => void analyze()} type="button">
        {pending ? <><LoaderCircle className="is-spinning" size={17} /> 계산 중</> : "목표 비중 계산하기"}
      </button>
      {error && <p className="fund-error" role="alert">{error}</p>}

      {proposal && (
        <div className="fund-result" aria-live="polite">
          <header><div><span>추천 포트폴리오</span><b>{proposal.objective === "min_volatility" ? "변동성을 낮춘 배분" : "위험 대비 수익을 높인 배분"}</b></div><small>{proposal.observation_count}개 관측치 · {proposal.optimizer}</small></header>
          <div className="fund-weight-list">
            {Object.entries(proposal.target_weights).sort((a, b) => Number(b[1]) - Number(a[1])).map(([symbol, weight]) => (
              <div key={symbol}><span><b>{symbol}</b><em>{percent(weight)}</em></span><i><em style={{ width: percent(weight) }} /></i></div>
            ))}
            <div className="cash"><span><b>현금</b><em>{percent(proposal.target_cash_weight)}</em></span><i><em style={{ width: percent(proposal.target_cash_weight) }} /></i></div>
          </div>
          <div className="fund-actions">
            <h3>이번에 조정할 항목</h3>
            {proposal.rebalance_actions.length ? proposal.rebalance_actions.map((action) => (
              <article key={`${action.side}:${action.symbol}`}>
                <div><span className={action.side}>{action.side === "buy" ? "매수" : "매도"}</span><b>{action.symbol}</b><small>{Number(action.quantity).toLocaleString("ko-KR")}주 · {money(action.notional, currency)}</small></div>
                <button disabled={applyingSymbol !== null} onClick={() => void applyAction(action)} type="button">
                  {applyingSymbol === action.symbol ? <LoaderCircle className="is-spinning" size={15} /> : "모의주문"}
                </button>
                {action.reason === "staged_for_order_limit" && <p>1회 30% 한도에 맞춘 1단계 주문이에요.</p>}
              </article>
            )) : <p>현재 비중이 목표 범위 안에 있어 조정할 항목이 없어요.</p>}
          </div>
          <footer>제안은 자동 실행되지 않으며, 각 모의주문을 직접 확인해야 반영됩니다.</footer>
        </div>
      )}
    </section>
  );
}
