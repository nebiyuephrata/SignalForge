# Explainer — Why SimPO Can Get Better At Rejection Faster Than Acceptance

**Written for:** Nureye Nigus  
**Topic:** Training and post-training mechanics — preference-tuned judges and asymmetric learning  
**Date:** 2026-05-07

---

## The question, anchored

In your Week 11 TheConversionEngine work, you chose Path B and trained a
preference-tuned judge because the failure pattern looked like inconsistency
near policy boundaries, not generally weak generation. But your evaluation
showed an uneven pattern: the judge became very strong on many `fail` and
`needs_human_review` rows while staying weaker on some `pass` and channel-policy
rows. That makes the natural question deeper than “did SimPO help?” The real
question is why pairwise preference training would produce **asymmetric
learning**: why a small judge can become sharper at spotting violations faster
than it becomes well-calibrated at recognizing acceptable outputs.

That matters because a critic that is excellent at rejection but weak at
acceptance can look strong on safety while still being a poor deployment gate.
The training-mechanics issue is not just accuracy. It is what the objective and
data format make easiest for the model to learn first.

## The load-bearing mechanism

SimPO is a **pairwise preference objective**. The model is not trained to assign
an absolute label like “good,” “bad,” or “safe.” Instead, it is trained to give
the chosen output a higher score than the rejected output by some margin. That
changes what counts as an easy solution to the optimization problem.

For a small LoRA judge, the easiest way to win that objective is often not to
build a deep latent notion of “commercially acceptable response.” The easiest
way is to find features that reliably separate chosen from rejected pairs with
minimal representational effort.

If many rejected examples contain obvious surface signals like:

- policy-violating phrasing
- banned lexical patterns
- missing required strings
- strong over-assertion markers
- structurally wrong channel choices

then the model can improve quickly by learning a high-weight rejection boundary
around those features. It does not yet need a comparably rich notion of what a
*good enough pass* looks like. Rejection can be learned as “spot the violation.”
Acceptance often requires something subtler: “this output is acceptable because
it balances tone, grounding, usefulness, and policy fit without any single
obvious cue.”

That is the asymmetry. **Violation detection is often sparse and local.
Acceptance is often compositional and calibrated.**

## Why pairwise objectives encourage that asymmetry

### 1. Pairwise training only needs separability, not full calibration

SimPO does not ask: “Is this output truly acceptable on an absolute scale?” It
asks: “Can you rank this chosen output above this rejected one?” If the model
can do that using a handful of cheap signals, the loss improves.

So if a rejected sample says something like:

- “book here” when booking is not allowed
- “clearly scaling aggressively”
- a too-confident claim on thin evidence

the model can win by strongly down-weighting those patterns. That produces
strong rejection behavior. But nothing in that setup forces the model to build a
smooth internal scale where many different valid positive examples are all
recognized as acceptable with equal confidence.

### 2. Negative cues are often more consistent than positive cues

In real agent data, “bad” examples are often bad in repeated, compressible ways.
They violate the same policies again and again. “Good” examples are usually more
diverse. There are many ways to be acceptable.

That means the rejected half of the pair distribution may have lower entropy
than the chosen half:

- rejections cluster around a few sharp failure patterns
- acceptable outputs vary in style, tone, brevity, and channel expression

A small judge can therefore learn a compact boundary for rejection earlier than
it can learn a robust manifold for acceptance.

### 3. Margin objectives reward whatever feature creates the cleanest gap

SimPO introduces a target reward margin. That is helpful, but it also means the
optimizer is actively looking for features that create a stable distance between
chosen and rejected outputs. If lexical or policy-surface cues produce that gap
cheaply, the model will use them first.

This is not a bug in SimPO specifically. It is a general feature of preference
optimization: the objective does not care *why* the ranking works, only that the
ranking works. If the data allows shortcut separation, the model has little
reason not to take it.

## Why `fail` and `needs_human_review` can improve faster than `pass`

This follows directly from the mechanism above.

`fail` and `needs_human_review` rows often contain:

- explicit policy violations
- obvious unsupported claims
- clearer structural channel mismatches
- strong reasons for rejection

