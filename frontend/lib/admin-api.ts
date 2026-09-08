/** admin-api 파일은 프론트 타입 계약과 API client 기능을 담당한다. */

export interface BacktestMetrics {
  total_return?: number;
  cagr?: number;
  max_drawdown?: number;
  sharpe_ratio?: number;
  win_rate?: number;
  trade_count?: number;
  final_equity?: number;
}

/** BacktestRunSummary 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. */
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

/** BacktestHistory 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. */
export interface BacktestHistory {
  persistence_status: "enabled" | "disabled";
  items: BacktestRunSummary[];
  total: number;
  limit: number;
  offset: number;
}

/** BacktestRunDetail 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. */
export interface BacktestRunDetail {
  summary: BacktestRunSummary;
  config: Record<string, unknown>;
  equity_curve: Array<Record<string, unknown>>;
  trades: Array<Record<string, unknown>>;
  events: Array<Record<string, unknown>>;
}

export type BacktestStrategy = "ma_cross" | "buy_and_hold" | "pattern_reference";
export type BacktestEngineName = "vectorized" | "event_driven";

/** BacktestComparisonRequest 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. */
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

/** BacktestEngineComparisonSummary 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. */
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

/** BacktestEngineComparison 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. */
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

/** BacktestStrategyComparisonRequest 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. */
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

/** BacktestStrategyComparisonItem 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. */
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

/** BacktestStrategyComparison 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. */
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

/** WalkForwardValidationRequest 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. */
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

/** WalkForwardFold 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. */
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

/** WalkForwardValidation 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. */
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

/** ModelVersion 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. */
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

/** ModelRegistryData 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. */
export interface ModelRegistryData {
  persistence_status: "enabled" | "disabled";
  runtime_activation_enabled: boolean;
  items: ModelVersion[];
  total: number;
  limit: number;
  offset: number;
}

/** 직접 학습 모델 하나의 검증 지표와 품질 게이트 결과다. */
export interface LocalAiReadinessItem {
  agent: string;
  label: string;
  scope: "core" | "etf";
  status: "available" | "quality_rejected" | "missing" | "artifact_invalid";
  model_version: string | null;
  trained_at: string | null;
  training_samples: number;
  validation_samples: number;
  required_validation_samples: number;
  remaining_validation_samples: number;
  metrics: Partial<Record<
    | "accuracy"
    | "baseline_accuracy"
    | "baseline_improvement"
    | "balanced_accuracy"
    | "roc_auc"
    | "brier_score"
    | "calibration_error"
    | "positive_rate"
    | "validation_samples",
    number
  >>;
  reasons: string[];
}

/** 직접 학습 AI 전체의 현재 운영 준비도 응답이다. */
export interface LocalAiReadinessData {
  enabled: boolean;
  generated_at: string;
  summary: {
    total: number;
    available: number;
    quality_rejected: number;
    missing: number;
    artifact_invalid: number;
    core_ready: boolean;
  };
  items: LocalAiReadinessItem[];
}

/** ApiEnvelope 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. */
interface ApiEnvelope<T> {
  success: boolean;
  data: T;
  error?: { message?: string };
}

/** WatchlistItem 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. */
export interface WatchlistItem {
  symbol: string;
  name: string;
  market: string;
  currency: string;
  created_at: string;
}

/** PriceAlert 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. */
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

/** WatchlistData 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. */
export interface WatchlistData {
  persistence_status: "enabled" | "disabled";
  items: WatchlistItem[];
}

/** PriceAlertData 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. */
export interface PriceAlertData {
  persistence_status: "enabled" | "disabled";
  items: PriceAlert[];
}

/** EvaluateResult 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. */
interface EvaluateResult {
  evaluated: number;
  triggered: PriceAlert[];
  failures: Array<{ symbol: string; error_type: string }>;
  execution_enabled: false;
}

/** BrokerAccount 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. */
export interface BrokerAccount {
  account_seq: number;
  account_no_masked: string;
  account_type: string;
}

/** PortfolioCurrencyAnalysis 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. */
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

/** PortfolioSyncResult 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. */
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

/** TossAccountWorkspace 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. */
export interface TossAccountWorkspace {
  provider: "toss";
  holdings: Record<string, unknown> | null;
  buying_power: Record<string, unknown> | null;
  commissions: Array<Record<string, unknown>>;
  orders: {
    open: Record<string, unknown>;
    closed: Record<string, unknown>;
  };
  conditional_orders: {
    open: Record<string, unknown>;
    closed: Record<string, unknown>;
  };
  trading_enabled: boolean;
  partial_errors: Record<string, { error_type?: string }>;
}

