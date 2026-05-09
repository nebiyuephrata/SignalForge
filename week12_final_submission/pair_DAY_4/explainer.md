# Explainer — Why Aggregate Metrics Hide Real LLM Failures

**Written for:** Amare Kassa  
**Topic:** Evaluation and statistics — aggregate metrics, subgroup effects, and metric validity  
**Date:** 2026-05-08

---

## The question, anchored

Your Week 10/11 evaluation pipeline produced a pattern that many LLM systems
run into: the global metrics looked reassuring, but later debugging showed that
important failures were hiding inside specific conditions. A mean pairwise
similarity around `0.415` suggested there was no global response collapse, yet
condition-level inspection showed multiple baseline traces reusing the same
fallback response across unrelated probe categories. Likewise, your judge gave
too much credit to fluency, confident tone, and tidy formatting while
under-penalizing generic template reuse, missed constraints, and absent probe
grounding.

So the real question is not “why was the metric wrong?” The real question is
why aggregate metrics can look healthy even when important behavior is broken,
and what evaluation-design principles tell us when to trust a global score
versus when to slice by condition, category, or failure mode.

## The load-bearing mechanism

An aggregate metric is a **compression**. It maps many behaviorally different
cases into one number. That compression is useful only if the cases being
averaged are meaningfully homogeneous with respect to the capability you care
about. When they are not, the average can be numerically correct and still
behaviorally misleading.

In other words: **the problem is not that the average lies; the problem is that
it erases structure.**

If your system behaves one way on grounded retrieval probes, another way on
fallback routing probes, and a third way on policy-sensitive probes, then a
single global score is combining multiple conditional distributions. Once that
happens, the aggregate can look stable even though one subgroup is collapsing.

## Why averages hide important structure

### 1. Averages collapse variance and subgroup identity

Suppose you have four probe categories:

- grounded retrieval
- routing / fallback
- constraint following
- policy-sensitive handling

If the model performs well on three and badly on one, the mean can still look
fine. But operationally, that one failing category may be the category that
matters most.

This is a classic statistical issue: a mean is sensitive to the **weighted
mixture**, not to whether one subgroup is broken. If the broken subgroup is
small, or if the other categories are easier and more numerous, then the global
metric can dilute the failure.

### 2. Distribution mixtures can hide multimodality

A global metric often assumes you are summarizing one distribution. But LLM
evaluation pipelines frequently produce **mixtures** of qualitatively different
cases. For example:

- some prompts demand retrieval-grounded synthesis
- some trigger deterministic fallbacks
- some test style under weak evidence
- some test routing correctness

If those subpopulations behave differently, then the overall distribution may be
multimodal. A single mean similarity or pass rate hides that shape. You lose the
fact that one mode is healthy while another is broken.

This is why a “non-alarming” average pairwise similarity can coexist with
condition-specific collapse. The mean only tells you the overall center of the
mixture. It does not tell you whether one component of the mixture has become
degenerate.

### 3. Aggregate metrics reward dominant easy cases

If most examples are easy, then the metric mostly measures performance on easy
examples. Hard or rare failure modes become statistically diluted.

This matters especially in LLM evaluation because production risk is often
concentrated in:

- rare edge cases
- policy boundaries
- routing failures
- low-confidence conditions
- subgroup-specific failures

A benchmark average reflects what is common in the dataset, not necessarily what
is costly in production.

## Why your similarity metric looked okay while collapse was happening

This is a good example of how metric semantics matter.

A mean pairwise similarity over all outputs is only a coarse summary of surface
response similarity. It does **not** directly measure “absence of collapse” in
the operational sense you care about. If some categories produce genuinely
varied outputs while others reuse a single fallback template, the varied cases
can keep the global average away from the alarming extreme even though one
condition is already collapsed.

So the metric was not useless. It was answering a different question:

> “What is the average similarity across the whole output pool?”

But your actual operational question was narrower:

> “Are certain conditions degenerating into repeated fallback behavior?”

Those are not the same capability. The first is global surface redundancy. The
second is condition-specific behavioral collapse.

That is the core lesson in metric validity: **a metric is only trustworthy when
its operational meaning matches the capability claim you are making from it.**

## Why the judge rewarded the wrong behavior

The same principle explains your judge issue.

If the judge prompt or scoring setup overweights:

- fluency
- confidence
- formatting cleanliness
- local coherence

then the judge may correlate with “looks polished” rather than “satisfies the
probe.” That means the evaluator itself is partially aligned to the wrong latent
target.

