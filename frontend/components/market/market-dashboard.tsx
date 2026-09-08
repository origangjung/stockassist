"use client";

/**
 * 사용자가 종목을 찾고 분석 결과를 확인하는 메인 작업 화면이다.
 *
 * 자동완성, URL·방문 기록, 브라우저 개인화, REST 조회와 실시간 시세 연결을 조율한다.
 * 지표와 AI 계산은 백엔드가 담당하며 이 컴포넌트는 사용자 상태와 결과 표시만 관리한다.
 */

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { FormEvent, KeyboardEvent, useEffect, useRef, useState } from "react";
import { Bookmark, Check, Search, Share2, X } from "lucide-react";
import {
  fetchCandles,
  fetchQuote,
  searchStocks,
  fetchStockSnapshot,
  quoteWebSocketUrl,
  type CandleInterval,
  type MarketQuote,
  type RealtimeError,
  type RealtimeQuote,
} from "../../lib/market-api";
import { AnalysisResult } from "../analysis/analysis-result";
import { type MeetingAgentKey } from "../analysis/agent-meeting-stage";
import { ResearchDetails } from "../analysis/research-details";
import { StockChart } from "./stock-chart";
import { TechnicalSnapshot } from "../analysis/technical-snapshot";
import { PaperTradingPanel } from "../paper/paper-trading-panel";
import { MarketMicrostructure } from "./market-microstructure";
import { MarketPulse } from "./market-pulse";
import { TossStockTrendsPanel } from "./toss-stock-trends";
import {
  readStoredItems,
  toggleStoredSymbol,
  writeStoredItems,
} from "../../lib/browser-watchlist";
import { stockResultUrl } from "../../lib/share-url";
import {
  filterStocksBySearch,
  findSimilarStockMatches,
  findStockByExactMatch,
} from "../../lib/stock-search";
import { stockCatalog } from "../../lib/stock-catalog";

/** DashboardStock 인터페이스는 종목 검색·차트·시장 데이터 화면을 담당합니다.에서 교환하는 필드 계약을 정의합니다. */
interface DashboardStock {
  /** 시세·분석 API가 종목을 식별할 때 사용하는 코드다. */
  symbol: string;
  /** 검색 결과와 화면 제목에 표시하는 종목명이다. */
  name: string;
  /** 국내·미국 데이터 지원 여부를 판단하는 시장 구분이다. */
  market: string;
  /** 가격 자릿수와 통화 기호를 결정한다. */
  currency: string;
  /** 종목명 외에 허용하는 한글·영문 연관 검색어다. */
  aliases?: string[];
}

const initialStocks: DashboardStock[] = stockCatalog.map((stock) => ({
  ...stock,
  aliases: [...stock.aliases],
}));

const intervals: Array<{ value: CandleInterval; label: string }> = [
  { value: "1d", label: "일" },
  { value: "1w", label: "주" },
  { value: "1M", label: "월" },
];

type RealtimeStatus = "connecting" | "live" | "reconnecting" | "offline" | "unavailable";
type AgentFocus = "all" | "technical" | "financial" | "news" | "investor_flow" | "risk";
type ServiceNoticeTone = "success" | "warning" | "neutral";

const REALTIME_STATUS_LABELS: Record<Exclude<RealtimeStatus, "unavailable">, string> = {
  connecting: "실시간 시세 연결 중",
  live: "실시간 시세 연결됨",
  reconnecting: "실시간 시세 재연결 중",
  offline: "오프라인 · 인터넷 연결 후 자동 재시도",
};
const TERMINAL_WEBSOCKET_CLOSE_CODES = new Set([1013, 4400, 4403, 4404]);

const agentRoster: Array<{ key: MeetingAgentKey; label: string; role: string }> = [
  { key: "technical", label: "기술 분석", role: "추세 · 모멘텀" },
  { key: "financial", label: "재무 분석", role: "실적 · 밸류에이션" },
  { key: "news", label: "뉴스·공시", role: "이슈 · 이벤트" },
  { key: "investor_flow", label: "수급 분석", role: "투자자 흐름" },
  { key: "risk", label: "위험 분석", role: "반대 근거" },
];

const RECENT_STOCKS_KEY = "stockpilot:recent-stocks";
const WATCHLIST_STOCKS_KEY = "stockpilot:watchlist-stocks";
const QUICK_SEARCH_SYMBOLS = ["005930", "AAPL", "NVDA", "TSLA", "SPY", "QQQ"];

