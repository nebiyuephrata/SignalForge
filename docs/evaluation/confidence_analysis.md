# Confidence Analysis

Artifact: [outputs/confidence_comparison.json](/home/rata/Documents/Ephrata/work/10Acadamy/training/SignalForge/outputs/confidence_comparison.json)

## Evaluation Design

SignalForge was run across `8` prospect fixtures in a controlled offline A/B harness:

1. `confidence calibration ON`
2. `confidence calibration OFF`

The harness holds the synthetic model behavior constant and changes only the confidence policy. That makes the comparison attributable to calibration behavior rather than provider availability.

Measured metrics:

- `over-claim rate`
- `unsupported assertion rate`
- `fallback frequency`

## Results

### Calibration ON

- Over-claim rate: `0.25`
- Unsupported assertion rate: `0.50`
- Fallback frequency: `0.50`

### Calibration OFF

- Over-claim rate: `0.62`
- Unsupported assertion rate: `0.75`
- Fallback frequency: `0.12`

### Delta

- Over-claim rate improvement: `0.37`
- Unsupported assertion improvement: `0.25`
- Fallback frequency increase: `0.38`

## What Improved

With calibration enabled, SignalForge falls back more often on low-confidence prospects instead of letting the model write through uncertainty. That change:

- cut measured over-claiming from `62%` to `25%`
- cut unsupported assertions from `75%` to `50%`
- increased deterministic fallback use from `12%` to `50%`

This is the expected tradeoff. Calibration is supposed to spend certainty carefully, not maximize fluent output.

## Why It Matters

Without calibration, weak-evidence accounts like `Harborline Ledger`, `Quiet Current Bank`, and similar edge cases are much more likely to receive confident language such as:

- `clearly expanding`
- `likely needs extra capacity`

That is exactly the business failure SignalForge is designed to prevent. A higher fallback rate is acceptable if it buys a lower false-assertion rate with technical buyers.

## Business Impact

The measured A/B direction supports the target failure analysis:

- fewer over-claims means fewer credibility breaks in first-touch outreach
- fewer unsupported assertions means less risk of immediate thread loss
- more fallbacks means more conservative output, which is cheaper than losing a high-ACV technical buyer because the system sounded more certain than the evidence justified

In short:

- calibration increases restraint
- restraint reduces avoidable trust loss
- that trade is favorable for Tenacious-style outbound
