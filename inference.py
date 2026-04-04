from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import sys
import time
from typing import Any, Dict, List, Optional

import httpx
from openai import OpenAI

# ── Configuration ─────────────────────────────────────────────────────────────

API_BASE_URL: str = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME:   str = os.getenv("MODEL_NAME",   "meta-llama/Llama-3.1-8B-Instruct:cerebras")
API_KEY:      str = os.getenv("HF_TOKEN",     "")
ENV_BASE_URL: str = os.getenv("ENV_BASE_URL", "https://soumyadiproy894-email-triage-env.hf.space")

TEMPERATURE:  float = float(os.getenv("TEMPERATURE", "0.2"))
MAX_TOKENS:   int   = int(os.getenv("MAX_TOKENS",    "2048"))
MAX_RETRIES:  int   = int(os.getenv("MAX_RETRIES",   "2"))

# One task per task_id — maps to max_steps from the environment spec
TASKS_CONFIG = [
    {"task_id": "task_classify", "max_steps": 1,  "max_total_reward": 1.0, "benchmark": "email-triage-easy"},
    {"task_id": "task_extract",  "max_steps": 2,  "max_total_reward": 2.0, "benchmark": "email-triage-medium"},
    {"task_id": "task_reply",    "max_steps": 3,  "max_total_reward": 3.0, "benchmark": "email-triage-hard"},
]

SUCCESS_SCORE_THRESHOLD = 0.60

# ── Logging (stderr only — stdout is reserved for structured logs) ─────────────
logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Structured stdout loggers (MANDATORY FORMAT — do not alter field names)
# ─────────────────────────────────────────────────────────────────────────────

def log_start(*, task: str, env: str, model: str) -> None:
    print(json.dumps({"type": "START", "task": task, "env": env, "model": model}), flush=True)


def log_step(
    *,
    step: int,
    action: str,
    reward: float,
    done: bool,
    error: Optional[str],
) -> None:
    print(
        json.dumps({
            "type":   "STEP",
            "step":   step,
            "action": action,
            "reward": reward,
            "done":   done,
            "error":  error,
        }),
        flush=True,
    )


