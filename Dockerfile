# Dockerfile
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy PYTHONUNBUFFERED=1

# Dependencias primero: capa cacheable, cambia poco
COPY pyproject.toml uv.lock* ./
RUN uv sync --frozen --no-install-project --no-dev || uv sync --no-install-project --no-dev

COPY src/ ./src/
COPY semantic/ ./semantic/
COPY prompts/ ./prompts/
COPY client/ ./client/
COPY migrations/ ./migrations/
COPY alembic.ini ./
RUN uv sync --no-dev

EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import httpx,sys; sys.exit(0 if httpx.get('http://localhost:8000/salud').status_code==200 else 1)"

CMD ["uv", "run", "uvicorn", "querypilot.service_boundary.app:app", "--host", "0.0.0.0", "--port", "8000"]
