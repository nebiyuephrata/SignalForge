# Probe Library

SignalForge keeps the full adversarial probe set in [probe_library.json](./probe_library.json). The JSON file is the source of truth because each probe includes the required structured fields:

- `id`
- `category`
- `setup`
- `expected_failure`
- `observed_trigger_rate`
- `business_cost_usd`
- `business_cost_formula`

Coverage in the current library:

- `36` total probes
- Required categories covered:
  `ICP misclassification`, `signal over-claiming`, `outsourcing mismatch`, `tone drift`, `multi-thread leakage`, `cost issues`, `coordination failures`, `scheduling edge cases (EU/US/Africa)`, `signal reliability`, `gap over-claiming`
- Tenacious-specific categories included:
  `outsourcing perception`, `CTO sensitivity`
- Targeted control-surface category included:
  `weak confidence handling`

Why the library is machine-readable:

- `eval/probe_analysis.py` computes trigger-rate summaries directly from the JSON file.
- `probes/failure_taxonomy.md` and `probes/target_failure_mode.md` are written to match those computed summaries.
- New probes should be added to the JSON first, then reflected in the markdown only if the narrative needs to change.

Exact next step if this moves beyond the local rubric environment:

- Connect the probe runner to real provider sandboxes and persist observed trigger rates from execution logs instead of fixture-based estimates.
