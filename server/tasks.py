from __future__ import annotations
from typing import Dict
from .models import TaskDefinition, TaskDifficulty, TaskType


# ── Task Registry ─────────────────────────────────────────────────────────────

TASK_REGISTRY: Dict[str, TaskDefinition] = {
    "task_classify": TaskDefinition(
        task_id="task_classify",
        name="Email Classification",
        difficulty=TaskDifficulty.EASY,
        description=(
            "Given a business email, predict its category and urgency level. "
            "Partial credit is awarded for getting either field correct."
        ),
        max_steps=1,
        reward_range=[0.0, 1.0],
    ),
    "task_extract": TaskDefinition(
        task_id="task_extract",
        name="Action Item Extraction",
        difficulty=TaskDifficulty.MEDIUM,
        description=(
            "Given a business email, extract all discrete action items and "
            "produce a brief summary. Scored on precision and recall of items."
        ),
        max_steps=2,
        reward_range=[0.0, 1.0],
    ),
    "task_reply": TaskDefinition(
        task_id="task_reply",
        name="Professional Email Reply",
        difficulty=TaskDifficulty.HARD,
        description=(
            "Given a business email, draft a complete, professional reply that "
            "addresses every point raised. Graded on tone, completeness, and "
            "professionalism by an LLM judge."
        ),
        max_steps=3,
        reward_range=[0.0, 1.0],
    ),
}

TASK_IDS = list(TASK_REGISTRY.keys())


def get_task(task_id: str) -> TaskDefinition:
    if task_id not in TASK_REGISTRY:
        raise ValueError(f"Unknown task_id '{task_id}'. Valid: {TASK_IDS}")
    return TASK_REGISTRY[task_id]


def task_type_for_id(task_id: str) -> TaskType:
    mapping = {
        "task_classify": TaskType.CLASSIFY,
        "task_extract":  TaskType.EXTRACT,
        "task_reply":    TaskType.REPLY,
    }
    return mapping[task_id]


# ── Instruction Generators ────────────────────────────────────────────────────

def classify_instructions(sender: str, subject: str) -> str:
    return (
        f"Incoming Message: '{subject}' from {sender}.\n\n"
        "OBJECTIVE — MULTI-DIMENSIONAL CLASSIFICATION:\n"
        "  1. CATEGORY: Map to the most specific business unit:\n"
        "     billing | technical_support | sales_inquiry | hr_policy |\n"
        "     legal | compliance | general_inquiry | complaint | partnership\n\n"
        "  2. URGENCY: Assess priority (critical | high | medium | low).\n\n"
        "CONSTRAINTS:\n"
        "  • 'compliance' is for regulatory/GDPR/data-privacy requests.\n"
        "  • 'legal' is for contracts, litigation, and formal disputes.\n\n"
        "RESPONSE FORMAT:\n"
        '  { "category": "<value>", "urgency": "<value>" }\n\n'
        "SCORING RIGOR: Full credit requires precision on both axes (0.5 pts each)."
    )


def extract_instructions(sender: str, subject: str, step: int, feedback: str) -> str:
    base = (
        f"Message Analysis Request: Subject '{subject}' via {sender}.\n\n"
        "OBJECTIVE — ACTIONABLE INTELLIGENCE EXTRACTION:\n"
        "  1. DISCRETE ACTION ITEMS: Identify atomic, non-redundant tasks.\n"
        "     Avoid vague descriptions; use imperative verbs (e.g., 'Update internal log').\n"
        "  2. EXECUTIVE SUMMARY: A rigorous 2–4 sentence synthesis.\n\n"
        "EVALUATION CRITERIA (Enterprise Grade):\n"
        "  • RECALL (40%): Did you miss any hidden requests or deadlines?\n"
        "  • PRECISION (40%): Are your items actually requests, or just summary facts?\n"
        "  • COHERENCE (20%): Is the summary logically sound and professional?\n\n"
        "RESPONSE FORMAT:\n"
        '  { "action_items": ["item 1", "item 2", ...], "summary": "..." }'
    )
    if step > 1 and feedback:
        base += f"\n\nCRITICAL FEEDBACK FOR REMEDIATION (Step {step}/2):\n{feedback}\nFailure to address feedback will result in score decay."
    return base


def reply_instructions(sender: str, subject: str, step: int, feedback: str) -> str:
    base = (
        f"Drafting Directive: Formal Response to {sender} regarding '{subject}'.\n\n"
        "OBJECTIVE — HIGH-FIDELITY PROFESSIONAL CORRESPONDENCE:\n"
        "  Draft a response that demonstrates high emotional intelligence and business logic.\n\n"
        "MANDATORY RUBRIC:\n"
        "  • FULL COVERAGE (40%): Cross-reference every entity, date, and question.\n"
        "  • READABILITY (15%): Use clear paragraph breaks and varied sentence structure.\n"
        "  • POLITENESS (20%): Use professional hedging and appreciation signals.\n"
        "  • TONE (15%): Strictly avoid 'lol', 'tbh', 'fyi', or colloquialisms.\n"
        "  • STRUCTURAL INTEGRITY (10%): Formal greeting and professional sign-off.\n\n"
        "PROHIBITED: Do NOT 'hallucinate' names (e.g., signing as 'Alice' if not in context).\n\n"
        "RESPONSE FORMAT:\n"
        '  { "reply": "Your full professional response here..." }'
    )
    if step > 1 and feedback:
        base += f"\n\nQUALITY REMEDIATION TASK (Step {step}/3):\n{feedback}\nAddress the identified deficiencies to restore reward potential."
    return base


def build_task_instructions(
    task_id: str,
    sender: str,
    subject: str,
    step: int = 1,
    feedback: str = "",
) -> str:
    if task_id == "task_classify":
        return classify_instructions(sender, subject)
    elif task_id == "task_extract":
        return extract_instructions(sender, subject, step, feedback)
    elif task_id == "task_reply":
        return reply_instructions(sender, subject, step, feedback)
    raise ValueError(f"Unknown task_id: {task_id}")