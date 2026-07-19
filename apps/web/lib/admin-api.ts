export interface BacktestMetrics {
  total_return?: number;
  cagr?: number;
  max_drawdown?: number;
  sharpe_ratio?: number;
  win_rate?: number;
  trade_count?: number;
  final_equity?: number;
}

export interface BacktestRunSummary {
  run_id: string;
  symbol: string;
  strategy: string;
  status: string;
  engine: "vectorized" | "event_driven";
  engine_version: string;
  started_at: string;
  finished_at: string | null;
  metrics: BacktestMetrics;
}

export interface BacktestHistory {
  persistence_status: "enabled" | "disabled";
  items: BacktestRunSummary[];
  total: number;
  limit: number;
  offset: number;
}

export interface BacktestRunDetail {
  summary: BacktestRunSummary;
  config: Record<string, unknown>;
  equity_curve: Array<Record<string, unknown>>;
  trades: Array<Record<string, unknown>>;
  events: Array<Record<string, unknown>>;
}

export type BacktestStrategy = "ma_cross" | "buy_and_hold" | "pattern_reference";
export type BacktestEngineName = "vectorized" | "event_driven";

export interface BacktestComparisonRequest {
  symbol: string;
  strategy: BacktestStrategy;
  limit: number;
  fast_period?: number;
  slow_period?: number;
  initial_capital?: number;
  commission_rate?: number;
  tax_rate?: number;
  slippage_rate?: number;
  max_volume_participation?: number;
}

export interface BacktestEngineComparisonSummary {
  engine_version: string;
  metrics: BacktestMetrics;
  equity_curve: Array<{
    timestamp: string;
    normalized_equity: number;
    drawdown: number;
  }>;
  execution: {
    fill_count: number;
    partial_fill_count: number;
    rejected_order_count: number;
    volume_limit_applied: boolean;
  };
}

export interface BacktestEngineComparison {
  comparison_version: string;
  validation_status: "experimental";
  symbol: string;
  provider: string;
  strategy: string;
  data_as_of: string;
  assumptions: {
    candle_count: number;
    initial_capital: number;
    costs: {
      commission_rate: number;
      tax_rate: number;
      slippage_rate: number;
    };
    max_volume_participation: number;
    same_market_data_snapshot: true;
    force_close: boolean;
  };
  vectorized: BacktestEngineComparisonSummary;
  event_driven: BacktestEngineComparisonSummary;
  deltas: {
    total_return: number;
    cagr: number;
    max_drawdown: number;
    sharpe_ratio: number;
    final_equity: number;
    trade_count: number;
  };
  interpretation: string;
}

export interface BacktestStrategyComparisonRequest {
  symbol: string;
  engine: BacktestEngineName;
  limit: number;
  fast_period: number;
  slow_period: number;
  initial_capital?: number;
  commission_rate?: number;
  tax_rate?: number;
  slippage_rate?: number;
  max_volume_participation?: number;
}

export interface BacktestStrategyComparisonItem {
  strategy: BacktestStrategy;
  metrics: BacktestMetrics;
  equity_curve: Array<{
    timestamp: string;
    normalized_equity: number;
    drawdown: number;
  }>;
  execution: {
    fill_count: number;
    partial_fill_count: number;
    rejected_order_count: number;
  };
  deltas_vs_buy_and_hold: {
    total_return: number;
    cagr: number;
    max_drawdown: number;
    sharpe_ratio: number;
    final_equity: number;
    trade_count: number;
  };
}

export interface BacktestStrategyComparison {
  comparison_version: string;
  validation_status: "experimental";
  symbol: string;
  provider: string;
  engine: BacktestEngineName;
  engine_version: string;
  data_as_of: string;
  benchmark: "buy_and_hold";
  assumptions: {
    candle_count: number;
    initial_capital: number;
    costs: {
      commission_rate: number;
      tax_rate: number;
      slippage_rate: number;
    };
    max_volume_participation: number;
    same_market_data_snapshot: true;
    force_close: boolean;
    fast_period: number;
    slow_period: number;
  };
  strategies: BacktestStrategyComparisonItem[];
  interpretation: string;
}

export interface WalkForwardValidationRequest {
  symbol: string;
  strategy: BacktestStrategy;
  engine: BacktestEngineName;
  limit: number;
  n_splits: number;
  warmup_candles: number;
  fast_period?: number;
  slow_period?: number;
  max_volume_participation?: number;
}