type HistoryMode = "none" | "push" | "replace";

const SEARCH_MATCH_LABEL: Record<"name" | "symbol" | "alias", string> = {
  name: "종목명 일치",
  symbol: "티커 일치",
  alias: "별칭 일치",
};

/** `syncResultUrl`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
function syncResultUrl(symbol: string, mode: Exclude<HistoryMode, "none"> = "push") {
  const nextUrl = stockResultUrl(symbol);
  if (window.location.href === nextUrl) return;
  if (mode === "push") {
    window.history.pushState({ symbol }, "", nextUrl);
  } else {
    window.history.replaceState({ symbol }, "", nextUrl);
  }
}

/** `clearResultUrl`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
function clearResultUrl(mode: Exclude<HistoryMode, "none"> = "push") {
  const nextUrl = new URL(window.location.pathname, window.location.origin).toString();
  if (window.location.href === nextUrl) return;
  if (mode === "push") {
    window.history.pushState({}, "", nextUrl);
  } else {
    window.history.replaceState({}, "", nextUrl);
  }
}

/** `isDashboardStock`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
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

/** `useRealtimeQuote`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
function useRealtimeQuote(symbol: string | null) {
  const [quote, setQuote] = useState<RealtimeQuote | null>(null);
  const [status, setStatus] = useState<RealtimeStatus>("unavailable");
  const [reconnectVersion, setReconnectVersion] = useState(0);

  // 종목 변경이나 오프라인 전환 시 기존 소켓과 재시도 타이머를 함께 정리한다.
  // 이전 종목의 늦은 시세가 새 화면을 덮어쓰는 것을 막기 위한 생명주기 규칙이다.
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

/** `formatPrice`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
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

/** `formatChange`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
function formatChange(value: string | null | undefined) {
  if (value == null) return "—";
  const number = Number(value);
  if (!Number.isFinite(number)) return "—";
  return `${number >= 0 ? "+" : ""}${number.toFixed(2)}%`;
}

/** `MarketDashboard`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
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
  const [serviceNotice, setServiceNotice] = useState<{
    message: string;
    tone: ServiceNoticeTone;
  } | null>(null);
  const [watchlistStorageMode, setWatchlistStorageMode] = useState<"browser" | "session">("browser");
  const [suggestionListOpen, setSuggestionListOpen] = useState(false);
  const [activeSuggestionIndex, setActiveSuggestionIndex] = useState(-1);
  const [remoteStocks, setRemoteStocks] = useState<DashboardStock[]>([]);
  const [remoteSearchPending, setRemoteSearchPending] = useState(false);
  const [priceMotion, setPriceMotion] = useState<"up" | "down" | null>(null);
  const resultsRef = useRef<HTMLDivElement>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);
  const queryLookupStarted = useRef(false);
  const lookupRequestId = useRef(0);
  const lookupAbortController = useRef<AbortController | null>(null);
  const previousPriceRef = useRef<string | null>(null);
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
    // WebSocket이 살아 있으면 REST 폴링을 멈춰 공급자 호출량을 줄인다.
    // 연결 실패·재연결 중에는 5초 폴링을 유지해 현재가가 완전히 끊기지 않게 한다.
    refetchInterval: realtime.status === "live" || realtime.status === "offline" ? false : 5000,
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
    if (!serviceNotice) return;
    const timer = window.setTimeout(() => setServiceNotice(null), 4200);
    return () => window.clearTimeout(timer);
  }, [serviceNotice]);

  useEffect(() => {
    const currentPrice = displayedQuote?.price;
    if (!currentPrice) return;
    const previousPrice = previousPriceRef.current;
    previousPriceRef.current = currentPrice;
    if (!previousPrice || previousPrice === currentPrice) return;

    const direction = Number(currentPrice) >= Number(previousPrice) ? "up" : "down";
    setPriceMotion(direction);
    const timer = window.setTimeout(() => setPriceMotion(null), 760);
    return () => window.clearTimeout(timer);
  }, [displayedQuote?.price]);

  useEffect(() => {
    const handleOffline = () => setServiceNotice({
      message: "인터넷 연결이 끊겼습니다. 연결되면 시세를 다시 확인합니다.",
      tone: "warning",
    });
    const handleOnline = () => setServiceNotice({
      message: "인터넷 연결이 복구됐습니다. 최신 시세를 다시 확인합니다.",
      tone: "success",
    });
    window.addEventListener("offline", handleOffline);
    window.addEventListener("online", handleOnline);
    return () => {
      window.removeEventListener("offline", handleOffline);
      window.removeEventListener("online", handleOnline);
    };
  }, []);

  // 로컬 별칭은 즉시 표시하고, 두 글자 이상 입력되면 토스 전체 종목 원장을 뒤에서 검색한다.
  // 빠르게 입력할 때 이전 요청을 취소해 늦은 응답이 최신 자동완성을 덮지 않게 한다.
  useEffect(() => {
    const query = searchValue.trim();
    if (query.length < 2) {
      setRemoteStocks([]);
      setRemoteSearchPending(false);
      return;
    }
    const controller = new AbortController();
    const timer = window.setTimeout(() => {
      setRemoteSearchPending(true);
      void searchStocks(query, 12, controller.signal)
        .then((result) => {
          setRemoteStocks(result.items.map((stock) => ({
            symbol: stock.symbol,
            name: stock.name || stock.englishName || stock.symbol,
            market: stock.market,
            currency: stock.currency,
            aliases: stock.englishName ? [stock.englishName] : [],
          })));
        })
        .catch(() => {
          if (!controller.signal.aborted) setRemoteStocks([]);
        })
        .finally(() => {
          if (!controller.signal.aborted) setRemoteSearchPending(false);
        });
    }, 260);
    return () => {
      window.clearTimeout(timer);
      controller.abort();
    };
  }, [searchValue]);

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
    setServiceNotice({
      message: next.added
        ? `${stock.name}을(를) 이 브라우저의 관심 종목에 저장했습니다.`
        : `${stock.name}을(를) 관심 종목에서 제거했습니다.`,
      tone: next.added ? "success" : "neutral",
    });
    setWatchlistStorageMode(
      writeStoredItems(window.localStorage, WATCHLIST_STOCKS_KEY, next.items) ? "browser" : "session",
    );
  };

  const copyShareLink = async () => {
    if (!symbol) return;
    const shareUrl = stockResultUrl(symbol);
    try {
      if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(shareUrl);
      } else {
        const temporaryInput = document.createElement("textarea");
        temporaryInput.value = shareUrl;
        temporaryInput.setAttribute("readonly", "");
        temporaryInput.style.position = "fixed";
        temporaryInput.style.opacity = "0";
        document.body.append(temporaryInput);
        temporaryInput.select();
        const copied = document.execCommand("copy");
        temporaryInput.remove();
        if (!copied) throw new Error("copy failed");
      }
      setServiceNotice({ message: "이 종목 분석의 공유 링크를 복사했습니다.", tone: "success" });
    } catch {
      setServiceNotice({
        message: "공유 링크를 복사하지 못했습니다. 브라우저 권한을 확인해 주세요.",
        tone: "warning",
      });
    }
  };

  // 조회마다 증가하는 요청 번호를 부여해 먼저 시작했지만 늦게 끝난 응답을 무시한다.
  // 사용자가 빠르게 입력하고 선택해도 이전 종목이 뒤늦게 표시되지 않게 한다.
  const lookupStock = async (input: string, historyMode: HistoryMode = "push") => {
    const requestId = ++lookupRequestId.current;
    lookupAbortController.current?.abort();
    lookupAbortController.current = null;
    const rawValue = input.trim();
    const localCandidates = [...remoteStocks, ...stocks];
    let matchedByName = findStockByExactMatch(localCandidates, rawValue)
      ?? findSimilarStockMatches(localCandidates, rawValue, 1)[0]?.stock;

    // 사용자가 자동완성을 기다리지 않고 한글 종목명을 바로 제출해도 전체 원장에서
    // 한 번 더 확인한다. 티커처럼 보이는 값은 불필요한 종목 원장 호출 없이 바로 조회한다.
    if (!matchedByName && !/^[0-9A-Z.-]{1,16}$/i.test(rawValue)) {
      setSearching(true);
      const searchController = new AbortController();
      lookupAbortController.current = searchController;
      try {
        const result = await searchStocks(rawValue, 8, searchController.signal);
        const exact = result.items.find((item) => (
          item.name.trim().toLocaleLowerCase("ko-KR") === rawValue.toLocaleLowerCase("ko-KR")
          || item.englishName?.trim().toLocaleLowerCase("en-US") === rawValue.toLocaleLowerCase("en-US")
        ));
        const candidate = exact ?? result.items[0];
        if (candidate) {
          matchedByName = {
            symbol: candidate.symbol,
            name: candidate.name || candidate.englishName || candidate.symbol,
            market: candidate.market,
            currency: candidate.currency,
            aliases: candidate.englishName ? [candidate.englishName] : [],
          };
        }
      } catch (reason) {
        if (searchController.signal.aborted) return;
        setSearchError(reason instanceof Error ? reason.message : "종목을 찾지 못했습니다.");
        setSearching(false);
        return;
      }
    }
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
        aliases: stocks.find((item) => item.symbol === snapshot.stock.symbol)?.aliases,
      };
      setStocks((current) => [
        stock,
        ...current.filter((item) => item.symbol !== stock.symbol),
      ]);
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

  // 최근 검색과 관심 종목을 정적 검색 목록보다 먼저 배치하되, 종목 필드 자체는
  // 가장 최근 공급자 응답을 기준으로 합친다.
  const knownStocksBySymbol = new Map(
    [...stocks, ...remoteStocks].map((stock) => [stock.symbol, stock]),
  );
  const searchableStocks = [...remoteStocks, ...watchlistStocks, ...recentStocks, ...stocks]
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
  const quickSearchStocks = QUICK_SEARCH_SYMBOLS
    .map((quickSymbol) => searchableStocks.find((stock) => stock.symbol === quickSymbol))
    .filter((stock): stock is DashboardStock => stock !== undefined);

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
          <span>{symbol ? "다른 종목 찾기" : "StockPilot AI"}</span>
          <b>{symbol ? "종목명이나 티커로 바로 이동하세요" : "어떤 종목이 궁금하세요?"}</b>
          {!symbol && (
            <>
              <p>이름만 입력해도 관련 종목과 ETF를 바로 찾아드려요.</p>
              <div className="market-search-assurances" aria-label="검색 안내">
                <span>한국·미국 주식</span>
                <span>ETF 분석</span>
                <span>5개 AI 교차 점검</span>
              </div>
            </>
          )}
          {symbol && (
            <div className="market-toolbar-actions">
              <button className="market-reset" onClick={() => resetSelection()} type="button">
                새 종목 찾기
              </button>
              {selected && (
                <>
                  <button
                    aria-pressed={watchlistStocks.some((stock) => stock.symbol === selected.symbol)}
                    /** Name 클래스는 종목 검색·차트·시장 데이터 화면을 담당합니다.의 상태와 동작을 캡슐화합니다. */
                    className="watchlist-toggle"
                    onClick={() => toggleWatchlist(selected)}
                    type="button"
                  >
                    <Bookmark aria-hidden="true" size={15} />
                    {watchlistStocks.some((stock) => stock.symbol === selected.symbol)
                      ? "저장됨"
                      : "관심 종목"}
                  </button>
                  <button
                    aria-label={`${selected.name} 분석 공유 링크 복사`}
                    /** Name 클래스는 종목 검색·차트·시장 데이터 화면을 담당합니다.의 상태와 동작을 캡슐화합니다. */
                    className="share-result"
                    onClick={() => void copyShareLink()}
                    title="분석 공유 링크 복사"
                    type="button"
                  >
                    <Share2 aria-hidden="true" size={15} />
                    <span>공유</span>
                  </button>
                </>
              )}
            </div>
          )}
        </div>
        <div className="market-search-control">
          <form aria-busy={searching} className="market-search-form" onSubmit={search}>
          <Search aria-hidden="true" className="market-search-icon" size={21} />
          <label className="sr-only" htmlFor="market-stock-search">종목명 또는 종목 코드</label>
          <input
              aria-activedescendant={activeSuggestionIndex >= 0 ? `stock-search-suggestion-${suggestionMatches[activeSuggestionIndex]?.symbol}` : undefined}
              aria-label="종목명 또는 종목 코드 검색"
              aria-describedby={searchError ? "market-search-error" : "market-search-help"}
              aria-autocomplete="list"
              aria-controls={showSuggestionList ? "stock-search-suggestions" : undefined}
              aria-expanded={showSuggestionList}
              aria-keyshortcuts="Control+K Meta+K"
              autoComplete="off"
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
              placeholder="종목명, 티커, ETF 검색"
              ref={searchInputRef}
              role="combobox"
              value={searchValue}
            />
          {searchValue && !searching && (
            <button
              aria-label="검색어 지우기"
              /** Name 클래스는 종목 검색·차트·시장 데이터 화면을 담당합니다.의 상태와 동작을 캡슐화합니다. */
              className="market-search-clear"
              onClick={() => {
                setSearchValue("");
                setSearchError(null);
                setSuggestionListOpen(true);
                setActiveSuggestionIndex(-1);
                searchInputRef.current?.focus();
              }}
              title="검색어 지우기"
              type="button"
            >
              <X aria-hidden="true" size={17} />
            </button>
          )}
          <button disabled={searching || !searchValue.trim()} type="submit">
            {searching ? "찾는 중" : "분석하기"}
          </button>
          </form>
          {showSuggestionList && (
          <div className="search-suggestions" aria-label="종목 자동완성">
            <div className="search-suggestion-heading">
              <span className="search-suggestion-label" id="stock-search-suggestion-label">
                {searchValue.trim() ? "연관 검색" : recentStocks.length > 0 ? "최근 검색" : "많이 찾는 종목"}
              </span>
              {searchValue.trim() && (
                <small>{remoteSearchPending ? "전체 종목 찾는 중" : `${suggestionMatches.length}개 일치`}</small>
              )}
              {!searchValue.trim() && recentStocks.length > 0 && (
                <button
                  /** Name 클래스는 종목 검색·차트·시장 데이터 화면을 담당합니다.의 상태와 동작을 캡슐화합니다. */
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
              /** Name 클래스는 종목 검색·차트·시장 데이터 화면을 담당합니다.의 상태와 동작을 캡슐화합니다. */
              className="search-suggestion-options"
              id="stock-search-suggestions"
              role="listbox"
            >
              {suggestionMatches.map((stock, index) => (
                <button
                  aria-selected={activeSuggestionIndex === index}
                  /** Name 클래스는 종목 검색·차트·시장 데이터 화면을 담당합니다.의 상태와 동작을 캡슐화합니다. */
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
            <span className="sr-only" role="status" aria-live="polite">
              {searchValue.trim()
                ? `${suggestionMatches.length}개의 유사 종목이 있습니다. 화살표 키로 선택할 수 있습니다.`
                : `${suggestionMatches.length}개의 빠른 종목이 있습니다. 화살표 키로 선택할 수 있습니다.`}
            </span>
          </div>
          )}
          {!symbol && !searchValue.trim() && !showSuggestionList && (
            <div className="quick-search-row" aria-label="많이 찾는 종목">
              {quickSearchStocks.map((stock) => (
                <button key={stock.symbol} onClick={() => selectKnownStock(stock)} type="button">
                  <b>{stock.name}</b><span>{stock.symbol}</span>
                </button>
              ))}
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
      {serviceNotice && (
        <div
          aria-atomic="true"
          /** Name 클래스는 종목 검색·차트·시장 데이터 화면을 담당합니다.의 상태와 동작을 캡슐화합니다. */
          className={`service-toast service-toast--${serviceNotice.tone}`}
          role="status"
        >
          <span aria-hidden="true" className="service-toast__icon">
            {serviceNotice.tone === "success" ? <Check size={14} /> : serviceNotice.tone === "warning" ? "!" : "i"}
          </span>
          <span>{serviceNotice.message}</span>
          <button aria-label="알림 닫기" onClick={() => setServiceNotice(null)} type="button">×</button>
        </div>
      )}

      <MarketPulse onSelectSymbol={(selectedSymbol) => void lookupStock(selectedSymbol)} />

      {symbol && selected && (
        <div
          aria-label={`${selected.name} 분석 결과`}
          /** Name 클래스는 종목 검색·차트·시장 데이터 화면을 담당합니다.의 상태와 동작을 캡슐화합니다. */
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
                      /** Name 클래스는 종목 검색·차트·시장 데이터 화면을 담당합니다.의 상태와 동작을 캡슐화합니다. */
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
          <section className="simulation-stage result-reveal reveal-2" id="agents">
            <header className="simulation-intro stage-piece stage-1">
              <span>STOCKPILOT · AI ANALYST OFFICE</span>
              <h2>AI 애널리스트들의 <em>회의가 시작됩니다</em></h2>
              <p>전문 AI가 각자 근거를 검토하고 강세·약세 토론을 거쳐 최종 참고 의견을 정리합니다.</p>
            </header>

            <div className="simulation-ticker stage-piece stage-2">
              <div>
                <strong>{selected.symbol}</strong>
                <span>{selected.name} · {selected.market}</span>
              </div>
              <b className={priceMotion ? `price-update price-update--${priceMotion}` : undefined}>
                {displayedQuote ? formatPrice(displayedQuote.price, currency) : "—"}
              </b>
              <em
                /** Name 클래스는 종목 검색·차트·시장 데이터 화면을 담당합니다.의 상태와 동작을 캡슐화합니다. */
                className={
                  Number(displayedQuote?.change_percent ?? 0) < 0 ? "negative-text" : ""
                }
              >
                {Number(displayedQuote?.change_percent ?? 0) < 0 ? "▼" : Number(displayedQuote?.change_percent ?? 0) > 0 ? "▲" : "•"}
                {" "}{currency} {formatChange(displayedQuote?.change_percent)}
              </em>
              <small><i />애널리스트팀 분석 중</small>
            </div>

            <nav className="result-section-nav" aria-label={`${selected.name} 분석 섹션`}>
              <a href="#market-chart">차트</a>
              <a href="#paper-trading">모의투자</a>
              <a href="#ai-analysis">AI 분석</a>
              <a href="#technical-detail">기술 지표</a>
              <a href="#company-research">기업 정보</a>
            </nav>

            <div className="simulation-workspace stage-piece stage-3">
              <aside className="agent-roster" aria-label="분석 관점 선택">
                <header>
                  <span>ANALYSIS LENSES</span>
                  <div className="agent-roster-title">
                    <b>분석 관점</b>
                    <button
                      aria-pressed={activeAgent === "all"}
                      /** Name 클래스는 종목 검색·차트·시장 데이터 화면을 담당합니다.의 상태와 동작을 캡슐화합니다. */
                      className="agent-roster-all"
                      onClick={() => setActiveAgent("all")}
                      type="button"
                    >
                      전체 보기
                    </button>
                  </div>
                  <small id="agent-roster-help">관점을 선택하면 해당 분석 근거를 강조합니다.</small>
                </header>
                <div className="agent-roster-list">
                  {agentRoster.map((agent, index) => (
                    <button
                      aria-describedby="agent-roster-help"
                      aria-pressed={activeAgent === agent.key}
                      /** Name 클래스는 종목 검색·차트·시장 데이터 화면을 담당합니다.의 상태와 동작을 캡슐화합니다. */
                      className={activeAgent === agent.key ? "active" : ""}
                      key={agent.key}
                      onClick={() => setActiveAgent(agent.key)}
                      type="button"
                    >
                      <span aria-hidden="true" className={`analysis-lens-mark lens-${agent.key}`}>
                        {String(index + 1).padStart(2, "0")}
                      </span>
                      <div><b>{agent.label}</b><span>{agent.role}</span></div>
                      <em />
                    </button>
                  ))}
                </div>
                <footer>
                  <i />
                  {selectedRosterAgent
                    ? `${selectedRosterAgent.label}의 근거를 강조하고 있습니다.`
                    : "모든 분석 관점의 근거를 함께 표시합니다."}
                </footer>
              </aside>

              <section className="simulation-market" id="market-chart" aria-label={`${selected.name} 차트`}>
                <header>
                  <div>
                    <span>MARKET CHART</span>
                    <b>{displayedQuote?.name ?? selected.name}</b>
                    <div className="realtime-connection">
                      <small
                        aria-atomic="true"
                        aria-live="polite"
                        /** Name 클래스는 종목 검색·차트·시장 데이터 화면을 담당합니다.의 상태와 동작을 캡슐화합니다. */
                        className={`live-status ${realtime.status}`}
                        role="status"
                      >
                        {realtimeStatusLabel}
                      </small>
                      {realtime.status === "unavailable" && (
                        <button
                          /** Name 클래스는 종목 검색·차트·시장 데이터 화면을 담당합니다.의 상태와 동작을 캡슐화합니다. */
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
                        /** Name 클래스는 종목 검색·차트·시장 데이터 화면을 담당합니다.의 상태와 동작을 캡슐화합니다. */
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
                {quoteQuery.isError && !realtime.quote && (
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
                <MarketMicrostructure currency={currency} symbol={symbol} />
                <TossStockTrendsPanel symbol={symbol} />
              </section>

              <PaperTradingPanel
                symbol={symbol}
                name={selected.name}
                currency={currency}
                currentPrice={displayedQuote?.price}
              />

              <div className="analysis-result-shell" id="ai-analysis">
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
            </div>
          </section>
          <div className="result-reveal reveal-3" id="technical-detail">
            <TechnicalSnapshot symbol={symbol} currency={currency} />
          </div>
          <div className="result-reveal reveal-4" id="company-research">
            <ResearchDetails symbol={symbol} currency={currency} market={selected.market} />
          </div>
        </div>
      )}
    </>
  );
}
