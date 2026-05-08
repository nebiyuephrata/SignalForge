# Sign-off — Day 4

**Asker (signing off):** Ephrata Nebiyu  
**Topic:** Evaluation and statistics — paired bootstrap, agreement, and what offline numbers justify  
**Date:** 2026-05-08

---

## Judgement

- [x] **Closed** — gap is closed; I can now defend the mechanism unaided.
- [ ] **Partially closed**
- [ ] **Not closed**

## What I understand now that I did not before

I can now explain that the key statistical issue is not just “what is the
number?” but “what dependence structure and capability claim does the number
preserve?” I understand why the critic comparison in SignalForge uses a
**paired** bootstrap rather than an unpaired one: the baseline and trained
systems are scored on the same held-out preference pairs, so the resampling
must preserve that per-example linkage instead of pretending the two systems are
independent. I also understand more clearly that a `95%` CI and `p = 0.0`
support a claim about benchmark lift on the sealed evaluation slice, not a
guarantee of equivalent production lift, and that a perfect `1.00` inter-rater
exact-match result on a deliberately crisp rubric is stronger evidence of rubric
reproducibility than of deep human consensus or broad benchmark validity.

## Residual gap (if partial / not closed)

_(N/A — closed after revision.)_
