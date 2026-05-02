# Methodology

## Path Declaration

**Selected path: Path B — preference-tuned judge or critic**

## Preliminary Justification

Path B best fits the Week 10 evidence because the most expensive failures were inconsistency failures, not pure "cannot generate text" failures. The confidence harness in [docs/evaluation/confidence_analysis.md](./docs/evaluation/confidence_analysis.md) shows calibration reducing over-claiming from `62%` to `25%`, which means the workflow already has a control surface that can respond to better judgment signals. Langfuse traces `2713c015315570e24157833b466ca775`, `2bc8574e0954a3902393c025758f243c`, and `47ab214adf0bc2f1ee3a762ebd3afb78` show the same system moving from acceptably narrow outreach to broad template-like messaging under similar prospect conditions. That is a critic problem: the generator can already produce good output, but it cannot always tell when its own answer has crossed from grounded synthesis into unsafe overreach.

The decision is also consistent with the failure taxonomy. `weak confidence handling`, `signal over-claiming`, `tone drift`, and `CTO sensitivity` all benefit from a critic that can score groundedness, restraint, and style adherence against a structured brief. This matches the design pressure described in the LLM-as-a-Judge survey, which treats consistency and domain adaptation as first-class concerns for evaluators, and it matches the contamination cautions from Chen et al.'s benchmark-contamination review: the narrow judge should be trained and tested against a sealed slice that is not recycled into prompting. A generation-only adapter could improve phrasing, but the current evidence says the system's larger problem is *knowing when not to trust its own output*.

## Week 10 Evidence References

- Langfuse trace `2713c015315570e24157833b466ca775`
- Langfuse trace `2bc8574e0954a3902393c025758f243c`
- Langfuse trace `47ab214adf0bc2f1ee3a762ebd3afb78`
- Adversarial scenarios in [eval/logs/trace_log.jsonl](./eval/logs/trace_log.jsonl)
- Failure categories in [probes/probe_library.json](./probes/probe_library.json)

## Required Reading References

- Liu et al., *Best Practices and Lessons Learned on Synthetic Data for Language Models*
- Chen et al., *Recent Advances in Large Language Model Benchmarks against Data Contamination*
- Gu et al., *A Survey on LLM-as-a-Judge*
- Meng, Xia, and Chen, *SimPO: Simple Preference Optimization with a Reference-Free Reward*

## Partitioning Protocol

The benchmark targets the required `50/30/20` split at the partition level, with family-level grouping taking precedence so near-duplicate task families do not leak into held-out:

- `train`: `98` tasks
- `dev`: `78` tasks
- `held_out`: `49` tasks

The v0.1 stratification logic is explicit rather than implicit. Tasks are first grouped by source family and failure dimension, then distributed across `train`, `dev`, and `held_out` so that every split contains all four source modes rather than a single-mode silo. The actual resulting source totals are `69` `trace-derived`, `72` `programmatic`, `48` `multi-LLM-synthesis`, and `36` `hand-authored`, which is close to the intended `30/30/25/15` shape. The partition split is slightly off the exact target because contamination prevention keeps near-duplicate families together.

During Week 11, authoring scripts may read train and dev, but may not import held-out examples into training-data formatting or prompt iteration.

## Contamination Protocol

Each held-out task must pass three checks before release:

1. N-gram overlap below the configured threshold against train.
2. Embedding similarity below the configured threshold against both train and dev.
3. Time-shift verification for any public-signal-dependent task.

The current implementation lives in [generation_scripts/contamination_check.py](./generation_scripts/contamination_check.py) and writes [contamination_check.json](./contamination_check.json). The script now emits structured reports for both `held_out_vs_train` and `held_out_vs_dev`, and the cheap embedding check is implemented as a local hashing-based embedding surrogate with cosine thresholding.

Current results, reported in prose:

- **Held-out vs train:** `0` violations at the `8`-gram and `0.85` embedding thresholds.
- **Held-out vs dev:** `0` violations at the same thresholds after the boilerplate-aware overlap filter and split repair.
- **Time-shift verification:** held-out trace-derived and synthesis rows still carry documented manual-review provenance tags where appropriate.

Final pass status: **0 contamination violations across both held-out vs train and held-out vs dev under the current structured policy.**

## Inter-Rater Agreement Protocol

A 30-task subset is labeled twice with blind reshuffling between passes. The benchmark requirement is still a 24-hour separation before final public publication; the current repo now includes an executed pilot in `outputs/inter_rater_summary.json` so the agreement loop is no longer just a placeholder. Agreement below `0.80` on any rubric dimension triggers rubric revision and relabeling.
