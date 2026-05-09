# Sources — Day 4

## Canonical sources

1. `A Survey on LLM-as-a-Judge`
   - Why it was used: primary source for evaluator validity, proxy measurement,
     and the risk that judges reward the wrong latent target.
   - Link: <https://arxiv.org/abs/2411.15594>

2. Simpson's paradox / subgroup-analysis literature
   - Why it was used: statistical foundation for why aggregate trends can mask
     subgroup failures and why slice analysis is often mandatory.
   - Representative reference: <https://plato.stanford.edu/entries/paradox-simpson/>

## Tool / pattern used

- Repo grounding pattern:
  - `reports/executive_memo.md`
  - `reports/week11_status_report.md`
  - `inter_rater_agreement.md`
  - `ablations/ablation_results.json`
- Practical pattern:
  - pair every global metric with mechanism-aware slices by failure mode,
    condition family, or subgroup before trusting the top-line summary