export interface WalkForwardFold {
  fold: number;
  test_started_at: string;
  test_ended_at: string;
  test_candles: number;
  metrics: BacktestMetrics;
  execution: {
    partial_fill_count: number;
    rejected_order_count: number;
  };
}

export interface WalkForwardValidation {
  symbol: string;
  provider: string;
  engine: BacktestEngineName;
  validation_version: string;
  validation_status: "experimental";
  engine_version: string;
  strategy: string;
  n_splits: number;
  warmup_candles: number;
  data_as_of: string;
  aggregate: {
    mean_total_return: number;
    profitable_fold_ratio: number;
    worst_max_drawdown: number;
    mean_sharpe_ratio: number;
    total_trade_count: number;
    total_partial_fill_count: number;
    total_rejected_order_count: number;
    stability: "consistent_positive" | "mixed" | "consistent_negative";
  };
  execution_model: {
    volume_limit_applied: boolean;
    max_volume_participation: number;
    force_close_bypasses_volume_limit: boolean;
  };
  folds: WalkForwardFold[];
}

export interface ModelVersion {
  version: string;
  symbol: string;
  algorithm: string;
  horizon_days: number;
  validation_status: string;
  validation_metrics: Record<string, number>;
  registry_stage: "challenger" | "champion";
  data_as_of: string;
  promoted_at: string | null;
  created_at: string | null;
}

export interface ModelRegistryData {
  persistence_status: "enabled" | "disabled";
  items: ModelVersion[];
  total: number;
  limit: number;
  offset: number;
}

interface ApiEnvelope<T> {
  success: boolean;
  data: T;
  error?: { message?: string };
}

export interface WatchlistItem {
  symbol: string;
  name: string;
  market: string;
  currency: string;
  created_at: string;
}

export interface PriceAlert {
  alert_id: string;
  symbol: string;
  condition: "above" | "below";
  target_price: number | string;
  status: "active" | "triggered" | "disabled";
  created_at: string;
  last_price: number | string | null;
  last_evaluated_at: string | null;
  triggered_at: string | null;
}

export interface WatchlistData {
  persistence_status: "enabled" | "disabled";
  items: WatchlistItem[];
}

export interface PriceAlertData {
  persistence_status: "enabled" | "disabled";
  items: PriceAlert[];
}

interface EvaluateResult {
  evaluated: number;
  triggered: PriceAlert[];
  failures: Array<{ symbol: string; error_type: string }>;
  execution_enabled: false;
}

export interface BrokerAccount {
  account_seq: number;
  account_no_masked: string;
  account_type: string;
}

export interface PortfolioCurrencyAnalysis {
  holding_count: number;
  market_value: number | string;
  purchase_amount: number | string;
  profit_loss_after_cost: number | string;
  profit_rate_after_cost: number | string;
  profitable_count: number;
  loss_making_count: number;
  largest_symbol: string;
  largest_allocation: number | string;
  concentration_index: number | string;
  effective_holding_count: number | string;
  concentration_level: "balanced" | "moderate" | "high";
  loss_exposure: number | string;
  risk_flags: string[];
}

export interface PortfolioSyncResult {
  provider: string;
  account: BrokerAccount;
  holdings: Array<{
    symbol: string;
    name: string;
    currency: string;
    market_value: number | string;
    profit_loss_after_cost: number | string;
    allocation_within_currency: number | string | null;
  }>;
  analysis: {
    analysis_version: string;
    currency_separated: true;
    currencies: Record<string, PortfolioCurrencyAnalysis>;
    reference_signal: "loss_watch" | "concentration_watch" | "balanced_monitor";
    experimental: true;
    execution_enabled: false;
  };
  data_as_of: string;
  is_read_only: true;
  persistence_status: "saved" | "disabled";
}

export interface DependencyStatus {
  status: "up" | "down" | "disabled";
  required: boolean;
  latency_ms: number | null;
  error_type: string | null;
}

export interface OperationsStatus {
  status: "operational" | "degraded";
  ready: boolean;
  service: string;
  release: string;
  environment: string;
  checked_at: string;
  readiness: {
    status: "ready" | "not_ready";
    service: string;
    checks: Record<string, DependencyStatus>;
  };
  providers: Record<string, string>;
  features: Record<string, boolean>;
  realtime: {
    source: string;
    max_symbols: number;
    max_connections: number;
    poll_interval_seconds: number;
  };
  partitions: {
    status: "ready" | "disabled" | "unsupported";
    dialect?: string;
    items: Array<{ name: string; bounds: string }>;
    lookahead_months: number;
    archive_plan: {
      status: "preview_only" | "disabled" | "unsupported";
      archive_after_months: number;
      cutoff_month: string | null;
      candidates: Array<{
        name: string;
        starts_at: string;
        ends_at: string;
      }>;
      automatic_action: false;
    };
  };
  provider_audit: ProviderAuditMaintenanceStatus;
  data_lifecycle: DataLifecycleStatus;
}

