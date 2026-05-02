# GitHub Issue / Community Post Ready Draft

## Suggested Title

Tenacious-Bench v0.1: feedback request on a sales-domain benchmark for grounded outbound failures generic agent benchmarks miss

## Suggested Body

I’m sharing a benchmark and training scaffold built around one narrow question: what do generic agent benchmarks miss when the task is not retail or general chat, but grounded B2B outbound work?

The failure modes that mattered most in this project were:

- over-claiming from weak public signals
- drifting into generic outsourcing language
- unsafe pricing handoffs
- qualification or channel decisions that do not match the thread state
- technically plausible but politically wrong messaging to a newly hired CTO

To address that, I built **Tenacious-Bench v0.1** with:

- `225` tasks total
- `98 / 78 / 49` train/dev/held-out
- four authoring modes: `trace-derived`, `programmatic`, `multi-LLM-synthesis`, `hand-authored`
- machine-verifiable scoring rules instead of free-form “sounds on-brand” judging
- a public Path B preference dataset: `https://huggingface.co/datasets/ephorata/tenacious-bench-path-b-preference`
- a local Path B critic baseline with held-out lift of `+48.84pp`

Methodology choices I would especially value feedback on:

1. `tau2-bench` retail is a useful public contrast, but it does not measure Tenacious-specific dimensions like `weak_confidence_handling`, `outsourcing_mismatch`, `pricing_handoff`, or `cto_sensitivity`.
2. The synthesis route uses explicit model-family rotation: Gemini-family generation, Qwen-family bulk judging, and a separate eval-tier calibration role.
3. The held-out contamination report now checks `held_out` against both `train` and `dev`, with a boilerplate-aware 8-gram filter plus a cheap local embedding surrogate. Current report status is `0` violations under that policy.

If you work on GTM agents, outbound personalization, or domain-specific evaluation, I’d love feedback on:

- whether this contamination policy feels strict enough for a small synthetic benchmark
- whether the four-mode source mix is reasonable for a first public release
- whether you have seen similarly costly “socially unsafe but technically fluent” failure modes

Repo artifacts:

- benchmark summary: `tenacious_bench_v0.1/summary.json`
- methodology: `methodology.md`
- rationale: `methodology_rationale.md`
- datasheet: `datasheet.md`
- ablation harness: `ablations/run_path_b_ablations.py`
- held-out comparison summary: `ablations/ablation_results.json`

If this seems useful, I’d be happy to open up the packaging further or compare notes with similar benchmark efforts.
