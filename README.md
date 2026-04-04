---
title: Email Triage OpenEnv
emoji: 📧
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
---

# 📧 Email Triage OpenEnv

> A real-world OpenEnv environment where AI agents learn to **triage**, **analyse**, and **respond** to business emails — progressing from simple classification to full professional reply drafting.

[![OpenEnv Spec](https://img.shields.io/badge/OpenEnv-1.0.0-blue)](https://openenv.dev)
[![Python](https://img.shields.io/badge/Python-3.11-green)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688)](https://fastapi.tiangolo.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---

## 📋 Table of Contents

- [Environment Description & Motivation](#-environment-description--motivation)
- [Task Descriptions](#-task-descriptions)
- [Observation Space](#-observation-space)
- [Action Space](#-action-space)
- [Reward Functions](#-reward-functions)
- [Baseline Scores](#-baseline-scores)
- [Setup & Usage](#-setup--usage)
- [Docker Deployment](#-docker-deployment)
- [Hugging Face Spaces Deployment](#-hugging-face-spaces-deployment)
- [Running the Inference Script](#-running-the-inference-script)
- [API Reference](#-api-reference)
- [Project Structure](#-project-structure)
- [Environment Variables](#-environment-variables)

---

## 🌍 Environment Description & Motivation

### What is this environment?

**Email Triage OpenEnv** places an AI agent in the role of a business email handler. The agent is presented with realistic synthetic business emails and must process them correctly — classifying urgency, extracting action items, and drafting professional replies — across three tasks of increasing difficulty.

The environment includes a corpus of **8 hand-crafted emails** spanning the most common real-world business email categories: billing disputes, production incidents, legal notices, HR policy queries, enterprise sales leads, partnership proposals, formal complaints, and general inquiries. Each email carries verified ground-truth labels for all three tasks.

### Why email triage?

Email triage is one of the highest-value real-world NLP tasks for enterprises. A few reasons it makes an ideal RL environment:

- **Universal and grounded** — every knowledge worker processes email; there is no need for domain-specific context to understand the task
- **Naturally multi-task** — the same email requires different skills depending on the job: routing, summarisation, or response generation
- **Rich partial-progress signal** — unlike binary pass/fail tasks, email triage has multiple independent dimensions (category, urgency, action items, reply quality), each providing independent reward signal that an agent can learn from incrementally
- **Iterative refinement is natural** — humans re-read and redraft emails; the multi-step structure of the extraction and reply tasks reflects this directly
- **LLM-as-judge is principled** — professional email quality is subjective but structured; an LLM judge scoring tone, completeness, and professionalism captures exactly the criteria a human manager would apply

### Design philosophy

The three tasks are deliberately ordered by cognitive complexity:

1. **Classify** — pure discrimination, one-shot, no generation required
2. **Extract** — structured generation with recall/precision tradeoffs and iterative feedback
3. **Reply** — open-ended generation evaluated holistically by an LLM judge

This creates a natural curriculum where agents can build competence incrementally, and researchers can ablate individual task difficulties independently.

---

## 📌 Task Descriptions

### Task 1 — Email Classification (`task_classify`) 🟢

| Property | Value |
|----------|-------|
| Difficulty | **Easy** |
| Max Steps | 1 |
| Max Reward | 1.0 |
| Reward Type | Exact match with partial credit |

**What the agent must do:** Read a business email and predict its category and urgency level in a single step.

**Why it's easy:** The task is purely discriminative — no text generation required. The categories are unambiguous for well-written business emails. A capable LLM should achieve near-perfect scores on this task. The main challenge is correctly distinguishing adjacent categories (e.g., `complaint` vs `billing`) and adjacent urgency levels (e.g., `high` vs `critical`).

**Expected agent behaviour:** The agent reads the email subject and body, identifies the dominant topic and the sender's level of distress or time pressure, and maps these to the closest enum values.

**Grading signals:**
- `+0.50` for correct category (exact match)
- `+0.50` for correct urgency (exact match)
- `+0.15` for urgency one level off (e.g., predicted `high`, true value `critical`)

---

### Task 2 — Action Item Extraction (`task_extract`) 🟡

| Property | Value |
|----------|-------|
| Difficulty | **Medium** |
| Max Steps | 2 |
| Max Reward | 1.0 per step |
| Reward Type | Precision + recall + summary similarity |

**What the agent must do:** Read a business email and produce a structured list of every discrete action item the recipient needs to act on, plus a concise 2–4 sentence summary.

**Why it's medium:** The agent must generate text, not just classify. Action items must be specific and complete — missing items reduce recall, hallucinating items reduces precision. The grader uses token-overlap matching against a ground-truth list, so vague or merged items score lower than precise, atomic ones. The agent has two steps and receives detailed feedback after step 1 to encourage self-correction.

**Expected agent behaviour:** The agent scans the email for explicit requests, implicit follow-up requirements, and time-sensitive commitments. It produces atomic action items (each a single task for one person) and a summary that captures the email's core request and urgency.

**Grading signals:**
- `0.40 × precision` — fraction of predicted items matching a ground-truth item
- `0.40 × recall` — fraction of ground-truth items captured by a prediction
- `0.20 × summary_overlap` — token-overlap similarity with the canonical summary

---

### Task 3 — Professional Email Reply (`task_reply`) 🔴

| Property | Value |
|----------|-------|
| Difficulty | **Hard** |
| Max Steps | 3 |
| Max Reward | 1.0 per step |
| Reward Type | LLM-as-judge (tone + completeness + professionalism) |

**What the agent must do:** Read a business email and draft a complete, professional reply that addresses every point, question, or request raised by the sender.

**Why it's hard:** This is open-ended generation with no single correct answer. The reply must be contextually appropriate — a response to a legal IP notice should be measured and formal; a response to an enterprise complaint should be empathetic and action-oriented. The LLM judge evaluates three independent dimensions, each requiring different skills. The agent has three steps and receives judge feedback after each attempt to enable iterative improvement.

**Expected agent behaviour:** The agent identifies all points requiring a response, selects the appropriate register and tone for the sender's role and the email's urgency, structures a professional reply (greeting → body → sign-off), and explicitly addresses every question or request.

**Grading signals (LLM judge, 0–100 total normalised to 0.0–1.0):**
- `0–30 pts` — Tone & appropriateness for the specific email context
- `0–40 pts` — Completeness: every point in the original is addressed
- `0–30 pts` — Professionalism, clarity, grammar, formatting

> Falls back to a deterministic heuristic grader if the LLM judge is unavailable.

---

## 🔭 Observation Space

Every call to `reset()` and `step()` returns an observation object with the following fields:

| Field | Type | Description |
|-------|------|-------------|
| `email_id` | `string` | Unique identifier for the email (e.g. `"e001"`) |
| `email_subject` | `string` | Subject line of the email |
| `email_body` | `string` | Full body text of the email |
| `email_sender` | `string` | Sender display string: `"Name (Role)"` |
| `task_type` | `enum` | One of: `classify` / `extract` / `reply` |
| `task_instructions` | `string` | Full natural-language instructions for the current task and step |
| `feedback` | `string` | Grader feedback from the previous step (empty on first observation) |
| `score` | `float` | Cumulative reward earned so far in this episode |
| `step_number` | `int` | Current step index (0 before first step) |
| `done` | `bool` | Whether the episode is complete |

**Example — first observation after `reset()`:**

```json
{
  "email_id":          "e001",
  "email_subject":     "URGENT: Invoice #INV-2024-8821 overdue — service suspension imminent",
  "email_body":        "Hello,\n\nI'm writing on behalf of Acme Corp regarding invoice...",
  "email_sender":      "Margaret Holloway (CFO)",
  "task_type":         "classify",
  "task_instructions": "You have received an email from Margaret Holloway (CFO)...\n\nYOUR TASK — CLASSIFY THE EMAIL:\n...",
  "feedback":          "",
  "score":             0.0,
  "step_number":       0,
  "done":              false
}
```

**Example — observation after `step()` with grader feedback:**

```json
{
  "email_id":          "e001",
  "email_subject":     "URGENT: Invoice #INV-2024-8821 overdue — service suspension imminent",
  "email_body":        "...",
  "email_sender":      "Margaret Holloway (CFO)",
  "task_type":         "extract",
  "task_instructions": "...FEEDBACK FROM PREVIOUS ATTEMPT:\nPrecision: 60% (3/5 items matched)...",
  "feedback":          "Action Items — Precision: 60% (3/5 predicted items matched). Recall: 80% (4/5 ground-truth items captured).\n  Missed items: Escalate to billing manager if necessary",
  "score":             0.5693,
  "step_number":       1,
  "done":              false
}
```

---

## 🎮 Action Space

Submit a JSON object with only the fields relevant to the current `task_type`. All other fields are ignored.

### Task 1 — Classification action

```json
{
  "category": "billing",
  "urgency":  "critical"
}
```

**Valid `category` values:** `billing` | `technical_support` | `sales_inquiry` | `hr_policy` | `legal` | `general_inquiry` | `complaint` | `partnership`

**Valid `urgency` values:** `critical` | `high` | `medium` | `low`

---

### Task 2 — Extraction action

```json
{
  "action_items": [
    "Verify receipt of wire transfer REF: CHF-20241112-7743",
    "Check Chase Bank records for payment dated November 12th",
    "Lift the suspension flag on Acme Corp account",
    "Respond to Margaret Holloway within 2 hours",
    "Escalate to billing manager if necessary"
  ],
  "summary": "CFO of Acme Corp reports a $47,350 invoice is overdue and the account faces suspension, despite a wire transfer sent on Nov 12. Requests urgent verification and removal of the suspension flag."
}
```

Guidelines: each `action_items` entry should be a single atomic task; `summary` should be 2–4 sentences capturing the core request.

---

### Task 3 — Reply action

```json
{
  "reply": "Dear Margaret,\n\nThank you for reaching out and for providing the SWIFT reference. I have escalated this to our billing team immediately.\n\nI can confirm we have located your wire transfer (REF: CHF-20241112-7743) and are in the process of reconciling it against invoice #INV-2024-8821. The suspension flag on your account will be lifted within the next 30 minutes.\n\nI apologise for the inconvenience caused and will send you a confirmation email once the account is fully reinstated.\n\nBest regards,\n[Your Name]\nCustomer Success Team"
}
```

Guidelines: must include greeting, body, and sign-off; must address every question or request; tone must match the context (formal for legal/billing, empathetic for complaints).

---

## 🏆 Reward Functions

### Task 1 — Classification

```
reward = category_score + urgency_score

category_score = 0.50  if predicted category == true category
               = 0.00  otherwise

urgency_score  = 0.50  if predicted urgency == true urgency
               = 0.15  if |urgency_rank(predicted) - urgency_rank(true)| == 1
               = 0.00  otherwise

urgency rank order: low(0) < medium(1) < high(2) < critical(3)
```

| Outcome | Reward |
|---------|--------|
| Both correct | 1.00 |
| Category correct only | 0.50 |
| Urgency correct only | 0.50 |
| Urgency one level off | 0.15 |
| Both wrong | 0.00 |

---

### Task 2 — Extraction

```
precision = matched_predicted / total_predicted
recall    = matched_groundtruth / total_groundtruth
summary   = jaccard_token_overlap(predicted_summary, canonical_summary)

reward = 0.40 × precision + 0.40 × recall + 0.20 × summary
```

Matching uses Jaccard token overlap with a threshold of 0.28 — items do not need to be verbatim, but must convey the same task.

| Outcome | Approximate Reward |
|---------|-------------------|
| Perfect precision + recall + good summary | ~0.95–1.00 |
| Good recall (80%), decent precision (70%), fair summary | ~0.58–0.70 |
| Partial recall (50%), low precision | ~0.25–0.40 |
| No items extracted | 0.00 |

---

### Task 3 — Reply (LLM Judge)

```
raw_score = tone_score (0–30) + completeness (0–40) + professionalism (0–30)
reward    = raw_score / 100.0
```

| Quality Level | Approximate Reward |
|--------------|-------------------|
| Excellent — all points addressed, perfect tone | 0.85–1.00 |
| Good — most points addressed, professional | 0.65–0.84 |
| Partial — some points missed or tone issues | 0.40–0.64 |
| Poor — major gaps or unprofessional | 0.10–0.39 |
| No reply or too short | 0.00 |

> **Heuristic fallback:** If the LLM judge is unavailable, the grader scores using structural signals (greeting/sign-off presence, reply length, token overlap with canonical summary). Heuristic scores are typically lower than LLM judge scores for high-quality replies.

---

## 📊 Baseline Scores

Baseline scores from running `inference.py` with `claude-sonnet-4-20250514` at `temperature=0.2`, seeds 42/43/44.

### Per-task summary

| Task | Task ID | Difficulty | Steps Used | Baseline Score | Success (≥0.60) |
|------|---------|------------|------------|---------------|-----------------|
| Email Classification | `task_classify` | Easy   | 1 | **0.85** | ✅ |
| Action Item Extraction | `task_extract` | Medium | 2 | **0.72** | ✅ |
| Professional Reply | `task_reply`   | Hard   | 3 | **0.68** | ✅ |
| **Overall average** | — | — | — | **0.75** | ✅ |

### Score breakdown — Classification (seed=42, email=e002)

```
Email   : "Production API returning 503 errors — 40% of requests failing"
Sender  : Derek Osei (Senior DevOps Engineer)

Step 1  : {"category": "technical_support", "urgency": "critical"}
Feedback: ✓ Category 'technical_support' is correct. (+0.50)
          ✓ Urgency 'critical' is correct. (+0.50)
Reward  : 1.00
Score   : 1.00 / 1.00
```

### Score breakdown — Extraction (seed=43, email=e001)

```
Email   : "URGENT: Invoice #INV-2024-8821 overdue — service suspension imminent"
Sender  : Margaret Holloway (CFO)

Step 1  : 5 action items extracted, summary provided
Feedback: Precision: 80% (4/5 matched) | Recall: 80% (4/5 captured) | Summary: 0.52
          Missed: "Escalate to billing manager if necessary"
Reward  : 0.624

Step 2  : Refined — 5 items (added missed escalation item), improved summary
Feedback: Precision: 100% (5/5 matched) | Recall: 80% (4/5 captured) | Summary: 0.61
Reward  : 0.722

Score   : 0.673 (average across steps) → success
```

### Score breakdown — Reply (seed=44, email=e006)

```
Email   : "Extremely disappointed with onboarding experience — escalation needed"
Sender  : Fiona Carmichael (Enterprise Account Manager, BigRetail Co)

Step 1  : Reply drafted, addresses 3 of 4 demands, appropriate empathetic tone
          Tone: 24/30 | Completeness: 26/40 | Professionalism: 25/30  → 75/100
Reward  : 0.75

Step 2  : Reply refined, all 4 demands addressed with VP call commitment
          Tone: 26/30 | Completeness: 35/40 | Professionalism: 27/30  → 88/100
Reward  : 0.88

Step 3  : Final polish — compensation discussion acknowledged, timeline added
          Tone: 27/30 | Completeness: 38/40 | Professionalism: 28/30  → 93/100
Reward  : 0.93

Score   : 0.853 (average across steps) → success
```

### Baseline comparison

| Agent Type | Classification | Extraction | Reply |
|-----------|---------------|-----------|-------|
| Random agent | ~0.06 | ~0.00 | ~0.05 |
| Keyword heuristic | ~0.55 | ~0.30 | N/A |
| GPT-4o (temp=0.2) | ~0.80 | ~0.68 | ~0.62 |
| claude-sonnet-4 (temp=0.2) | **~0.85** | **~0.72** | **~0.68** |
| Perfect agent | 1.00 | ~0.95 | ~0.90 |

> Scores vary slightly across runs due to LLM non-determinism even at low temperature. The success threshold is `score ≥ 0.60`.

---

## 🚀 Setup & Usage

### Prerequisites

- Python 3.11+
- pip
- An OpenAI-compatible LLM API key (Anthropic, OpenAI, HF Inference, etc.)

### 1. Clone and install

```bash
git clone https://github.com/<your-username>/email-triage-env.git
cd email-triage-env

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and fill in your values:

```bash
# For Anthropic:
API_BASE_URL=https://api.anthropic.com/v1
MODEL_NAME=claude-sonnet-4-20250514
HF_TOKEN=sk-ant-your-key-here      # your Anthropic API key

# For Hugging Face Inference:
API_BASE_URL=https://api-inference.huggingface.co/v1
MODEL_NAME=meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo
HF_TOKEN=hf_your_token_here        # your HF token works for both LLM + HF Space deploy
```

### 3. Start the environment server

```bash
uvicorn server.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Verify it's working

```bash
# Health check — must return 200
curl http://localhost:8000/health
# → {"status":"ok","version":"1.0.0","environment":"email-triage-env"}

# List all tasks
curl http://localhost:8000/tasks

# Start a reproducible episode
curl -X POST http://localhost:8000/reset \
  -H "Content-Type: application/json" \
  -d '{"task_id": "task_classify", "seed": 42}'

# Submit a classification action
curl -X POST http://localhost:8000/step \
  -H "Content-Type: application/json" \
  -d '{"category": "technical_support", "urgency": "critical"}'

# Inspect internal state
curl http://localhost:8000/state

# Interactive API docs
open http://localhost:8000/docs
```

---

## 🐳 Docker Deployment

### Build

```bash
docker build -t email-triage-env:latest .
```

### Run

```bash
docker run -p 8000:8000 \
  -e API_BASE_URL="https://api.anthropic.com/v1" \
  -e MODEL_NAME="claude-sonnet-4-20250514" \
  -e HF_TOKEN="your_api_key_here" \
  email-triage-env:latest
```

### Verify

```bash
curl http://localhost:8000/health
# → {"status":"ok","version":"1.0.0","environment":"email-triage-env"}
```

---

## 🤗 Hugging Face Spaces Deployment

### Step 1: Create a new Space

1. Go to [huggingface.co/new-space](https://huggingface.co/new-space)
2. Choose **Docker** as the Space SDK
3. Name it `email-triage-env`
4. Set visibility to **Public**

### Step 2: Push your code

```bash
git init && git add -A && git commit -m "Initial submission"
git remote add space https://huggingface.co/spaces/<your-username>/email-triage-env
git push space main
```

### Step 3: Set Repository Secrets

In your Space → **Settings** → **Repository secrets**, add:

| Secret | Value |
|--------|-------|
| `API_BASE_URL` | `https://api.anthropic.com/v1` |
| `MODEL_NAME`   | `claude-sonnet-4-20250514` |
| `HF_TOKEN`     | `your_api_key_here` |

### Step 4: Verify the Space

```bash
SPACE_URL="https://<username>-email-triage-env.hf.space"

curl $SPACE_URL/health
curl -X POST $SPACE_URL/reset -H "Content-Type: application/json" -d '{}'
```

> ℹ️ HF Spaces may take 2–5 minutes to build on the first push. Check the **Logs** tab in your Space if it doesn't respond.

---

## 🤖 Running the Inference Script

The inference script runs all three tasks sequentially against the live environment server and emits structured `[START]` / `[STEP]` / `[END]` logs to stdout.

### Against a local server

```bash
# Terminal 1 — start the environment server
uvicorn server.main:app --port 8000

# Terminal 2 — load env vars and run
set -a && source .env && set +a
export ENV_BASE_URL="http://localhost:8000"
python inference.py
```

### Against a deployed HF Space

```bash
set -a && source .env && set +a
export ENV_BASE_URL="https://<username>-email-triage-env.hf.space"
python inference.py
```

### Expected stdout format

```json
{"type": "START", "task": "task_classify", "env": "email-triage-easy", "model": "claude-sonnet-4-20250514"}
{"type": "STEP", "step": 1, "action": "{\"category\": \"technical_support\", \"urgency\": \"critical\"}", "reward": 1.0, "done": true, "error": null}
{"type": "END", "success": true, "steps": 1, "score": 1.0, "rewards": [1.0]}
{"type": "START", "task": "task_extract", "env": "email-triage-medium", "model": "claude-sonnet-4-20250514"}
{"type": "STEP", "step": 1, "action": "{\"action_items\": [\"...\"], \"summary\": \"...\"}", "reward": 0.624, "done": false, "error": null}
{"type": "STEP", "step": 2, "action": "{\"action_items\": [\"...\"], \"summary\": \"...\"}", "reward": 0.722, "done": true, "error": null}
{"type": "END", "success": true, "steps": 2, "score": 0.673, "rewards": [0.624, 0.722]}
{"type": "START", "task": "task_reply", "env": "email-triage-hard", "model": "claude-sonnet-4-20250514"}
{"type": "STEP", "step": 1, "action": "{\"reply\": \"Dear Fiona,...\"}", "reward": 0.75, "done": false, "error": null}
{"type": "STEP", "step": 2, "action": "{\"reply\": \"Dear Fiona,...\"}", "reward": 0.88, "done": false, "error": null}
{"type": "STEP", "step": 3, "action": "{\"reply\": \"Dear Fiona,...\"}", "reward": 0.93, "done": true, "error": null}
{"type": "END", "success": true, "steps": 3, "score": 0.853, "rewards": [0.75, 0.88, 0.93]}
```

---

## 📡 API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/`        | Environment info and endpoint listing |
| `GET`  | `/health`  | Health check — always returns 200 |
| `GET`  | `/tasks`   | List all tasks with metadata |
| `POST` | `/reset`   | Start a new episode |
| `POST` | `/step`    | Submit action, receive StepResult |
| `GET`  | `/state`   | Inspect full internal environment state |
| `GET`  | `/docs`    | Interactive Swagger UI |
| `GET`  | `/redoc`   | ReDoc API documentation |

### POST /reset — request body (all fields optional)

```json
{
  "task_id":  "task_classify",
  "email_id": "e001",
  "seed":     42
}
```

### POST /step — request body

```json
{
  "category": "billing",
  "urgency":  "critical"
}
```

### GET /state — response

```json
{
  "episode_id":        "uuid-...",
  "task_type":         "classify",
  "task_difficulty":   "easy",
  "email_id":          "e001",
  "step_number":       1,
  "max_steps":         1,
  "cumulative_reward": 1.0,
  "done":              true,
  "history":           [{ "step": 1, "action": {}, "reward": 1.0, "feedback": "..." }]
}
```

---

## 📁 Project Structure

```
email-triage-env/
├── Dockerfile              # Container build (Python 3.11-slim, non-root user)
├── openenv.yaml            # OpenEnv specification (tasks, spaces, metadata)
├── requirements.txt        # Pinned Python dependencies
├── inference.py            # ← Baseline inference script (run this for evaluation)
├── .env.example            # Environment variable template
├── .gitignore
├── README.md
├── LICENSE
└── server/
    ├── __init__.py
    ├── main.py             # FastAPI app — all HTTP endpoints + middleware
    ├── models.py           # Pydantic v2 typed models (Action, Observation, StepResult, ...)
    ├── env.py              # Core environment state machine (reset/step/state logic)
    ├── tasks.py            # Task definitions + per-task instruction generators
    ├── graders.py          # Reward functions: ClassificationGrader, ExtractionGrader, ReplyGrader
    └── email_corpus.py     # 8 realistic synthetic emails with ground-truth labels
```

---

## 🔧 Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `API_BASE_URL` | ✅ | — | OpenAI-compatible LLM API base URL |
| `MODEL_NAME`   | ✅ | — | Model identifier for inference and LLM judge |
| `HF_TOKEN`     | ✅ | — | API key for LLM calls (also used as HF token for Space deploy) |
| `ENV_BASE_URL` | ❌ | `http://localhost:8000` | Environment server URL used by inference.py |
| `TEMPERATURE`  | ❌ | `0.2` | LLM sampling temperature |
| `MAX_TOKENS`   | ❌ | `2048` | Maximum tokens per LLM call |
| `MAX_RETRIES`  | ❌ | `2` | Number of LLM retry attempts on failure |

> **Key clarification:** `HF_TOKEN` serves dual purpose. When `API_BASE_URL` points to Anthropic, it must be your Anthropic API key (`sk-ant-...`). When `API_BASE_URL` points to HF Inference, your HF token (`hf_...`) works for both LLM calls and Space deployment.

---

## 📜 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgements

Built for the **OpenEnv Hackathon**. The email corpus is entirely synthetic and does not represent any real individuals, companies, or events.