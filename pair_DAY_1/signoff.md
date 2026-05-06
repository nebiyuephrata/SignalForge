# Sign-off — Day 1

**Asker (signing off):** Ephrata Nebiyu  
**Explainer (received from):** Atnabon Deressa  
**Topic:** Inference-time mechanics — prefix-cache invalidation rules  
**Date:** 2026-05-04

---

## Judgement

- [x] **Closed** — gap is closed; I can now defend the mechanism unaided.
- [ ] **Partially closed**
- [ ] **Not closed**

## What I understand now that I did not before

I now see that prefix caching is not a fuzzy "the system noticed your prompt
was similar" — it is a strict longest-common-prefix match on the *tokenized*
sequence, evaluated provider-side, where the cache is the literal KV
tensors at every transformer layer for those prefix tokens. A hit lets the
provider skip prefill on the cached portion and bills it at the discounted
cached-input rate; decode writes new KV pairs every step and gets nothing
from the cache. The consequence I had not internalised before today is that
**any byte-different token at position `i` in my system prompt invalidates
every cache hit downstream of `i`** — so prepending a per-call timestamp,
request ID, or A/B-test tag to the system prompt collapses my hit rate to
0% silently. The 25-line `usage.prompt_tokens_details.cached_tokens` probe
in the explainer makes the mechanism directly verifiable on my own
endpoint, which is what closed it for me — I ran it twice while Atnabon
walked me through the second pass and watched `cached_tokens` jump from
`0` to `1198` between calls.

## Residual gap (if partial / not closed)

_(N/A — closed on first revision.)_

## Notes for the cohort vote

I am voting Atnabon's question (prefill / decode billing split) into the
top-three slot for tomorrow's presentation. The mechanism explanation he
got from me, combined with what landed in his cost log, is the most
concrete grounding commit I have seen any pair produce this week.
