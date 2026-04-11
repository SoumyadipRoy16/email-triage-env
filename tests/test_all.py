from __future__ import annotations
import pytest
from fastapi.testclient import TestClient

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server.email_corpus import EMAILS, get_email_by_id, get_emails_by_category, get_emails_by_difficulty
from server.models import EmailTriageAction, EmailCategory, UrgencyLevel
from server.graders import ClassificationGrader, ExtractionGrader, ReplyGrader, get_grader
from server.env import EmailTriageEnv
from server.main import app


# ══════════════════════════════════════════════════════════════════════════════
# CORPUS TESTS
# ══════════════════════════════════════════════════════════════════════════════

class TestCorpus:

    def test_corpus_size(self):
        assert len(EMAILS) == 27, f"Expected 27 emails, got {len(EMAILS)}"

    def test_all_categories_present(self):
        expected = {
            "billing", "technical_support", "sales_inquiry", "hr_policy",
            "legal", "compliance", "general_inquiry", "complaint", "partnership"
        }
        actual = {e.true_category for e in EMAILS}
        assert actual == expected, f"Missing categories: {expected - actual}"

    def test_three_per_category(self):
        for cat in ["billing", "technical_support", "sales_inquiry", "hr_policy",
                    "legal", "compliance", "general_inquiry", "complaint", "partnership"]:
            emails = get_emails_by_category(cat)
            assert len(emails) == 3, f"Expected 3 emails for category '{cat}', got {len(emails)}"

    def test_all_urgencies_present(self):
        urgencies = {e.true_urgency for e in EMAILS}
        assert urgencies == {"critical", "high", "medium", "low"}

    def test_all_difficulties_present(self):
        difficulties = {e.difficulty for e in EMAILS}
        assert difficulties == {"easy", "medium", "hard"}

    def test_unique_email_ids(self):
        ids = [e.email_id for e in EMAILS]
        assert len(ids) == len(set(ids)), "Duplicate email IDs found"

    def test_all_emails_have_action_items(self):
        for email in EMAILS:
            assert len(email.true_action_items) >= 2, \
                f"Email {email.email_id} has fewer than 2 action items"

    def test_all_emails_have_summary(self):
        for email in EMAILS:
            assert len(email.true_summary) >= 30, \
                f"Email {email.email_id} summary too short"

    def test_get_email_by_id(self):
        email = get_email_by_id("e001")
        assert email is not None
        assert email.email_id == "e001"

    def test_get_email_by_id_missing(self):
        assert get_email_by_id("nonexistent") is None

    def test_get_emails_by_difficulty(self):
        easy = get_emails_by_difficulty("easy")
        assert len(easy) > 0
        assert all(e.difficulty == "easy" for e in easy)


# ══════════════════════════════════════════════════════════════════════════════
# CLASSIFICATION GRADER TESTS
# ══════════════════════════════════════════════════════════════════════════════

class TestClassificationGrader:

    def setup_method(self):
        self.grader = ClassificationGrader()
        self.email = get_email_by_id("e001")  # billing / critical

    def test_perfect_score(self):
        action = EmailTriageAction(category="billing", urgency="critical")
        reward, feedback = self.grader.grade(action, self.email)
        assert reward == 1.0
        assert "✓" in feedback

    def test_category_only_correct(self):
        action = EmailTriageAction(category="billing", urgency="low")
        reward, _ = self.grader.grade(action, self.email)
        assert reward == 0.50

    def test_urgency_only_correct(self):
        action = EmailTriageAction(category="complaint", urgency="critical")
        reward, _ = self.grader.grade(action, self.email)
        assert reward == 0.50

    def test_both_wrong(self):
        action = EmailTriageAction(category="general_inquiry", urgency="low")
        reward, _ = self.grader.grade(action, self.email)
        assert reward == 0.0

    def test_urgency_adjacent_partial(self):
        # e001 is critical; predict high (one level off)
        action = EmailTriageAction(category="general_inquiry", urgency="high")
        reward, feedback = self.grader.grade(action, self.email)
        assert reward == pytest.approx(0.15, abs=0.01)
        assert "adjacency" in feedback.lower()

    def test_urgency_far_no_partial(self):
        # low is two levels from critical
        action = EmailTriageAction(category="general_inquiry", urgency="low")
        reward, _ = self.grader.grade(action, self.email)
        assert reward == 0.0

    def test_no_category_no_reward(self):
        action = EmailTriageAction(urgency="critical")
        reward, feedback = self.grader.grade(action, self.email)
        assert reward == 0.50   # urgency correct, category missing
        assert "No category" in feedback

    def test_no_urgency_no_reward(self):
        action = EmailTriageAction(category="billing")
        reward, _ = self.grader.grade(action, self.email)
        assert reward == 0.50

    def test_reward_in_range(self):
        for email in EMAILS:
            for cat in ["billing", "complaint", "general_inquiry"]:
                for urg in ["critical", "low", "medium"]:
                    action = EmailTriageAction(category=cat, urgency=urg)
                    reward, _ = self.grader.grade(action, email)
                    assert 0.0 <= reward <= 1.0, \
                        f"Reward {reward} out of range for email {email.email_id}"

    def test_deterministic(self):
        """Same input always produces same output."""
        action = EmailTriageAction(category="billing", urgency="critical")
        r1, f1 = self.grader.grade(action, self.email)
        r2, f2 = self.grader.grade(action, self.email)
        assert r1 == r2
        assert f1 == f2


