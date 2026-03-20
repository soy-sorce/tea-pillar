FROM python:3.11-slim

COPY --from=ghcr.io/astral-sh/uv:0.5.29 /uv /usr/local/bin/uv

WORKDIR /app

COPY pyproject.toml /app/
RUN uv sync --no-dev --no-install-project

COPY src /app/src
COPY artifacts /app/artifacts

CMD ["/app/.venv/bin/uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8080"]
