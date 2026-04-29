# Generation Scripts

This directory contains the reproducible Week 11 authoring pipeline for `tenacious_bench_v0.1`.

## Scripts

- `build_bench.py`
  - builds the current benchmark partitions from trace-derived, programmatic, hand-authored, and multi-LLM-synthesized sources
  - writes:
    - `tenacious_bench_v0.1/train/tasks.jsonl`
    - `tenacious_bench_v0.1/dev/tasks.jsonl`
    - `tenacious_bench_v0.1/held_out/tasks.jsonl`
    - `tenacious_bench_v0.1/summary.json`
- `synthesize_tasks.py`
  - generates multi-LLM benchmark seeds with a generator / judge route
  - writes:
    - `generation_scripts/synthesis_cache.json`
- `contamination_check.py`
  - checks held-out overlap against `train`
  - reports:
    - longest shared n-gram overlap
    - lexical cosine similarity
    - manual time-shift verification status
- `prepare_preference_data.py`
  - formats the train split into Path B preference pairs
  - writes:
    - `training_data/path_b_preferences.jsonl`

- `run_inter_rater_pilot.py`
  - executes a blind two-pass pilot over a 30-task subset
  - writes:
    - `outputs/inter_rater_pass1.json`
    - `outputs/inter_rater_pass2.json`
    - `outputs/inter_rater_summary.json`

## Current authoring modes

Implemented in this repo right now:

- `trace-derived`
- `programmatic`
- `hand-authored`
- `multi-LLM synthesis`
- `LLM judge filter calibration`

## Rebuild commands

From the repo root:

```bash
.venv/bin/python generation_scripts/synthesize_tasks.py
.venv/bin/python generation_scripts/build_bench.py
.venv/bin/python generation_scripts/contamination_check.py
.venv/bin/python generation_scripts/run_inter_rater_pilot.py
.venv/bin/python generation_scripts/prepare_preference_data.py
```

## Current outputs

As of the latest rebuild:

- total tasks: `225`
- train: `110`
- dev: `70`
- held_out: `45`
- contamination violations: `0`
- preference pairs: `110`

## Judge filter policy in v0.1

The current `v0.1` cut now includes an actual multi-LLM route:

1. `google/gemini-2.5-flash` authors synthesis seeds
2. `qwen/qwen3-32b` performs the cheap-model judge filter
3. an eval-tier frontier-family calibration sample spot-checks a small slice
4. pairwise duplicate resolution keeps the stronger diagnostic variant
5. tasks are normalized into the schema used by `scoring_evaluator.py`
6. held-out must pass contamination checks

Prompt files are committed under `generation_scripts/prompts/` so the generator and judge instructions are inspectable instead of buried inside JSON or handwritten notes.
