# Draft Community Engagement Post

## Title

Tenacious-Bench v0.1: a sales-domain benchmark for grounded outbound failures generic agent benchmarks miss

## Body

I’ve been working on a benchmark derived from a Tenacious-style outbound workflow, and I wanted to share one concrete gap I found in generic retail/assistant benchmarks.

The core issue is that a lot of existing benchmarks do not grade the commercially expensive failure modes in B2B outbound:

- over-claiming from weak public signals
- drifting into generic outsourcing language
- mishandling pricing handoffs
- sounding technically plausible but politically tone-deaf to a newly hired CTO

To address that, I built **Tenacious-Bench v0.1** as a machine-verifiable benchmark with:

- `225` tasks total
- `110 / 70 / 45` train/dev/held-out
- `trace-derived`, `programmatic`, `hand-authored`, and `multi-LLM-synthesis` source modes
- contamination checks on the sealed held-out split
- a narrow Path B critic run that improves held-out preference ranking by `+33.33pp` over a static heuristic baseline

What felt most important methodologically:

1. the held-out slice is not just a random sample of templates; it is weighted toward trace-derived, hand-authored, and synthesized tasks
2. the benchmark is machine-verifiable rather than “sounds on-brand” hand-waving
3. the judge component is evaluated against the benchmark’s own failure taxonomy rather than generic assistant preferences

I’d especially love feedback on:

- whether the contamination protocol is strong enough for a small-data synthetic benchmark
- whether the source-mode balance feels right for a first public release
- whether others have seen similar “socially unsafe but technically fluent” failure modes in outbound or GTM agents

Local repo artifacts:

- benchmark summary: `tenacious_bench_v0.1/summary.json`
- datasheet: `datasheet.md`
- methodology: `methodology.md`
- critic ablations: `ablations/ablation_results.json`

If this is useful, I’d be glad to adapt the benchmark packaging for a cleaner public release.
