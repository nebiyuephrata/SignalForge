---
pretty_name: Tenacious Bench Path B Preference
license: cc-by-4.0
task_categories:
- text-generation
- text-classification
language:
- en
size_categories:
- n<1K
---

# Tenacious Bench Path B Preference

## 1. Motivation

This dataset exists because generic assistant benchmarks do not reliably measure the failure modes that matter in Tenacious-style B2B outbound work. The goal here is not broad conversational quality; it is grounded business behavior under uncertainty.

The preference pairs focus on:

- grounded language
- weak-confidence handling
- over-claiming avoidance
- pricing handoff safety
- qualification correctness
- channel routing behavior

## 2. Composition

This public Hugging Face release contains the Path B preference bundle built from Tenacious-Bench.

Files in this release:

- `preferences_train.jsonl`
- `preferences_dev.jsonl`
- `preferences_held_out_metadata.json`
- `manifest.json`

Split counts:

- `train`: `62`
- `dev`: `113`
- `held_out`: `50` rows recorded as sealed metadata only

The `held_out` partition is intentionally represented as metadata rather than public preference rows so final evaluation remains sealed.

Each row in `train` and `dev` includes:

- `task_id`
- `split`
- `dimension`
- `task_type`
- `source_mode`
- `prompt`
- `prompt_messages`
- `chosen`
- `rejected`
- `chosen_structured`
- `rejected_structured`
- `sft_text`
- `chosen_chatml`
- `rejected_chatml`
- `metadata`

## 3. Collection Process

The underlying benchmark tasks were assembled from four source modes:

- `trace-derived`
- `programmatic`
- `multi-llm-synthesis`
- `hand-authored`

Preference pairs were created by:

1. taking the benchmark-approved output as `chosen`
2. generating a controlled worse variant as `rejected`

For email tasks, the rejected variant introduces problems such as worse subject prefixes, removed uncertainty markers, or banned sales phrasing. For structured tasks, the rejected variant flips fields toward worse qualification or channel decisions.

## 4. Preprocessing, Cleaning, and Labeling

The benchmark rows are normalized into a consistent preference-training schema.

Preprocessing includes:

- converting prompts into trainer-friendly plain strings
- keeping `chosen` and `rejected` in both rendered and structured form
- exporting `sft_text` for optional warm-start supervised tuning
- preserving `source_mode` and task metadata for provenance

The corresponding contamination report in the repo checks held-out overlap against both `train` and `dev`, with a boilerplate-aware 8-gram filter and a cheap local embedding surrogate.

## 5. Uses

Recommended uses:

- train a small preference model or critic
- run ORPO, DPO, or SimPO style experiments
- regression-test sales-domain safety and groundedness behavior

Not recommended uses:

- treating this as a broad instruction-following benchmark
- tuning directly against the sealed held-out partition
- interpreting the dataset as a measure of real-world conversion performance

## 6. Distribution

This dataset is distributed publicly on Hugging Face as the Tenacious Bench Path B preference bundle.

License:

- `CC-BY-4.0`

Repo context:

- benchmark and methodology live in the public SignalForge repository
- this Hugging Face dataset is the public preference-training slice, not the full benchmark release

## 7. Maintenance

The current maintenance priorities are:

1. keep benchmark and preference export counts aligned with the benchmark source of truth
2. complete the ideal 24-hour inter-rater rerun in the repo artifacts
3. publish a fuller benchmark-facing Hugging Face artifact if and when the sealed evaluation protocol is frozen

## Notes

- `manifest.json` is the top-level split index for the preference bundle
- `preferences_held_out_metadata.json` exists so the sealed held-out partition is discoverable during walkthroughs without exposing the held-out rows themselves
