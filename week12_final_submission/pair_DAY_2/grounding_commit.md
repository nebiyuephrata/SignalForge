# Grounding Commit — Day 2 (For Peer)

**Artifact updated:** [docs/system_architecture.md](/home/rata/Documents/Ephrata/work/10Acadamy/training/SignalForge/docs/system_architecture.md)

I updated the architecture write-up to make the channel orchestrator's
defensive role explicit instead of describing only the happy-path flow. The new
section names the invariants I can now defend after reading Amir's explainer:
authoritative shared state, monotonic transitions, duplicate suppression when
`external_id` is available, centralized channel eligibility, and the
separation between provider adapters and policy. This changed the document from
"here is the sequence of channels" to "here is the mechanism that prevents
invalid tool actions," which is the concrete portfolio improvement produced by
closing this gap.
