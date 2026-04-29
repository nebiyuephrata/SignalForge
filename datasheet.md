# Tenacious-Bench v0.1 Datasheet

## Telescopic Summary

Tenacious-Bench v0.1 is a 225-task benchmark for evaluating Tenacious-style B2B outbound behavior. It is designed to catch the failures that generic assistant and retail benchmarks under-grade: evidence inflation, confidence-insensitive outreach, routing mistakes across lifecycle state, and socially wrong but technically plausible messaging to technical buyers.

Workflow domain only: **Tenacious-style outbound sales evaluation**. No private customer or prospect data is intentionally included.

## 1. Motivation

The benchmark exists because Week 10 showed that SignalForge’s highest-risk failures were not generic “bad email” failures. They were specific business failures: over-claiming from thin public signals, drifting into commodity outsourcing language, escalating to booking too early, and using technically grounded peer comparisons in a way that still lands poorly with a newly hired CTO.

Tenacious-Bench therefore measures:

1. whether the message uses only evidence present in the supplied brief,
2. whether confidence level changes language and call to action,
3. whether qualification and channel decisions match the thread evidence,
4. whether Tenacious-specific tone and routing constraints are preserved.

## 2. Composition

### Periscopic Summary

The current release contains **225 total tasks**, inside the required 200-300 band.

| Partition | Count | Share |
| --- | ---: | ---: |
| `train` | 112 | 49.8% |
| `dev` | 69 | 30.7% |
| `held_out` | 44 | 19.6% |

### Source modes

| Source mode | Count | Share | Typical use in v0.1 |
| --- | ---: | ---: | --- |
| `trace-derived` | 69 | 30.7% | Convert real Week 10 behavior into benchmark tasks with direct trace references |
| `programmatic` | 72 | 32.0% | High-volume probe expansions with controlled slot variation |
| `multi-LLM-synthesis` | 48 | 21.3% | Hard-case expansion using generator/judge model rotation |
| `hand-authored` | 36 | 16.0% | Highest-value adversarial edge cases written directly for Tenacious-specific failure modes |

The target design mix is `30/30/25/15`. The current release is much closer to that target than the earlier seed cut, but it is still slightly underweight on `multi-LLM-synthesis` and slightly overweight on `programmatic`. The bigger remaining composition debt is not mode share but label normalization inside a few failure dimensions.

### Task types

| Task type | Count | Share |
| --- | ---: | ---: |
| `email_grounding` | 161 | 71.6% |
| `channel_decision` | 41 | 18.2% |
| `qualification_decision` | 23 | 10.2% |

### Failure dimensions

The benchmark covers the following failure dimensions, reported from the current task files:

| Failure dimension | Count |
| --- | ---: |
| `weak_confidence_handling` | 16 |
| `outsourcing_mismatch` | 14 |
| `pricing_handoff` | 14 |
| `signal_over_claiming` | 14 |
| `cto_sensitivity` | 10 |
| `conflicting_signals` | 8 |
| `conflicting_signals_channel_plan` | 8 |
| `conflicting_signals_qualification` | 8 |
| `no_hiring_signals` | 8 |
| `no_hiring_signals_channel_plan` | 8 |
| `no_hiring_signals_qualification` | 8 |
| `scheduling_calibration` | 8 |
| `weak_confidence` | 7 |
| `weak_confidence_channel_plan` | 7 |
| `weak_confidence_qualification` | 7 |
| `bench_to_brief_match` | 6 |
| `coordination_failures` | 6 |
| `cost_issues` | 6 |
| `defensive_reply_recovery` | 6 |
| `gap_over_claiming` | 6 |
| `icp_misclassification` | 6 |
| `multi_thread_leakage` | 6 |
| `new_cto_transition` | 6 |
| `scheduling_edge_cases_eu_us_africa` | 6 |
| `signal_reliability` | 6 |
| `soft_defer_graceful_close` | 6 |
| `tone_drift` | 6 |
| `warm_reply_grounded_answer` | 6 |
| `outsourcing_perception` | 2 |