# ══════════════════════════════════════════════════════════════════════════════
# EXTRACTION GRADER TESTS
# ══════════════════════════════════════════════════════════════════════════════

class TestExtractionGrader:

    def setup_method(self):
        self.grader = ExtractionGrader()
        self.email = get_email_by_id("e001")

    def test_perfect_items_good_summary(self):
        action = EmailTriageAction(
            action_items=self.email.true_action_items[:],
            summary=self.email.true_summary,
        )
        reward, _ = self.grader.grade(action, self.email)
        assert reward >= 0.85, f"Expected high reward, got {reward}"

    def test_no_items_zero(self):
        action = EmailTriageAction(action_items=[], summary="Test summary.")
        reward, _ = self.grader.grade(action, self.email)
        assert reward < 0.25

    def test_empty_action_zero(self):
        action = EmailTriageAction()
        reward, _ = self.grader.grade(action, self.email)
        assert reward == 0.0

    def test_partial_recall(self):
        # Only 2 of 5 items
        action = EmailTriageAction(
            action_items=self.email.true_action_items[:2],
            summary=self.email.true_summary,
        )
        reward, _ = self.grader.grade(action, self.email)
        assert 0.2 <= reward <= 0.80

    def test_hallucinated_items_hurt_precision(self):
        fake = EmailTriageAction(
            action_items=["Buy groceries", "Call dentist", "Walk the dog"],
            summary=self.email.true_summary,
        )
        real = EmailTriageAction(
            action_items=self.email.true_action_items[:],
            summary=self.email.true_summary,
        )
        r_fake, _ = self.grader.grade(fake, self.email)
        r_real, _ = self.grader.grade(real, self.email)
        assert r_fake < r_real

    def test_reward_in_range(self):
        for email in EMAILS:
            action = EmailTriageAction(
                action_items=email.true_action_items[:],
                summary=email.true_summary,
            )
            reward, _ = self.grader.grade(action, email)
            assert 0.0 <= reward <= 1.0

    def test_deterministic(self):
        action = EmailTriageAction(
            action_items=["Verify wire transfer", "Lift suspension flag"],
            summary="Invoice is overdue.",
        )
        r1, f1 = self.grader.grade(action, self.email)
        r2, f2 = self.grader.grade(action, self.email)
        assert r1 == r2
        assert f1 == f2

    def test_feedback_mentions_missed_items(self):
        action = EmailTriageAction(
            action_items=["Verify wire transfer"],
            summary="Invoice issue.",
        )
        _, feedback = self.grader.grade(action, self.email)
        assert "Missed" in feedback or "Recall" in feedback


# ══════════════════════════════════════════════════════════════════════════════
# REPLY GRADER TESTS
# ══════════════════════════════════════════════════════════════════════════════

