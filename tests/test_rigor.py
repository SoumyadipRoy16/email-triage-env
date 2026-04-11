import pytest
from server.env import EmailTriageEnv
from server.models import EmailTriageAction
from server.email_corpus import EMAILS

class TestRigor:
    """
    Exceptional Rigor Suite:
    Ensures the environment correctly identifies and penalizes 
    advanced failure modes (Hallucination, Unprofessionalism, Regulatory Mappings).
    """

    def setup_method(self):
        self.env = EmailTriageEnv()

    def test_hallucination_penalty(self):
        """Verify that mentioning unknown names (hallucination) results in a -0.25 penalty."""
        # Find e001 (Margaret Holloway)
        self.env.reset(task_id="task_reply", email_id="e001")
        
        # This reply signs as 'Bob', who is NOT in the email or allowed entities
        action = EmailTriageAction(
            reply="Dear Margaret,\n\nWe have received your payment. Thank you.\n\nBest regards,\nBob"
        )
        result = self.env.step(action)
        
        assert "✘ Entity Hallucination" in result.observation.feedback
        # Since greeting/closing/minimal coverage is there, reward will be >0 but penalized by 0.25
        assert result.reward < 0.75 # Penalized

    def test_unprofessionalism_trap(self):
        """Verify that slang (lol, tbh) triggers a severe professional failure penalty."""
        self.env.reset(task_id="task_reply", email_id="e001")
        
        action = EmailTriageAction(
            reply="Dear Margaret,\n\nLOL we got the cash tbh. No worries about the suspension.\n\nBest, Team"
        )
        result = self.env.step(action)
        
        assert result.reward < 0.4
        assert "! Critical failure: Unprofessional language" in result.observation.feedback

    def test_regulatory_logic_penalty(self):
        """Verify that misidentifying a Compliance email (GDPR) as 'General Inquiry' is penalized."""
        # Find a compliance email (e010a)
        target_id = "e010a"
        self.env.reset(task_id="task_classify", email_id=target_id)
        
        # e010a is 'compliance'. We incorrectly call it 'general_inquiry'
        action = EmailTriageAction(
            category="general_inquiry",
            urgency="high"
        )
        result = self.env.step(action)
        
        # It should lose the 0.5 category reward AND get the -0.20 regulatory penalty
        # Base reward for urgency high (matching e010a) is 0.5. 
        # Final should be 0.5 - 0.2 = 0.3 (clamped)
        assert "✘ Regulatory Failure" in result.observation.feedback
        assert result.reward <= 0.35

    def test_reasoning_bonus_logic(self):
        """Verify that providing high-quality reasoning gives a reward bonus +0.05."""
        self.env.reset(task_id="task_classify", email_id="e001")
        
        action_no_reason = EmailTriageAction(
            category="billing",
            urgency="critical"
        )
        action_with_reason = EmailTriageAction(
            category="billing",
            urgency="critical",
            reasoning="The sender is the CFO of Acme Corp and mentions an overdue invoice with an imminent suspension flag, which qualifies as a billing issue with critical urgency."
        )
        
        # Reset and step twice (stateless internally except for the session, 
        # but easier to just use two resets)
        self.env.reset(task_id="task_classify", email_id="e001")
        res1 = self.env.step(action_no_reason)
        
        self.env.reset(task_id="task_classify", email_id="e001")
        res2 = self.env.step(action_with_reason)
        
        # In res2 it gets a bonus, but total is still capped at 1.0. 
        # So we check if the feedback mentions the bonus.
        assert "✔ Analysis reasoning provided" in res2.observation.feedback
        assert res2.reward == 1.0

    def test_clipping_bounds(self):
        """Ensure reward never drops below 0.0 or above 1.0 even with multiple penalties/bonuses."""
        self.env.reset(task_id="task_reply", email_id="e001")
        
        # Extreme bad case: empty/short + slang + hallucination
        action = EmailTriageAction(
            reply="lol kthx bye. Bob." # Too short anyway, but let's test clipping
        )
        result = self.env.step(action)
        assert 0.0 <= result.reward <= 1.0
