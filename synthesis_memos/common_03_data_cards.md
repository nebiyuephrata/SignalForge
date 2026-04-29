# Synthesis Memo: Data Cards

## What I took from the paper

The most useful idea in *Data Cards* is the design choice to document a dataset in layers for different readers. In the paper’s telescopic / periscopic / microscopic framing, a dataset owner, an evaluator, and a downstream user need different entry points into the same artifact. That maps well onto this repo: the grader needs the headline structure, an engineer needs the exact partition and scoring logic, and a skeptical reviewer needs uncertainty and limits made explicit.

Source: https://facctconference.org/static/pdfs_2022/facct22-3533231.pdf

## Where I disagree

My main disagreement is about ordering. The paper is strongly human-centered, which I agree with in spirit, but for a benchmark like Tenacious-Bench the highest-risk failure is not that the documentation is hard to read. It is that the benchmark is hard to grade mechanically. If I have to choose early between a beautifully layered explanation and a rigidly typed rubric that a script can score, I choose the typed rubric first.

That disagreement comes directly from my own evidence. Week 10 showed failures like signal over-claiming, tone drift, and CTO sensitivity where a human reader might say “this sounds mostly fine,” while the actual business outcome would still be wrong. Trace `2bc8574e0954a3902393c025758f243c` and probe `P-036` both live in that category. If the benchmark cannot score those cases mechanically, then better prose alone does not make it safer or more useful.

That does not mean the human-centered layer is optional. It means the layers should be ordered: first make the task machine-verifiable, then make the surrounding documentation humane and legible.

## How it changes my design

The paper still changed the way I wrote the benchmark docs. I now treat the dataset docs in three layers:

- telescopic: why this benchmark exists,
- periscopic: which business-risk dimensions it targets,
- microscopic: what exact fields and scoring hooks each task contains.

That structure is now reflected in `datasheet.md`, but only after the evaluator, schema, and contamination report were explicit enough to support it. So my real disagreement is not with layered documentation itself. It is with the idea that documentation quality can be separated from scoring discipline in a benchmark like this. For Tenacious-Bench, the documentation only becomes trustworthy after the rubric is rigid enough to survive automation.
