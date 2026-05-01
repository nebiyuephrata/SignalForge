# Colab Unsloth Plan

This plan connects `TRP1_week11_unsloth.ipynb` to the current SignalForge repo.

## What the notebook already gets right

- Unsloth is a good fit for free or low-VRAM Colab runs.
- QLoRA plus 4-bit loading is the right default for a `T4`.
- A small Qwen-family backbone is a sensible starting point for Week 11.

## What is currently missing

1. The notebook expects `/content/preferences_train.jsonl` and `/content/preferences_dev.jsonl`, but the repo only ships a single local file at `training_data/path_b_preferences.jsonl`.
2. The repo preference rows store `prompt` as messages and `chosen` / `rejected` as structured objects; the notebook expects plain strings.
3. The notebook switches from Path B language into pure SFT on `chosen` responses. That is useful as a warm start, but it is not the main Path B objective.
4. There is no Colab-ready held-out export or documented rule for when to touch held-out.
5. There is no explicit post-training evaluation loop for "generate on dev, then score with `scoring_evaluator.py`".

## Files added to close the gap

- `training/export_unsloth_datasets.py`
  Exports:
  - `training_data/unsloth/preferences_train.jsonl`
  - `training_data/unsloth/preferences_dev.jsonl`
  - `training_data/unsloth/preferences_held_out.jsonl`
  - `training_data/unsloth/manifest.json`

Each exported row now contains:

- `prompt`
- `chosen`
- `rejected`
- `sft_text`
- `chosen_chatml`
- `rejected_chatml`

That means the same export works for either:

- optional SFT warm start
- ORPO / DPO / SimPO preference tuning

## Recommended training path

### Phase 0: Export data from the repo

Run locally:

```bash
.venv/bin/python training/export_unsloth_datasets.py
```

Upload or copy these two files into Colab for tuning:

- `training_data/unsloth/preferences_train.jsonl`
- `training_data/unsloth/preferences_dev.jsonl`

Keep this file sealed until the end:

- `training_data/unsloth/preferences_held_out.jsonl`

### Phase 1: Optional warm-start SFT

Use `sft_text` only if the base model is still too generic in tone or structure.

Good use cases:

- subject-line formatting is unstable
- the model ignores Tenacious style constraints
- the model struggles to emit the structured email shape you need

Keep it short:

- `50-150` steps
- low learning rate
- no held-out access

### Phase 2: Main preference tuning

Use the pairwise fields:

- `prompt`
- `chosen`
- `rejected`

Preferred order:

1. `ORPO` if you want a simple one-stage Colab run with low operational friction.
2. `SimPO` if you want the strongest Path B fit and can tolerate slightly more setup sensitivity.
3. `DPO` only if the notebook or trainer version makes ORPO / SimPO awkward.

Why this order:

- `ORPO` is reference-free and fits well on a small LoRA run.
- `SimPO` is also reference-free and was designed to improve margin efficiency over DPO.
- `DPO` is still solid, but it usually asks for a reference model story you do not need on a tight Colab budget.

### Phase 3: Dev evaluation

After each run, generate outputs for the `dev` split only.

Evaluate:

- exact benchmark pass rate
- per-dimension pass rate
- over-claiming failures
- booking-link misuse
- calibration failures on low-confidence tasks

Do not use `held_out` to tune prompts, hyperparameters, or trainer choice.

### Phase 4: Final held-out pass

Once the recipe is locked:

1. generate outputs on `held_out`
2. run the sealed evaluation once
3. compare to the current local linear critic baseline

## Hyperparameter starting point for a free T4

Backbone:

- start with `Qwen/Qwen2.5-1.5B-Instruct`

LoRA:

- `r=16`
- `lora_alpha=16`
- `lora_dropout=0`
- target modules: `q_proj`, `k_proj`, `v_proj`, `o_proj`, `gate_proj`, `up_proj`, `down_proj`

