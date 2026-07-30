# Desktop validation checklist

<!-- current-alembic-head: 20260720_0021 -->

Run this checklist on the desktop after receiving the laptop's tested changes. These tasks are
kept off the space-constrained laptop. Pull only when the user has chosen to transfer the changes
through the remote repository; do not create a commit or push merely to start this checklist.

## Required for the current handoff

- [ ] If the user transferred changes through Git, run `git pull --ff-only origin main`; otherwise confirm the received worktree/archive or commit is the intended tested version
- [ ] Confirm `.env` exists locally but is not tracked with `git ls-files .env`
- [ ] Run `.venv\Scripts\python.exe -m scripts.check_production_env --env-file .env` for a production deployment
- [ ] `docker compose config --quiet`
- [ ] `docker compose build` and record image sizes
- [ ] `docker compose up -d` and wait for healthy services
- [ ] `docker compose exec api alembic heads` reports `20260720_0021`
- [ ] Confirm CI's `PostgreSQL migration round-trip` job passed before touching a persistent database
- [ ] Confirm the three `created_at` lifecycle indexes exist in PostgreSQL
- [ ] Confirm `corporate_actions` and `stock_candles.price_basis` exist after migration
- [ ] Verify existing candle rows are `unknown` and new Toss rows are `provider_adjusted`
- [ ] Open the admin Operations tab and verify lifecycle preview counts load
- [ ] Verify the candle archive preview lists only complete monthly partitions older than the cutoff
- [ ] Confirm candle archive preview reports `automatic_action=false`; do not detach or drop data
- [ ] Keep automatic lifecycle cleanup disabled until the preview and policy are approved
- [ ] Perform the isolated backup/restore rehearsal in `postgresql-backup-restore.md`
- [ ] Run the full backend and TypeScript checks from `DESKTOP_CODEX_HANDOFF.md`

## Later heavy verification

- [ ] Toss REST soak test with real 401/403/429/5xx and `Retry-After` behavior
- [ ] KIS domestic and US WebSocket reconnect/subscription-limit tests
- [ ] Redis Pub/Sub and distributed rate-limit load tests
- [ ] XGBoost dependency installation, long training and walk-forward evaluation
- [ ] Measure PostgreSQL partition and lifecycle cleanup performance with production-like volumes

Never commit `.env`, database dumps, model artifacts containing private data, credentials or raw
provider responses. Commit only source changes and sanitized measurement reports.
