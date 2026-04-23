# SignalForge

SignalForge is a production-oriented starter repo for a B2B lead qualification and conversion agent. It is designed around one core constraint: every outbound claim must be grounded in verified signals, explicit uncertainty, or a question.

## What this scaffold includes

- Deterministic enrichment and brief generation for one prospect flow
- Rule-based hiring signals and AI maturity scoring
- Simple peer benchmarking for competitor-gap analysis
- Confidence-aware email drafting that asks instead of over-claiming
- FastAPI endpoints for single runs, scenario runs, and batch evaluation
- JSON artifacts and trace logs for inspection and evaluation

## Repo layout

```text
agent/       Deterministic signal logic, orchestrator, tools, and email generator
backend/     FastAPI application and request handling
data/        Local synthetic company and layoffs datasets
eval/        Adversarial scenario definitions and evaluator
logs/        Run history in JSONL format
outputs/     Generated briefs, emails, and evaluation summaries
scripts/     Local entrypoints for direct runs and batch evaluation
```

## Quick start

1. Create a virtual environment.
2. Install dependencies from `requirements.txt`.
3. Copy `.env.example` to `.env` and fill in any keys you need.
4. Run the API:

```bash
uvicorn backend.main:app --reload
```

5. Check health:

```bash
curl http://127.0.0.1:8000/health
```

## Core flow

SignalForge currently proves one complete deterministic loop:

`Input -> Enrichment -> Hiring Brief -> Competitor Gap -> Draft Email -> Reply -> Qualification -> Booking`

The default prospect is `Northstar Lending`, backed by the local dataset in `data/crunchbase_sample.json`.

## Local scripts

Run the default prospect:

```bash
python3 scripts/run_prospect.py
```

Run the adversarial suite:

```bash
python3 scripts/run_adversarial_cases.py
```

Run the compact batch summary directly from Python:

```bash
python3 scripts/run_batch_summary.py
```

## API usage

Start the API:

```bash
uvicorn backend.main:app --reload
```

List available scenarios:

```bash
curl http://127.0.0.1:8000/run-prospect/scenarios
```

Run the default prospect:

```bash
curl -X POST http://127.0.0.1:8000/run-prospect
```

Run a named scenario:

```bash
curl -X POST http://127.0.0.1:8000/run-prospect \
  -H 'Content-Type: application/json' \
  -d '{"scenario_name":"weak_confidence"}'
```

Run a direct company override:

```bash
curl -X POST http://127.0.0.1:8000/run-prospect \
  -H 'Content-Type: application/json' \
  -d '{"company_name":"Quiet Current Bank","reply_text":"No, not a priority"}'
```

Run all adversarial scenarios as a compact evaluation batch:

```bash
curl http://127.0.0.1:8000/run-prospect/batch
```

## Output artifacts

Every run writes inspectable artifacts under `outputs/`:

- `hiring_signal_brief.json`
- `competitor_gap_brief.json`
- `draft_email.json`
- `full_prospect_run.json`
- scenario-specific files such as `weak_confidence_full_run.json`
- `adversarial_results.json`
- `adversarial_batch_summary.json`

Run history is appended to:

- `logs/prospect_runs.jsonl`
- `eval/logs/trace_log.jsonl`
- `eval/logs/score_log.json`

## Current scenarios

- `conflicting_signals`: hiring growth plus recent layoffs
- `no_hiring_signals`: flat roles and stale funding
- `weak_confidence`: slight role growth but not enough evidence for a hard claim

## Notes

- Most external integrations are intentionally thin stubs so the repo stays runnable before keys are wired in.
- The repo is intentionally local-first: company data and layoffs data are synthetic and deterministic.
- The current emphasis is evaluation and traceability, not volume or automation.
- The orchestration path can later be swapped to tool-backed live enrichment without changing the API shape.
