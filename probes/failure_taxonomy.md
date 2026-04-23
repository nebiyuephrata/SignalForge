# Failure Taxonomy

## ICP misclassification

- `number_of_probes`: `4`
- `average_trigger_rate`: `0.28`
- `average_business_cost`: `$33,840`
- `key_insight`: Tenacious loses leverage when technically real signals are mapped to the wrong buyer, wrong org owner, or wrong service line. The problem is not weak enrichment alone; it is incorrect interpretation of what kind of hiring pain exists.

Covered probes: `P-001`, `P-002`, `P-003`, `P-034`

## Signal over-claiming

- `number_of_probes`: `4`
- `average_trigger_rate`: `0.34`
- `average_business_cost`: `$54,240`
- `key_insight`: The most common expensive mistake is converting partial evidence into strong narrative claims. In Tenacious outbound, this creates immediate credibility loss with CTO and VP Engineering buyers who can inspect the premise in seconds.

Covered probes: `P-004`, `P-005`, `P-006`, `P-007`

## Weak-signal handling

- `number_of_probes`: `3`
- `average_trigger_rate`: `0.26`
- `average_business_cost`: `$30,560`
- `key_insight`: Weak inputs should collapse into a clean exploratory question. If the system keeps "helpfully" filling gaps, it destroys the trust advantage that a signal-grounded system is supposed to create.

Covered probes: `P-008`, `P-009`, `P-010`

## Confidence miscalibration

- `number_of_probes`: `4`
- `average_trigger_rate`: `0.23`
- `average_business_cost`: `$41,160`
- `key_insight`: Confidence is the control surface for tone. When it is wrong, everything downstream is wrong: too aggressive for weak evidence, too timid for strong evidence, or distorted by competitor-gap signals that should not dominate prospect evidence.

Covered probes: `P-011`, `P-012`, `P-013`, `P-014`

## Competitor-gap hallucination

- `number_of_probes`: `4`
- `average_trigger_rate`: `0.27`
- `average_business_cost`: `$50,800`
- `key_insight`: Benchmarking is SignalForge's sharpest hook and its sharpest knife. Wrong peer sets, invented practices, or judgmental framing turn differentiation into reputational damage quickly.

Covered probes: `P-015`, `P-016`, `P-017`, `P-018`

## Tone drift

- `number_of_probes`: `3`
- `average_trigger_rate`: `0.29`
- `average_business_cost`: `$37,440`
- `key_insight`: Tone errors do not always look catastrophic in logs, but they quietly kill reply rates. Tenacious needs "informed and calm," not SDR enthusiasm and not hand-wavy vagueness.

Covered probes: `P-019`, `P-020`, `P-021`

## Bench over-commitment

- `number_of_probes`: `2`
- `average_trigger_rate`: `0.16`
- `average_business_cost`: `$78,000`
- `key_insight`: Even though bench logic is not fully implemented yet, this is a dangerous future category. Promise inflation around staffing capacity can create high-dollar pipeline damage and delivery trust risk fast.

Covered probes: `P-022`, `P-023`

## Multi-turn inconsistency

- `number_of_probes`: `3`
- `average_trigger_rate`: `0.22`
- `average_business_cost`: `$34,400`
- `key_insight`: Follow-up turns will eventually matter as much as first-touch quality. If the system cannot hold a consistent uncertainty boundary after replies, the first email's discipline will not save the thread.

Covered probes: `P-024`, `P-025`, `P-026`

## Cost pathology

- `number_of_probes`: `3`
- `average_trigger_rate`: `0.27`
- `average_business_cost`: `$14,000`
- `key_insight`: Cost failures have lower per-thread revenue damage than trust failures, but they matter operationally. If low-value threads consume full LLM paths or cache poorly, evaluation quality and scalable deployment both degrade.

Covered probes: `P-027`, `P-028`, `P-029`

## Adversarial contradiction inputs

- `number_of_probes`: `4`
- `average_trigger_rate`: `0.21`
- `average_business_cost`: `$54,100`
- `key_insight`: The system's strongest trust test is what it does when a prospect says "that is wrong." If it keeps asserting, the thread often dies immediately and the brand cost can exceed normal missed-opportunity cost.

Covered probes: `P-030`, `P-031`, `P-032`, `P-033`

## Cross-category insight

The highest-risk categories are not simply the highest-frequency ones. Three categories dominate expected downside:

1. `Bench over-commitment` for highest per-event dollar risk
2. `Signal over-claiming` for the most damaging blend of frequency and cost
3. `Competitor-gap hallucination` because it attacks SignalForge's central differentiator directly

Taken together, these suggest the next mechanism-design investments should prioritize:

1. stronger claim-boundary enforcement
2. peer-set validity checks
3. hard promise suppression for any delivery or staffing language
