from __future__ import annotations
import logging
import time
import uuid
from contextlib import asynccontextmanager
from typing import Dict

from fastapi import FastAPI, HTTPException, Header, Request
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
from .tasks import TASK_REGISTRY

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── Session store — one EmailTriageEnv instance per session ID ────────────────
_sessions: Dict[str, EmailTriageEnv] = {}
_DEFAULT_SESSION = "default"
_MAX_SESSIONS = 256   # cap to avoid unbounded memory growth


def _get_session(session_id: str) -> EmailTriageEnv:
    """Return existing session env or create a new one."""
    if session_id not in _sessions:
        if len(_sessions) >= _MAX_SESSIONS:
            # Evict oldest session (FIFO)
            oldest = next(iter(_sessions))
            del _sessions[oldest]
            logger.info("Session evicted (max reached): %s", oldest)
        _sessions[session_id] = EmailTriageEnv()
        logger.info("Session created: %s (total active: %d)", session_id, len(_sessions))
    return _sessions[session_id]


# ── Lifespan ──────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Email Triage environment starting up...")
    _get_session(_DEFAULT_SESSION)   # pre-warm default session
    logger.info("Environment ready. Awaiting requests.")
    yield
    logger.info("Shutting down. Active sessions: %d", len(_sessions))
    _sessions.clear()


# ── FastAPI app ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="Email Triage OpenEnv",
    description=(
        "A real-world OpenEnv environment for AI agents to learn email triage, "
        "action-item extraction, and professional reply drafting.\n\n"
        "**Session isolation:** Pass `X-Session-ID: <your-id>` header to maintain "
        "independent episode state across concurrent callers."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_process_time(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    response.headers["X-Process-Time"] = f"{time.perf_counter() - start:.4f}s"
    return response


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/", tags=["info"])
async def root():
    return {
        "name": "email-triage-env",
        "version": "1.0.0",
        "description": "Email Triage OpenEnv — 24-email corpus, 3 tasks, deterministic graders",
        "session_isolation": "Pass X-Session-ID header for independent concurrent sessions",
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
    return HealthResponse()


@app.get("/tasks", response_model=TasksResponse, tags=["info"])
async def list_tasks():
    return TasksResponse(tasks=list(TASK_REGISTRY.values()))


@app.get("/sessions", tags=["info"])
async def list_sessions():
    """Return count of active sessions (diagnostic endpoint)."""
    return {"active_sessions": len(_sessions), "max_sessions": _MAX_SESSIONS}


@app.post("/reset", response_model=ResetResponse, tags=["openenv"])
async def reset(
    request: ResetRequest = ResetRequest(),
    x_session_id: str = Header(default=_DEFAULT_SESSION, alias="X-Session-ID"),
):
    """
    Start a new episode.

    - **X-Session-ID** header: optional session identifier for isolation.
      Multiple callers can run concurrent episodes by providing different IDs.
    - **task_id**: pin to a specific task (`task_classify`, `task_extract`, `task_reply`).
    - **email_id**: pin to a specific email (`e001`–`e009c`).
    - **seed**: integer seed for reproducibility.
    """
    env = _get_session(x_session_id)
    try:
        response = env.reset(
            task_id=request.task_id,
            email_id=request.email_id,
            seed=request.seed,
        )
        logger.info(
            "POST /reset [session=%s] → episode=%s task=%s",
            x_session_id, response.episode_id[:8], response.task_id,
        )
        return response
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.exception("Error in /reset")
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/step", response_model=StepResult, tags=["openenv"])
async def step(
    action: EmailTriageAction,
    x_session_id: str = Header(default=_DEFAULT_SESSION, alias="X-Session-ID"),
):
    """
    Submit an agent action and receive a StepResult.

    Provide the same **X-Session-ID** used in your `/reset` call.
    """
    env = _get_session(x_session_id)
    try:
        result = env.step(action)
        logger.info(
            "POST /step [session=%s] → reward=%.4f done=%s",
            x_session_id, result.reward, result.done,
        )
        return result
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except Exception as exc:
        logger.exception("Error in /step")
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/state", response_model=EnvState, tags=["openenv"])
async def state(
    x_session_id: str = Header(default=_DEFAULT_SESSION, alias="X-Session-ID"),
):
    """Return full internal environment state for the given session."""
    env = _get_session(x_session_id)
    try:
        return env.state()
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except Exception as exc:
        logger.exception("Error in /state")
        raise HTTPException(status_code=500, detail=str(exc))


# ── Error handlers ────────────────────────────────────────────────────────────

@app.exception_handler(404)
async def not_found(request: Request, exc):
    return JSONResponse(status_code=404, content={"detail": f"Endpoint '{request.url.path}' not found."})


@app.exception_handler(405)
async def method_not_allowed(request: Request, exc):
    return JSONResponse(status_code=405, content={"detail": f"Method '{request.method}' not allowed."})