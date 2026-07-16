# Investor-flow analysis

Phase 11 adds a domestic-stock investor-flow snapshot with foreign, institution, and individual net quantities plus foreign holding information.

- `MockInvestorFlowProvider` supplies deterministic Korean fixtures for local development.
- `KisInvestorFlowProvider` maps KIS's domestic investor endpoint to the shared contract and caches the access token in-process.
- Results are stored in `stock_investor_flows` and always marked `experimental: true`.
- The combined foreign-plus-institution quantity becomes a neutral `reference_signal`: `net_inflow`, `net_outflow`, or `balanced`. It is not a trade instruction.

Set `INVESTOR_FLOW_PROVIDER=kis`, `KIS_APP_KEY`, and `KIS_APP_SECRET` to use KIS. This source is intentionally limited to Korean six-digit symbols; US investor-flow categories need a separate provider and are rejected rather than mislabelled.
