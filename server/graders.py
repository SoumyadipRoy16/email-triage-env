from __future__ import annotations
import re
import logging
from typing import Tuple, List, Set

from .models import EmailTriageAction
from .email_corpus import Email

logger = logging.getLogger(__name__)


# ── Text utilities ─────────────────────────────────────────────────────────────

def _normalize(text: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace."""
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _tokens(text: str) -> Set[str]:
    return set(_normalize(text).split())


def _jaccard(a: str, b: str) -> float:
    sa, sb = _tokens(a), _tokens(b)
    if not sa and not sb:
        return 1.0
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def _best_match(candidate: str, references: List[str], threshold: float = 0.28) -> bool:
    return any(_jaccard(candidate, ref) >= threshold for ref in references)


def _contains_any(text: str, phrases: List[str]) -> bool:
    tl = text.lower()
    return any(p in tl for p in phrases)


def _word_count(text: str) -> int:
    return len(text.split())


def _sentence_count(text: str) -> int:
    return len(re.split(r'[.!?]+', text.strip()))


# ── Grader 1 — Classification ─────────────────────────────────────────────────

class ClassificationGrader:
    """
    Easy task grader — fully deterministic.

    Scoring:
      +0.50  correct category (exact match)
      +0.50  correct urgency  (exact match)
      +0.15  urgency one level adjacent (e.g. high vs critical)
    Total: 0.0 – 1.0
    """
    CATEGORY_REWARD = 0.50
    URGENCY_REWARD  = 0.50
    ADJACENCY_BONUS = 0.15

    _URGENCY_ORDER = ["low", "medium", "high", "critical"]

    def grade(self, action: EmailTriageAction, email: Email) -> Tuple[float, str]:
        reward = 0.0
        parts: List[str] = []

        # Category
        if action.category is None:
            parts.append("✗ No category provided.")
        elif action.category == email.true_category:
            reward += self.CATEGORY_REWARD
            parts.append(f"✓ Category '{action.category}' correct. (+{self.CATEGORY_REWARD})")
        else:
            parts.append(
                f"✗ Category '{action.category}' incorrect. "
                f"Expected: '{email.true_category}'. (+0.00)"
            )

        # Urgency
        if action.urgency is None:
            parts.append("✗ No urgency provided.")
        elif action.urgency == email.true_urgency:
            reward += self.URGENCY_REWARD
            parts.append(f"✓ Urgency '{action.urgency}' correct. (+{self.URGENCY_REWARD})")
        else:
            bonus = self._adjacency(action.urgency, email.true_urgency)
            reward += bonus
            parts.append(
                f"✗ Urgency '{action.urgency}' incorrect. "
                f"Expected: '{email.true_urgency}'. "
                f"(+{bonus:.2f} adjacency credit)"
            )

        return round(min(max(reward, 0.0), 1.0), 4), "\n".join(parts)

    def _adjacency(self, predicted: str, true: str) -> float:
        try:
            pi = self._URGENCY_ORDER.index(predicted)
            ti = self._URGENCY_ORDER.index(true)
            return self.ADJACENCY_BONUS if abs(pi - ti) == 1 else 0.0
        except ValueError:
            return 0.0


# ── Grader 2 — Extraction ─────────────────────────────────────────────────────

class ExtractionGrader:
    """
    Medium task grader — fully deterministic.

    Scoring:
      0.40 × precision   (matched predicted / total predicted)
      0.40 × recall      (matched ground-truth / total ground-truth)
      0.20 × summary     (Jaccard overlap with canonical summary)
    Total: 0.0 – 1.0
    """
    PRECISION_WEIGHT = 0.40
    RECALL_WEIGHT    = 0.40
    SUMMARY_WEIGHT   = 0.20
    MATCH_THRESHOLD  = 0.28

    def grade(self, action: EmailTriageAction, email: Email) -> Tuple[float, str]:
        reward = 0.0
        parts: List[str] = []
        predicted   = action.action_items or []
        ground_truth = email.true_action_items

        if not predicted:
            parts.append("✗ No action_items provided.")
            precision = recall = 0.0
        else:
            tp_pred = sum(
                1 for p in predicted
                if _best_match(p, ground_truth, self.MATCH_THRESHOLD)
            )
            tp_gt = sum(
                1 for g in ground_truth
                if _best_match(g, predicted, self.MATCH_THRESHOLD)
            )
            precision = tp_pred / len(predicted)
            recall    = tp_gt   / len(ground_truth)
            reward   += self.PRECISION_WEIGHT * precision
            reward   += self.RECALL_WEIGHT    * recall

            parts.append(
                f"Action Items — Precision: {precision:.0%} ({tp_pred}/{len(predicted)}) | "
                f"Recall: {recall:.0%} ({tp_gt}/{len(ground_truth)})"
            )
            if recall < 0.6:
                missed = [g for g in ground_truth if not _best_match(g, predicted, self.MATCH_THRESHOLD)]
                parts.append(f"  Missed: {'; '.join(missed[:3])}")

        # Summary
        if not action.summary:
            parts.append("✗ No summary provided.")
            summary_score = 0.0
        else:
            summary_score = _jaccard(action.summary, email.true_summary)
            reward += self.SUMMARY_WEIGHT * summary_score
            level = "Good" if summary_score >= 0.50 else "Partial" if summary_score >= 0.25 else "Poor"
            parts.append(
                f"Summary: {level} (similarity {summary_score:.2f}). "
                f"(+{self.SUMMARY_WEIGHT * summary_score:.3f})"
            )

        return round(min(max(reward, 0.0), 1.0), 4), "\n".join(parts)


# ── Grader 3 — Reply (Deterministic Rubric) ───────────────────────────────────

class ReplyGrader:
    """
    Hard task grader — fully deterministic, LLM-free.

    Evaluates a reply email on five independent axes using lexical signals,
    structural analysis, and keyword coverage. Each axis contributes a
    weighted sub-score; the total normalises to [0.0, 1.0].

    Axes:
      1. Greeting / opening       (0.08)  — professional salutation present
      2. Sign-off / closing       (0.08)  — professional closing present
      3. Point coverage           (0.40)  — key topics from email body addressed
      4. Structural quality       (0.20)  — length, paragraphs, formatting
      5. Professional tone        (0.24)  — register, hedging, politeness signals

    Total: 0.0 – 1.0 (fully reproducible for identical inputs)
    """

    # ── Weight constants ──────────────────────────────────────────────────────
    W_GREETING    = 0.08
    W_CLOSING     = 0.08
    W_COVERAGE    = 0.40
    W_STRUCTURE   = 0.20
    W_TONE        = 0.24

    # ── Lexical signal lists ──────────────────────────────────────────────────
    GREETINGS = [
        "dear ", "hello ", "hi ", "good morning", "good afternoon",
        "good evening", "greetings", "to whom it may concern",
    ]
    CLOSINGS = [
        "sincerely", "regards", "best regards", "kind regards",
        "yours faithfully", "yours sincerely", "thank you", "thanks",
        "warm regards", "respectfully",
    ]
    PROFESSIONAL_SIGNALS = [
        "please", "kindly", "appreciate", "understand", "apologi",
        "assure", "ensure", "confirm", "happy to", "glad to",
        "would be", "we will", "i will", "follow up", "look forward",
        "do not hesitate", "feel free", "let me know",
    ]
    UNPROFESSIONAL_SIGNALS = [
        "lol", "omg", "wtf", "nope", "yep", "gonna", "wanna",
        "dunno", "tbh", "fyi mate", "cheers mate",
    ]

    def grade(self, action: EmailTriageAction, email: Email) -> Tuple[float, str]:
        reply = (action.reply or "").strip()
        parts: List[str] = []
        reward = 0.0

        if len(reply) < 40:
            return 0.0, "✗ Reply too short or missing (minimum 40 characters)."

        rl = reply.lower()

        # ── 1. Greeting ───────────────────────────────────────────────────────
        has_greeting = _contains_any(rl, self.GREETINGS)
        g_score = self.W_GREETING if has_greeting else 0.0
        reward += g_score
        parts.append(
            f"{'✓' if has_greeting else '✗'} Greeting: "
            f"{'present' if has_greeting else 'missing'}. (+{g_score:.2f})"
        )

        # ── 2. Sign-off ───────────────────────────────────────────────────────
        # Check last 150 chars for closing
        tail = rl[-150:]
        has_closing = _contains_any(tail, self.CLOSINGS)
        c_score = self.W_CLOSING if has_closing else 0.0
        reward += c_score
        parts.append(
            f"{'✓' if has_closing else '✗'} Sign-off: "
            f"{'present' if has_closing else 'missing'}. (+{c_score:.2f})"
        )

        # ── 3. Point coverage ─────────────────────────────────────────────────
        # Extract key noun phrases from email body and check if reply addresses them
        coverage_score = self._coverage_score(reply, email)
        reward += self.W_COVERAGE * coverage_score
        parts.append(
            f"Coverage: {coverage_score:.0%} of key topics addressed. "
            f"(+{self.W_COVERAGE * coverage_score:.3f})"
        )

        # ── 4. Structural quality ─────────────────────────────────────────────
        struct_score = self._structure_score(reply)
        reward += self.W_STRUCTURE * struct_score
        parts.append(
            f"Structure score: {struct_score:.2f}. "
            f"(words={_word_count(reply)}, paragraphs={reply.count(chr(10))+1}). "
            f"(+{self.W_STRUCTURE * struct_score:.3f})"
        )

        # ── 5. Professional tone ──────────────────────────────────────────────
        tone_score = self._tone_score(rl)
        reward += self.W_TONE * tone_score
        parts.append(
            f"Tone score: {tone_score:.2f}. (+{self.W_TONE * tone_score:.3f})"
        )

        return round(min(max(reward, 0.0), 1.0), 4), "\n".join(parts)

    def _coverage_score(self, reply: str, email: Email) -> float:
        """
        Measure how many of the email's key topics appear in the reply.
        Extracts meaningful tokens (>4 chars) from email body and action items
        as proxy for 'topics that must be addressed'.
        """
        # Collect key tokens from email body + action items
        source_tokens: Set[str] = set()
        for item in email.true_action_items:
            source_tokens |= {t for t in _tokens(item) if len(t) > 4}
        for t in _tokens(email.body):
            if len(t) > 5:
                source_tokens.add(t)

        if not source_tokens:
            return 0.5

        reply_tokens = _tokens(reply)
        matched = len(source_tokens & reply_tokens)
        # Use diminishing returns: sqrt to avoid penalising concise but complete replies
        raw = matched / len(source_tokens)
        import math
        return min(math.sqrt(raw) * 1.2, 1.0)

    def _structure_score(self, reply: str) -> float:
        """
        Score structural quality:
          - Word count in ideal range (60–400)
          - Multiple paragraphs
          - Not just one giant block
        """
        score = 0.0
        wc = _word_count(reply)
        paragraphs = len([p for p in reply.split("\n") if p.strip()])

        # Word count
        if wc >= 60:
            score += 0.35
        elif wc >= 30:
            score += 0.15

        if wc >= 120:
            score += 0.25
        elif wc >= 80:
            score += 0.10

        if wc > 500:   # penalise excessive length
            score -= 0.10

        # Paragraph structure
        if paragraphs >= 3:
            score += 0.30
        elif paragraphs >= 2:
            score += 0.15

        # Sentence variety
        if _sentence_count(reply) >= 4:
            score += 0.10

        return min(max(score, 0.0), 1.0)

    def _tone_score(self, reply_lower: str) -> float:
        """
        Score professional tone using lexical signals:
          + professional signals present
          - unprofessional signals present
        """
        score = 0.0
        signals_found = sum(
            1 for s in self.PROFESSIONAL_SIGNALS
            if s in reply_lower
        )
        # Up to 0.8 from professional signals (cap at 6)
        score += min(signals_found / 6, 1.0) * 0.80

        # Deduct for unprofessional language
        unprofessional = sum(
            1 for s in self.UNPROFESSIONAL_SIGNALS
            if s in reply_lower
        )
        score -= unprofessional * 0.20

        # Bonus: uses sender's name (personalisation)
        score += 0.20

        return min(max(score, 0.0), 1.0)


# ── Grader Factory ────────────────────────────────────────────────────────────

def get_grader(task_id: str):
    mapping = {
        "task_classify": ClassificationGrader(),
        "task_extract":  ExtractionGrader(),
        "task_reply":    ReplyGrader(),
    }
    if task_id not in mapping:
        raise ValueError(f"No grader for task_id '{task_id}'")
    return mapping[task_id]