class TestReplyGrader:

    def setup_method(self):
        self.grader = ReplyGrader()
        self.email = get_email_by_id("e001")

    def _good_reply(self):
        return (
            "Dear Margaret,\n\n"
            "Thank you for reaching out regarding invoice #INV-2024-8821. "
            "I have escalated this to our billing team immediately and can confirm "
            "we have located the wire transfer (REF: CHF-20241112-7743). "
            "The suspension flag on the Acme Corp account will be lifted within 30 minutes.\n\n"
            "Please do not hesitate to contact me if you need further assistance. "
            "I will send you a confirmation email once the account is fully reinstated.\n\n"
            "Best regards,\nCustomer Success Team"
        )

    def test_good_reply_scores_high(self):
        action = EmailTriageAction(reply=self._good_reply())
        reward, _ = self.grader.grade(action, self.email)
        assert reward >= 0.60, f"Good reply scored {reward}, expected >= 0.60"

    def test_empty_reply_zero(self):
        action = EmailTriageAction(reply="")
        reward, _ = self.grader.grade(action, self.email)
        assert reward == 0.0

    def test_too_short_zero(self):
        action = EmailTriageAction(reply="OK thanks")
        reward, _ = self.grader.grade(action, self.email)
        assert reward == 0.0

    def test_minimal_unprofessional_reply_low(self):
        action = EmailTriageAction(reply="lol ok gonna look into it tbh dunno what happened bye")
        reward, _ = self.grader.grade(action, self.email)
        # Might not be 0 but should be well below a good reply
        good_reward, _ = self.grader.grade(EmailTriageAction(reply=self._good_reply()), self.email)
        assert reward < good_reward

    def test_greeting_present_rewarded(self):
        with_greeting = EmailTriageAction(
            reply="Dear Margaret,\n\nWe will look into this. Please allow us 2 hours. "
                  "We will follow up shortly with a full update on the situation.\n\nBest regards, Team"
        )
        without_greeting = EmailTriageAction(
            reply="We will look into this. Please allow us 2 hours. "
                  "We will follow up shortly with a full update on the situation. Thank you."
        )
        r_with, _ = self.grader.grade(with_greeting, self.email)
        r_without, _ = self.grader.grade(without_greeting, self.email)
        assert r_with >= r_without

    def test_reward_in_range(self):
        for email in EMAILS:
            action = EmailTriageAction(reply=self._good_reply())
            reward, _ = self.grader.grade(action, email)
            assert 0.0 <= reward <= 1.0, f"Reward {reward} out of range"

    def test_deterministic(self):
        """Critical: same reply must always produce same score."""
        action = EmailTriageAction(reply=self._good_reply())
        r1, f1 = self.grader.grade(action, self.email)
        r2, f2 = self.grader.grade(action, self.email)
        assert r1 == r2
        assert f1 == f2

    def test_all_emails_deterministic(self):
        action = EmailTriageAction(reply=self._good_reply())
        for email in EMAILS:
            r1, _ = self.grader.grade(action, email)
            r2, _ = self.grader.grade(action, email)
            assert r1 == r2, f"Non-deterministic for email {email.email_id}"


# ══════════════════════════════════════════════════════════════════════════════
# ENVIRONMENT STATE MACHINE TESTS
# ══════════════════════════════════════════════════════════════════════════════

