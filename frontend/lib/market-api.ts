/**
 * StockPilot Next.js BFF와 통신할 때 사용하는 브라우저 타입 계약이다.
 *
 * 화면 컴포넌트는 FastAPI나 외부 공급자를 직접 호출하지 않고 이 파일의 함수를 사용한다.
 * API 키를 서버에만 보관하고 모든 화면에 같은 오류·응답 처리 규칙을 적용하기 위해서다.
 */
export type CandleInterval = "1d" | "1w" | "1M";

/** MarketCandle 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. */
export interface MarketCandle {
  timestamp: string;
  open: string;
  high: string;
  low: string;
  close: string;
  volume: number;
}

/** ProcessedCandles 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. */
export interface ProcessedCandles {
  symbol: string;
  provider: string;
  interval: CandleInterval;
  raw_count: number;
  aggregation_version: string;
  candles: MarketCandle[];
  quality_logs: Array<{ rule: string; severity: string; message: string }>;
}

/** StockInfo 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. */
export interface StockInfo {
  symbol: string;
  name: string;
  market: string;
  sector: string | null;
  listed_at: string | null;
  currency: string;
  provider: string;
}

/** MarketQuote 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. */
export interface MarketQuote {
  symbol: string;
  name: string | null;
  price: string;
  change: string | null;
  change_percent: string | null;
  volume: number | null;
  as_of: string | null;
  currency: string | null;
  provider: string;
}

/** StockSnapshot 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. */
export interface StockSnapshot {
  stock: StockInfo;
  quote: MarketQuote;
}

/** StockSearchResult 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. */
export interface StockSearchResult {
  provider: string;
  catalog_size: number;
  items: Array<{
    symbol: string;
    name: string;
    englishName?: string | null;
    market: string;
    securityType?: string | null;
    status?: string | null;
    currency: string;
  }>;
}

/** MarketOverview 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. */
export interface MarketOverview {
  provider: string;
  indicators: Array<{ symbol: string; lastPrice: string; timestamp?: string | null }>;
  exchange_rate: {
    baseCurrency: string;
    quoteCurrency: string;
    rate: string;
    midRate?: string;
    rateChangeType?: "UP" | "EQUAL" | "DOWN";
    validUntil?: string;
  } | null;
  calendars: Record<string, Record<string, unknown> | null>;
  rankings: Record<
    string,
    {
      rankedAt?: string | null;
      rankings: Array<{
        rank: number;
        symbol: string;
        currency: string;
        price: { lastPrice: string; basePrice: string; changeRate?: string | null };
        tradingVolume: string;
        tradingAmount: string;
      }>;
    }
  >;
  partial_errors: Record<string, { code: string; status_code: number }>;
}

export type TossRankingType =
  | "MARKET_TRADING_AMOUNT"
  | "MARKET_TRADING_VOLUME"
  | "TOP_GAINERS"
  | "TOP_LOSERS"
  | "TOSS_SECURITIES_TRADING_AMOUNT"
  | "TOSS_SECURITIES_TRADING_VOLUME";

/** MarketRankings 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. */
export interface MarketRankings {
  provider: string;
  type: TossRankingType;
  market_country: "KR" | "US";
  duration: string;
  rankedAt?: string | null;
  rankings: MarketOverview["rankings"][string]["rankings"];
}

/** MarketIndicatorHistory 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. */
export interface MarketIndicatorHistory {
  provider: string;
  symbol: string;
  candles: {
    candles: Array<{
      timestamp: string;
      openPrice: string;
      highPrice: string;
      lowPrice: string;
      closePrice: string;
      volume: string;
    }>;
    nextBefore?: string | null;
  };
  investor_trading: Record<string, unknown> | null;
  partial_errors: Record<string, { code: string; status_code: number }>;
}

/** StockMicrostructure 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. */
export interface StockMicrostructure {
  provider: string;
  price_limit: {
    timestamp?: string;
    upperLimitPrice: string | null;
    lowerLimitPrice: string | null;
    currency: string;
  };
  orderbook: {
    asks: Array<{ price: string; quantity: string }>;
    bids: Array<{ price: string; quantity: string }>;
  };
  trades: Array<{
    symbol: string;
    price: string;
    quantity: string;
    side: string | null;
    executed_at: string;
  }>;
  pressure: MarketPressure;
  warnings: Array<{
    warning_type: string;
    exchange: string | null;
    start_date: string | null;
    end_date: string | null;
  }>;
}

