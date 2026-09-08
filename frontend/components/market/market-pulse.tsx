"use client";

/** 토스 시장 지표·환율·거래대금 상위를 한 줄 시장 브리핑으로 보여준다. */

import { useQuery } from "@tanstack/react-query";
import { ArrowDownRight, ArrowUpRight, Clock3, RefreshCw } from "lucide-react";
import { fetchMarketOverview } from "../../lib/market-api";

/** MarketPulseProps 인터페이스는 종목 검색·차트·시장 데이터 화면을 담당합니다.에서 교환하는 필드 계약을 정의합니다. */
interface MarketPulseProps {
  onSelectSymbol: (symbol: string) => void;
}

const indicatorNames: Record<string, string> = {
  KOSPI: "코스피",
  KOSDAQ: "코스닥",
  KR_BOND_10Y: "국채 10년",
};

/** `MarketPulse`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export function MarketPulse({ onSelectSymbol }: MarketPulseProps) {
  const overview = useQuery({
    queryKey: ["toss-market-overview"],
    queryFn: ({ signal }) => fetchMarketOverview(signal),
    staleTime: 60_000,
    retry: 1,
  });

  if (overview.isError) return null;
  if (overview.isLoading || !overview.data) {
    return (
      <section aria-label="시장 현황 불러오는 중" className="market-pulse market-pulse--loading">
        <RefreshCw aria-hidden="true" size={14} /> 토스 시장 데이터를 확인하고 있습니다
      </section>
    );
  }

  const indicators = overview.data.indicators.filter((item) => indicatorNames[item.symbol]);
  const leaders = [
    ...(overview.data.rankings.KR?.rankings ?? []).slice(0, 2),
    ...(overview.data.rankings.US?.rankings ?? []).slice(0, 2),
  ];
  const rateDirection = overview.data.exchange_rate?.rateChangeType;

  return (
    <section aria-label="오늘의 시장 현황" className="market-pulse">
      <div className="market-pulse__metrics">
        {indicators.map((indicator) => (
          <div key={indicator.symbol}>
            <span>{indicatorNames[indicator.symbol]}</span>
            <strong>{Number(indicator.lastPrice).toLocaleString("ko-KR")}</strong>
          </div>
        ))}
        {overview.data.exchange_rate && (
          <div>
            <span>달러 환율</span>
            <strong>
              {Number(overview.data.exchange_rate.rate).toLocaleString("ko-KR")}
              {rateDirection === "UP" ? <ArrowUpRight aria-hidden="true" size={14} /> : null}
              {rateDirection === "DOWN" ? <ArrowDownRight aria-hidden="true" size={14} /> : null}
            </strong>
          </div>
        )}
      </div>
      <div className="market-pulse__leaders">
        <span><Clock3 aria-hidden="true" size={13} /> 거래대금 상위</span>
        {leaders.map((item) => (
          <button key={`${item.currency}-${item.symbol}`} onClick={() => onSelectSymbol(item.symbol)} type="button">
            {item.symbol}
          </button>
        ))}
      </div>
    </section>
  );
}