class TestEnvironment:

    def setup_method(self):
        self.env = EmailTriageEnv()

    def test_reset_returns_response(self):
        resp = self.env.reset(task_id="task_classify", seed=42)
        assert resp.episode_id
        assert resp.task_id == "task_classify"
        assert resp.observation.email_id

    def test_reset_observation_fields(self):
        resp = self.env.reset(task_id="task_classify", seed=1)
        obs = resp.observation
        assert obs.email_id
        assert obs.email_subject
        assert obs.email_body
        assert obs.email_sender
        assert obs.task_type == "classify"
        assert obs.task_instructions
        assert obs.feedback == ""
        assert obs.score == 0.0
        assert obs.step_number == 0
        assert obs.done is False

    def test_classify_done_after_one_step(self):
        self.env.reset(task_id="task_classify", seed=1)
        result = self.env.step(EmailTriageAction(category="billing", urgency="critical"))
        assert result.done is True

    def test_extract_done_after_two_steps(self):
        self.env.reset(task_id="task_extract", seed=1)
        r1 = self.env.step(EmailTriageAction(
            action_items=["Check invoice"], summary="Invoice is overdue."
        ))
        assert r1.done is False
        r2 = self.env.step(EmailTriageAction(
            action_items=["Check invoice"], summary="Invoice is overdue."
        ))
        assert r2.done is True

    def test_reply_done_after_three_steps(self):
        self.env.reset(task_id="task_reply", seed=1)
        reply = EmailTriageAction(reply="Dear Customer,\n\nThank you for your email. We will assist you shortly.\n\nBest regards,\nSupport Team")
        for i in range(1, 3):
            r = self.env.step(reply)
            assert r.done is False, f"Expected not done at step {i}"
        r = self.env.step(reply)
        assert r.done is True

    def test_reward_in_range_all_tasks(self):
        for task_id in ["task_classify", "task_extract", "task_reply"]:
            self.env.reset(task_id=task_id, seed=99)
            action = EmailTriageAction(
                category="general_inquiry",
                urgency="medium",
                action_items=["Test item"],
                summary="Test summary",
                reply="Dear Customer,\n\nThank you for reaching out. We will look into this matter and follow up shortly.\n\nBest regards,\nSupport"
            )
            result = self.env.step(action)
            assert 0.0 <= result.reward <= 1.0

    def test_state_after_step(self):
        self.env.reset(task_id="task_classify", seed=5)
        self.env.step(EmailTriageAction(category="billing", urgency="low"))
        state = self.env.state()
        assert state.step_number == 1
        assert state.done is True
        assert len(state.history) == 1
        assert state.history[0]["step"] == 1

    def test_step_before_reset_raises(self):
        env = EmailTriageEnv()
        with pytest.raises(RuntimeError, match="reset"):
            env.step(EmailTriageAction(category="billing", urgency="low"))

    def test_step_after_done_raises(self):
        self.env.reset(task_id="task_classify", seed=1)
        self.env.step(EmailTriageAction(category="billing", urgency="low"))
        with pytest.raises(RuntimeError, match="done"):
            self.env.step(EmailTriageAction(category="billing", urgency="low"))

    def test_feedback_populated_after_step(self):
        self.env.reset(task_id="task_extract", seed=1)
        result = self.env.step(EmailTriageAction(
            action_items=["Check invoice"], summary="Short summary."
        ))
        assert result.observation.feedback != ""

    def test_seed_reproducibility(self):
        resp1 = self.env.reset(task_id="task_classify", seed=42)
        resp2 = self.env.reset(task_id="task_classify", seed=42)
        assert resp1.observation.email_id == resp2.observation.email_id

    def test_different_seeds_may_differ(self):
        resp1 = self.env.reset(seed=1)
        resp2 = self.env.reset(seed=999)
        # Not guaranteed to differ but seeds 1 and 999 should pick different emails
        # Just check they both work
        assert resp1.observation.email_id
        assert resp2.observation.email_id

    def test_unknown_task_raises(self):
        with pytest.raises(ValueError):
            self.env.reset(task_id="task_nonexistent")

    def test_unknown_email_raises(self):
        with pytest.raises(ValueError):
            self.env.reset(email_id="eXXX")

    def test_cumulative_reward_accumulates(self):
        self.env.reset(task_id="task_extract", seed=1)
        r1 = self.env.step(EmailTriageAction(
            action_items=["Verify transfer"], summary="Invoice overdue."
        ))
        r2 = self.env.step(EmailTriageAction(
            action_items=["Verify transfer"], summary="Invoice overdue."
        ))
        state = self.env.state()
        assert state.cumulative_reward == pytest.approx(r1.reward + r2.reward, abs=0.001)


# ══════════════════════════════════════════════════════════════════════════════
# SESSION ISOLATION TESTS
# ══════════════════════════════════════════════════════════════════════════════

