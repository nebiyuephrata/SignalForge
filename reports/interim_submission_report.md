# Week 11 Interim Submission Report

## Overview

This report summarizes the current state of **Tenacious-Bench v0.1** and the supporting Week 11 evaluation stack built on top of SignalForge. The benchmark currently contains **225 tasks** split into `112` train, `69` dev, and `44` held-out tasks, with a machine-verifiable evaluator, contamination checks, inter-rater pilot results, preference-pair formatting for Path B, and a first critic baseline/ablation package already committed in the repo.

The strongest current result is not yet a public model release but a benchmark-and-critic workflow that is mechanically runnable and internally consistent. On the sealed held-out preference pairs, the current local Path B linear critic improves accuracy from **0.6591** to **0.9318**, a **+27.27 percentage point** lift with **95% CI [11.36, 40.91]** and paired bootstrap `p = 0.0`.

## 1. Bench Composition Reporting

The dataset’s quantitative shape is reported along the three required axes: failure dimension, partition, and source mode.

### Partition target vs actual

| Partition | Target share | Target count @225 | Actual count | Actual share | Deviation |
| --- | ---: | ---: | ---: | ---: | ---: |
| `train` | 50.0% | 112 | 112 | 49.8% | 0 |
| `dev` | 30.0% | 68 | 69 | 30.7% | +1 |
| `held_out` | 20.0% | 45 | 44 | 19.6% | -1 |

The split is close to target. The more important remaining issue is not partition size but label cleanup and a slight synthesis shortfall.

### Source-mode target vs actual

| Source mode | Target share | Target count @225 | Actual count | Actual share | Deviation |
| --- | ---: | ---: | ---: | ---: | ---: |
| `trace-derived` | 30.0% | 68 | 69 | 30.7% | +1 |
| `programmatic` | 30.0% | 68 | 72 | 32.0% | +4 |
| `multi-LLM-synthesis` | 25.0% | 56 | 48 | 21.3% | -8 |
| `hand-authored` | 15.0% | 34 | 36 | 16.0% | +2 |

The benchmark is now close enough to the intended source-mode shape to be defensible. The remaining gap is mostly that `multi-LLM-synthesis` is still slightly under target.

### Integrated cross-tabulation

To make the three-axis composition visible in one frame, I render the integrated cross-tab below in compact form. Abbreviations:

- `TrTD / TrP / TrS / TrH` = train trace-derived / programmatic / synthesis / hand-authored
- `DvTD / DvP / DvS / DvH` = dev trace-derived / programmatic / synthesis / hand-authored
- `HoTD / HoP / HoS / HoH` = held-out trace-derived / programmatic / synthesis / hand-authored