Sequence lengths:

- `max_prompt_length=1024`
- `max_length=1536`

Batching:

- per-device batch size `1` or `2`
- gradient accumulation `8` to `16`

Learning rate:

- SFT warm start: `1e-4` to `2e-4`
- ORPO / SimPO: `5e-6` to `2e-5`

Training length:

- first smoke test: `50-100` optimizer steps
- first real run: `1-2` epochs

Kill criteria:

- stop if dev pass rate is flat after the first checkpoint
- stop if the model gets more fluent but less grounded
- stop if low-confidence tasks start getting confident sales language

## What will raise the score fastest

1. Normalize label drift before training.
   `CTO_sensitivity` and `cto_sensitivity` should not compete as separate concepts in the prompt space.
2. Hard-negative mining.
   Add more subtle rejected responses, not only obviously bad ones with banned phrases.
3. Split by failure mode during evaluation.
   The score gains will likely come from `weak_confidence`, `signal_over_claiming`, `pricing_handoff`, and `cto_sensitivity`.
4. Train the critic or judge narrowly.
   Tenacious-specific groundedness beats generic "helpfulness".
5. Add dev-time candidate reranking.
   Generate `N=3-4` candidates, then pick the one that best satisfies the local rubric or critic.

## Better patterns to implement next

### 1. Two-stage training

Use:

- short SFT warm start
- then ORPO or SimPO

This is still the safest small-data recipe for your setup.

### 2. Verifier-gated generation

Do not rely on one-shot generation alone.

Use:

- generator produces `3-4` candidates
- local critic or rubric-based verifier picks one
- reject outputs that miss required signal strings or violate handoff rules

### 3. Reward decomposition before full RL

If you try GRPO later, do not start with a single vague reward.

Break reward into:

- grounded evidence match
- confidence calibration
- routing safety
- tone safety
- directness constraints

This repo already has that decomposition in the evaluator logic, which is exactly the kind of reward surface GRPO needs.

### 4. Hard-example curriculum

Start with obvious chosen-vs-rejected pairs, then add:

- subtle over-claiming
- almost-correct routing mistakes
- low-confidence tasks where the failure is overconfidence, not syntax

### 5. Synthetic failure replay

After every dev run:

1. collect failing outputs
2. turn them into new preference rows
3. retrain or continue LoRA

This is one of the highest-leverage loops in narrow-domain alignment work.

## Latest patterns worth borrowing

These are the ones that fit this project best right now:

1. Reference-free preference optimization.
   SimPO and ORPO are both designed to avoid the extra reference-model overhead common in DPO-style workflows.
2. Judge or verifier integration.
   TRL now exposes experimental judge APIs, which matches the repo's "critic in front of generator" direction.
3. Structured-reward RL only after offline preference tuning.
   GRPO is strong when you can express a reward clearly, but it is a second step here, not the first.
4. Narrow-domain reranking instead of only bigger models.
   In this benchmark, better selection and calibration are likely to beat raw parameter count on a free GPU.

## Practical execution plan

Day 1:

1. export the new Unsloth datasets
2. run a `Qwen2.5-1.5B` warm-start SFT smoke test
3. confirm the model still obeys email structure

Day 2:

1. run `ORPO` on train
2. evaluate on dev
3. inspect failures by dimension

Day 3:

1. add hard negatives for the top two failing dimensions
2. rerun ORPO or switch to SimPO
3. compare dev pass rate again

Day 4:

1. add candidate reranking with the local critic or deterministic rubric checks
2. rerun dev
3. freeze the best recipe

Day 5:

1. run the sealed held-out pass once
2. update the report with the final numbers

## Success criterion

A good Week 11 result is not "the model sounds smoother."

It is:

- higher dev pass rate
- fewer over-claiming failures
- stronger low-confidence restraint
- cleaner routing and pricing handoff behavior
- held-out improvement without using held-out during tuning