/** 호가·체결 기반 단기 주문 압력이며 양수 점수는 매수 우위를 뜻합니다. */
export interface MarketPressure {
  signal: "buying" | "selling" | "balanced" | "unavailable";
  score: number;
  strength: number;
  source: "trades_and_orderbook" | "trades_only" | "orderbook_only" | "unavailable";
  book_imbalance: number | null;
  trade_imbalance: number | null;
  bid_quantity: string;
  ask_quantity: string;
  buy_trade_quantity: string;
  sell_trade_quantity: string;
  known_trade_ratio: number;
  explicit_side_ratio: number;
  is_estimate: boolean;
}

/** TossStockTrends 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. */
export interface TossStockTrends {
  provider: string;
  investor_trading: Record<string, unknown>;
  program_trades: Record<string, unknown>;
  short_selling: Record<string, unknown>;
  credit_trades: Record<string, unknown>;
  securities_lending: Record<string, unknown>;
}

/** RealtimeQuote 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. */
export interface RealtimeQuote {
  type: "quote";
  symbol: string;
  name: string | null;
  price: string;
  change: string | null;
  change_percent: string | null;
  volume: number | null;
  currency: string | null;
  data_as_of: string;
  provider: string;
  is_investment_advice: false;
}

/** RealtimeError 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. */
export interface RealtimeError {
  type: "error";
  symbol?: string;
  error: { code: string; message: string };
}

export type ReferenceSignal =
  | "positive_watch"
  | "neutral_watch"
  | "defensive_watch"
  | "risk_aware"
  | "data_insufficient";

/** DetectedPattern 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. */
export interface DetectedPattern {
  category: "candlestick" | "chart";
  name: string;
  direction: "upward" | "downward" | "neutral";
  confidence: number;
  started_at: string;
  ended_at: string;
  evidence: string[];
}

/** IndicatorPoint 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. */
export interface IndicatorPoint {
  timestamp: string;
  ma_5: number | null;
  ma_20: number | null;
  rsi_14: number | null;
  macd: number | null;
  macd_signal: number | null;
  macd_histogram: number | null;
  bb_middle: number | null;
  bb_upper: number | null;
  bb_lower: number | null;
  atr_14: number | null;
  plus_di_14: number | null;
  minus_di_14: number | null;
  adx_14: number | null;
  mfi_14: number | null;
  vwap: number | null;
  obv: number | null;
  supertrend_10_3: number | null;
  supertrend_direction: number | null;
}

/** TechnicalAnalysis 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. */
export interface TechnicalAnalysis {
  symbol: string;
  provider: string;
  engine_version: string;
  validation_status: "experimental";
  indicators: IndicatorPoint[];
}

/** PatternAnalysis 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. */
export interface PatternAnalysis {
  symbol: string;
  provider: string;
  engine_version: string;
  validation_status: "experimental";
  data_as_of: string | null;
  window_size: number;
  patterns: DetectedPattern[];
  reference_signals: PatternReferenceSignal[];
}

/** 시간순 외부 검증을 통과했지만 강도가 약한 패턴 참고 신호입니다. */
export interface PatternReferenceSignal {
  pattern_name: string;
  outlook: "relative_underperformance_watch";
  horizon_days: number;
  benchmark: string;
  validation_accuracy: number;
  validation_samples: number;
  validation_status: "weak_walk_forward_validated";
}

/** FinancialSnapshot 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. */
export interface FinancialSnapshot {
  symbol: string;
  corp_code: string;
  fiscal_year: number;
  report_code: string;
  statement_type: string;
  currency: string;
  revenue: string | number | null;
  operating_income: string | number | null;
  net_income: string | number | null;
  total_assets: string | number | null;
  total_liabilities: string | number | null;
  total_equity: string | number | null;
  data_as_of: string;
  provider: string;
  persistence_status: "saved" | "disabled";
}

/** ValuationAnalysis 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. */
export interface ValuationAnalysis {
  symbol: string;
  currency: string | null;
  price: string | number;
  shares_outstanding: string | number | null;
  market_cap: string | number | null;
  per: string | number | null;
  pbr: string | number | null;
  psr: string | number | null;
  roe: string | number | null;
  financial_data_as_of: string;
  quote_data_as_of: string | null;
  financial_source: string;
  quote_provider: string;
  unavailable_metrics: string[];
  methodology: string;
  experimental: true;
}

/** NewsArticle 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. */
export interface NewsArticle {
  symbol: string;
  title: string;
  url: string;
  publisher: string;
  published_at: string;
  summary: string | null;
  sentiment_score: number;
}

/** NewsAnalysis 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. */
export interface NewsAnalysis {
  symbol: string;
  provider: string;
  experimental: true;
  sentiment_score: number;
  sentiment_label: "positive" | "negative" | "neutral";
  articles: NewsArticle[];
  persistence_status: "saved" | "disabled";
}

