/**
 * 전문 AI 한 명의 분석 결과를 사무실 UI가 공통 방식으로 소비하기 위한 계약입니다.
 * 식별·배치 정보, 보정된 확률, 데이터 품질, 검증 성능, 주요 근거를 함께 전달합니다.
 */
export interface OfficeAnalysisAgent {
  id: "technical" | "risk" | "financial" | "news" | "flow" | "master";
  name: string;
  role: string;
  room: "ANALYSTS" | "RISK_MGMT" | "PM_OFFICE";
  probability: number | null;
  calibrated_band: "LOW" | "MID" | "HIGH";
  data_available: boolean;
  experimental: boolean;
  experimental_reason?: string;
  sample_size: number;
  validation_accuracy: number | null;
  baseline_accuracy: number | null;
  top_features: Array<{ name: string; value: number; direction: "bullish" | "neutral" | "bearish" }>;
}

/**
 * 종목 분석 API와 사무실 UI 사이의 최상위 응답 계약입니다.
 * 실제 시세, 최종 판정, 전문가별 결과, 회의 기록과 투자 유의 문구를 한 응답으로 묶습니다.
 */
export interface OfficeAnalysisResponse {
  analysis_id: string;
  symbol: string;
  name: string;
  market: string;
  price: number | null;
  change_pct: number | null;
  currency: string;
  verdict: {
    signal: "UPSIDE_FAVORED" | "DOWNSIDE_FAVORED" | "NEUTRAL" | "DATA_INSUFFICIENT";
    signal_label: string;
    confidence: number | null;
    summary: string;
    key_points: string[];
    levels: {
      entry_zone: { low: number | null; high: number | null };
      stop_reference: { price: number | null; pct: number | null };
      target_reference: { price: number | null; pct: number | null };
      risk_reward: number | null;
    };
    final_note: string;
  };
  agents: OfficeAnalysisAgent[];
  meeting_log: Array<{ seq: number; agent: string; message: string }>;
  disclaimer: string;
  data_as_of: string;
  model_version: string;
  is_investment_advice: false;
}

const specialistDefaults: Array<Pick<OfficeAnalysisAgent, "id" | "name" | "role" | "room">> = [
  { id: "technical", name: "차트", role: "테크니컬 애널리스트", room: "ANALYSTS" },
  { id: "risk", name: "볼가드", role: "리스크 매니저", room: "RISK_MGMT" },
  { id: "financial", name: "장부", role: "재무 애널리스트", room: "ANALYSTS" },
  { id: "news", name: "뉴스", role: "뉴스 애널리스트", room: "ANALYSTS" },
  { id: "flow", name: "저울추", role: "수급 애널리스트", room: "RISK_MGMT" },
  { id: "master", name: "회장님", role: "종합 판단", room: "PM_OFFICE" },
];

/**
 * 백엔드 연결 없이 UI 계약만 점검할 때 사용하는 안전한 모의 응답을 만듭니다.
 * 실제로 얻지 않은 가격이나 확률은 만들지 않고 모두 null 또는 데이터 부족으로 표시합니다.
 */
export function createSafeMockAnalysis(symbol: string): OfficeAnalysisResponse {
  const normalizedSymbol = symbol.toUpperCase().replace(/[^0-9A-Z.-]/g, "").slice(0, 16) || "UNKNOWN";
  return {
    analysis_id: `mock_${normalizedSymbol}`,
    symbol: normalizedSymbol,
    name: normalizedSymbol,
    market: "MOCK",
    price: null,
    change_pct: null,
    currency: "USD",
    verdict: {
      signal: "DATA_INSUFFICIENT",
      signal_label: "데이터 부족 · 판단 보류",
      confidence: null,
      summary: "이 응답은 프론트엔드 연동 확인용 목업입니다. 실제 종목 분석 결과가 아닙니다.",
      key_points: ["실제 API 연결 전 UI 계약 확인용", "확률과 가격 수준을 임의 생성하지 않음", "투자 판단에 사용할 수 없음"],
      levels: {
        entry_zone: { low: null, high: null },
        stop_reference: { price: null, pct: null },
        target_reference: { price: null, pct: null },
        risk_reward: null,
      },
      final_note: "모든 에이전트는 목업 상태이며 verdict 산출에서 제외되었습니다.",
    },
    agents: specialistDefaults.map((agent) => ({
      ...agent,
      probability: null,
      calibrated_band: "LOW",
      data_available: false,
      experimental: true,
      experimental_reason: "UI 계약 확인용 목업",
      sample_size: 0,
      validation_accuracy: null,
      baseline_accuracy: null,
      top_features: [],
    })),
    meeting_log: specialistDefaults.map((agent, index) => ({
      seq: index + 1,
      agent: agent.id,
      message: `${agent.name} 에이전트 연결을 확인했습니다. 실제 분석 데이터는 포함되지 않습니다.`,
    })),
    disclaimer: "본 분석은 투자 자문이 아닌 참고 정보입니다. 투자 판단과 책임은 본인에게 있습니다.",
    data_as_of: new Date().toISOString(),
    model_version: "mock_ui_contract_v1",
    is_investment_advice: false,
  };
}
