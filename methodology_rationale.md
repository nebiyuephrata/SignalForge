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

That is also why the benchmark emphasizes:

- confidence-conditioned language
- benchmark-safe competitor framing
- qualification correctness
- channel/booking state consistency

## Paper-grounded rationale

Two paper families shaped this choice most directly.

First, the **LLM-as-a-Judge survey** argues that judge reliability depends on careful attention to consistency, bias, and scenario adaptation. That matches this project closely: Tenacious does not need a judge that is universally eloquent, it needs one that is narrow, reliable, and calibrated for one outbound workflow.  
Source: https://huggingface.co/papers/2411.15594

Second, **SimPO** is the preference objective I would start with for the first training run because it removes the need for a reference model and is explicitly positioned as simpler and more compute-efficient than DPO while staying strong on preference benchmarks. That matters in this repo because the Week 11 cost envelope is tight and the training set is relatively small.  
Source: https://huggingface.co/papers/2405.14734

I am also explicitly adopting the warning from **Preference Leakage**: the same or closely related model family should not generate the chosen/rejected rewrites and then grade them. For Tenacious-Bench, that means generator family, cheap judge family, and eval-tier judge family should be rotated deliberately.  
Source: https://huggingface.co/papers/2502.01534

## Practical consequence

The concrete plan is:

1. use Tenacious-Bench to score the current Week 10 agent,
2. train a small Path B critic on `training_data/path_b_preferences.jsonl`,
3. deploy that critic as a rejection-sampling or rollback layer ahead of outbound delivery,
4. measure whether the critic improves held-out benchmark performance without materially increasing latency or cost.

That path matches both the evidence and the budget. It also preserves the strongest part of the current system: the deterministic-first structured-brief pipeline.
