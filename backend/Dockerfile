FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/backend

COPY backend/pyproject.toml /app/backend/pyproject.toml

RUN pip install --no-cache-dir uv \
    && uv pip install --system \
      "fastapi>=0.115.0" \
      "pika>=1.3.2" \
      "pydantic-settings>=2.6.0" \
      "uvicorn[standard]>=0.32.0"

COPY backend /app/backend

WORKDIR /app/backend

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
