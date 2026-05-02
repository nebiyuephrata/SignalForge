# I Built a Benchmark for the Failures Generic LLM Evaluations Miss

Generic LLM benchmarks are useful, but they are not the same thing as a workflow benchmark.

That gap became obvious in my Week 11 project. I was working on **SignalForge**, a deterministic-first outbound workflow for **Tenacious**. The system already had structured enrichment, confidence calibration, grounded email generation, CRM sync, lifecycle routing, and evaluation hooks. But Week 10 evidence showed that the hardest failures were not “can the model produce text?” failures. They were **judgment failures**:

- over-claiming from weak public signals,
- drifting into generic outsourcing language,
- escalating to booking too early,
- mishandling pricing handoffs,
- sounding technically plausible but socially wrong with a new CTO.

That is the kind of behavior that a broad assistant benchmark or a retail-agent benchmark can easily under-measure.

The short version of the result is this: the current Path B critic improved held-out accuracy by **+48.84 percentage points** over the pre-trained heuristic gate on the executed held-out preference set, with a **95% confidence interval of [34.88, 62.79]**. That is not a claim that the system is finished, but it is strong evidence that narrowing the problem to judgment and evaluation was the right move.

## What I built

I built **Tenacious-Bench v0.1**, a benchmark designed around those workflow-specific failure modes.

The current release has:

- `225` total tasks
- `62` train tasks
- `113` dev tasks
- `50` held-out tasks

It also uses four dataset authoring modes:

- `trace-derived`
- `programmatic`
- `multi-LLM-synthesis`
- `hand-authored`

That mix matters because I did not want a benchmark that was only synthetic slot-filling or only anecdotal trace replay. I wanted coverage from real traces, systematic parameter sweeps, adversarial hand-written cases, and harder generated cases that simple templating would miss.

## Why I chose Path B

The central project decision was choosing **Path B: preference-tuned judge or critic**.

I did not choose Path B because it sounded fashionable. I chose it because the Week 10 evidence suggested the generator was not the primary bottleneck. The system could already produce acceptable drafts some of the time. The problem was that it could not always tell when a fluent answer had crossed into unsafe overreach.

So instead of treating this as a “make the generator more eloquent” problem, I treated it as a **judgment consistency** problem.

That led to a narrower but more useful setup:

- benchmark the exact Tenacious-specific failures,
- generate preference pairs from benchmark-approved vs degraded outputs,
- train a lightweight critic,
- compare it against the Week 10 heuristic baseline on held-out data.

## How the dataset was authored

The benchmark is not one monolithic blob. It is a structured artifact with provenance.

Each task carries metadata such as:

- `source_mode`
- `dimension`
- `task_type`
- benchmark inputs
- candidate output
- explicit ground truth
- scoring rubric

The programmatic authoring route uses structured variables like company profile, signal confidence, lifecycle state, and routing state. The synthesis route uses a multi-LLM policy with separation between the generator family, the dev-tier bulk judge family, and the eval-tier calibration family. That anti-leakage policy matters because if the same family both generates and judges the data, evaluation gets much less trustworthy.

I also added a contamination check that compares held-out against both train and dev using:

- n-gram overlap
- lexical cosine
- cheap embedding cosine
- time-shift provenance flags

The current structured report shows `0` held-out contamination violations under the repo policy.

## How preference optimization fit the project

After building the benchmark, I created a Path B preference dataset.

The public preference export currently includes:

- `62` train pairs
- `113` dev pairs

The `50` held-out preference rows remain sealed for final evaluation.

Each pair uses:

- a benchmark-approved response as `chosen`
- a controlled degraded variant as `rejected`

That makes the dataset usable for ORPO, DPO, or SimPO-style training while keeping the benchmark tied to real failure dimensions instead of generic “better sounding” preferences.

## What improved

The strongest executed result in the repo is a lightweight local critic rather than the final GPU-backed adapter I originally planned.

Even so, the result is meaningful:

- held-out baseline accuracy: `0.5116`
- held-out trained accuracy: `1.0000`
- held-out lift: `+48.84` percentage points
- `95%` bootstrap CI: `[34.88, 62.79]`
- paired bootstrap `p-value`: `0.0`

That result matters because it is not a generic quality score. It is a measured improvement on the exact business-specific failure modes the benchmark was designed to catch.

## What is still incomplete

The project is strong technically, but I wanted to keep the public artifacts honest.

The biggest remaining limitation is procedural:

- the inter-rater study has been executed as a blind pilot, but the ideal second pass separated by a real `24`-hour gap is still pending

There are also a few practical hardening tasks left:

- continue increasing multi-LLM synthesis coverage
- complete the stronger ORPO or SimPO small-model pass
- complete the true 24-hour inter-rater rerun for the public-release version

## What I learned

The biggest lesson from this project is that the most important question was not “what model should I fine-tune?” It was “what exactly is failing, and how do I measure it honestly?”

Once I framed the problem that way, the system design got much clearer:

- use a domain-specific benchmark
- keep held-out sealed
- train a narrow critic before a bigger generator
- make contamination and provenance visible

That changed the project from a vague “LLM improvement” exercise into something much more concrete: a benchmark, a preference dataset, a judge path, and an ablation result that can actually be defended.

## Public artifacts

- Dataset: `https://huggingface.co/datasets/ephorata/tenacious-bench-path-b-preference`
- Repo: `https://github.com/nebiyuephrata/SignalForge`
- Community issue: `https://github.com/nebiyuephrata/SignalForge/issues/1`

If you are building evaluation for a narrow workflow, my main advice is simple: **do not assume a generic benchmark is grading the thing your business actually cares about**.
