# Multi-market stock data

Market-data contracts now carry both `market` and `currency`. Domestic symbols keep their KRX market and `KRW`; US symbols can use their standard ticker (for example `AAPL`, `MSFT`, `NVDA`, `TSLA`, and `JPM`) with `NASDAQ` or `NYSE` and `USD`.

The Mock provider includes deterministic domestic and US fixtures. The Toss provider uses the same market-data endpoints for both symbol types, preserving the currency returned by the upstream API and allowing decimal execution quantities for US fractional-share trades.

This change covers market data: quote, candles, order book, trades, stock master, and warnings. DART financial statements and disclosures remain domestic-company features. US financials and filings require a separate SEC/EDGAR provider before they are exposed through the financial and disclosure endpoints.