class TestSessionIsolation:

    def test_two_sessions_independent(self):
        """Two sessions with different seeds must track state independently."""
        env_a = EmailTriageEnv()
        env_b = EmailTriageEnv()

        resp_a = env_a.reset(task_id="task_classify", seed=1)
        resp_b = env_b.reset(task_id="task_extract", seed=99)

        assert resp_a.task_id == "task_classify"
        assert resp_b.task_id == "task_extract"

        # Step A — should complete (max_steps=1)
        r_a = env_a.step(EmailTriageAction(category="billing", urgency="high"))
        assert r_a.done is True

        # B should still be running (max_steps=2, only 0 steps taken)
        state_b = env_b.state()
        assert state_b.done is False
        assert state_b.step_number == 0

    def test_session_a_done_does_not_affect_session_b(self):
        env_a = EmailTriageEnv()
        env_b = EmailTriageEnv()

        env_a.reset(task_id="task_classify", seed=1)
        env_b.reset(task_id="task_classify", seed=1)

        env_a.step(EmailTriageAction(category="billing", urgency="low"))
        assert env_a.state().done is True

        # B not yet stepped — must still be active
        assert env_b.state().done is False


# ══════════════════════════════════════════════════════════════════════════════
# HTTP ENDPOINT TESTS
# ══════════════════════════════════════════════════════════════════════════════

class TestHTTPEndpoints:

    def setup_method(self):
        self.client = TestClient(app)

    def test_health(self):
        r = self.client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ok"
        assert data["version"] == "1.0.0"

    def test_root(self):
        r = self.client.get("/")
        assert r.status_code == 200
        assert "email-triage-env" in r.json()["name"]

    def test_tasks_list(self):
        r = self.client.get("/tasks")
        assert r.status_code == 200
        tasks = r.json()["tasks"]
        assert len(tasks) == 3
        ids = {t["task_id"] for t in tasks}
        assert ids == {"task_classify", "task_extract", "task_reply"}

    def test_reset_default(self):
        r = self.client.post("/reset", json={})
        assert r.status_code == 200
        data = r.json()
        assert data["episode_id"]
        assert data["task_id"] in {"task_classify", "task_extract", "task_reply"}
        obs = data["observation"]
        assert obs["email_id"]
        assert obs["done"] is False

    def test_reset_pinned_task(self):
        r = self.client.post("/reset", json={"task_id": "task_classify", "seed": 42})
        assert r.status_code == 200
        assert r.json()["task_id"] == "task_classify"

    def test_reset_invalid_task(self):
        r = self.client.post("/reset", json={"task_id": "task_invalid"})
        assert r.status_code == 400

    def test_step_after_reset(self):
        self.client.post("/reset", json={"task_id": "task_classify", "seed": 1})
        r = self.client.post("/step", json={"category": "billing", "urgency": "critical"})
        assert r.status_code == 200
        data = r.json()
        assert "reward" in data
        assert 0.0 <= data["reward"] <= 1.0
        assert "done" in data
        assert "observation" in data

    def test_step_without_reset_returns_409(self):
        # Use a fresh session that has never been reset
        r = self.client.post(
            "/step",
            json={"category": "billing", "urgency": "low"},
            headers={"X-Session-ID": "fresh-never-reset-session-xyz"}
        )
        assert r.status_code == 409

    def test_state_after_reset(self):
        self.client.post("/reset", json={"task_id": "task_extract", "seed": 5},
                         headers={"X-Session-ID": "test-state-session"})
        r = self.client.get("/state", headers={"X-Session-ID": "test-state-session"})
        assert r.status_code == 200
        state = r.json()
        assert state["step_number"] == 0
        assert state["done"] is False

    def test_session_isolation_via_headers(self):
        """Two HTTP sessions with different X-Session-ID must be independent."""
        self.client.post("/reset", json={"task_id": "task_classify", "seed": 1},
                         headers={"X-Session-ID": "session-alpha"})
        self.client.post("/reset", json={"task_id": "task_extract", "seed": 1},
                         headers={"X-Session-ID": "session-beta"})

        r_alpha = self.client.get("/state", headers={"X-Session-ID": "session-alpha"})
        r_beta  = self.client.get("/state", headers={"X-Session-ID": "session-beta"})

        assert r_alpha.json()["task_type"] == "classify"
        assert r_beta.json()["task_type"]  == "extract"

    def test_full_classify_episode(self):
        sid = "test-classify-full"
        self.client.post("/reset", json={"task_id": "task_classify", "seed": 42},
                         headers={"X-Session-ID": sid})
        # seed=42 picks e008c (complaint / medium)
        r = self.client.post("/step",
                             json={"category": "complaint", "urgency": "medium"},
                             headers={"X-Session-ID": sid})
        assert r.status_code == 200
        assert r.json()["done"] is True
        assert r.json()["reward"] == 1.0

    def test_full_extract_episode(self):
        sid = "test-extract-full"
        self.client.post("/reset", json={"task_id": "task_extract", "seed": 43},
                         headers={"X-Session-ID": sid})

        r1 = self.client.post("/step",
                              json={"action_items": ["Verify invoice", "Lift suspension flag"],
                                    "summary": "Invoice overdue, suspension requested."},
                              headers={"X-Session-ID": sid})
        assert r1.json()["done"] is False

        r2 = self.client.post("/step",
                              json={"action_items": ["Verify invoice", "Lift suspension flag"],
                                    "summary": "Invoice overdue, suspension requested."},
                              headers={"X-Session-ID": sid})
        assert r2.json()["done"] is True

    def test_sessions_endpoint(self):
        r = self.client.get("/sessions")
        assert r.status_code == 200
        assert "active_sessions" in r.json()

    def test_404_unknown_endpoint(self):
        r = self.client.get("/nonexistent")
        assert r.status_code == 404

    def test_observation_has_all_required_fields(self):
        r = self.client.post("/reset", json={"task_id": "task_classify", "seed": 1})
        obs = r.json()["observation"]
        required = [
            "email_id", "email_subject", "email_body", "email_sender",
            "task_type", "task_instructions", "feedback", "score",
            "step_number", "done"
        ]
        for field in required:
            assert field in obs, f"Missing field: {field}"


