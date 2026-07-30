"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { FormEvent, KeyboardEvent, useEffect, useRef, useState } from "react";
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
import { AnalystAvatar, type MeetingAgentKey } from "./agent-meeting-stage";
import { ResearchDetails } from "./research-details";
import { StockChart } from "./stock-chart";
import { TechnicalSnapshot } from "./technical-snapshot";
import {
  readStoredItems,
  toggleStoredSymbol,
  writeStoredItems,
} from "../lib/browser-watchlist";
import { stockResultUrl } from "../lib/share-url";
import {
  filterStocksBySearch,
  findSimilarStockMatches,
  findStockByExactMatch,
} from "../lib/stock-search";

interface DashboardStock {
  symbol: string;
  name: string;
  market: string;
  currency: string;
  aliases?: string[];
}

const initialStocks: DashboardStock[] = [
  { symbol: "005930", name: "삼성전자", market: "KOSPI", currency: "KRW", aliases: ["삼전", "samsung", "samsung electronics"] },
  { symbol: "000660", name: "SK하이닉스", market: "KOSPI", currency: "KRW", aliases: ["하이닉스", "sk hynix"] },
  { symbol: "035420", name: "NAVER", market: "KOSPI", currency: "KRW", aliases: ["네이버"] },
  { symbol: "AAPL", name: "Apple", market: "NASDAQ", currency: "USD", aliases: ["애플"] },
  { symbol: "MSFT", name: "Microsoft", market: "NASDAQ", currency: "USD", aliases: ["마이크로소프트", "마소"] },
  { symbol: "NVDA", name: "NVIDIA", market: "NASDAQ", currency: "USD", aliases: ["엔비디아", "nvidia"] },
  { symbol: "TSLA", name: "Tesla", market: "NASDAQ", currency: "USD", aliases: ["테슬라"] },
];

const intervals: Array<{ value: CandleInterval; label: string }> = [
  { value: "1d", label: "일" },
  { value: "1w", label: "주" },
  { value: "1M", label: "월" },
];

type RealtimeStatus = "connecting" | "live" | "reconnecting" | "offline" | "unavailable";
type AgentFocus = "all" | "technical" | "financial" | "news" | "investor_flow" | "risk";

const REALTIME_STATUS_LABELS: Record<Exclude<RealtimeStatus, "unavailable">, string> = {
  connecting: "실시간 시세 연결 중",
  live: "실시간 시세 연결됨",
  reconnecting: "실시간 시세 재연결 중",
  offline: "오프라인 · 인터넷 연결 후 자동 재시도",
};
const TERMINAL_WEBSOCKET_CLOSE_CODES = new Set([1013, 4400, 4403, 4404]);

const agentRoster: Array<{ key: MeetingAgentKey; label: string; role: string }> = [
  { key: "technical", label: "차트 셰프", role: "추세 소스" },
  { key: "financial", label: "재무 셰프", role: "가치 육수" },
  { key: "news", label: "뉴스 셰프", role: "이슈 가니시" },
  { key: "investor_flow", label: "수급 셰프", role: "흐름 리덕션" },
  { key: "risk", label: "리스크 셰프", role: "안전 점검" },
];

const RECENT_STOCKS_KEY = "stockpilot:recent-stocks";
const WATCHLIST_STOCKS_KEY = "stockpilot:watchlist-stocks";

type HistoryMode = "none" | "push" | "replace";

const SEARCH_MATCH_LABEL: Record<"name" | "symbol" | "alias", string> = {
  name: "종목명 일치",
  symbol: "티커 일치",
  alias: "별칭 일치",
};

function syncResultUrl(symbol: string, mode: Exclude<HistoryMode, "none"> = "push") {
  const nextUrl = stockResultUrl(symbol);
  if (window.location.href === nextUrl) return;
  if (mode === "push") {
    window.history.pushState({ symbol }, "", nextUrl);
  } else {
    window.history.replaceState({ symbol }, "", nextUrl);
  }
}

