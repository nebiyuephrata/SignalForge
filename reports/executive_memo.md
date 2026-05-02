# Executive Memo: Tenacious-Bench v0.1 and Path B Critic

## Page 1

### Executive Summary

The current Path B critic improves held-out Tenacious-Bench accuracy by **+48.84 percentage points** versus the pre-trained heuristic gate, moving from **0.5116** to **1.0000** on the executed sealed held-out preference set, with a **95% confidence interval of [34.88, 62.79]** from a **paired bootstrap test** and **p = 0.0**. The deployment case is favorable on cost and latency: the measured local per-task cost delta is **$0.00** in this repo environment and the measured latency increase is only **+3.7036 ms per task**. My recommendation is **deploy with caveat**: use the critic as a production gate on the highest-risk outbound slices, but keep rollback monitoring because the current trained artifact is still a lightweight linear critic and the public-signal benchmark remains a lossy approximation of real Tenacious selling.

### Headline Delta A

**Delta A definition:** trained Path B critic versus the Week 10 static heuristic baseline on the executed sealed held-out preference pairs in [`ablations/ablation_results.json`](../ablations/ablation_results.json).

- Baseline accuracy: `0.5116`
- Trained accuracy: `1.0000`
- Lift: `+48.84pp`
- `95% CI`: `[34.88, 62.79]`
- Statistical test: `paired bootstrap`
- `p-value`: `0.0`

Plain-English interpretation: on the current held-out evaluation slice, the trained critic is materially better at separating preferred from rejected behavior than the pre-trained heuristic gate.

### Delta B Honesty

**Delta B definition:** trained critic versus the current prompt-engineered baseline using the same intervention shape, meaning a non-learned gate over the same held-out preference pairs rather than a new model family.

- Prompt-engineered baseline accuracy: `0.5116`
- Trained accuracy: `1.0000`
- Lift: `+48.84pp`

The honest caveat is that this is **not** yet a strong “training versus best possible prompting” claim. The current comparator is the repo’s prompt-engineered static heuristic gate, not a stronger same-backbone learned-free prompt baseline on a small open model. So the result supports “training beat the current prompt-only gate we actually run,” but it does **not** close the door on a stronger prompt-only baseline outperforming or matching this critic later.

### Cost, Latency, and Production Implication

The currently executed artifact is cheap to run in this environment:

- Baseline cost per task: `$0.00`
- Trained critic cost per task: `$0.00`
- Cost delta per task: `$0.00`
- Baseline latency per task: `0.032 ms`
- Trained latency per task: `3.7356 ms`
- Latency delta per task: `+3.7036 ms`

For a deployment decision, the meaningful tradeoff is therefore **not** direct inference cost in the current local setup. It is whether a roughly four-millisecond gate is worth adding in exchange for a large measured reduction in unsafe approvals on the benchmark. Given the current lift size, that trade looks favorable as long as the gate does not suppress real send volume in production.

### Production Recommendation

**Recommendation: deploy with caveat.**

Why this is the right category:

- the measured held-out lift is large: `+48.84pp`
- the confidence interval stays meaningfully above zero: `[34.88, 62.79]`
- the measured cost delta is effectively `$0.00` in the current environment
- the latency increase is small: `+3.7036 ms`

The caveats are specific:

1. Deploy first on the highest-risk slices: `weak_confidence_handling`, `signal_over_claiming`, `pricing_handoff`, and `cto_sensitivity`.
2. Keep the pre-trained heuristic path available as an immediate fallback.
3. Do not treat the current linear critic as the final model artifact; it is the deployable safety gate **until** the stronger ORPO or SimPO pass is proven.

### Kill Switch

Roll back the trained critic and revert to the pre-trained heuristic gate if **either** of these conditions is true over any rolling **7-day** production window:

1. outbound send volume drops by **more than 10%** versus the pre-critic baseline for comparable lead mix, because that would mean the gate is likely suppressing too many acceptable messages relative to the observed benchmark lift, or
2. complaint-like negative replies or manual human overrides rise above **2% of critic-blocked or critic-approved decisions**, because that would mean the critic is no longer paying for itself operationally.

The action is simple: disable the trained critic, restore the heuristic gate, and route the flagged slice to human review while recalibrating.

## Page 2

### v0.2 Coverage Gaps

The current benchmark is strong on grounded email behavior, qualification, and channel choice, but there are still **zero-task** gaps that v0.2 should add explicitly.

1. **Cross-channel opt-out and suppression handling**
   Current gap: there are no tasks that grade whether an SMS `STOP`, email unsubscribe, or manual suppression flag correctly blocks future outreach across all channels.
   v0.2 addition: add a new `suppression_decision` task type with input fields for channel-specific stop events and CRM suppression state.

2. **Warm-intro and referral-chain behavior**
   Current gap: there are no tasks that grade how the agent should behave when the real reason to contact is a private referral, founder connection, or advisor introduction rather than a public signal.
   v0.2 addition: add a new private-context input category plus a small shadow partition for `warm_intro_grounding`.

3. **CRM ownership and duplicate-contact resolution**
   Current gap: there are no tasks that grade whether the system should defer because another rep owns the account, the contact is already active in CRM, or two records should be merged before outbound continues.
   v0.2 addition: add a `crm_state_resolution` task type with HubSpot ownership, stage, and duplicate-record fields.

4. **Post-booking human handoff brief quality**
   Current gap: there are no tasks that grade the quality of the brief handed to the human seller after booking is triggered.
   v0.2 addition: add a `handoff_brief_generation` task type with scoring on evidence completeness, next-step clarity, and risk flags for the human call owner.

### Ground Truth Faithfulness Self-Critique

The benchmark is intentionally built from public or repo-available signals such as hiring data, layoffs data, and redacted case-study context. That makes it measurable, but it also makes the headline numbers **lossy** relative to a real Tenacious motion.

The most important lossiness mechanism is that **public hiring and funding signals lag real buying intent**. In practice, that means the benchmark can over-reward cautious emails that are perfectly grounded in stale public evidence while under-rewarding stronger outreach that would be justified by private context a real rep already has, such as an active referral chain, named-account history, or a live human conversation. So the current `+48.84pp` lift should be read as “better under public-signal-grounded scoring,” not as proof that the critic is equally better in every live sales context.

### One Unresolved Training Failure

There is one unresolved training failure I would call out plainly: **the current linear critic still over-values lexical compliance on medium-confidence email tasks**.

Concretely, when a draft is short, question-led, avoids banned phrases, and mentions the required strings, the critic can score it as preferred even when the business ask is still too generic to be truly useful. I tried to reduce that by generating controlled rejected variants and by evaluating on dev and held-out splits, but the current training setup still gives the model too much incentive to latch onto surface-form cues. The next fix is to add harder negative pairs that remain lexically compliant while changing only commercial usefulness, then rerun the stronger ORPO or SimPO path.

### Closing Judgment

This is strong enough to ship as a guarded production component, not strong enough to call “finished.” The benchmark and ablation evidence justify deploying a critic gate with monitoring, but the unresolved lexical-shortcut failure and the public-signal measurement lossiness are the reasons the recommendation remains **deploy with caveat** rather than unconditional deploy.