export interface DataQualityLogItem {
  log_id: number;
  symbol: string;
  rule: string;
  severity: "error" | "warning";
  message: string;
  observed_at: string | null;
  created_at: string;
}

export interface DataQualityHistory {
  persistence_status: "enabled" | "disabled";
  items: DataQualityLogItem[];
  total: number;
  severity_counts: { error: number; warning: number };
  limit: number;
  offset: number;
}

export type ProviderAuditOutcome = "success" | "error" | "transport_error";

export interface ProviderAuditItem {
  audit_id: number;
  provider: string;
  method: string;
  endpoint: string;
  api_group: string;
  outcome: ProviderAuditOutcome;
  status_code: number | null;
  error_code: string | null;
  provider_request_id: string | null;
  internal_request_id: string;
  attempt_count: number;
  duration_ms: number;
  occurred_at: string;
}

export interface ProviderAuditHistory {
  persistence_status: "enabled" | "disabled";
  items: ProviderAuditItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface ProviderAuditMaintenanceStatus {
  status: "disabled" | "pending" | "healthy" | "failed";
  enabled: boolean;
  retention_days: number;
  cleanup_hour_kst: number;
  last_run_at: string | null;
  last_cutoff: string | null;
  last_deleted_count: number | null;
  last_error_type: string | null;
}

export interface DataLifecycleStatus {
  status: "disabled" | "pending" | "healthy" | "failed";
  enabled: boolean;
  retention_days: Record<string, number>;
  cleanup_hour_kst: number;
  last_run_at: string | null;
  last_deleted_counts: Record<string, number> | null;
  last_error_type: string | null;
}

export interface DataLifecyclePreview extends DataLifecycleStatus {
  preview_status?: "ready" | "failed";
  eligible_counts: Record<string, number> | null;
  cutoffs: Record<string, string> | null;
  preview_error_type?: string | null;
}

export interface IngestionStatus {
  scheduler_enabled: boolean;
  persistence_enabled: boolean;
  manual_ingestion_available: boolean;
  interval_minutes: number;
  ingestion_limit: number;
  symbols: string[];
}

export interface IngestionResult {
  summary: {
    symbol: string;
    provider: string;
    raw_count: number;
    cleaned_count: number;
    quality_log_count: number;
    aggregation_version: string;
  };
  configured_symbol: boolean;
  triggered_at: string;
}

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, { ...init, cache: "no-store" });
  let envelope: ApiEnvelope<T>;
  try {
    envelope = (await response.json()) as ApiEnvelope<T>;
  } catch {
    throw new Error(`관리자 API 응답을 해석할 수 없습니다. (${response.status})`);
  }
  if (!response.ok) {
    const retryAfter = response.headers.get("retry-after");
    const suffix = retryAfter ? ` ${retryAfter}초 후 다시 시도하세요.` : "";
    throw new Error(
      `${envelope.error?.message ?? `관리자 요청 실패 (${response.status})`}${suffix}`,
    );
  }
  return envelope.data;
}

export function fetchBacktestHistory(symbol = ""): Promise<BacktestHistory> {
  const params = new URLSearchParams({ limit: "25", offset: "0" });
  if (symbol) params.set("symbol", symbol);
  return request<BacktestHistory>(`/api/admin/backtests?${params}`);
}

export function fetchBacktestRun(runId: string): Promise<BacktestRunDetail> {
  return request<BacktestRunDetail>(`/api/admin/backtests/${encodeURIComponent(runId)}`);
}