/** DependencyStatus 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. */
export interface DependencyStatus {
  status: "up" | "down" | "disabled";
  required: boolean;
  latency_ms: number | null;
  error_type: string | null;
}

/** OperationsStatus 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. */
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

/** DataQualityLogItem 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. */
export interface DataQualityLogItem {
  log_id: number;
  symbol: string;
  rule: string;
  severity: "error" | "warning";
  message: string;
  observed_at: string | null;
  created_at: string;
}

/** DataQualityHistory 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. */
export interface DataQualityHistory {
  persistence_status: "enabled" | "disabled";
  items: DataQualityLogItem[];
  total: number;
  severity_counts: { error: number; warning: number };
  limit: number;
  offset: number;
}

export type CandlePriceBasis =
  | "unknown"
  | "unadjusted"
  | "provider_adjusted"
  | "point_in_time_adjusted";

/** CandlePriceBasisInventoryItem 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. */
export interface CandlePriceBasisInventoryItem {
  source_provider: string;
  price_basis: CandlePriceBasis;
  price_basis_rule_version: string;
  data_stage: string;
  interval: string;
  aggregation_version: string;
  candle_count: number;
  first_timestamp: string;
  last_timestamp: string;
  review_status: "evidence_required" | "evidence_recorded";
  required_evidence: string[];
}

/** CandlePriceBasisInventory 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. */
export interface CandlePriceBasisInventory {
  persistence_status: "enabled" | "disabled";
  symbol: string;
  items: CandlePriceBasisInventoryItem[];
  total_candles: number;
  unknown_candles: number;
  legacy_unknown_candles: number;
  legacy_rule_candles: number;
  total_groups: number;
  review_ready_groups: number;
  blocked_review_groups: number;
  groups_truncated: boolean;
  /** ification_blockers 클래스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.의 상태와 동작을 캡슐화합니다. */
  classification_blockers?: string[];
  automatic_relabel: false;
  mutation_performed: false;
}

export type ProviderAuditOutcome = "success" | "error" | "transport_error";

/** ProviderAuditItem 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. */
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

/** ProviderAuditHistory 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. */
export interface ProviderAuditHistory {
  persistence_status: "enabled" | "disabled";
  items: ProviderAuditItem[];
  total: number;
  limit: number;
  offset: number;
}

/** ProviderAuditMaintenanceStatus 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. */
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

/** DataLifecycleStatus 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. */
export interface DataLifecycleStatus {
  status: "disabled" | "pending" | "healthy" | "failed";
  enabled: boolean;
  retention_days: Record<string, number>;
  cleanup_hour_kst: number;
  last_run_at: string | null;
  last_deleted_counts: Record<string, number> | null;
  last_error_type: string | null;
}

/** DataLifecyclePreview 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. */
export interface DataLifecyclePreview extends DataLifecycleStatus {
  preview_status?: "ready" | "failed";
  eligible_counts: Record<string, number> | null;
  cutoffs: Record<string, string> | null;
  preview_error_type?: string | null;
}

/** CorporateActionItem 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. */
export interface CorporateActionItem {
  symbol: string;
  action_type: "split" | "reverse_split" | "cash_dividend" | "stock_dividend" | "rights_issue";
  event_id: string;
  revision: number;
  effective_at: string;
  announced_at: string | null;
  known_at: string;
  price_factor: number | string;
  volume_factor: number | string;
  status: "announced" | "confirmed" | "cancelled";
  source: string;
  rule_version: string;
  recorded_at: string | null;
}

/** CorporateActionHistory 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. */
export interface CorporateActionHistory {
  persistence_status: "enabled" | "disabled";
  items: CorporateActionItem[];
  total: number;
  limit: number;
  offset: number;
  data_as_of: string;
  adjustment_version: string;
  application_mode: "preview_only";
  raw_candles_mutated: false;
}

/** CorporateActionSource 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. */
export interface CorporateActionSource {
  name: string;
  markets: string[];
  trust_status: "experimental" | "verified" | "disabled";
  revision_strategy: string;
}