function clearResultUrl(mode: Exclude<HistoryMode, "none"> = "push") {
  const nextUrl = new URL(window.location.pathname, window.location.origin).toString();
  if (window.location.href === nextUrl) return;
  if (mode === "push") {
    window.history.pushState({}, "", nextUrl);
  } else {
    window.history.replaceState({}, "", nextUrl);
  }
}

function isDashboardStock(value: unknown): value is DashboardStock {
  if (typeof value !== "object" || value === null) return false;
  const stock = value as Partial<DashboardStock>;
  return (
    typeof stock.symbol === "string"
    && /^[0-9A-Z.-]{1,16}$/.test(stock.symbol)
    && typeof stock.name === "string"
    && typeof stock.market === "string"
    && typeof stock.currency === "string"
    && (stock.aliases === undefined
      || (Array.isArray(stock.aliases) && stock.aliases.every((alias) => typeof alias === "string")))
  );
}

function useRealtimeQuote(symbol: string | null) {
  const [quote, setQuote] = useState<RealtimeQuote | null>(null);
  const [status, setStatus] = useState<RealtimeStatus>("unavailable");
  const [reconnectVersion, setReconnectVersion] = useState(0);

  useEffect(() => {
    if (!symbol) {
      setQuote(null);
      setStatus("unavailable");
      return;
    }

    let socket: WebSocket | null = null;
    let retryTimer: ReturnType<typeof setTimeout> | null = null;
    let retryCount = 0;
    let stopped = false;

    const clearRetryTimer = () => {
      if (retryTimer === null) return;
      clearTimeout(retryTimer);
      retryTimer = null;
    };

    const disconnectSocket = () => {
      const currentSocket = socket;
      socket = null;
      if (currentSocket && currentSocket.readyState < WebSocket.CLOSING) {
        currentSocket.close();
      }
    };

    setQuote(null);

    const connect = () => {
      if (stopped) return;
      if (!navigator.onLine) {
        setStatus("offline");
        return;
      }

      let currentSocket: WebSocket;
      try {
        currentSocket = new WebSocket(quoteWebSocketUrl(symbol));
      } catch {
        setStatus("unavailable");
        return;
      }
      socket = currentSocket;
      currentSocket.onopen = () => {
        if (stopped || socket !== currentSocket) return;
        retryCount = 0;
        setStatus("live");
      };
      currentSocket.onmessage = (event) => {
        if (stopped || socket !== currentSocket) return;
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
      currentSocket.onclose = (event) => {
        if (stopped || socket !== currentSocket) return;
        if (!navigator.onLine) {
          setStatus("offline");
          return;
        }
        if (TERMINAL_WEBSOCKET_CLOSE_CODES.has(event.code) || retryCount >= 5) {
          setStatus("unavailable");
          return;
        }
        retryCount += 1;
        setStatus("reconnecting");
        retryTimer = setTimeout(() => {
          retryTimer = null;
          connect();
        }, Math.min(1000 * 2 ** retryCount, 10_000));
      };
      currentSocket.onerror = () => currentSocket.close();
    };

    const handleOffline = () => {
      clearRetryTimer();
      disconnectSocket();
      setQuote(null);
      setStatus("offline");
    };
    const handleOnline = () => {
      if (stopped) return;
      clearRetryTimer();
      disconnectSocket();
      retryCount = 0;
      setStatus("connecting");
      connect();
    };

    window.addEventListener("offline", handleOffline);
    window.addEventListener("online", handleOnline);
    if (navigator.onLine) {
      setStatus("connecting");
      connect();
    } else {
      setStatus("offline");
    }

    return () => {
      stopped = true;
      clearRetryTimer();
      disconnectSocket();
      window.removeEventListener("offline", handleOffline);
      window.removeEventListener("online", handleOnline);
    };
  }, [symbol, reconnectVersion]);

  return { quote, reconnect: () => setReconnectVersion((current) => current + 1), status };
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
  const [symbol, setSymbol] = useState<string | null>(null);
  const [interval, setInterval] = useState<CandleInterval>("1d");
  const [searchValue, setSearchValue] = useState("");
  const [searchError, setSearchError] = useState<string | null>(null);
  const [searching, setSearching] = useState(false);
  const [revealVersion, setRevealVersion] = useState(0);
  const [activeAgent, setActiveAgent] = useState<AgentFocus>("all");
  const [recentStocks, setRecentStocks] = useState<DashboardStock[]>([]);
  const [watchlistStocks, setWatchlistStocks] = useState<DashboardStock[]>([]);
  const [watchlistNotice, setWatchlistNotice] = useState<string | null>(null);
  const [watchlistStorageMode, setWatchlistStorageMode] = useState<"browser" | "session">("browser");
  const [suggestionListOpen, setSuggestionListOpen] = useState(true);
  const [activeSuggestionIndex, setActiveSuggestionIndex] = useState(-1);
  const resultsRef = useRef<HTMLDivElement>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);
  const queryLookupStarted = useRef(false);
  const lookupRequestId = useRef(0);
  const lookupAbortController = useRef<AbortController | null>(null);
  const selected = symbol ? stocks.find((stock) => stock.symbol === symbol) : undefined;
  const selectedRosterAgent = activeAgent === "all"
    ? null
    : agentRoster.find((agent) => agent.key === activeAgent);
  const realtime = useRealtimeQuote(symbol);
  const activeSymbol = symbol ?? "";
  const quoteQuery = useQuery({
    queryKey: ["quote", symbol],
    queryFn: ({ signal }) => fetchQuote(activeSymbol, signal),
    enabled: Boolean(symbol),
    refetchInterval: 5000,
    retry: 1,
    staleTime: 3000,
  });
  const candleQuery = useQuery({
    queryKey: ["candles", symbol, interval],
    queryFn: ({ signal }) => fetchCandles(activeSymbol, interval, signal),
    enabled: Boolean(symbol),
  });
  const displayedQuote: RealtimeQuote | MarketQuote | undefined =
    realtime.quote ?? quoteQuery.data;
  const currency = displayedQuote?.currency ?? selected?.currency ?? "KRW";
  const realtimeStatusLabel = realtime.status === "unavailable"
    ? displayedQuote
      ? "실시간 시세를 사용할 수 없음 · 현재가는 5초마다 갱신"
      : "현재가를 불러올 수 없음"
    : REALTIME_STATUS_LABELS[realtime.status];

  useEffect(() => {
    if (revealVersion === 0) return;
    const frame = requestAnimationFrame(() => {
      const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      resultsRef.current?.focus({ preventScroll: true });
      resultsRef.current?.scrollIntoView({
        behavior: prefersReducedMotion ? "auto" : "smooth",
        block: "start",
      });
    });
    return () => cancelAnimationFrame(frame);
  }, [revealVersion]);

  useEffect(() => {
    try {
      const saved = JSON.parse(window.localStorage.getItem(RECENT_STOCKS_KEY) ?? "[]") as unknown;
      if (Array.isArray(saved)) {
        setRecentStocks(saved.filter(isDashboardStock).slice(0, 5));
      }
    } catch {
      // Browser storage is an optional convenience, including in private mode.
      try {
        window.localStorage.removeItem(RECENT_STOCKS_KEY);
      } catch {
        // A blocked storage policy should never block stock search.
      }
    }

    const storedWatchlist = readStoredItems(
      window.localStorage,
      WATCHLIST_STOCKS_KEY,
      isDashboardStock,
      20,
    );
    setWatchlistStocks(storedWatchlist.items);
    setWatchlistStorageMode(storedWatchlist.persisted ? "browser" : "session");
  }, []);

  const rememberStock = (stock: DashboardStock) => {
    setRecentStocks((current) => {
      const next = [stock, ...current.filter((item) => item.symbol !== stock.symbol)].slice(0, 5);
      try {
        window.localStorage.setItem(RECENT_STOCKS_KEY, JSON.stringify(next));
      } catch {
        // Retain the in-memory list when persistent storage is unavailable.
      }
      return next;
    });
  };

  const clearRecentStocks = () => {
    setRecentStocks([]);
    setActiveSuggestionIndex(-1);
    try {
      window.localStorage.removeItem(RECENT_STOCKS_KEY);
    } catch {
      // The in-memory list is already cleared when browser storage is unavailable.
    }
  };

  const toggleWatchlist = (stock: DashboardStock) => {
    const next = toggleStoredSymbol(watchlistStocks, stock, 20);
    setWatchlistStocks(next.items);
    setWatchlistNotice(
      next.added
        ? `${stock.name}을(를) 관심 종목에 저장했습니다.`
        : `${stock.name}을(를) 관심 종목에서 제거했습니다.`,
    );
    setWatchlistStorageMode(
      writeStoredItems(window.localStorage, WATCHLIST_STOCKS_KEY, next.items) ? "browser" : "session",
    );
  };

  const lookupStock = async (input: string, historyMode: HistoryMode = "push") => {
    const requestId = ++lookupRequestId.current;
    lookupAbortController.current?.abort();
    lookupAbortController.current = null;
    const rawValue = input.trim();
    const matchedByName = findStockByExactMatch(stocks, rawValue);
    const normalized = matchedByName?.symbol ?? rawValue.toUpperCase();
    setSearchError(null);
    if (!/^[0-9A-Z.-]{1,16}$/.test(normalized)) {
      setSearchError("종목명 또는 종목 코드를 확인해 주세요. 예: 삼성전자, 005930, AAPL");
      return;
    }

    setSearching(true);
    const controller = new AbortController();
    lookupAbortController.current = controller;
    try {
      const snapshot = await fetchStockSnapshot(normalized, controller.signal);
      if (requestId !== lookupRequestId.current) return;
      const stock: DashboardStock = {
        symbol: snapshot.stock.symbol,
        name: snapshot.stock.name,
        market: snapshot.stock.market,
        currency: snapshot.stock.currency ?? snapshot.quote.currency ?? "KRW",
      };
      setStocks((current) => [
        stock,
        ...current.filter((item) => item.symbol !== stock.symbol),
      ].slice(0, 12));
      queryClient.setQueryData(["quote", stock.symbol], snapshot.quote);
      setInterval("1d");
      setSymbol(stock.symbol);
      setSearchValue(stock.name);
      setActiveAgent("all");
      setSuggestionListOpen(false);
      setActiveSuggestionIndex(-1);
      rememberStock(stock);
      if (historyMode !== "none") syncResultUrl(stock.symbol, historyMode);
      setRevealVersion((current) => current + 1);
    } catch (reason) {
      if (requestId !== lookupRequestId.current) return;
      setSearchError(reason instanceof Error ? reason.message : "종목을 찾지 못했습니다.");
    } finally {
      if (requestId === lookupRequestId.current) {
        lookupAbortController.current = null;
        setSearching(false);
      }
    }
  };

  const search = async (event: FormEvent) => {
    event.preventDefault();
    await lookupStock(searchValue);
  };

  const selectKnownStock = (stock: DashboardStock) => {
    setSuggestionListOpen(false);
    setActiveSuggestionIndex(-1);
    setSearchValue(stock.name);
    void lookupStock(stock.symbol);
  };

  const resetSelection = (historyMode: HistoryMode = "push") => {
    lookupRequestId.current += 1;
    lookupAbortController.current?.abort();
    lookupAbortController.current = null;
    setSymbol(null);
    setSearchValue("");
    setSearchError(null);
    setSearching(false);
    setActiveAgent("all");
    setSuggestionListOpen(true);
    setActiveSuggestionIndex(-1);
    if (historyMode !== "none") clearResultUrl(historyMode);
    window.requestAnimationFrame(() => searchInputRef.current?.focus());
  };

  useEffect(() => {
    if (queryLookupStarted.current) return;
    const requestedSymbol = new URLSearchParams(window.location.search).get("symbol");
    if (!requestedSymbol) return;
    queryLookupStarted.current = true;
    setSearchValue(requestedSymbol);
    void lookupStock(requestedSymbol, "none");
  }, []);

  useEffect(() => () => lookupAbortController.current?.abort(), []);

  useEffect(() => {
    const focusSearch = (event: globalThis.KeyboardEvent) => {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setSuggestionListOpen(true);
        searchInputRef.current?.focus();
      }
    };
    window.addEventListener("keydown", focusSearch);
    return () => window.removeEventListener("keydown", focusSearch);
  }, []);

  useEffect(() => {
    const handlePopState = () => {
      const requestedSymbol = new URLSearchParams(window.location.search).get("symbol");
      if (!requestedSymbol) {
        resetSelection("none");
        return;
      }
      if (requestedSymbol === symbol) return;
      setSearchValue(requestedSymbol);
      void lookupStock(requestedSymbol, "none");
    };

    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, [symbol, stocks]);

  const knownStocksBySymbol = new Map(stocks.map((stock) => [stock.symbol, stock]));
  const searchableStocks = [...watchlistStocks, ...recentStocks, ...stocks]
    .map((stock) => knownStocksBySymbol.get(stock.symbol) ?? stock)
    .filter((stock, index, collection) => collection.findIndex((item) => item.symbol === stock.symbol) === index);
  const similarStockMatches = findSimilarStockMatches(searchableStocks, searchValue);
  const suggestionMatches = searchValue.trim()
    ? similarStockMatches.map(({ stock }) => stock)
    : filterStocksBySearch(searchableStocks, searchValue);
  const suggestionMatchKinds = new Map(
    similarStockMatches.map(({ kind, stock }) => [stock.symbol, kind]),
  );
  const showSuggestionList = suggestionListOpen && suggestionMatches.length > 0;

  const handleSearchKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key === "Escape") {
      if (suggestionListOpen) {
        event.preventDefault();
        setSuggestionListOpen(false);
        setActiveSuggestionIndex(-1);
      }
      return;
    }

    if (!suggestionMatches.length) return;

    if (event.key === "ArrowDown" || event.key === "ArrowUp") {
      event.preventDefault();
      setSuggestionListOpen(true);
      setActiveSuggestionIndex((current) => {
        if (event.key === "ArrowDown") return (current + 1) % suggestionMatches.length;
        return current <= 0 ? suggestionMatches.length - 1 : current - 1;
      });
      return;
    }

    if (event.key === "Enter" && suggestionListOpen && activeSuggestionIndex >= 0) {
      const activeStock = suggestionMatches[activeSuggestionIndex];
      if (activeStock) {
        event.preventDefault();
        selectKnownStock(activeStock);
      }
    }
  };

  return (
    <>
      <section className={`market-toolbar ${symbol ? "compact" : "market-search-launcher"}`}>
        <div className="market-toolbar-copy">
          <span>{symbol ? "종목 검색" : "종목 분석"}</span>
          <b>{symbol ? "국내 · 미국 종목" : "궁금한 종목을 검색해 보세요"}</b>
          {!symbol && (
            <>
              <p>삼성전자, 005930, AAPL처럼 종목명이나 티커를 입력하세요.</p>
              <div className="market-search-assurances" aria-label="검색 안내">
                <span>국내 · 미국 종목</span>
                <span>로그인 없이 확인</span>
                <span>참고 정보 전용</span>
              </div>
            </>
          )}
          {symbol && (
            <div className="market-toolbar-actions">
              <button className="market-reset" onClick={() => resetSelection()} type="button">
                새 종목 찾기
              </button>
              {selected && (
                <button
                  aria-pressed={watchlistStocks.some((stock) => stock.symbol === selected.symbol)}
                  className="watchlist-toggle"
                  onClick={() => toggleWatchlist(selected)}
                  type="button"
                >
                  {watchlistStocks.some((stock) => stock.symbol === selected.symbol)
                    ? "관심 종목 해제"
                    : "관심 종목에 추가"}
                </button>
              )}
            </div>
          )}
        </div>
        <div className="market-search-control">
          <form aria-busy={searching} className="market-search-form" onSubmit={search}>
          <label className="sr-only" htmlFor="market-stock-search">종목명 또는 종목 코드</label>
          <input
            aria-activedescendant={activeSuggestionIndex >= 0 ? `stock-search-suggestion-${suggestionMatches[activeSuggestionIndex]?.symbol}` : undefined}
            aria-label="종목명 또는 종목 코드 검색"
            aria-describedby={searchError ? "market-search-error" : "market-search-help"}
            aria-autocomplete="list"
            aria-controls={showSuggestionList ? "stock-search-suggestions" : undefined}
            aria-expanded={showSuggestionList}
            aria-keyshortcuts="Control+K Meta+K"
            id="market-stock-search"
            maxLength={80}
            onChange={(event) => {
              setSearchValue(event.target.value);
              setSearchError(null);
              setSuggestionListOpen(true);
              setActiveSuggestionIndex(-1);
            }}
            onFocus={() => setSuggestionListOpen(true)}
            onKeyDown={handleSearchKeyDown}
            placeholder="삼성전자, 005930, AAPL"
            ref={searchInputRef}
            role="combobox"
            value={searchValue}
          />
          <button disabled={searching || !searchValue.trim()} type="submit">
            {searching ? "분석 준비 중" : "종목 분석"}
          </button>
          </form>
          {showSuggestionList && (
          <div className="search-suggestions" aria-label="종목 자동완성">
            <div className="search-suggestion-heading">
              <span className="search-suggestion-label" id="stock-search-suggestion-label">
                {searchValue.trim() ? "유사 종목" : recentStocks.length > 0 ? "최근 검색" : "빠른 종목"}
              </span>
              {searchValue.trim() && <small>{suggestionMatches.length}개 일치</small>}
              {!searchValue.trim() && recentStocks.length > 0 && (
                <button
                  className="clear-recent-searches"
                  onClick={clearRecentStocks}
                  title="이 기기의 최근 종목 목록만 지웁니다"
                  type="button"
                >
                  최근 검색 지우기
                </button>
              )}
            </div>
            <div
              aria-labelledby="stock-search-suggestion-label"
              className="search-suggestion-options"
              id="stock-search-suggestions"
              role="listbox"
            >
              {suggestionMatches.map((stock, index) => (
                <button
                  aria-selected={activeSuggestionIndex === index}
                  className={activeSuggestionIndex === index ? "active" : ""}
                  disabled={searching}
                  id={`stock-search-suggestion-${stock.symbol}`}
                  key={stock.symbol}
                  onClick={() => selectKnownStock(stock)}
                  onMouseDown={(event) => event.preventDefault()}
                  role="option"
                  type="button"
                >
                  <span className="search-option-copy">
                    <b>{stock.name}</b>
                    <small>{stock.symbol} · {stock.market}</small>
                  </span>
                  <span className="search-option-match">
                    {searchValue.trim()
                      ? SEARCH_MATCH_LABEL[suggestionMatchKinds.get(stock.symbol) ?? "name"]
                      : watchlistStocks.some((item) => item.symbol === stock.symbol)
                        ? "관심 종목"
                        : recentStocks.some((item) => item.symbol === stock.symbol)
                          ? "최근 검색"
                          : "빠른 탐색"}
                  </span>
                </button>
              ))}
            </div>
            <div className="search-suggestion-footer" aria-hidden="true">
              <span>↑↓ 선택</span><span>Enter 분석</span><span>Ctrl K 검색</span>
            </div>
            <span className="sr-only" role="status" aria-live="polite">
              {searchValue.trim()
                ? `${suggestionMatches.length}개의 유사 종목이 있습니다. 화살표 키로 선택할 수 있습니다.`
                : `${suggestionMatches.length}개의 빠른 종목이 있습니다. 화살표 키로 선택할 수 있습니다.`}
            </span>
          </div>
          )}
        </div>
        {!symbol && <p className="sr-only" id="market-search-help">종목명 또는 종목 코드를 입력하고 Enter를 누르세요.</p>}
        {searchValue.trim() && suggestionMatches.length === 0 && (
          <p className="search-empty" role="status">
            일치하는 종목이 없습니다. 종목명·티커·등록된 별칭으로 다시 검색해 보세요.
          </p>
        )}
      </section>
      {searchError && <div className="market-search-error" id="market-search-error" role="alert">{searchError}</div>}

      {symbol && selected && (
        <div
          aria-label={`${selected.name} 분석 결과`}
          className="market-results"
          key={`${symbol}-${revealVersion}`}
          ref={resultsRef}
          role="region"
          tabIndex={-1}
        >
          {watchlistStocks.length > 0 && (
            <section aria-label="이 브라우저의 관심 종목" className="personal-watchlist result-reveal reveal-1">
              <header>
                <div>
                  <span>관심 종목</span>
                  <p>{watchlistStorageMode === "browser" ? "이 브라우저에만 저장됩니다." : "저장소를 사용할 수 없어 이 탭에서만 유지됩니다."}</p>
                </div>
                <small>{watchlistStocks.length}개 저장됨</small>
              </header>
              <div className="personal-watchlist-items">
                {watchlistStocks.map((stock) => (
                  <div className={stock.symbol === symbol ? "active" : ""} key={stock.symbol}>
                    <button
                      aria-current={stock.symbol === symbol ? "page" : undefined}
                      onClick={() => selectKnownStock(stock)}
                      type="button"
                    >
                      <b>{stock.name}</b>
                      <span>{stock.symbol} · {stock.market}</span>
                    </button>
                    <button
                      aria-label={`${stock.name} 관심 종목에서 제거`}
                      className="personal-watchlist-remove"
                      onClick={() => toggleWatchlist(stock)}
                      title="관심 종목에서 제거"
                      type="button"
                    >
                      <span aria-hidden="true">×</span>
                    </button>
                  </div>
                ))}
              </div>
            </section>
          )}
          <p aria-live="polite" className="sr-only" role="status">{watchlistNotice}</p>
          <section className="stock-tabs result-reveal reveal-1" aria-label="종목 선택">
            {stocks.map((stock) => (
              <button
                aria-pressed={stock.symbol === symbol}
                className={stock.symbol === symbol ? "active" : ""}
                key={stock.symbol}
                onClick={() => selectKnownStock(stock)}
                type="button"
              >
                <span>{stock.name}</span>
                <small>{stock.symbol} · {stock.market}</small>
              </button>
            ))}
          </section>

          <section className="simulation-stage result-reveal reveal-2">
            <header className="simulation-intro stage-piece stage-1">
              <span>STOCKPILOT KITCHEN · ANALYST COURSE</span>
              <h2>AI 셰프팀이 <em>분석 코스를 완성합니다</em></h2>
              <p>분야별 셰프가 같은 데이터를 검토해 한 접시씩 플레이팅하고, 서빙 후 최종 참고 결과를 보여줍니다.</p>
            </header>

            <div className="simulation-ticker stage-piece stage-2">
              <div>
                <strong>{selected.symbol}</strong>
                <span>{selected.name} · {selected.market}</span>
              </div>
              <b>{displayedQuote ? formatPrice(displayedQuote.price, currency) : "—"}</b>
              <em
                className={
                  Number(displayedQuote?.change_percent ?? 0) < 0 ? "negative-text" : ""
                }
              >
                {formatChange(displayedQuote?.change_percent)}
              </em>
              <small><i />AI 셰프 키친 연결됨</small>
            </div>

            <div className="simulation-workspace stage-piece stage-3">
              <aside className="agent-roster" aria-label="AI 셰프 키친 코스 선택">
                <header>
                  <span>KITCHEN STAFF</span>
                  <div className="agent-roster-title">
                    <b>AI 셰프 키친</b>
                    <button
                      aria-pressed={activeAgent === "all"}
                      className="agent-roster-all"
                      onClick={() => setActiveAgent("all")}
                      type="button"
                    >
                      전체 보기
                    </button>
                  </div>
                  <small id="agent-roster-help">셰프를 선택하면 해당 코스 근거를 강조합니다.</small>
                </header>
                <div className="agent-roster-list">
                  {agentRoster.map((agent) => (
                    <button
                      aria-describedby="agent-roster-help"
                      aria-pressed={activeAgent === agent.key}
                      className={activeAgent === agent.key ? "active" : ""}
                      key={agent.key}
                      onClick={() => setActiveAgent(agent.key)}
                      type="button"
                    >
                      <AnalystAvatar agent={agent.key} size="roster" />
                      <div><b>{agent.label}</b><span>{agent.role}</span></div>
                      <em />
                    </button>
                  ))}
                </div>
                <footer>
                  <i />
                  {selectedRosterAgent
                    ? `${selectedRosterAgent.label}의 근거를 강조하고 있습니다.`
                    : "모든 셰프 코스의 근거를 함께 표시합니다."}
                </footer>
              </aside>

              <section className="simulation-market" aria-label={`${selected.name} 차트`}>
                <header>
                  <div>
                    <span>MARKET CHART</span>
                    <b>{displayedQuote?.name ?? selected.name}</b>
                    <div className="realtime-connection">
                      <small
                        aria-atomic="true"
                        aria-live="polite"
                        className={`live-status ${realtime.status}`}
                        role="status"
                      >
                        {realtimeStatusLabel}
                      </small>
                      {realtime.status === "unavailable" && (
                        <button
                          className="realtime-reconnect"
                          onClick={() => {
                            realtime.reconnect();
                            void quoteQuery.refetch();
                          }}
                          type="button"
                        >
                          실시간 연결 다시 시도
                        </button>
                      )}
                    </div>
                  </div>
                  <div className="intervals">
                    {intervals.map((item) => (
                      <button
                        aria-pressed={item.value === interval}
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
                {quoteQuery.isError && (
                  <div className="quote-warning" role="status">
                    <span>REST 현재가를 불러오지 못했습니다.</span>
                    <button onClick={() => quoteQuery.refetch()} type="button">현재가 다시 시도</button>
                  </div>
                )}
                {candleQuery.isPending && (
                  <div className="chart-state" role="status">차트 데이터를 불러오는 중입니다.</div>
                )}
                {candleQuery.isError && (
                  <div className="chart-state error" role="alert">
                    <b>API 연결 실패</b>
                    <span>{candleQuery.error.message}</span>
                    <button onClick={() => candleQuery.refetch()} type="button">다시 시도</button>
                  </div>
                )}
                {candleQuery.data && candleQuery.data.candles.length === 0 && (
                  <div className="chart-state" role="status">
                    <span>표시할 캔들 데이터가 없습니다.</span>
                    <button onClick={() => candleQuery.refetch()} type="button">다시 시도</button>
                  </div>
                )}
                {candleQuery.data && candleQuery.data.candles.length > 0 && <StockChart candles={candleQuery.data.candles} />}
                {candleQuery.data && (
                  <footer>
                    <span>{candleQuery.data.provider} · {candleQuery.data.aggregation_version}</span>
                    <span>원본 {candleQuery.data.raw_count}개</span>
                  </footer>
                )}
              </section>

              <AnalysisResult
                autoRun
                symbol={symbol}
                name={selected.name}
                market={selected.market}
                currency={currency}
                currentPrice={displayedQuote?.price}
                changePercent={displayedQuote?.change_percent}
                activeAgent={activeAgent}
              />
            </div>
          </section>
          <div className="result-reveal reveal-3">
            <TechnicalSnapshot symbol={symbol} currency={currency} />
          </div>
          <div className="result-reveal reveal-4">
            <ResearchDetails symbol={symbol} currency={currency} market={selected.market} />
          </div>
        </div>
      )}
    </>
  );
}
