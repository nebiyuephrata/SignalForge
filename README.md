# SignalForge

SignalForge is a production-oriented B2B outbound intelligence system for Tenacious. It ingests a prospect, enriches deterministic public signals, builds structured briefs, constrains LLM behavior behind confidence and claim validation, routes follow-up across channels, syncs lifecycle data to CRM and calendar systems, and evaluates failure modes with adversarial probes.

The design rule is simple: `the model is never the source of truth`.

## System Overview

SignalForge follows this runtime order:

1. `Input`
2. `Enrichment`
3. `Briefs`
4. `Decision`
5. `Channels`
6. `CRM / Calendar`
7. `Observability`
8. `Evaluation`

In code, that means:

- deterministic prospect enrichment in `agent/tools` and `agent/signals`
- structured artifacts in `hiring_signal_brief.json` and `competitor_gap_brief.json`
- confidence calibration in `agent/core/confidence.py`
- outbound generation in `agent/llm/email_generator.py`
- centralized handoff state in `agent/core/channel_orchestrator.py`
- HubSpot and Cal.com lifecycle writes in `backend/services`
- JSONL and Langfuse instrumentation in `logs/` and `agent/llm/client.py`
- adversarial probe analysis in `probes/` and `eval/`

## Architecture

```text
Input
  -> Crunchbase / job scrape / layoffs / leadership detection
  -> hiring_signal_brief.json
  -> competitor_gap_brief.json
  -> confidence calibration layer
  -> guarded email generation
  -> claim + tone validation
  -> channel orchestration
  -> HubSpot + Cal.com sync
  -> JSONL + Langfuse traces
  -> adversarial evaluation
```

Key implementation boundaries:

- `agent/signals/hiring_signals.py` is the authoritative hiring brief builder.
- `agent/signals/competitor_gap.py` is the authoritative peer-benchmark builder.
- `agent/core/confidence.py` is the authoritative confidence-to-behavior mapping.
- `agent/guards/claim_validator.py` is the authoritative post-generation validation layer.
- `agent/core/channel_orchestrator.py` is the authoritative email -> SMS -> voice handoff layer.

## Pinned Dependencies

SignalForge uses the pinned versions in [requirements.txt](./requirements.txt):

- `fastapi==0.115.0`
- `uvicorn==0.30.1`
- `pydantic==2.8.2`
- `pydantic-settings==2.3.4`
- `httpx==0.27.0`
- `langchain==0.3.0`
- `langfuse==2.44.0`
- `redis==5.0.7`
- `sqlalchemy==2.0.32`
- `python-dotenv==1.0.1`
- `pyyaml==6.0.2`
- `playwright==1.52.0`
- `pytest==8.3.2`

## Environment Variables

Copy `.env.example` if you have one locally, or create `.env` manually. These are the runtime variables SignalForge reads from `agent/utils/config.py`.

Core app:

- `APP_NAME`: FastAPI application name.
- `APP_ENV`: environment label used by logs and Langfuse.
- `APP_HOST`: backend bind host.
- `APP_PORT`: backend bind port.
- `LOG_LEVEL`: logger verbosity.
- `FRONTEND_ORIGINS`: comma-separated allowed CORS origins.

LLM:

- `OPENROUTER_API_KEY`: required for live LLM generation.
- `OPENROUTER_BASE_URL`: OpenRouter endpoint.
- `OPENROUTER_MODEL`: primary model for structured email generation.
- `OPENROUTER_FALLBACK_MODEL`: secondary model if the primary fails.
- `OPENROUTER_TIMEOUT_SECONDS`: request timeout for the LLM gateway.
- `OPENROUTER_MAX_TOKENS`: hard completion cap.
- `OPENAI_API_KEY`: reserved for future direct OpenAI adapters.
- `ANTHROPIC_API_KEY`: reserved for future Anthropic adapters.

Email / SMS:

- `RESEND_API_KEY`: required for live outbound email.
- `RESEND_API_BASE_URL`: Resend REST endpoint.
- `RESEND_FROM_EMAIL`: default sender identity.
- `RESEND_REPLY_TO`: reply target placed on outbound mail.
- `RESEND_WEBHOOK_SECRET`: reserved for webhook signature verification.
- `AFRICAS_TALKING_API_KEY`: required for live outbound SMS.
- `AFRICAS_TALKING_USERNAME`: Africa's Talking account name.
- `AFRICAS_TALKING_BASE_URL`: Africa's Talking REST endpoint.
- `AFRICAS_TALKING_WEBHOOK_SECRET`: reserved for webhook verification.

