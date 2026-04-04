"""
env.py
──────
Core environment state machine for the Email Triage OpenEnv environment.
Manages episode lifecycle: reset → step → step → ... → done.
"""

from __future__ import annotations
import random
import uuid
import logging
from typing import Optional, Dict, Any, List

from .models import (
    EmailTriageAction,
    EmailTriageObservation,
    StepResult,
    EnvState,
    TaskType,
    TaskDifficulty,
    ResetResponse,
)
from .email_corpus import EMAILS, get_email_by_id, Email
from .tasks import (
    TASK_IDS,
    TASK_REGISTRY,
    get_task,
    task_type_for_id,
    build_task_instructions,
)
from .graders import get_grader

logger = logging.getLogger(__name__)

# ── Task → max steps mapping ───────────────────────────────────────────────────
TASK_MAX_STEPS = {
    "task_classify": 1,
    "task_extract":  2,
    "task_reply":    3,
}


class EmailTriageEnv:
    """
    Stateful environment implementing the OpenEnv step() / reset() / state() contract.
    One instance is shared across the FastAPI process (single-session mode).
    """

    def __init__(self) -> None:
        self._episode_id: str = ""
        self._task_id: str = ""
        self._email: Optional[Email] = None
        self._step_number: int = 0
        self._max_steps: int = 1
        self._cumulative_reward: float = 0.0
        self._done: bool = True
        self._last_feedback: str = ""
        self._history: List[Dict[str, Any]] = []
        self._rng = random.Random()

    # ── Public API ─────────────────────────────────────────────────────────────

    def reset(
        self,
        task_id: Optional[str] = None,
        email_id: Optional[str] = None,
        seed: Optional[int] = None,
    ) -> ResetResponse:
        """
        Start a new episode.
        Returns the first observation and episode metadata.
        """
        if seed is not None:
            self._rng.seed(seed)

        # Choose task
        if task_id is None:
            task_id = self._rng.choice(TASK_IDS)
        if task_id not in TASK_REGISTRY:
            raise ValueError(f"Unknown task_id '{task_id}'. Valid IDs: {TASK_IDS}")

        # Choose email
        if email_id is not None:
            email = get_email_by_id(email_id)
            if email is None:
                raise ValueError(f"Unknown email_id '{email_id}'.")
        else:
            email = self._rng.choice(EMAILS)

        # Initialise episode state
        self._episode_id = str(uuid.uuid4())
        self._task_id = task_id
        self._email = email
        self._step_number = 0
        self._max_steps = TASK_MAX_STEPS[task_id]
        self._cumulative_reward = 0.0
        self._done = False
        self._last_feedback = ""
        self._history = []

        logger.info(
            "Episode %s started | task=%s | email=%s",
            self._episode_id, task_id, email.email_id,
        )

        obs = self._build_observation()
        return ResetResponse(
            observation=obs,
            episode_id=self._episode_id,
            task_id=self._task_id,
        )

    def step(self, action: EmailTriageAction) -> StepResult:
        """
        Execute one agent action and return the resulting StepResult.
        """
        if self._done:
            raise RuntimeError(
                "Episode is done. Call reset() to start a new episode."
            )
        if self._email is None:
            raise RuntimeError("Environment not initialised. Call reset() first.")

        self._step_number += 1

        # Grade the action
        grader = get_grader(self._task_id)
        reward, feedback = grader.grade(action, self._email)

        self._cumulative_reward += reward
        self._last_feedback = feedback

        # Record history
        self._history.append({
            "step": self._step_number,
            "action": action.model_dump(exclude_none=True),
            "reward": reward,
            "feedback": feedback,
        })

        # Determine done
        done = self._step_number >= self._max_steps
        self._done = done

        logger.info(
            "Episode %s | step=%d | reward=%.4f | done=%s",
            self._episode_id, self._step_number, reward, done,
        )

        obs = self._build_observation()
        return StepResult(
            observation=obs,
            reward=reward,
            done=done,
            info={
                "episode_id": self._episode_id,
                "step": self._step_number,
                "max_steps": self._max_steps,
                "cumulative_reward": round(self._cumulative_reward, 4),
                "task_id": self._task_id,
                "email_id": self._email.email_id,
                "grader_feedback": feedback,
            },
        )

    def state(self) -> EnvState:
        """Return the full internal state for debugging / monitoring."""
        if self._email is None:
            raise RuntimeError("Environment not initialised. Call reset() first.")

        task_def = get_task(self._task_id)
        difficulty_map = {
            "task_classify": TaskDifficulty.EASY,
            "task_extract":  TaskDifficulty.MEDIUM,
            "task_reply":    TaskDifficulty.HARD,
        }
        return EnvState(
            episode_id=self._episode_id,
            task_type=task_type_for_id(self._task_id),
            task_difficulty=difficulty_map[self._task_id],
            email_id=self._email.email_id,
            step_number=self._step_number,
            max_steps=self._max_steps,
            cumulative_reward=round(self._cumulative_reward, 4),
            done=self._done,
            history=self._history,
        )

    # ── Internal ───────────────────────────────────────────────────────────────

    def _build_observation(self) -> EmailTriageObservation:
        assert self._email is not None
        task_type = task_type_for_id(self._task_id)
        sender_str = f"{self._email.sender_name} ({self._email.sender_role})"
        instructions = build_task_instructions(
            task_id=self._task_id,
            sender=sender_str,
            subject=self._email.subject,
            step=self._step_number,
            feedback=self._last_feedback,
        )
        return EmailTriageObservation(
            email_id=self._email.email_id,
            email_subject=self._email.subject,
            email_body=self._email.body,
            email_sender=sender_str,
            task_type=task_type,
            task_instructions=instructions,
            feedback=self._last_feedback,
            score=round(self._cumulative_reward, 4),
            step_number=self._step_number,
            done=self._done,
        )