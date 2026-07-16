# Portfolio synchronization

Phase 14 provides read-only synchronization for a user's own Toss Securities account.
It maps the documented `GET /api/v1/accounts` and `GET /api/v1/holdings` responses
through the existing capability router.

```text
GET /api/v1/broker-accounts (X-Admin-Key required)
    -> select ACCOUNT_SYNC provider
    -> account list (masked account number only)

POST /api/v1/portfolios/{account_seq}/sync (X-Admin-Key required)
    -> verify the selected own account
    -> holdings snapshot with X-Tossinvest-Account
    -> broker_accounts + holdings persistence
    -> read-only exposure analysis
```

Account synchronization is disabled by default. Enable it only after protecting the
server with user authentication and private network access:

```dotenv
ACCOUNT_SYNC_ENABLED=true
```

The API never returns a full account number; only the final four digits are shown.
It stores a masked account number, `accountSeq`, account type, and latest holdings.
No broker credential is stored in the database.

JWT/RBAC 사용자 인증이 추가되기 전까지 계좌 API는 관리자 키 경계 안에서만 접근할 수 있다. Next.js 관리자 BFF가 서버 사이드에서 키를 전달하므로 브라우저에는 `ADMIN_API_KEY`가 노출되지 않는다.

Korean and US holdings can be synchronized together. Monetary totals and allocations
are kept separate by currency (`KRW` and `USD`), rather than silently applying an
unverified exchange rate. The analysis is labelled experimental and reference-only;
it creates no order and exposes no order endpoint.

`portfolio-2026.2` 분석은 통화별로 평가금액, 비용 반영 손익률, 최대 종목 비중, HHI 집중도, 실효 종목 수, 손실 종목 평가금액 비중을 계산한다. 검증되지 않은 환율로 KRW와 USD를 합산하지 않는다. 결과의 `execution_enabled`는 항상 `false`이며 집중도·손실 신호는 참고 정보다.
