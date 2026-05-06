# SignalForge Week 12 Knowledge Gaps

This repo is not missing features as much as it is missing defended mechanisms.

The strongest Week 12 questions here are the places where SignalForge clearly makes a technical choice, ships that choice in code, and reports outcomes from it, but does not yet fully explain the underlying mechanism well enough to defend it under pressure.

## Short Gap Read

The main gaps in this repo are:

1. `Confidence calibration is encoded, but not deeply justified.`
   The repo has concrete weights, penalties, and thresholds in `agent/core/confidence.py`, but the mechanism behind those values is still more heuristic than defended science.

2. `The critic result is strong, but the learning mechanism is only partially explained.`
   The repo reports a `+48.84pp` held-out lift, but the executed artifact is still a local linear critic with hand-built sparse features in `training/run_path_b_critic.py`. That makes the obvious gap not "did training help?" but "what exactly is the critic learning, and why does it still fail on lexical shortcuts?"

3. `Evaluation claims are stronger than the statistical explanation.`
   The repo uses paired bootstrap confidence intervals and p-values in `reports/executive_memo.md`, but the meaning of that test, why it is appropriate here, and what it does not prove are not yet explained at the level of a public technical explainer.

4. `Contamination checking is implemented, but the surrogate embedding story is fragile.`
   `generation_scripts/contamination_check.py` uses `cheap_local_hashing_embedding_v1`. That is a practical engineering choice, but it raises a real knowledge gap: what kinds of contamination can this detect, what kinds can it miss, and how should an FDE reason about false reassurance?

5. `Agent/channel policy is deterministic, but the state machine semantics are under-explained.`
   `agent/core/channel_orchestrator.py` clearly encodes lifecycle transitions and channel eligibility, but the repo does not yet fully unpack why those transitions are safe, where they can break, or how they relate to broader agent tool-use/state-management patterns.

6. `Generation/judge routing is explicit, but preference-leakage prevention is still mostly asserted.`
   The repo rotates model families in `generation_scripts/synthesize_tasks.py`, but a good explainer would need to clarify what leakage risk actually is, why same-family relatedness matters, and how much protection routing alone really buys.

## Best Questions To Use

These are the sharpest repo-grounded questions I would hand to a teammate.

### 1. Confidence Calibration

**Question**

How should I defend the weighting and threshold design in `agent/core/confidence.py`? More specifically: what mechanism justifies combining brief confidence, average signal confidence, competitor-gap confidence, and source success rate with fixed weights and hand-set penalties, and what failure modes appear when a calibrated policy like this is used to gate both wording and channel eligibility?

**Why this is a real gap here**

- The confidence layer is load-bearing in this repo.
- It changes prompt tone, booking-link eligibility, and SMS eligibility.
- The repo shows outcome deltas in `docs/evaluation/confidence_analysis.md`, but the mapping from evidence to score is still mostly heuristic.

**Grounding artifacts**

- `agent/core/confidence.py`
- `docs/evaluation/confidence_analysis.md`
- `agent/llm/email_generator.py`
- `agent/core/channel_orchestrator.py`

**What a strong explainer should cover**

- calibration vs classification in agent systems
- threshold selection and tradeoffs
- how policy layers propagate into downstream behavior
- when heuristic calibration is acceptable and when it needs empirical recalibration

### 2. What The Critic Is Actually Learning

**Question**

The repo reports a large held-out lift from the Path B critic, but the executed artifact is a sparse linear model. What exactly is this critic learning in `training/run_path_b_critic.py`, why can it separate chosen from rejected outputs so well on this benchmark, and why does it still over-value lexical compliance on medium-confidence email tasks?

**Why this is a real gap here**

- This is the headline technical claim of the repo.
- The model is not a generic neural mystery box; it is inspectable.
- The unresolved failure is already named in `reports/executive_memo.md`, which makes this a perfect diagnostic gap.

**Grounding artifacts**

- `training/run_path_b_critic.py`
- `training/artifacts/path_b_linear_critic.json`
- `reports/executive_memo.md`
- `training_data/path_b_preferences.jsonl`

**What a strong explainer should cover**

- pairwise preference learning with margin/logistic objectives
- hashed sparse features and explicit rubric features
- why linear critics can look strong on structured tasks
- lexical shortcut learning and harder-negative construction

### 3. What Paired Bootstrap Really Proves

**Question**

What does the paired bootstrap confidence interval in the repo actually measure, and what does it not justify? More specifically: why is paired bootstrap the right test for the held-out chosen/rejected comparison in SignalForge, what assumptions does it relax, and why does a high lift with `p = 0.0` still not prove robust real-world superiority?

