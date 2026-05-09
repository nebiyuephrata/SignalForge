# Sources — Day 2

## Canonical sources

1. OpenAI, `Structured Outputs in the API`
   - Why it was used: primary source for the distinction between JSON mode,
     schema-constrained outputs, and decode-time constrained decoding.
   - Link: <https://openai.com/index/introducing-structured-outputs-in-the-api/>

2. Anthropic, `Tool use implementation guide`
   - Why it was used: primary source for tool-use protocol behavior and the fact
     that tool definitions are incorporated into a structured serving-time prompt
     and protocol.
   - Link: <https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/implement-tool-use>

## Tool / pattern used

- Repo grounding pattern:
  - `agent/llm/client.py`
  - `pair_DAY_2/question.md`
  - `pair_DAY_2/explainer.md`
- Practical pattern:
  - compare raw JSON prompting, JSON mode, and strict structured output paths
    by tracing which failures still require parser-repair logic