/** CorporateActionIngestionStatus 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. */
export interface CorporateActionIngestionStatus {
  persistence_status: "enabled" | "disabled";
  ingestion_available: boolean;
  sources: CorporateActionSource[];
  source_candidates: CorporateActionSource[];
  verified_source_count: number;
  automatic_ingestion: false;
  consumer_adjustment_mode: "opt_in_disabled";
  max_batch_records: number;
}

/** CorporateActionIngestionResult 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. */
export interface CorporateActionIngestionResult {
  source: string;
  symbol: string;
  requested_start: string;
  requested_end: string;
  data_as_of: string;
  fetched: number;
  created: number;
  unchanged: number;
  atomic_batch: true;
  consumer_adjustment_mode: "opt_in_disabled";
}

/** CorporateActionCandidateStatus 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. */
export interface CorporateActionCandidateStatus {
  available: boolean;
  sources: CorporateActionSource[];
  read_only: true;
  automatic_confirmation: false;
  point_in_time_eligible: false;
  max_range_days: number;
  max_candidates: number;
}

/** CorporateActionCandidateItem 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. */
export interface CorporateActionCandidateItem {
  source: string;
  symbol: string;
  event_id: string;
  receipt_no: string;
  action_type: string;
  filed_on: string;
  decision_date: string | null;
  record_date: string | null;
  proposed_price_factor: number | string | null;
  proposed_volume_factor: number | string | null;
  evidence_url: string;
  report_name: string | null;
  remarks: string | null;
  correction_hint: boolean;
  superseded_hint: boolean;
  warnings: string[];
  confirmation_ready: false;
}

/** CorporateActionCandidatePreview 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. */
export interface CorporateActionCandidatePreview {
  source: string;
  symbol: string;
  requested_start: string;
  requested_end: string;
  data_as_of: string;
  items: CorporateActionCandidateItem[];
  revision_groups: Array<{
    group_hint: string;
    source: string;
    symbol: string;
    action_type: string;
    anchor_date: string | null;
    receipt_nos: string[];
    suggested_revisions: number[];
    confidence: "isolated" | "likely_correction" | "ambiguous_multiple_receipts";
    reasons: string[];
    requires_manual_confirmation: true;
    persistence_allowed: false;
  }>;
  count: number;
  read_only: true;
  write_performed: false;
  automatic_confirmation: false;
  point_in_time_eligible: false;
}

/** CorporateActionApprovalStatus 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. */
export interface CorporateActionApprovalStatus {
  enabled: boolean;
  available: boolean;
  persistence_status: "enabled" | "disabled";
  confirmation_phrase: "CONFIRM_CORPORATE_ACTION";
  candidate_refetch_required: true;
  supported_sources: string[];
  exchange_evidence_required: true;
  allowed_exchange_evidence_hosts: string[];
  known_at_policy: "approval_time";
  bulk_approval: false;
  automatic_execution: false;
  raw_candles_mutated: false;
  exchange_verification: Record<string, unknown>;
}

/** CorporateActionApprovalRequest 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. */
export interface CorporateActionApprovalRequest {
  start: string;
  end: string;
  group_hint: string;
  receipt_no: string;
  effective_at: string;
  exchange_evidence_url: string;
  confirmation: "CONFIRM_CORPORATE_ACTION";
}

/** CorporateActionApprovalResult 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. */
export interface CorporateActionApprovalResult {
  action: CorporateActionItem;
  evidence_hash: string;
  created: boolean;
  candidate_refetched_at: string;
  known_at_policy: "approval_time";
  automatic_execution: false;
  raw_candles_mutated: false;
}

/** IngestionStatus 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. */
export interface IngestionStatus {
  scheduler_enabled: boolean;
  persistence_enabled: boolean;
  manual_ingestion_available: boolean;
  interval_minutes: number;
  ingestion_limit: number;
  symbols: string[];
}

/** IngestionResult 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. */
export interface IngestionResult {
  summary: {
    symbol: string;
    provider: string;
    raw_count: number;
    cleaned_count: number;
    quality_log_count: number;
    aggregation_version: string;
    price_basis: CandlePriceBasis;
    price_basis_rule_version: string;
    price_basis_verification_status: "unverified" | "verified" | "synthetic";
  };
  configured_symbol: boolean;
  triggered_at: string;
}