/** DisclosureItem 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. */
export interface DisclosureItem {
  symbol: string;
  corp_code: string;
  receipt_no: string;
  company_name: string;
  report_name: string;
  filed_at: string;
  filer_name: string;
  remarks: string | null;
  document_url: string;
  risk_level: "high" | "normal";
}

/** DisclosureAnalysis 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. */
export interface DisclosureAnalysis {
  symbol: string;
  provider: string;
  experimental: true;
  risk_flags: string[];
  disclosures: DisclosureItem[];
  persistence_status: "saved" | "disabled";
}

/** InvestorFlow 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. */
export interface InvestorFlow {
  symbol: string;
  as_of_date: string;
  foreign_net_quantity: string | number;
  institution_net_quantity: string | number;
  individual_net_quantity: string | number;
  foreign_holding_quantity: string | number | null;
  foreign_holding_rate: string | number | null;
  data_as_of: string;
  provider: string;
  experimental: true;
  foreign_institution_net_quantity: string | number;
  reference_signal: "net_inflow" | "net_outflow" | "balanced";
  persistence_status: "saved" | "disabled";
}

/** AIAnalysisReport 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. */
export interface AIAnalysisReport {
  symbol: string;
  generator: string;
  llm_model: string;
  model_version: string;
  validation_status: "experimental";
  overall_score: number | null;
  rise_probability: string | number | null;
  downside_risk: "low" | "medium" | "high";
  reference_signal: ReferenceSignal;
  signal_strength: number;
  signal_basis: string[];
  confidence: "low" | "medium" | "high";
  score_coverage: number | null;
  prediction_horizon_days: number | null;
  summary: string;
  key_points: string[];
  risk_factors: string[];
  counterpoints: string[];
  chart_patterns: {
    engine_version: string;
    validation_status: "experimental";
    data_as_of: string | null;
    window_size: number;
    patterns: DetectedPattern[];
    reference_signals: PatternReferenceSignal[];
  } | null;
  market_pressure: (MarketPressure & { provider: string }) | null;
  support_resistance: {
    method: string;
    support: string | number;
    resistance: string | number;
    status: "experimental";
  } | null;
  risk_warnings: Array<Record<string, unknown>>;
  agent_status: Record<string, "available" | "unavailable">;
  agent_findings: Record<
    string,
    {
      name: string;
      status: "available" | "unavailable";
      evidence: string[];
      data_as_of: string | null;
      value: unknown;
    }
  >;
  local_ai_findings?: Record<
    string,
    {
      agent: string;
      target: string;
      status:
        | "available"
        | "model_missing"
        | "data_unavailable"
        | "artifact_invalid"
        | "quality_rejected";
      signal: "positive" | "neutral" | "negative" | null;
      probability: number | null;
      confidence: number | null;
      model_version: string | null;
      evidence: string[];
    }
  >;
  local_ai_synthesis?: {
    status:
      | "available"
      | "model_missing"
      | "insufficient_specialists"
      | "data_unavailable"
      | "artifact_invalid"
      | "quality_rejected";
    target: string;
    signal: "positive" | "neutral" | "negative" | null;
    probability: number | null;
    confidence: number | null;
    model_version: string | null;
    available_agents: number;
    disagreement: number | null;
    evidence: string[];
    diagnostic_score?: number | null;
  } | null;
  data_as_of: string;
  disclaimer: string;
  is_investment_advice: false;
  compliance_status: "passed";
}

/** ApiEnvelope 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. */
interface ApiEnvelope<T> {
  success: boolean;
  request_id: string;
  data: T;
  error?: { message?: string };
}

const MARKET_API_URL = process.env.NEXT_PUBLIC_MARKET_API_URL ?? "/api/market";
const MARKET_REQUEST_TIMEOUT_MS = 120_000;

