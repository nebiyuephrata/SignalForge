# Question — Day 3

**Topic:** Training and post-training mechanics  
**Asker:** Ephrata Nebiyu  
**Date:** 2026-05-07

## Final sharpened question

In my Week 11 SignalForge Path B work, the unresolved training failure I named
was that the current critic can still over-value **lexical compliance** on
medium-confidence email tasks: if a draft is short, question-led, avoids banned
phrases, and mentions the required strings, the model can score it as preferred
even when the business ask is still too generic to be commercially useful. My
gap is this: **what is it about pairwise preference training, especially
SimPO/ORPO-style objectives and chosen/rejected data formatting, that makes a
small judge learn surface-form shortcuts more easily than deeper commercial
usefulness?** And why would adding harder negatives that remain lexically
compliant but differ in business value help in a way that supervised fine-tuning
or prompt-only changes would not?

## Why this is my real gap

I can already say at a high level that “the model is latching onto shortcuts,”
but I cannot yet defend the training-mechanics reason that this happens. If a
senior engineer pushed me, I would struggle to explain:

- why pairwise preference objectives may reward separability on easy cues before
  they reward deeper judgment
- how the chosen/rejected format shapes what margins the model actually learns
- why a small LoRA judge might internalize lexical signals faster than latent
  commercial quality
- why harder negatives are not just “more data,” but a change to the reward
  geometry the model sees during post-training

That means I am still using the phrase “shortcut learning” descriptively, not
mechanistically.

## Grounding in my shipped work

Closing this gap would let me better defend and likely refine:

- `reports/executive_memo.md` — unresolved lexical-shortcut failure
- `methodology_rationale.md` — why Path B is the right route
- `training_data/path_b_preferences.jsonl`
- any future SimPO / ORPO rerun where I redesign negatives for better critic
  calibration

Concretely, if this gap closes well, I expect to improve both the way I explain
the current critic’s limitations and the way I design the next round of
preference data.

## Why this question is worth a day of research

This question is:

- **Diagnostic:** it names a precise failure mode already present in my repo,
  not a generic curiosity about post-training.
- **Grounded:** it points to a real unresolved issue in the current Path B
  artifact.
- **Generalizable:** many preference-tuned judges and reward models fail by
  learning superficial but predictive cues.
- **Resolvable:** a strong explainer could close this by connecting pairwise
  objectives, margin learning, hard-negative design, and calibration.

## What a satisfying answer would need to do

A good answer would help me explain:

1. why preference objectives can amplify shortcut features
2. how chosen/rejected pair construction shapes what the model finds easiest to
   separate
3. why lexically compliant but commercially weak negatives are especially
   important
4. how this differs from what SFT or prompt-only iteration would teach
5. what this implies for deciding whether the critic is actually production-ready
