# syntax=docker/dockerfile:1

FROM python:3.12-slim AS builder
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /build
COPY pyproject.toml README.md /build/
RUN pip install --no-cache-dir -U pip setuptools wheel
COPY src/ /build/src/
RUN pip wheel --no-cache-dir --wheel-dir /wheels .

FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
# add non-root user
RUN useradd -u 10001 -m appuser
WORKDIR /app
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/*
COPY src/ /app/src/
COPY README.md /app/README.md
ENV APP_HOST=0.0.0.0 APP_PORT=8000
EXPOSE 8000
USER appuser
CMD ["uvicorn", "soc_agent.webapp:app", "--host", "0.0.0.0", "--port", "8000"]
