"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { FormEvent, useEffect, useState } from "react";
import {
  fetchCandles,
  fetchQuote,
  fetchStockSnapshot,
  quoteWebSocketUrl,
  type CandleInterval,
  type MarketQuote,
  type RealtimeError,
  type RealtimeQuote,
} from "../lib/market-api";
import { AnalysisResult } from "./analysis-result";
import { ResearchDetails } from "./research-details";
import { StockChart } from "./stock-chart";
import { TechnicalSnapshot } from "./technical-snapshot";

interface DashboardStock {
  symbol: string;
  name: string;
  market: string;
  currency: string;
}

const initialStocks: DashboardStock[] = [
  { symbol: "005930", name: "삼성전자", market: "KOSPI", currency: "KRW" },
  { symbol: "000660", name: "SK하이닉스", market: "KOSPI", currency: "KRW" },
  { symbol: "035420", name: "NAVER", market: "KOSDAQ", currency: "KRW" },
  { symbol: "AAPL", name: "Apple", market: "NASDAQ", currency: "USD" },
  { symbol: "MSFT", name: "Microsoft", market: "NASDAQ", currency: "USD" },
  { symbol: "NVDA", name: "NVIDIA", market: "NASDAQ", currency: "USD" },
  { symbol: "TSLA", name: "Tesla", market: "NASDAQ", currency: "USD" },
];

const intervals: Array<{ value: CandleInterval; label: string }> = [
  { value: "1d", label: "일" },
  { value: "1w", label: "주" },
  { value: "1M", label: "월" },
];

type RealtimeStatus = "connecting" | "live" | "reconnecting" | "unavailable";

function useRealtimeQuote(symbol: string) {
  const [quote, setQuote] = useState<RealtimeQuote | null>(null);
  const [status, setStatus] = useState<RealtimeStatus>("connecting");

  useEffect(() => {
    let socket: WebSocket | null = null;
    let retryTimer: ReturnType<typeof setTimeout> | null = null;
    let retryCount = 0;
    let stopped = false;

    setQuote(null);
    setStatus("connecting");

    const connect = () => {
      socket = new WebSocket(quoteWebSocketUrl(symbol));
      socket.onopen = () => {
        retryCount = 0;
        setStatus("live");
      };
      socket.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data) as RealtimeQuote | RealtimeError;
          if (message.type === "quote") {
            setQuote(message);
            setStatus("live");
          } else {
            setStatus("unavailable");
          }
        } catch {
          setStatus("unavailable");
        }
      };
      socket.onclose = (event) => {
        if (stopped) return;
        if ([4400, 4403, 4404].includes(event.code) || retryCount >= 5) {
          setStatus("unavailable");
          return;
        }
        retryCount += 1;
        setStatus("reconnecting");
        retryTimer = setTimeout(connect, Math.min(1000 * 2 ** retryCount, 10000));
      };
      socket.onerror = () => socket?.close();
    };

    connect();
    return () => {
      stopped = true;
      if (retryTimer !== null) clearTimeout(retryTimer);
      socket?.close();
    };
  }, [symbol]);

  return { quote, status };
}

function formatPrice(price: string, currency: string) {
  const value = Number(price);
  const formatted = Number.isFinite(value)
    ? new Intl.NumberFormat(currency === "KRW" ? "ko-KR" : "en-US", {
        minimumFractionDigits: currency === "KRW" ? 0 : 2,
        maximumFractionDigits: currency === "KRW" ? 0 : 2,
      }).format(value)
    : price;
  return `${currency === "USD" ? "$" : "₩"} ${formatted}`;
}

function formatChange(value: string | null | undefined) {
  if (value == null) return "—";
  const number = Number(value);
  if (!Number.isFinite(number)) return "—";
  return `${number >= 0 ? "+" : ""}${number.toFixed(2)}%`;
}