CRM / calendar:

- `HUBSPOT_ACCESS_TOKEN`: preferred HubSpot private app token for live contact and activity writes.
- `HUBSPOT_API_KEY`: legacy fallback used only when `HUBSPOT_ACCESS_TOKEN` is not set.
- `HUBSPOT_BASE_URL`: HubSpot REST endpoint.
- `CALCOM_API_KEY`: reserved for future authenticated Cal.com actions.
- `CALCOM_BASE_URL`: base URL used to generate booking links.
- `CALCOM_BOOKING_SLUG`: public booking slug used in outreach.
- `CALCOM_WEBHOOK_SECRET`: reserved for webhook verification.

Observability / infrastructure:

- `LANGFUSE_PUBLIC_KEY`: enables remote trace export when paired with the secret key.
- `LANGFUSE_SECRET_KEY`: enables remote trace export when paired with the public key.
- `LANGFUSE_HOST`: Langfuse host URL.
- `REDIS_URL`: reserved for future distributed lifecycle state.
- `DATABASE_URL`: reserved for future durable workflow state.

## Local Run Instructions

1. Create a Python environment.

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies.

```bash
.venv/bin/pip install -r requirements.txt
```

3. Optional but recommended: install Playwright Chromium.

```bash
.venv/bin/python -m playwright install chromium
```

4. Start the backend.

```bash
.venv/bin/uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

5. Optional: start the frontend.

```bash
cd frontend
npm install
npm run dev
```

6. Run a default prospect.

```bash
curl -sS -X POST http://127.0.0.1:8000/run-prospect
```

7. Run the batch adversarial suite.

```bash
curl -sS http://127.0.0.1:8000/run-prospect/batch
```

8. Run tests.

```bash
uv run --with pytest pytest -q
```

## Local Run Order

When you want a clean end-to-end local check, use this order:

1. Install dependencies.
2. Install Playwright browsers if you want live DOM parsing.
3. Start the backend.
4. Run `/run-prospect`.
5. Check `outputs/` and `logs/`.
6. Exercise `/webhooks/email/send`.
7. Post an inbound email webhook to `/webhooks/email/resend/events`.
8. Exercise `/webhooks/sms/send-warm` only after the lifecycle store shows an email reply.
9. Post a booking webhook to `/webhooks/cal/booking-completed`.
10. Run the adversarial suite and inspect `outputs/adversarial_batch_summary.json`.

## Output Artifacts

SignalForge writes inspectable artifacts to `outputs/` and `logs/`:

- `outputs/hiring_signal_brief.json`
- `outputs/competitor_gap_brief.json`
- `outputs/email.json`
- `outputs/channel_plan.json`
- `outputs/full_prospect_run.json`
- `outputs/verified_run.json`
- `outputs/confidence_comparison.json`
- `outputs/probe_results.json`
- `outputs/adversarial_batch_summary.json`
- `logs/prospect_runs.jsonl`
- `logs/conversation_events.jsonl`
- `logs/claim_validation_failures.jsonl`

## Verified Execution

SignalForge now ships with a checked real-execution artifact:

- [outputs/verified_run.json](./outputs/verified_run.json)
- [docs/evidence/real_run.md](./docs/evidence/real_run.md)

The current verified run proves a real end-to-end execution path and records the actual outcome:

- the pipeline executed successfully
- the OpenRouter path was attempted
- the live model call failed with DNS resolution errors in this environment
- deterministic fallback preserved a grounded final email

Related evaluation artifacts:

- [outputs/confidence_comparison.json](./outputs/confidence_comparison.json)
- [docs/evaluation/confidence_analysis.md](./docs/evaluation/confidence_analysis.md)
- [outputs/probe_results.json](./outputs/probe_results.json)

## Known Local Constraints

The repository ships with explicit fallbacks rather than pretending live integrations always exist:

- job scraping falls back to local fixture parsing when Playwright is unavailable
- OpenRouter failures fall back to deterministic email generation
- HubSpot writes fall back to structured offline results when both `HUBSPOT_ACCESS_TOKEN` and `HUBSPOT_API_KEY` are missing
- Langfuse export is skipped when the host is unreachable
- live BuiltIn / Wellfound / LinkedIn scraping is intentionally marked as a TODO in source attribution because the current repo uses offline fixtures

See [HANDOFF_NOTES.md](./HANDOFF_NOTES.md) for the exact next steps on those gaps and [DIRECTORY_INDEX.md](./DIRECTORY_INDEX.md) for the repository map.
