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
    difficulty: str          # easy | medium | hard  (for reply task difficulty)
    true_category: str
    true_urgency: str
    true_action_items: List[str]
    true_summary: str
    allowed_entities: List[str] = []  # Names, IDs, dates mentioned/allowable


EMAILS: List[Email] = [

    # ════════════════════════════════════════════════════════════
    # BILLING  (3 emails)
    # ════════════════════════════════════════════════════════════

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
        difficulty="medium",
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
        allowed_entities=["Margaret Holloway", "Acme Corp", "Invoice #INV-2024-8821", "$47,350", "November 12th", "Chase Bank", "REF: CHF-20241112-7743", "November 15th"],
    ),

    Email(
        email_id="e002b",
        sender_name="James Whitfield",
        sender_role="Accounts Payable Manager",
        sender_email="j.whitfield@retailgroup.com",
        subject="Duplicate charge on account — requesting refund of $12,400",
        body=(
            "Hi Billing Team,\n\n"
            "We noticed two identical charges of $12,400 each posted to our account "
            "(ACC-77821) on December 3rd and December 4th. Only one charge is valid "
            "per our contract (Order #ORD-2024-551).\n\n"
            "I have attached our bank statement showing both transactions. "
            "Please process a refund of $12,400 to our account within 5 business days "
            "per your refund policy, and send written confirmation of the refund "
            "initiation.\n\n"
            "Could you also investigate how the duplicate occurred so we can "
            "prevent this in future billing cycles?\n\n"
            "James Whitfield\nAccounts Payable Manager, Retail Group\n"
            "j.whitfield@retailgroup.com"
        ),
        difficulty="easy",
        true_category="billing",
        true_urgency="high",
        true_action_items=[
            "Investigate duplicate charge on account ACC-77821 for Order #ORD-2024-551",
            "Verify both $12,400 charges posted December 3rd and 4th",
            "Process refund of $12,400 within 5 business days",
            "Send written confirmation of refund initiation to James Whitfield",
            "Investigate root cause of duplicate charge to prevent recurrence",
        ],
        true_summary=(
            "Accounts Payable Manager at Retail Group reports a duplicate $12,400 "
            "charge on account ACC-77821. Requests refund within 5 business days, "
            "written confirmation, and root cause investigation."
        ),
    ),

    Email(
        email_id="e002c",
        sender_name="Hiroshi Tanaka",
        sender_role="Finance Director",
        sender_email="h.tanaka@nippontech.co.jp",
        subject="Billing query — unclear line items on Q4 invoice",
        body=(
            "Dear Finance Team,\n\n"
            "We received invoice #Q4-2024-0982 for ¥4,280,000 last week. "
            "While reviewing it, we noticed three line items that do not correspond "
            "to any services in our current contract:\n\n"
            "  - 'Platform Enhancement Fee' — ¥420,000\n"
            "  - 'Data Residency Surcharge' — ¥180,000\n"
            "  - 'API Overage (November)' — ¥95,000\n\n"
            "Our contract (signed March 2024) does not include these items. "
            "Could you please provide a breakdown and contract reference for each "
            "of these charges? We are unable to approve payment until these are "
            "clarified.\n\n"
            "We are happy to schedule a call if that would help resolve this faster.\n\n"
            "Best regards,\nHiroshi Tanaka\nFinance Director, NipponTech\n"
            "+81-3-5555-0192"
        ),
        difficulty="hard",
        true_category="billing",
        true_urgency="medium",
        true_action_items=[
            "Review invoice #Q4-2024-0982 line items against NipponTech contract signed March 2024",
            "Provide contract reference and breakdown for Platform Enhancement Fee (¥420,000)",
            "Provide contract reference and breakdown for Data Residency Surcharge (¥180,000)",
            "Provide contract reference and breakdown for API Overage November (¥95,000)",
            "Respond to Hiroshi Tanaka before payment approval deadline",
            "Offer call to resolve invoice dispute if written explanation insufficient",
        ],
        true_summary=(
            "Finance Director at NipponTech disputes three unrecognised line items "
            "totalling ¥695,000 on invoice #Q4-2024-0982, none of which appear in "
            "their March 2024 contract. Payment is withheld pending clarification."
        ),
    ),

    # ════════════════════════════════════════════════════════════
    # TECHNICAL SUPPORT  (3 emails)
    # ════════════════════════════════════════════════════════════

    Email(
        email_id="e003",
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
        difficulty="medium",
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
        email_id="e003b",
        sender_name="Ananya Krishnamurthy",
        sender_role="Platform Engineer",
        sender_email="a.krishnamurthy@finserve.in",
        subject="SSO integration broken after your SDK v4.2 upgrade",
        body=(
            "Hello Support,\n\n"
            "Following your SDK upgrade to v4.2 (released Tuesday), our SAML-based "
            "SSO integration has completely stopped working for approximately 230 of "
            "our users. The error we are seeing in our logs is:\n\n"
            "  AuthError: SAML assertion validation failed — "
            "  issuer mismatch (expected: urn:finserve:prod, got: urn:legacy:entity)\n\n"
            "This was working perfectly on v4.1. We have not changed anything on "
            "our side. The timing strongly suggests the issue was introduced by your "
            "v4.2 release.\n\n"
            "We need:\n"
            "- Confirmation this is a known bug in v4.2\n"
            "- An urgent patch or rollback instructions for v4.1\n"
            "- ETA on a fix\n\n"
            "230 users cannot log in. This is critical.\n\n"
            "Ananya Krishnamurthy | Platform Engineer | FinServe India"
        ),
        difficulty="hard",
        true_category="technical_support",
        true_urgency="critical",
        true_action_items=[
            "Investigate SAML issuer mismatch introduced in SDK v4.2",
            "Confirm whether AuthError issuer mismatch is a known bug in v4.2",
            "Provide rollback instructions to SDK v4.1",
            "Provide ETA for a patch fixing the SAML regression",
            "Escalate to engineering team responsible for v4.2 release",
        ],
        true_summary=(
            "Platform Engineer at FinServe India reports that 230 users cannot "
            "log in via SAML SSO after the SDK v4.2 upgrade, due to an issuer "
            "mismatch error. Requests bug confirmation, rollback instructions, "
            "and patch ETA."
        ),
    ),

    Email(
        email_id="e003c",
        sender_name="Luca Ferretti",
        sender_role="Systems Administrator",
        sender_email="l.ferretti@hotelgroup.it",
        subject="Data export stuck — job has been running for 19 hours",
        body=(
            "Hi,\n\n"
            "I initiated a full data export job (Job ID: EXP-20241204-00812) "
            "yesterday at 09:15 CET. It is now 04:20 CET the following morning "
            "and the job is still showing 'In Progress' at 67% completion. "
            "Normal export jobs complete in 2–3 hours for our data volume.\n\n"
            "I have tried cancelling and restarting but the cancel button does "
            "not respond. The job appears to be stuck.\n\n"
            "We have a regulatory reporting deadline at 08:00 CET this morning "
            "and need this data. Please assist urgently.\n\n"
            "Luca Ferretti\nSystems Administrator, Ferretti Hotel Group"
        ),
        difficulty="easy",
        true_category="technical_support",
        true_urgency="critical",
        true_action_items=[
            "Investigate stuck export job EXP-20241204-00812 running 19 hours at 67%",
            "Force-terminate or restart the stuck export job",
            "Fix unresponsive cancel button in export UI",
            "Ensure data export completes before Luca Ferretti's 08:00 CET deadline",
            "Communicate status update to Luca Ferretti immediately",
        ],
        true_summary=(
            "Systems Administrator at Ferretti Hotel Group has a data export job "
            "stuck at 67% for 19 hours with an unresponsive cancel button. "
            "Regulatory reporting deadline is at 08:00 CET — urgent resolution required."
        ),
    ),

    # ════════════════════════════════════════════════════════════
    # SALES INQUIRY  (3 emails)
    # ════════════════════════════════════════════════════════════

    Email(
        email_id="e004",
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
        difficulty="easy",
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
        email_id="e004b",
        sender_name="Beatrice Okonkwo",
        sender_role="Chief Procurement Officer",
        sender_email="b.okonkwo@govagency.ng",
        subject="Vendor evaluation — request for formal quotation and compliance pack",
        body=(
            "Dear Sales Department,\n\n"
            "The National Infrastructure Development Agency (NIDA) is conducting "
            "a formal vendor evaluation for a data management platform contract "
            "valued at approximately USD 1.2M over 3 years.\n\n"
            "To proceed with your organisation as a candidate vendor, we require:\n\n"
            "1. A formal quotation (RFQ response) for 500 user licences\n"
            "2. ISO 27001 and local data residency compliance certificates\n"
            "3. References from at least two government or public sector clients\n"
            "4. Proof of company registration and financial statements (last 2 years)\n"
            "5. Your standard SLA and uptime guarantees\n\n"
            "The evaluation deadline is January 31st. Late submissions will not "
            "be considered. Please direct all correspondence to our procurement "
            "portal: procurement.nida.gov.ng/rfq-2024-017\n\n"
            "Beatrice Okonkwo\nCPO, National Infrastructure Development Agency"
        ),
        difficulty="hard",
        true_category="sales_inquiry",
        true_urgency="high",
        true_action_items=[
            "Prepare formal RFQ response for 500 user licences for NIDA contract",
            "Compile ISO 27001 and data residency compliance certificates",
            "Gather two government or public sector client references",
            "Prepare company registration documents and 2-year financial statements",
            "Document SLA and uptime guarantees",
            "Submit all materials to procurement.nida.gov.ng/rfq-2024-017 before January 31st",
        ],
        true_summary=(
            "CPO of Nigeria's National Infrastructure Development Agency requests "
            "a formal RFQ response for a USD 1.2M/3-year contract covering "
            "500 licences, compliance docs, public sector references, and financials. "
            "Deadline is January 31st via procurement portal."
        ),
    ),

    Email(
        email_id="e004c",
        sender_name="Sophie Marchetti",
        sender_role="Marketing Manager",
        sender_email="s.marchetti@startup.fr",
        subject="Quick question about your Starter plan",
        body=(
            "Bonjour,\n\n"
            "I found your website and I was wondering if your Starter plan "
            "includes API access or only the dashboard? We are a small startup "
            "of about 12 people and we don't have a huge budget.\n\n"
            "Also do you have a free trial?\n\n"
            "Merci,\nSophie"
        ),
        difficulty="easy",
        true_category="sales_inquiry",
        true_urgency="low",
        true_action_items=[
            "Clarify whether Starter plan includes API access or only dashboard",
            "Inform Sophie Marchetti about free trial availability",
        ],
        true_summary=(
            "Marketing Manager at a 12-person French startup asks whether the "
            "Starter plan includes API access and whether a free trial is available."
        ),
    ),

    # ════════════════════════════════════════════════════════════
    # HR POLICY  (3 emails)
    # ════════════════════════════════════════════════════════════

    Email(
        email_id="e005",
        sender_name="Samuel Kline",
        sender_role="Software Engineer",
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
        difficulty="easy",
        true_category="hr_policy",
        true_urgency="medium",
        true_action_items=[
            "Clarify number of weeks of paid parental leave available for adoption",
            "Confirm whether policy differs between biological and adoptive parents",
            "Explain flexible leave options such as part-time usage",
            "List required documentation for processing parental leave",
            "Provide written response to Samuel Kline",
        ],
        true_summary=(
            "Software Engineer Samuel Kline is expecting an adoption placement "
            "in February 2025 and requests written clarification on the parental "
            "leave policy including entitlement, flexibility, and documentation."
        ),
    ),

    Email(
        email_id="e005b",
        sender_name="Priya Menon",
        sender_role="Senior Analyst",
        sender_email="p.menon@internal.company.com",
        subject="Formal grievance — hostile work environment from direct manager",
        body=(
            "Dear HR,\n\n"
            "I am writing to formally raise a grievance against my direct manager, "
            "David Chen (Engineering Manager). Over the past three months, I have "
            "experienced persistent belittling comments in team meetings, being "
            "excluded from key project decisions despite being the lead analyst, "
            "and receiving a below-expectations performance rating that I believe "
            "is retaliatory following my complaint to him in September.\n\n"
            "I have documented seven specific incidents with dates, witnesses, and "
            "written evidence (email excerpts). I am requesting:\n\n"
            "1. A formal grievance investigation under company policy\n"
            "2. An interim arrangement to reduce direct interaction while under review\n"
            "3. Confirmation that raising this grievance will not affect my employment\n"
            "4. A timeline for the investigation process\n\n"
            "I am available to meet at any time this week.\n\n"
            "Priya Menon\nSenior Analyst"
        ),
        difficulty="hard",
        true_category="hr_policy",
        true_urgency="high",
        true_action_items=[
            "Acknowledge receipt of formal grievance from Priya Menon against David Chen",
            "Initiate formal grievance investigation under company policy",
            "Arrange interim working arrangement to reduce direct contact during review",
            "Provide written confirmation that raising grievance will not affect employment",
            "Communicate investigation timeline and process to Priya Menon",
            "Review documented incidents and evidence provided",
        ],
        true_summary=(
            "Senior Analyst Priya Menon files a formal grievance against her manager "
            "David Chen for persistent belittling, exclusion from decisions, and a "
            "suspected retaliatory poor performance rating. Requests a formal "
            "investigation, interim separation, non-retaliation assurance, and timeline."
        ),
    ),

    Email(
        email_id="e005c",
        sender_name="Marcus Webb",
        sender_role="Account Executive",
        sender_email="m.webb@internal.company.com",
        subject="Clarification on remote work policy for international travel",
        body=(
            "Hi HR,\n\n"
            "I have an opportunity to work remotely from Portugal for 6 weeks "
            "while my partner completes a work assignment there "
            "(January 15 – February 28). I wanted to check whether this is "
            "permitted under our remote work policy and if there are any "
            "tax or compliance considerations I should be aware of.\n\n"
            "I'm a UK-based employee and would still be working UK hours. "
            "Is there a formal approval process I need to follow?\n\n"
            "Marcus Webb\nAccount Executive"
        ),
        difficulty="medium",
        true_category="hr_policy",
        true_urgency="medium",
        true_action_items=[
            "Confirm whether remote work from Portugal for 6 weeks is permitted under policy",
            "Advise on tax and compliance implications for UK employee working in Portugal",
            "Explain formal approval process for international remote work",
            "Respond to Marcus Webb before his January 15th start date",
        ],
        true_summary=(
            "UK-based Account Executive Marcus Webb requests HR approval and "
            "compliance guidance for working remotely from Portugal for 6 weeks "
            "(Jan 15 – Feb 28) while maintaining UK working hours."
        ),
    ),

    # ════════════════════════════════════════════════════════════
    # LEGAL  (3 emails)
    # ════════════════════════════════════════════════════════════

    Email(
        email_id="e006",
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
        difficulty="hard",
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
        email_id="e006b",
        sender_name="Compliance Officer",
        sender_role="Data Protection Authority",
        sender_email="enforcement@dpa.eu",
        subject="GDPR investigation notice — mandatory response within 14 days",
        body=(
            "Dear Data Controller,\n\n"
            "This office has received a complaint from an EU data subject (Case "
            "Ref: DPA-2024-EU-08812) alleging that your organisation failed to "
            "respond to a Subject Access Request (SAR) submitted on October 1st "
            "within the statutory 30-day window required under Article 15 GDPR.\n\n"
            "Under Article 83 GDPR, non-compliance may result in administrative "
            "fines of up to €20 million or 4% of global annual turnover, "
            "whichever is higher.\n\n"
            "You are required to:\n"
            "1. Provide a written response to this notice within 14 calendar days\n"
            "2. Supply evidence that the SAR was processed or an explanation for delay\n"
            "3. Confirm your DPO's contact details\n\n"
            "Failure to respond will result in escalation of enforcement proceedings.\n\n"
            "Data Protection Authority\nEnforcement Division"
        ),
        difficulty="hard",
        true_category="legal",
        true_urgency="critical",
        true_action_items=[
            "Escalate GDPR investigation notice DPA-2024-EU-08812 to DPO and legal team immediately",
            "Locate and review Subject Access Request submitted October 1st",
            "Prepare written response to DPA within 14 calendar days",
            "Supply evidence of SAR processing or written explanation for any delay",
            "Confirm DPO contact details to Data Protection Authority",
        ],
        true_summary=(
            "EU Data Protection Authority has opened an investigation (Case "
            "DPA-2024-EU-08812) over an alleged failure to respond to a GDPR SAR "
            "within 30 days. Demands written response and SAR evidence within 14 days; "
            "non-compliance risks fines up to €20M or 4% of turnover."
        ),
    ),

    Email(
        email_id="e006c",
        sender_name="Nina Holst",
        sender_role="Legal Counsel",
        sender_email="n.holst@employmentlaw.no",
        subject="Potential wrongful termination claim — settlement discussion",
        body=(
            "Dear HR and Legal,\n\n"
            "I represent Mr. Thomas Berg, formerly employed as a Senior Engineer "
            "at your organisation until his dismissal on November 14th. "
            "Mr. Berg believes his dismissal was procedurally unfair and potentially "
            "discriminatory under the Norwegian Working Environment Act (§ 15-7).\n\n"
            "Before initiating formal proceedings at the Labour Court, my client "
            "is willing to consider an out-of-court settlement. We propose a "
            "meeting within the next 10 business days to discuss terms.\n\n"
            "Please confirm within 5 business days whether your organisation is "
            "willing to engage in settlement discussions, and provide your legal "
            "representative's contact details.\n\n"
            "Nina Holst\nEmployment Law Attorney\nHolst & Partners AS, Oslo"
        ),
        difficulty="hard",
        true_category="legal",
        true_urgency="high",
        true_action_items=[
            "Forward wrongful termination claim to internal legal department",
            "Review termination of Thomas Berg on November 14th for procedural compliance",
            "Assess claim under Norwegian Working Environment Act Section 15-7",
            "Respond to Nina Holst within 5 business days on settlement willingness",
            "Appoint legal representative and provide contact details if proceeding",
        ],
        true_summary=(
            "Employment attorney Nina Holst represents former employee Thomas Berg "
            "who alleges procedurally unfair and potentially discriminatory dismissal "
            "under Norwegian law. Proposes out-of-court settlement meeting; requires "
            "response within 5 business days."
        ),
    ),

    # ════════════════════════════════════════════════════════════
    # GENERAL INQUIRY  (3 emails)
    # ════════════════════════════════════════════════════════════

    Email(
        email_id="e007",
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
        difficulty="easy",
        true_category="general_inquiry",
        true_urgency="low",
        true_action_items=[
            "Share holiday support hours for December 24 – January 2 with Tomoko Watanabe",
            "Confirm any planned maintenance windows during the holiday period",
        ],
        true_summary=(
            "Office administrator at SmallBiz KK asks about support team "
            "availability and any planned downtime during the Christmas–New Year "
            "holiday period (Dec 24 – Jan 2)."
        ),
    ),

    Email(
        email_id="e007b",
        sender_name="Carlos Medina",
        sender_role="IT Manager",
        sender_email="c.medina@constructora.mx",
        subject="Onboarding 45 new users next week — any guidance?",
        body=(
            "Hello,\n\n"
            "We are planning to onboard 45 new users to your platform starting "
            "Monday. This is our first large-scale rollout. Could you point me to "
            "your bulk user import documentation and let me know if there are any "
            "rate limits I should be aware of?\n\n"
            "Also, should I assign all users to our existing workspace or create "
            "a new one? We have two teams: Construction and Finance.\n\n"
            "Carlos Medina | IT Manager | Constructora del Norte"
        ),
        difficulty="easy",
        true_category="general_inquiry",
        true_urgency="medium",
        true_action_items=[
            "Share bulk user import documentation with Carlos Medina",
            "Advise on rate limits for bulk user onboarding",
            "Recommend workspace structure for Construction and Finance teams",
        ],
        true_summary=(
            "IT Manager at Constructora del Norte is onboarding 45 users starting "
            "Monday and requests bulk import documentation, rate limit information, "
            "and workspace structure guidance for two teams."
        ),
    ),

    Email(
        email_id="e007c",
        sender_name="Fatima Al-Rashidi",
        sender_role="Research Analyst",
        sender_email="f.alrashidi@university.ae",
        subject="Academic research inquiry — data access for peer-reviewed study",
        body=(
            "Dear Team,\n\n"
            "I am a research analyst at the UAE University conducting a peer-reviewed "
            "study on AI adoption patterns in Gulf-region enterprises. I would like "
            "to request access to any aggregated, anonymised usage data or published "
            "benchmarks you may be willing to share for academic purposes.\n\n"
            "The research has been approved by our institutional ethics board "
            "(Reference: UAE-U-IRB-2024-0441). All data would be used solely for "
            "non-commercial academic publication.\n\n"
            "Would your organisation be open to collaborating? I am also happy to "
            "share our findings with you prior to publication.\n\n"
            "Fatima Al-Rashidi\nResearch Analyst, UAE University"
        ),
        difficulty="medium",
        true_category="general_inquiry",
        true_urgency="low",
        true_action_items=[
            "Evaluate whether aggregated anonymised usage data can be shared for academic research",
            "Review ethics board approval UAE-U-IRB-2024-0441",
            "Assess legal and privacy implications of data sharing for Fatima Al-Rashidi's study",
            "Respond to collaboration request with decision and any conditions",
        ],
        true_summary=(
            "Research analyst at UAE University requests aggregated anonymised usage "
            "data for an IRB-approved academic study on AI adoption in Gulf enterprises. "
            "Offers to share findings pre-publication."
        ),
    ),

    # ════════════════════════════════════════════════════════════
    # COMPLAINT  (3 emails)
    # ════════════════════════════════════════════════════════════

    Email(
        email_id="e008",
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
        difficulty="hard",
        true_category="complaint",
        true_urgency="critical",
        true_action_items=[
            "Schedule call with VP of Customer Success within 24 hours",
            "Assign dedicated senior implementation engineer to BigRetail Co account today",
            "Prepare written remediation plan by end of week",
            "Initiate compensation discussion for onboarding delays",
            "Review SLA commitments for BigRetail Co $180k contract",
        ],
        true_summary=(
            "Enterprise account manager at BigRetail Co ($180k contract) formally "
            "escalates severe onboarding failures: 3 weeks behind with Black Friday "
            "8 days away. Demands VP call within 24h, dedicated engineer, remediation "
            "plan, and compensation discussion under contract termination threat."
        ),
    ),

    Email(
        email_id="e008b",
        sender_name="Kwame Asante",
        sender_role="Head of Operations",
        sender_email="k.asante@logistics-gh.com",
        subject="Data loss during platform migration — critical business records missing",
        body=(
            "To Whom It May Concern,\n\n"
            "During the platform migration your team performed on November 28th, "
            "approximately 14 months of historical shipment records (Feb 2023 – "
            "March 2024) have gone missing from our account (ID: LGH-44210).\n\n"
            "These records are not only critical for our day-to-day operations "
            "but are required for an ongoing customs audit that began this week. "
            "We have already informed the customs authority that the data will be "
            "provided by December 10th.\n\n"
            "This data loss appears to have been caused by your migration process. "
            "I am holding your organisation responsible and expect:\n\n"
            "1. Full recovery of all missing data by December 9th\n"
            "2. A written root cause analysis of how this occurred\n"
            "3. Confirmation that all other client data was unaffected\n"
            "4. A formal apology and compensation proposal\n\n"
            "Failure to recover the data will result in legal action.\n\n"
            "Kwame Asante\nHead of Operations, Ghana Logistics Ltd"
        ),
        difficulty="hard",
        true_category="complaint",
        true_urgency="critical",
        true_action_items=[
            "Escalate data loss on account LGH-44210 to engineering and data recovery team immediately",
            "Investigate migration performed November 28th as root cause of data loss",
            "Initiate full recovery of 14 months of shipment records by December 9th",
            "Prepare written root cause analysis of data loss",
            "Confirm whether other client data was affected by the migration",
            "Draft formal apology and compensation proposal for Kwame Asante",
        ],
        true_summary=(
            "Head of Operations at Ghana Logistics Ltd reports 14 months of critical "
            "shipment records lost during a Nov 28th platform migration, affecting an "
            "active customs audit with a Dec 10th deadline. Demands data recovery by "
            "Dec 9th, root cause analysis, and compensation under threat of legal action."
        ),
    ),

    Email(
        email_id="e008c",
        sender_name="Rebecca Nourse",
        sender_role="Customer",
        sender_email="r.nourse@gmail.com",
        subject="Still haven't received my refund after 3 weeks",
        body=(
            "Hello,\n\n"
            "I cancelled my subscription on November 10th and was told I would "
            "receive a refund of $89 within 7–10 business days. It has now been "
            "almost 3 weeks and I still have not received anything.\n\n"
            "I have contacted support twice already (tickets #RT-8821 and #RT-9043) "
            "but both were closed without resolution. I am very frustrated.\n\n"
            "Please process my refund immediately or I will dispute the charge "
            "with my bank.\n\n"
            "Rebecca Nourse"
        ),
        difficulty="easy",
        true_category="complaint",
        true_urgency="medium",
        true_action_items=[
            "Locate refund for Rebecca Nourse's cancelled subscription from November 10th",
            "Review previous support tickets RT-8821 and RT-9043",
            "Process $89 refund immediately",
            "Send refund confirmation to Rebecca Nourse",
        ],
        true_summary=(
            "Customer Rebecca Nourse cancelled her subscription on Nov 10th and has "
            "not received the promised $89 refund after 3 weeks and two unresolved "
            "support tickets. Threatens bank dispute."
        ),
    ),

    # ════════════════════════════════════════════════════════════
    # PARTNERSHIP  (3 emails)
    # ════════════════════════════════════════════════════════════

    Email(
        email_id="e009",
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
            "Best,\nPriya Nambiar\nHead of Partnerships, GreenLabs Co\n"
            "priya.n@greenlabs.co | +1 (212) 445-9901"
        ),
        difficulty="medium",
        true_category="partnership",
        true_urgency="medium",
        true_action_items=[
            "Review GreenLabs Co partnership proposal",
            "Schedule 30-minute introductory call with Priya Nambiar before end of month",
            "Evaluate API integration feasibility between GreenLabs ESG dashboard and platform",
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
        email_id="e009b",
        sender_name="Chen Wei",
        sender_role="VP Business Development",
        sender_email="chen.wei@cloudventures.cn",
        subject="OEM partnership — white-label integration for APAC market",
        body=(
            "Dear Partnerships Team,\n\n"
            "I represent CloudVentures, a cloud distribution company with "
            "established channels across 11 APAC markets including China, "
            "Singapore, and Australia (combined customer base: 340,000 SMBs).\n\n"
            "We are interested in an OEM / white-label arrangement to bundle "
            "your platform under our CloudSuite brand for the APAC SMB segment. "
            "Specifically, we would like to explore:\n\n"
            "1. White-label licensing terms and revenue share model\n"
            "2. Technical requirements for custom branding and SSO integration\n"
            "3. Dedicated APAC instance with local data residency (China, AU)\n"
            "4. Joint support and escalation model\n\n"
            "This arrangement could represent $2–4M ARR in year one. "
            "We are moving quickly and would like to hold a technical and "
            "commercial discovery call within the next 2 weeks.\n\n"
            "Chen Wei | VP Business Development | CloudVentures\n"
            "chen.wei@cloudventures.cn | WeChat: chenwei_cv"
        ),
        difficulty="hard",
        true_category="partnership",
        true_urgency="high",
        true_action_items=[
            "Evaluate OEM white-label partnership proposal from CloudVentures",
            "Prepare white-label licensing terms and revenue share model",
            "Assess technical requirements for custom branding and SSO integration",
            "Investigate feasibility of dedicated APAC instance with China and Australia data residency",
            "Define joint support and escalation model",
            "Schedule technical and commercial discovery call within 2 weeks",
        ],
        true_summary=(
            "VP BD at CloudVentures proposes an OEM/white-label arrangement to "
            "distribute under their CloudSuite brand across 11 APAC markets "
            "(340k SMBs), potentially $2–4M ARR year one. Requests discovery "
            "call within 2 weeks to discuss licensing, branding, data residency, "
            "and support model."
        ),
    ),

    Email(
        email_id="e009c",
        sender_name="Isabella Romano",
        sender_role="Head of Ecosystem",
        sender_email="i.romano@techaccelerator.eu",
        subject="Startup accelerator — technology partner opportunity",
        body=(
            "Hi,\n\n"
            "I run the technology partnership programme at EuroTech Accelerator, "
            "a pan-European startup accelerator with 180 portfolio companies.\n\n"
            "We're looking for one or two platform partners to offer discounted "
            "or free access to our startups in exchange for logo placement, "
            "co-branded content, and speaking slots at our quarterly demo days "
            "(attended by 800+ investors and founders).\n\n"
            "Would you be interested in discussing a partner arrangement? "
            "It's low commercial risk — primarily brand and community value.\n\n"
            "Isabella Romano\nHead of Ecosystem, EuroTech Accelerator"
        ),
        difficulty="easy",
        true_category="partnership",
        true_urgency="low",
        true_action_items=[
            "Evaluate EuroTech Accelerator partnership proposal for brand and community value",
            "Assess feasibility of discounted or free access for 180 portfolio startups",
            "Respond to Isabella Romano with decision or request for more details",
        ],
        true_summary=(
            "Head of Ecosystem at EuroTech Accelerator proposes a technology partner "
            "arrangement offering logo placement, co-branded content, and demo day "
            "speaking slots in exchange for discounted/free access for 180 portfolio startups."
        ),
    ),

    # ════════════════════════════════════════════════════════════
    # COMPLIANCE (3 emails)
    # ════════════════════════════════════════════════════════════

    Email(
        email_id="e010a",
        sender_name="Sarah Jenkins",
        sender_role="General Counsel",
        sender_email="s.jenkins@bigcorp.com",
        subject="Notice of Data Processing Amendment (DPA) Update — Urgent Compliance Review",
        body=(
            "Dear Compliance Team,\n\n"
            "Pursuant to our Master Service Agreement (MSA) dated January 12th, 2023, "
            "BigCorp is issuing an updated Data Processing Amendment (DPA) to align "
            "with the latest EU-US Data Privacy Framework (DPF) and new UK GDPR "
            "requirements.\n\n"
            "You are required to review the attached 42-page DPA and provide signed "
            "acceptance by April 30th. Failure to execute this update will result "
            "in a breach of the Data Protection Clause (Section 14.2) of our MSA.\n\n"
            "Specifically, please verify your sub-processor list in Annex III and "
            "confirm that all international transfers are now governed by the 2021 "
            "SCCs as incorporated in this new version.\n\n"
            "This is a non-negotiable legal requirement. Please confirm receipt "
            "immediately.\n\n"
            "Sarah Jenkins\nGeneral Counsel, BigCorp"
        ),
        difficulty="hard",
        true_category="compliance",
        true_urgency="critical",
        true_action_items=[
            "Review updated Data Processing Amendment (DPA) from BigCorp",
            "Align DPA with EU-US Data Privacy Framework and UK GDPR requirements",
            "Verify sub-processor list in Annex III of the new DPA",
            "Confirm international transfers use 2021 SCCs",
            "Provide signed acceptance of DPA by April 30th",
            "Confirm receipt of notice to Sarah Jenkins immediately",
        ],
        true_summary=(
            "General Counsel at BigCorp issues a 42-page DPA update required by "
            "April 30th for regulatory compliance (GDPR/DPF). Non-compliance "
            "threatens a breach of contract. Requires sub-processor verification "
            "and immediate confirmation of receipt."
        ),
    ),

    Email(
        email_id="e010b",
        sender_name="Marcus Thorne",
        sender_role="Data Protection Officer",
        sender_email="m.thorne@healthtrust.co.uk",
        subject="Subject Access Request (SAR) — Case #SAR-2024-9912",
        body=(
            "Hello,\n\n"
            "We have received a formal Subject Access Request (SAR) from a former "
            "employee, Jane Doe (ID: JD-9912), who exercised her rights under "
            "Article 15 of the GDPR. As you are a data processor for our HR "
            "management system, we require your assistance in fulfilling this "
            "request.\n\n"
            "Please provide a portable, machine-readable export of all personally "
            "identifiable information (PII) related to Jane Doe stored in your "
            "production and backup databases within 72 hours. This must include "
            "access logs, profile metadata, and any encrypted blobs that belong "
            "to her account.\n\n"
            "Please upload the data to our secure SFTP vault and notify us once "
            "it is available.\n\n"
            "Marcus Thorne\nData Protection Officer, HealthTrust"
        ),
        difficulty="medium",
        true_category="compliance",
        true_urgency="high",
        true_action_items=[
            "Fulfill Subject Access Request (SAR) for Jane Doe (ID: JD-9912)",
            "Export all PII from production and backup databases in machine-readable format",
            "Include access logs, profile metadata, and encrypted blobs in the export",
            "Upload data to HealthTrust secure SFTP vault within 72 hours",
            "Notify Marcus Thorne upon completion of the data upload",
        ],
        true_summary=(
            "DPO at HealthTrust requires assistance with a formal Subject Access "
            "Request (SAR) under GDPR Article 15. Requests all PII for a former "
            "employee within 72 hours, to be uploaded via secure SFTP."
        ),
    ),

    Email(
        email_id="e010c",
        sender_name="Legal Bot",
        sender_role="Compliance Automated System",
        sender_email="no-reply@compliance-check.com",
        subject="Annual Certification of Insurance (COI) — Request for Renewal",
        body=(
            "Dear Partner,\n\n"
            "Our records indicate that your Certification of Insurance (COI) on file "
            "is set to expire in 45 days. To remain in compliance with our vendor "
            "risk management policy, please upload a renewed COI to the partner portal.\n\n"
            "Requirements:\n"
            "  - General Liability: $2M minimum\n"
            "  - Cyber/Data Breach: $5M minimum\n\n"
            "If you have any questions, please contact your account manager.\n\n"
            "Regards,\nCompliance Automated System"
        ),
        difficulty="easy",
        true_category="compliance",
        true_urgency="low",
        true_action_items=[
            "Renew Certification of Insurance (COI) before expiration in 45 days",
            "Ensure General Liability is $2M minimum and Cyber is $5M minimum",
            "Upload renewed COI to the partner portal",
            "Contact account manager if clarification is needed",
        ],
        true_summary=(
            "Automated system requests a renewal of the Certification of Insurance (COI) "
            "within 45 days to maintain vendor compliance. Specifies $2M General and "
            "$5M Cyber liability minimums."
        ),
    ),
]


def get_email_by_id(email_id: str) -> Email | None:
    return next((e for e in EMAILS if e.email_id == email_id), None)


def get_emails_for_task(task_type: str) -> List[Email]:
    return EMAILS


def get_email_by_index(index: int) -> Email:
    return EMAILS[index % len(EMAILS)]


def get_emails_by_difficulty(difficulty: str) -> List[Email]:
    return [e for e in EMAILS if e.difficulty == difficulty]


def get_emails_by_category(category: str) -> List[Email]:
    return [e for e in EMAILS if e.true_category == category]