/** `publicRequestError`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
function publicRequestError<T>(
  envelope: ApiEnvelope<T> | null,
  fallbackMessage: string,
  status: number,
): Error {
  if (status === 429) return new Error("요청이 많습니다. 잠시 후 다시 시도해 주세요.");
  if (status >= 500) return new Error(`${fallbackMessage} 잠시 후 다시 시도해 주세요.`);

  const suppliedMessage = envelope?.error?.message?.trim();
  if (suppliedMessage && suppliedMessage.length <= 240) return new Error(suppliedMessage);

  return new Error(status > 0 ? `${fallbackMessage} (${status})` : fallbackMessage);
}

/** `request`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
async function request<T>(
  path: string,
  fallbackMessage: string,
  signal?: AbortSignal,
): Promise<T> {
  let response: Response;
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), MARKET_REQUEST_TIMEOUT_MS);
  const abortFromCaller = () => controller.abort();
  signal?.addEventListener("abort", abortFromCaller, { once: true });

  try {
    response = await fetch(`${MARKET_API_URL}${path}`, {
      cache: "no-store",
      signal: controller.signal,
    });
  } catch {
    if (controller.signal.aborted) {
      throw new Error("응답이 지연되고 있습니다. 네트워크를 확인한 뒤 다시 시도해 주세요.");
    }
    throw new Error(`${fallbackMessage} 네트워크 연결을 확인한 뒤 다시 시도해 주세요.`);
  } finally {
    window.clearTimeout(timeout);
    signal?.removeEventListener("abort", abortFromCaller);
  }

  let envelope: ApiEnvelope<T> | null = null;
  try {
    envelope = (await response.json()) as ApiEnvelope<T>;
  } catch {
    // The status code still provides a useful bounded public error below.
  }
  if (!response.ok || envelope === null || !envelope.success) {
    throw publicRequestError(envelope, fallbackMessage, response.status);
  }
  return envelope.data;
}

/** `quoteWebSocketUrl`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export function quoteWebSocketUrl(symbol: string): string {
  const realtimeUrl =
    process.env.NEXT_PUBLIC_REALTIME_URL ??
    process.env.NEXT_PUBLIC_API_URL ??
    window.location.origin;
  const url = new URL(realtimeUrl, window.location.origin);
  url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
  url.pathname = `/ws/v1/quotes/${encodeURIComponent(symbol)}`;
  url.search = "";
  url.hash = "";
  return url.toString();
}

/** `fetchCandles`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export async function fetchCandles(
  symbol: string,
  interval: CandleInterval,
  signal?: AbortSignal,
): Promise<ProcessedCandles> {
  const params = new URLSearchParams({ interval, limit: "180" });
  return request<ProcessedCandles>(
    `/api/v1/stocks/${encodeURIComponent(symbol)}/candles/processed?${params}`,
    "차트 데이터를 불러오지 못했습니다.",
    signal,
  );
}

/** `fetchStockInfo`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export function fetchStockInfo(symbol: string, signal?: AbortSignal): Promise<StockInfo> {
  return request<StockInfo>(
    `/api/v1/stocks/${encodeURIComponent(symbol)}`,
    "종목 정보를 불러오지 못했습니다.",
    signal,
  );
}

/** `fetchQuote`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export function fetchQuote(symbol: string, signal?: AbortSignal): Promise<MarketQuote> {
  return request<MarketQuote>(
    `/api/v1/stocks/${encodeURIComponent(symbol)}/quote`,
    "현재가를 불러오지 못했습니다.",
    signal,
  );
}

/** `fetchStockSnapshot`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export async function fetchStockSnapshot(symbol: string, signal?: AbortSignal): Promise<StockSnapshot> {
  const [stock, quote] = await Promise.all([
    fetchStockInfo(symbol, signal),
    fetchQuote(symbol, signal),
  ]);
  return { stock, quote };
}

/** `searchStocks`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export function searchStocks(
  query: string,
  limit = 12,
  signal?: AbortSignal,
): Promise<StockSearchResult> {
  const params = new URLSearchParams({ q: query, limit: String(limit) });
  return request<StockSearchResult>(
    `/api/v1/stocks/search?${params}`,
    "전체 종목을 검색하지 못했습니다.",
    signal,
  );
}

/** `fetchMarketOverview`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export function fetchMarketOverview(signal?: AbortSignal): Promise<MarketOverview> {
  return request<MarketOverview>(
    "/api/v1/market/overview",
    "시장 현황을 불러오지 못했습니다.",
    signal,
  );
}

/** `fetchMarketRankings`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export function fetchMarketRankings(
  type: TossRankingType,
  marketCountry: "KR" | "US",
  duration = "1d",
  signal?: AbortSignal,
): Promise<MarketRankings> {
  const params = new URLSearchParams({
    type,
    market_country: marketCountry,
    duration,
    count: "20",
  });
  return request<MarketRankings>(
    `/api/v1/market/rankings?${params}`,
    "시장 랭킹을 불러오지 못했습니다.",
    signal,
  );
}

/** `fetchMarketIndicatorHistory`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export function fetchMarketIndicatorHistory(
  symbol: string,
  signal?: AbortSignal,
): Promise<MarketIndicatorHistory> {
  const params = new URLSearchParams({ interval: "1d", count: "30" });
  return request<MarketIndicatorHistory>(
    `/api/v1/market/indicators/${encodeURIComponent(symbol)}?${params}`,
    "시장 지표 흐름을 불러오지 못했습니다.",
    signal,
  );
}

/** `fetchStockMicrostructure`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export function fetchStockMicrostructure(
  symbol: string,
  signal?: AbortSignal,
): Promise<StockMicrostructure> {
  const params = new URLSearchParams({ trade_limit: "20" });
  return request<StockMicrostructure>(
    `/api/v1/stocks/${encodeURIComponent(symbol)}/microstructure?${params}`,
    "호가와 체결 정보를 불러오지 못했습니다.",
    signal,
  );
}

/** `fetchTossStockTrends`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export function fetchTossStockTrends(
  symbol: string,
  signal?: AbortSignal,
): Promise<TossStockTrends> {
  const params = new URLSearchParams({ count: "20" });
  return request<TossStockTrends>(
    `/api/v1/stocks/${encodeURIComponent(symbol)}/toss-trends?${params}`,
    "수급 상세를 불러오지 못했습니다.",
    signal,
  );
}

/** `fetchTechnicalAnalysis`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export function fetchTechnicalAnalysis(symbol: string, signal?: AbortSignal): Promise<TechnicalAnalysis> {
  const params = new URLSearchParams({ limit: "180" });
  return request<TechnicalAnalysis>(
    `/api/v1/stocks/${encodeURIComponent(symbol)}/indicators?${params}`,
    "기술지표를 불러오지 못했습니다.",
    signal,
  );
}

/** `fetchPatternAnalysis`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export function fetchPatternAnalysis(symbol: string, signal?: AbortSignal): Promise<PatternAnalysis> {
  const params = new URLSearchParams({ limit: "180" });
  return request<PatternAnalysis>(
    `/api/v1/stocks/${encodeURIComponent(symbol)}/patterns?${params}`,
    "패턴 분석을 불러오지 못했습니다.",
    signal,
  );
}

/** `fetchFinancials`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export function fetchFinancials(
  symbol: string,
  fiscalYear: number,
  signal?: AbortSignal,
): Promise<FinancialSnapshot> {
  const params = new URLSearchParams({ fiscal_year: String(fiscalYear) });
  return request<FinancialSnapshot>(
    `/api/v1/stocks/${encodeURIComponent(symbol)}/financials?${params}`,
    "재무 정보를 불러오지 못했습니다.",
    signal,
  );
}

/** `fetchValuation`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export function fetchValuation(
  symbol: string,
  fiscalYear: number,
  signal?: AbortSignal,
): Promise<ValuationAnalysis> {
  const params = new URLSearchParams({ fiscal_year: String(fiscalYear) });
  return request<ValuationAnalysis>(
    `/api/v1/stocks/${encodeURIComponent(symbol)}/valuation?${params}`,
    "밸류에이션 정보를 불러오지 못했습니다.",
    signal,
  );
}

/** `fetchNews`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export function fetchNews(symbol: string, signal?: AbortSignal): Promise<NewsAnalysis> {
  const params = new URLSearchParams({ limit: "12" });
  return request<NewsAnalysis>(
    `/api/v1/stocks/${encodeURIComponent(symbol)}/news?${params}`,
    "뉴스 분석을 불러오지 못했습니다.",
    signal,
  );
}

/** `fetchDisclosures`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export function fetchDisclosures(symbol: string, signal?: AbortSignal): Promise<DisclosureAnalysis> {
  const params = new URLSearchParams({ days: "90", limit: "12" });
  return request<DisclosureAnalysis>(
    `/api/v1/stocks/${encodeURIComponent(symbol)}/disclosures?${params}`,
    "공시 정보를 불러오지 못했습니다.",
    signal,
  );
}

/** `fetchInvestorFlow`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export function fetchInvestorFlow(symbol: string, signal?: AbortSignal): Promise<InvestorFlow> {
  return request<InvestorFlow>(
    `/api/v1/stocks/${encodeURIComponent(symbol)}/investor-flow`,
    "투자자 수급을 불러오지 못했습니다.",
    signal,
  );
}

/** `fetchAnalysisReport`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export async function fetchAnalysisReport(symbol: string, signal?: AbortSignal): Promise<AIAnalysisReport> {
  const params = new URLSearchParams({ horizon_days: "5", limit: "180" });
  return request<AIAnalysisReport>(
    `/api/v1/stocks/${encodeURIComponent(symbol)}/ai-report?${params}`,
    "AI 분석을 완료하지 못했습니다.",
    signal,
  );
}
