# Synthesis Memo: SimPO

## What I took from the paper

SimPO is the first path-specific paper that felt immediately actionable for this repo. Its value is practical: it removes the reference model and replaces it with a simpler implicit reward based on average log probability and a target reward margin. That is attractive here because the benchmark is still small and the week’s compute envelope is intentionally constrained.

Source: https://huggingface.co/papers/2405.14734

## Where I disagree

My disagreement is not with the algorithm, but with the transfer assumption that preference gains on broad instruction-following benchmarks map cleanly into a narrow business critic. Tenacious-Bench is not AlpacaEval. A critic that gets better at generic preference ranking but worse at recognizing soft over-claiming would be a regression for this project.

So I would not interpret a successful SimPO training run as proof of usefulness unless it improves held-out Tenacious-specific dimensions such as weak-confidence handling and CTO sensitivity.

## How it changes my design

Even with that caveat, SimPO is still my first-choice training objective because it fits the constraints:

- lower memory footprint than reference-model methods,
- good fit for small LoRA-scale runs,
- more room inside the Week 11 cost budget.

That is why I wrote the starter config around a SimPO run rather than a DPO one. If the first training pass is flat, that will be a meaningful result: it would suggest the data or the problem framing is weaker than the optimizer choice, which is useful to learn early.
