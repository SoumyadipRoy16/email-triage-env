"""
graders.py
──────────
Agent graders for the Email Triage OpenEnv environment.

Each grader:
  • Accepts an action and the ground-truth email
  • Returns a reward in [0.0, 1.0] and human-readable feedback
  • Provides meaningful partial-progress signals
"""

from __future__ import annotations
import os
import re
import json
import logging
from typing import Tuple, List

from openai import OpenAI

from .models import EmailTriageAction, EmailCategory, UrgencyLevel
from .email_corpus import Email

logger = logging.getLogger(__name__)

# ── LLM client (used by ReplyGrader) ─────────────────────────────────────────

def _get_llm_client() -> OpenAI:
    return OpenAI(
        base_url=os.getenv("API_BASE_URL", "https://api.anthropic.com/v1"),
        api_key=os.getenv("HF_TOKEN", ""),
    )

MODEL_NAME = os.getenv("MODEL_NAME", "claude-sonnet-4-20250514")


# ── Utility ───────────────────────────────────────────────────────────────────

def _normalize(text: str) -> str:
    """Lower-case, strip punctuation, collapse whitespace."""
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _token_overlap(a: str, b: str) -> float:
    """Jaccard token overlap between two strings, in [0, 1]."""
    sa = set(_normalize(a).split())
    sb = set(_normalize(b).split())
    if not sa and not sb:
        return 1.0
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def _best_match(candidate: str, references: List[str], threshold: float = 0.30) -> bool:
    """Return True if candidate matches any reference above the token-overlap threshold."""
    return any(_token_overlap(candidate, ref) >= threshold for ref in references)


# ── Grader 1 — Classification ─────────────────────────────────────────────────

class ClassificationGrader:
    """
    Easy task grader.
    Scores:
      +0.50 for correct category
      +0.50 for correct urgency
    Total: 0.0 – 1.0
    """

    CATEGORY_REWARD = 0.50
    URGENCY_REWARD  = 0.50

    def grade(self, action: EmailTriageAction, email: Email) -> Tuple[float, str]:
        reward = 0.0
        feedback_parts: List[str] = []

        # ── Category ──────────────────────────────────────────────────────────
        if action.category is None:
            feedback_parts.append("✗ No category provided (expected one of the valid enum values).")
        elif action.category == email.true_category:
            reward += self.CATEGORY_REWARD
            feedback_parts.append(f"✓ Category '{action.category}' is correct. (+{self.CATEGORY_REWARD})")
        else:
            feedback_parts.append(
                f"✗ Category '{action.category}' is incorrect. "
                f"Expected: '{email.true_category}'. (+0.0)"
            )

        # ── Urgency ───────────────────────────────────────────────────────────
        if action.urgency is None:
            feedback_parts.append("✗ No urgency provided (expected: critical | high | medium | low).")
        elif action.urgency == email.true_urgency:
            reward += self.URGENCY_REWARD
            feedback_parts.append(f"✓ Urgency '{action.urgency}' is correct. (+{self.URGENCY_REWARD})")
        else:
            # Partial credit for adjacent urgency levels
            adjacency_bonus = self._urgency_partial(action.urgency, email.true_urgency)
            reward += adjacency_bonus
            feedback_parts.append(
                f"✗ Urgency '{action.urgency}' is incorrect. "
                f"Expected: '{email.true_urgency}'. "
                f"(+{adjacency_bonus:.2f} partial credit for adjacent level)"
            )

        feedback = "\n".join(feedback_parts)
        reward = round(min(max(reward, 0.0), 1.0), 4)
        return reward, feedback

    @staticmethod
    def _urgency_partial(predicted: str, true: str) -> float:
        """Award 0.15 for being one level off, 0.0 for two+ levels off."""
        order = ["low", "medium", "high", "critical"]
        try:
            pi = order.index(predicted)
            ti = order.index(true)
            diff = abs(pi - ti)
            if diff == 1:
                return 0.15
        except ValueError:
            pass
        return 0.0


# ── Grader 2 — Extraction ─────────────────────────────────────────────────────

