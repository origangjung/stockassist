FROM ghcr.io/astral-sh/uv:0.11.28 AS uv

FROM python:3.12-slim
WORKDIR /app
COPY --from=uv /uv /uvx /bin/
ENV PATH="/app/.venv/bin:$PATH" \
    UV_COMPILE_BYTECODE=0 \
    UV_LINK_MODE=copy
ARG INSTALL_ML=false
COPY pyproject.toml uv.lock README.md ./
COPY alembic.ini ./
RUN if [ "$INSTALL_ML" = "true" ]; then \
      uv sync --locked --no-dev --extra ml --no-install-project; \
    else \
      uv sync --locked --no-dev --no-install-project; \
    fi
COPY backend ./backend
RUN if [ "$INSTALL_ML" = "true" ]; then \
      uv sync --locked --no-dev --extra ml; \
    else \
      uv sync --locked --no-dev; \
    fi && \
    groupadd --system --gid 10001 stockpilot && \
    useradd --system --uid 10001 --gid stockpilot --home-dir /nonexistent stockpilot && \
    mkdir -p /app/artifacts/models && \
    chown -R stockpilot:stockpilot /app/artifacts
USER stockpilot
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--app-dir", "backend", "--host", "0.0.0.0", "--port", "8000"]
