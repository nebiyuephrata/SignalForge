# Training Scaffold

This directory holds the Week 11 training scaffold for **Path B**.

## Goal

Train a small preference-tuned critic that can distinguish:

- grounded vs over-claiming outreach
- safe vs unsafe routing decisions
- Tenacious-calibrated vs generic B2B phrasing

The critic is intended to sit in front of the existing SignalForge generator as a rejection or rollback layer.

## Inputs

- preference data: `training_data/path_b_preferences.jsonl`
- benchmark source: `tenacious_bench_v0.1/train/tasks.jsonl`
- rationale: `methodology_rationale.md`

## Implemented run

The repo now includes an executable local critic run in [`run_path_b_critic.py`](./run_path_b_critic.py). It trains a lightweight pairwise linear preference critic over the Path B preference data and writes:

- critic weights: `training/artifacts/path_b_linear_critic.json`
- training log: `training/training_run.log`
- held-out traces: `ablations/held_out_traces.jsonl`
- ablation summary: `ablations/ablation_results.json`

This is intentionally a local, dependency-light Path B run rather than a TRL/Unsloth GPU training job, because the current repo environment does not ship the full transformer fine-tuning stack. It still gives the project a real trained critic artifact and a statistically tested held-out comparison.

## Current result

- held-out baseline accuracy: `0.4000`
- held-out trained accuracy: `0.7333`
- held-out lift: `+33.33pp`
- `95% CI`: `[15.56, 51.11]`
- paired bootstrap `p-value`: `0.0`

## Optional next run

1. Expand the train split to at least 100–300 preference pairs.
2. Swap the local linear critic for the intended SimPO/ORPO run once `transformers`, `trl`, and `datasets` are available.
3. Keep the judge narrow: score Tenacious criteria, not broad assistant quality.
4. Evaluate only on the sealed held-out split after training.

## Planned outputs

- adapter checkpoint or lightweight critic weights
- training log with seed and hyperparameters
- held-out benchmark scores
- cost and latency deltas

## Current status

- preference data formatting: `done`
- training script: `done`
- first run: `done`
- held-out ablation: `done`