class ExtractionGrader:
    """
    Medium task grader.
    Scores:
      Precision  = fraction of predicted items that match a ground-truth item (0.40 weight)
      Recall     = fraction of ground-truth items matched by a prediction   (0.40 weight)
      Summary    = token-overlap quality of the summary                     (0.20 weight)
    Total: 0.0 – 1.0
    """

    PRECISION_WEIGHT = 0.40
    RECALL_WEIGHT    = 0.40
    SUMMARY_WEIGHT   = 0.20
    MATCH_THRESHOLD  = 0.28  # Jaccard threshold for item match

    def grade(self, action: EmailTriageAction, email: Email) -> Tuple[float, str]:
        feedback_parts: List[str] = []
        reward = 0.0

        # ── Action Items ──────────────────────────────────────────────────────
        predicted = action.action_items or []
        ground_truth = email.true_action_items

        if not predicted:
            feedback_parts.append("✗ No action_items provided.")
            precision = 0.0
            recall = 0.0
        else:
            # Precision: how many predicted items match a ground-truth item?
            tp_pred = sum(
                1 for p in predicted
                if _best_match(p, ground_truth, self.MATCH_THRESHOLD)
            )
            precision = tp_pred / len(predicted) if predicted else 0.0

            # Recall: how many ground-truth items were captured?
            tp_recall = sum(
                1 for g in ground_truth
                if _best_match(g, predicted, self.MATCH_THRESHOLD)
            )
            recall = tp_recall / len(ground_truth) if ground_truth else 0.0

            reward += self.PRECISION_WEIGHT * precision
            reward += self.RECALL_WEIGHT    * recall

            feedback_parts.append(
                f"Action Items — Precision: {precision:.0%} ({tp_pred}/{len(predicted)} predicted items matched). "
                f"Recall: {recall:.0%} ({tp_recall}/{len(ground_truth)} ground-truth items captured)."
            )
            if recall < 0.5:
                missed = [g for g in ground_truth if not _best_match(g, predicted, self.MATCH_THRESHOLD)]
                feedback_parts.append(
                    f"  Missed items (examples): {'; '.join(missed[:3])}"
                )

        # ── Summary ───────────────────────────────────────────────────────────
        if not action.summary:
            feedback_parts.append("✗ No summary provided.")
            summary_score = 0.0
        else:
            summary_score = _token_overlap(action.summary, email.true_summary)
            reward += self.SUMMARY_WEIGHT * summary_score
            level = "Good" if summary_score >= 0.5 else "Partial" if summary_score >= 0.25 else "Poor"
            feedback_parts.append(
                f"Summary quality: {level} (similarity score {summary_score:.2f}). "
                f"(+{self.SUMMARY_WEIGHT * summary_score:.3f})"
            )

        reward = round(min(max(reward, 0.0), 1.0), 4)
        feedback = "\n".join(feedback_parts)
        return reward, feedback


# ── Grader 3 — Reply ──────────────────────────────────────────────────────────

