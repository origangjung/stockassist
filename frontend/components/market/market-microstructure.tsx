"use client";

/** 호가·최근 체결·투자 유의와 가격 제한을 종목 차트 아래에서 전환해 확인한다. */

import { useQuery } from "@tanstack/react-query";
import { AlertTriangle, ListTree, RefreshCw, Rows3 } from "lucide-react";
import { useState } from "react";
import { fetchStockMicrostructure } from "../../lib/market-api";

type MarketDetailTab = "orderbook" | "trades" | "warnings";

/** MarketMicrostructureProps 인터페이스는 종목 검색·차트·시장 데이터 화면을 담당합니다.에서 교환하는 필드 계약을 정의합니다. */
interface MarketMicrostructureProps {
  currency: string;
  symbol: string;
}

/** `formatNumber`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
function formatNumber(value: string, maximumFractionDigits = 2): string {
  const parsed = Number(value);
  return Number.isFinite(parsed)
    ? parsed.toLocaleString("ko-KR", { maximumFractionDigits })
    : value;
}

const pressureLabels = {
  buying: "매수세 우위",
  selling: "매도세 우위",
  balanced: "매수·매도 균형",
  unavailable: "압력 계산 불가",
} as const;

/** `MarketMicrostructure`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export function MarketMicrostructure({ currency, symbol }: MarketMicrostructureProps) {
  const [tab, setTab] = useState<MarketDetailTab>("orderbook");
  const details = useQuery({
    queryKey: ["stock-microstructure", symbol],
    queryFn: ({ signal }) => fetchStockMicrostructure(symbol, signal),
    staleTime: 10_000,
    retry: 1,
  });

  return (
    <section className="market-depth" aria-label={`${symbol} 실시간 시장 상세`}>
      <header>
        <div><span>MARKET DEPTH</span><b>호가와 체결</b></div>
        <div className="market-depth__tabs" role="tablist" aria-label="시장 상세 선택">
          <button aria-selected={tab === "orderbook"} onClick={() => setTab("orderbook")} role="tab" type="button"><ListTree size={14} />호가</button>
          <button aria-selected={tab === "trades"} onClick={() => setTab("trades")} role="tab" type="button"><Rows3 size={14} />체결</button>
          <button aria-selected={tab === "warnings"} onClick={() => setTab("warnings")} role="tab" type="button"><AlertTriangle size={14} />유의</button>
        </div>
      </header>

      {details.isLoading && <p className="market-depth__state"><RefreshCw className="spin" size={14} /> 토스 데이터를 불러오는 중입니다</p>}
      {details.isError && <p className="market-depth__state">현재 호가와 체결 정보를 표시할 수 없습니다.</p>}
      {details.data && (
        <div className={`market-depth__pressure ${details.data.pressure.signal}`}>
          <div>
            <span>실시간 주문 압력</span>
            <strong>{pressureLabels[details.data.pressure.signal]}</strong>
            <small>{details.data.pressure.is_estimate ? "일부 체결 방향 추정 포함" : "체결 방향 확인"}</small>
          </div>
          <b>{details.data.pressure.score > 0 ? "+" : ""}{Math.round(details.data.pressure.score * 100)}</b>
          <div aria-label="매도와 매수 압력 비율" className="market-depth__pressure-track">
            <i style={{ width: `${Math.max(0, Math.min(100, (details.data.pressure.score + 1) * 50))}%` }} />
          </div>
        </div>
      )}
      {details.data && tab === "orderbook" && (
        <div className="market-depth__orderbook" role="tabpanel">
          <div><span>매도 잔량</span>{details.data.orderbook.asks.slice(0, 6).reverse().map((level) => <p key={`ask-${level.price}`}><em>{formatNumber(level.quantity, 6)}</em><b>{formatNumber(level.price)}</b></p>)}</div>
          <div><span>매수 잔량</span>{details.data.orderbook.bids.slice(0, 6).map((level) => <p key={`bid-${level.price}`}><b>{formatNumber(level.price)}</b><em>{formatNumber(level.quantity, 6)}</em></p>)}</div>
        </div>
      )}
      {details.data && tab === "trades" && (
        <div className="market-depth__trades" role="tabpanel">
          {details.data.trades.slice(0, 10).map((trade) => <p key={`${trade.executed_at}-${trade.price}`}><time>{new Date(trade.executed_at).toLocaleTimeString("ko-KR", { hour: "2-digit", minute: "2-digit", second: "2-digit" })}</time><b>{currency} {formatNumber(trade.price)}</b><span>{formatNumber(trade.quantity, 6)}주</span></p>)}
          {!details.data.trades.length && <p className="market-depth__state">오늘 체결 내역이 없습니다.</p>}
        </div>
      )}
      {details.data && tab === "warnings" && (
        <div className="market-depth__warnings" role="tabpanel">
          <div className="market-depth__limits"><span>하한가 <b>{details.data.price_limit.lowerLimitPrice ? formatNumber(details.data.price_limit.lowerLimitPrice) : "없음"}</b></span><span>상한가 <b>{details.data.price_limit.upperLimitPrice ? formatNumber(details.data.price_limit.upperLimitPrice) : "없음"}</b></span></div>
          {details.data.warnings.map((warning) => <p key={`${warning.warning_type}-${warning.start_date}`}><AlertTriangle size={14} /><b>{warning.warning_type}</b><span>{warning.start_date ?? "시작일 미제공"}{warning.end_date ? ` ~ ${warning.end_date}` : ""}</span></p>)}
          {!details.data.warnings.length && <p className="market-depth__state">현재 확인된 매수 유의사항이 없습니다.</p>}
        </div>
      )}
    </section>
  );
}
