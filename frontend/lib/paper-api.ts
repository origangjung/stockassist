/** 모의투자 BFF와 통신하는 브라우저 전용 타입 및 함수다. */

export interface PaperPosition {
  symbol: string;
  name: string;
  market: string;
  currency: "KRW" | "USD";
  quantity: string;
  average_price: string;
  last_price: string;
  market_value: string;
  unrealized_pnl: string;
  realized_pnl: string;
  return_percent: string;
  price_status: "live" | "last_fill";
}

/** PaperOrder 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. */
export interface PaperOrder {
  order_id: string;
  symbol: string;
  name: string;
  currency: "KRW" | "USD";
  side: "buy" | "sell";
  quantity: string;
  fill_price: string;
  commission: string;
  executed_at: string;
}

/** PaperRiskSummary 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. */
export interface PaperRiskSummary {
  status: "stable" | "caution" | "high";
  invested_ratio: string;
  cash_ratio: string;
  largest_position_symbol: string | null;
  largest_position_ratio: string;
  warnings: Array<"single_position_concentration" | "low_cash_buffer">;
  limits: {
    max_order_ratio: string;
    max_position_ratio: string;
    max_invested_ratio: string;
  };
}

/** PaperPortfolio 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. */
export interface PaperPortfolio {
  account: { account_id: string; cash_krw: string; cash_usd: string };
  persistence_status: "saved" | "temporary";
  saved_at: string;
  totals: Record<"KRW" | "USD", {
    initial_cash: string;
    cash: string;
    market_value: string;
    unrealized_pnl: string;
    equity: string;
    total_pnl: string;
    return_percent: string;
  }>;
  risk: Record<"KRW" | "USD", PaperRiskSummary>;
  positions: PaperPosition[];
  orders: PaperOrder[];
  commission_rate: string;
  execution_policy: string;
  is_real_order: false;
}

/** 자금배분 엔진이 반환하는 실행 전용이 아닌 목표 비중과 단계별 모의주문 후보다. */
export interface FundAllocationProposal {
  account_id: string;
  currency: "KRW" | "USD";
  objective: "min_volatility" | "max_sharpe";
  optimizer: string;
  lookback_days: number;
  observation_count: number;
  equity: string;
  target_weights: Record<string, string>;
  target_cash_weight: string;
  current_weights: Record<string, string>;
  rebalance_actions: Array<{
    symbol: string;
    side: "buy" | "sell";
    quantity: string;
    notional: string;
    target_weight: string;
    reason: "target_allocation_gap" | "outside_universe" | "staged_for_order_limit";
  }>;
  estimated_turnover: string;
  warnings: string[];
  execution_enabled: false;
  is_real_order: false;
}

const ACCOUNT_KEY = "stockpilot:paper-account-id";

/** 개인정보 없이 브라우저에만 보관되는 모의투자 계정 식별자를 반환한다. */
export function getPaperAccountId(): string {
  const created = crypto.randomUUID();
  for (const storage of [window.localStorage, window.sessionStorage]) {
    try {
      const existing = storage.getItem(ACCOUNT_KEY);
      if (existing && /^[0-9a-f-]{36}$/.test(existing)) return existing;
      storage.setItem(ACCOUNT_KEY, created);
      return created;
    } catch {
      // 개인정보 보호 설정이 한 저장소를 막으면 다음 저장소나 현재 탭 계정으로 계속한다.
    }
  }
  return created;
}

/** Envelope 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. */
interface Envelope<T> { success: boolean; data?: T; error?: { message?: string } }

/** `request`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`/api/paper${path}`, { ...init, cache: "no-store" });
  const envelope = await response.json().catch(() => null) as Envelope<T> | null;
  if (!response.ok || !envelope?.success || envelope.data === undefined) {
    throw new Error(envelope?.error?.message || "모의투자 요청을 처리하지 못했습니다.");
  }
  return envelope.data;
}

/** `fetchPaperPortfolio`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export function fetchPaperPortfolio(accountId: string): Promise<PaperPortfolio> {
  return request(`/${accountId}`);
}

/** `createPaperOrder`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export function createPaperOrder(
  accountId: string,
  order: { symbol: string; side: "buy" | "sell"; quantity: string; idempotency_key: string },
): Promise<PaperPortfolio> {
  return request(`/${accountId}/orders`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(order),
  });
}

/** `resetPaperPortfolio`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export function resetPaperPortfolio(accountId: string): Promise<PaperPortfolio> {
  return request(`/${accountId}/reset`, { method: "POST" });
}

/** 선택한 종목과 운용 성향으로 실제 주문 없는 목표배분 제안을 생성한다. */
export function createAllocationProposal(
  accountId: string,
  input: {
    symbols: string[];
    objective: "min_volatility" | "max_sharpe";
    invest_ratio: string;
    max_asset_weight: string;
    lookback_days: number;
  },
): Promise<FundAllocationProposal> {
  return request(`/${accountId}/allocation-proposals`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
}