def log_end(
    *,
    success: bool,
    steps: int,
    score: float,
    rewards: List[float],
) -> None:
    print(
        json.dumps({
            "type":    "END",
            "success": success,
            "steps":   steps,
            "score":   score,
            "rewards": rewards,
        }),
        flush=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Environment HTTP client
# ─────────────────────────────────────────────────────────────────────────────

class EnvClient:
    """Thin async HTTP client wrapping the Email Triage OpenEnv REST API."""

    def __init__(self, base_url: str, timeout: float = 60.0) -> None:
        self.base_url = base_url.rstrip("/")
        self._client  = httpx.AsyncClient(timeout=timeout)

    async def health(self) -> Dict[str, Any]:
        r = await self._client.get(f"{self.base_url}/health")
        r.raise_for_status()
        return r.json()

    async def reset(
        self,
        task_id: Optional[str] = None,
        email_id: Optional[str] = None,
        seed: Optional[int] = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {}
        if task_id:  payload["task_id"]  = task_id
        if email_id: payload["email_id"] = email_id
        if seed is not None: payload["seed"] = seed
        r = await self._client.post(f"{self.base_url}/reset", json=payload)
        r.raise_for_status()
        return r.json()

    async def step(self, action: Dict[str, Any]) -> Dict[str, Any]:
        r = await self._client.post(f"{self.base_url}/step", json=action)
        r.raise_for_status()
        return r.json()

    async def state(self) -> Dict[str, Any]:
        r = await self._client.get(f"{self.base_url}/state")
        r.raise_for_status()
        return r.json()

    async def close(self) -> None:
        await self._client.aclose()


# ─────────────────────────────────────────────────────────────────────────────
# LLM agent
# ─────────────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """\
You are an expert email triage agent. You receive business emails and must
analyse them carefully to complete the assigned task.

CRITICAL: Your response MUST be valid JSON matching the task requirements.
Do NOT include markdown fences (```json) — output raw JSON only.

For task_classify:
  {"category": "<value>", "urgency": "<value>"}

For task_extract:
  {"action_items": ["item 1", "item 2", ...], "summary": "..."}

For task_reply:
  {"reply": "Full professional email reply text here..."}

Think carefully before responding. Partial credit is available.\
"""


def build_user_prompt(obs: Dict[str, Any], history: List[str]) -> str:
    """Construct the user-facing prompt from the current observation."""
    parts = [
        f"=== EMAIL ===",
        f"From   : {obs['email_sender']}",
        f"Subject: {obs['email_subject']}",
        f"",
        obs["email_body"],
        f"",
        f"=== YOUR TASK ===",
        obs["task_instructions"],
    ]
    if obs.get("feedback"):
        parts += ["", f"=== PREVIOUS FEEDBACK ===", obs["feedback"]]
    if history:
        parts += ["", f"=== STEP HISTORY ==="] + history
    return "\n".join(parts)


def call_llm(
    client: OpenAI,
    obs: Dict[str, Any],
    history: List[str],
) -> str:
    """Call the LLM and return the raw response string. Retries on failure."""
    user_prompt = build_user_prompt(obs, history)
    last_error: Exception | None = None

    for attempt in range(1, MAX_RETRIES + 2):  # +2: attempts = retries + 1 initial
        try:
            completion = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user",   "content": user_prompt},
                ],
                temperature=TEMPERATURE,
                max_tokens=MAX_TOKENS,
                stream=False,
            )
            text = (completion.choices[0].message.content or "").strip()
            return text if text else "{}"
        except Exception as exc:
            last_error = exc
            logger.warning("[DEBUG] LLM attempt %d failed: %s", attempt, exc)
            if attempt <= MAX_RETRIES:
                time.sleep(2 ** attempt)  # exponential back-off

    logger.error("[DEBUG] All LLM attempts failed: %s", last_error)
    return "{}"


def parse_action(raw: str, task_id: str) -> Dict[str, Any]:
    """
    Parse the LLM raw output into an action dict.
    Handles: markdown fences, truncated JSON, escaped quotes,
    and extracts partial JSON using regex as a last resort.
    """
    cleaned = raw.strip()

    # Strip markdown fences
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        cleaned = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
    cleaned = cleaned.strip()

    # Attempt 1 — direct parse
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Attempt 2 — find the outermost { ... } block
    try:
        start = cleaned.index("{")
        depth, end = 0, start
        for i, ch in enumerate(cleaned[start:], start):
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    end = i
                    break
        return json.loads(cleaned[start:end + 1])
    except (ValueError, json.JSONDecodeError):
        pass

    # Attempt 3 — regex extract "reply" value for reply task
    if task_id == "task_reply":
        m = re.search(r'"reply"\s*:\s*"(.*?)(?<!\\)"(?:\s*[,}]|$)', cleaned, re.DOTALL)
        if m:
            reply_text = m.group(1).replace('\\"', '"').replace("\\'", "'")
            if len(reply_text) > 30:
                logger.info("[DEBUG] Extracted reply via regex (%d chars)", len(reply_text))
                return {"reply": reply_text}

    # Attempt 4 — if output looks like a letter, use it directly as reply
    if task_id == "task_reply":
        lower = cleaned.lower()
        if any(g in lower for g in ["dear ", "hello ", "hi ", "thank you"]) and len(cleaned) > 50:
            logger.info("[DEBUG] Using raw output as reply (%d chars)", len(cleaned))
            return {"reply": cleaned}

    logger.warning("[DEBUG] Failed to parse JSON from LLM: %r", cleaned[:300])
    fallbacks = {
        "task_classify": {"category": "general_inquiry", "urgency": "medium"},
        "task_extract":  {"action_items": [], "summary": "Could not extract."},
        "task_reply":    {"reply": "Thank you for your email. We will follow up shortly."},
    }
    return fallbacks.get(task_id, {})


# ─────────────────────────────────────────────────────────────────────────────
# Single task runner
# ─────────────────────────────────────────────────────────────────────────────

async def run_task(
    env: EnvClient,
    llm: OpenAI,
    task_config: Dict[str, Any],
    seed: int,
) -> Dict[str, Any]:
    """
    Run one complete episode for a given task.
    Returns a summary dict with score, rewards, steps, success.
    """
    task_id         = task_config["task_id"]
    max_steps       = task_config["max_steps"]
    max_total_reward = task_config["max_total_reward"]
    benchmark       = task_config["benchmark"]

    history: List[str] = []
    rewards: List[float] = []
    steps_taken = 0
    score = 0.0
    success = False

    log_start(task=task_id, env=benchmark, model=MODEL_NAME)
    logger.info("── Starting task: %s (seed=%d) ──", task_id, seed)

    try:
        # ── Reset ──────────────────────────────────────────────────────────────
        reset_data = await env.reset(task_id=task_id, seed=seed)
        obs = reset_data["observation"]
        logger.info("Episode %s | email=%s", reset_data["episode_id"], obs["email_id"])

        last_reward = 0.0

        for step in range(1, max_steps + 1):
            if obs.get("done", False):
                break

            # ── LLM call ──────────────────────────────────────────────────────
            raw_response = call_llm(llm, obs, history)
            action_dict  = parse_action(raw_response, task_id)

            logger.info("Step %d | action_preview=%r", step, str(action_dict)[:120])

            # ── Env step ──────────────────────────────────────────────────────
            try:
                step_result = await env.step(action_dict)
            except Exception as exc:
                logger.error("Step %d env error: %s", step, exc)
                log_step(step=step, action=str(action_dict), reward=0.0, done=True, error=str(exc))
                break

            reward = float(step_result.get("reward", 0.0))
            done   = bool(step_result.get("done", False))
            obs    = step_result.get("observation", obs)
            error  = None

            rewards.append(reward)
            steps_taken  = step
            last_reward  = reward

            log_step(
                step=step,
                action=json.dumps(action_dict, ensure_ascii=False),
                reward=reward,
                done=done,
                error=error,
            )

            history.append(
                f"Step {step}: action={json.dumps(action_dict)[:80]} → reward={reward:+.4f}"
            )

            if done:
                break

        # ── Score ──────────────────────────────────────────────────────────────
        # For multi-step tasks, use the BEST step reward as the score.
        # This rewards improvement and prevents a bad final step from
        # dragging down an earlier excellent attempt.
        if rewards:
            score = max(rewards)
        else:
            score = sum(rewards) / max_total_reward if max_total_reward > 0 else 0.0
        score   = min(max(score, 0.0), 1.0)
        success = score >= SUCCESS_SCORE_THRESHOLD

    except Exception as exc:
        logger.exception("Fatal error in task %s: %s", task_id, exc)

    log_end(success=success, steps=steps_taken, score=score, rewards=rewards)
    logger.info(
        "── Finished task: %s | score=%.4f | success=%s ──",
        task_id, score, success,
    )

    return {
        "task_id": task_id,
        "score":   score,
        "rewards": rewards,
        "steps":   steps_taken,
        "success": success,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Main entry point
# ─────────────────────────────────────────────────────────────────────────────

async def main() -> None:
    logger.info("=" * 60)
    logger.info("Email Triage OpenEnv — Baseline Inference Script")
    logger.info("Model      : %s", MODEL_NAME)
    logger.info("API Base   : %s", API_BASE_URL)
    logger.info("Env URL    : %s", ENV_BASE_URL)
    logger.info("=" * 60)

    # Validate required config
    if not API_KEY:
        logger.error("HF_TOKEN environment variable is not set.")
        sys.exit(1)

    # Initialise clients
    llm = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)
    env = EnvClient(base_url=ENV_BASE_URL)

    # Health check
    try:
        health = await env.health()
        logger.info("Environment health: %s", health)
    except Exception as exc:
        logger.error("Cannot reach environment at %s: %s", ENV_BASE_URL, exc)
        logger.error("Ensure the server is running: uvicorn server.main:app --port 8000")
        sys.exit(1)

    # Run all three tasks in sequence
    all_results = []
    base_seed = 42

    for idx, task_config in enumerate(TASKS_CONFIG):
        seed = base_seed + idx
        result = await run_task(env, llm, task_config, seed=seed)
        all_results.append(result)
        logger.info("")

    # Final summary
    await env.close()

    overall_score = sum(r["score"] for r in all_results) / len(all_results)
    overall_success = all(r["success"] for r in all_results)

    logger.info("=" * 60)
    logger.info("FINAL RESULTS")
    logger.info("=" * 60)
    for r in all_results:
        status = "✓ PASS" if r["success"] else "✗ FAIL"
        logger.info(
            "  %-20s | score=%.4f | steps=%d | %s",
            r["task_id"], r["score"], r["steps"], status,
        )
    logger.info("-" * 60)
    logger.info(
        "  %-20s | score=%.4f | %s",
        "OVERALL",
        overall_score,
        "✓ PASS" if overall_success else "✗ FAIL",
    )
    logger.info("=" * 60)

    sys.exit(0 if overall_success else 1)


if __name__ == "__main__":
    asyncio.run(main())