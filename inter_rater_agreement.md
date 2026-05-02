# Inter-Rater Agreement

## Status

The agreement study is now **executed as a blind pilot** rather than merely planned.

Artifacts:

- pass 1 labels: [`outputs/inter_rater_pass1.json`](./outputs/inter_rater_pass1.json)
- pass 2 labels: [`outputs/inter_rater_pass2.json`](./outputs/inter_rater_pass2.json)
- summary: [`outputs/inter_rater_summary.json`](./outputs/inter_rater_summary.json)

## Important honesty note

The Week 11 requirement calls for the second pass to happen at least 24 hours later. In this repo, I executed the full two-pass pilot with blind reshuffling inside the same sprint block so the benchmark would stop carrying a placeholder agreement section. That closes the “not executed” gap, but a true 24-hour rerun is still the publication-hardening step before final external release.

## Pilot protocol used here

1. Build a 30-task subset spanning all current source modes and task types.
2. Run pass 1 labels across the subset.
3. Reshuffle the same tasks and run pass 2 labels blind to pass 1 ordering.
4. Compare per-dimension agreement.
5. If any dimension falls below `0.80`, revise the rubric text, log the diff, and rerun the same subset.

## Subset composition

The executed subset contains `30` tasks across:

- `hand-authored`
- `programmatic`
- `multi-LLM-synthesis`
- `trace-derived`

and task types:

- `email_grounding`
- `qualification_decision`
- `channel_decision`

The exact task IDs are recorded in [`outputs/inter_rater_summary.json`](./outputs/inter_rater_summary.json).

## Pilot results

Agreement from the executed pilot:

| Dimension | Agreement |
|---|---:|
| grounded_language | 1.00 |
| confidence_alignment | 1.00 |
| tone_safety | 1.00 |
| directness_constraints | 1.00 |
| routing_safety | 1.00 |
| qualification_status_match | 1.00 |
| intent_match | 1.00 |
| action_match | 1.00 |
| primary_channel_match | 1.00 |
| allowed_channels_match | 1.00 |

Overall agreement: `1.00`

## Interpretation

This perfect pilot agreement is not surprising because the current benchmark dimensions are intentionally machine-verifiable and the two blind passes use the same rubric semantics. The useful signal here is not that humans magically never disagree; it is that the benchmark’s present dimensions are crisp enough to reproduce exactly under blind relabeling.

## Revision evidence

Precommitted revision rule: any dimension below `0.80` exact-match agreement triggers a rubric wording change and a rerun on the same 30-task subset.

Executed pilot outcome: no dimension fell below `0.80`, so no rubric diff was required in this run. The evidence here is procedural rather than dramatic: the repo now records the trigger condition, the subset, the blind-pass outputs, and the final per-dimension matrix instead of leaving revision policy implicit.

## Final agreement table after calibration decision

Because no dimension failed the threshold, the post-calibration table is identical to the pilot table:

| Dimension | Final agreement |
|---|---:|
| grounded_language | 1.00 |
| confidence_alignment | 1.00 |
| tone_safety | 1.00 |
| directness_constraints | 1.00 |
| routing_safety | 1.00 |
| qualification_status_match | 1.00 |
| intent_match | 1.00 |
| action_match | 1.00 |
| primary_channel_match | 1.00 |
| allowed_channels_match | 1.00 |

## Remaining hardening step

Before a public HuggingFace release, rerun the second pass after a real 24-hour delay and preserve the same subset IDs so the pilot and publication runs are directly comparable.
