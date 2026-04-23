# SignalForge

SignalForge is a production-oriented B2B outbound intelligence system for Tenacious Consulting. It turns structured hiring and market signals into grounded outreach, then carries the thread through qualification and booking without inventing facts.

The current system is intentionally built around one discipline: `prove before you persuade`.

## Executive Summary

SignalForge currently provides:

- a deterministic enrichment pipeline over local synthetic data
- structured hiring and competitor-gap briefs
- a confidence engine that controls tone
- an OpenRouter-backed email generation layer with claim validation
- a FastAPI backend for single-run and batch evaluation
- adversarial probes for business-risk-focused evaluation

The repo is designed to be evaluation-ready before it is automation-heavy.

## Product Goal

For Tenacious, the job is not to blast generic outbound. The job is to identify credible hiring pressure, frame a relevant talent or advisory angle, and earn a discovery call with a technical buyer such as a CTO or VP Engineering.

SignalForge is optimized around:

- signal grounding
- confidence-aware messaging
- hallucination resistance
- traceability
- low operating cost per prospect

## System Architecture

```text
                        +-----------------------+
                        |   Local Datasets      |
                        |  crunchbase_sample    |
                        |  layoffs.csv          |
                        +-----------+-----------+
                                    |
                                    v
                    +---------------+---------------+
                    |    Deterministic Enrichment   |
                    |  CrunchbaseTool               |
                    |  layoffs loader               |
                    |  peer selection               |
                    +---------------+---------------+
                                    |
                   +----------------+----------------+
                   |                                 |
                   v                                 v
        +----------+-----------+         +-----------+----------+
        | Hiring Signal Brief  |         | Competitor Gap Brief |
        | funding              |         | peer AI maturity     |
        | job velocity         |         | top practices        |
        | layoffs              |         | benchmark summary    |
        | AI maturity          |         +-----------+----------+
        +----------+-----------+                     |
                   |                                 |
                   +----------------+----------------+
                                    |
                                    v
                       +------------+------------+
                       | Confidence Engine       |
                       | low / medium / high     |
                       +------------+------------+
                                    |
                                    v
                     +--------------+---------------+
                     | LLM Email Generation Layer   |
                     | OpenRouter client            |
                     | confidence-aware prompt      |
                     | claim validator              |
                     | deterministic fallback       |
                     +--------------+---------------+
                                    |
                                    v
                     +--------------+---------------+
                     | Orchestrator / API Layer     |
                     | /run-prospect                |
                     | /run-prospect/scenarios      |
                     | /run-prospect/batch          |
                     +--------------+---------------+
                                    |
                                    v
                     +--------------+---------------+
                     | Outputs / Evaluation         |
                     | JSON artifacts               |
                     | JSONL traces                 |
                     | adversarial probe library    |
                     +------------------------------+
```

## Repository Structure

```text
agent/
  core/         orchestration, confidence, routing
  signals/      hiring signals, AI maturity, competitor gap logic
  tools/        local data loaders and deterministic enrichers
  llm/          OpenRouter client and email generation
  guards/       claim validation and outbound safety checks
  channels/     email, sms, voice channel adapters and stubs
  crm/          HubSpot-facing mapping and logging stubs
  calendar/     booking link adapter
  utils/        config, tracing, logging

backend/
  routes/       FastAPI endpoints
  services/     run orchestration and API-facing service layer
  schemas.py    request and response contracts

frontend/       React + Vite dashboard for signals, email output, and peers
data/           local synthetic prospect and layoffs data
eval/           adversarial scenarios and evaluation harness
probes/         production-grade probe library and failure analysis
scripts/        local execution helpers
tests/          regression and LLM-layer tests
outputs/        generated artifacts for latest and scenario runs
logs/           append-only JSONL run logs
```

## Core Runtime Flow

The active working path is:

`Input -> Enrichment -> Hiring Signal Brief -> Competitor Gap Brief -> Confidence -> LLM Email -> Claim Validation -> Reply -> Qualification -> Booking`

Default synthetic prospect:

- `Northstar Lending`

Default API response shape:

```json
{
  "company": "Northstar Lending",
  "hiring_signal_brief": {},
  "competitor_gap_brief": {},
  "email": {
    "subject": "string",
    "body": "string"
  },
  "confidence": "low|medium|high",
  "trace_id": "string"
}
```

## Technology Stack

### Backend

- `FastAPI` for the API surface
- `Pydantic v2` for typed request and response contracts
- `Uvicorn` for local serving
- `Python 3.12+`

### Frontend

- `React` with `Vite`
- `TanStack Query` for async data fetching and cache control
- `Tailwind CSS` for the UI system
- `Lucide React` for iconography
- lightweight custom data visualization for peer comparison

### Intelligence Layer

- deterministic enrichment over local datasets
- rule-based AI maturity scoring
- confidence-aware orchestration
- `OpenRouter` as the LLM gateway
- `deepseek/deepseek-chat` as the default generation model
- `qwen/qwen3-32b` as fallback

### Observability and Evaluation

- JSON artifacts in `outputs/`
- JSONL run logs in `logs/`
- `Langfuse` hooks for trace and cost instrumentation
- adversarial scenario runner in `eval/`
- business-risk-focused probe pack in `probes/`

### Planned / Stubbed Integrations

- `Resend` for outbound email delivery
- `HubSpot` for CRM logging
- `Cal.com` for booking links
- `Africa's Talking` for SMS

These keys can be configured now, but not all integrations are live in the request path yet.

## Design Principles

SignalForge follows a few hard rules:

