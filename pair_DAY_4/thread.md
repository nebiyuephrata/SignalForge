# Thread — Day 4

**1/**  
Aggregate metrics don’t lie, but they often erase structure. A global pass
rate, similarity score, or judge average can be numerically correct while still
hiding the exact subgroup or condition where the model is failing.

**2/**  
That happens because a single metric is compressing a mixture of behaviors:
retrieval cases, fallback cases, policy-boundary cases, routing cases,
easy cases, hard cases. If one slice collapses while others stay healthy, the
average can still look fine.

**3/**  
So the right question is never just “what is the average?” It’s “average over
what distribution, for what capability, and with what hidden subgroup
structure?”

**4/**  
The same issue shows up in judge-based evaluation. If the judge rewards fluency,
confidence, and formatting more than grounding or constraint-following, then the
evaluator is aligned to the wrong proxy. The score becomes a construct mismatch,
not just a noisy measurement.

**5/**  
Global metrics are useful for trend tracking and coarse comparison. But slicing
is mandatory when failures are rare, high-cost, condition-specific, or tied to
different mechanisms. That’s where real LLM reliability work happens.

**6/**  
A good evaluation stack has both layers: top-line summaries for regressions and
mechanism-aware slices for truth. If you only keep the average, you keep the
headline and lose the behavior.

