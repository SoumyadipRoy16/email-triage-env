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

        # Step 0: Reasoning Bonus (Optional but recommended)
        if action.reasoning and len(action.reasoning) > 10:
            reward += 0.05
            parts.append("✔ Analysis reasoning provided (+0.05 bonus)")

        # Category
        if action.category is None:
            parts.append("✗ No category provided.")
        elif str(action.category).lower() == str(email.true_category).lower():
            reward += self.CATEGORY_REWARD
            parts.append(f"✓ Category '{action.category}' correct. (+{self.CATEGORY_REWARD})")
        else:
            # Critical Logic Penalty: Identifying Compliance as something else 
            # or vice versa is a severe enterprise failure.
            if email.true_category == "compliance" or action.category == "compliance":
                reward -= 0.20
                parts.append("✘ Regulatory Failure: Incorrect compliance classification (-0.20)")
            
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

        # Bonus for Reasoning Trace
        if action.reasoning and len(action.reasoning) > 15:
            reward += 0.05
            parts.append("✔ Step-by-step reasoning trace provided (+0.05 bonus)")

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

    # ── WEIGHTS ─────────────────────────────────────────────────────────────
    # Normalise weights to sum to 1.0 (Total: 0.0 – 1.0)
    W_GREETING    = 0.05
    W_CLOSING     = 0.05
    W_COVERAGE    = 0.40
    W_TONE        = 0.15
    W_READABILITY = 0.15
    W_POLITENESS  = 0.20

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
    # Professionalism: Politeness is a separate metric now
    POLITE_SIGNALS = [
        "please", "kindly", "could you", "would you mind", "i appreciate", 
        "thank you for", "many thanks", "your patience", "apologies for",
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

        # ── 1. Structural Checks (Greeting/Closing) ──────────────────────────
        has_greeting = _contains_any(rl, self.GREETINGS)
        reward += self.W_GREETING if has_greeting else 0.0
        
        tail = rl[-150:]
        has_closing = _contains_any(tail, self.CLOSINGS)
        reward += self.W_CLOSING if has_closing else 0.0

        # ── 2. Information Coverage ───────────────────────────────────────────
        coverage_score = self._coverage_score(reply, email)
        reward += self.W_COVERAGE * coverage_score

        # ── 3. Readability Analysis (Flesch-Kincaid surrogate) ───────────────
        read_score = self._readability_score(reply)
        reward += self.W_READABILITY * read_score

        # ── 4. Politeness & Tone ──────────────────────────────────────────────
        polite_score = self._politeness_score(rl)
        reward += self.W_POLITENESS * polite_score
        
        tone_score = self._tone_score(rl)
        reward += self.W_TONE * tone_score

        # ── 5. Penalty Engines ───────────────────────────────────────────────
        
        # Penalise identifying a non-compliance email as compliance (False Positive)
        # and penalise missing compliance markers (False Negative)
        # Note: This usually happens in ClassificationGrader, but adding logic here
        # to check for "Entity Hallucination" in the Body content.
        
        # Critical Hallucination Penalty: Does the reply mention names NOT in the email?
        unseen_names = self._hallucinated_names(reply, email)
        if unseen_names:
            reward -= 0.25
            parts.append(f"✘ Entity Hallucination: Mentions unknown names {', '.join(unseen_names[:2])} (-0.25)")

        # Reasoning Trace: Did the agent provide reasoning? (Reward for good habits)
        if action.reasoning and len(action.reasoning) > 15:
            reward += 0.05
            parts.append("✔ Step-by-step reasoning provided (+0.05 bonus)")

        # Professionalism Fail: Slang or shorthand
        if any(s in rl for s in self.UNPROFESSIONAL_SIGNALS):
             reward -= 0.35
             parts.append("! Critical failure: Unprofessional language detected (-0.35)")

        # Result construction
        parts.append(f"Coverage: {coverage_score:.0%}")
        parts.append(f"Readability: {read_score:.2f}")
        parts.append(f"Politeness/Tone: {(polite_score + tone_score)/2:.2f}")

        return round(min(max(reward, 0.0), 1.0), 4), "\n".join(parts)

    def _readability_score(self, text: str) -> float:
        """Surrogate for professionalism: neither too simple nor overly complex."""
        wc = _word_count(text)
        sc = _sentence_count(text)
        if sc == 0: return 0.0
        
        avg_sent_len = wc / sc
        # Business sweet spot for clarity: 12-25 words per sentence
        if 12 <= avg_sent_len <= 25:
            return 1.0
        elif 8 <= avg_sent_len <= 35:
            return 0.6
        return 0.2

    def _politeness_score(self, rl: str) -> float:
        found = sum(1 for s in self.POLITE_SIGNALS if s in rl)
        return min(found / 4, 1.0)

    def _hallucinated_names(self, reply: str, email: Email) -> List[str]:
        """Detect names or entities in reply that aren't in the source context."""
        common = {"david", "sarah", "john", "michael", "emily", "jessica", "alice", "bob"}
        
        # Tokens from body and sender
        body_tokens = _tokens(email.body)
        sender_tokens = _tokens(email.sender_name)
        
        # Add explicitly allowed entities if they exist
        allowed = set()
        if hasattr(email, "allowed_entities") and email.allowed_entities:
            for entity in email.allowed_entities:
                allowed |= _tokens(entity)

        present = body_tokens | sender_tokens | allowed
        reply_tokens = _tokens(reply)
        
        # Find common names in reply that are NOT in the source
        hallucinated = [n for n in (common & reply_tokens) if n not in present]
        
        # EXTRA: If the reply is signed as a name not in body/sender/allowed
        # (Simple signature check: last 2-3 tokens)
        tail = " ".join(reply.split()[-5:]).lower()
        for name in common:
            if name in tail and name not in present:
                if name not in hallucinated:
                    hallucinated.append(name)

        return hallucinated

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
          - Penalise unprofessional signals
        """
        score = 1.0  # start at 1.0; tone is about lack of unprofessionalism here
        unprofessional = sum(
            1 for s in self.UNPROFESSIONAL_SIGNALS
            if s in reply_lower
        )
        score -= unprofessional * 0.25

        # Also check for professional signals
        signals_found = sum(
            1 for s in self.POLITE_SIGNALS
            if s in reply_lower
        )
        # Having some politeness is good; 2+ signals = full credit for this axis
        polite_part = min(signals_found / 2, 1.0)
        
        return min(max(score * 0.7 + polite_part * 0.3, 0.0), 1.0)


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