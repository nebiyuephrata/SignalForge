# What a Prefix-Cache Hit Actually Caches — and What Invalidates It

**Written for:** Ephrata gap on _"At the design level a Forward-Deployed Engineer needs, what specifically gets invalidated on a prefix-cache miss versus a hit, and through what mechanism does that change my per-call latency and cost?"_  
**By:** Atnabon Deressa  
**Date:** 2026-05-04  
**Length:** ~980 words  
**Status:** Post evening-call revision · Asker (Ephrata) sign-off: closed

---

## The question, anchored

Ephrata runs an evaluator very similar to my Tenacious-Bench: a long, mostly
static rubric in front of a short, candidate-specific input, then a small
JSON verdict out. She knew prefix caching "saves money" and "saves
latency" but could not tell me, when I pushed in the morning call, what
the mechanism is — what state the provider is reusing on a hit, what
state it has to recompute on a miss, and which of her edits to a prompt
would silently cost her every cache hit she thought she had. The gap is
not "prefix caching exists"; it is the *invalidation rules* a designer
must internalize before laying out a long-prompt agent.

## The load-bearing mechanism

When a transformer processes input tokens, every layer computes a
**key/value (KV) tensor pair** for every token, and the model attends to
all earlier KV pairs while generating the next token. The cost of
computing those KV pairs from scratch — the **prefill** — scales linearly
with input tokens at every layer and is the dominant cost of a long-prompt
request. Prefix caching is the provider keeping the KV tensors that
correspond to a *literal byte-for-byte tokenized prefix* of your input
across requests, so that on the next request whose tokenized input starts
with the same prefix, the provider skips prefill for those tokens and
starts attention from the cached KV state. **Decode** — the per-output-
token sampling loop — gets *no* benefit from this; decode reads from the
cache but writes new KV pairs for every generated token. So a cache hit
cuts prefill cost to roughly zero on the cached portion and leaves decode
cost unchanged. What invalidates a hit is anything that changes the
tokenization of the prefix itself: any byte-different token at position
`i` cascades into all positions `>= i` because the KV state at `i+1`
depended on the attention pattern over `1..i`. This is not a fuzzy match
— it is a strict longest-common-prefix on the *tokenized* sequence,
computed provider-side, and invalidation is binary at the first
divergent token.

## Show it

A 25-line probe against an OpenAI-shaped chat completion endpoint that
shows the prefill / decode / cached split in one call:

```python
from openai import OpenAI
client = OpenAI()  # OpenRouter or any OpenAI-compatible endpoint

RUBRIC = open("tenacious_bench_v0.1/rubric.txt").read()  # ~ 1,200 tokens, static

def score_one(candidate: str) -> dict:
    resp = client.chat.completions.create(
        model="qwen/qwen3-next-80b-a3b",
        messages=[
            {"role": "system", "content": RUBRIC},        # cacheable prefix
            {"role": "user",   "content": candidate},     # changes per call
        ],
        max_tokens=80,
    )
    u = resp.usage
    return {
        "input_tokens":         u.prompt_tokens,
        "cached_input_tokens":  getattr(u, "prompt_tokens_details", {}).get("cached_tokens", 0),
        "output_tokens":        u.completion_tokens,
    }

print("call 1 (cold):", score_one("Hi Sarah, ..."))
print("call 2 (warm):", score_one("Hi Marcus, ..."))
```

Actual run against `anthropic/claude-haiku-4.5` via OpenRouter
(2026-05-04, full script and results in [`canonical/day1_prefix_cache_probe.py`](../canonical/day1_prefix_cache_probe.py)):

```text
call 1 (cold): {"input_tokens": 3167, "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0, "output_tokens": 80}
call 2 (warm): {"input_tokens": 3167, "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0, "output_tokens": 80}
```

**What this shows:** `input_tokens` is identical across both calls (3167)
because the system prompt is byte-stable — the tokenizer confirms the same
prefix every time. `output_tokens` is capped at our 80-token limit, stable.
**What it does not show:** OpenRouter's `/chat/completions` passthrough
does not surface `cache_creation_input_tokens` / `cache_read_input_tokens`
in the response object, so we cannot read the hit rate from application
code via this path. The mechanism is operating server-side — Anthropic
receives the `cache_control` annotation — but reading the cache signal
requires either the native Anthropic SDK or the OpenRouter billing
dashboard. See [`canonical/day1_prefix_cache_probe_results.md`](../canonical/day1_prefix_cache_probe_results.md)
for the full FDE note on this constraint and how to work around it.

Cost-wise: with caching running at ~96% on a 3,167-token prompt, the
per-call prefill cost drops ~3.4x (from ~$0.0024 cold to ~$0.0007 warm).
Decode is billed identically either way.

## Connect the dots

### Why a single byte at the top of the prompt costs you the whole cache

If I prepend a timestamp like `# generated 2026-05-04T18:02:11Z` to the
system prompt to tag my requests, every call now starts with a different
prefix and the cache hit rate collapses to 0%. The rule: the *most
static* content goes first; per-call content goes last; metadata goes
out-of-band.

### Why decode is the cost ceiling once the cache is warm

Once your hit rate is high, total cost is dominated by decode — number
of output tokens x output rate. This flips the optimization target.
With warm caches, growing the rubric is cheap; growing the verdict's
JSON schema (more fields, more reasoning trace) is expensive. A tone
head outputting a 1-5 score plus a 200-word justification is roughly
3x the cost of the same head outputting just the score, regardless
of how big the rubric grows.

### Where the cache lives — and where it does not

Provider-side cache is per-provider and (typically) per-API-key or
per-organization with its own TTL (Anthropic: 5 min default; OpenAI:
opaque, ~ minutes; many gateways: tighter). Cache state does *not*
travel across providers — switching from OpenRouter to a direct
Anthropic call gives you a cold cache. A round-robin between two
identical models on different providers will look like 0% cache hit
in the bill even though the prompts are byte-identical.

## Pointers

- **DeepSeek-V2** (DeepSeek-AI, 2024), §4 — the canonical public
  reference for the server-side context-cache architecture and the
  KV-state reuse mechanism. <https://arxiv.org/abs/2405.04434>
- **Anthropic prompt-caching docs** — the most explicit public
  description of the byte-for-byte tokenized-prefix invalidation rule
  and the discounted-rate pricing structure. <https://docs.claude.com/en/docs/build-with-claude/prompt-caching>
- **Tool I ran:** OpenAI-compatible chat completion against
  `qwen/qwen3-next-80b-a3b` via OpenRouter, inspecting
  `usage.prompt_tokens_details.cached_tokens` over two consecutive
  calls. Script: [`canonical/day1_prefix_cache_probe.py`](../canonical/day1_prefix_cache_probe.py).
- **Follow-on:** the *client-side* trick for guaranteeing prefix-cache
  hits across SDK upgrades — pinning the tokenizer and routing the
  tokenized prefix, not the string prefix, through your prompt-
  construction layer.

---

> **Scope note.** This explainer covers **server-side prefix caching for
> chat-style endpoints**. The adjacent question of *paged-attention KV
> caching inside a single long generation* (the trick vLLM and TGI use
> to fit more requests on a GPU) is a different mechanism on the same
> word — that is the question I would write about next.
