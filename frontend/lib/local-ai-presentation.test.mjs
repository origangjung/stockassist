import assert from "node:assert/strict";
import { test } from "node:test";

import {
  humanizeAnalysisText,
  isLocalQualityEvidence,
  localConfidenceLabel,
  localEvidenceLabel,
} from "./local-ai-presentation.ts";

test("maps local model values into readable Korean evidence", () => {
  assert.equal(localEvidenceLabel("technical", "return_5d=0.031"), "5일 수익률 +3.1%");
  assert.equal(localEvidenceLabel("technical", "rsi_14=0.62"), "RSI 62.0");
  assert.equal(localEvidenceLabel("news", "article_count_3d=1.386294"), "최근 3일 기사 3건");
  assert.equal(localEvidenceLabel("risk", "asset_scope=equity"), null);
});

test("separates validation quality and maps confidence bands", () => {
  assert.equal(
    localEvidenceLabel("risk", "validation_calibration_error=0.0199"),
    "확률 보정 오차 2.0%",
  );
  assert.equal(isLocalQualityEvidence("validation_roc_auc=0.8213"), true);
  assert.equal(localConfidenceLabel(0.2), "낮음");
  assert.equal(localConfidenceLabel(0.5), "보통");
  assert.equal(localConfidenceLabel(0.8), "높음");
});

test("converts known developer diagnostics into readable Korean", () => {
  assert.equal(humanizeAnalysisText("active_warning_count=0"), "활성 투자유의 신호 없음");
  assert.equal(humanizeAnalysisText("reference_signal+net_inflow"), "순매수 우위 수급 신호");
  assert.equal(humanizeAnalysisText("뉴스 감성 neutral (0.000)"), "뉴스 감성 중립");
  assert.equal(humanizeAnalysisText("MACD histogram 6209.56"), "MACD 히스토그램 양전환 (+)");
});
