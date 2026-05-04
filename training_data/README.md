# Path B Preference Data

This directory contains the current Path B training-format artifact:

- `path_b_preferences.jsonl`

## What it is

Each row contains:

- the task prompt
- a `chosen` response
- a `rejected` response
- task metadata

The rows are derived from the `train` split of `tenacious_bench_v0.1`.

## Current status

- total preference pairs: `186`
- source benchmark split: `train`
- source train tasks: `62`
- negative variants per task: `3`
- rejection strategies: `strong_overclaiming`, `constraint_break`, `wordy_overconfident`

## Scope

The current artifact is large enough to support the local Path B critic run in [`../training/run_path_b_critic.py`](../training/run_path_b_critic.py). It is still not the full long-run benchmark release, but it has moved past the starter-scale stage and now supports a real held-out ablation pass.

For Colab and Unsloth runs, export the split-specific bundle with:

```bash
.venv/bin/python training/export_unsloth_datasets.py
```