/** `request`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
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

/** `fetchBacktestHistory`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export function fetchBacktestHistory(symbol = ""): Promise<BacktestHistory> {
  const params = new URLSearchParams({ limit: "25", offset: "0" });
  if (symbol) params.set("symbol", symbol);
  return request<BacktestHistory>(`/api/admin/backtests?${params}`);
}

/** `fetchBacktestRun`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export function fetchBacktestRun(runId: string): Promise<BacktestRunDetail> {
  return request<BacktestRunDetail>(`/api/admin/backtests/${encodeURIComponent(runId)}`);
}

/** `runWalkForwardValidation`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export function runWalkForwardValidation(
  input: WalkForwardValidationRequest,
): Promise<WalkForwardValidation> {
  return request<WalkForwardValidation>("/api/admin/backtests/walk-forward", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
}

/** `compareBacktestEngines`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export function compareBacktestEngines(
  input: BacktestComparisonRequest,
): Promise<BacktestEngineComparison> {
  return request<BacktestEngineComparison>("/api/admin/backtests/compare", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
}

/** `compareBacktestStrategies`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export function compareBacktestStrategies(
  input: BacktestStrategyComparisonRequest,
): Promise<BacktestStrategyComparison> {
  return request<BacktestStrategyComparison>("/api/admin/backtests/strategies/compare", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
}

/** `fetchModelVersions`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export function fetchModelVersions(symbol = ""): Promise<ModelRegistryData> {
  const params = new URLSearchParams({ limit: "25", offset: "0" });
  if (symbol) params.set("symbol", symbol);
  return request<ModelRegistryData>(`/api/admin/models?${params}`);
}

/** 체크섬을 통과한 직접 학습 모델의 품질 준비도를 조회한다. */
export function fetchLocalAiReadiness(): Promise<LocalAiReadinessData> {
  return request<LocalAiReadinessData>("/api/admin/local-ai/readiness");
}

