# Week 11 Status Report

## 1. Bench Composition Reporting

The current benchmark release is **225 tasks**. The partition target was `50/30/20`; actuals are `112 / 69 / 44`, or `49.8% / 30.7% / 19.6%`. That is close enough to target that the remaining methodological risk is not split size. The sharper remaining issues are a mild underweight on synthesis tasks and a few legacy dimension labels that still need normalization.

The source-mode target was `30/30/25/15` for `trace-derived / programmatic / multi-LLM synthesis / hand-authored`. Actuals are:

| Source mode | Target share | Target count @225 | Actual count | Actual share | Deviation |
| --- | ---: | ---: | ---: | ---: | ---: |
| `trace-derived` | 30.0% | 68 | 69 | 30.7% | +1 |
| `programmatic` | 30.0% | 68 | 72 | 32.0% | +4 |
| `multi-LLM-synthesis` | 25.0% | 56 | 48 | 21.3% | -8 |
| `hand-authored` | 15.0% | 34 | 36 | 16.0% | +2 |

This is now a credible composition story. The benchmark is no longer dominated by a single authoring mode. The remaining deviation is mostly that `multi-LLM-synthesis` is still slightly under target, and some older rows still carry unnormalized dimension names.

Integrated cross-tabulation follows. From a single look, the reader can answer questions like “how many held-out multi-LLM synthesis tasks target `cto_sensitivity`?” or “how many trace-derived `conflicting_signals` tasks are in dev?”

| Dimension | train:trace-derived | train:programmatic | train:multi-llm-synthesis | train:hand-authored | dev:trace-derived | dev:programmatic | dev:multi-llm-synthesis | dev:hand-authored | held_out:trace-derived | held_out:programmatic | held_out:multi-llm-synthesis | held_out:hand-authored | Total |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bench_to_brief_match | 0 | 0 | 0 | 6 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 6 |
| conflicting_signals | 4 | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 8 |
| conflicting_signals_channel_plan | 4 | 0 | 0 | 0 | 3 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 8 |
| conflicting_signals_qualification | 4 | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 8 |
| coordination_failures | 0 | 2 | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 2 | 0 | 0 | 6 |
| cost_issues | 0 | 4 | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 6 |
| cto_sensitivity | 0 | 0 | 4 | 0 | 0 | 0 | 2 | 0 | 0 | 2 | 2 | 0 | 10 |
| defensive_reply_recovery | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 6 | 0 | 0 | 0 | 0 | 6 |
| gap_over_claiming | 0 | 4 | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 6 |
| icp_misclassification | 0 | 2 | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 2 | 0 | 0 | 6 |
| multi_thread_leakage | 0 | 4 | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 6 |
| new_cto_transition | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 6 | 6 |
| no_hiring_signals | 3 | 0 | 0 | 0 | 3 | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 8 |
| no_hiring_signals_channel_plan | 5 | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 8 |
| no_hiring_signals_qualification | 3 | 0 | 0 | 0 | 3 | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 8 |
| outsourcing_mismatch | 0 | 2 | 4 | 0 | 0 | 2 | 2 | 0 | 0 | 2 | 2 | 0 | 14 |
| outsourcing_perception | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 |
| pricing_handoff | 0 | 0 | 4 | 6 | 0 | 0 | 2 | 0 | 0 | 0 | 2 | 0 | 14 |
| scheduling_calibration | 0 | 0 | 4 | 0 | 0 | 0 | 4 | 0 | 0 | 0 | 0 | 0 | 8 |
| scheduling_edge_cases_eu_us_africa | 0 | 2 | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 2 | 0 | 0 | 6 |
| signal_over_claiming | 0 | 4 | 4 | 0 | 0 | 2 | 2 | 0 | 0 | 0 | 2 | 0 | 14 |
| signal_reliability | 0 | 2 | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 2 | 0 | 0 | 6 |
| soft_defer_graceful_close | 0 | 0 | 0 | 6 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 6 |
| tone_drift | 0 | 4 | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 6 |
| warm_reply_grounded_answer | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 6 | 0 | 0 | 0 | 0 | 6 |
| weak_confidence | 4 | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 7 |
| weak_confidence_channel_plan | 3 | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 7 |
| weak_confidence_handling | 0 | 4 | 4 | 0 | 0 | 2 | 2 | 0 | 0 | 2 | 2 | 0 | 16 |
| weak_confidence_qualification | 4 | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 7 |
| Total | 34 | 36 | 24 | 18 | 21 | 22 | 14 | 12 | 14 | 14 | 10 | 6 | 225 |