Those are easier to learn as boundaries.

`pass` rows are harder because acceptance is usually not defined by a single
surface marker. A “pass” may need:

- enough grounding, but not too much verbosity
- enough usefulness, but not unsafe confidence
- the correct channel, but also the right social calibration
- tone that is compliant but still commercially useful

In other words, rejection can often be solved as **boundary detection**.
Acceptance usually requires **calibrated composition** across multiple
dimensions.

That is why your judge can become visibly better at finding problems while still
remaining uneven at confidently recognizing “this is fine.”

## Why this differs from SFT or prompt-only iteration

### SFT

Supervised fine-tuning teaches the model to imitate target outputs directly. If
you trained on accepted outputs only, the model would get more exposure to the
distribution of what “good” looks like. That can help positive-class fluency or
style consistency. But it would not necessarily teach the sharp contrastive
boundary that makes a judge good at ranking near-miss failures against strong
outputs.

So SFT is often better at **pattern imitation**, while preference tuning is
often better at **relative discrimination**.

### Prompt-only changes

Prompt iteration can move behavior, but it does not change the learned scoring
geometry of the model. It may help the model attend to the right rubric, but it
does not change what features the judge has internalized as high-signal ranking
cues.

That is why a post-training asymmetry is not something you should expect prompt
engineering alone to fix. If the learned representation treats policy violations
as easier signals than positive acceptability, then the data and objective need
to change.

## Why harder negatives matter so much

This is the most important practical implication.

If your rejected examples are too easy, then the model can separate pairs using
cheap cues. Harder negatives are not just “more challenging examples.” They
reshape the reward landscape.

A lexically compliant but commercially weak negative forces the model to stop
relying on:

- banned-phrase detection
- obvious formatting errors
- shallow tone heuristics
- crude channel-rule violations

and start learning deeper distinctions like:

- useful vs generic
- grounded confidence vs empty caution
- acceptable handoff vs passive deflection
- commercially relevant channel choice vs mechanically allowed channel choice

That is exactly why harder negatives can improve acceptance calibration. They
force the model to learn features that matter *within the region where surface
compliance is already satisfied*.

## A simple mental model

Think of the judge as learning a scoring function.

If the pair distribution looks like:

- chosen: mostly compliant  
- rejected: often obviously noncompliant

then the score function can learn:

> “Down-rank clear violations.”

That produces strong rejection behavior.

If you instead add pairs like:

- chosen: grounded, useful, commercially specific  
- rejected: lexically compliant, policy-safe, but generic and unhelpful

then the model must learn:

> “Among compliant outputs, prefer the commercially stronger one.”

That is the step that moves the judge from being a safety detector toward being
a calibrated production critic.

## What this implies for production readiness

A judge that is much better at rejection than acceptance is not necessarily bad.
It may still be useful as a conservative safety gate. But it is not yet a fully
calibrated deployment critic if:

- it over-flags acceptable outputs
- it hesitates on legitimate `pass` rows
- it confuses lexical safety with commercial usefulness

So the right conclusion is not “SimPO failed.” It is:

1. the objective learned the easiest discriminative boundary available,
2. the data likely made negative-class separation easier than positive-class
   calibration,
3. the next improvement should come from **harder pair design**, especially
   lexically compliant but commercially weak negatives,
4. evaluation should separate “good at rejection” from “good at calibrated
   acceptance.”

## Bottom line

SimPO can improve rejection faster than acceptance because pairwise preference
training only requires the model to rank chosen above rejected, and the easiest
way for a small judge to do that is often to learn sharp, low-cost negative
cues before it learns a richer notion of what acceptable outputs look like.

That asymmetry is especially likely when rejected samples are more repetitive,
more local, and more lexically obvious than chosen samples are diverse and
compositional. Harder negatives help not because they are “harder” in the
abstract, but because they remove shortcut separability and force the model to
learn the deeper features that real deployment depends on.

## Pointers

- SimPO paper: <https://arxiv.org/abs/2405.14734>
- LLM-as-a-Judge survey: <https://arxiv.org/abs/2411.15594>
- Preference Leakage paper: <https://arxiv.org/abs/2502.01534>
