# Function Calling Is Not Just "Better JSON Prompting"

**Written for:** Amir's question on Week 10 `complete_json()` parsing fallback  
**Topic:** Agent and tool-use internals  
**Date:** 2026-05-06

---

## The question, anchored

Your Week 10 conversion engine does something many of us build first: ask the
model for JSON, strip markdown fences, remove `<think>` blocks, try
`json.loads()`, and if that fails, salvage the substring between the first `{`
and the last `}`. That works often enough to feel like a "poor man's function
call," so the real question is: when an API offers **function calling** or
**tool use**, is the model actually doing something different at decode time, or
is the provider just stuffing your schema into the prompt and hoping the model
behaves?

The short answer is: **it depends on the API mode, but it is not just a prompt
trick**. The decoding mechanism is the core of the answer; the API stack is the
adjacent context that makes the answer actionable for your deployment. Modern
tool-calling stacks usually combine three layers:

1. provider-side prompt construction from the tool schema,
2. model training to recognize the tool-calling protocol, and
3. in some modes, constrained decoding so only schema-valid outputs can be emitted.

The important distinction is that **plain prompted JSON** only gives you layer
1 informally, while **strict structured outputs** add layer 3 explicitly.

There are actually two related but different questions here:

1. **structured argument generation**
   This is the core Week 10 gap in your `complete_json()` path: when you need
   valid structured fields back, what guarantees does the API actually give you?
2. **tool choice**
   This is adjacent: how the model decides whether to call a tool at all. That
   matters for systems like Oracle Forge where the wrong tool may be selected,
   but it is not the main mechanism you are asking about here.

So below, I stay centered on **structured argument generation under strict
schema enforcement**, and I treat tool choice as neighboring context rather
than the core question.

## The load-bearing mechanism

At the token level, a language model always predicts the next token from a
distribution over its vocabulary. In practice, that means the model produces a
logit for every possible next token, those logits are transformed into a
distribution, and decoding picks from the legal candidates. The real question
is: **does the serving stack merely bias those logits through prompting and
fine-tuning, or does it actively mask illegal tokens before sampling?**

That is the key distinction because it decides whether your fallback parsing
chain is dead code or correct engineering.

### Case 1: Plain "please output JSON"

This is your current pattern. The model is still doing ordinary free-form next
token prediction over the full vocabulary. It may *tend* to emit `{`, `"reply_class"`,
`true`, and so on because your prompt makes that pattern likely, but it can also
emit:

- prose before the JSON
- markdown fences
- commentary after the JSON
- malformed commas or quotes
- schema drift like `book_call` instead of `should_book_call`

At decode time, nothing hard-stops it from generating those tokens. No token is
being masked just because it would break your schema. Your repair logic exists
because the output channel is still fundamentally free-form text.

### Case 2: JSON mode

This is stronger, but still not the same as function calling with strict schema
guarantees. In OpenAI's docs, `response_format: {"type": "json_object"}`
ensures valid JSON, but **does not guarantee your specific schema**. That means
the decoding process is more constrained than plain text generation, but only at
the level of "must be valid JSON," not "must be exactly the object shape I
wanted."

So the model may still return:

```json
{"replyType": "warm", "book": true, "handoff": false}
```

That parses fine. It is valid JSON. It is still wrong for your downstream code.

### Case 3: Function calling / tool use without strict schema enforcement

Here the provider usually does more than your manual prompt. Anthropic's tool
docs explicitly say that when you pass `tools`, they construct a **special
system prompt** from the tool definitions, tool configuration, and your own
system prompt. So yes, there is protocol-level prompt injection happening.

But it is not only that. The model is also trained to emit a special structured
tool-call shape rather than arbitrary assistant prose. In Anthropic, this
appears as `tool_use` blocks. In OpenAI, this appears as tool/function call
arguments. The model is no longer merely "trying to be nice and output JSON";
it is participating in a serving protocol where the assistant turn can take on
a distinct tool-call form.

Still, unless strict schema enforcement is enabled, this is mostly **learned
behavior plus protocol scaffolding**, not a full hard grammar guarantee. In
other words, the model may be very likely to emit the right structure because it
has been trained for it, but reliability comes from learned behavior, not from
a proof-by-construction constraint on the decoder.

### Case 4: Function calling with strict structured outputs

This is the strongest mode, and this is where the answer becomes clearly
"different at the token level."

OpenAI's Structured Outputs docs state that with `strict: true`, outputs are
guaranteed to match the supplied JSON Schema, and the company explicitly says
this is achieved by both:

- training models to understand schemas better, and
- **constraining decoding** to match the developer-supplied schema.

