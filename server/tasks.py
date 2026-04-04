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
        f"You have received an email from {sender} with the subject: '{subject}'.\n\n"
        "YOUR TASK — CLASSIFY THE EMAIL:\n"
        "  1. Predict the CATEGORY from one of:\n"
        "     billing | technical_support | sales_inquiry | hr_policy |\n"
        "     legal | general_inquiry | complaint | partnership\n\n"
        "  2. Predict the URGENCY LEVEL from one of:\n"
        "     critical | high | medium | low\n\n"
        "RESPOND with a JSON action containing exactly:\n"
        '  { "category": "<value>", "urgency": "<value>" }\n\n'
        "SCORING: +0.5 for correct category, +0.5 for correct urgency.\n"
        "Partial credit is awarded — get one right for 0.5."
    )


def extract_instructions(sender: str, subject: str, step: int, feedback: str) -> str:
    base = (
        f"You have received an email from {sender} with the subject: '{subject}'.\n\n"
        "YOUR TASK — EXTRACT ACTION ITEMS AND SUMMARIZE:\n"
        "  1. List every discrete ACTION ITEM the recipient must act on.\n"
        "     Be specific — each item should be a single, clear task.\n"
        "  2. Write a concise SUMMARY (2–4 sentences) capturing the core request.\n\n"
        "RESPOND with a JSON action containing:\n"
        '  { "action_items": ["item 1", "item 2", ...], "summary": "..." }\n\n'
        "SCORING: Based on precision + recall of action items vs. ground truth.\n"
        "  Precision = fraction of your items that are correct.\n"
        "  Recall    = fraction of ground-truth items you captured.\n"
        "  Final reward = 0.4 × precision + 0.4 × recall + 0.2 × summary quality."
    )
    if step > 1 and feedback:
        base += f"\n\nFEEDBACK FROM PREVIOUS ATTEMPT:\n{feedback}\nUse this to improve your answer."
    return base


def reply_instructions(sender: str, subject: str, step: int, feedback: str) -> str:
    base = (
        f"You have received an email from {sender} with the subject: '{subject}'.\n\n"
        "YOUR TASK — DRAFT A PROFESSIONAL REPLY:\n"
        "  Write a complete, professional email reply that:\n"
        "  • Addresses EVERY point or question raised in the email\n"
        "  • Uses an appropriate professional tone for the context\n"
        "  • Includes a greeting, body paragraphs, and a sign-off\n"
        "  • Is clear, concise, and actionable\n\n"
        "RESPOND with a JSON action containing:\n"
        '  { "reply": "Your full email reply text here..." }\n\n'
        "SCORING by LLM judge (0.0–1.0):\n"
        "  • Tone & appropriateness      (0–30 pts)\n"
        "  • Completeness (addresses all points) (0–40 pts)\n"
        "  • Professionalism & clarity   (0–30 pts)"
    )
    if step > 1 and feedback:
        base += f"\n\nFEEDBACK FROM PREVIOUS ATTEMPT:\n{feedback}\nRevise your reply accordingly."
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