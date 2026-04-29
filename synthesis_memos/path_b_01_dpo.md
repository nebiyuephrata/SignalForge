# Synthesis Memo: Direct Preference Optimization

## What I took from the paper

The most important contribution of DPO is conceptual simplicity. It shows that we can optimize a policy directly from preference pairs without the full RLHF stack of reward model plus reinforcement learning loop. For a small project, that is liberating: it lowers the barrier to running preference-based experiments at all.

Source: https://huggingface.co/papers/2305.18290

## Where I disagree

I do not disagree with DPO’s core formulation, but I do disagree with treating it as the automatic default for this repo. The reference-model requirement is not fatal, but it is a real cost when the dataset is small, the budget is tight, and the goal is a narrow critic rather than a broad conversational assistant. In this setting, “simpler than RLHF” is still not necessarily simple enough.

## How it changes my design

DPO still matters here because it provides the mental model for the preference data we are preparing:

- prompt
- chosen output
- rejected output

That structure directly shaped `training_data/path_b_preferences.jsonl`. Even if the first training run ends up using SimPO, DPO is the paper that makes the pairwise training setup feel rigorous rather than improvised.