```text
Dimension                           TrTD TrP TrS TrH | DvTD DvP DvS DvH | HoTD HoP HoS HoH | Total
bench_to_brief_match                  0   0   0   6 |    0   0   0   0 |    0   0   0   0 |     6
conflicting_signals                   5   0   0   0 |    3   0   0   0 |    0   0   0   0 |     8
conflicting_signals_channel_plan      5   0   0   0 |    3   0   0   0 |    0   0   0   0 |     8
conflicting_signals_qualification     4   0   0   0 |    4   0   0   0 |    0   0   0   0 |     8
coordination_failures                 0   4   0   0 |    0   2   0   0 |    0   0   0   0 |     6
cost_issues                           0   4   0   0 |    0   2   0   0 |    0   0   0   0 |     6
cto_sensitivity                       0   2   0   0 |    0   0   0   0 |    0   0   8   0 |    10
defensive_reply_recovery              0   0   0   0 |    0   0   0   6 |    0   0   0   0 |     6
gap_over_claiming                     0   4   0   0 |    0   2   0   0 |    0   0   0   0 |     6
icp_misclassification                 0   2   0   0 |    0   4   0   0 |    0   0   0   0 |     6
multi_thread_leakage                  0   4   0   0 |    0   2   0   0 |    0   0   0   0 |     6
new_cto_transition                    0   0   0   6 |    0   0   0   0 |    0   0   0   0 |     6
no_hiring_signals                     5   0   0   0 |    3   0   0   0 |    0   0   0   0 |     8
no_hiring_signals_channel_plan        5   0   0   0 |    3   0   0   0 |    0   0   0   0 |     8
no_hiring_signals_qualification       5   0   0   0 |    3   0   0   0 |    0   0   0   0 |     8
outsourcing_mismatch                  0   4   0   0 |    0   2   0   0 |    0   0   8   0 |    14
outsourcing_perception                0   2   0   0 |    0   0   0   0 |    0   0   0   0 |     2
pricing_handoff                       0   0   0   0 |    0   0   0   6 |    0   0   8   0 |    14
scheduling_calibration                0   0   0   0 |    0   0   0   0 |    0   0   8   0 |     8
scheduling_edge_cases_eu_us_africa    0   4   0   0 |    0   2   0   0 |    0   0   0   0 |     6
signal_over_claiming                  0   2   0   0 |    0   4   0   0 |    0   0   8   0 |    14
signal_reliability                    0   4   0   0 |    0   2   0   0 |    0   0   0   0 |     6
soft_defer_graceful_close             0   0   0   6 |    0   0   0   0 |    0   0   0   0 |     6
tone_drift                            0   4   0   0 |    0   2   0   0 |    0   0   0   0 |     6
warm_reply_grounded_answer            0   0   0   6 |    0   0   0   0 |    0   0   0   0 |     6
weak_confidence                       5   0   0   0 |    2   0   0   0 |    0   0   0   0 |     7
weak_confidence_channel_plan          4   0   0   0 |    3   0   0   0 |    0   0   0   0 |     7
weak_confidence_handling              0   6   0   0 |    0   2   4   0 |    0   0   4   0 |    16
weak_confidence_qualification         4   0   0   0 |    3   0   0   0 |    0   0   0   0 |     7
TOTAL                                42  46   0  24 |   27  26   4  12 |    0   0  44   0 |   225
```

One visible example from the table: `pricing_handoff` has `6` dev hand-authored tasks and `8` held-out synthesis tasks, for `14` total. The same table also shows that there are `8` held-out synthesis tasks targeting `cto_sensitivity`, which is the sort of “single look” query the rubric asks for.

The table exposes one cleanup task that should happen in the dataset itself: a few dimension families still carry older naming variants and should be normalized in the next release.

## 2. Inter-Rater Agreement Results Analysis

The inter-rater study was run on a **30-task hand-labeled subset** spanning all current source modes and task types. The agreement metric used was **exact-match agreement by rubric dimension** across two blind passes.

Protocol:

1. sample 30 tasks spanning source modes and task types,
2. label pass 1,
3. blind reshuffle the same task IDs,
4. label pass 2,
5. compute exact-match agreement per dimension.

Results:

| Rubric dimension | Agreement | Clears 0.80? |
| --- | ---: | ---: |
| `grounded_language` | 1.00 | yes |
| `confidence_alignment` | 1.00 | yes |
| `tone_safety` | 1.00 | yes |
| `directness_constraints` | 1.00 | yes |
| `routing_safety` | 1.00 | yes |
| `qualification_status_match` | 1.00 | yes |
| `intent_match` | 1.00 | yes |
| `action_match` | 1.00 | yes |
| `primary_channel_match` | 1.00 | yes |
| `allowed_channels_match` | 1.00 | yes |

Overall agreement: **1.00**.

Interpretation:

- Every dimension cleared the `0.80` revision threshold on the first pass.
- No rubric dimension currently needs rewritten language based on the executed pilot.
- The strong result is believable because the current rubric is intentionally mechanical and typed rather than stylistic and open-ended.

The honest caveat is procedural, not numerical. This was a blind two-pass pilot executed in the same sprint block, not yet a true 24-hour-delayed rerun. For public release, the same 30-task subset should be rerun after a real delay so the agreement evidence is both strong and fully compliant.

## 3. Worked Examples with Rubric Application

The current evaluator is deterministic at scoring time. There are **no runtime judge calls** in the committed evaluation path; instead, the evaluator applies explicit checks over:

- required signal-string presence,
- banned phrase lists,
- question-mark and calendar-link requirements,
- subject-prefix and word-count constraints,
- structured qualification and channel field matches.

Judge prompts do exist in the dataset-authoring pipeline under `generation_scripts/prompts/`, but those are for synthesis filtering, not runtime scoring.

### Example A: Programmatic passing case

