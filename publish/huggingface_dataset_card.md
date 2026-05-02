# HuggingFace Dataset Card Draft

## Dataset name

`tenacious-bench-v0.1`

## Summary

Tenacious-Bench v0.1 is a sales-domain evaluation dataset for grounded outbound intelligence systems. It measures failures that generic assistant benchmarks usually miss, including weak-confidence handling, signal over-claiming, CTO sensitivity, pricing handoff safety, qualification correctness, and channel routing behavior.

## Composition

- total tasks: `225`
- train/dev/held_out: `106 / 76 / 43`
- source modes:
  - `trace-derived`: `9`
  - `programmatic`: `180`
  - `hand-authored`: `24`
  - `multi-LLM-synthesis`: `12`

Task types:

- `email_grounding`: `174`
- `channel_decision`: `48`
- `qualification_decision`: `3`

## Files

- `train/tasks.jsonl`
- `dev/tasks.jsonl`
- `held_out/tasks.jsonl`
- `summary.json`

## Evaluation interface

Machine-verifiable evaluator:

- `scoring_evaluator.py`

Contamination report:

- `contamination_check.json`

## Benchmark status

- held-out contamination violations: `0`
- train evaluator pass rate: `106 / 106`
- dev evaluator pass rate: `76 / 76`
- held-out evaluator pass rate: `43 / 43`

## Intended use

- benchmark a Tenacious-style outbound agent
- generate preference pairs for Path B judge training
- regression-test confidence, routing, and pricing/booking safeguards

## Limitations

1. The current inter-rater artifact is a blind pilot, with a true 24-hour rerun still recommended before public publication.
2. The current contamination similarity check uses a cosine proxy rather than a dedicated embedding model.
3. The benchmark is intentionally narrow and should not be treated as a broad measure of all sales quality.

## License

Planned license: `CC-BY-4.0`