- never fabricate signals
- never overstate weak evidence
- prefer asking over asserting when confidence is low
- keep deterministic logic where deterministic logic is enough
- make every prospect run inspectable after the fact

This is especially important for Tenacious, where one wrong hiring claim can kill a high-value thread instantly.

## How Confidence Works

SignalForge reduces the structured brief into a global confidence label:

- `high`: strong, recent, internally consistent signals
- `medium`: some evidence, but not enough for aggressive claims
- `low`: incomplete, stale, or contradictory signals

Confidence controls prompt tone:

- `high` -> assertive and specific
- `medium` -> careful and directional
- `low` -> exploratory and question-led

## Claim Validation

Every LLM-generated email is checked against the available structured claims.

Current protections include:

- only using claims present in the generated claim catalog
- rejecting unsupported numeric language
- regeneration in strict mode if a mismatch is detected
- deterministic fallback if claim validation still fails

This is the main anti-hallucination boundary in the current architecture.

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/nebiyuephrata/SignalForge.git
cd SignalForge
```

### 2. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Minimum useful configuration:

```env
APP_NAME=SignalForge
APP_ENV=development
APP_HOST=127.0.0.1
APP_PORT=8000
LOG_LEVEL=INFO

OPENROUTER_API_KEY=your_openrouter_key
OPENROUTER_MODEL=deepseek/deepseek-chat
OPENROUTER_FALLBACK_MODEL=qwen/qwen3-32b
OPENROUTER_TIMEOUT_SECONDS=30
OPENROUTER_MAX_TOKENS=300
```

Optional integrations:

- `LANGFUSE_PUBLIC_KEY`
- `LANGFUSE_SECRET_KEY`
- `LANGFUSE_HOST`
- `RESEND_API_KEY`
- `HUBSPOT_API_KEY`
- `CALCOM_API_KEY`
- `AFRICAS_TALKING_API_KEY`

## Running the Backend

Start the API locally:

```bash
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

Health check:

```bash
curl -sS http://127.0.0.1:8000/health
```

## Running the Frontend

From the `frontend/` directory:

```bash
cp .env.example .env
npm install
npm run dev
```

The dashboard runs at:

```text
http://127.0.0.1:5173
```

If your backend is not on the default port, set:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

## API Endpoints

### Run the default prospect

```bash
curl -sS -X POST http://127.0.0.1:8000/run-prospect
```

### Run a named adversarial scenario

```bash
curl -sS -X POST http://127.0.0.1:8000/run-prospect \
  -H 'Content-Type: application/json' \
  -d '{"scenario_name":"weak_confidence"}'
```

### Run a direct company override

```bash
curl -sS -X POST http://127.0.0.1:8000/run-prospect \
  -H 'Content-Type: application/json' \
  -d '{"company_name":"Quiet Current Bank","reply_text":"No, not a priority"}'
```

### List adversarial scenarios

```bash
curl -sS http://127.0.0.1:8000/run-prospect/scenarios
```

### Run the compact batch evaluation

```bash
curl -sS http://127.0.0.1:8000/run-prospect/batch
```

## Local Execution Scripts

Run the default prospect from Python:

```bash
python3 scripts/run_prospect.py
```

Run the adversarial scenarios:

```bash
python3 scripts/run_adversarial_cases.py
```

Run the compact batch summary:

```bash
python3 scripts/run_batch_summary.py
```

## Generated Artifacts

Each prospect run writes machine-readable artifacts into `outputs/`:

- `hiring_signal_brief.json`
- `competitor_gap_brief.json`
- `email.json`
- `draft_email.json`
- `full_prospect_run.json`
- scenario-specific output files such as `weak_confidence_full_run.json`
- `adversarial_results.json`
- `adversarial_batch_summary.json`

Append-only run logging:

- `logs/prospect_runs.jsonl`
- `eval/logs/trace_log.jsonl`
- `eval/logs/score_log.json`

## Evaluation Assets

SignalForge includes two layers of evaluation:

### 1. Executable adversarial scenarios

Located in:

- [eval/adversarial_cases.py](eval/adversarial_cases.py)
- [eval/run_adversarial.py](eval/run_adversarial.py)

Current scenarios include:

- `conflicting_signals`
- `no_hiring_signals`
- `weak_confidence`

### 2. Probe-driven failure analysis

Located in:

- [probes/probe_library.md](probes/probe_library.md)
- [probes/failure_taxonomy.md](probes/failure_taxonomy.md)
- [probes/target_failure_mode.md](probes/target_failure_mode.md)

This layer is aimed at production risk, not just unit correctness.

## Current Status

Working today:

- deterministic enrichment
- structured brief generation
- confidence-aware OpenRouter email generation
- claim validation
- FastAPI execution path
- frontend dashboard over the live API
- run logging and artifact emission
- adversarial evaluation pack

Not yet fully wired into the live path:

- real outbound email sending via Resend
- HubSpot writeback
- live Cal.com automation beyond booking link return
- multi-turn conversational orchestration

## Recommended Next Steps

1. add the frontend dashboard over the existing API
2. wire Resend into a guarded outbound send path
3. connect HubSpot writeback and activity logging
4. make Langfuse tracing first-class in deployment
5. turn the markdown probe library into executable scored probes

## Professional Notes

This repo is intentionally local-first and evaluation-heavy. That is by design.

Before a system like this is trusted to automate outbound at scale, it should prove:

- that its claims stay inside evidence bounds
- that its tone follows confidence
- that its failure modes are visible
- that its cost profile is controlled

SignalForge is built to make those properties inspectable.
