export type CandleInterval = "1d" | "1w" | "1M";

export interface MarketCandle {
  timestamp: string;
  open: string;
  high: string;
  low: string;
  close: string;
  volume: number;
}

export interface ProcessedCandles {
  symbol: string;
  provider: string;
  interval: CandleInterval;
  raw_count: number;
  aggregation_version: string;
  candles: MarketCandle[];
  quality_logs: Array<{ rule: string; severity: string; message: string }>;
}

export interface StockInfo {
  symbol: string;
  name: string;
  market: string;
  sector: string | null;
  listed_at: string | null;
  currency: string;
  provider: string;
}

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

export interface StockSnapshot {
  stock: StockInfo;
  quote: MarketQuote;
}

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

export interface DetectedPattern {
  category: "candlestick" | "chart";
  name: string;
  direction: "upward" | "downward" | "neutral";
  confidence: number;
  started_at: string;
  ended_at: string;
  evidence: string[];
}

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

export interface TechnicalAnalysis {
  symbol: string;
  provider: string;
  engine_version: string;
  validation_status: "experimental";
  indicators: IndicatorPoint[];
}

export interface PatternAnalysis {
  symbol: string;
  provider: string;
  engine_version: string;
  validation_status: "experimental";
  data_as_of: string | null;
  window_size: number;
  patterns: DetectedPattern[];
}

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

export interface NewsArticle {
  symbol: string;
  title: string;
  url: string;
  publisher: string;
  published_at: string;
  summary: string | null;
  sentiment_score: number;
}

export interface NewsAnalysis {
  symbol: string;
  provider: string;
  experimental: true;
  sentiment_score: number;
  sentiment_label: "positive" | "negative" | "neutral";
  articles: NewsArticle[];
  persistence_status: "saved" | "disabled";
}

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

export interface DisclosureAnalysis {
  symbol: string;
  provider: string;
  experimental: true;
  risk_flags: string[];
  disclosures: DisclosureItem[];
  persistence_status: "saved" | "disabled";
}

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
  } | null;
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
  data_as_of: string;
  disclaimer: string;
  is_investment_advice: false;
  compliance_status: "passed";
}

interface ApiEnvelope<T> {
  success: boolean;
  request_id: string;
  data: T;
  error?: { message?: string };
}

const MARKET_API_URL = process.env.NEXT_PUBLIC_MARKET_API_URL ?? "/api/market";
const MARKET_REQUEST_TIMEOUT_MS = 20_000;

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

export function fetchStockInfo(symbol: string, signal?: AbortSignal): Promise<StockInfo> {
  return request<StockInfo>(
    `/api/v1/stocks/${encodeURIComponent(symbol)}`,
    "종목 정보를 불러오지 못했습니다.",
    signal,
  );
}

export function fetchQuote(symbol: string, signal?: AbortSignal): Promise<MarketQuote> {
  return request<MarketQuote>(
    `/api/v1/stocks/${encodeURIComponent(symbol)}/quote`,
    "현재가를 불러오지 못했습니다.",
    signal,
  );
}

export async function fetchStockSnapshot(symbol: string, signal?: AbortSignal): Promise<StockSnapshot> {
  const [stock, quote] = await Promise.all([
    fetchStockInfo(symbol, signal),
    fetchQuote(symbol, signal),
  ]);
  return { stock, quote };
}

export function fetchTechnicalAnalysis(symbol: string, signal?: AbortSignal): Promise<TechnicalAnalysis> {
  const params = new URLSearchParams({ limit: "180" });
  return request<TechnicalAnalysis>(
    `/api/v1/stocks/${encodeURIComponent(symbol)}/indicators?${params}`,
    "기술지표를 불러오지 못했습니다.",
    signal,
  );
}

export function fetchPatternAnalysis(symbol: string, signal?: AbortSignal): Promise<PatternAnalysis> {
  const params = new URLSearchParams({ limit: "180" });
  return request<PatternAnalysis>(
    `/api/v1/stocks/${encodeURIComponent(symbol)}/patterns?${params}`,
    "패턴 분석을 불러오지 못했습니다.",
    signal,
  );
}

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

export function fetchNews(symbol: string, signal?: AbortSignal): Promise<NewsAnalysis> {
  const params = new URLSearchParams({ limit: "12" });
  return request<NewsAnalysis>(
    `/api/v1/stocks/${encodeURIComponent(symbol)}/news?${params}`,
    "뉴스 분석을 불러오지 못했습니다.",
    signal,
  );
}

export function fetchDisclosures(symbol: string, signal?: AbortSignal): Promise<DisclosureAnalysis> {
  const params = new URLSearchParams({ days: "90", limit: "12" });
  return request<DisclosureAnalysis>(
    `/api/v1/stocks/${encodeURIComponent(symbol)}/disclosures?${params}`,
    "공시 정보를 불러오지 못했습니다.",
    signal,
  );
}

export function fetchInvestorFlow(symbol: string, signal?: AbortSignal): Promise<InvestorFlow> {
  return request<InvestorFlow>(
    `/api/v1/stocks/${encodeURIComponent(symbol)}/investor-flow`,
    "투자자 수급을 불러오지 못했습니다.",
    signal,
  );
}

export async function fetchAnalysisReport(symbol: string, signal?: AbortSignal): Promise<AIAnalysisReport> {
  const params = new URLSearchParams({ horizon_days: "5", limit: "180" });
  return request<AIAnalysisReport>(
    `/api/v1/stocks/${encodeURIComponent(symbol)}/ai-report?${params}`,
    "AI 분석을 완료하지 못했습니다.",
    signal,
  );
}
