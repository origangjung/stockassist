"use client";

/** 토스 시장 지표와 랭킹을 탐색 가능한 독립 화면으로 구성한다. */

import { useQuery } from "@tanstack/react-query";
import { BarChart3, Landmark, RefreshCw, Search, TrendingDown, TrendingUp } from "lucide-react";
import { useState } from "react";
import {
  fetchMarketIndicatorHistory,
  fetchMarketOverview,
  fetchMarketRankings,
  type TossRankingType,
} from "../../lib/market-api";

const rankingOptions: Array<{ value: TossRankingType; label: string }> = [
  { value: "MARKET_TRADING_AMOUNT", label: "거래대금" },
  { value: "MARKET_TRADING_VOLUME", label: "거래량" },
  { value: "TOP_GAINERS", label: "상승" },
  { value: "TOP_LOSERS", label: "하락" },
  { value: "TOSS_SECURITIES_TRADING_AMOUNT", label: "토스 거래대금" },
  { value: "TOSS_SECURITIES_TRADING_VOLUME", label: "토스 거래량" },
];

const indicatorLabels: Record<string, string> = {
  KOSPI: "코스피",
  KOSDAQ: "코스닥",
  KR_BOND_2Y: "국채 2년",
  KR_BOND_3Y: "국채 3년",
  KR_BOND_5Y: "국채 5년",
  KR_BOND_10Y: "국채 10년",
  KR_BOND_20Y: "국채 20년",
  KR_BOND_30Y: "국채 30년",
};