One alignment note: this table still exposes a few near-duplicate label families inherited from earlier authoring passes. The report leaves those visible instead of silently merging them, because that cleanup belongs in the dataset rows, not in the prose.

## 2. Inter-Rater Agreement Results Analysis

Metric used: **per-dimension exact-match agreement** on a 30-task, hand-labeled subset, scored across two blind passes.

Protocol used:

1. sample 30 tasks spanning source modes and task types,
2. label pass 1,
3. reshuffle the same subset,
4. label pass 2 blind to the first ordering,
5. compute exact-match agreement per dimension.

Per-dimension agreement results:

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

The honest interpretation is not “humans never disagree.” It is that the current rubric is deliberately crisp and mechanical enough that the same labels reproduce cleanly under blind relabeling. Every dimension cleared the `0.80` trigger on the first pass, so no rubric revision loop was required in the executed pilot. The remaining caveat is procedural rather than numerical: this was still a same-sprint blind pilot, not yet a true 24-hour-separated rerun.

## 3. Worked Examples with Rubric Application

The current v0.1 scoring evaluator is **deterministic at runtime**. No runtime judge call is invoked during scoring; the evaluator applies explicit presence checks, banned-phrase checks, subject-prefix checks, calendar-link checks, and structured field matches. Judge prompts exist in the authoring pipeline under `generation_scripts/prompts/`, but not in the runtime scoring path.

### Example A: Programmatic task, passing case

**Task ID:** `tb-p-002-v01`  
**Source mode:** `programmatic`  
**Failure mode:** `icp_misclassification`

**Input fields**
- company: `Harborline Ledger`
- signal confidence: `0.54`
- hiring brief: regulated bank hiring only compliance analysts while SignalForge matches a technical ICP
- competitor gap: message should avoid claiming engineering pressure without evidence

**Candidate output**
```text
Subject: Question: Harborline Ledger signal check
Body: Question: Prospect is a regulated bank hiring only compliance analysts while SignalForge matches a technical ICP. Before assuming New CTO owns this problem at Harborline Ledger, I want to confirm whether the pressure is actually technical capacity rather than an adjacent operations need?
```

**Mechanical scoring path**
- `grounded_language`: matched `2/2` required strings (`harborline`, `technical`) -> `1.0`
- `tone_safety`: no banned phrases -> `1.0`
- `confidence_alignment`: question mark required and present; calendar link not required and absent -> `1.0`
- `directness_constraints`: subject prefix allowed, body under `120` words -> `1.0`
- `routing_safety`: no handoff phrase required, no dollar-sign violation -> `1.0`

**Final score:** `1.00` against pass threshold `0.80` -> **pass**

### Example B: Trace-derived task, passing case

**Task ID:** `tb-trace-email-001`  
**Source mode:** `trace-derived`  
**Failure mode:** `conflicting_signals`

**Input fields**
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

**Mechanical scoring path**
- `grounded_language`: matched `2/2` required strings -> `1.0`
- `tone_safety`: no banned phrases -> `1.0`
- `confidence_alignment`: no question required; calendar link required and present -> `1.0`
- `directness_constraints`: subject prefix allowed, body under `120` words -> `1.0`

**Final score:** `1.00` against pass threshold `0.80` -> **pass**

### Example C: Hand-authored adversarial task, deliberate failure case

