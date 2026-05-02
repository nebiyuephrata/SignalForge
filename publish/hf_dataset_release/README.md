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

## Summary

This dataset contains the public training and development preference pairs for the Tenacious Bench Path B workflow.

Each row represents a preference comparison for a narrow sales-domain task. The preferred output is stored as `chosen`, and a controlled lower-quality alternative is stored as `rejected`.

The dataset is intended for preference optimization or preference-based critic training focused on:

- grounded language
- weak-confidence handling
- over-claiming avoidance
- pricing handoff safety
- qualification correctness
- channel routing behavior

## Files

- `preferences_train.jsonl`
- `preferences_dev.jsonl`
- `manifest.json`

## Split Sizes

- `train`: `106`
- `dev`: `76`

The sealed `held_out` split is intentionally excluded from this public release so final evaluation remains credible.

## Schema

Each row includes:

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

## How It Was Built

The benchmark tasks were assembled from four source modes:

- `trace-derived`
- `programmatic`
- `multi-llm-synthesis`
- `hand-authored`

Preference pairs were then created by:

1. taking the benchmark-approved output as `chosen`
2. generating a controlled worse variant as `rejected`

For email tasks, the rejected variant intentionally introduces issues such as overconfident wording, poor subject prefixes, removed uncertainty markers, or banned sales phrasing. For structured tasks, the rejected variant flips fields toward worse qualification or channel decisions.

## Intended Use

- train a small preference model or critic
- run ORPO, DPO, or SimPO style experiments
- regression-test sales-domain safety and groundedness behavior

## Limitations

- this is a narrow domain dataset, not a general instruction-following benchmark
- the public release excludes the sealed held-out split
- synthetic rejected examples are controlled corruptions, not free-form human rewrites

## Notes

- `manifest.json` describes the export bundle layout
- `sft_text` is included for optional short supervised warm-start experiments
