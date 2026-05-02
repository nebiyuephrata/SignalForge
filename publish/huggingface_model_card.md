# HuggingFace Model Card Draft

## Model name

`signalforge-path-b-linear-critic-v1`

## Summary

This model is a narrow Path B critic trained to rank grounded Tenacious-style outbound behavior above plausible but degraded alternatives. It is intended as a benchmark-facing or pre-send rejection layer, not as a general assistant judge.

## Training artifact

- script: `training/run_path_b_critic.py`
- weights: `training/artifacts/path_b_linear_critic.json`
- run log: `training/training_run.log`

## Training data

- benchmark source: `tenacious_bench_v0.1/train/tasks.jsonl`
- preference pairs: `training_data/path_b_preferences.jsonl`
- pair count: `106`

## Evaluation

Primary result from `ablations/ablation_results.json`:

- held-out baseline accuracy: `0.5116`
- held-out trained accuracy: `1.0000`
- lift: `+48.84pp`
- `95% CI`: `[34.88, 62.79]`
- paired bootstrap `p-value`: `0.0`

## Intended use

- judge outbound email safety and groundedness
- score qualification and routing correctness
- reject or down-rank outputs that drift from Tenacious constraints

## Limitations

1. This is a local linear critic, not yet the intended transformer-based SimPO or ORPO adapter.
2. It is tuned to benchmark tasks derived from SignalForge and may not generalize beyond this workflow.
3. It should be treated as a conservative ranking signal, not as the system’s sole source of truth.
