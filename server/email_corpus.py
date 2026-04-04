from __future__ import annotations
from typing import List
from pydantic import BaseModel


class Email(BaseModel):
    email_id: str
    sender_name: str
    sender_role: str
    sender_email: str
    subject: str
    body: str
    # Ground-truth labels
    true_category: str   # billing | technical_support | sales_inquiry | hr_policy | legal | general_inquiry | complaint | partnership
    true_urgency: str    # critical | high | medium | low
    true_action_items: List[str]   # canonical action items for extract task
    true_summary: str              # canonical summary for extract task


EMAILS: List[Email] = [

    # ── EASY / CLASSIFY ────────────────────────────────────────────────────
    Email(
        email_id="e001",
        sender_name="Margaret Holloway",
        sender_role="CFO",
        sender_email="m.holloway@acmecorp.com",
        subject="URGENT: Invoice #INV-2024-8821 overdue — service suspension imminent",
        body=(
            "Hello,\n\n"
            "I'm writing on behalf of Acme Corp regarding invoice #INV-2024-8821 "
            "for $47,350 which was due on November 15th. We have now passed the "
            "30-day grace period and your accounting system shows a suspension flag "
            "on our account.\n\n"
            "Our team has confirmed that the wire transfer was initiated on "
            "November 12th from Chase Bank. I've attached the SWIFT confirmation "
            "(REF: CHF-20241112-7743). Could you please check your records and "
            "lift the suspension flag immediately? We have critical operations "
            "depending on your platform and cannot afford any downtime.\n\n"
            "Please respond within the next 2 hours. If needed, escalate to your "
            "billing manager directly.\n\n"
            "Margaret Holloway\nCFO, Acme Corp\n+1 (415) 882-0012"
        ),
        true_category="billing",
        true_urgency="critical",
        true_action_items=[
            "Verify receipt of wire transfer REF: CHF-20241112-7743",
            "Check Chase Bank records for payment dated November 12th",
            "Lift the suspension flag on Acme Corp account",
            "Respond to Margaret Holloway within 2 hours",
            "Escalate to billing manager if necessary",
        ],
        true_summary=(
            "CFO of Acme Corp reports a $47,350 invoice (#INV-2024-8821) is "
            "overdue and the account faces suspension, despite a wire transfer "
            "sent on Nov 12. Requests urgent verification and suspension removal."
        ),
    ),

    Email(
        email_id="e002",
        sender_name="Derek Osei",
        sender_role="Senior DevOps Engineer",
        sender_email="d.osei@techflow.io",
        subject="Production API returning 503 errors — 40% of requests failing",
        body=(
            "Hi Support Team,\n\n"
            "Since approximately 14:32 UTC today, we have been experiencing "
            "widespread 503 Service Unavailable errors on your REST API. "
            "Around 40% of our production requests are failing, which is "
            "directly impacting our end customers.\n\n"
            "Affected endpoint: POST /v2/process/batch\n"
            "Error rate: ~40% (normally <0.1%)\n"
            "Start time: 14:32 UTC\n"
            "Our account ID: TF-98821\n\n"
            "We've already ruled out issues on our side (load balancers are "
            "healthy, no recent deployments). This appears to be on your "
            "infrastructure.\n\n"
            "Could you:\n"
            "1. Confirm if there is an active incident on your status page\n"
            "2. Provide an ETA for resolution\n"
            "3. Let us know if we should implement a retry strategy in the meantime\n\n"
            "This is blocking our SLA commitments. Please escalate immediately.\n\n"
            "Derek Osei\nSenior DevOps Engineer, TechFlow"
        ),
        true_category="technical_support",
        true_urgency="critical",
        true_action_items=[
            "Check status page for active incident affecting POST /v2/process/batch",
            "Investigate 503 error rate spike starting at 14:32 UTC on account TF-98821",
            "Provide ETA for resolution to Derek Osei",
            "Advise on whether to implement a retry strategy",
            "Escalate incident internally",
        ],
        true_summary=(
            "Senior DevOps Engineer reports ~40% of production API requests "
            "failing with 503 errors since 14:32 UTC on endpoint POST /v2/process/batch. "
            "Requests confirmation of incident, ETA, and retry guidance."
        ),
    ),

    Email(
        email_id="e003",
        sender_name="Priya Nambiar",
        sender_role="Head of Partnerships",
        sender_email="priya.n@greenlabs.co",
        subject="Partnership proposal — joint go-to-market for Q1 2025",
        body=(
            "Dear Business Development Team,\n\n"
            "I hope this message finds you well. I'm Priya Nambiar, Head of "
            "Partnerships at GreenLabs Co. We are a B2B SaaS company serving "
            "2,400+ mid-market clients in the sustainability and ESG reporting space.\n\n"
            "We've been following your product closely and believe there is a "
            "compelling joint go-to-market opportunity heading into Q1 2025. "
            "Specifically, we see potential for:\n\n"
            "• Co-marketing campaigns targeting CFOs in the manufacturing sector\n"
            "• API integration between our ESG dashboard and your data platform\n"
            "• Joint webinar series (our audience: ~18,000 newsletter subscribers)\n\n"
            "We'd love to schedule a 30-minute introductory call with your BD "
            "team before the end of this month to explore alignment.\n\n"
            "Would any slot next week work? I'm available Mon–Thu, 9am–5pm EST.\n\n"
            "Best,\nPriya Nambiar\nHead of Partnerships, GreenLabs Co\n"
            "priya.n@greenlabs.co | +1 (212) 445-9901"
        ),
        true_category="partnership",
        true_urgency="medium",
        true_action_items=[
            "Review GreenLabs Co partnership proposal",
            "Schedule 30-minute introductory call with Priya Nambiar before end of month",
            "Evaluate API integration feasibility between GreenLabs ESG dashboard and our platform",
            "Assess co-marketing campaign opportunity targeting CFOs in manufacturing",
            "Consider joint webinar series with GreenLabs 18k subscriber audience",
        ],
        true_summary=(
            "Head of Partnerships at GreenLabs Co proposes a Q1 2025 joint "
            "go-to-market including co-marketing, API integration, and a joint "
            "webinar series. Requests a 30-min call before end of month."
        ),
    ),

    Email(
        email_id="e004",
        sender_name="Samuel Kline",
        sender_role="Employee",
        sender_email="s.kline@internal.company.com",
        subject="Question about parental leave policy for adoption",
        body=(
            "Hi HR Team,\n\n"
            "My partner and I are in the process of adopting a child and we "
            "expect the placement to happen sometime in February 2025. I wanted "
            "to understand our company's parental leave policy as it applies to "
            "adoption — specifically:\n\n"
            "1. How many weeks of paid leave am I entitled to?\n"
            "2. Does the policy differ between biological and adoptive parents?\n"
            "3. Can I use the leave on a flexible basis (e.g., part-time for "
            "a period rather than all at once)?\n"
            "4. What documentation will HR need from me to process the leave?\n\n"
            "I'd appreciate a written response so I can plan accordingly. "
            "Happy to schedule a call if that's easier.\n\n"
            "Thanks in advance,\nSamuel Kline\nSoftware Engineer, Platform Team"
        ),
        true_category="hr_policy",
        true_urgency="medium",
        true_action_items=[
            "Clarify number of weeks of paid parental leave available for adoption",
            "Confirm whether policy differs between biological and adoptive parents",
            "Explain flexible leave options (e.g., part-time usage)",
            "List required documentation for processing parental leave",
            "Provide written response to Samuel Kline",
        ],
        true_summary=(
            "Employee Samuel Kline is expecting an adoption placement in "
            "February 2025 and is requesting written clarification on the "
            "company parental leave policy, including entitlement, flexibility, "
            "and documentation requirements."
        ),
    ),

    Email(
        email_id="e005",
        sender_name="Rachel Torres",
        sender_role="Legal Counsel",
        sender_email="r.torres@torreslaw.com",
        subject="Notice of potential IP infringement — formal response required",
        body=(
            "Dear Legal Department,\n\n"
            "I am writing on behalf of my client, NovaTech Solutions LLC, "
            "regarding potential infringement of US Patent No. 11,842,330 "
            "('System and Method for Automated Data Pipeline Orchestration').\n\n"
            "Our analysis indicates that features released in your v3.4 product "
            "update (October 2024) may implement methods that are substantially "
            "similar to the claims of the aforementioned patent.\n\n"
            "We request that your legal team review this matter and provide a "
            "formal written response within 21 days of receipt of this letter. "
            "We are open to discussing licensing arrangements as an alternative "
            "to litigation.\n\n"
            "Please direct all correspondence to:\n"
            "Rachel Torres, Esq.\nTorres & Associates LLP\n"
            "r.torres@torreslaw.com\n+1 (310) 557-2200\n\n"
            "Sincerely,\nRachel Torres"
        ),
        true_category="legal",
        true_urgency="high",
        true_action_items=[
            "Forward notice to internal legal department immediately",
            "Review v3.4 product update against claims of US Patent No. 11,842,330",
            "Engage patent counsel for analysis",
            "Prepare formal written response within 21 days",
            "Evaluate licensing arrangement as alternative to litigation",
        ],
        true_summary=(
            "Legal counsel for NovaTech Solutions claims potential infringement "
            "of US Patent 11,842,330 by the v3.4 product update. Demands a "
            "formal written response within 21 days and is open to licensing talks."
        ),
    ),

    Email(
        email_id="e006",
        sender_name="Fiona Carmichael",
        sender_role="Enterprise Account Manager",
        sender_email="f.carmichael@bigretail.com",
        subject="Extremely disappointed with onboarding experience — escalation needed",
        body=(
            "Dear Customer Success Team,\n\n"
            "I am writing to formally escalate my dissatisfaction with our "
            "onboarding experience over the past three weeks. BigRetail Co "
            "signed a $180,000 annual contract and we were promised a dedicated "
            "onboarding specialist and 5-day implementation timeline.\n\n"
            "Reality: our onboarding specialist changed twice without notice, "
            "our implementation is now 3 weeks behind schedule, and we've had "
            "4 scheduled calls cancelled last-minute.\n\n"
            "This is directly impacting our Black Friday preparation — our most "
            "critical trading period of the year starts in 8 days.\n\n"
            "I am requesting:\n"
            "1. A call with your VP of Customer Success within 24 hours\n"
            "2. A dedicated senior implementation engineer assigned today\n"
            "3. A written remediation plan by end of week\n"
            "4. Compensation discussion for the delays caused\n\n"
            "If this is not resolved promptly, I will be forced to discuss "
            "contract termination with our procurement team.\n\n"
            "Fiona Carmichael\nEnterprise Account Manager, BigRetail Co"
        ),
        true_category="complaint",
        true_urgency="critical",
        true_action_items=[
            "Schedule call with VP of Customer Success within 24 hours",
            "Assign dedicated senior implementation engineer to BigRetail Co account today",
            "Prepare written remediation plan by end of week",
            "Initiate compensation discussion for onboarding delays",
            "Review contract terms and SLA commitments for BigRetail Co $180k contract",
        ],
        true_summary=(
            "Enterprise account manager at BigRetail Co ($180k contract) formally "
            "escalates severe onboarding failures: 3 weeks behind schedule with "
            "Black Friday 8 days away. Demands VP call within 24h, dedicated "
            "engineer, remediation plan, and compensation discussion."
        ),
    ),

    Email(
        email_id="e007",
        sender_name="Alan Brewster",
        sender_role="Sales Director",
        sender_email="a.brewster@prospectco.com",
        subject="Interested in your Enterprise plan — pricing and features inquiry",
        body=(
            "Hi Sales Team,\n\n"
            "We are ProspectCo, a 350-person fintech company currently evaluating "
            "enterprise data platforms for a planned migration in Q2 2025. "
            "I came across your platform through a G2 review and it looks "
            "promising for our use case.\n\n"
            "Could you send me:\n"
            "1. Your Enterprise pricing sheet\n"
            "2. A feature comparison vs. your Standard plan\n"
            "3. Information about SOC 2 Type II and ISO 27001 compliance\n"
            "4. Case studies from fintech or financial services clients\n\n"
            "We have a budget of approximately $200k–$300k annually and our "
            "decision timeline is mid-January 2025. We'd also be interested in "
            "a personalized demo if that's something you offer.\n\n"
            "Best,\nAlan Brewster\nSales Director, ProspectCo\n"
            "+44 20 7946 0312"
        ),
        true_category="sales_inquiry",
        true_urgency="high",
        true_action_items=[
            "Send Enterprise pricing sheet to Alan Brewster",
            "Provide feature comparison between Enterprise and Standard plans",
            "Share SOC 2 Type II and ISO 27001 compliance documentation",
            "Send fintech/financial services client case studies",
            "Schedule personalized demo for ProspectCo",
        ],
        true_summary=(
            "Sales Director at ProspectCo (350 people, fintech) inquires about "
            "Enterprise plan with $200-300k budget and mid-January decision timeline. "
            "Requests pricing, feature comparison, compliance docs, case studies, and demo."
        ),
    ),

    Email(
        email_id="e008",
        sender_name="Tomoko Watanabe",
        sender_role="Office Administrator",
        sender_email="t.watanabe@smallbiz.jp",
        subject="Quick question about office hours during holidays",
        body=(
            "Hello,\n\n"
            "I just wanted to check — will your support team be available "
            "during the upcoming Christmas and New Year holiday period "
            "(December 24 – January 2)?\n\n"
            "We sometimes have questions about our subscription during month-end "
            "processing, and it would be helpful to know in advance if there "
            "are any reduced hours or if we should plan around any downtime.\n\n"
            "Thank you!\nTomoko Watanabe\nOffice Administrator, SmallBiz KK"
        ),
        true_category="general_inquiry",
        true_urgency="low",
        true_action_items=[
            "Share holiday support hours (Dec 24 – Jan 2) with Tomoko Watanabe",
            "Confirm any planned maintenance windows during the holiday period",
        ],
        true_summary=(
            "Office administrator at SmallBiz KK asks about support team "
            "availability and any planned downtime during the Christmas–New Year "
            "holiday period (Dec 24 – Jan 2)."
        ),
    ),
]


def get_email_by_id(email_id: str) -> Email | None:
    return next((e for e in EMAILS if e.email_id == email_id), None)


def get_emails_for_task(task_type: str) -> List[Email]:
    """Return all emails (all are usable for any task type)."""
    return EMAILS


def get_email_by_index(index: int) -> Email:
    return EMAILS[index % len(EMAILS)]