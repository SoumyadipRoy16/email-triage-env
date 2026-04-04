FROM python:3.11-slim

# ── metadata ────────────────────────────────────────────────────────────────
LABEL maintainer="openenv-hackathon"
LABEL description="Email Triage OpenEnv Environment"
LABEL version="1.0.0"

# ── system deps ─────────────────────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

# ── working dir ─────────────────────────────────────────────────────────────
WORKDIR /app

# ── python deps (cached layer) ───────────────────────────────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ── application code ─────────────────────────────────────────────────────────
COPY server/ ./server/
COPY openenv.yaml .

# ── non-root user for security ───────────────────────────────────────────────
RUN useradd -m -u 1000 appuser \
    && chown -R appuser:appuser /app
USER appuser

# ── runtime config ───────────────────────────────────────────────────────────
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV HOST=0.0.0.0
ENV PORT=8000

EXPOSE 8000

# ── healthcheck ──────────────────────────────────────────────────────────────
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# ── entrypoint ───────────────────────────────────────────────────────────────
CMD ["uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8000", \
     "--workers", "1", "--log-level", "info"]