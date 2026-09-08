import assert from "node:assert/strict";
import { test } from "node:test";

import {
  buildAnalysisSequence,
  orderedAvailableAgents,
} from "./analysis-sequence.ts";

test("keeps the canonical specialist order and excludes unavailable agents", () => {
  assert.deepEqual(
    orderedAvailableAgents(["risk", "technical", "investor_flow"]),
    ["technical", "investor_flow", "risk"],
  );
});

test("moves from specialists through debate, trading, and final review", () => {
  const steps = buildAnalysisSequence(["technical", "risk"], {
    briefingMs: 10,
    courseMs: 20,
    researchDebateMs: 30,
    tradingReviewMs: 40,
    finalServiceMs: 50,
  });

  assert.deepEqual(steps.map((step) => step.phase), [
    "technical",
    "risk",
    "research",
    "trading",
    "serving",
    "synthesis",
  ]);
  assert.deepEqual(steps.map((step) => step.atMs), [10, 30, 50, 80, 120, 170]);
  assert.equal(steps.at(-1)?.complete, true);
  assert.equal(steps.at(-1)?.revealedCount, 2);
});

test("finishes immediately and safely when no specialist data is available", () => {
  const steps = buildAnalysisSequence([]);
  assert.equal(steps.length, 1);
  assert.deepEqual(steps[0], {
    announcement: "사용 가능한 분석 근거가 없어 종합 참고 결과만 표시합니다.",
    atMs: 0,
    complete: true,
    phase: "synthesis",
    revealedCount: 0,
  });
});