export function MarketDashboard() {
  const queryClient = useQueryClient();
  const [stocks, setStocks] = useState(initialStocks);
  const [symbol, setSymbol] = useState("005930");
  const [interval, setInterval] = useState<CandleInterval>("1d");
  const [searchValue, setSearchValue] = useState("");
  const [searchError, setSearchError] = useState<string | null>(null);
  const [searching, setSearching] = useState(false);
  const selected = stocks.find((stock) => stock.symbol === symbol) ?? stocks[0];
  const realtime = useRealtimeQuote(symbol);
  const quoteQuery = useQuery({
    queryKey: ["quote", symbol],
    queryFn: () => fetchQuote(symbol),
    refetchInterval: 5000,
    retry: 1,
    staleTime: 3000,
  });
  const candleQuery = useQuery({
    queryKey: ["candles", symbol, interval],
    queryFn: () => fetchCandles(symbol, interval),
  });
  const displayedQuote: RealtimeQuote | MarketQuote | undefined =
    realtime.quote ?? quoteQuery.data;
  const currency = displayedQuote?.currency ?? selected.currency;

  const search = async (event: FormEvent) => {
    event.preventDefault();
    const normalized = searchValue.trim().toUpperCase();
    setSearchError(null);
    if (!/^[0-9A-Z.-]{1,16}$/.test(normalized)) {
      setSearchError("종목 코드는 영문, 숫자, 점 또는 하이픈 1~16자로 입력하세요.");
      return;
    }

    setSearching(true);
    try {
      const snapshot = await fetchStockSnapshot(normalized);
      const stock: DashboardStock = {
        symbol: snapshot.stock.symbol,
        name: snapshot.stock.name,
        market: snapshot.stock.market,
        currency: snapshot.stock.currency ?? snapshot.quote.currency ?? "KRW",
      };
      setStocks((current) => [stock, ...current.filter((item) => item.symbol !== stock.symbol)].slice(0, 12));
      queryClient.setQueryData(["quote", stock.symbol], snapshot.quote);
      setSymbol(stock.symbol);
      setSearchValue("");
    } catch (reason) {
      setSearchError(reason instanceof Error ? reason.message : "종목을 찾지 못했습니다.");
    } finally {
      setSearching(false);
    }
  };

  return (
    <>
      <section className="market-toolbar">
        <div><span>MARKET UNIVERSE</span><b>국내 · 미국 종목</b></div>
        <form onSubmit={search}>
          <input
            aria-label="종목 코드 검색"
            maxLength={16}
            onChange={(event) => setSearchValue(event.target.value)}
            placeholder="005930, AAPL, JPM"
            value={searchValue}
          />
          <button disabled={searching} type="submit">{searching ? "조회 중" : "종목 조회"}</button>
        </form>
      </section>
      {searchError && <div className="market-search-error" role="alert">{searchError}</div>}

      <section className="stock-tabs" aria-label="종목 선택">
        {stocks.map((stock) => (
          <button
            className={stock.symbol === symbol ? "active" : ""}
            key={stock.symbol}
            onClick={() => setSymbol(stock.symbol)}
            type="button"
          >
            <span>{stock.name}</span><small>{stock.symbol} · {stock.market}</small>
          </button>
        ))}
      </section>

      <section className="chart-panel">
        <header>
          <div>
            <p>
              {selected.symbol} • {selected.market}
              <span className={`live-status ${realtime.status}`}>{realtime.status}</span>
            </p>
            <h2>{displayedQuote?.name ?? selected.name}</h2>
            <strong>{displayedQuote ? formatPrice(displayedQuote.price, currency) : "—"}</strong>
            <em className={(Number(displayedQuote?.change_percent ?? 0) < 0) ? "negative-text" : ""}>
              {formatChange(displayedQuote?.change_percent)}
            </em>
            {quoteQuery.isError && <small className="quote-warning">REST 현재가를 불러오지 못했습니다.</small>}
          </div>
          <div className="intervals">
            {intervals.map((item) => (
              <button
                className={item.value === interval ? "active" : ""}
                key={item.value}
                onClick={() => setInterval(item.value)}
                type="button"
              >
                {item.label}
              </button>
            ))}
          </div>
        </header>
        {candleQuery.isPending && <div className="chart-state">차트 데이터를 불러오는 중입니다.</div>}
        {candleQuery.isError && (
          <div className="chart-state error">
            <b>API 연결 실패</b><span>{candleQuery.error.message}</span>
            <button onClick={() => candleQuery.refetch()} type="button">다시 시도</button>
          </div>
        )}
        {candleQuery.data && (
          <>
            <StockChart candles={candleQuery.data.candles} />
            <footer>
              <span>{candleQuery.data.provider} • 집계 {candleQuery.data.aggregation_version}</span>
              <span>원본 {candleQuery.data.raw_count}개 • 품질 알림 {candleQuery.data.quality_logs.length}건</span>
            </footer>
          </>
        )}
      </section>
      <TechnicalSnapshot symbol={symbol} currency={currency} />
      <ResearchDetails symbol={symbol} currency={currency} />
      <AnalysisResult symbol={symbol} name={selected.name} currency={currency} />
    </>
  );
}