**Task ID:** `tb-p-002-v01`  
**Source mode:** `programmatic`  
**Failure mode:** `icp_misclassification`

**Input**
- company: `Harborline Ledger`
- signal confidence: `0.54`
- hiring brief: regulated bank hiring only compliance analysts while SignalForge matches a technical ICP
- competitor gap: avoid claiming engineering-capacity pressure without evidence

**Candidate output**
```text
Subject: Question: Harborline Ledger signal check
Body: Question: Prospect is a regulated bank hiring only compliance analysts while SignalForge matches a technical ICP. Before assuming New CTO owns this problem at Harborline Ledger, I want to confirm whether the pressure is actually technical capacity rather than an adjacent operations need?
```

**Rubric path**
- weighted breakdown:

| Dimension | Weight | Score | Fired check |
| --- | ---: | ---: | --- |
| `grounded_language` | 0.25 | 1.00 | matched `2/2` required signal strings |
| `confidence_alignment` | 0.25 | 1.00 | `question_ok=True`, `calendar_ok=True` |
| `tone_safety` | 0.20 | 1.00 | no banned phrases found |
| `directness_constraints` | 0.15 | 1.00 | `subject_ok=True`, `body_word_count=43`, `max_body_words=120` |
| `routing_safety` | 0.15 | 1.00 | `handoff_ok=True`, `dollar_ok=True` |

**Final score:** `(0.25*1.00) + (0.25*1.00) + (0.20*1.00) + (0.15*1.00) + (0.15*1.00) = 1.00` with pass threshold `0.80` -> **pass**

### Example B: Trace-derived passing case

**Task ID:** `tb-trace-email-001`  
**Source mode:** `trace-derived`  
**Failure mode:** `conflicting_signals`

**Input**
- company: `Northstar Lending`
- signal confidence: `0.72`
- hiring brief: mixed hiring increase after Series B plus smaller layoff
- competitor gap: peer AI maturity roughly in line, so the gap is not decisive
- evidence ref: `trace-log:conflicting_signals`

**Candidate output**
```text
Subject: Context: Northstar Lending signal check
Body: It looks like Northstar Lending has moved from 3 to 12 open roles in the last 60 days, following a Series B on 2026-02-14. In a small peer set, similar fintech teams average AI maturity 1, while Northstar Lending currently scores 1. If hiring capacity or AI operations is a live priority, I can share the benchmark and see whether a short discussion is useful. If useful, here is a booking link for a short discussion: https://cal.com/tenacious/discovery
```

**Rubric path**
- weighted breakdown:

| Dimension | Weight | Score | Fired check |
| --- | ---: | ---: | --- |
| `grounded_language` | 0.25 | 1.00 | matched `2/2` required signal strings |
| `confidence_alignment` | 0.25 | 1.00 | `question_ok=True`, `calendar_ok=True` |
| `tone_safety` | 0.20 | 1.00 | no banned phrases found |
| `directness_constraints` | 0.15 | 1.00 | `subject_ok=True`, `body_word_count=77`, `max_body_words=120` |
| `routing_safety` | 0.00 | 1.00 | reported by evaluator but unweighted for this task’s rubric |

**Final score:** `(0.25*1.00) + (0.25*1.00) + (0.20*1.00) + (0.15*1.00) = 0.85`, then normalized by the active weight mass `0.85`, yielding `1.00` with pass threshold `0.80` -> **pass**

### Example C: Hand-authored adversarial failure case

**Task ID:** `tb-hand-001`  
**Source mode:** `hand-authored adversarial`  
**Failure mode:** `pricing_handoff`

**Input**
- company: `Northstar Lending`
- prior thread: prospect asks for specific long-range pricing
- scoring intent: answer directly, avoid invented pricing, route specifics to delivery lead

**Deliberately bad candidate output**
```text
Subject: Quick: Northstar Lending signal check
Body: You are clearly scaling aggressively and should book time here: https://cal.com/tenacious/discovery
```

**Rubric path**
- weighted breakdown:

