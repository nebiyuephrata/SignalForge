# Thread — Day 2

## Thread A: Centralized Orchestration As An Agent Tool-Use Mechanism

**1/**  
In multi-tool agents, "tool use" is not just about calling a tool correctly. It is also about deciding **when** a tool is allowed to fire, what state is authoritative, and how to stop retries, duplicate events, or partial failures from corrupting the workflow.

**2/**  
That is why a centralized orchestrator is different from letting each handler decide locally. A local handler only sees its slice. An orchestrator can enforce global invariants like: closed leads cannot reopen, booked leads cannot be escalated, and SMS cannot fire unless the lifecycle state makes it eligible.

**3/**  
The real failure mode in distributed tool policy is not just "two tools both ran." It is **local decisions made from incomplete state**. One handler may think escalation is allowed while another still believes the lead is only in an emailed state, or already booked, or already closed.

**4/**  
So the important mechanism is not the sales cadence itself. It is the state machine: monotonic transitions, duplicate-event detection, and a single policy layer that separates "provider adapter behavior" from "agent decision policy."

**5/**  
That generalizes beyond outbound sales. Any agent with multiple tools, asynchronous events, retries, and side effects needs the same question answered: where do correctness guarantees live, and who is allowed to make tool-use decisions?

**6/**  
My Day 2 gap was learning how to explain that architecture as an agent-systems mechanism rather than just business logic. The SignalForge example made the failure modes visible. The deeper lesson is about safe tool use under partial failure.

## Thread B: Function Calling Is Not Just Better JSON Prompting

**1/**  
If you prompt an LLM to "return JSON," you are still usually doing free-form text generation. The model may output valid fields. It may also output markdown fences, `<think>` blocks, extra prose, or wrong keys. That is why parser-repair chains exist.

**2/**  
The key question is what happens at decode time. Are invalid tokens merely unlikely because of prompting and fine-tuning, or are they **impossible** because the serving stack masks schema-invalid tokens before sampling?

**3/**  
That is the difference between soft structure and hard structure. Prompted JSON gives you soft structure. Strict structured outputs add decode-time constraints, so the next-token vocabulary is pruned to what is legal under the schema at that exact step.

**4/**  
So "function calling" is not one thing. There is:
- prompted JSON
- JSON mode
- tool calling with protocol scaffolding
- strict schema enforcement with constrained decoding

Those modes have very different guarantees.

**5/**  
For workflow systems, that distinction matters. If reliability comes only from training, fallback parsing is still correct engineering. If reliability comes from constrained decoding, much of that fallback code becomes dead weight because structural invalidity is blocked during generation.

**6/**  
My peer's Day 2 question was really about that boundary: at what point does structured output stop being prompt engineering and become decoder-level constraint? That is the line between a poor man's function call and a real one.