That means the next-token vocabulary is not merely "biased toward valid tool
arguments." It is actively pruned by the decoder according to what tokens are
legal at that point in the schema. Put differently: the logits for illegal
tokens are effectively masked out before sampling. If the schema says the next
valid key must be `"reply_class"`, the decoder should not be allowed to emit
`"replyType"` there. If the value must be a boolean, the decoder should not be
allowed to emit `"yes"`.

This is much closer to grammar-guided decoding than to prompt engineering.

You can think of this as a finite-state or grammar-like controller sitting on
top of ordinary next-token prediction. The model still produces logits, but the
serving layer intersects those logits with the set of schema-valid continuations
at that exact step.

## Show it as a stack

The clean mental model is:

| Mode | What the model is generating | What constrains next tokens |
| --- | --- | --- |
| Prompted JSON | plain assistant text | only prompt likelihood |
| JSON mode | valid JSON text | JSON well-formedness |
| Tool calling, non-strict | tool-call protocol plus learned schema behavior | protocol + training, sometimes soft constraints |
| Tool calling, strict structured outputs | tool-call arguments matching schema | protocol + training + constrained decoding |

So your current parser-repair pipeline sits entirely in the first row. It works
because you are patching model errors **after** decoding. Function calling with
strict schema support prevents many of those errors **during** decoding.

## Why this matters in your Week 10 engine

In your conversion engine, fields like `reply_class`, `should_book_call`, and
`needs_human_handoff` are not decorative. They drive workflow decisions. That
means your real requirement is not "JSON-ish text." It is "a typed object whose
keys and value domains are safe to execute against."

With your current setup, these failure modes remain possible:

- syntactic failure: the JSON does not parse
- structural failure: the JSON parses but uses the wrong keys
- semantic drift: the keys are right but values are the wrong type or enum
- contamination failure: hidden reasoning or markdown survives cleanup and
  breaks parsing or auditing

Function calling reduces those risks in proportion to how much the provider
actually enforces the schema. If the API only injects tool definitions into a
prompt, you still need validation and retries. If the API supports strict schema
enforcement, a lot of your current cleanup logic becomes unnecessary because the
bad tokens never become legal emissions in the first place.

This is why your clarified framing is so useful:

- if the mechanism is **fine-tuning plus protocol prompting**, reliability is
  high but not guaranteed, and your fallback chain is still correct engineering
- if the mechanism is **constrained decoding under a strict schema**, reliability
  is effectively guaranteed by construction for structural validity, and much of
  that fallback chain becomes dead code

## Connect the dots

### Why your fallback parser is evidence of free-form decoding

The fact that you need to strip fences, remove `<think>` blocks, and salvage the
substring between braces is itself the clue. Those repairs only make sense if
the model had permission to emit tokens outside the intended object.

### Why "schema in prompt" and "schema in decoder" are not equivalent

A prompt can *encourage* a model to output `"needs_human_handoff": false`. A
decoder constraint can *forbid* it from outputting `"handoff_needed": "no"` in
that slot. For workflow safety, forbidding beats encouraging.

### Why vendors differ

Anthropic publicly documents the tool-use system prompt construction and even
notes that some `tool_choice` modes prefill the assistant message to force tool
use. OpenAI publicly documents constrained decoding for strict structured
outputs. So the exact mechanism is provider-specific, but the broad lesson is
stable: **tool calling is usually a serving protocol, not just a nicer prompt**.

That is also where OpenRouter or any relay layer matters for deployment. The
core mechanism is still about decode-time constraints versus unconstrained
generation, but the operational question becomes: which guarantees survive the
gateway, and which only exist when the upstream provider's strict mode is
actually exposed end to end?

## Bottom line

If you prompt for raw JSON, the model is still doing free-form text generation
and you are repairing the damage afterward.

If you use function/tool calling without strict schema enforcement, you usually
get better behavior because the provider adds tool definitions, protocol
structure, and model training around that behavior, but it may still be partly
soft.

If you use function/tool calling with **strict structured outputs**, then yes:
the difference is genuinely at the token level. The decoder is constrained so
illegal schema-breaking tokens are not valid next-token choices in the first
place.

That is the real line between "poor man's function call" and an actual
tool-calling interface.

## Pointers

- OpenAI Function Calling help: <https://help.openai.com/en/articles/8555517-function-calling-in-the-openai-api>
- OpenAI Structured Outputs guide: <https://developers.openai.com/api/docs/guides/structured-outputs>
- OpenAI Structured Outputs post, including constrained decoding: <https://openai.com/index/introducing-structured-outputs-in-the-api/>
- Anthropic tool use implementation guide: <https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/implement-tool-use>
