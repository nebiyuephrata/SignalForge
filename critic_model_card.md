# SignalForge Path B Critic Model Card

## Model summary

This artifact is the current Week 11 Path B critic for SignalForge:

- model type: `linear_preference_critic`
- training script: [`training/run_path_b_critic.py`](./training/run_path_b_critic.py)
- weights artifact: [`training/artifacts/path_b_linear_critic.json`](./training/artifacts/path_b_linear_critic.json)

The critic is trained to prefer grounded, Tenacious-calibrated outputs over subtly degraded alternatives on benchmark-style sales tasks.

## Intended use

Use this critic as a narrow evaluation or rejection layer in front of outbound delivery. It is designed to score:

- grounded vs over-claiming email replies
- safe vs unsafe pricing and booking handoff behavior
- qualification and channel decisions against the supplied task evidence

It is not intended as a general-purpose assistant-quality judge.

## Training data

- source benchmark: [`tenacious_bench_v0.1/train/tasks.jsonl`](./tenacious_bench_v0.1/train/tasks.jsonl)
- formatted preferences: [`training_data/path_b_preferences.jsonl`](./training_data/path_b_preferences.jsonl)
- pair count: `106`

Training pairs are constructed from benchmark gold outputs plus programmatically mutated rejected variants.

## Training configuration

- seed: `42`
- vector size: `2064`
- epochs: `14`
- learning rate: `0.35`
- L2 regularization: `0.0005`
- cost: local run, effectively `$0.00`

The current run is a dependency-light local critic rather than a transformer fine-tune because this repository does not currently include the full TRL / transformer training stack.

## Evaluation

Primary ablation artifact:

- [`ablations/ablation_results.json`](./ablations/ablation_results.json)

Held-out result:

- baseline accuracy: `0.5116`
- trained accuracy: `1.0000`
- lift: `+48.84pp`
- `95% CI`: `[34.88, 62.79]`
- paired bootstrap `p-value`: `0.0`

Held-out trace rows:

- [`ablations/held_out_traces.jsonl`](./ablations/held_out_traces.jsonl)

## Limitations

1. This is a local linear critic, not yet the intended SimPO/ORPO small-model run.
2. The current benchmark dimensions are strongly machine-verifiable, so perfect train accuracy should not be mistaken for broad robustness.
3. The inter-rater study has been executed as a blind pilot, but the true 24-hour delayed rerun is still the publication-hardening step.
4. The critic scores benchmark-style tasks, not live end-user value directly.

## Next step

Replace this local critic with the planned small open-model Path B run once the repo has the required GPU training stack and HuggingFace publishing credentials.