### Per-mode examples

`trace-derived` tasks usually start from a real Week 10 trace where the system produced a grounded or borderline outreach draft, then turn that draft into a scored task with explicit evidence hooks and trace IDs.

`programmatic` tasks usually start from one probe category such as signal over-claiming or warm-thread routing, then sweep structured variables like company stage, signal confidence, buyer role, or reply state to create controlled variants.

`multi-LLM-synthesis` tasks usually target the hardest narrative edge cases, such as CTO sensitivity or pricing handoff, where simple slot filling is not enough and the benchmark needs more human-like pressure on the generator.

`hand-authored` tasks are the sharpest adversarial slice: cases written directly to expose failures like role-transition condescension, bench mismatch, or socially wrong escalation.

## 3. Collection Process

The benchmark was assembled from four local sources:

- Week 10 traces in `eval/logs/trace_log.jsonl`
- Langfuse export in `1777146734291-lf-events-export-cmobegllz0071ad07uzr7gkjk.csv`
- probe definitions in `probes/probe_library.json`
- Tenacious seed collateral in `tenacious_sales_data/.../seed/`

Authoring modes in v0.1:

1. `trace-derived`: extract real Week 10 agent behavior and restructure it as machine-verifiable tasks.
2. `programmatic`: expand probe categories using deterministic slot variation.
3. `multi-LLM-synthesis`: use Gemini-family generation, Qwen-family judging, and limited eval-tier calibration.
4. `hand-authored`: write adversarial tasks for edge cases the automated routes under-cover.

## 4. Preprocessing and Cleaning

### Microscopic Detail

Each task stores:

- `task_id`
- `split`
- `source_mode`
- `dimension`
- `task_type`
- structured `input`
- `candidate_output`
- explicit `ground_truth`
- weighted `scoring_rubric`
- `metadata` with evidence and probe references

Before a task enters the benchmark:

- candidate outputs are normalized into typed fields,
- banned phrases and required strings are made explicit,
- pass thresholds are encoded numerically,
- contamination checks are run against the sealed held-out partition,
- source mode and evidence references are attached for provenance.

Current contamination status from `contamination_check.json`:

- n-gram overlap threshold: `8`
- similarity threshold: `0.85`
- held-out comparisons: `44`
- n-gram flags: `0`
- similarity flags: `0`
- manual time-shift reviews: `44`
- final violations: `0`

The time-shift review is still partly manual because some held-out tasks intentionally anchor to Week 10 repository artifacts rather than newly fetched public snapshots.

## 5. Uses

Recommended uses:

- baseline evaluation of the Week 10 SignalForge agent,
- regression checks during Week 11 training and ablations,
- preference-pair preparation for Path B critic training,
- critic or judge gating ahead of outbound delivery.

Not recommended uses:

- claiming real-market reply-rate performance,
- using the held-out slice for prompt iteration,
- treating the benchmark as complete production ground truth,
- training directly on the sealed held-out partition.

## 6. Distribution

Planned public destination:

- HuggingFace Hub dataset: `tenacious_bench_v0.1`

Planned license:

- `CC-BY-4.0`

License rationale: the benchmark is meant to be inspectable, reproducible, and reusable for open evaluation work, but the release is framed around the workflow domain rather than any private Tenacious customer detail. The public artifact should include the train/dev slices, datasheet, evaluator, and reproducibility steps; the sealed held-out slice should remain unreleased until the public evaluation protocol is ready.

## 7. Maintenance

Responsible maintainer for v0.1: the repository author / Week 11 trainee maintaining this benchmark release.

The maintenance plan for v0.2 is:

1. normalize dimension labels such as `CTO_sensitivity` versus `cto_sensitivity` and `signal_over-claiming` versus `signal_over_claiming`,
2. raise `multi-LLM-synthesis` coverage from `48` toward the target band of roughly `56`,
3. replace the current lexical cosine proxy with a true embedding similarity checker,
4. rerun the inter-rater study with a true 24-hour delay before public release,
5. publish the reproducibility example and dataset card on HuggingFace.