class ReplyGrader:
    """
    Hard task grader — LLM-as-judge.
    Scores the reply on three axes:
      • Tone & appropriateness      (0–30 pts → normalised to 0.30 max)
      • Completeness (all points)   (0–40 pts → normalised to 0.40 max)
      • Professionalism & clarity   (0–30 pts → normalised to 0.30 max)
    Total: 0.0 – 1.0

    Falls back to heuristic scoring if the LLM call fails.
    """

    JUDGE_SYSTEM_PROMPT = (
        "You are an expert email quality judge. You assess professional email replies "
        "on three axes. Return ONLY valid JSON with no markdown fences."
    )

    JUDGE_USER_TEMPLATE = """\
ORIGINAL EMAIL:
Subject: {subject}
From: {sender}
---
{body}
---

AGENT'S REPLY:
---
{reply}
---

Score the agent's reply on a scale of 0–100 total, broken into:
- tone_score      (0–30): Appropriateness of tone for this specific email context
- completeness    (0–40): All points/questions in the original email are addressed
- professionalism (0–30): Clarity, formatting, grammar, professional language

Return EXACTLY this JSON (integers only, no explanation):
{{
  "tone_score": <0-30>,
  "completeness": <0-40>,
  "professionalism": <0-30>,
  "brief_feedback": "<one sentence>"
}}"""

    def grade(self, action: EmailTriageAction, email: Email) -> Tuple[float, str]:
        if not action.reply or len(action.reply.strip()) < 30:
            return 0.0, "✗ No reply provided or reply is too short (minimum 30 characters)."

        try:
            reward, feedback = self._llm_grade(action.reply, email)
        except Exception as exc:
            logger.warning("LLM judge failed (%s), falling back to heuristic.", exc)
            reward, feedback = self._heuristic_grade(action.reply, email)

        reward = round(min(max(reward, 0.0), 1.0), 4)
        return reward, feedback

    def _llm_grade(self, reply: str, email: Email) -> Tuple[float, str]:
        client = _get_llm_client()
        prompt = self.JUDGE_USER_TEMPLATE.format(
            subject=email.subject,
            sender=f"{email.sender_name} ({email.sender_role})",
            body=email.body,
            reply=reply,
        )
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": self.JUDGE_SYSTEM_PROMPT},
                {"role": "user",   "content": prompt},
            ],
            temperature=0.0,
            max_tokens=256,
        )
        raw = (completion.choices[0].message.content or "").strip()
        # Strip markdown fences if present
        raw = re.sub(r"```[a-z]*\n?", "", raw).strip("` \n")
        parsed = json.loads(raw)

        tone           = int(parsed.get("tone_score", 0))
        completeness   = int(parsed.get("completeness", 0))
        professionalism = int(parsed.get("professionalism", 0))
        brief_feedback = str(parsed.get("brief_feedback", ""))

        tone            = max(0, min(30, tone))
        completeness    = max(0, min(40, completeness))
        professionalism = max(0, min(30, professionalism))

        total   = tone + completeness + professionalism
        reward  = total / 100.0

        feedback = (
            f"LLM Judge Scores:\n"
            f"  Tone & appropriateness : {tone}/30\n"
            f"  Completeness           : {completeness}/40\n"
            f"  Professionalism        : {professionalism}/30\n"
            f"  Total                  : {total}/100  →  reward {reward:.2f}\n"
            f"  Feedback               : {brief_feedback}"
        )
        return reward, feedback

    def _heuristic_grade(self, reply: str, email: Email) -> Tuple[float, str]:
        """
        Fallback heuristic grader when LLM is unavailable.
        Uses token overlap + structural signals.
        """
        score = 0.0
        feedback_parts: List[str] = []

        # Completeness proxy: overlap with true summary
        overlap = _token_overlap(reply, email.true_summary)
        completeness = min(overlap * 1.5, 0.40)
        score += completeness
        feedback_parts.append(f"Completeness (heuristic): {completeness:.2f}/0.40")

        # Professionalism proxy: structural signals
        prof = 0.0
        if any(g in reply.lower() for g in ["dear", "hello", "hi ", "good morning", "good afternoon"]):
            prof += 0.08
        if any(s in reply.lower() for s in ["sincerely", "regards", "best regards", "thank you", "kind regards"]):
            prof += 0.08
        if len(reply.split()) >= 50:
            prof += 0.07
        if len(reply.split("\n")) >= 3:
            prof += 0.07
        prof = min(prof, 0.30)
        score += prof
        feedback_parts.append(f"Professionalism (heuristic): {prof:.2f}/0.30")

        # Tone proxy: length + question response
        tone = min(0.10 + (0.10 if "?" not in reply else 0.20), 0.30)
        score += tone
        feedback_parts.append(f"Tone (heuristic): {tone:.2f}/0.30")

        feedback_parts.append("(Heuristic grader used — LLM judge unavailable)")
        return score, "\n".join(feedback_parts)


# ── Grader Factory ────────────────────────────────────────────────────────────

def get_grader(task_id: str):
    mapping = {
        "task_classify": ClassificationGrader(),
        "task_extract":  ExtractionGrader(),
        "task_reply":    ReplyGrader(),
    }
    if task_id not in mapping:
        raise ValueError(f"No grader found for task_id '{task_id}'")
    return mapping[task_id]