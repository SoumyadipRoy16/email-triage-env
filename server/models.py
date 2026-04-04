from __future__ import annotations
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


# ── Enums ────────────────────────────────────────────────────────────────────

class TaskType(str, Enum):
    CLASSIFY = "classify"
    EXTRACT  = "extract"
    REPLY    = "reply"


class EmailCategory(str, Enum):
    BILLING           = "billing"
    TECHNICAL_SUPPORT = "technical_support"
    SALES_INQUIRY     = "sales_inquiry"
    HR_POLICY         = "hr_policy"
    LEGAL             = "legal"
    GENERAL_INQUIRY   = "general_inquiry"
    COMPLAINT         = "complaint"
    PARTNERSHIP       = "partnership"


class UrgencyLevel(str, Enum):
    CRITICAL = "critical"
    HIGH     = "high"
    MEDIUM   = "medium"
    LOW      = "low"


class TaskDifficulty(str, Enum):
    EASY   = "easy"
    MEDIUM = "medium"
    HARD   = "hard"


# ── Action ───────────────────────────────────────────────────────────────────

class EmailTriageAction(BaseModel):
    """
    The action the agent submits for a given step.
    Fill only the fields relevant to the current task_type.
    """

    # Task 1 – Classification
    category: Optional[EmailCategory] = Field(
        default=None,
        description="[task=classify] Predicted email category",
    )
    urgency: Optional[UrgencyLevel] = Field(
        default=None,
        description="[task=classify] Predicted urgency level",
    )

    # Task 2 – Extraction
    action_items: Optional[List[str]] = Field(
        default=None,
        description="[task=extract] Discrete action items extracted from the email",
        min_length=0,
    )
    summary: Optional[str] = Field(
        default=None,
        description="[task=extract] Brief summary of the email",
    )

    # Task 3 – Reply
    reply: Optional[str] = Field(
        default=None,
        description="[task=reply] Full text of the professional reply email",
    )

    class Config:
        use_enum_values = True
        extra = "ignore"


# ── Observation ──────────────────────────────────────────────────────────────

class EmailTriageObservation(BaseModel):
    """
    The observation returned to the agent after reset() or step().
    """
    email_id: str = Field(description="Unique identifier for the current email")
    email_subject: str = Field(description="Subject line of the email")
    email_body: str = Field(description="Full body text of the email")
    email_sender: str = Field(description="Sender display string: 'Name (Role)'")
    task_type: TaskType = Field(description="Which task the agent must perform")
    task_instructions: str = Field(description="Detailed natural-language instructions for the task")
    feedback: str = Field(default="", description="Grader feedback from the last step")
    score: float = Field(default=0.0, description="Cumulative score for this episode")
    step_number: int = Field(default=0, description="Current step index")
    done: bool = Field(default=False, description="Whether the episode is complete")

    class Config:
        use_enum_values = True


# ── Step Result ───────────────────────────────────────────────────────────────

class StepResult(BaseModel):
    """
    Return value of step().
    """
    observation: EmailTriageObservation
    reward: float = Field(description="Reward earned in this step, in [0.0, 1.0]")
    done: bool = Field(description="Whether the episode is complete")
    info: Dict[str, Any] = Field(default_factory=dict, description="Diagnostic metadata")


# ── State ─────────────────────────────────────────────────────────────────────

class EnvState(BaseModel):
    """
    Full internal state of the environment, returned by state().
    """
    episode_id: str
    task_type: TaskType
    task_difficulty: TaskDifficulty
    email_id: str
    step_number: int
    max_steps: int
    cumulative_reward: float
    done: bool
    history: List[Dict[str, Any]] = Field(default_factory=list)

    class Config:
        use_enum_values = True


# ── Task Definition ───────────────────────────────────────────────────────────

class TaskDefinition(BaseModel):
    task_id: str
    name: str
    difficulty: TaskDifficulty
    description: str
    max_steps: int
    reward_range: List[float] = [0.0, 1.0]

    class Config:
        use_enum_values = True


# ── Reset Request / Response ──────────────────────────────────────────────────

class ResetRequest(BaseModel):
    task_id: Optional[str] = Field(
        default=None,
        description="Optional task ID to run. If omitted, a random task is chosen.",
    )
    email_id: Optional[str] = Field(
        default=None,
        description="Optional email ID to use. If omitted, an email is chosen automatically.",
    )
    seed: Optional[int] = Field(
        default=None,
        description="Optional random seed for reproducibility.",
    )


class ResetResponse(BaseModel):
    observation: EmailTriageObservation
    episode_id: str
    task_id: str


# ── Health ────────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "1.0.0"
    environment: str = "email-triage-env"


# ── Tasks List ────────────────────────────────────────────────────────────────

class TasksResponse(BaseModel):
    tasks: List[TaskDefinition]