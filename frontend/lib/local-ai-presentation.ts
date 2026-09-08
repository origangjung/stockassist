type LocalAgent = "technical" | "financial" | "news" | "investor_flow" | "risk";

const labels: Record<string, string> = {
  return_1d: "1일 수익률",
  return_5d: "5일 수익률",
  sma_5_gap: "5일 평균선 대비",
  sma_20_gap: "20일 평균선 대비",
  volatility_20: "20일 변동성",
  volume_ratio: "평균 거래량 대비",
  rsi_14: "RSI",
  revenue_growth_yoy: "매출 성장률",
  net_income_growth_yoy: "순이익 성장률",
  net_margin: "순이익률",
  debt_to_assets: "자산 대비 부채",
  equity_to_assets: "자산 대비 자기자본",
  asset_growth_yoy: "자산 성장률",
  article_count_3d: "최근 3일 기사",
  positive_ratio: "긍정 표현 비중",
  negative_ratio: "부정 표현 비중",
  sentiment_balance: "뉴스 감성 균형",
  source_diversity: "뉴스 출처 다양성",
  short_volume_ratio: "공매도 거래 비율",
  short_exempt_ratio: "공매도 면제 비율",
  short_ratio_5d: "5일 평균 공매도 비율",
  short_ratio_20d: "20일 평균 공매도 비율",
  short_ratio_change_5d: "5일 공매도 비율 변화",
  reported_volume_ratio_20d: "평균 보고 거래량 대비",
  drawdown_20: "20일 최대 낙폭",
  downside_deviation_20: "20일 하방 변동성",
  range_width_20: "20일 가격 범위",
  market_volatility_20: "시장 변동성",
  relative_volatility_20: "시장 대비 변동성",
  vix_level: "VIX",
  treasury_10y: "미국 10년물 금리",
  yield_curve_10y_2y: "10년-2년 금리차",
  fed_funds_rate: "미국 기준금리",
  broad_dollar_change_20d: "달러지수 20일 변화",
  validation_balanced_accuracy: "검증 균형 정확도",
  validation_roc_auc: "검증 ROC-AUC",
  validation_calibration_error: "확률 보정 오차",
};

const ratios = new Set(["volume_ratio", "reported_volume_ratio_20d"]);
const plainHundreds = new Set(["rsi_14", "vix_level"]);
const signedPercentKeys = new Set([
  "return_1d",
  "return_5d",
  "sma_5_gap",
  "sma_20_gap",
  "revenue_growth_yoy",
  "net_income_growth_yoy",
  "asset_growth_yoy",
  "sentiment_balance",
  "short_ratio_change_5d",
  "drawdown_20",
  "relative_volatility_20",
  "yield_curve_10y_2y",
  "broad_dollar_change_20d",
]);
const qualityKeys = new Set([
  "validation_balanced_accuracy",
  "validation_roc_auc",
  "validation_calibration_error",
]);

/** `signedPercent`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
function signedPercent(value: number) {
  const percentage = value * 100;
  const prefix = percentage > 0 ? "+" : "";
  return `${prefix}${percentage.toFixed(1)}%`;
}

/** `localConfidenceLabel`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export function localConfidenceLabel(value: number | null | undefined) {
  if (value == null || value < 0.34) return "낮음";
  if (value < 0.67) return "보통";
  return "높음";
}

/** `localEvidenceLabel`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export function localEvidenceLabel(
  _agent: LocalAgent | string,
  evidence: string,
): string | null {
  const separator = evidence.indexOf("=");
  if (separator <= 0) return null;
  const key = evidence.slice(0, separator);
  const label = labels[key];
  const value = Number(evidence.slice(separator + 1));
  if (!label || !Number.isFinite(value)) return null;
  if (key === "article_count_3d") {
    return `${label} ${Math.max(0, Math.round(Math.expm1(value)))}건`;
  }
  if (ratios.has(key)) return `${label} ${value.toFixed(2)}배`;
  if (plainHundreds.has(key)) return `${label} ${(value * 100).toFixed(1)}`;
  if (key === "validation_roc_auc") return `${label} ${value.toFixed(3)}`;
  if (qualityKeys.has(key)) return `${label} ${(value * 100).toFixed(1)}%`;
  return `${label} ${signedPercentKeys.has(key) ? signedPercent(value) : `${(value * 100).toFixed(1)}%`}`;
}

/** `isLocalQualityEvidence`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export function isLocalQualityEvidence(evidence: string) {
  return qualityKeys.has(evidence.split("=", 1)[0]);
}

/** 백엔드 진단 문자열 중 알려진 원시 표현을 투자자가 읽는 문장으로 변환한다. */
export function humanizeAnalysisText(text: string) {
  if (/^active_warning_count=0(?:\.0+)?$/.test(text)) return "활성 투자유의 신호 없음";
  if (/^active_warning_count=/.test(text)) {
    const count = Number(text.split("=", 2)[1]);
    return Number.isFinite(count) ? `활성 투자유의 신호 ${Math.round(count)}건` : "투자유의 신호 확인 필요";
  }
  if (/reference_signal\+net_inflow/i.test(text)) return "순매수 우위 수급 신호";
  if (/뉴스 감성\s+neutral\s*\(0(?:\.0+)?\)/i.test(text)) return "뉴스 감성 중립";
  if (/neutral\s*\(0(?:\.0+)?\)/i.test(text)) return text.replace(/neutral\s*\(0(?:\.0+)?\)/i, "중립");
  const macd = text.match(/MACD histogram\s+(-?[\d,.]+)/i);
  if (macd) {
    const value = Number(macd[1].replaceAll(",", ""));
    if (Number.isFinite(value)) return `MACD 히스토그램 ${value >= 0 ? "양전환 (+)" : "음전환 (-)"}`;
  }
  return text;
}
