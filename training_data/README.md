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

- total preference pairs: `110`
- source benchmark split: `train`
- chosen examples evaluator status: `110 / 110 passing`

## Scope

The current artifact is large enough to support the local Path B critic run in [`../training/run_path_b_critic.py`](../training/run_path_b_critic.py). It is still not the full long-run benchmark release, but it has moved past the starter-scale stage and now supports a real held-out ablation pass.
