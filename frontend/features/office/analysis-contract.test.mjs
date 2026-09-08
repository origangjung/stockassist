import assert from "node:assert/strict";
import { test } from "node:test";

import { createSafeMockAnalysis } from "./analysis-contract.ts";

test("creates a complete mock contract without fabricated investment values", () => {
  const response = createSafeMockAnalysis("aapl<script>");
  assert.equal(response.symbol, "AAPLSCRIPT");
  assert.equal(response.verdict.signal, "DATA_INSUFFICIENT");
  assert.equal(response.verdict.confidence, null);
  assert.equal(response.verdict.levels.risk_reward, null);
  assert.equal(response.agents.length, 6);
  assert.equal(response.agents.every((agent) => agent.experimental), true);
  assert.equal(response.is_investment_advice, false);
});
