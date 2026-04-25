# Handoff Notes

## Current Status

SignalForge now has a single deterministic pipeline for:

- hiring signal enrichment
- competitor gap analysis
- confidence calibration
- guarded email generation
- centralized channel handoff state
- lifecycle-aware HubSpot and Cal.com synchronization
- machine-readable probe analysis

The repository is runnable locally with fallbacks, but a few production-facing dependencies are still environment-bound.

## Known Limitations

### Playwright

- Current behavior:
  `agent/tools/job_scraper.py` uses Playwright when Chromium is installed, otherwise it falls back to deterministic fixture parsing.
- Real observed log:
  verified run recorded `company_careers_page -> fallback` with detail `Used deterministic fixture parsing because Playwright was unavailable locally.`
- Why this exists:
  the local training repository ships offline fixtures and must stay runnable without browser binaries.
- Exact next step:
  run `.venv/bin/python -m playwright install chromium`, then connect each company fixture to a real public careers URL and add robots.txt fetch checks before enabling live network scraping.

### OpenRouter

- Current behavior:
  `agent/llm/client.py` will fail over to deterministic email generation if `OPENROUTER_API_KEY` is missing or the network call fails.
- Real observed log:
  `OpenRouter request failed for model=deepseek/deepseek-chat attempt=1 prompt=generate_outreach_email: [Errno -3] Temporary failure in name resolution`
- Verified artifact:
  [outputs/verified_run.json](/home/rata/Documents/Ephrata/work/10Acadamy/training/SignalForge/outputs/verified_run.json)
- Why this exists:
  correctness is preferred over partial LLM output and the local environment may not have outbound network access.
- Exact next step:
  set `OPENROUTER_API_KEY`, confirm outbound HTTPS access, then run `/run-prospect` and inspect `trace_id`, `trace_url`, and `logs/claim_validation_failures.jsonl`.

### Langfuse

- Current behavior:
  tracing hooks are implemented, but export is skipped if `LANGFUSE_HOST` is unreachable or keys are absent.
- Real observed log:
  `Langfuse host is unreachable. Continuing without trace export.`
- Why this exists:
  the repo must not hard-fail local runs just because observability infrastructure is unavailable.
- Exact next step:
  start a reachable Langfuse instance, set `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, and `LANGFUSE_HOST`, then rerun `/run-prospect` and confirm trace URLs resolve.

### MCP

- Current behavior:
  HubSpot and Cal.com are implemented through HTTP boundary clients, not MCP connectors.
- Why this exists:
  the current runtime does not expose HubSpot or Cal.com MCP tools for this repository.
- Exact next step:
  if MCP becomes available, replace `agent/crm/hubspot_client.py` and `agent/calendar/cal_client.py` with connector-backed adapters while preserving the `CRMService` and `ChannelOrchestrator` contracts.

## Practical Follow-Up Work

1. Replace file-backed lifecycle state with Postgres or Redis-backed state plus optimistic locking.
2. Add webhook signature verification for Resend, Africa's Talking, and Cal.com using the already-declared secret environment variables.
3. Connect real public BuiltIn, Wellfound, and LinkedIn public URLs per company and persist robots.txt decisions in source attribution.
4. Add a durable CRM activity type model instead of logging all activities as notes.
5. Extend the centralized channel orchestrator with WhatsApp and LinkedIn only after the current rubric paths are stable in production.

## Reproduction Steps For Real Failures

1. Run the verified execution artifact generator:

```bash
.venv/bin/python -m eval.verified_execution
```

2. Inspect:

- [outputs/verified_run.json](/home/rata/Documents/Ephrata/work/10Acadamy/training/SignalForge/outputs/verified_run.json)
- [docs/evidence/real_run.md](/home/rata/Documents/Ephrata/work/10Acadamy/training/SignalForge/docs/evidence/real_run.md)

3. To reproduce the confidence A/B output:

```bash
.venv/bin/python -m eval.confidence_eval
```

4. To reproduce probe execution:

```bash
.venv/bin/python -m eval.run_probes
```

## Mitigation Plan

- OpenRouter:
  restore outbound DNS/network access, then rerun the verified execution path and compare the new artifact to the current fallback-based run.
- Langfuse:
  point `LANGFUSE_HOST` to a reachable instance and verify `trace_url` becomes non-null in `verified_run.json`.
- Scraping:
  install Chromium, add public board URLs, persist robots.txt outcomes, and rerun the verified execution to replace skipped source statuses with real public-source statuses.

## Safe Extension Rules For New Engineers

When extending SignalForge:

- add new signal sources inside `agent/tools` or `agent/signals`, not inside prompts
- add new confidence behavior in `agent/core/confidence.py`, not inline in handlers
- add new validation checks in `agent/guards/claim_validator.py`, not ad hoc in routes
- add new channel transitions in `agent/core/channel_orchestrator.py`, not in provider clients
- keep fallbacks explicit and write the exact next step whenever an external dependency is unavailable
