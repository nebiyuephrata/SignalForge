# Synthesis Memo: Prometheus 2

## What I took from the paper

Prometheus 2 is the clearest argument in the reading set for an open evaluator model being a serious product component rather than just a research curiosity. The important part for this repo is not the leaderboard result by itself. It is the combination of:

- direct assessment support,
- pairwise ranking support,
- custom evaluation criteria,
- strong agreement with humans and proprietary judges.

Source: https://huggingface.co/papers/2405.01535

## Where I disagree

I disagree with applying a general evaluator LM directly as the production judge for SignalForge without first narrowing the criterion surface. Tenacious does not need a broadly capable evaluator as much as it needs a stubbornly specific one. A judge that is excellent at broad helpfulness scoring can still miss the difference between a grounded benchmark note and a socially risky one.

## How it changes my design

Prometheus 2 still changes the design in two useful ways:

1. it validates the idea that open judges can be credible enough to matter,
2. it encourages using both direct scoring and pairwise comparison in the evaluation workflow.

That second point is especially helpful. For Tenacious-Bench, I want pairwise preference data for training, but I also want direct rubric scoring for evaluation. Prometheus 2 makes that mixed evaluation pattern feel like a deliberate architecture, not a patchwork.
