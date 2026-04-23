# Target Failure Mode

## Name

`Signal Over-Claiming Under Medium Confidence`

## Why It Matters In The Tenacious Context

Tenacious is not selling a commodity email sequence. It is trying to win trust with technical buyers by showing that it understands when hiring pressure is real, when AI maturity is lagging, and when outside help might be timely. In that context, the most damaging failure is not silence - it is sounding precise when the evidence only supports a directional read.

CTOs and VP Engineering leaders can spot exaggerated hiring claims immediately:

- "You are hiring aggressively"
- "Recent funding means your team is scaling now"
- "You clearly need outside capacity"

If those claims are even slightly off, the system loses the one thing it is supposed to create: credibility.

## Why This Is The Highest-ROI Failure

This failure sits at the intersection of:

- high business frequency
- high revenue loss
- direct relevance to the current architecture
- tractable mechanism fixes

It is more important than generic tone drift because tone can be forgiven. False specificity usually cannot.

It is more important than pure cost pathology because wasted tokens are recoverable; broken trust in a high-ACV outbound thread usually is not.

It is more important than future multi-turn issues because it already exists in the first-touch path and directly affects conversion.

## Expected Frequency

Using the signal over-claiming group (`P-004` to `P-007`):

- average trigger rate: `0.34`

This means roughly one in three relevant prospect generations can drift into over-assertion if controls are loose, especially around:

- stale funding
- tiny role growth
- layoffs without rebound evidence
- weak AI maturity signals

## Dollar Impact Calculation

Use the signal over-claiming category average:

- average business cost: `$54,240`
- average trigger rate: `0.34`

Expected downside at modest scale:

- `100` medium-confidence outbound threads x `$54,240` expected loss x `0.34` trigger exposure is not the right way to compound thread-level expected value because each probe already encodes trigger-adjusted loss
- more practically: at `100` affected threads, aggregate expected downside is roughly `100 x $54,240 = $5.424M` in expected pipeline damage across comparable opportunities

For a single-thread mental model:

- a false hiring assertion can easily create a `30%-60%` disengagement probability
- applied against a `$240K-$480K` realistic Tenacious opportunity, expected loss lands quickly in the `$50K-$70K` band

That is why this failure dominates ROI: it is frequent enough to matter and expensive enough to hurt.

## Why Fixing It Improves Conversion

Fixing this failure does three things at once:

1. It increases reply trust

   Buyers are more likely to engage when the system says:
   - "It looks like..."
   - "Is that directionally right?"
   instead of pretending certainty.

2. It improves differentiation

   SignalForge's pitch is not "we also send emails." It is "we know when to assert and when to ask." Over-claiming destroys that edge.

3. It reduces downstream contamination

   Once the first email is wrong, later qualification, booking, and CRM scoring become noisy. Fixing the first-touch truth boundary improves the whole funnel.

## Mechanism Design Implications

This failure mode points directly to the next mechanism work:

1. Stronger confidence-to-tone mapping

   Medium confidence should default to careful language unless at least two independent strong signals agree.

2. Structured claim budgeting

   Cap the number of asserted claims in medium-confidence emails.

3. Explicit stale-signal suppression

   Funding older than the target window should not be framed as current urgency.

4. Mixed-signal contradiction handling

   Hiring growth plus layoffs should force balanced language, never "aggressive hiring."

5. Claim validator hardening

   The guardrail should detect exaggerated paraphrases, not just unsupported numbers or claim ids.

## Bottom Line

If SignalForge fixes only one thing next, it should fix `signal over-claiming under medium confidence`.

That is the single best ROI move because it:

- protects trust with technical buyers
- reduces high-ACV thread loss
- improves conversion quality
- strengthens the system's core differentiator
- fits the current architecture cleanly