/** `compactNumber`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
function compactNumber(value: string): string {
  const number = Number(value);
  return Number.isFinite(number)
    ? new Intl.NumberFormat("ko-KR", { notation: "compact", maximumFractionDigits: 1 }).format(number)
    : value;
}

/** `MarketOverviewDashboard`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export function MarketOverviewDashboard() {
  const [country, setCountry] = useState<"KR" | "US">("KR");
  const [rankingType, setRankingType] = useState<TossRankingType>("MARKET_TRADING_AMOUNT");
  const [indicator, setIndicator] = useState("KOSPI");
  const overview = useQuery({
    queryKey: ["toss-market-overview"],
    queryFn: ({ signal }) => fetchMarketOverview(signal),
    staleTime: 60_000,
  });
  const rankings = useQuery({
    queryKey: ["toss-market-rankings", country, rankingType],
    queryFn: ({ signal }) => fetchMarketRankings(rankingType, country, "1d", signal),
    staleTime: 30_000,
  });
  const history = useQuery({
    queryKey: ["toss-market-indicator", indicator],
    queryFn: ({ signal }) => fetchMarketIndicatorHistory(indicator, signal),
    staleTime: 60_000,
  });

  return (
    <div className="market-overview-page">
      <header className="market-overview-heading">
        <div>
          <span>MARKET NOW</span>
          <h1>오늘 시장 한눈에 보기</h1>
          <p>토스증권의 국내·미국 시장 지표와 거래 흐름을 한 화면에서 비교합니다.</p>
        </div>
        <a href="/#market-search"><Search size={16} /> 종목 검색</a>
      </header>

      {overview.isPending && <div className="market-overview-state"><RefreshCw className="spin" size={16} /> 시장을 확인하고 있습니다.</div>}
      {overview.isError && <div className="market-overview-state market-overview-state--error">시장 요약을 불러오지 못했습니다.</div>}
      {overview.data && (
        <section aria-label="주요 시장 지표" className="market-indicator-strip">
          {overview.data.indicators.map((item) => (
            <button aria-pressed={indicator === item.symbol} key={item.symbol} onClick={() => setIndicator(item.symbol)} type="button">
              <span>{indicatorLabels[item.symbol] ?? item.symbol}</span>
              <strong>{Number(item.lastPrice).toLocaleString("ko-KR")}{item.symbol.startsWith("KR_BOND") ? "%" : ""}</strong>
            </button>
          ))}
          {overview.data.exchange_rate && (
            <div><span>USD/KRW</span><strong>{Number(overview.data.exchange_rate.rate).toLocaleString("ko-KR")}</strong></div>
          )}
        </section>
      )}

      <div className="market-overview-grid">
        <section className="market-ranking-panel">
          <header>
            <div><span>RANKING</span><h2>시장 랭킹</h2></div>
            <div className="market-country-control" role="group" aria-label="시장 선택">
              {(["KR", "US"] as const).map((value) => <button aria-pressed={country === value} key={value} onClick={() => setCountry(value)} type="button">{value === "KR" ? "국내" : "미국"}</button>)}
            </div>
          </header>
          <div className="market-ranking-tabs" role="tablist" aria-label="랭킹 기준">
            {rankingOptions.map((option) => <button aria-selected={rankingType === option.value} key={option.value} onClick={() => setRankingType(option.value)} role="tab" type="button">{option.label}</button>)}
          </div>
          {rankings.isPending && <div className="market-overview-state"><RefreshCw className="spin" size={15} /> 랭킹 집계 중</div>}
          {rankings.isError && <div className="market-overview-state market-overview-state--error">랭킹을 불러오지 못했습니다.</div>}
          {rankings.data && (
            <div className="market-ranking-list">
              {rankings.data.rankings.map((item) => {
                const changeRate = Number(item.price.changeRate ?? 0) * 100;
                return (
                  <a href={`/?symbol=${encodeURIComponent(item.symbol)}`} key={item.symbol}>
                    <span className="market-ranking-position">{item.rank}</span>
                    <b>{item.symbol}</b>
                    <span>{item.currency} {Number(item.price.lastPrice).toLocaleString("ko-KR")}</span>
                    <em data-direction={changeRate > 0 ? "up" : changeRate < 0 ? "down" : "flat"}>{changeRate > 0 ? <TrendingUp size={14} /> : changeRate < 0 ? <TrendingDown size={14} /> : null}{changeRate.toFixed(2)}%</em>
                    <small>{rankingType.includes("VOLUME") ? compactNumber(item.tradingVolume) : compactNumber(item.tradingAmount)}</small>
                  </a>
                );
              })}
              {!rankings.data.rankings.length && <div className="market-overview-state">현재 집계된 종목이 없습니다.</div>}
            </div>
          )}
        </section>

        <section className="market-flow-panel">
          <header><div><span>INDICATOR FLOW</span><h2>{indicatorLabels[indicator] ?? indicator} 30일</h2></div><Landmark size={19} /></header>
          {history.isPending && <div className="market-overview-state"><RefreshCw className="spin" size={15} /> 지표 흐름 확인 중</div>}
          {history.isError && <div className="market-overview-state market-overview-state--error">지표 흐름을 불러오지 못했습니다.</div>}
          {history.data && (
            <>
              <div className="market-mini-chart" aria-label={`${indicator} 최근 30일 종가`}>
                {history.data.candles.candles.slice().reverse().map((candle) => {
                  const open = Number(candle.openPrice);
                  const close = Number(candle.closePrice);
                  const high = Number(candle.highPrice);
                  const low = Number(candle.lowPrice);
                  const range = Math.max(high - low, 0.0001);
                  return <i data-direction={close >= open ? "up" : "down"} key={candle.timestamp} style={{ height: `${Math.max(10, Math.min(100, ((close - low) / range) * 80 + 10))}%` }} />;
                })}
              </div>
              <div className="market-flow-summary"><BarChart3 size={16} /><span>최신 종가</span><strong>{history.data.candles.candles[0]?.closePrice ?? "-"}</strong></div>
              <p>지수는 투자자별 매매대금도 함께 수집하며, 국채는 공식 일봉 기준으로 표시합니다.</p>
            </>
          )}
        </section>
      </div>
    </div>
  );
}
