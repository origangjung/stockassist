# Desktop validation record: 2026-08-10

This record captures the non-mutating local checks completed against the Docker Compose stack.
It supplements the reusable [desktop validation checklist](desktop-validation.md) and contains no
credentials, provider payloads, connection strings, or backup hashes.

## Verified

| Check | Result |
| --- | --- |
| Alembic head and applied revision | `20260720_0021` |
| Lifecycle `created_at` indexes | All three expected indexes present |
| Corporate-action table | Present |
| `stock_candles.price_basis` | Present |
| Operations API | `operational`, ready |
| PostgreSQL persistence | Enabled and ready |
| Redis distributed rate limiting | Enabled and ready |
| Lifecycle preview | Ready; zero eligible rows in all three allowlisted datasets |
| Automatic lifecycle cleanup | Disabled |
| Price-basis inventory | Read only; `automatic_relabel=false`, `mutation_performed=false` |
| Partition archive automatic action | `false` |
| API image size | 172,571,043 bytes, approximately 164.6 MiB |
| Web image size | 68,333,326 bytes, approximately 65.2 MiB |

The database contained only the `stock_candles_default` partition. Partition maintenance was
disabled by the local environment, so archive status was disabled with no candidates and no
cutoff. No partition was created, detached, dropped, or otherwise changed during this validation.

The lifecycle preview reported two retained news rows and no expired rows. Data-quality,
disclosure, corporate-action, and candle tables had no rows relevant to the requested checks.

## Not claimed

- Existing-candle `legacy_unknown` classification could not be observed because no candle rows
  were stored.
- New Toss candle `provider_adjusted` classification was not exercised because doing so would call
  the live provider and persist data. Unit and integration tests cover the classification policy.
- Remote CI status was not inferred from the local worktree.
- External HTTPS, alert delivery, and production host configuration still depend on deployment
  domains, certificates, and an operator-selected notification destination.

The local stack remained available through `http://127.0.0.1:8080` after validation.
