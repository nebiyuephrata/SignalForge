# Sources — Day 3

## Canonical sources

1. SimPO: `Simple Preference Optimization with a Reference-Free Reward`
   - Why it was used: primary source for the pairwise preference objective and
     the margin-based training mechanics that shape what the judge learns.
   - Link: <https://arxiv.org/abs/2405.14734>

2. `A Survey on LLM-as-a-Judge`
   - Why it was used: primary source for evaluator behavior, judge reliability,
     and the distinction between relative discrimination and broader evaluation
     validity.
   - Link: <https://arxiv.org/abs/2411.15594>

## Tool / pattern used

- Repo grounding pattern:
  - `reports/executive_memo.md`
  - `methodology_rationale.md`
  - `training_data/path_b_preferences.jsonl`
- Practical pattern:
  - use hard-negative preference pairs that remain lexically compliant while
    differing in commercial usefulness to reduce shortcut separability

