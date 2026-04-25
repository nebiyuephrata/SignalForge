# System Architecture

SignalForge is organized as a deterministic-first pipeline:

1. `Prospect input`
2. `Deterministic enrichment`
3. `Structured briefs`
4. `Confidence calibration`
5. `Guarded generation`
6. `Centralized channel handoff`
7. `CRM / calendar synchronization`
8. `Observability`
9. `Adversarial evaluation`

## Runtime Modules

- `agent/tools/crunchbase_tool.py`
  Loads firmographic and funding fixtures.
- `agent/tools/job_scraper.py`
  Handles public-page scraping interfaces plus explicit offline fallbacks for BuiltIn, Wellfound, LinkedIn public pages, and company careers pages.
- `agent/tools/layoffs_tool.py`
  Parses the layoffs CSV fixture.
- `agent/tools/leadership_tool.py`
  Extracts recent leadership changes from public fixture data.
- `agent/signals/hiring_signals.py`
  Produces the unified `hiring_signal_brief.json` artifact.
- `agent/signals/competitor_gap.py`
  Produces the unified `competitor_gap_brief.json` artifact.
- `agent/core/confidence.py`
  Converts evidence quality into runtime behavior.
- `agent/llm/email_generator.py`
  Builds the grounded claim catalog and applies confidence-conditioned prompting.
- `agent/guards/claim_validator.py`
  Performs post-generation claim and tone validation.
- `agent/core/channel_orchestrator.py`
  Owns email -> SMS -> voice progression and lifecycle state.
- `backend/services/crm_service.py`
  Writes contact, enrichment, and activity data to HubSpot.
- `backend/routes/webhook_cal.py`
  Accepts booking completion and syncs lifecycle state.

## Why This Shape Exists

SignalForge is supposed to win trust by being more disciplined than a generic outbound sequencer. That means:

- signals are gathered before writing
- uncertainty is preserved instead of smoothed away
- channel escalation follows recorded state instead of caller intent
- external integration failures produce explicit fallbacks instead of hidden partial success

## Operational Notes

- The local repo is intentionally offline-friendly.
- Live scraping and live providers are supported through code boundaries, but the fixture-backed path remains the default safe mode.
- The current production upgrade path is:
  file-backed lifecycle state -> durable store
  HTTP provider adapters -> connector-backed adapters when available
