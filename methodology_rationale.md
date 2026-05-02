# Methodology Rationale

## Why Path B

I selected **Path B: preference-tuned judge or critic** because the strongest Week 10 evidence points to an inconsistency problem, not a pure generation-capability problem. SignalForge can already produce acceptable, grounded outreach in many cases. The failure is that it does not always know when its own output has crossed the line from useful synthesis into over-claiming, tone drift, or socially clumsy benchmarking.

That pattern shows up clearly in the Week 10 evidence:

- Langfuse trace `2713c015315570e24157833b466ca775` stayed narrow and grounded even after provider retries, which suggests the base workflow already knows how to produce acceptable output.
- Langfuse trace `2bc8574e0954a3902393c025758f243c` drifted toward a broader template-style pitch under similar operating conditions.
- Langfuse trace `47ab214adf0bc2f1ee3a762ebd3afb78` remained technically plausible but read more like generic startup outbound than Tenacious-calibrated outreach.

Those three traces, together with the Week 10 confidence analysis showing over-claiming dropping from `62%` to `25%`, suggest the leverage point is a better critic layer that can gate, rewrite, or reject weak outputs before they ship.

## Why not Path A first

Path A would improve phrasing, but it would not directly solve the underlying business problem. Tenacious is not primarily hurt by awkward wording; it is hurt when the system sends a fluent message that is wrong in confidence, routing, or social calibration. In other words, the expensive failures are judgment failures.

The practical dismissal is:

- Week 10 already showed acceptable generations in traces `2713c015315570e24157833b466ca775`, `1d08f6e1a9f4db0c23a48c5f728f7b2d`, and `47ab214adf0bc2f1ee3a762ebd3afb78`.
- The misses were inconsistent restraint, not missing language capacity.
- A generator-only adapter would therefore optimize the part of the system that is already sometimes good while leaving the safety gate weak.

That is also why the benchmark emphasizes:

- confidence-conditioned language
- benchmark-safe competitor framing
- qualification correctness
- channel/booking state consistency

## Paper-grounded rationale

Two paper families shaped this choice most directly.

First, the **LLM-as-a-Judge survey** is directly relevant in three specific places: Section `2.1.1` on score generation, Section `2.1.3` on pairwise comparisons, and the survey roadmap into Sections `3` and `4` on improving and evaluating judge reliability. That matches this repo closely because Tenacious does not need a universally eloquent evaluator; it needs a narrow judge that can score groundedness, tone safety, and routing correctness consistently on a fixed workflow.  
Source: https://arxiv.org/abs/2411.15594

Second, **SimPO** is the preference objective I would start with for the first training run because Section `2.2` introduces a reference-free reward aligned with generation, Section `2.3` adds the target reward margin, and Section `4.3` discusses how margin size affects generation quality. That matters here because the Week 11 budget is tight, the training set is small, and the repo benefits from a lighter objective than a reference-model-dependent alternative.  
Source: https://arxiv.org/abs/2405.14734

I am also explicitly adopting the warning from **Preference Leakage**: the paper’s framing defines three relatedness modes between generator and judge models, namely same-model, inheritance, and same-family relatedness. For Tenacious-Bench, that means generator family, cheap judge family, and eval-tier judge family should be rotated deliberately, and the repo now includes a regression test for that routing guard so the same family cannot both generate and judge the same synthesis path.  
Source: https://arxiv.org/abs/2502.01534

## Why not Path C first

Path C would be defensible only if the main Week 10 failure were long-horizon trajectory control, multistep reasoning across branches, or process supervision. That is not what the evidence shows. The dominant failures in traces `2bc8574e0954a3902393c025758f243c`, `47ab214adf0bc2f1ee3a762ebd3afb78`, and `2713c015315570e24157833b466ca775` are still local judgment failures inside otherwise plausible outputs: over-claiming, tone drift, poor calibration, and socially wrong benchmarking. A PRM-first route would therefore solve a more complex problem than the repo currently needs to solve.

The practical dismissal is:

- there is little evidence that multistep search or branch selection is the bottleneck,
- the benchmark tasks are mostly single-turn judgment checks,
- a PRM route would add more implementation complexity than the current failure mode justifies.

## Practical consequence

The concrete plan is:

1. use Tenacious-Bench to score the current Week 10 agent,
2. train a small Path B critic on `training_data/path_b_preferences.jsonl`,
3. deploy that critic as a rejection-sampling or rollback layer ahead of outbound delivery,
4. measure whether the critic improves held-out benchmark performance without materially increasing latency or cost.

That path matches both the evidence and the budget. It also preserves the strongest part of the current system: the deterministic-first structured-brief pipeline.
