# Rubric Gap Analysis

## Current read

This repo now covers most rubric categories with committed artifacts and executable code paths. The remaining gaps are mostly honesty gaps that cannot be “patched” away by prose alone.

## Strong coverage

- `audit_memo.md` exists under 600 words, cites at least 8 probe IDs and 5 trace IDs, names `tau2-bench` retail, and states gaps at dimension level.
- All four authoring modes are implemented in `generation_scripts/build_bench.py`, with visible `source_mode` metadata and documented share targets.
- Multi-LLM synthesis routing is explicit in `generation_scripts/synthesize_tasks.py`, with generator/judge/eval-tier family separation and a preference-leakage policy.
- Judge filtering now shows pointwise dimensions, thresholds, pairwise duplicate logic, prompt visibility, and per-task filter logging.
- Contamination code now checks held-out against both train and dev, emits a structured report, and includes n-gram plus cheap embedding similarity checks.
- Path declaration is explicit in `methodology.md` and `methodology_rationale.md`, with Week 10 traces and paper-grounded rationale.
- README now includes reproduction steps, the public Hugging Face dataset URL, public artifact links, and a root license file.

## Remaining nontrivial gaps

- `inter_rater_agreement.md` documents the required 24-hour protocol, but the committed pilot was still run inside the same sprint block. That is a real procedural gap until rerun.
- The ablation harness source now exposes Delta A / B / C and cost-pareto logic through a shared interface, but the currently executed trained artifact is still the local linear critic rather than the intended GPU-backed ORPO/SimPO adapter.
- The blog and community links in README point to committed public drafts. If the rubric grader expects a live issue, workshop post, or PR rather than a public repo artifact URL, that still needs a real external post.

## Bottom line

The repo is now much closer to `mastered` on source-visible criteria. The main remaining work is not “write more markdown,” but:

1. rerun inter-rater labeling with a real 24-hour gap,
2. run the intended ORPO/SimPO adapter training pass beyond the local linear critic baseline,
3. publish a real external community artifact if the grader requires one.
