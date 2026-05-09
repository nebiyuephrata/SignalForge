# Canonical List

This is my annotated contribution to the Week 12 canon: the papers, docs,
patterns, and tools that most improved my ability to reason about the systems
in this repo as a Forward-Deployed Engineer.

## Papers and Primary References

### 1. SimPO

`Meng, Xia, and Chen — SimPO: Simple Preference Optimization with a Reference-Free Reward`

Why it belongs in the canon:
- best starting point for understanding why pairwise objectives reward
  separability
- useful for diagnosing shortcut learning and asymmetry between rejection and
  acceptance
- directly relevant to small critic / judge fine-tunes

When to read it:
- when a preference-tuned judge seems strong but poorly calibrated
- when redesigning chosen/rejected pairs

### 2. LLM-as-a-Judge Survey

`Gu et al. — A Survey on LLM-as-a-Judge`

Why it belongs:
- maps the evaluator problem clearly
- useful for distinguishing score generation, pairwise comparisons, and judge
  reliability concerns
- helps separate proxy measurement from intended capability

When to read it:
- when designing judges, judge prompts, or benchmark scoring layers

### 3. Preference Leakage

`Preference Leakage` paper

Why it belongs:
- gives a practical framework for relatedness between generator and judge models
- important for synthetic-data and evaluation-pipeline design
- useful guardrail when the same model family might contaminate both authoring
  and scoring

When to read it:
- when designing multi-LLM synthesis or evaluator rotation policies

### 4. DeepSeek-V2 context-cache architecture

Why it belongs:
- the clearest public pointer for the server-side KV-cache intuition
- turns “prompt caching” from product language into mechanism language

When to read it:
- when latency/cost work depends on long static prompts

### 5. Anthropic prompt caching docs

Why it belongs:
- explicit about byte-for-byte tokenized-prefix invalidation
- helps convert vague caching advice into actionable prompt-design rules

When to read it:
- when designing cache-friendly prompts or trying to explain cache misses

### 6. OpenAI Structured Outputs / function-calling docs

Why it belongs:
- best primary source for the boundary between JSON prompting and strict schema
  enforcement
- useful for understanding when decoding is merely encouraged vs constrained

When to read it:
- when replacing parser-repair chains with stricter structured output APIs

### 7. Enterprise Integration Patterns — Process Manager

Why it belongs:
- best systems-pattern framing for centralized orchestration
- makes agent tool-use policy legible as a coordination problem, not just app
  code

When to read it:
- when a multi-tool agent starts depending on shared state and side effects

### 8. Sagas

Why it belongs:
- clarifies long-lived multi-step coordination under failure
- useful for thinking about what an orchestrator can guarantee and what requires
  stronger infrastructure

When to read it:
- when partial failures and recovery semantics matter

## Statistical and Evaluation Patterns

### 1. Paired bootstrap for same-example model comparisons

Why it belongs:
- preserves dependence structure when two systems are scored on the same
  examples
- much more honest than pretending paired outputs are independent

Use it when:
- baseline and candidate are evaluated on the same slice

### 2. Subgroup and slice analysis

Why it belongs:
- catches exactly the failures aggregate metrics dilute
- mandatory for routing, safety, and rare-but-costly failures

Use it when:
- the benchmark is a mixture of task types, conditions, or failure modes

### 3. Construct-validity checks for metrics and judges

Why it belongs:
- forces the question: what capability does this metric really measure?
- helps catch evaluator alignment to the wrong proxy

Use it when:
- a judge rewards polish instead of grounding
- a metric gives stable numbers but wrong operational conclusions

## Tools and Workflow Patterns

### 1. Langfuse traces

Why it belongs:
- best bridge from anecdotal failure to inspectable evidence
- makes it easier to connect mechanism questions back to real traces

### 2. Probe libraries plus failure-taxonomy slices

Why it belongs:
- turns “the model sometimes fails” into named behavioral regimes
- makes hidden slice failures visible

### 3. Deterministic evaluators for crisp dimensions

Why it belongs:
- useful when you need reproducibility and low ambiguity
- especially strong for structural checks, channel policy, and explicit
  constraints

### 4. Hard-negative design in preference datasets

Why it belongs:
- one of the highest-leverage tools for pushing a critic away from surface
  cues and toward deeper distinctions

### 5. Mechanism-aware documentation

Why it belongs:
- the portfolio is stronger when docs explain what the system prevents, not just
  what it does
- this week proved that architecture and memo docs are part of the technical
  surface, not just presentation