**Task ID:** `tb-hand-001`  
**Source mode:** `hand-authored adversarial`  
**Failure mode:** `pricing_handoff`

**Input fields**
- company: `Northstar Lending`
- prior thread: prospect asks for specific long-range pricing
- rubric intent: give a bounded answer, do not invent numbers, and route pricing specifics to a delivery lead

**Deliberately bad candidate output**
```text
Subject: Quick: Northstar Lending signal check
Body: You are clearly scaling aggressively and should book time here: https://cal.com/tenacious/discovery
```

**Mechanical scoring path**
- `grounded_language`: matched `0/1` required strings -> `0.0`
- `tone_safety`: banned phrase hit (`clearly scaling aggressively`) -> `0.0`
- `confidence_alignment`: calendar link not allowed here and present -> `0.0`
- `directness_constraints`: subject prefix `Quick:` not allowed -> `0.0`
- `routing_safety`: required handoff phrase `our delivery lead will follow up within 24 hours` missing -> `0.0`

**Final score:** `0.00` against pass threshold `0.80` -> **fail**

This matters because it shows the evaluator discriminating rather than rubber-stamping. The original hand-authored benchmark output passes at `1.00`; the deliberately wrong variant fails every scored dimension.

## 4. Honest Status Assessment and Forward Plan

### What is working

- The benchmark is real and machine-runnable: `225` tasks with `112 / 69 / 44` train/dev/held-out and `0` contamination violations.
- The evaluator is mechanically stable: `112/112` train tasks, `69/69` dev tasks, and `44/44` held-out tasks pass their committed benchmark outputs.
- The critic path is directionally promising: the current local Path B linear critic lifts held-out accuracy from `0.6591` to `0.9318`, a `+27.27pp` gain with `95% CI [11.36, 40.91]`.
- The inter-rater pilot is numerically clean: every dimension cleared the `0.80` bar on the first pass.

### What is weak or still risky

- Dimension labels still contain naming drift such as `CTO_sensitivity` versus `cto_sensitivity` and `signal_over-claiming` versus `signal_over_claiming`.
- The held-out contamination check is clean, but all `44` held-out tasks still require manual time-shift review before a polished public release.
- `multi-LLM-synthesis` remains slightly under target at `48` tasks versus the target band of roughly `56`.
- The inter-rater result is numerically strong but still lacks the required 24-hour second-pass separation.
- The current trained artifact is a local linear critic, not yet the planned GPU-backed SimPO or ORPO run on a small open backbone.

### Days 4 to 7 plan

**Day 4: training-data preparation**
- Keep Path B.
- Clean and normalize `training_data/path_b_preferences.jsonl`, especially around duplicate failure-dimension labels and source-mode provenance.
- Follow the path-specific reading logic from SimPO and Preference Leakage: chosen/rejected pairs stay reference-free, and generator/judge model families remain rotated.

**Day 5: core training run**
- Run the first small SimPO critic on a Qwen 3.5 `0.8B` or `2B` backbone with LoRA.
- Use the current linear critic as the baseline gating artifact, not as the final published model.

**Kill criterion**
- If the Day 5 run does not show meaningful dev improvement within the first `30` minutes, or if validation behavior is flat/noisy after the first early checkpoint, kill the run and pivot back to preference-pair cleanup plus dimension-label normalization instead of spending more compute.

**Days 5 to 6: ablations**
- Reserve the eval-tier spend for the sealed held-out pass only.
- Current spending is `$0.01593473` on synthesis authoring and `$0.00` on training/eval in this environment.
- Remaining budget envelope still comfortably supports the brief’s intended split: roughly `$2-3` held-out eval, `$0-5` training, and `$1-2` reserve.

**Day 7: publication hardening**
- rerun the inter-rater subset with a true 24-hour delay,
- normalize the remaining dimension-label drift and close the held-out manual-review queue,
- publish the dataset card and model card,
- finalize the external memo using the held-out lift numbers already present in `ablations/ablation_results.json`.
