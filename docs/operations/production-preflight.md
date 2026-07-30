# Production environment preflight

Run this check before building or starting a production deployment. It validates configuration
shape only; it does not contact PostgreSQL, Redis, brokers, or public APIs.

```powershell
.venv\Scripts\python.exe -m scripts.check_production_env --env-file .env
```

The env file path is mandatory. The command never opens `.env` implicitly and never prints values.
It reports only variable names and required actions. In particular it verifies:

- production mode, PostgreSQL persistence, Redis rate limiting, JSON logs and metrics;
- non-placeholder PostgreSQL, administrator, analysis, UI and Grafana credentials;
- agreement between `DATABASE_URL` and `POSTGRES_PASSWORD` without displaying either value;
- an HTTPS public URL, HTTPS CORS origins and a bounded Host allowlist;
- credentials required by enabled Toss, DART, KIS and OpenAI providers.

A passing result does not prove that credentials work or that external IP allowlists are correct.
After it passes, run `docker compose config --quiet`, start the stack, wait for
`/health/ready`, and complete the desktop validation checklist. Production credentials should be
in a deployment secret manager rather than a repository or image layer.

Repository documentation is checked separately with `python scripts/check_docs.py`. That check
validates relative Markdown links and compares documented current-head markers with the Alembic
revision graph, so a new migration must update the marked operational documents in the same change.
