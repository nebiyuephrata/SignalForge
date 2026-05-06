# Sign-Off — Day 2

## Amir's sign-off on Ephrata's explainer (for Amir's question)

**Asker:** Amir Ahmedin
**Explainer:** Ephrata Nebiyu
**Date:** Day 2, Week 12
**Judgment:** Closed ✓

### What I understand now that I did not before

Before this explainer, I treated "function-calling" as a single thing — either it's constrained decoding or it's prompt injection. I couldn't explain why my `complete_json()` fallback chain sometimes works perfectly and sometimes catches real parse failures.

Now I understand there are **four distinct levels**, not two:

1. **Plain prompted JSON** (my current approach) — full vocabulary available at every step. Model can emit fences, think blocks, wrong keys. My fallback chain is correct and necessary.

2. **JSON mode** (`response_format: json_object`) — guarantees valid JSON syntax but NOT my specific schema. Model can still return wrong keys or wrong value types. My fallback chain is partially needed (syntax is safe, schema is not).

3. **Tool calling without strict** — provider adds protocol structure + model is trained on tool-call patterns. Much better than prompting, but still learned behavior, not proof-by-construction. Fallback chain is mostly unnecessary but not dead code.

4. **Tool calling with strict structured outputs** (`strict: true`) — constrained decoding at the token level. Illegal schema-breaking tokens are masked before sampling. My fallback chain IS dead code for this mode.

The key insight Ephrata named: "The fact that you need to strip fences, remove think blocks, and salvage substrings is itself the clue — those repairs only make sense if the model had permission to emit tokens outside the intended object." My repair code is *evidence* of the decoding mode, not just defensive engineering.

The revised explainer also addressed the OpenRouter relay question honestly: I should treat deletion of the fallback chain as a **testable hypothesis**, not an assumption. The concrete test procedure (run eval set on both paths, compare parse/key/type failures) gives me an immediate next step.

The one-sentence version I'll carry forward: **"A prompt can encourage a model to output the right key. A decoder constraint can forbid it from outputting the wrong key. For workflow safety, forbidding beats encouraging."**

---

## Ephrata's sign-off on Amir's explainer (for Ephrata's question)

**Asker:** Ephrata Nebiyu
**Explainer:** Amir Ahmedin
**Date:** Day 2, Week 12
**Judgment:** Closed ✓

### What Ephrata understands now that he did not before

Before this explainer, I could describe my orchestrator's happy path but could not name what it *prevents*. If a senior engineer asked "why not just let each handler decide?", I would have said "single source of truth" without being able to name the specific failure modes.

Now I can name three concrete invariants my orchestrator enforces:

1. **Monotonic transitions** — state only moves forward. No handler can independently revert the lifecycle. This prevents the "SMS sent to a closed lead" scenario I was worried about.

2. **Idempotent event processing** — duplicate webhooks (which happen constantly in production) are rejected because the orchestrator checks current state before transitioning. Without this, the same event processed by two handlers produces contradictory actions.

3. **Global eligibility** — "is SMS allowed right now?" depends on the full lifecycle state, not just "a reply was received." Each handler only sees a projection of state; only the orchestrator sees the full picture.

The analogy to constrained decoding was the insight that reframed this as an agent-systems pattern rather than just CRM workflow code: the orchestrator restricts the action space (which tools can fire) the same way constrained decoding restricts the token space (which tokens can be sampled). Both enforce correctness by making invalid actions structurally impossible rather than hoping the actor makes the right choice.

I can now defend my architecture by naming what breaks without it, not just describing what it does.
