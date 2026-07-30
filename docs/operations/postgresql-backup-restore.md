# PostgreSQL backup and restore runbook

This procedure is a desktop/operations task. It creates a custom-format logical backup and
restores it into a separate verification database. Never restore a rehearsal backup over the live
`stockpilot` database.

## 1. Preconditions

1. Pull the tested `main` branch and start the Compose stack.
2. Confirm `docker compose ps` reports PostgreSQL and the API as healthy.
3. Create the ignored local directory with `New-Item -ItemType Directory -Force backups`.
4. Keep passwords in `.env` or a secret manager. Do not paste them into this document, command
   history, issue comments or test output.

## 2. Create and inspect a backup

Run the dump inside the PostgreSQL container to avoid PowerShell binary redirection problems:

```powershell
docker compose exec -T postgres sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc --no-owner --no-privileges -f /tmp/stockpilot.dump'
docker compose exec -T postgres pg_restore --list /tmp/stockpilot.dump
docker compose cp postgres:/tmp/stockpilot.dump .\backups\stockpilot-latest.dump
docker compose exec -T postgres rm -f /tmp/stockpilot.dump
```

Record the backup time, application release, Alembic revision, file size and SHA-256 digest in the
operations ticket. Backup files are excluded by `.gitignore` and must never be committed.

```powershell
Get-FileHash .\backups\stockpilot-latest.dump -Algorithm SHA256
.venv\Scripts\alembic.exe -c alembic.ini current
```

## 3. Restore into an isolated database

Use a disposable name and verify it does not already contain required data before proceeding:

```powershell
docker compose exec -T postgres createdb -U stockpilot stockpilot_restore_check
docker compose cp .\backups\stockpilot-latest.dump postgres:/tmp/stockpilot-restore.dump
docker compose exec -T postgres pg_restore -U stockpilot -d stockpilot_restore_check --no-owner --no-privileges --exit-on-error /tmp/stockpilot-restore.dump
```

If `createdb` reports that the database already exists, stop and select another disposable name.
Do not drop a database until its identity and purpose have been independently confirmed.

## 4. Validate the restored database

Check that critical tables exist and compare row counts between the source and restored database.
At minimum compare `stocks`, `stock_candles`, `data_quality_logs`, `backtest_runs`, `predictions`,
`ai_reports`, `broker_accounts`, `holdings` and `provider_audit_logs`.

```powershell
docker compose exec -T postgres psql -U stockpilot -d stockpilot_restore_check -c "SELECT version_num FROM alembic_version;"
docker compose exec -T postgres psql -U stockpilot -d stockpilot_restore_check -c "SELECT count(*) FROM stocks; SELECT count(*) FROM stock_candles; SELECT count(*) FROM backtest_runs; SELECT count(*) FROM broker_accounts;"
```

Run the API against the restored database only in an isolated process/container and verify
`/health/ready`, one market-data read, administrator operations status and a backtest-history read.
Do not enable schedulers, lifecycle cleanup, account sync or external providers during the
rehearsal.

## 5. Close the rehearsal

Save the validation record and remove the temporary file inside the container. Deleting the
verification database or local backup is a deliberate operator action and is not automated by this
project.

```powershell
docker compose exec -T postgres rm -f /tmp/stockpilot-restore.dump
```

Production backups additionally require encrypted storage, access control, off-host copies,
retention rules, restore drills and monitoring appropriate to the deployment platform.
