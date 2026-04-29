# Synthesis Memo: Recent Advances in Large Language Model Benchmarks against Data Contamination

## What I took from the paper

The paper’s main contribution is to reframe contamination as a benchmark-design problem rather than a post-hoc embarrassment. Static test sets get absorbed into model training distributions; dynamic and time-sensitive benchmark strategies are a response to that reality. For Tenacious-Bench, the practical lesson is that “held-out” is not enough. We need explicit overlap checks, provenance discipline, and time-sensitive rules for public-signal tasks.

Source: https://arxiv.gg/abs/2502.17521

## Where I disagree

I disagree with the idea that the static-to-dynamic shift is itself the key move for a benchmark like this one. Tenacious-Bench is not failing because its domain changes every day like news QA. It is failing because the easiest way to author tasks is to accidentally restate the same sales failure five times. In other words, local structural contamination is a bigger immediate threat than internet-scale contamination.

That is why the first useful contamination check in this repo is not a heroic dynamic benchmark pipeline. It is a boring but necessary combination of:

- split discipline,
- longest shared n-gram checks,
- lexical similarity checks,
- manual time-shift review.

## How it changes my design

The paper pushed me to treat contamination prevention as part of the authoring pipeline, not an evaluation afterthought. In practice that means:

- `generation_scripts/contamination_check.py` runs from the repo root,
- `contamination_check.json` is versioned as an artifact,
- held-out tasks are compared against both train and dev,
- and time-shift verification stays visible even when it is still manual.

For this benchmark, that is the right early compromise: transparent contamination controls now, and more dynamic public-signal freshness checks in `v0.2`.
