# Confidence Calibration Layer

## Purpose

SignalForge's primary mechanism-design intervention is a `Confidence Calibration Layer`. Its job is to convert evidence quality into operational behavior before the LLM and before channel escalation.

## Root Cause Addressed

The target problem is not simply hallucination. The deeper problem is that partial evidence often looks structurally complete:

- there is a funding row
- there is a job-count delta
- there is a peer gap summary

If the system does not explicitly discount contradictory or sparse evidence, the LLM receives a clean-looking packet and writes with more certainty than the business context deserves.

That is why the calibration layer scores:

- overall brief confidence
- average signal confidence
- competitor-gap confidence
- source-success rate
- contradiction penalties
- sparse-sector penalties

## Thresholds

Implemented in `agent/core/confidence.py`:

- `high >= 0.78`
- `medium >= 0.55 and < 0.78`
- `low < 0.55`

Penalty rules:

- `layoff_overrides_funding` subtracts `0.12`
- `weak_hiring_velocity_signal` subtracts `0.08`
- `sparse_sector` subtracts `0.05`

## Behavior Mapping

### High confidence

- Tone: `assertive`
- Max claims: `3`
- Booking link allowed: `true`
- SMS allowed automatically: `false`
- Post-generation validation required: `true`

### Medium confidence

- Tone: `directional`
- Max claims: `2`
- Booking link allowed: `true`
- SMS allowed automatically: `false`
- Post-generation validation required: `true`

### Low confidence

- Tone: `exploratory`
- Max claims: `1`
- Booking link allowed: `false`
- SMS allowed automatically: `false`
- Copy must be question-led: `true`
- Deterministic fallback is preferred over live generation

## Prompt Conditioning

The layer affects prompt construction in `agent/llm/email_generator.py` by:

- capping how many claims can be included
- changing tone instructions
- forcing exploratory language for low confidence
- routing weak-confidence drafts directly to deterministic fallback

## Post-Generation Validation

Implemented in `agent/guards/claim_validator.py`:

- numeric-token validation blocks unsupported numbers
- claim-id validation blocks unsupported structured claims
- tone validation blocks:
  - low-confidence drafts without a question
  - low-confidence drafts with assertive phrases
  - medium-confidence drafts that sound assertive without hedging language

## Ablation Variants

1. Remove threshold penalties
   - Keep the score, but delete contradiction and sparse-signal penalties.
   - Expected effect: more signal over-claiming and more premature booking CTAs.

2. Remove post-generation validation
   - Keep confidence-conditioned prompts, but skip claim and tone checks.
   - Expected effect: more unsupported numeric language and more medium-confidence tone drift.

3. Remove deterministic fallback
   - Force every low-confidence case through the LLM.
   - Expected effect: weak evidence becomes fluent outreach instead of constrained outreach.

## Statistical Test Plan

Primary experiment:

- A/B test current calibration layer vs ablation variant
- Unit of analysis: outbound thread
- Minimum success metrics:
  - lower probe trigger rate for `weak confidence handling`
  - equal or better qualified-reply rate
  - lower claim-validation failure rate

Statistical plan:

- Two-proportion z-test on qualified-reply rate
- Two-proportion z-test on validation-failure rate
- Significance threshold: `p < 0.05`
- Guardrail metrics:
  - no increase in opt-out rate
  - no increase in SMS policy violations
  - no decrease in booking-to-reply ratio larger than `5%` relative

Operational note:

- Run at least `400` threads per arm before drawing conclusions if live traffic volume allows.
