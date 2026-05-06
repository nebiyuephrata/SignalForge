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

## Channel-Orchestrator Invariants

The centralized orchestrator is not just a convenience wrapper around channel
handlers. It is the policy layer that protects a few system-wide invariants:

- `authoritative lifecycle state lives in one place`
  `ChannelOrchestrator` reads and updates the shared `LeadLifecycleState`
  through `ProspectStateStore` instead of letting each provider adapter keep its
  own partial view of progress.

- `transitions are monotonic`
  `_transition()` only allows forward movement through the lifecycle and rejects
  invalid or backward transitions, which keeps retries and stale events from
  rewriting the lead into an earlier stage.

- `duplicate inbound events are no-ops when identifiable`
  `_is_duplicate_event()` suppresses replay of inbound events that reuse the
  same `external_id`, `channel`, and `event_type`, so retries do not trigger
  repeated policy decisions.

- `tool eligibility is derived from global state, not local handler context`
  `allowed_next_channels()` computes which channels are currently legal from the
  full lifecycle state. Handlers execute provider calls, but they do not decide
  whether SMS, WhatsApp, calendar, or voice should be available.

- `provider adapters and policy are deliberately separated`
  The handlers are responsible for talking to providers and parsing payloads.
  The orchestrator is responsible for deciding what happens next.

## Operational Notes

- The local repo is intentionally offline-friendly.
- Live scraping and live providers are supported through code boundaries, but the fixture-backed path remains the default safe mode.
- The current production upgrade path is:
  file-backed lifecycle state -> durable store
  HTTP provider adapters -> connector-backed adapters when available
