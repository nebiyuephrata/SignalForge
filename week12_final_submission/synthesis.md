# Week 12 Synthesis

Week 12 changed the center of gravity of my portfolio. Weeks 10 and 11 were
about shipping systems, probes, and benchmarks. Week 12 was about finding the
places where I could still describe what I built but could not yet defend the
mechanism underneath it. The most valuable shift for me was learning to treat
that discomfort as a diagnostic signal rather than as a gap I should hide with
high-level language.

Across the four recorded day folders, I named four gaps in my own work and
researched three peer questions that forced me to explain adjacent mechanisms
clearly enough to teach them. Even where the outward artifact was a short
markdown deliverable, the actual work was learning how to connect a concrete
code path or evaluation claim to the underlying system mechanics.

## The Four Gaps I Named

### 1. Prefix-cache invalidation and inference-time mechanics

The first gap I closed was around prefix caching. Before this week, I knew the
product-level claim: cache hits reduce latency and cost. I did not fully
understand the mechanism. What landed is that server-side prefix caching is not
a fuzzy similarity match over prompts. It is KV-state reuse over a
byte-for-byte tokenized prefix, and the first divergent token invalidates the
downstream cached segment. That changed how I think about prompt construction:
per-call metadata at the top of a prompt is not harmless formatting, it is a
cache-killing design choice.

### 2. Centralized orchestration as an agent tool-use policy layer

My Day 2 gap was about `agent/core/channel_orchestrator.py`. I could describe
the happy path, but I could not yet defend why the policy belonged in a central
orchestrator rather than in individual channel handlers. That gap closed once I
could explain the orchestrator as the place that protects authoritative shared
state, monotonic transitions, duplicate suppression, and centralized channel
eligibility. The key insight was that distributed handlers act on partial local
views of state, while the orchestrator can make one globally consistent tool-use
decision.

### 3. Why pairwise preference training learns lexical shortcuts

My Day 3 gap came from the unresolved training failure already named in the
repo: the Path B critic could still over-value lexical compliance on
medium-confidence email tasks. The closure came from understanding that SimPO-
style pairwise training rewards separability, not absolute calibration. A small
judge can therefore learn cheap rejection cues earlier than it learns a rich
notion of commercially useful acceptance. Harder negatives matter because they
remove shortcut separability and force the model to learn inside the region
where surface compliance is already satisfied.

### 4. What offline statistics actually justify

My Day 4 gap was statistical rather than architectural. I could cite the
headline numbers in the repo — `+48.84pp`, paired bootstrap, `95% CI`,
`p = 0.0`, and perfect inter-rater pilot agreement — but I could not yet defend
what those numbers meant mechanistically. I now understand why the bootstrap is
paired, what dependence structure it preserves, why a confidence interval on a
sealed evaluation slice is not a production guarantee, and why `1.00`
exact-match agreement on a deliberately mechanical rubric is stronger evidence
of rubric reproducibility than of broad human consensus.

## The Peer Questions I Researched

### 1. Structured outputs vs function calling

For a peer question about a “poor man’s function call” built from prompted JSON
plus parser repair, I wrote through the difference between plain JSON prompting,
JSON mode, tool calling, and strict structured outputs. The most useful lesson I
take from that work is the distinction between encouraging the model to emit the
right key and constraining the decoder so it cannot emit the wrong key. That is
now one of my clearest mental models for workflow-safe LLM integration.

### 2. SimPO asymmetry: stronger rejection than acceptance

For Nureye’s Day 3 question, I had to explain why a preference-trained judge
could become very good at spotting `fail` and `needs_human_review` cases while
remaining weaker on `pass` and channel-policy rows. Researching that forced me
to connect pairwise objectives, low-entropy negative cues, margin learning, and
hard-negative design into one coherent explanation. That work also fed back into
my own understanding of lexical shortcut formation.

### 3. Why aggregate metrics hide real failures

For Amare’s Day 4 question, I explained why global averages, pass rates, and
judge scores can be numerically correct while behaviorally misleading. The key
lesson is that aggregate metrics compress mixtures of qualitatively different
cases into one number, so they can hide subgroup collapse, routing failures, or
judge construct mismatch. That sharpened my own sense of when slice analysis is
mandatory.

## The Most Surprising Thing I Learned

The most surprising thing I learned this week is how often a system looks
“reasonable” precisely because the summary layer is hiding the mechanism. That
showed up in four different ways:

- a prompt cache looks like a latency optimization until you understand tokenized
  prefix invalidation
- an orchestrator looks like business logic until you understand the invariants
  it enforces against partial local state
- a preference-trained critic looks like it is learning judgment until you
  realize it may simply be learning the cheapest available separation cues
- a strong benchmark result looks decisive until you understand what the
  statistics preserve and what they collapse

The week made me much less willing to accept a top-line claim without asking
what exact mechanism is carrying it.

## What Changed In My Portfolio

The most concrete portfolio effect is that my explanatory surface is now closer
to the actual mechanisms in the code and evaluation stack.

- I updated `docs/system_architecture.md` so the orchestrator is described as a
  defensive policy layer, not just a routing sequence.
- I updated `reports/executive_memo.md` so the paired bootstrap claim is named
  more honestly and more precisely.
- I now have clearer language for the unresolved lexical-shortcut failure in the
  critic and a more defensible next-step plan for harder preference pairs.
- I also have a stronger framework for interpreting benchmark metrics: what is a
  coarse summary, what is a slice, what is a proxy, and what is a capability
  claim.

## Canon I Would Contribute To The Cohort

The reading and tooling canon I would contribute has three themes.

First, on **mechanism over abstraction**, I would contribute sources that force
you to ask what is really happening inside caching, function calling, and agent
orchestration, not just what the API claims at the product layer.

Second, on **post-training and evaluator design**, I would contribute SimPO,
LLM-as-a-Judge, and preference-leakage reading because they sharpen the question
of what a small judge actually learns and why evaluation pipelines can become
aligned to the wrong proxies.

Third, on **evaluation honesty**, I would contribute a small set of practical
statistical habits: preserve dependence structure when comparing systems, do not
confuse reproducibility with validity, and never let a global metric stand in
for condition-level behavior when production risk lives in slices.

## Closing Reflection

Week 12 paid back into the portfolio in exactly the way the curriculum intended.
I did not build a new system. I made the systems I had already built more
defensible. The most important output is not the markdown itself. It is that I
am now less likely to hide behind phrases like “deterministic-first,”
“preference-tuned judge,” “function calling,” or “strong held-out lift” without
being able to say what mechanism makes each of those phrases true, where that
mechanism breaks, and how I know.
