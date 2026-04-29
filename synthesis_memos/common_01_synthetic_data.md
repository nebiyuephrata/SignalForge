# Synthesis Memo: Best Practices and Lessons Learned on Synthetic Data for Language Models

## What I took from the paper

The paper’s practical value for this project is not “synthetic data is good.” It is that synthetic data only helps when generation, filtering, and provenance are treated as separate engineering problems. The paper’s design choice I found most useful is its separation between data creation and data curation in the discussion of synthetic-pipeline best practices. For Tenacious-Bench, that maps cleanly onto the four authoring modes: trace-derived tasks for fidelity, programmatic sweeps for controllable variation, multi-LLM synthesis for hard-case expansion, and hand-authored adversarial tasks for originality.

The strongest lesson for this repo is that synthetic volume is not the point. If the synthetic task does not preserve the business failure we care about, it becomes cheap noise.

Source: https://www.aimodels.fyi/papers/arxiv/best-practices-lessons-learned-synthetic-data

## Where I disagree

I disagree with the paper’s practical bias toward scaling synthetic expansion as soon as a generation-and-filtering loop is “good enough.” For this project, that would have been the wrong early optimization. My own Week 10 evidence says the dominant risk is not lack of examples; it is loss of Tenacious-specific nuance. A weak synthetic task that says “do not overclaim” is far less useful than one trace-derived task that captures the exact way a new CTO hears peer benchmarking as condescension.

That disagreement is not abstract. Trace `47ab214adf0bc2f1ee3a762ebd3afb78` is perfectly fluent, but it still drifts toward generic startup-style outbound. Probe `P-036` shows the harder failure: the message can remain factual while still being strategically wrong for a newly hired CTO. If I had followed a quantity-first synthetic strategy too early, I would have produced many more evaluator-friendly tasks and still missed the real business failure.

That means I would overweight `trace-derived` and `hand-authored adversarial` examples earlier than the paper’s average recipe seems to suggest, even if that makes the dataset smaller and slower to build. The paper argues for disciplined synthesis, and I agree with that. My stronger claim is that domain-specific benchmarks with reputational stakes should accept lower quantity in exchange for sharper task identity until the benchmark has proven it can preserve the domain’s non-obvious failure modes.

## How it changes my design

For Tenacious-Bench, the paper pushes me toward three rules:

1. every synthetic task must name its source mode,
2. every generated task must be machine-verifiable,
3. every held-out task must survive contamination checks before it counts as benchmark data.

That is why the current benchmark scaffold records `source_mode`, `probe_refs`, `week10_evidence_refs`, and a contamination report. It is also why I kept the audit anchored to concrete Week 10 traces and probes rather than letting the synthetic route define the benchmark by itself. In this repo, synthetic generation is supporting infrastructure, not the source of truth.
