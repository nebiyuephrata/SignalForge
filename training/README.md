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
- Colab/Unsloth export bundle: `training_data/unsloth/`
- benchmark source: `tenacious_bench_v0.1/train/tasks.jsonl` plus `tenacious_bench_v0.1/dev/tasks.jsonl`
- rationale: `methodology_rationale.md`
- Colab notebook: [`SignalForge_PathB_ORPO_Colab.ipynb`](./SignalForge_PathB_ORPO_Colab.ipynb)

## Implemented run

The repo now includes an executable local critic run in [`run_path_b_critic.py`](./run_path_b_critic.py). It trains a lightweight pairwise linear preference critic over the Path B preference data and writes:

- critic weights: `training/artifacts/path_b_linear_critic.json`
- training log: `training/training_run.log`
- held-out traces: `ablations/held_out_traces.jsonl`
- ablation summary: `ablations/ablation_results.json`

This is intentionally a local, dependency-light Path B run rather than a TRL/Unsloth GPU training job, because the current repo environment does not ship the full transformer fine-tuning stack. It still gives the project a real trained critic artifact and a statistically tested held-out comparison.

## Colab / Unsloth bridge

The repo now includes a Colab-ready export step for the Week 11 notebook:

```bash
.venv/bin/python training/export_unsloth_datasets.py
```

This writes:

- `training_data/unsloth/preferences_train.jsonl`
- `training_data/unsloth/preferences_dev.jsonl`
- `training_data/unsloth/preferences_held_out.jsonl`
- `training_data/unsloth/manifest.json`

Use the export bundle as follows:

- `sft_text` for an optional short SFT warm start,
- `prompt` / `chosen` / `rejected` for ORPO, DPO, or SimPO,
- `held_out` only after the training recipe is locked.

The current export now:

- re-splits the combined non-held-out benchmark pool into tuning `train` and tuning `dev`
- keeps benchmark `held_out` separate for final sealed evaluation
- mines three rejected variants per source task
- covers `email_grounding`, `qualification_decision`, and `channel_decision`

Current train/dev export counts:

- tuning `train`: `420` rows
- tuning `dev`: `105` rows
- sealed `held_out`: `142` rows

Current negative families:

- `strong_overclaiming`
- `constraint_break`
- `wordy_overconfident`
- `qualification_aggressive`
- `qualification_conservative`
- `qualification_mixed_signal`
- `channel_primary_mismatch`
- `channel_over_broad_followup`
- `channel_over_narrow_followup`

See [`COLAB_UNSLOTH_PLAN.md`](./COLAB_UNSLOTH_PLAN.md) for the execution plan.

## Current result

- held-out baseline accuracy: `0.5116`
- held-out trained accuracy: `1.0000`
- held-out lift: `+48.84pp`
- `95% CI`: `[34.88, 62.79]`
- paired bootstrap `p-value`: `0.0`

## Optional next run

1. Add replay pairs from actual dev failures instead of only synthetic negatives.
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
