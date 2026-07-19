# Desktop validation checklist

Run this checklist on the desktop after pulling the laptop's tested `main` branch. These tasks are
kept off the space-constrained laptop.

## Required for the current handoff

- [ ] `git pull --ff-only origin main`
- [ ] Confirm `.env` exists locally but is not tracked with `git ls-files .env`
- [ ] `docker compose config --quiet`
- [ ] `docker compose build` and record image sizes
- [ ] `docker compose up -d` and wait for healthy services
- [ ] `docker compose exec api alembic heads` reports `20260719_0017`
- [ ] Confirm the three `created_at` lifecycle indexes exist in PostgreSQL
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
