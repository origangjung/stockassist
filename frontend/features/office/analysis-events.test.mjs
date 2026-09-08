import assert from "node:assert/strict";
import { test } from "node:test";

import { createTimedAnalysisEventStream } from "./analysis-events.ts";

test("emits room, alternating debate, and verdict events through one stream", async () => {
  const events = [];
  const steps = [
    { announcement: "debate", atMs: -150, complete: false, phase: "research", revealedCount: 2 },
    { announcement: "done", atMs: 5, complete: true, phase: "synthesis", revealedCount: 2 },
  ];
  const stream = createTimedAnalysisEventStream({ analysisId: "test-1", steps });
  const unsubscribe = stream.subscribe((event) => events.push(event));
  await new Promise((resolve) => setTimeout(resolve, 25));
  unsubscribe();

  assert.equal(events[0].type, "room_active");
  assert.equal(events.some((event) => event.type === "agent_speak" && event.payload.agent === "bull"), true);
  assert.deepEqual(events.at(-1), { type: "verdict_ready", payload: { analysisId: "test-1" } });
});
