FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/backend:/app/workers

COPY backend/pyproject.toml /app/backend/pyproject.toml
COPY workers/pyproject.toml /app/workers/pyproject.toml

RUN pip install --no-cache-dir uv \
    && uv pip install --system \
      "fastapi>=0.115.0" \
      "pika>=1.3.2" \
      "pydantic-settings>=2.6.0"

COPY backend /app/backend
COPY workers /app/workers

WORKDIR /app/workers
