# Target Failure Mode

## Selected Failure

`weak confidence handling`

This is the highest-ROI failure for SignalForge to suppress because it is the earliest control-surface error in the pipeline. When weak evidence is not translated into cautious behavior, every downstream step becomes noisier:

- the prompt becomes too fluent
- the claim set grows too large
- SMS may be offered too early
- booking links appear before confidence is earned
- CRM records inflated intent

## Root Cause

The root cause is not "the model sounds too confident." The root cause is that evidence strength is treated as descriptive metadata instead of an execution constraint.

In other words:

- signal confidence is computed
- but if the system still sends medium-style or high-style outreach on low evidence, the score did not actually control behavior

That is why the current repository now routes confidence through a dedicated calibration layer before generation and channel handoff.

## Arithmetic

From [failure_taxonomy.md](./failure_taxonomy.md):

- `weak confidence handling`
  - `average_trigger_rate = 0.40`
  - `average_business_cost_usd = $53,662.50`
  - `expected_loss_index = 0.40 x 53,662.50 = 21,330.84`

Single-thread mental model:

- Assume a representative Tenacious ACV of `$300,000`
- Assume weak confidence handling causes a `45%` conversion loss once a shaky claim or premature CTA appears
- Assume the failure triggers on `40%` of affected weak-evidence threads

Expected downside per affected weak-evidence thread:

- `0.40 x 0.45 x $300,000 = $54,000`

That aligns closely with the probe-library average of `$53,662.50`.

## Comparison To Alternatives

Alternative 1: `signal over-claiming`

- `average_trigger_rate = 0.33`
- `average_business_cost_usd = $55,800.00`
- `expected_loss_index = 18,600.00`

Why it loses:

- It is slightly less frequent.
- Much of it is a downstream manifestation of the same calibration problem.
- Fixing confidence handling should reduce a meaningful portion of signal over-claiming automatically.

Alternative 2: `coordination failures`

- `average_trigger_rate = 0.17`
- `average_business_cost_usd = $31,500.00`
- `expected_loss_index = 5,460.00`

Why it loses:

- It still matters, especially around CRM and booking sync.
- But the expected-loss index is far smaller.
- Coordination bugs harm workflow integrity; weak confidence handling harms both trust and workflow quality at once.

Alternative 3: `outsourcing perception`

- `average_trigger_rate = 0.27`
- `average_business_cost_usd = $60,750.00`
- `expected_loss_index = 16,402.50`

Why it loses:

- Brand damage per event is high.
- But it is narrower in scope than calibration failure.
- Better confidence control also reduces this category by suppressing over-eager outsourcing language on weak signals.

## Why This Has The Highest ROI

`weak confidence handling` has the best improvement leverage because one mechanism can reduce failures in multiple adjacent categories:

- `signal over-claiming`
- `gap over-claiming`
- `tone drift`
- `outsourcing perception`
- parts of `coordination failures` where premature channel escalation is the symptom

That is why SignalForge now treats confidence as a hard gating layer instead of a cosmetic label.