This is not just “judge error.” It is a form of **construct mismatch**. The
metric or judge score is not fully measuring the intended capability. It is
measuring a proxy that overlaps with the capability but does not define it.

In your case, “good-looking answer” and “probe-grounded, constraint-faithful,
non-template answer” are overlapping but different constructs. Once that gap
exists, aggregate judge scores can systematically hide the failures you care
about.

## When global metrics are trustworthy

A global metric is more trustworthy when these conditions hold:

1. **The evaluation set is behaviorally homogeneous enough** that one summary
   number corresponds to one coherent capability.
2. **Subgroups are balanced or intentionally weighted** so that rare but
   important failures are not drowned out.
3. **The metric has construct validity** — it really measures the capability
   being claimed.
4. **Slice metrics agree with the global trend** — no important subgroup is
   moving in the opposite direction.

If those conditions are not true, the global score should be treated as a top
line, not as the real diagnosis.

## When slicing is mandatory

For FDE work, slicing is not optional whenever:

- the system is multi-stage
- the dataset mixes qualitatively different task types
- some failures are rare but high-cost
- the judge may be rewarding proxies
- the benchmark is built from multiple authoring routes
- different customer conditions map to different failure risks

In those situations, you should expect subgroup effects and inspect them
directly.

Good slices are not random. They should correspond to plausible mechanisms:

- probe category
- routing path
- confidence bucket
- failure mode
- input source mode
- channel or action type
- presence or absence of retrieval evidence

The point of slicing is not “make more charts.” It is to expose the hidden
conditional structure of the system.

## How to partition datasets so failures are observable

A good evaluation partition is not just train/dev/held-out. It is also a
**semantic partition**.

You want categories that correspond to different failure-generating mechanisms.
For example:

- fallback-eligible vs retrieval-grounded
- policy-sensitive vs style-only
- short-context vs long-context
- straightforward pass cases vs near-boundary pass cases
- deterministic constraint probes vs open-ended synthesis probes

If failure modes are mixed together without those partitions, important problems
become statistically diluted inside the average.

This is why your later debugging was so valuable: once you grouped traces by
condition and probe category, the response-collapse pattern became visible.
That means the diagnostic unit was not “all outputs.” It was “outputs within the
same condition family.”

## A practical rule for metric validity

Here is the simplest decision rule:

Before trusting a metric, ask:

> “If this number improved, what exact capability improved?”

If you cannot answer that clearly, the metric is too indirect to carry the
claim on its own.

Then ask:

> “Could one important subgroup get worse while this number still improves or
stays flat?”

If the answer is yes, then the global metric is insufficient without slices.

Those two questions catch most metric-validity failures in practice.

## A useful mental model

Think of evaluation in two layers:

### Layer 1: Global summaries

These are for:

- trend tracking
- quick regressions
- coarse model comparison
- top-line reporting

### Layer 2: Mechanism-aware slices

These are for:

- debugging
- failure attribution
- safety validation
- determining whether the global score is actually meaningful

A mature evaluation stack needs both. If you only have slices, you lose the
headline summary. If you only have aggregates, you lose the real behavior.

## What this implies for your redesign

Your evaluation redesign should probably do three things:

1. **Keep the aggregate metrics**, but stop treating them as sufficient.
2. **Add mandatory condition-level and failure-mode slices** for all critical
   capabilities.
3. **Revise the judge or rubric so it scores the intended construct more
   directly**, especially grounding, constraint faithfulness, and template reuse.

That moves the evaluation system from “plausible-looking summary numbers” toward
“numbers that preserve operationally important structure.”

## Bottom line

Aggregate metrics hide LLM failures because they summarize mixtures of
behaviorally different cases into one number, and that compression can dilute
rare, conditional, or subgroup-specific failures even when those failures are
operationally critical.

The right question is never just “what is the average?” It is “average over
what distribution, for what capability, and with what hidden subgroup
structure?” Once that is clear, the rule becomes simple: trust a global metric
for coarse reporting only when the capability is sufficiently homogeneous and
slice results agree; otherwise, treat slicing by condition, category, or failure
mode as mandatory, because that is where real LLM failures become visible.

## Pointers

- *The Harmful Dysfunction of Benchmark Datasets in AI Evaluation* — for how
  benchmark summaries can hide important structure in what is being measured.
- *A Survey on LLM-as-a-Judge* — for judge validity, proxy measurement, and why
  evaluator alignment matters.
- Simpson's paradox / subgroup analysis literature — for the broader statistical
  principle that aggregate trends can mask subgroup behavior.
