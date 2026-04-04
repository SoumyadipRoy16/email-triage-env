FROM python:3.11-slim

# ── metadata ────────────────────────────────────────────────────────────────
LABEL maintainer="openenv-hackathon"
LABEL description="Email Triage OpenEnv Environment"
LABEL version="1.0.0"

# ── system deps ─────────────────────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
    && rm -rf /var/lib/apt/lists/*

# ── working dir ─────────────────────────────────────────────────────────────
WORKDIR /app

# ── python deps ──────────────────────────────────────────────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ── application code ─────────────────────────────────────────────────────────
COPY server/ ./server/
COPY openenv.yaml .

# ── non-root user (HF Spaces runs as uid 1000) ───────────────────────────────
RUN useradd -m -u 1000 appuser \
    && chown -R appuser:appuser /app
USER appuser

# ── runtime config ───────────────────────────────────────────────────────────
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV HOST=0.0.0.0
# HF Spaces requires port 7860 — all external traffic is proxied through it
ENV PORT=7860

EXPOSE 7860

# ── healthcheck ──────────────────────────────────────────────────────────────
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:7860/health || exit 1

# ── entrypoint ───────────────────────────────────────────────────────────────
CMD ["uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "7860", \
     "--workers", "1", "--log-level", "info"]