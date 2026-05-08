# Question — Day 4

**Topic:** Evaluation and statistics  
**Asker:** Ephrata Nebiyu  
**Date:** 2026-05-08

## Final sharpened question

In my SignalForge Week 11 evaluation stack, I use a **paired bootstrap**
confidence interval and `p = 0.0` to support the claim that the current Path B
critic materially improves held-out accuracy, and I also report a perfect
`1.00` inter-rater pilot agreement on a 30-task subset. My gap is this:
**what do those numbers actually justify, and what do they not justify, at the
statistical-mechanism level?** More specifically: why is paired bootstrap the
right test for the held-out chosen/rejected critic comparison, what assumptions
does it preserve that an unpaired analysis would miss, and how should I
interpret a perfect inter-rater exact-match result on a deliberately mechanical
rubric without overstating what it means about human agreement or benchmark
validity?

## Why this is my real gap

I can already repeat the headline numbers:

- `+48.84pp` held-out lift
- `95% CI [34.88, 62.79]`
- paired bootstrap
- `p = 0.0`
- inter-rater exact-match agreement `1.00`

But I cannot yet defend the statistical meaning of those claims well enough.
If a senior engineer or researcher pushed me, I would struggle to explain:

- why the bootstrap is **paired**, not just any bootstrap
- what dependence structure is being preserved by resampling paired critic
  decisions
- why a confidence interval on benchmark lift is not the same as a guarantee of
  production performance
- why a perfect agreement pilot on a crisp rubric may reflect rubric
  mechanicality more than deep human consensus
- how to talk honestly about strong offline numbers without overselling them

That means I am currently using the statistics as decision support, but not yet
fully understanding the mechanism that makes those statistics appropriate.

## Grounding in my shipped work

Closing this gap would let me better defend and likely tighten:

- `reports/executive_memo.md`
- `reports/week11_status_report.md`
- `inter_rater_agreement.md`
- `ablations/ablation_results.json`
- any future deployment memo where I use offline lift and agreement numbers to
  justify rollout

Concretely, if this gap closes well, I expect to improve both the way I explain
the current critic result and the way I communicate the limits of the benchmark
and agreement study.

## Why this question is worth a day of research

This question is:

- **Diagnostic:** it names a specific statistical mechanism already used in my
  repo, not a generic question about evaluation.
- **Grounded:** it points to the exact artifacts where the project makes claims
  from those numbers.
- **Generalizable:** many FDE systems make rollout decisions from offline model
  comparisons, confidence intervals, and judge-agreement studies.
- **Resolvable:** a strong explainer could close it by connecting paired
  resampling, dependence structure, calibration of claims, and the difference
  between rubric reproducibility and broader validity.

## What a satisfying answer would need to do

A good answer would help me explain:

1. why paired bootstrap is the right fit for this held-out critic comparison
2. what would go wrong if I treated the two systems as independent samples
3. what a `95%` confidence interval and `p = 0.0` do and do not mean here
4. why `1.00` inter-rater exact-match agreement on a mechanical rubric is not
   the same as proving deep human consensus
5. how to communicate strong offline evidence honestly without overstating
   production readiness
