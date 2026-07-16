# AI reports and compliance

Phase 13 adds an explanatory report pipeline. It is deliberately separated from the
calculation engines so an LLM cannot invent, calculate, or execute trading decisions.

```text
stock profile
    -> Score Agent (one candle/source collection)
       -> Technical / Financial / News / Disclosure findings
       -> cached warnings and investor-flow facts
    -> Prediction / Risk / Investor Flow / Chart Pattern / Support-Resistance agents
    -> MasterAnalysisOrchestrator (bounded structured findings)
    -> mock generator (default) or OpenAI structured-output generator
    -> ComplianceValidator final gate
    -> ai_reports audit history
```

`GET /api/v1/stocks/{symbol}/ai-report?horizon_days=5&limit=180` returns an
experimental, reference-only report. Its own payload, as well as the common API
envelope, always includes `data_as_of`, a non-empty `disclaimer`, and
`is_investment_advice: false`.

The deterministic `mock` generator is the default and needs no external key. To use
OpenAI, set `AI_REPORT_PROVIDER=openai` and configure `OPENAI_API_KEY` only on the
server. The OpenAI adapter calls the Responses API with strict JSON Schema output and
sends only pre-computed facts. It does not expose the key to the browser.

The final validator rejects missing compliance fields, unsupported reference signals,
and direct buy/sell instructions. A rejected report is not stored. Passing reports are
recorded in `ai_reports` with generator, model version, data timestamp, validation
status, and the full audited payload.

The Score analysis bundle retains the exact facts and candles used for its six axes.
Downstream agents reuse that bundle, so warnings, investor flow, and support/resistance
are not fetched again during the same report. `agent_findings` exposes each agent's
status, bounded evidence, source timestamp, and structured value for auditability.
The Chart Pattern Agent reuses the same cleaned candle bundle and exposes only
deterministically calculated experimental patterns.

The current reference signals are `positive_watch`, `neutral_watch`,
`defensive_watch`, `risk_aware`, and `data_insufficient`.
They are not investment recommendations. Support and resistance are a clearly labelled
experimental trailing 20-candle range, computed in the service layer rather than by the
LLM.