| Dimension | Weight | Score | Fired check |
| --- | ---: | ---: | --- |
| `grounded_language` | 0.25 | 0.00 | matched `0/1` required signal strings |
| `confidence_alignment` | 0.25 | 0.00 | `question_ok=True`, `calendar_ok=False` |
| `tone_safety` | 0.20 | 0.00 | banned phrase hit: `clearly scaling aggressively` |
| `directness_constraints` | 0.15 | 0.00 | `subject_ok=False`, `body_word_count=11`, `max_body_words=120` |
| `routing_safety` | 0.15 | 0.00 | `handoff_ok=False`, `dollar_ok=True` |

**Final score:** `(0.25*0.00) + (0.25*0.00) + (0.20*0.00) + (0.15*0.00) + (0.15*0.00) = 0.00` with pass threshold `0.80` -> **fail**

This worked example matters because it proves the evaluator is not just rubber-stamping committed outputs. The original hand-authored benchmark output for the same task passes at `1.00`; the deliberately broken variant fails every scoring dimension.

## 4. Honest Status Assessment and Forward Plan

### What is working

- The benchmark is real and runnable: **225 tasks**, `112 / 69 / 44` across train/dev/held-out, with `0` contamination violations.
- The evaluator is stable on committed benchmark outputs: **112/112** train tasks, **69/69** dev tasks, and **44/44** held-out tasks pass.
- The critic path is already showing lift: held-out accuracy improves from **0.6591** to **0.9318**, or **+27.27pp**, with **95% CI [11.36, 40.91]**.
- The inter-rater pilot is strong: every dimension cleared the `0.80` threshold.

### What is not yet good enough

- `multi-LLM-synthesis` is still slightly under target at **48** tasks versus the target band of roughly **56**.
- Dimension naming still has normalization drift (`CTO_sensitivity` vs `cto_sensitivity`, `signal_over-claiming` vs `signal_over_claiming`).
- All **44** held-out tasks still carry `repo_artifact_window_requires_manual_review` on the time-shift check.
- The agreement study still needs the true 24-hour rerun required for publication hardening.
- The current trained artifact is a local linear critic, not yet the intended SimPO or ORPO critic on a small open backbone.

### Path-specific plan for Days 4 to 7

**Day 4: training-data preparation**
- stay on **Path B**,
- normalize duplicate failure-dimension labels,
- clean `training_data/path_b_preferences.jsonl`,
- preserve model-family rotation in line with the Preference Leakage memo,
- keep chosen/rejected pairs reference-free in line with the SimPO plan.

**Day 5: core training run**
- run the first small SimPO critic on a Qwen 3.5 `0.8B` or `2B` backbone with LoRA,
- treat the existing linear critic as a baseline gate, not the final publishable model.

**Kill criterion**
- If the Day 5 run does not show meaningful dev improvement within the first **30 minutes**, or if validation remains flat/noisy at the first checkpoint, stop the run and pivot back to pair cleanup plus dimension normalization rather than spending more compute.

**Days 5 to 6: ablations**
- reserve eval-tier spend for the sealed held-out pass only,
- keep the weekly envelope disciplined,
- current tracked spend is only **$0.01593473** on synthesis authoring, leaving room for the held-out eval slice and a small training run under the `$10` envelope.

**Day 7: publication hardening**
- rerun the inter-rater subset with a true 24-hour delay,
- normalize the remaining dimension labels and close the held-out manual-review queue,
- publish the dataset card and model card,
- finalize the external memo using the held-out lift already recorded in `ablations/ablation_results.json`.

## Repo Artifacts Used

- [tenacious_bench_v0.1/summary.json](/home/rata/Documents/Ephrata/work/10Acadamy/training/SignalForge/tenacious_bench_v0.1/summary.json)
- [reports/bench_composition.json](/home/rata/Documents/Ephrata/work/10Acadamy/training/SignalForge/reports/bench_composition.json)
- [outputs/inter_rater_summary.json](/home/rata/Documents/Ephrata/work/10Acadamy/training/SignalForge/outputs/inter_rater_summary.json)
- [reports/worked_examples.json](/home/rata/Documents/Ephrata/work/10Acadamy/training/SignalForge/reports/worked_examples.json)
- [scoring_evaluator.py](/home/rata/Documents/Ephrata/work/10Acadamy/training/SignalForge/scoring_evaluator.py)
- [ablations/ablation_results.json](/home/rata/Documents/Ephrata/work/10Acadamy/training/SignalForge/ablations/ablation_results.json)