export function runWalkForwardValidation(
  input: WalkForwardValidationRequest,
): Promise<WalkForwardValidation> {
  return request<WalkForwardValidation>("/api/admin/backtests/walk-forward", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
}

export function compareBacktestEngines(
  input: BacktestComparisonRequest,
): Promise<BacktestEngineComparison> {
  return request<BacktestEngineComparison>("/api/admin/backtests/compare", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
}

export function compareBacktestStrategies(
  input: BacktestStrategyComparisonRequest,
): Promise<BacktestStrategyComparison> {
  return request<BacktestStrategyComparison>("/api/admin/backtests/strategies/compare", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
}

export function fetchModelVersions(symbol = ""): Promise<ModelRegistryData> {
  const params = new URLSearchParams({ limit: "25", offset: "0" });
  if (symbol) params.set("symbol", symbol);
  return request<ModelRegistryData>(`/api/admin/models?${params}`);
}

export function promoteModelVersion(version: string): Promise<{
  model: ModelVersion;
  runtime_activation: false;
  notice: string;
}> {
  return request(`/api/admin/models/${encodeURIComponent(version)}/promote`, {
    method: "POST",
  });
}

export function fetchWatchlist(): Promise<WatchlistData> {
  return request<WatchlistData>("/api/admin/watchlist");
}

export function addWatchlist(symbol: string): Promise<{ item: WatchlistItem }> {
  return request("/api/admin/watchlist", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ symbol }),
  });
}

export function removeWatchlist(symbol: string): Promise<{ removed: boolean }> {
  return request(`/api/admin/watchlist/${encodeURIComponent(symbol)}`, { method: "DELETE" });
}

export function fetchPriceAlerts(): Promise<PriceAlertData> {
  return request<PriceAlertData>("/api/admin/alerts");
}

export function createPriceAlert(
  symbol: string,
  condition: "above" | "below",
  targetPrice: number,
): Promise<{ alert: PriceAlert; execution_enabled: false }> {
  return request("/api/admin/alerts", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ symbol, condition, target_price: targetPrice }),
  });
}

export function disablePriceAlert(alertId: string): Promise<{ disabled: boolean }> {
  return request(`/api/admin/alerts/${encodeURIComponent(alertId)}`, { method: "DELETE" });
}

export function evaluatePriceAlerts(): Promise<EvaluateResult> {
  return request<EvaluateResult>("/api/admin/alerts/evaluate", { method: "POST" });
}

export function fetchBrokerAccounts(): Promise<{ accounts: BrokerAccount[] }> {
  return request<{ accounts: BrokerAccount[] }>("/api/admin/broker-accounts");
}

export function syncPortfolio(accountSeq: number): Promise<PortfolioSyncResult> {
  return request<PortfolioSyncResult>(`/api/admin/portfolios/${accountSeq}/sync`, {
    method: "POST",
  });
}

export function fetchOperationsStatus(): Promise<OperationsStatus> {
  return request<OperationsStatus>("/api/admin/operations/status");
}

export function fetchDataQualityHistory(
  symbol: string,
  severity: "" | "error" | "warning",
  limit: number,
  offset: number,
): Promise<DataQualityHistory> {
  const params = new URLSearchParams({ limit: String(limit), offset: String(offset) });
  if (symbol) params.set("symbol", symbol);
  if (severity) params.set("severity", severity);
  return request<DataQualityHistory>(`/api/admin/data-quality?${params}`);
}

export function fetchProviderAuditHistory(
  provider: string,
  outcome: "" | ProviderAuditOutcome,
  limit: number,
  offset: number,
): Promise<ProviderAuditHistory> {
  const params = new URLSearchParams({ limit: String(limit), offset: String(offset) });
  if (provider) params.set("provider", provider);
  if (outcome) params.set("outcome", outcome);
  return request<ProviderAuditHistory>(`/api/admin/provider-audits?${params}`);
}

export function cleanupProviderAuditHistory(): Promise<ProviderAuditMaintenanceStatus> {
  return request<ProviderAuditMaintenanceStatus>("/api/admin/provider-audits/cleanup", {
    method: "POST",
  });
}

export function fetchDataLifecyclePreview(): Promise<DataLifecyclePreview> {
  return request<DataLifecyclePreview>("/api/admin/data-lifecycle/preview");
}

export function cleanupDataLifecycle(): Promise<DataLifecycleStatus> {
  return request<DataLifecycleStatus>("/api/admin/data-lifecycle/cleanup", {
    method: "POST",
  });
}

export function fetchIngestionStatus(): Promise<IngestionStatus> {
  return request<IngestionStatus>("/api/admin/ingestion");
}

export function triggerIngestion(symbol: string, limit?: number): Promise<IngestionResult> {
  const params = new URLSearchParams();
  if (limit != null) params.set("limit", String(limit));
  const query = params.size > 0 ? `?${params}` : "";
  return request<IngestionResult>(
    `/api/admin/ingestion/${encodeURIComponent(symbol)}${query}`,
    { method: "POST" },
  );
}