/** `promoteModelVersion`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export function promoteModelVersion(version: string): Promise<{
  model: ModelVersion;
  runtime_activation: boolean;
  notice: string;
}> {
  return request(`/api/admin/models/${encodeURIComponent(version)}/promote`, {
    method: "POST",
  });
}

/** `fetchWatchlist`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export function fetchWatchlist(): Promise<WatchlistData> {
  return request<WatchlistData>("/api/admin/watchlist");
}

/** `addWatchlist`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export function addWatchlist(symbol: string): Promise<{ item: WatchlistItem }> {
  return request("/api/admin/watchlist", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ symbol }),
  });
}

/** `removeWatchlist`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export function removeWatchlist(symbol: string): Promise<{ removed: boolean }> {
  return request(`/api/admin/watchlist/${encodeURIComponent(symbol)}`, { method: "DELETE" });
}

/** `fetchPriceAlerts`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export function fetchPriceAlerts(): Promise<PriceAlertData> {
  return request<PriceAlertData>("/api/admin/alerts");
}

/** `createPriceAlert`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
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

/** `disablePriceAlert`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export function disablePriceAlert(alertId: string): Promise<{ disabled: boolean }> {
  return request(`/api/admin/alerts/${encodeURIComponent(alertId)}`, { method: "DELETE" });
}

/** `evaluatePriceAlerts`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export function evaluatePriceAlerts(): Promise<EvaluateResult> {
  return request<EvaluateResult>("/api/admin/alerts/evaluate", { method: "POST" });
}

/** `fetchBrokerAccounts`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export function fetchBrokerAccounts(): Promise<{ accounts: BrokerAccount[] }> {
  return request<{ accounts: BrokerAccount[] }>("/api/admin/broker-accounts");
}

/** `syncPortfolio`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export function syncPortfolio(accountSeq: number): Promise<PortfolioSyncResult> {
  return request<PortfolioSyncResult>(`/api/admin/portfolios/${accountSeq}/sync`, {
    method: "POST",
  });
}

/** `fetchTossAccountWorkspace`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export function fetchTossAccountWorkspace(
  accountSeq: number,
  currency: "KRW" | "USD" = "KRW",
): Promise<TossAccountWorkspace> {
  return request<TossAccountWorkspace>(
    `/api/admin/toss/accounts/${accountSeq}/workspace?currency=${currency}`,
  );
}

/** `fetchOperationsStatus`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export function fetchOperationsStatus(): Promise<OperationsStatus> {
  return request<OperationsStatus>("/api/admin/operations/status");
}

/** `fetchDataQualityHistory`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
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

/** `fetchCandlePriceBasisInventory`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export function fetchCandlePriceBasisInventory(
  symbol: string,
  limit = 200,
): Promise<CandlePriceBasisInventory> {
  const params = new URLSearchParams({ symbol, limit: String(limit) });
  return request<CandlePriceBasisInventory>(
    `/api/admin/candles/price-basis-inventory?${params}`,
  );
}

/** `fetchCorporateActionHistory`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export function fetchCorporateActionHistory(
  symbol: string,
  limit: number,
  offset: number,
): Promise<CorporateActionHistory> {
  const params = new URLSearchParams({ limit: String(limit), offset: String(offset) });
  if (symbol) params.set("symbol", symbol);
  return request<CorporateActionHistory>(`/api/admin/corporate-actions?${params}`);
}

/** `fetchCorporateActionIngestionStatus`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export function fetchCorporateActionIngestionStatus(): Promise<CorporateActionIngestionStatus> {
  return request<CorporateActionIngestionStatus>("/api/admin/corporate-actions/ingestion");
}

/** `triggerCorporateActionIngestion`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export function triggerCorporateActionIngestion(
  source: string,
  symbol: string,
  start: string,
  end: string,
  limit = 200,
): Promise<CorporateActionIngestionResult> {
  const params = new URLSearchParams({ start, end, limit: String(limit) });
  return request<CorporateActionIngestionResult>(
    `/api/admin/corporate-actions/ingestion/${encodeURIComponent(source)}/${encodeURIComponent(symbol)}?${params}`,
    { method: "POST" },
  );
}

/** `fetchCorporateActionCandidateStatus`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export function fetchCorporateActionCandidateStatus(): Promise<CorporateActionCandidateStatus> {
  return request<CorporateActionCandidateStatus>("/api/admin/corporate-actions/candidates");
}

/** `fetchCorporateActionApprovalStatus`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export function fetchCorporateActionApprovalStatus(): Promise<CorporateActionApprovalStatus> {
  return request<CorporateActionApprovalStatus>("/api/admin/corporate-actions/approvals");
}

/** `fetchCorporateActionCandidates`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export function fetchCorporateActionCandidates(
  source: string,
  symbol: string,
  start: string,
  end: string,
  limit = 100,
): Promise<CorporateActionCandidatePreview> {
  const params = new URLSearchParams({ start, end, limit: String(limit) });
  return request<CorporateActionCandidatePreview>(
    `/api/admin/corporate-actions/candidates/${encodeURIComponent(source)}/${encodeURIComponent(symbol)}?${params}`,
  );
}

/** `approveCorporateActionCandidate`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export function approveCorporateActionCandidate(
  source: string,
  symbol: string,
  input: CorporateActionApprovalRequest,
): Promise<CorporateActionApprovalResult> {
  return request<CorporateActionApprovalResult>(
    `/api/admin/corporate-actions/approvals/${encodeURIComponent(source)}/${encodeURIComponent(symbol)}`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(input),
    },
  );
}

/** `fetchProviderAuditHistory`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
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

/** `cleanupProviderAuditHistory`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export function cleanupProviderAuditHistory(): Promise<ProviderAuditMaintenanceStatus> {
  return request<ProviderAuditMaintenanceStatus>("/api/admin/provider-audits/cleanup", {
    method: "POST",
  });
}

/** `fetchDataLifecyclePreview`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export function fetchDataLifecyclePreview(): Promise<DataLifecyclePreview> {
  return request<DataLifecyclePreview>("/api/admin/data-lifecycle/preview");
}

/** `cleanupDataLifecycle`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export function cleanupDataLifecycle(): Promise<DataLifecycleStatus> {
  return request<DataLifecycleStatus>("/api/admin/data-lifecycle/cleanup", {
    method: "POST",
  });
}

/** `fetchIngestionStatus`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export function fetchIngestionStatus(): Promise<IngestionStatus> {
  return request<IngestionStatus>("/api/admin/ingestion");
}

/** `triggerIngestion`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export function triggerIngestion(symbol: string, limit?: number): Promise<IngestionResult> {
  const params = new URLSearchParams();
  if (limit != null) params.set("limit", String(limit));
  const query = params.size > 0 ? `?${params}` : "";
  return request<IngestionResult>(
    `/api/admin/ingestion/${encodeURIComponent(symbol)}${query}`,
    { method: "POST" },
  );
}
