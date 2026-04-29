# Tenacious-Bench v0.1

This folder contains the current Week 11 sales evaluation benchmark.

Current state:

- `train/`, `dev/`, and `held_out/` partitions exist.
- Tasks follow the schema in [`../schema.json`](../schema.json).
- The machine-verifiable evaluator is [`../scoring_evaluator.py`](../scoring_evaluator.py).
- Current counts:
  - `train`: 110
  - `dev`: 70
  - `held_out`: 45
- Current source modes:
  - `trace-derived`
  - `programmatic`
  - `hand-authored`
  - `multi-LLM-synthesis`
- Current contamination status:
  - `0` held-out violations in [`../contamination_check.json`](../contamination_check.json)
 - Current evaluator status:
   - `train`: `110 / 110` passing
   - `dev`: `70 / 70` passing
   - `held_out`: `45 / 45` passing

This benchmark now sits inside the target Week 11 release band at `225` tasks total. The held-out split is deliberately composed of trace-derived, hand-authored, and multi-LLM-synthesized families so the sealed slice stays more diagnostic than the repetitive programmatic train/dev families.

Quick verification:

```bash
.venv/bin/python ../generation_scripts/synthesize_tasks.py
.venv/bin/python ../generation_scripts/build_bench.py
.venv/bin/python ../generation_scripts/contamination_check.py
.venv/bin/python ../scoring_evaluator.py --tasks train/tasks.jsonl
.venv/bin/python ../scoring_evaluator.py --tasks dev/tasks.jsonl
.venv/bin/python ../scoring_evaluator.py --tasks held_out/tasks.jsonl
```
