# Tenacious-Bench v0.1: What Generic Benchmarks Miss About Grounded B2B Outbound

Generic assistant and retail-agent benchmarks are useful for tool correctness, basic instruction following, and obvious hallucinations. They are much weaker at grading the failures that actually matter for Tenacious-style B2B outbound: over-claiming from weak public signals, drifting into generic outsourcing language, mishandling pricing handoffs, escalating through the wrong channel at the wrong lifecycle state, or sounding technically plausible but politically tone-deaf to a newly hired CTO.

That was the core lesson from SignalForge Week 10. The system already had a deterministic-first signal pipeline, typed briefs, confidence-conditioned generation, lifecycle state, CRM sync, and booking flow. The bigger problem was not “can the model write a fluent email?” It was “can the system tell when a fluent email is not actually grounded or safe for this sales motion?”

So for Week 11 I built **Tenacious-Bench v0.1** around those business-specific failures rather than generic assistant quality. The current benchmark contains `225` tasks split into `62` train, `113` dev, and `50` held-out tasks, with four authoring modes:

- `trace-derived`
- `programmatic`
- `multi-LLM-synthesis`
- `hand-authored`

The design choice that mattered most was keeping the benchmark machine-verifiable. Instead of a vague “does this sound good?” judge, the tasks encode explicit requirements such as subject-prefix constraints, banned-phrase checks, question-mark requirements, pricing handoff rules, qualification-field matches, and allowed-channel logic. That makes the benchmark narrower than a generic assistant benchmark, but much more aligned to the actual failure surface.

I also built a Path B preference-training scaffold around the benchmark. The public preference export now contains `62` train pairs and `113` dev pairs, while the `50` held-out preference rows remain sealed for evaluation. Each pair keeps the benchmark-approved answer as `chosen` and a controlled degraded variant as `rejected`, which makes the dataset usable for ORPO, DPO, or SimPO-style runs.

The current trained artifact in the repo is still a lightweight local critic rather than the full GPU-backed small-model adapter I originally wanted. Even so, the ablation result is meaningful: the held-out comparison shows a `+48.84pp` lift over the static heuristic baseline, with a `95%` confidence interval of `[34.88, 62.79]` and a paired bootstrap `p-value` of `0.0`. That is exactly the kind of Week 11 result I wanted: not a broad “my model is better at everything” claim, but a visible improvement on the benchmark built from the business’s own failure modes.

The benchmark still has real limits. The current inter-rater artifact is a blind pilot, not yet the ideal 24-hour-delayed rerun. The contamination check uses a cheap local embedding surrogate plus a boilerplate-aware n-gram policy rather than a dedicated embedding API. And the current public Hugging Face dataset is the preference bundle, not the full benchmark release. But those are now hardening and publication decisions, not missing-foundation problems.

The practical takeaway is simple: Tenacious did not need another generic benchmark score. It needed a benchmark that knew why “technically correct” can still be commercially wrong. Tenacious-Bench v0.1 is my first pass at that, and it already changed which component looked worth training.