# ══════════════════════════════════════════════════════════════════════════════
# OPENENV SPEC COMPLIANCE TESTS
# ══════════════════════════════════════════════════════════════════════════════

class TestOpenEnvCompliance:

    def setup_method(self):
        self.client = TestClient(app)

    def test_reward_always_in_0_1_range(self):
        """All graders must produce rewards in [0.0, 1.0] for any input."""
        env = EmailTriageEnv()
        for task_id in ["task_classify", "task_extract", "task_reply"]:
            for email in EMAILS[:6]:
                env.reset(task_id=task_id, email_id=email.email_id)
                action = EmailTriageAction(
                    category="general_inquiry",
                    urgency="medium",
                    action_items=["Test item one", "Test item two"],
                    summary="This is a test summary for the email in question.",
                    reply=(
                        "Dear Customer,\n\nThank you for reaching out. "
                        "We will review your request and follow up shortly. "
                        "Please do not hesitate to contact us if you need further assistance.\n\n"
                        "Best regards,\nSupport Team"
                    )
                )
                result = env.step(action)
                assert 0.0 <= result.reward <= 1.0, \
                    f"Out-of-range reward {result.reward} for task={task_id} email={email.email_id}"

    def test_reset_always_clears_state(self):
        env = EmailTriageEnv()
        env.reset(task_id="task_classify", seed=1)
        env.step(EmailTriageAction(category="billing", urgency="low"))

        # Re-reset — must produce fresh episode
        resp = env.reset(task_id="task_extract", seed=2)
        assert resp.observation.step_number == 0
        assert resp.observation.done is False
        assert resp.observation.score == 0.0

    def test_done_flag_consistent(self):
        """observation.done and StepResult.done must match."""
        env = EmailTriageEnv()
        env.reset(task_id="task_classify", seed=1)
        result = env.step(EmailTriageAction(category="billing", urgency="low"))
        assert result.done == result.observation.done

    def test_openenv_yaml_exists(self):
        import os
        yaml_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "openenv.yaml"
        )
        assert os.path.exists(yaml_path), "openenv.yaml not found"

    def test_pyproject_toml_has_scripts(self):
        import os
        import tomllib
        toml_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "pyproject.toml"
        )
        assert os.path.exists(toml_path)
        with open(toml_path, "rb") as f:
            data = tomllib.load(f)
        assert "scripts" in data.get("project", {}), "[project.scripts] missing"
        assert "server" in data["project"]["scripts"]