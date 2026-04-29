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

The benchmark uses the required `50/30/20` split at the partition level:

- `train`: `110` tasks
- `dev`: `70` tasks
- `held_out`: `45` tasks

The v0.1 stratification logic is explicit rather than implicit. High-volume `programmatic` tasks populate train and dev so the critic can learn stable, mechanically scorable rules over the repeated Tenacious failure surface. The held-out slice is intentionally originality-heavy: it contains the `trace-derived`, `hand-authored`, and `multi-LLM-synthesis` tasks so the final evaluation is pressure-tested on the most diagnostic and contamination-sensitive examples. This is not the final desired source-mode balance, but it does serve the failure-coverage goal of keeping the sealed slice behaviorally sharper than the training slice.

During Week 11, authoring scripts may read train and dev, but may not import held-out examples into training-data formatting or prompt iteration.

## Contamination Protocol

Each held-out task must pass three checks before release:

1. N-gram overlap below the configured threshold against train.
2. Embedding similarity below the configured threshold against train.
3. Time-shift verification for any public-signal-dependent task.

The current implementation lives in [generation_scripts/contamination_check.py](./generation_scripts/contamination_check.py) and writes [contamination_check.json](./contamination_check.json).

Current results, reported in prose:

- **N-gram overlap:** `0` held-out/task pairs were flagged at or above the `8`-gram threshold. Maximum observed shared n-gram length was `0`.
- **Similarity check:** `0` held-out/task pairs were flagged at or above the `0.85` similarity threshold. Maximum observed lexical cosine proxy was `0.4048`.
- **Time-shift verification:** `21` held-out tasks were marked `repo_artifact_window_requires_manual_review` because they anchor to Week 10 repository artifacts or synthesized public-signal windows, while `24` held-out tasks were marked `not_required_synthetic_or_repo_authored_task`. No task failed time-shift review strongly enough to be dropped in v0.1, but the flagged set is carried forward as the first manual-review queue for v0.2.

Final pass status: **0 contamination violations** on the sealed held-out slice against train.

## Inter-Rater Agreement Protocol

A 30-task subset is labeled twice with blind reshuffling between passes. The benchmark requirement is still a 24-hour separation before final public publication; the current repo now includes an executed pilot in `outputs/inter_rater_summary.json` so the agreement loop is no longer just a placeholder. Agreement below `0.80` on any rubric dimension triggers rubric revision and relabeling.
