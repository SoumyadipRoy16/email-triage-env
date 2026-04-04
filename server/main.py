"""
main.py
───────
FastAPI application implementing the OpenEnv HTTP API for the
Email Triage environment.

Endpoints:
  POST /reset   — Start a new episode
  POST /step    — Submit an action, receive StepResult
  GET  /state   — Inspect current environment state
  GET  /health  — Health check (200 OK)
  GET  /tasks   — List all tasks with metadata
  GET  /        — Root info endpoint
"""

from __future__ import annotations
import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from .models import (
    EmailTriageAction,
    ResetRequest,
    ResetResponse,
    StepResult,
    EnvState,
    HealthResponse,
    TasksResponse,
)
from .env import EmailTriageEnv
from .tasks import TASK_REGISTRY, TaskDefinition

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── Lifespan (startup / shutdown) ─────────────────────────────────────────────
_env: EmailTriageEnv | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _env
    logger.info("Initialising Email Triage environment...")
    _env = EmailTriageEnv()
    logger.info("Environment ready. Awaiting requests.")
    yield
    logger.info("Shutting down Email Triage environment.")


# ── FastAPI application ───────────────────────────────────────────────────────
app = FastAPI(
    title="Email Triage OpenEnv",
    description=(
        "A real-world OpenEnv environment for AI agents to learn email triage, "
        "action-item extraction, and professional reply drafting. "
        "Implements the full OpenEnv step() / reset() / state() API contract."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — allow all origins (needed for HF Spaces iframe / external clients)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request timing middleware ─────────────────────────────────────────────────
@app.middleware("http")
async def add_process_time(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed = time.perf_counter() - start
    response.headers["X-Process-Time"] = f"{elapsed:.4f}s"
    return response


# ── Helpers ───────────────────────────────────────────────────────────────────
def _get_env() -> EmailTriageEnv:
    if _env is None:
        raise HTTPException(status_code=503, detail="Environment not initialised.")
    return _env


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/", tags=["info"])
async def root():
    """Root info endpoint — confirms the server is alive."""
    return {
        "name": "email-triage-env",
        "version": "1.0.0",
        "description": "Email Triage OpenEnv environment",
        "endpoints": {
            "reset":  "POST /reset",
            "step":   "POST /step",
            "state":  "GET  /state",
            "health": "GET  /health",
            "tasks":  "GET  /tasks",
            "docs":   "GET  /docs",
        },
    }


@app.get("/health", response_model=HealthResponse, tags=["info"])
async def health():
    """Health check — returns 200 and status 'ok'."""
    return HealthResponse()


@app.get("/tasks", response_model=TasksResponse, tags=["info"])
async def list_tasks():
    """Enumerate all available tasks with metadata."""
    return TasksResponse(tasks=list(TASK_REGISTRY.values()))


@app.post("/reset", response_model=ResetResponse, tags=["openenv"])
async def reset(request: ResetRequest = ResetRequest()):
    """
    Start a new episode.

    - **task_id**: Optional. Pin to a specific task (`task_classify`, `task_extract`, `task_reply`).
    - **email_id**: Optional. Pin to a specific email ID (`e001`–`e008`).
    - **seed**: Optional integer seed for reproducibility.

    Returns the first observation and episode metadata.
    """
    env = _get_env()
    try:
        response = env.reset(
            task_id=request.task_id,
            email_id=request.email_id,
            seed=request.seed,
        )
        logger.info("POST /reset → episode_id=%s task=%s", response.episode_id, response.task_id)
        return response
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.exception("Unexpected error in /reset")
        raise HTTPException(status_code=500, detail=f"Internal error: {exc}")


@app.post("/step", response_model=StepResult, tags=["openenv"])
async def step(action: EmailTriageAction):
    """
    Submit an agent action and receive a StepResult.

    Fill only the fields relevant to the current task:
    - **category** + **urgency** for `task_classify`
    - **action_items** + **summary** for `task_extract`
    - **reply** for `task_reply`

    Returns reward (0.0–1.0), done flag, grader feedback, and next observation.
    """
    env = _get_env()
    try:
        result = env.step(action)
        logger.info(
            "POST /step → reward=%.4f done=%s",
            result.reward, result.done,
        )
        return result
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except Exception as exc:
        logger.exception("Unexpected error in /step")
        raise HTTPException(status_code=500, detail=f"Internal error: {exc}")


@app.get("/state", response_model=EnvState, tags=["openenv"])
async def state():
    """
    Return the full internal environment state.
    Useful for debugging, logging, and monitoring agent progress.
    """
    env = _get_env()
    try:
        return env.state()
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except Exception as exc:
        logger.exception("Unexpected error in /state")
        raise HTTPException(status_code=500, detail=f"Internal error: {exc}")


# ── Error handlers ────────────────────────────────────────────────────────────

@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={"detail": f"Endpoint '{request.url.path}' not found."},
    )


@app.exception_handler(405)
async def method_not_allowed_handler(request: Request, exc):
    return JSONResponse(
        status_code=405,
        content={"detail": f"Method '{request.method}' not allowed on '{request.url.path}'."},
    )