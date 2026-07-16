# Realtime quote architecture

## Phase 15-A: REST polling

The first realtime stage polls only symbols with active WebSocket subscribers.

1. `PollingQuoteSource` resolves the active quote provider through `BrokerAdapter`.
2. `RealtimeQuoteHub` validates subscriptions, limits the active symbol set, and polls every
   configured interval.
3. `RedisQuoteBus` stores the latest quote with a short TTL and publishes it to a per-symbol
   Redis channel.
4. `/ws/v1/quotes/{symbol}` fans Redis events out to browser clients.

The provider remains responsible for its own rate limiting. With the default 20-symbol limit
and two-second polling interval, the nominal request rate is at most 10 quote requests per
second before provider-side throttling.

Set these variables to enable the path:

```env
REALTIME_ENABLED=true
REALTIME_POLL_INTERVAL_SECONDS=2
REALTIME_CACHE_TTL_SECONDS=3
REALTIME_MAX_SYMBOLS=20
REALTIME_MAX_CONNECTIONS=200
```

Quote messages always include `data_as_of`, `provider`, and
`is_investment_advice: false`. Provider failures are emitted as structured error messages and
do not terminate the polling task.

## Phase 15-B: KIS streaming

The KIS streaming source is available behind `REALTIME_SOURCE=kis`. It obtains a WebSocket
approval key from `/oauth2/Approval`, shares one upstream connection across active browser
subscriptions, and reconnects with bounded exponential backoff.

- Domestic KRX trades use `H0STCNT0`.
- Overseas trades use `HDFSCNT0`; NASDAQ, NYSE, and AMEX symbols are normalized to the KIS
  subscription key format.
- Provider payloads are converted to the same `Quote` and browser message contracts used by
  polling, so `/ws/v1/quotes/{symbol}` and the frontend remain unchanged.
- The official KIS maximum of 40 active subscriptions is enforced by both the source and hub.
- KIS system `PINGPONG` messages are answered and malformed records are rejected as provider
  validation errors.

Production configuration:

```env
REALTIME_ENABLED=true
REALTIME_SOURCE=kis
KIS_BASE_URL=https://openapi.koreainvestment.com:9443
KIS_WS_URL=ws://ops.koreainvestment.com:21000/tryitout
KIS_APP_KEY=...
KIS_APP_SECRET=...
```

For paper trading, use the matching virtual REST and WebSocket endpoints instead of mixing
production and virtual environments. Keep `REALTIME_SOURCE=polling` until KIS credentials have
been issued and registered. The implementation follows the current
[official KIS Open API examples](https://github.com/koreainvestment/open-trading-api).
