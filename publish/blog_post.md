# What Generic Benchmarks Miss About Tenacious-Style Outbound, and How I Built Tenacious-Bench

Generic assistant and retail agent benchmarks are good at finding broken tool calls and obviously false statements. They are much worse at grading the failures that actually matter for Tenacious-style B2B outbound: over-claiming from weak public signals, drifting into generic outsourcing language, mishandling pricing handoffs, or sounding technically plausible but politically tone-deaf to a newly hired CTO.

That gap showed up clearly in SignalForge. The Week 10 system already had a deterministic-first signal pipeline, typed briefs, confidence-conditioned generation, lifecycle state, CRM sync, and booking flow. The problem was not “can the model write an email?” It was “can the system tell when an email is just fluent versus truly grounded and safe for this sales motion?”

So for Week 11 I built Tenacious-Bench v0.1 around those failure modes instead of around generic assistant quality. The benchmark now contains `225` tasks split into `110` train, `70` dev, and `45` held-out tasks, with four authoring modes:

- `9` trace-derived tasks grounded in Week 10 execution
- `180` programmatic tasks expanded from the probe library
- `24` hand-authored adversarial tasks
- `12` multi-LLM-synthesized tasks filtered through a separate judge

The multi-LLM slice matters because it is where the benchmark starts to feel less like template expansion and more like a real attack surface. I used a Gemini-class generator for hard task seeds and a Qwen-class judge for filter scoring, then normalized those tasks into the same machine-verifiable schema as the trace and programmatic examples. I also changed the partitioning logic so the held-out slice is composed of trace-derived, hand-authored, and synthesized families rather than the repetitive programmatic train/dev families. That mattered because the first naive expanded build had contamination problems; the final current report is back to `0` held-out violations under the configured n-gram and cosine checks.

The second major deliverable was the Path B critic. Rather than pretending I had a full GPU-backed SimPO stack wired into this repo already, I trained a local linear preference critic against the benchmark’s chosen/rejected pairs. The training set contains `110` preference pairs derived from the train split. The critic is narrow on purpose: it is not trying to judge all assistant behavior, only whether a candidate output is more Tenacious-calibrated than a plausible but degraded alternative.

The result is meaningful. On the sealed held-out preference pairs, the trained critic reached `0.7333` accuracy versus `0.4000` for the static heuristic baseline, for a `+33.33` percentage-point lift. The paired bootstrap confidence interval is `[15.56, 51.11]`, and the measured paired bootstrap p-value is `0.0` in the current local run. That is exactly the kind of result I wanted from a Week 11 component: not a giant general-model claim, but a specific improvement on a benchmark built from the business’s own failure modes.

The benchmark still has limits. The current inter-rater artifact is a blind pilot rather than the ideal 24-hour delayed rerun. The embedding-style contamination check is still a cosine proxy rather than a proper embedding model. And the current critic is a local linear scorer, not yet the intended small-model SimPO or ORPO run. But those are now hardening tasks, not missing-foundation tasks.

The practical takeaway is simple: Tenacious did not need another generic benchmark score. It needed a benchmark that knew why “technically correct” can still be commercially wrong. Tenacious-Bench v0.1 is my first pass at that, and it already changes which model component looks worth training.