**Why this is a real gap here**

- The repo uses the statistic in decision memos and deployment recommendations.
- It is exactly the kind of phrase that can become citation-shaped language if not fully understood.
- Closing this gap would sharpen both the executive memo and public benchmark claims.

**Grounding artifacts**

- `reports/executive_memo.md`
- `reports/week11_status_report.md`
- `ablations/ablation_results.json`

**What a strong explainer should cover**

- paired vs unpaired resampling
- confidence intervals vs practical significance
- why benchmark variance differs from production variance
- how to talk honestly about strong offline results

### 4. Contamination Detection Beyond N-grams

**Question**

How trustworthy is the repo’s contamination check in `generation_scripts/contamination_check.py`? In particular, what signal is captured by the local hashing-based embedding surrogate, how does that differ from semantic embedding models, and what contamination patterns could still slip through despite `0` reported violations?

**Why this is a real gap here**

- The contamination story is central to the credibility of the benchmark.
- The implementation is practical and reproducible, but not obviously equivalent to stronger semantic methods.
- This is a generalizable FDE question, not just a repo-specific one.

**Grounding artifacts**

- `generation_scripts/contamination_check.py`
- `contamination_check.json`
- `methodology.md`

**What a strong explainer should cover**

- n-gram overlap vs embedding similarity
- locality-sensitive hashing style surrogates vs true embedding encoders
- false positives, false negatives, and boilerplate filtering
- what contamination checks can and cannot prove

### 5. Tool Use, State, and Safe Escalation

**Question**

How should I explain the state-machine design in `agent/core/channel_orchestrator.py` as an agent-systems mechanism rather than just business logic? Specifically: why is centralizing channel transitions safer than letting handlers decide locally, and what invariants must hold for email, SMS, WhatsApp, calendar, and voice escalation to remain correct under retries, duplicate events, and partial failures?

**Why this is a real gap here**

- This repo claims deterministic-first orchestration as a core architectural advantage.
- The code already encodes nontrivial lifecycle rules.
- The deeper mechanism is about agent control, not just outbound messaging.

**Grounding artifacts**

- `agent/core/channel_orchestrator.py`
- `agent/core/state_manager.py`
- `backend/routes/webhook_*.py`
- `docs/system_architecture.md`

**What a strong explainer should cover**

- finite-state-machine patterns in agent systems
- idempotency and duplicate-event handling
- centralized policy vs distributed tool autonomy
- how channel safety policies map to runtime invariants

### 6. Preference Leakage And Model-Family Separation

**Question**

Why does `generation_scripts/synthesize_tasks.py` force generator, bulk judge, and eval-tier judge to come from different model families, and what leakage risk is actually being reduced by that policy? Is family separation enough, or do inheritance and style similarity still create evaluator bias even when the route validator passes?

**Why this is a real gap here**

- The repo makes this a first-class methodological choice.
- It connects directly to modern agent-eval and synthetic-data practice.
- It is precise enough for a good public explainer without becoming a textbook chapter.

**Grounding artifacts**

- `generation_scripts/synthesize_tasks.py`
- `tests/test_synthesis_routing.py`
- `methodology_rationale.md`

**What a strong explainer should cover**

- preference leakage modes
- generator-judge relatedness
- why family rotation helps
- what risks remain even after route separation

## My Recommended First Pick

If you want the single best Week 12 question from this repo, use this one:

> The repo reports a large held-out lift from the Path B critic, but the executed artifact is a sparse linear model. What exactly is this critic learning in `training/run_path_b_critic.py`, why can it separate chosen from rejected outputs so well on this benchmark, and why does it still over-value lexical compliance on medium-confidence email tasks?

Why this is the best pick:

- it is highly diagnostic
- it is tied to the headline result
- it produces a concrete portfolio payoff
- it generalizes to broader preference-learning and evaluation work

## One Non-Research Cleanup Gap

There is also one repo-quality issue you should fix separately because it weakens trust in the artifacts:

**Benchmark split counts drift across docs.**

- The live files in `tenacious_bench_v0.1/` are `62 / 113 / 50`.
- `README.md` matches that.
- `reports/week11_status_report.md` claims `106 / 76 / 43`.
- `reports/interim_submission_report.md` claims `112 / 69 / 44`.

That is not a science gap; it is a source-of-truth gap. Clean it before publishing or presenting, because it makes the stronger research claims easier to doubt.
